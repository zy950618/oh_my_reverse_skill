# INSTALL — 安装指南

> 一站式安装。从零到能用大约 5-10 分钟,加上 CloakBrowser 二进制下载额外 3-5 分钟。
>
> 别的入口:[USAGE](./USAGE.md) 使用 · [TRIGGERS](./TRIGGERS.md) 触发词速查 · [CHERRY_STUDIO](./CHERRY_STUDIO.md) GUI 适配

---

## 前置

| 依赖 | 版本 | 用途 |
|---|---|---|
| **git** | 任意 | clone 仓库 |
| **Python** | 3.11+ | 跑 tools/ 下的脚本 + 评分 |
| **Claude Code** | 最新 | 加载 Skills,运行 hooks |
| **管理员权限**(Windows) | - | 创建 junction 软链(普通 mklink 不需要) |

可选(只在用对应功能时装):

| 依赖 | 用途 |
|---|---|
| **cloakbrowser** | 录 fixtures(反爬严的站点);否则用 Chrome DevTools 导 HAR 也行 |
| **pyyaml** | 部分脚本(评分本身不强依赖,但解析 meta.yaml 更准) |

---

## 完整步骤

### GUI / Cherry Studio

如果使用 Cherry Studio 或其他 Claude-compatible GUI,先看 [CHERRY_STUDIO.md](./CHERRY_STUDIO.md)。本仓库提供 `.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json`;GUI 导入后生成的本机 `plugins.json`、`contentHash`、`sourcePath` 不提交到仓库。

### Step 1: clone 仓库

```bash
git clone <repo-url> ~/SKILLS/oh_my_reverse_skill
cd ~/SKILLS/oh_my_reverse_skill
```

Windows:

```powershell
git clone <repo-url> E:\SKILLS\oh_my_reverse_skill
cd E:\SKILLS\oh_my_reverse_skill
```

### Step 2: 软链 active Skill 到 ~/.claude/skills/

Claude Code 默认从 `~/.claude/skills/` 加载 Skill,本仓库分层放在子目录里,需要软链回去。active Skill inventory 以根目录 `skills-manifest.json` 为单一来源；先跑 `python3 tools/skills_manifest.py validate` 确认当前工作树一致。

#### Windows (PowerShell)

> 必须用管理员权限运行 PowerShell,否则 New-Item Junction 会失败。

```powershell
python3 tools/skills_manifest.py emit-install --shell powershell --repo "E:\SKILLS\oh_my_reverse_skill" --dst "$env:USERPROFILE\.claude\skills"
# 检查输出无误后,复制执行输出的 New-Item 命令。
```

#### macOS / Linux

```bash
REPO="$HOME/SKILLS/oh_my_reverse_skill"   # 改成你本地实际路径
DST="$HOME/.claude/skills"
python3 tools/skills_manifest.py emit-install --shell bash --repo "$REPO" --dst "$DST"
# 检查输出无误后,复制执行输出的 ln -snf 命令。
```

### Step 3: (可选) 装 CloakBrowser 录 fixtures

只有要做一致性验证 fixtures 录制时才需要。**反爬不严的站点可以跳过这步,用 Chrome DevTools 导 HAR 即可**(见 [07 一致性验证规约 Step 1B](./99-SKILLS治理/07-一致性验证规约.md))。

```bash
pip install cloakbrowser
python3 -m cloakbrowser install   # 下载浏览器二进制,3-5 分钟
python3 -m cloakbrowser info      # 验证装好
```

可选装 pyyaml(让评分脚本更准地解析 meta.yaml):

```bash
pip install pyyaml
```

### Step 4: 装 hooks

本仓库默认在项目级 `.claude/settings.json` 注册了 Stop hook(任务结束扫 transcript 提醒沉淀)。

**项目级** (默认,推荐) — 已经装好,无需操作。只在 cwd 在本仓库内时触发,不污染其他项目。

**跨项目级** (可选,有副作用) — 在外部项目工作时也想触发提醒,把下面这段加到 `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"E:/SKILLS/oh_my_reverse_skill/tools/lifecycle/post_task_reminder.py\""
          }
        ]
      }
    ]
  }
}
```

> 副作用:**所有项目的 Stop 事件都会跑这个 hook**。脚本异常时退出码 0 静默,不影响主任务,但还是会多一次 fork。
>
> Windows 上 `python` 不在 PATH 时改成 `py`。

### Step 5: 验证安装

#### Unix / macOS / Git Bash

```bash
# 1. 检查 Skills 软链
ls ~/.claude/skills/ | grep -E '(website-|reverse-js|imperva|authorized-target|web-h5-loop|find-crypto|ast-|env-patch|js-page-runtime|karpathy|site-api|ai-reverse|skills-evaluation|browser-fingerprint|fingerprint-block)'
python3 tools/skills_manifest.py summary

# 2. 跑评分(应该不报错)
cd ~/SKILLS/oh_my_reverse_skill   # 或 E:\SKILLS\oh_my_reverse_skill
python3 1-业务流程层/skills-evaluation-governance/scripts/score_skills.py --manifest skills-manifest.json --output .ci-out/manifest.json
# 应该输出 JSON；active Skill 数量以 manifest summary 输出为准

# 3. 跑 fixtures 验证(空仓库,应该 PASS)
python3 tools/replayer/validate_fixtures.py
# 应该输出: domains: 0  snapshots: 0  ... all good.

# 4. 重启 Claude Code, 在仓库目录内打开
# 输入 "/" 应该能看到所有 Skill
# 输入 "逆向" 等关键词时, Claude 会自动加载触发的 Skill
```

#### Windows PowerShell

```powershell
# 1. 检查 Skills 软链 (数量以 manifest summary 输出为准)
(Get-ChildItem "$env:USERPROFILE\.claude\skills" -Directory).Count
python3 tools/skills_manifest.py summary

# 2. 跑评分
cd E:\SKILLS\oh_my_reverse_skill
python3 1-业务流程层/skills-evaluation-governance/scripts/score_skills.py --manifest skills-manifest.json --output .ci-out/manifest.json

# 3. 跑 fixtures 验证
python3 tools\replayer\validate_fixtures.py

# 4. 重启 Claude Code
```

#### Windows cmd

```cmd
:: 1. 检查 Skills 软链
dir "%USERPROFILE%\.claude\skills" /B | find /C /V ""

:: 2. 跑评分
cd /d E:\SKILLS\oh_my_reverse_skill
python3 1-业务流程层/skills-evaluation-governance/scripts/score_skills.py --manifest skills-manifest.json --output .ci-out/manifest.json

:: 3. 跑 fixtures 验证
python3 tools\replayer\validate_fixtures.py
```

---

## 升级

```bash
cd ~/SKILLS/oh_my_reverse_skill
git pull
# 软链指向本仓库目录,git pull 后自动生效。Skills 内容已更新。
```

---

## 卸载

卸载只删除 `skills-manifest.json` 中本仓库 installable skills 对应、且 target 指向本仓库的链接 / junction；不删除仓库本体，也不清空 `~/.claude/skills/` 中其他来源的 skill。

```powershell
# Windows (PowerShell): 只删除 manifest 中本仓库 installable skills 对应、且 Target 指向本仓库的 junction。
$Repo = (Resolve-Path "E:\SKILLS\oh_my_reverse_skill").Path   # 改成你本地实际路径
$Dst = Join-Path $env:USERPROFILE ".claude\skills"
python3 tools/skills_manifest.py list-skills --names --installable | ForEach-Object {
  $Path = Join-Path $Dst $_
  if (Test-Path $Path) {
    $Item = Get-Item $Path -Force
    $Targets = @($Item.Target)
    if ($Item.LinkType -eq "Junction" -and ($Targets | Where-Object { $_ -like "$Repo*" })) {
      Remove-Item $Path -Force
    }
  }
}
```

```bash
# macOS / Linux: 只删除 manifest 中本仓库 installable skills 对应、且 target 指向本仓库的 symlink。
REPO="$(cd "$HOME/SKILLS/oh_my_reverse_skill" && pwd -P)"   # 改成你本地实际路径
DST="$HOME/.claude/skills"
python3 tools/skills_manifest.py list-skills --names --installable | while IFS= read -r n; do
  target="$DST/$n"
  if [ -L "$target" ]; then
    link_target="$(readlink "$target")"
    case "$link_target" in
      "$REPO"/*) rm "$target" ;;
      *) printf 'skip non-repo skill link: %s -> %s\n' "$target" "$link_target" ;;
    esac
  fi
done
```

仓库目录本身只有在确认没有唯一证据、经验库、本地抓包和未迁移 ledger 后，才可以手动删除，例如 `rm -rf ~/SKILLS/oh_my_reverse_skill`。

---

## 常见问题

### Q1: Windows 创建 Junction 报权限错

A: 用**管理员**身份打开 PowerShell。普通用户没权限创建 Junction(虽然 mklink /J 在 cmd 里 Win10+ 可以)。

替代方案:用 mklink /J:

```cmd
mklink /J "%USERPROFILE%\.claude\skills\find-crypto-entry" "E:\SKILLS\oh_my_reverse_skill\2-JS逆向工具层\find-crypto-entry"
```

### Q2: Python 命令找不到(Windows Store 版 Python)

A: macOS / Linux 示例统一用 `python3`。Windows Store 装的 Python 可能叫 `py`；如需用户级 hook,把配置里的 `python3` 显式改成 `py`。

### Q3: cloakbrowser 装失败

A: 常见原因:
- 国内网络问题 → 设代理 `pip install --proxy http://... cloakbrowser`
- Python 版本 < 3.8 → 升级到 3.11+
- `python3 -m cloakbrowser install` 下载二进制失败 → 设环境变量代理或重试

跳过 CloakBrowser 也能用 90% 功能 — 一致性验证用 HAR 导入(har_to_fixtures.py)就行。

### Q4: Hook 没触发(任务结束没看到沉淀提醒)

A: 三个原因:
1. cwd 不在仓库内 → 项目级 hook 只在仓库内触发,跨项目要装用户级(Step 4)
2. python3 不在 PATH → 见 Q2
3. 对话里没出现"逆向 / sign / crawler / waf"等 marker → hook 只对逆向任务触发,通用问题不打扰

debug:看 `tools/.reminder-stats.jsonl` 是否有新行(每次 hook 触发都会写)。

### Q5: 跑 score_skills.py 报 Windows 中文乱码

A: 仓库 score_skills.py 已经 `sys.stdout.reconfigure(encoding="utf-8")`。如果还乱码,改环境变量:

```cmd
set PYTHONIOENCODING=utf-8
```

或 PowerShell:

```powershell
$env:PYTHONIOENCODING="utf-8"
```

### Q6: 软链装好了但 Claude 看不到 Skill

A: 关闭重开 Claude Code。Skill 加载在启动时扫描 `~/.claude/skills/`,运行中改不生效。

### Q7: 怎么知道某次任务 Claude 用了哪些 Skill

A: 看 Claude 回复里 `Skill(...)` 调用块,或在仓库外跑:

```bash
grep -c "Skill(" ~/.claude/projects/<sanitized-cwd>/conversation.jsonl
```

### Q8: CI 跑不动(GitHub Actions)

A: `.github/workflows/skill-bench.yml` 和 `consistency-replay.yml` 默认配置应该开箱即用。问题排查:
- Repo permissions: Settings → Actions → 给 Actions read+write 权限
- consistency-replay.yml 的 replay-diff job 需要 ADAPTER_BASE_URL secret 或 workflow_dispatch 输入。否则只跑 validate-schema

---

## 验证清单

装完跑一遍:

- [ ] `ls ~/.claude/skills/` 能看到本仓库 active Skill 软链（数量以 `python3 tools/skills_manifest.py summary` 输出为准）
- [ ] `python3 --version` ≥ 3.11
- [ ] `python3 tools/skills_manifest.py validate` 通过
- [ ] `python3 1-业务流程层/skills-evaluation-governance/scripts/score_skills.py --manifest skills-manifest.json --output .ci-out/manifest.json` 不报错
- [ ] `python3 tools/replayer/validate_fixtures.py` 输出 `all good`
- [ ] `cat .claude/settings.json` 有 Stop hook 配置
- [ ] Claude Code 启动,仓库目录内输入 `/逆向` 能匹配到 Skill
- [ ] (可选) `python3 -m cloakbrowser info` 显示版本号
