# Heptabase MCP Skill 速查表

## 🚀 快速啟動

```bash
# 首次認證
heptabase auth

# 啟動 Daemon（推薦）
nohup heptabase daemon start > /tmp/heptabase-daemon.log 2>&1 &
export HEPTABASE_USE_DAEMON=true
```

---

## 📝 常用指令

### 寫入

```bash
# 儲存卡片
heptabase save --title "標題" --content "內容"

# 寫入 Journal
heptabase append-journal "今天的思考"
```

### 搜尋

```bash
# 語義搜尋（1-3 個查詢）
heptabase search "關鍵字1" "關鍵字2"
heptabase search "專案架構" --types card,webCard

# 搜尋白板（1-5 個關鍵字）
heptabase search-whiteboard "專案" "管理"

# 搜尋 PDF（需先取得 PDF ID）
heptabase search-pdf <pdf_id> "關鍵字1" "關鍵字2"
```

### 讀取

```bash
# 讀取對象
heptabase get <object_id>
heptabase get <id> --type journal

# 讀取白板
heptabase get-whiteboard <whiteboard_id>

# 讀取日誌範圍（最多 92 天）
heptabase get-journal --start-date 2026-01-01 --end-date 2026-03-14

# 讀取 PDF 頁面
heptabase get-pdf <pdf_id> --start 1 --end 10
```

### Daemon 管理

```bash
# 啟動
heptabase daemon start              # 前景
nohup heptabase daemon start ... &  # 背景

# 狀態
heptabase daemon status

# 停止
heptabase daemon stop
```

---

## 🔧 環境變數

```bash
# 使用 Daemon 模式
export HEPTABASE_USE_DAEMON=true

# 使用直連模式（預設）
export HEPTABASE_USE_DAEMON=false
# 或
unset HEPTABASE_USE_DAEMON
```

---

## 📊 工作流範例

### 研究筆記工作流

```bash
# 1. 搜尋現有筆記
heptabase search "深度學習" "Transformer"

# 2. 讀取相關白板
heptabase get-whiteboard <wb_id>

# 3. 儲存新筆記
heptabase save \
  --title "Transformer 研究" \
  --content "$(cat research.md)"

# 4. 每日總結
heptabase append-journal "研究了 Transformer attention 機制"
```

### PDF 研究工作流

```bash
# 1. 搜尋 PDF
heptabase search "論文標題" --types pdfCard

# 2. 搜尋 PDF 內容
heptabase search-pdf <pdf_id> "neural" "network"

# 3. 讀取相關頁面
heptabase get-pdf <pdf_id> --start 5 --end 10
```

---

## ⚡ 效能對比

| 模式 | 首次認證 | 後續操作 | 適用場景 |
|------|---------|---------|---------|
| 直連 | 30-120s | 30-120s | 偶爾使用 |
| Daemon | 30-120s | < 1s | 頻繁使用 |

---

## ⚠️ 限制

- 日誌範圍：單次最多 92 天
- PDF 頁數：建議不超過 100 頁
- 關鍵字數量：
  - 語義搜尋：1-3 個
  - 白板/PDF 搜尋：1-5 個
- 只能新增，無法刪除或修改

---

## 🐛 常見問題

**Q: 每次都要 OAuth？**  
A: 使用 Daemon 模式

**Q: Daemon 未啟動錯誤？**  
A: `heptabase daemon status` 檢查，然後 `daemon start`

**Q: 指令很慢？**  
A: 確認 `HEPTABASE_USE_DAEMON=true` 且 Daemon 在執行

**Q: 如何查看 Daemon log？**  
A: `tail -f /tmp/heptabase-daemon.log`

---

## 📚 完整文件

- [README.md](../README.md) — 專案說明
- [SKILL.md](../SKILL.md) — 完整使用手冊
- [API-SCHEMA.md](API-SCHEMA.md) — API 詳細規格
- [TESTING.md](TESTING.md) — 測試指南
- [DEVELOPMENT.md](DEVELOPMENT.md) — 開發筆記
