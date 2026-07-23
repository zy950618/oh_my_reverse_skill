# RunContext 与 artifact provenance

此目录提供标准库实现的共享基础设施，用于把命令和产物绑定到同一个
`run_id`、`producer`、`target` 与输入哈希集合。它不是 Runtime、
Orchestrator、事件日志器、浏览器/MCP adapter 或外部服务能力。

## 信任边界

- 命令的 stdout/stderr 和 artifact 均按原始字节计算 SHA-256。
- 时间使用带显式 UTC offset 的严格 RFC3339 格式。
- artifact 只能是仓库根目录内的相对路径普通文件；目录、符号链接、缺失文件和
  越界路径均拒绝。
- manifest 不包含自身 digest，也不能自证。验证者必须从不可变控制面、签名记录
  或其他外部可信通道取得 `trusted_manifest_sha256` 并显式传入。
- JSON 必须是严格 UTF-8、无重复键、无 NaN/Infinity，并使用确定性紧凑序列化。
- authorization、cookie、secret、token、API key、password 以及 URL query
  中的敏感参数会被拒绝；面向调用者的辅助脱敏只产生固定 `[REDACTED]`，异常不会
  回显原值。

## 最小用法

```python
import hashlib

from run_context import RunContext
from artifact_manifest import create_artifact_record, build_manifest, validate_manifest

inputs = {"request.bin": hashlib.sha256(open("request.bin", "rb").read()).hexdigest()}
run = RunContext("run-20260723-001", "local-generator", "result.bin")
run.run(["python3", "generator.py"], cwd=".", input_hashes=inputs)

artifact = create_artifact_record(
    ".",
    "result.bin",
    producer_run_id=run.run_id,
    producer=run.producer,
    target=run.target,
    input_hashes=inputs,
)
manifest = build_manifest([run.to_dict()], [artifact], ".")
trusted_digest = hashlib.sha256(manifest).hexdigest()  # 交给外部可信通道保存
validate_manifest(manifest, ".", trusted_manifest_sha256=trusted_digest)
```

调用者必须自行验证 `input_hashes` 对应的输入文件和可信 digest 的来源。此层只保存
并校验绑定关系，不执行命令白名单、网络访问、调度、重试、事件持久化或能力声明。

## 测试

```bash
python3 -B -m unittest discover -s tools/runtime/tests -p "test_*.py" -v
```
