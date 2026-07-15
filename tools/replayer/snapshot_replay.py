#!/usr/bin/env python3
"""重放 fixtures/snapshots/*.req.json 到本方接口 (adapter),落 actual。

用法:
  python3 tools/replayer/snapshot_replay.py \\
      --domain thaiairways.com \\
      --target https://my-adapter.local

  # 重放某一个 endpoint
  python3 tools/replayer/snapshot_replay.py \\
      --domain thaiairways.com \\
      --target https://my-adapter.local \\
      --filter "GET_search-airports"

  # 直接重放回原站(诊断用,默认禁用)
  python3 tools/replayer/snapshot_replay.py --domain X --target original

行为:
  1. 读 snapshots/*.req.json 与对应 meta.yaml
  2. 检查 meta.expires_at 未过期(过期 warn 但不跳)
  3. 重写 URL host 为 --target
  4. 发请求 (用 stdlib urllib,零依赖)
  5. 落 actual/<prefix>.actual.json (同 resp.json 结构)
  6. 不做 diff,diff 由 consistency_report 调
"""
from __future__ import annotations

import argparse
import datetime
import ipaddress
import json
import os
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urlunparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"
sys.path.insert(0, str(REPO_ROOT / "tools" / "replayer"))

from fixture_layout import select_fixture_layout

try:
    from field_rules import yaml as yaml_parser
except ImportError:
    yaml_parser = None


@dataclass(frozen=True)
class ReplayResult:
    status: str
    exit_code: int
    total: int
    selected: int
    replayed: int
    failed: int
    expired: int
    no_data: bool
    actual_artifacts: tuple[str, ...]
    filtered: int = 0

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "exit_code": self.exit_code,
            "total": self.total,
            "selected": self.selected,
            "replayed": self.replayed,
            "failed": self.failed,
            "expired": self.expired,
            "no_data": self.no_data,
            "actual_artifacts": list(self.actual_artifacts),
            "filtered": self.filtered,
        }


def emit_result(result: ReplayResult) -> int:
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    return result.exit_code


def refused_result() -> ReplayResult:
    return ReplayResult(
        status="REFUSED",
        exit_code=2,
        total=0,
        selected=0,
        replayed=0,
        failed=0,
        expired=0,
        no_data=False,
        actual_artifacts=(),
    )


class ReplayArgumentError(Exception):
    pass


class ReplayArgumentParser(argparse.ArgumentParser):
    def print_help(self, file=None) -> None:
        super().print_help(file=sys.stderr if file is None else file)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if message:
            print(message, end="", file=sys.stderr)
        raise ReplayArgumentError("help requested" if status == 0 else "parser exit")

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise ReplayArgumentError(message)


def parse_target(target: str) -> tuple[str, str] | None:
    """返回 adapter 的 (scheme, netloc),或 None 表示显式重放回原站。"""
    if target == "original":
        return None
    if not target or any(char.isspace() for char in target):
        raise ValueError("adapter target must not be empty or contain whitespace")
    parsed = urlparse(target if "://" in target else f"https://{target}")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("adapter target must use http/https with a non-empty host")
    if "\\" in parsed.netloc or parsed.username is not None or parsed.password is not None:
        raise ValueError("adapter target authority must not contain userinfo or separators")
    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"invalid adapter authority: {exc}") from exc
    if not hostname or any(char.isspace() for char in hostname) or parsed.netloc.endswith(":"):
        raise ValueError("adapter target must contain a valid host")
    if port is not None and not 0 <= port <= 65535:
        raise ValueError("adapter target port is out of range")
    try:
        if ":" in hostname or hostname.replace(".", "").isdigit():
            ipaddress.ip_address(hostname)
        else:
            ascii_hostname = hostname.encode("idna").decode("ascii").rstrip(".")
            labels = ascii_hostname.split(".")
            if (
                not ascii_hostname
                or len(ascii_hostname) > 253
                or any(
                    not label
                    or len(label) > 63
                    or label.startswith("-")
                    or label.endswith("-")
                    or any(not char.isalnum() and char != "-" for char in label)
                    for label in labels
                )
            ):
                raise ValueError
    except (UnicodeError, ValueError) as exc:
        raise ValueError("adapter target must contain a valid host") from exc
    return parsed.scheme, parsed.netloc


def rewrite_url(original: str, target: tuple[str, str] | None) -> str:
    if target is None:
        return original
    target_scheme, target_netloc = target
    p = urlparse(original)
    return urlunparse((target_scheme, target_netloc, p.path, p.params, p.query, p.fragment))


def normalize_meta(meta: object, prefix: str) -> dict:
    if isinstance(meta, Mapping):
        return dict(meta)
    print(f"WARN: invalid metadata {prefix}: root must be a mapping", file=sys.stderr)
    return {}


def load_replay_meta(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        if yaml_parser is None:
            print(
                f"WARN: unable to parse metadata {path.name}: YAML parser unavailable",
                file=sys.stderr,
            )
            return {}
        raw_meta = yaml_parser.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARN: invalid metadata {path.name}: {exc}", file=sys.stderr)
        return {}
    if raw_meta is None:
        return {}
    return normalize_meta(raw_meta, path.name)


def check_expiry(meta: Mapping, prefix: str) -> bool:
    if "expires_at" not in meta or meta["expires_at"] is None:
        return True
    exp = meta["expires_at"]
    if isinstance(exp, datetime.datetime):
        exp_dt = exp
    elif isinstance(exp, datetime.date):
        exp_dt = datetime.datetime.combine(exp, datetime.time.min)
    elif isinstance(exp, str):
        try:
            exp_dt = datetime.datetime.fromisoformat(exp.replace("Z", "+00:00"))
        except ValueError:
            print(f"WARN: invalid expires_at for {prefix}: {exp!r}", file=sys.stderr)
            return True
    else:
        print(f"WARN: invalid expires_at for {prefix}: {exp!r}", file=sys.stderr)
        return True
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=datetime.timezone.utc)
    else:
        exp_dt = exp_dt.astimezone(datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    if exp_dt < now:
        print(
            f"WARN: {prefix} expired at {exp} "
            "(recorded > 30 days ago, re-record recommended)",
            file=sys.stderr,
        )
        return False
    return True


def normalize_request(req_doc: object) -> tuple[str, str, dict, object]:
    if not isinstance(req_doc, dict):
        raise ValueError("root must be an object")
    method = req_doc.get("method", "GET")
    url = req_doc.get("url")
    headers = req_doc.get("headers")
    body = req_doc.get("body")
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")
    if not isinstance(url, str) or not url:
        raise ValueError("url must be a non-empty string")
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("url must be an absolute http/https URL")
    if headers is None:
        headers = {}
    if not isinstance(headers, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in headers.items()
    ):
        raise ValueError("headers must be an object with string keys and values")
    return method, url, headers, body


def discard_actual(out_file: Path) -> None:
    try:
        out_file.unlink(missing_ok=True)
    except OSError as exc:
        print(f"WARN: unable to remove stale actual {out_file}: {exc}", file=sys.stderr)


def cleanup_temporary_siblings(out_file: Path) -> None:
    try:
        candidates = out_file.parent.glob(f".{out_file.name}.*.tmp")
        for candidate in candidates:
            try:
                candidate.unlink(missing_ok=True)
            except OSError:
                pass
    except OSError:
        pass


def write_actual_atomic(out_file: Path, actual_doc: dict) -> None:
    temp_name: str | None = None
    try:
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=out_file.parent,
            prefix=f".{out_file.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(actual_doc, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, out_file)
    except Exception:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
        cleanup_temporary_siblings(out_file)
        discard_actual(out_file)
        raise


def contained_path(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def resolve_fixtures_dir(domain: str) -> Path:
    if (
        not domain
        or domain in {".", ".."}
        or domain != domain.strip()
        or "/" in domain
        or "\\" in domain
        or any(
            char.isspace() or unicodedata.category(char).startswith("C")
            for char in domain
        )
        or Path(domain).is_absolute()
    ):
        raise ValueError("domain must be a safe single path component")
    try:
        site_root = SITE_ROOT.resolve()
        domain_root = (SITE_ROOT / domain).resolve()
        fixtures_path = SITE_ROOT / domain / "fixtures"
        fixtures_dir = fixtures_path.resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"unable to resolve domain safely: {exc}") from exc
    if domain_root == site_root or not contained_path(domain_root, site_root):
        raise ValueError("domain resolves outside SITE_ROOT")
    if not contained_path(fixtures_dir, site_root):
        raise ValueError("fixtures resolve outside SITE_ROOT")
    return fixtures_path


def send_request(method: str, url: str, headers: dict, body: object,
                 timeout: int = 30) -> dict:
    if isinstance(body, (dict, list)):
        body_bytes = json.dumps(body).encode("utf-8")
        if "content-type" not in {k.lower() for k in headers}:
            headers = {**headers, "content-type": "application/json"}
    elif isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif body is None:
        body_bytes = None
    else:
        body_bytes = str(body).encode("utf-8")

    req = urllib.request.Request(url, data=body_bytes, method=method)
    # 默认 strip 压缩相关 header,让服务器返回明文(urllib 不自动解压)
    # 即使如此服务器仍可能返回 gzip,后面用 Content-Encoding 兜底解压
    skip_headers = {"host", "content-length", "connection",
                    "accept-encoding"}
    for k, v in headers.items():
        if k.lower() in skip_headers:
            continue
        req.add_header(k, v)
    req.add_header("Accept-Encoding", "identity")  # 显式要明文

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = resp.read()
    except urllib.error.HTTPError as e:
        status = e.code
        resp_headers = {k.lower(): v for k, v in (e.headers or {}).items()}
        raw = e.read() or b""
    except urllib.error.URLError as e:
        return {"status": 0, "headers": {}, "body": None,
                "_meta": {"error": str(e), "body_encoding": "none"}}

    # 服务器无视 Accept-Encoding:identity 时,按 Content-Encoding 解压
    content_enc = resp_headers.get("content-encoding", "").lower().strip()
    if content_enc == "gzip":
        import gzip
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    elif content_enc == "deflate":
        import zlib
        try:
            raw = zlib.decompress(raw)
        except Exception:
            try:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            except Exception:
                pass
    elif content_enc in ("br", "brotli"):
        try:
            import brotli  # type: ignore
            raw = brotli.decompress(raw)
        except ImportError:
            print(f"    WARN: brotli encoding but `pip install brotli` missing, body will be binary",
                  file=sys.stderr)
        except Exception:
            pass

    content_type = resp_headers.get("content-type", "").lower()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        import base64
        return {"status": status, "headers": resp_headers,
                "body": base64.b64encode(raw).decode("ascii"),
                "_meta": {"body_encoding": "base64", "body_size_bytes": len(raw)}}

    if "json" in content_type:
        try:
            return {"status": status, "headers": resp_headers, "body": json.loads(text),
                    "_meta": {"body_encoding": "json", "body_size_bytes": len(raw)}}
        except Exception:
            pass
    return {"status": status, "headers": resp_headers, "body": text,
            "_meta": {"body_encoding": "text", "body_size_bytes": len(raw)}}


def main() -> int:
    parser = ReplayArgumentParser(
        description="重放 snapshots → actual",
        allow_abbrev=False,
    )
    parser.add_argument("--domain", required=True)
    parser.add_argument("--target", required=True,
                        help="本方 adapter base URL, 或 'original' 重放回原站(危险)")
    parser.add_argument("--filter", default=None,
                        help="只重放 prefix 匹配的 snapshot")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--allow-original", action="store_true",
                        help="允许 --target original (默认禁用)")
    try:
        args = parser.parse_args()
    except ReplayArgumentError:
        return emit_result(refused_result())

    try:
        replay_target = parse_target(args.target)
    except ValueError as exc:
        print(f"ERROR: invalid --target: {exc}", file=sys.stderr)
        return emit_result(refused_result())
    if replay_target is None and not args.allow_original:
        print("ERROR: --target original 危险,默认禁用。加 --allow-original 才用。", file=sys.stderr)
        return emit_result(refused_result())

    try:
        fixtures_dir = resolve_fixtures_dir(args.domain)
    except ValueError as exc:
        print(f"ERROR: invalid --domain: {exc}", file=sys.stderr)
        return emit_result(refused_result())
    selected_root, snap_dir = select_fixture_layout(fixtures_dir)
    if not contained_path(selected_root, fixtures_dir) or not contained_path(
        snap_dir, fixtures_dir
    ):
        print("ERROR: selected fixture layout escapes domain fixtures", file=sys.stderr)
        return emit_result(refused_result())
    if not snap_dir.is_dir():
        print(f"ERROR: {snap_dir} not found", file=sys.stderr)
        return emit_result(ReplayResult(
            status="NO_DATA",
            exit_code=4,
            total=0,
            selected=0,
            replayed=0,
            failed=0,
            expired=0,
            no_data=True,
            actual_artifacts=(),
        ))

    req_files = sorted(snap_dir.glob("*.req.json"))
    total = len(req_files)
    selected_files = [
        req_file
        for req_file in req_files
        if not args.filter or args.filter in req_file.stem[:-4]
    ]
    selected = len(selected_files)
    filtered = total - selected
    if not selected_files:
        print(
            f"ERROR: no snapshots selected (total={total}, filter={args.filter!r})",
            file=sys.stderr,
        )
        return emit_result(ReplayResult(
            status="NO_DATA",
            exit_code=4,
            total=total,
            selected=0,
            replayed=0,
            failed=0,
            expired=0,
            no_data=True,
            actual_artifacts=(),
            filtered=filtered,
        ))

    actual_dir = selected_root / "actual"
    if not contained_path(actual_dir, selected_root) or not contained_path(
        actual_dir, fixtures_dir
    ):
        print("ERROR: actual directory escapes selected fixture root", file=sys.stderr)
        return emit_result(refused_result())
    for req_file in selected_files:
        prefix = req_file.stem[:-4]
        meta_file = snap_dir / f"{prefix}.meta.yaml"
        if not contained_path(req_file, snap_dir) or (
            meta_file.exists() and not contained_path(meta_file, snap_dir)
        ):
            print("ERROR: fixture file escapes selected snapshots root", file=sys.stderr)
            return emit_result(refused_result())

    replayed = 0
    failed = 0
    expired = 0
    actual_artifacts: list[str] = []

    for req_file in selected_files:
        prefix = req_file.stem[:-4]  # strip ".req"
        out_file = actual_dir / f"{prefix}.actual.json"

        meta_file = snap_dir / f"{prefix}.meta.yaml"
        meta = load_replay_meta(meta_file)
        if not check_expiry(meta, prefix):
            expired += 1

        try:
            req_doc = json.loads(req_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"ERROR parse {req_file.name}: {e}", file=sys.stderr)
            failed += 1
            discard_actual(out_file)
            continue

        try:
            method, original_url, headers, body = normalize_request(req_doc)
        except ValueError as e:
            print(f"ERROR request shape {req_file.name}: {e}", file=sys.stderr)
            failed += 1
            discard_actual(out_file)
            continue

        url = rewrite_url(original_url, replay_target)

        try:
            actual_doc = send_request(method, url, headers, body, args.timeout)
        except Exception as e:
            print(f"ERROR transport {req_file.name}: {e}", file=sys.stderr)
            failed += 1
            discard_actual(out_file)
            continue
        if not isinstance(actual_doc, dict) or actual_doc.get("status") == 0:
            error = (
                actual_doc.get("_meta", {}).get("error", "unknown error")
                if isinstance(actual_doc, dict)
                and isinstance(actual_doc.get("_meta"), dict)
                else "invalid transport result"
            )
            print(
                f"ERROR transport {req_file.name}: {error}",
                file=sys.stderr,
            )
            failed += 1
            discard_actual(out_file)
            continue

        replay_meta = actual_doc.get("_meta")
        if not isinstance(replay_meta, dict):
            replay_meta = {}
            actual_doc["_meta"] = replay_meta
        replay_meta["replayed_at"] = (
            datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        )
        replay_meta["replay_target"] = args.target

        try:
            write_actual_atomic(out_file, actual_doc)
        except Exception as e:
            print(f"ERROR write {out_file}: {e}", file=sys.stderr)
            failed += 1
            continue
        replayed += 1
        actual_artifacts.append(out_file.relative_to(selected_root).as_posix())

    if failed:
        status = "PARTIAL_FAILURE" if replayed else "FAILURE"
        exit_code = 3
    else:
        status = "PASS"
        exit_code = 0
    return emit_result(ReplayResult(
        status=status,
        exit_code=exit_code,
        total=total,
        selected=selected,
        replayed=replayed,
        failed=failed,
        expired=expired,
        no_data=False,
        actual_artifacts=tuple(sorted(actual_artifacts)),
        filtered=filtered,
    ))


if __name__ == "__main__":
    sys.exit(main())
