# Heptabase MCP Skill 測試指南

## 測試 Daemon 模式

### 1. 啟動 Daemon（前景測試）

```bash
cd ~/.openclaw/skills/heptabase
./heptabase daemon start
```

**預期結果：**
- 顯示 "正在啟動 MCP Session..."
- 自動開啟瀏覽器進行 OAuth 認證
- 認證完成後顯示 "✅ MCP Session 已建立！"
- 顯示 "✅ Socket Server 已啟動：/Users/xxx/.heptabase-daemon/daemon.sock"

### 2. 測試 Daemon 狀態（另開 terminal）

```bash
cd ~/.openclaw/skills/heptabase
./heptabase daemon status
```

**預期結果：**
```
✅ Daemon 正在執行（PID: 12345）
   Socket: /Users/xxx/.heptabase-daemon/daemon.sock
```

### 3. 測試 Daemon 模式操作

```bash
# 設定使用 Daemon
export HEPTABASE_USE_DAEMON=true

# 測試搜尋（應該毫秒級完成）
time ./heptabase search "測試"

# 測試儲存
./heptabase save --title "Daemon 測試" --content "測試 Daemon 模式"

# 測試寫入 Journal
./heptabase append-journal "測試 Daemon 模式寫入 Journal"
```

**預期結果：**
- 所有操作在 < 1 秒內完成（直連模式需 30-120 秒）
- 沒有 "正在進行 OAuth 認證" 訊息
- 正常回傳結果

### 4. 停止 Daemon

```bash
./heptabase daemon stop
```

**預期結果：**
```
✅ 已發送停止信號給 Daemon（PID: 12345）
```

前景執行的 terminal 會顯示：
```
正在關閉 Daemon...
✅ Daemon 已關閉
```

---

## 測試直連模式

### 1. 確保 Daemon 未執行

```bash
./heptabase daemon status
# 應顯示：❌ Daemon 未在執行
```

### 2. 取消 Daemon 環境變數

```bash
unset HEPTABASE_USE_DAEMON
```

### 3. 測試各指令

#### 認證測試
```bash
./heptabase auth
```

**預期：** 開啟瀏覽器 → OAuth → "✅ 認證成功！"

#### 儲存卡片
```bash
./heptabase save \
  --title "測試卡片" \
  --content "這是測試內容\n\n支援 Markdown"
```

**預期：** OAuth → "✅ 儲存成功！" → 回傳 JSON（包含 card ID）

#### 搜尋
```bash
./heptabase search "測試"
```

**預期：** OAuth → "✅ 搜尋完成！" → 回傳搜尋結果 JSON

#### 寫入 Journal
```bash
./heptabase append-journal "今天測試了 Heptabase Skill"
```

**預期：** OAuth → "✅ 附加成功！" → 回傳結果

---

## 測試完整 API 支援

### 讀取對象
```bash
# 需先透過 search 取得 object ID
CARD_ID="<從搜尋結果取得>"
./heptabase get "$CARD_ID" --type card
```

### 讀取白板
```bash
# 需先透過 search-whiteboard 取得 whiteboard ID
WB_ID="<從搜尋結果取得>"
./heptabase get-whiteboard "$WB_ID"
```

### 讀取日誌範圍
```bash
./heptabase get-journal \
  --start-date 2026-03-01 \
  --end-date 2026-03-14
```

### 搜尋白板
```bash
./heptabase search-whiteboard "專案" "管理"
```

### 搜尋 PDF 內容
```bash
# 需先取得 PDF card ID
PDF_ID="<從搜尋結果取得>"
./heptabase search-pdf "$PDF_ID" "關鍵字1" "關鍵字2"
```

### 讀取 PDF 頁面
```bash
./heptabase get-pdf "$PDF_ID" --start 1 --end 5
```

---

## 效能對比測試

### 直連模式
```bash
unset HEPTABASE_USE_DAEMON
time ./heptabase search "測試"
```

**預期：** 30-120 秒

### Daemon 模式
```bash
# 確保 Daemon 已啟動
./heptabase daemon start &
sleep 60  # 等待 OAuth 完成

export HEPTABASE_USE_DAEMON=true
time ./heptabase search "測試"
```

**預期：** < 1 秒

---

## 錯誤處理測試

### 1. Daemon 未啟動時使用 Daemon 模式

```bash
export HEPTABASE_USE_DAEMON=true
./heptabase daemon stop  # 確保停止
./heptabase search "測試"
```

**預期：**
```
❌ Daemon 未啟動，請先執行 `heptabase daemon start`
   或設定 HEPTABASE_USE_DAEMON=false 使用直連模式
```

### 2. 參數驗證

```bash
# 關鍵字過多（搜尋白板限制 5 個）
./heptabase search-whiteboard "1" "2" "3" "4" "5" "6"
```

**預期：** "❌ 關鍵字數量不能超過 5 個"

```bash
# 查詢過多（語義搜尋限制 3 個）
./heptabase search "1" "2" "3" "4"
```

**預期：** "❌ 查詢數量不能超過 3 個"

```bash
# PDF 起始頁碼錯誤
./heptabase get-pdf "$PDF_ID" --start 0 --end 5
```

**預期：** "❌ 起始頁碼必須 >= 1"

---

## 清理測試資料

測試完成後，可在 Heptabase 手動刪除測試卡片（MCP 不支援刪除）。

---

## 常見問題

### Q: OAuth 每次都需要重新登入？
A: 是的，這是 MCP Remote 的限制。解決方案是使用 Daemon 模式。

### Q: Daemon 背景執行如何查看 log？
A: 使用 `nohup ... > /tmp/heptabase-daemon.log 2>&1 &`，然後 `tail -f /tmp/heptabase-daemon.log`

### Q: 如何確認 Daemon 真的在使用？
A: 觀察執行時間和訊息，Daemon 模式不會顯示 "正在進行 OAuth 認證"

---

**測試檢查表：**
- [ ] 直連模式：auth, save, search, append-journal
- [ ] Daemon 啟動/停止/狀態
- [ ] Daemon 模式：所有指令
- [ ] 效能對比（直連 vs Daemon）
- [ ] 錯誤處理
- [ ] 完整 9 個 API 都有測試
