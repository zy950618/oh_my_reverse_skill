# Cherry Studio / GUI 适配

本仓库支持两种安装路径:

- CLI: 继续按 `INSTALL.md` 创建 11 个 skill 的软链 / junction。
- GUI: 通过仓库级 plugin manifest 安装，让 Cherry Studio / Claude-compatible GUI 扫描本仓库内的 `SKILL.md`。

## 当前落地边界

Observed:

- 仓库内已有 11 个 `SKILL.md`。
- 本次新增 `.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json`。
- 现有 CLI 安装方式不变。

Derived:

- GUI 应通过仓库 manifest 或导入流程生成自己的本机状态。
- GUI 本机状态里的 `contentHash`、`sourcePath`、缓存路径属于安装后的派生数据，不应提交进本仓库。

Assumed:

- Cherry Studio 使用 Claude-compatible skill / plugin 目录扫描时，会识别仓库内递归存在的 `SKILL.md`。
- 如果 Cherry Studio 版本只支持手动导入目录，则应选择本仓库根目录 `E:\SKILLS\oh_my_reverse_skill`。

Unverified:

- 本机当前没有检测到 Cherry Studio 配置目录，因此没有验证 GUI 内部 `plugins.json` 的实际字段名和缓存路径。

## GUI 安装方式

优先使用 Cherry Studio 的插件 / Skills 导入入口:

1. 选择从 GitHub 仓库或本地目录导入。
2. 仓库地址使用:

   ```text
   https://github.com/zy950618/oh_my_reverse_skill
   ```

3. 本地目录使用:

   ```text
   E:\SKILLS\oh_my_reverse_skill
   ```

4. 导入后确认 GUI 能识别以下 11 个 skill:

   ```text
   website-314-api-delivery
   reverse-js-crawler
   imperva-waf-reese84
   skills-evaluation-governance
   find-crypto-entry
   ast-deobfuscate
   env-patch
   ai-reverse-skill-creator
   karpathy-guidelines
   site-api-adapter
   captcha-service-delivery
   ```

## 验收标准

- CLI 下原有 11 个 skill 仍能通过 `~/.claude/skills/` 软链加载。
- GUI 下能识别同一组 11 个 skill。
- 不提交 Cherry Studio 本机生成的 `plugins.json`、缓存目录、`contentHash` 或绝对用户路径。
- 不把单个 GUI 的成功泛化成所有 GUI 均支持；每个 GUI 需要独立验证。

## 排查

如果 GUI 导入后只识别到部分 skill:

1. 确认导入的是仓库根目录，不是某个分层子目录。
2. 确认 `.claude-plugin/plugin.json` 存在。
3. 确认 11 个 `SKILL.md` 仍在原分层目录内。
4. 重启 GUI 后再检查 skill 列表。

如果 GUI 需要手工维护 `plugins.json`:

- 不要把本机 `plugins.json` 提交到仓库。
- 可以把 GUI 生成的条目作为 issue / PR 验证证据贴出来。
- PR 中只提交可复用的 manifest、文档、脚本或 skill 元数据。
