# session-index-viewer

[English](README.md) · **简体中文**

当前维护版本：**v0.1.0**。

本机浏览 AI 编程 CLI 会话的小工具。合并 **Claude Code**、**Codex**、**Devin**、
**Grok**、**Pi**、**Copilot CLI**、**opencode** 的 session，可搜索，可看 token /
工具用量（有元数据时），并可一键在新的终端窗口中 resume。

<p align="center">
  <img src="docs/screenshot.jpg" alt="Session Index Viewer：浏览并恢复 Claude Code / Codex / Devin / Grok / Pi / Copilot / opencode 会话" width="900" />
</p>

各 CLI 的 resume 列表多半只有 session ID 和时间戳，看不出当时在聊什么。本工具
展示每条 session 的开头提问和最后一次回复，方便挑中目标并接上。

> **支持 Windows 和 macOS。** Windows 优先使用 Windows Terminal，找不到
> `wt.exe` 时回退到新的 CMD 窗口；macOS 保留 Ghostty、iTerm、Terminal.app
> 自动检测。Linux 后端兼容性由 CI 覆盖，目前没有一等支持的安装器和桌面终端启动保证。

长期维护文档：[Windows 指南](docs/windows.md) ·
[兼容性矩阵](docs/compatibility.md) · [支持策略](SUPPORT.md) ·
[发布流程](RELEASE.md)。

## 运行

### Windows

PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

安装器会注册当前用户登录自启动并启动 Viewer。默认使用 Task Scheduler；注册失败时
回退到用户 Startup 文件夹。运行状态和日志放在：

```text
%LOCALAPPDATA%\session-index-viewer\
```

浏览器打开：

```text
http://127.0.0.1:7333
```

卸载：

```powershell
.\uninstall.ps1
```

只想前台运行也可以：

```powershell
py server.py
```

### macOS

```bash
./install.sh
open http://localhost:7333
```

前台运行：`python3 server.py`。

改 UI 后重建前端（可选）：

```bash
cd frontend && npm install && npm run build
```

有 `frontend/dist/` 时由 `server.py` 提供该构建；否则回退到
`sessions-index.html`。

## 支持的来源

| 来源 | 默认路径 | Resume | 用量说明 |
|------|----------|--------|----------|
| Claude Code | `~/.claude/projects/*/*.jsonl` | `claude --resume <id>` | 累加 assistant 的 `message.usage`；Context 约为单轮 input+cache 峰值 |
| Codex | `~/.codex/sessions/**/rollout-*.jsonl` | `codex resume <id>` | 取最后一次累计 `token_count`；Context 约为各轮 total 最大 |
| Devin | Windows `%APPDATA%\devin\cli\sessions.db`；macOS `~/Library/Application Support/devin/cli/sessions.db`；Linux `~/.local/share/devin/cli/sessions.db` | `devin -r <id>` | 从 `message_nodes` 聚合；支持 `DEVIN_HOME` 覆盖 |
| Grok | `$GROK_HOME/sessions`（默认 `~/.grok/sessions`） | `grok --resume <id>` | 磁盘上多为上下文占用；无头单次会话会跳过 |
| Pi | `~/.pi/agent/sessions/*/*.jsonl` | `pi --session <id>` | 累加每轮 assistant 的 `message.usage`；Context 约为各轮 total 最大 |
| Copilot CLI | `~/.copilot/session-store.db`；fallback `~/.copilot/session-state/<id>/events.jsonl` | `copilot --resume <id>` | DB 可提供完整 usage；events fallback 提供会话正文、模型、输出 token 和工具调用等可用信息 |
| opencode | `~/.local/share/opencode/opencode.db` | `opencode --session <id>` | 取 `session` 累计 token 汇总；支持 `OPENCODE_DB` / `XDG_DATA_HOME` |

平台相关的路径发现规则和 cwd 归一化细节见
[docs/compatibility.md](docs/compatibility.md)。

卡片上的 usage 是短 chip（`ctx · out · tools · turns`）。点击，或在选中卡片后
按 **`u`**，打开 modal：Overview KPI、token 分项、Activity、上下文压力条
（峰值 context 占该模型窗口上限的百分比），以及该 source 的计量口径说明。

**Context** 表示峰值 / 窗口占用，不代表整场会话的计费 total。Grok 往往只有
size 信号（chip 上标 **size only**）。

## Codex 本地图片

Codex 回复里若包含：

```text
file:///C:/Users/<user>/.codex/visualizations/...png
```

Viewer 会将其改写为受限 localhost 图片接口。接口只允许读取当前用户
`~/.codex/visualizations` 下的 PNG、JPEG、WebP、GIF、BMP，并拒绝绝对路径、
`..` 路径穿越、SVG 和超大文件。

## 键盘

| 键 | 作用 |
|----|------|
| `j` / `k` 或方向键 | 移动当前卡片 |
| `Enter` | 在终端中 resume |
| `c` | 复制 resume 命令 |
| `p` | 置顶 / 取消置顶 |
| `u` | 打开 usage modal（有用量数据时） |
| `⌘K` / `Ctrl+K` | 命令面板 |

## 各部分

- `server.py`：后端入口，监听 `127.0.0.1:7333`。
- `siv/`：仅标准库的后端：
  - `GET /` 返回页面。
  - `GET /api/sessions?limit=1000` 实时扫描 session，并按 mtime/size 缓存。
  - `POST /api/resume` 校验 source、session ID、cwd 后打开平台终端。
  - `GET /api/codex-visualization?path=...` 安全代理 Codex 本地图片。
  - Host 标签与 cwd 映射支持 macOS、Linux、Windows `C:\Users\...` 和 WSL `/mnt/c/Users/...`。
  - 解析逻辑在 `siv/sources/`。
- `frontend/`：React 卡片 UI。
- `sessions-index.html`：无 `frontend/dist` 时的单文件 fallback UI。
- `install.ps1` / `run-windows.ps1` / `uninstall.ps1`：Windows 安装、自启动、运行和卸载。
- `install.sh` / `uninstall.sh`：macOS launchd 安装与卸载。
- `.github/workflows/tests.yml`：Windows、macOS、Ubuntu 后端回归，Windows 安装烟雾测试和前端 build。

## 测试与发布门槛

Windows：

```powershell
py -m unittest discover -s tests -v
```

CI 同时覆盖 Windows、macOS、Ubuntu，并在 Windows runner 上真实执行
`install.ps1`、HTTP 健康检查、自启动注册验证和 `uninstall.ps1`。正式发布还要求
React production build 成功。维护门槛见 [SUPPORT.md](SUPPORT.md) 和
[docs/release-checklist.md](docs/release-checklist.md)。

## 多机配置

用 Syncthing 等同步 session 目录时：

| 路径 | 是否适合同步 |
|------|----------------|
| `~/.claude/projects` | 适合（按文件 jsonl） |
| `~/.codex/sessions` | 适合（按文件 jsonl） |
| `~/.grok/sessions` | 适合，建议只同步会话目录，并忽略 SQLite 索引和 `*.lock` |
| `~/.pi/agent/sessions` | 适合（按文件 jsonl） |
| Devin `sessions.db` | **不适合**，单库 SQLite 无法多机合并 |
| Copilot `session-store.db` | **不适合**，单库 SQLite 无法多机合并 |
| opencode `opencode.db` | **不适合**，单库 SQLite 无法多机合并 |

Viewer 会从 session 记录的 cwd 推导 host 标签。用户 Home 下的跨机器 cwd 可以按相对
后缀映射到当前机器 Home；本机已经存在的 `D:\...` 等路径会原样保留。

避免两台机器同时写同一个 session id，以免产生 conflict 副本。

## 维护

根目录 `VERSION` 是此 fork 的版本号来源。v0.1.0 发布说明位于
[docs/release-v0.1.0.md](docs/release-v0.1.0.md)，维护规则位于
[docs/maintenance.md](docs/maintenance.md)。
