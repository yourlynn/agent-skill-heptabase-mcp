# 開發筆記

## 架構設計

### CLI 架構（heptabase.py）
```
CLI Entry (Click)
    ↓
run_with_mcp(tool_name, tool_args)
    ↓
    ├─→ [Daemon 模式] call_via_daemon() → Unix Socket → daemon.py
    └─→ [直連模式] stdio_client → npx mcp-remote → Heptabase API
```

### Daemon 架構（daemon.py）
```
Daemon Process
    ├─→ MCP Session (persistent)
    │      ↓
    │   stdio_client → npx mcp-remote → Heptabase API
    │
    └─→ Unix Socket Server
           ↓
       handle_client(reader, writer)
           ↓
       session.call_tool(tool_name, tool_args)
```

---

## 關鍵實作細節

### 1. 統一介面設計

所有指令都透過 `run_with_mcp(tool_name, tool_args)` 執行，這個函數會：
- 檢查 `USE_DAEMON` 環境變數
- Daemon 模式 → 透過 Unix Socket 呼叫
- 直連模式 → 建立新的 MCP Session

好處：
- 所有指令邏輯一致
- 切換模式只需設定環境變數
- 容易測試和維護

### 2. Daemon 生命週期

```python
async def run(self):
    self.running = True
    PID_FILE.write_text(str(os.getpid()))  # 寫入 PID
    
    # 註冊信號處理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 同時啟動 MCP Session 和 Socket Server
    await asyncio.gather(
        self.start_mcp_session(),
        self.start_socket_server()
    )
```

### 3. Unix Socket 通訊協議

**請求格式（JSON）：**
```json
{
  "tool": "semantic_search_objects",
  "args": {
    "queries": ["關鍵字"],
    "resultObjectTypes": ["card", "journal"]
  }
}
```

**回應格式（JSON）：**
```json
{
  "result": "{ ... MCP tool result ... }"
}
```

或錯誤時：
```json
{
  "error": "Session not ready"
}
```

### 4. 錯誤處理

- **ExceptionGroup 解包**：MCP SDK 會拋出 ExceptionGroup，需要遞迴解包
- **參數驗證**：在 Click 層就驗證（關鍵字數量、頁碼範圍等）
- **連線檢查**：Daemon 模式會檢查 socket 檔案是否存在

---

## API 參數對應

| CLI 指令 | MCP Tool | 關鍵參數對應 |
|---------|----------|-------------|
| `save` | `save_to_note_card` | `content` = `# {title}\n\n{content}` |
| `search` | `semantic_search_objects` | `queries`, `resultObjectTypes` |
| `append-journal` | `append_to_journal` | `content` |
| `get` | `get_object` | `objectId`, `objectType` |
| `get-whiteboard` | `get_whiteboard_with_objects` | `whiteboardId` |
| `get-journal` | `get_journal_range` | `startDate`, `endDate` |
| `search-whiteboard` | `search_whiteboards` | `keywords` (array) |
| `search-pdf` | `search_pdf_content` | `pdfCardId`, `keywords` (array) |
| `get-pdf` | `get_pdf_pages` | `pdfCardId`, `startPageNumber`, `endPageNumber` |

---

## 待辦事項（Future Work）

### Phase 3（效能優化）
- [ ] 支援 HTTP Server 模式（替代 Unix Socket，跨機器使用）
- [ ] Token 快取機制（研究 MCP Remote 是否支援）
- [ ] 批次操作 API（一次儲存多張卡片）
- [ ] 結果快取（避免重複搜尋）

### Phase 4（功能擴充）
- [ ] 支援編輯卡片（需研究 MCP 是否支援）
- [ ] 支援刪除卡片（需研究 MCP 是否支援）
- [ ] 支援上傳圖片/檔案
- [ ] 支援建立白板
- [ ] 支援卡片之間建立連結

### Phase 5（開發者體驗）
- [ ] 互動式模式（REPL）
- [ ] 設定檔支援（`~/.heptabase-config.yaml`）
- [ ] 自動補全（bash/zsh）
- [ ] 進度條（大量操作時）

---

## 已知限制

1. **MCP Remote 限制**
   - 不支援 token 快取
   - 每次連線都需 OAuth
   - 解法：Daemon 模式

2. **Heptabase API 限制**
   - 不支援刪除/修改（只能新增）
   - 日誌查詢最多 92 天
   - PDF 頁數建議不超過 100 頁

3. **Unix Socket 限制**
   - 僅支援同機器通訊
   - 需要檔案系統權限
   - 未來可加 HTTP Server 模式

---

## 除錯技巧

### 查看 MCP Session 詳細輸出
```python
# 在 run_with_mcp 加上 debug log
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 查看 Daemon 內部狀態
```python
# 在 daemon.py handle_client 加上
print(f"收到請求：{request}", file=sys.stderr)
```

### 測試 Unix Socket 通訊
```bash
# 手動發送請求
echo '{"tool":"semantic_search_objects","args":{"queries":["測試"],"resultObjectTypes":[]}}' | \
  nc -U ~/.heptabase-daemon/daemon.sock
```

---

## 貢獻指南

1. **提交 PR 前**
   - 執行所有測試（參考 `docs/TESTING.md`）
   - 確保所有 9 個 API 都能正常運作
   - 更新相關文件（SKILL.md / README.md）

2. **程式碼風格**
   - 遵循 PEP 8
   - 使用 Type Hints
   - 函數加上 docstring

3. **文件更新**
   - 新增指令 → 更新 README.md 和 SKILL.md
   - API 變更 → 更新 docs/API-SCHEMA.md
   - 架構變更 → 更新此文件

---

**維護者：** Lynn  
**最後更新：** 2026-03-14
