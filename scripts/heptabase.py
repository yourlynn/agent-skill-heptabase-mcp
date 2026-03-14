#!/usr/bin/env python3
"""
Heptabase CLI - OpenClaw Skill
與 Heptabase MCP Server 互動的命令列工具
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


TOKEN_FILE = Path.home() / ".heptabase-token.json"
MCP_SERVER_URL = "https://api.heptabase.com/mcp"
SOCKET_FILE = Path.home() / ".heptabase-daemon" / "daemon.sock"


# Daemon 模式支援
USE_DAEMON = os.environ.get("HEPTABASE_USE_DAEMON", "false").lower() == "true"


async def call_via_daemon(tool_name: str, tool_args: dict) -> str:
    """透過 Daemon 呼叫工具"""
    if not SOCKET_FILE.exists():
        click.echo("❌ Daemon 未啟動，請先執行 `heptabase daemon start`", err=True)
        click.echo("   或設定 HEPTABASE_USE_DAEMON=false 使用直連模式", err=True)
        sys.exit(1)
    
    # 連線到 Daemon
    reader, writer = await asyncio.open_unix_connection(str(SOCKET_FILE))
    
    try:
        # 發送請求
        request = {"tool": tool_name, "args": tool_args}
        writer.write(json.dumps(request).encode())
        await writer.drain()
        
        # 接收回應
        data = await reader.read(8192)
        response = json.loads(data.decode())
        
        if "error" in response:
            click.echo(f"❌ 錯誤：{response['error']}", err=True)
            sys.exit(1)
        
        return response.get("result", "{}")
    finally:
        writer.close()
        await writer.wait_closed()


async def run_with_mcp(tool_name: str, tool_args: dict) -> str:
    """使用 MCP Server 執行操作（直連或 Daemon）"""
    
    # Daemon 模式
    if USE_DAEMON:
        return await call_via_daemon(tool_name, tool_args)
    
    # 直連模式
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "mcp-remote@latest", MCP_SERVER_URL, "--transport", "http-only"],
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                click.echo("正在進行 OAuth 認證，請在瀏覽器完成登入...", err=True)
                await session.initialize()
                
                # 執行工具
                result = await session.call_tool(tool_name, tool_args)
                return result.content[0].text if result.content else "{}"
    except BaseException as e:
        # 遞迴解包 ExceptionGroup
        def unwrap(exc, depth=0):
            prefix = "  " * depth
            if isinstance(exc, (ExceptionGroup, BaseExceptionGroup)):
                click.echo(f"{prefix}ExceptionGroup ({len(exc.exceptions)} sub-exceptions):", err=True)
                for sub in exc.exceptions:
                    unwrap(sub, depth + 1)
            else:
                click.echo(f"{prefix}{type(exc).__name__}: {exc}", err=True)
        
        click.echo("錯誤詳情:", err=True)
        unwrap(e)
        sys.exit(1)


# CLI Commands

@click.group()
def cli():
    """Heptabase CLI - 透過 MCP 操作 Heptabase"""
    pass


@cli.command()
def auth():
    """進行 OAuth 認證（測試連線）"""
    
    async def _auth():
        # 強制使用直連模式測試認證
        global USE_DAEMON
        old_daemon = USE_DAEMON
        USE_DAEMON = False
        
        try:
            # 使用 semantic_search 測試連線（空結果也 OK）
            await run_with_mcp("semantic_search_objects", {
                "queries": ["test"],
                "resultObjectTypes": []
            })
            click.echo("✅ 認證成功！", err=True)
        finally:
            USE_DAEMON = old_daemon
    
    asyncio.run(_auth())


@cli.command()
@click.option('--title', required=True, help='卡片標題')
@click.option('--content', required=True, help='卡片內容（Markdown 格式）')
def save(title: str, content: str):
    """儲存內容到 Heptabase 卡片"""
    
    # 組合成 Markdown（第一行必須是 h1）
    markdown_content = f"# {title}\n\n{content}"
    
    async def _save():
        click.echo(f"正在儲存卡片：{title}", err=True)
        output = await run_with_mcp("save_to_note_card", {"content": markdown_content})
        click.echo("✅ 儲存成功！", err=True)
        click.echo(output)
    
    asyncio.run(_save())


@cli.command()
@click.argument('queries', nargs=-1, required=True)
@click.option('--types', 'object_types',
              default='card,journal,webCard',
              help='對象類型（逗號分隔，留空搜尋全部）')
def search(queries, object_types: str):
    """語義搜尋（1-3 個查詢）"""
    
    if len(queries) > 3:
        click.echo("❌ 查詢數量不能超過 3 個", err=True)
        sys.exit(1)
    
    # 解析對象類型
    types_list = [t.strip() for t in object_types.split(',') if t.strip()] if object_types else []
    
    async def _search():
        click.echo(f"正在搜尋：{', '.join(queries)}", err=True)
        output = await run_with_mcp("semantic_search_objects", {
            "queries": list(queries),
            "resultObjectTypes": types_list
        })
        click.echo("✅ 搜尋完成！", err=True)
        click.echo(output)
    
    asyncio.run(_search())


@cli.command()
@click.argument('content')
def append_journal(content: str):
    """附加內容到今日日誌"""
    
    async def _append():
        click.echo("正在附加到今日日誌...", err=True)
        output = await run_with_mcp("append_to_journal", {"content": content})
        click.echo("✅ 附加成功！", err=True)
        click.echo(output)
    
    asyncio.run(_append())


@cli.command()
@click.argument('object_id')
@click.option('--type', 'object_type', 
              type=click.Choice(['card', 'journal', 'videoCard', 'audioCard', 'imageCard',
                                'highlightElement', 'textElement', 'videoElement', 'imageElement',
                                'chat', 'chatMessage', 'chatMessagesElement', 'webCard', 'section']),
              default='card',
              help='對象類型')
def get(object_id: str, object_type: str):
    """讀取特定對象（卡片/日誌/元素）"""
    
    async def _get():
        click.echo(f"正在讀取對象：{object_id} ({object_type})", err=True)
        output = await run_with_mcp("get_object", {
            "objectId": object_id,
            "objectType": object_type
        })
        click.echo("✅ 讀取完成！", err=True)
        click.echo(output)
    
    asyncio.run(_get())


@cli.command()
@click.argument('whiteboard_id')
def get_whiteboard(whiteboard_id: str):
    """讀取白板及其上的所有對象"""
    
    async def _get_wb():
        click.echo(f"正在讀取白板：{whiteboard_id}", err=True)
        output = await run_with_mcp("get_whiteboard_with_objects", {
            "whiteboardId": whiteboard_id
        })
        click.echo("✅ 讀取完成！", err=True)
        click.echo(output)
    
    asyncio.run(_get_wb())


@cli.command()
@click.option('--start-date', required=True, help='開始日期 (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='結束日期 (YYYY-MM-DD)')
def get_journal(start_date: str, end_date: str):
    """讀取日誌範圍（最多 92 天）"""
    
    async def _get_journal():
        click.echo(f"正在讀取日誌：{start_date} ~ {end_date}", err=True)
        output = await run_with_mcp("get_journal_range", {
            "startDate": start_date,
            "endDate": end_date
        })
        click.echo("✅ 讀取完成！", err=True)
        click.echo(output)
    
    asyncio.run(_get_journal())


@cli.command()
@click.argument('keywords', nargs=-1, required=True)
def search_whiteboard(keywords):
    """搜尋白板（1-5 個關鍵字）"""
    
    if len(keywords) > 5:
        click.echo("❌ 關鍵字數量不能超過 5 個", err=True)
        sys.exit(1)
    
    async def _search_wb():
        click.echo(f"正在搜尋白板：{', '.join(keywords)}", err=True)
        output = await run_with_mcp("search_whiteboards", {
            "keywords": list(keywords)
        })
        click.echo("✅ 搜尋完成！", err=True)
        click.echo(output)
    
    asyncio.run(_search_wb())


@cli.command()
@click.argument('pdf_card_id')
@click.argument('keywords', nargs=-1, required=True)
def search_pdf(pdf_card_id: str, keywords):
    """搜尋 PDF 內容（1-5 個關鍵字）"""
    
    if len(keywords) > 5:
        click.echo("❌ 關鍵字數量不能超過 5 個", err=True)
        sys.exit(1)
    
    async def _search_pdf():
        click.echo(f"正在搜尋 PDF {pdf_card_id}：{', '.join(keywords)}", err=True)
        output = await run_with_mcp("search_pdf_content", {
            "pdfCardId": pdf_card_id,
            "keywords": list(keywords)
        })
        click.echo("✅ 搜尋完成！", err=True)
        click.echo(output)
    
    asyncio.run(_search_pdf())


@cli.command()
@click.argument('pdf_card_id')
@click.option('--start', 'start_page', type=int, required=True, help='起始頁碼（從 1 開始）')
@click.option('--end', 'end_page', type=int, required=True, help='結束頁碼（包含）')
def get_pdf(pdf_card_id: str, start_page: int, end_page: int):
    """讀取 PDF 特定頁面"""
    
    if start_page < 1:
        click.echo("❌ 起始頁碼必須 >= 1", err=True)
        sys.exit(1)
    
    if end_page < start_page:
        click.echo("❌ 結束頁碼必須 >= 起始頁碼", err=True)
        sys.exit(1)
    
    async def _get_pdf():
        click.echo(f"正在讀取 PDF {pdf_card_id} 第 {start_page}-{end_page} 頁", err=True)
        output = await run_with_mcp("get_pdf_pages", {
            "pdfCardId": pdf_card_id,
            "startPageNumber": start_page,
            "endPageNumber": end_page
        })
        click.echo("✅ 讀取完成！", err=True)
        click.echo(output)
    
    asyncio.run(_get_pdf())


@cli.group()
def daemon():
    """Daemon 模式管理"""
    pass


@daemon.command(name="start")
def daemon_start():
    """啟動 Daemon（背景模式請用 nohup）"""
    import subprocess
    daemon_script = Path(__file__).parent / "daemon.py"
    subprocess.run([sys.executable, str(daemon_script), "start"])


@daemon.command(name="stop")
def daemon_stop():
    """停止 Daemon"""
    import subprocess
    daemon_script = Path(__file__).parent / "daemon.py"
    subprocess.run([sys.executable, str(daemon_script), "stop"])


@daemon.command(name="status")
def daemon_status():
    """檢查 Daemon 狀態"""
    import subprocess
    daemon_script = Path(__file__).parent / "daemon.py"
    subprocess.run([sys.executable, str(daemon_script), "status"])


if __name__ == "__main__":
    cli()
