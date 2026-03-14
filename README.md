# Heptabase MCP Skill for OpenClaw

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一個讓 [OpenClaw](https://openclaw.ai) / [Claude Code](https://anthropic.com/claude/code) 可以操作 [Heptabase](https://heptabase.com) 的 CLI 工具。

透過 [Heptabase MCP Server](https://support.heptabase.com/en/articles/12679581-how-to-use-heptabase-mcp)，你的 AI Agent 可以：
- 💾 儲存研究筆記到 Heptabase
- 🔍 搜尋知識庫（語義搜尋、白板、PDF）
- 📓 每日總結寫入 Journal
- 📚 讀取白板與卡片內容
- ⚡ Daemon 模式（毫秒級響應，無需每次認證）

---

## 🚀 快速開始

### 1. 安裝

將此 skill 放入 OpenClaw skills 目錄：

```bash
cd ~/.openclaw/skills/
git clone https://github.com/yourusername/heptabase-mcp-skill.git heptabase
```

### 2. 首次認證

```bash
~/.openclaw/skills/heptabase/heptabase auth
```

會自動開啟瀏覽器完成 OAuth 認證。

### 3. 開始使用

```bash
# 儲存筆記
~/.openclaw/skills/heptabase/heptabase save \
  --title "今天學到的事" \
  --content "MCP 協議超好用！"

# 搜尋知識庫
~/.openclaw/skills/heptabase/heptabase search "AI Agent"

# 寫入 Journal
~/.openclaw/skills/heptabase/heptabase append-journal "今天完成了 Heptabase 整合！"
```

---

## ⚡ Daemon 模式（推薦）

直連模式每次操作都需要重新認證（30-120 秒），Daemon 模式可以保持連線，後續操作毫秒級完成。

### 啟動 Daemon

```bash
# 背景執行
nohup ~/.openclaw/skills/heptabase/heptabase daemon start > /tmp/heptabase-daemon.log 2>&1 &

# 設定環境變數
export HEPTABASE_USE_DAEMON=true
```

### 使用 Daemon

```bash
# 現在所有指令都是毫秒級！
heptabase search "關鍵字"  # < 100ms
heptabase save --title "筆記" --content "內容"  # < 100ms
```

### 管理 Daemon

```bash
# 檢查狀態
heptabase daemon status

# 停止
heptabase daemon stop
```

---

## 📖 指令參考

### 核心指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `auth` | 測試認證 | `heptabase auth` |
| `save` | 儲存卡片 | `heptabase save --title "標題" --content "內容"` |
| `search` | 語義搜尋（1-3 個查詢） | `heptabase search "關鍵字1" "關鍵字2"` |
| `append-journal` | 寫入今日日誌 | `heptabase append-journal "今天的思考"` |
| `get` | 讀取對象 | `heptabase get <id> --type card` |
| `get-whiteboard` | 讀取白板 | `heptabase get-whiteboard <id>` |
| `get-journal` | 讀取日誌範圍 | `heptabase get-journal --start-date 2026-01-01 --end-date 2026-03-14` |
| `search-whiteboard` | 搜尋白板（1-5 關鍵字） | `heptabase search-whiteboard "專案" "管理"` |
| `search-pdf` | 搜尋 PDF 內容（1-5 關鍵字） | `heptabase search-pdf <pdf_id> "關鍵字"` |
| `get-pdf` | 讀取 PDF 頁面 | `heptabase get-pdf <pdf_id> --start 1 --end 10` |

### Daemon 管理

| 指令 | 說明 |
|------|------|
| `daemon start` | 啟動 Daemon |
| `daemon stop` | 停止 Daemon |
| `daemon status` | 檢查狀態 |

---

## 🛠️ 技術架構

### 直連模式
```
CLI → npx mcp-remote → Heptabase API
     ↑ OAuth (30-120s)
```

### Daemon 模式
```
CLI → Unix Socket → Daemon (persistent MCP session) → Heptabase API
     ↑ < 100ms         ↑ OAuth once
```

### 依賴
- Python 3.8+
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Click](https://click.palletsprojects.com/)
- Node.js (for `npx`)

使用 `uv run --with` 自動管理依賴，無需手動安裝。

---

## 📚 使用範例

### 研究工作流

```bash
# 1. 搜尋現有筆記
heptabase search "深度學習" "Transformer"

# 2. 讀取相關白板
heptabase get-whiteboard <whiteboard_id>

# 3. 儲存新研究筆記
heptabase save \
  --title "Transformer 架構研究" \
  --content "$(cat research.md)"

# 4. 每日總結
heptabase append-journal "今天研究了 Transformer 的 attention 機制"
```

### PDF 研究

```bash
# 1. 搜尋 PDF
heptabase search "機器學習論文" --types pdfCard

# 2. 搜尋 PDF 內容
heptabase search-pdf <pdf_id> "neural network" "backpropagation"

# 3. 讀取相關頁面
heptabase get-pdf <pdf_id> --start 5 --end 10
```

---

## ⚠️ 限制

- **日誌範圍**：單次查詢最多 92 天
- **PDF 頁數**：建議單次不超過 100 頁
- **關鍵字數量**：
  - 語義搜尋：1-3 個查詢
  - 白板/PDF 搜尋：1-5 個關鍵字
- **寫入限制**：MCP 僅支援新增，不支援刪除或修改

---

## 🤝 貢獻

歡迎 PR！請確保：
1. 程式碼符合現有風格
2. 更新相關文件
3. 測試過所有指令

---

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE)

---

## 🔗 相關資源

- [Heptabase MCP 官方文件](https://support.heptabase.com/en/articles/12679581-how-to-use-heptabase-mcp)
- [OpenClaw](https://openclaw.ai)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

**Made with ❤️ by [Lynn](https://github.com/yourusername)**
