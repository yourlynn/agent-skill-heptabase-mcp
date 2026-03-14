#!/usr/bin/env python3
"""
Heptabase Daemon - 持久化 MCP Session
保持連線以避免每次都重新認證
"""

import asyncio
import json
import os
import signal
import sys
from pathlib import Path
from typing import Optional

import click
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# 設定檔案
DAEMON_DIR = Path.home() / ".heptabase-daemon"
PID_FILE = DAEMON_DIR / "daemon.pid"
SOCKET_FILE = DAEMON_DIR / "daemon.sock"
MCP_SERVER_URL = "https://api.heptabase.com/mcp"


class HeptabaseDaemon:
    """Heptabase Daemon 主程式"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.running = False
        self.server = None
        
    async def start_mcp_session(self):
        """啟動 MCP Session"""
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "mcp-remote@latest", MCP_SERVER_URL, "--transport", "http-only"],
        )
        
        print("正在啟動 MCP Session...", file=sys.stderr)
        print("首次啟動需要 OAuth 認證，請在瀏覽器完成登入...", file=sys.stderr)
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.session = session
                print("✅ MCP Session 已建立！", file=sys.stderr)
                
                # 保持連線
                while self.running:
                    await asyncio.sleep(1)
    
    async def handle_client(self, reader, writer):
        """處理客戶端請求"""
        try:
            # 讀取請求
            data = await reader.read(8192)
            request = json.loads(data.decode())
            
            # 執行 MCP 工具
            tool_name = request.get("tool")
            tool_args = request.get("args", {})
            
            if not self.session:
                response = {"error": "Session not ready"}
            else:
                try:
                    result = await self.session.call_tool(tool_name, tool_args)
                    output = result.content[0].text if result.content else "{}"
                    response = {"result": output}
                except Exception as e:
                    response = {"error": str(e)}
            
            # 回傳結果
            writer.write(json.dumps(response).encode())
            await writer.drain()
            
        except Exception as e:
            print(f"處理請求時發生錯誤：{e}", file=sys.stderr)
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def start_socket_server(self):
        """啟動 Unix Socket Server"""
        # 確保目錄存在
        DAEMON_DIR.mkdir(parents=True, exist_ok=True)
        
        # 刪除舊的 socket
        if SOCKET_FILE.exists():
            SOCKET_FILE.unlink()
        
        # 啟動 server
        self.server = await asyncio.start_unix_server(
            self.handle_client,
            path=str(SOCKET_FILE)
        )
        
        print(f"✅ Socket Server 已啟動：{SOCKET_FILE}", file=sys.stderr)
        
        async with self.server:
            await self.server.serve_forever()
    
    async def run(self):
        """主執行流程"""
        self.running = True
        
        # 確保目錄存在
        DAEMON_DIR.mkdir(parents=True, exist_ok=True)
        
        # 寫入 PID
        PID_FILE.write_text(str(os.getpid()))
        
        # 註冊信號處理
        def signal_handler(sig, frame):
            print("\n正在關閉 Daemon...", file=sys.stderr)
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # 同時啟動 MCP Session 和 Socket Server
            await asyncio.gather(
                self.start_mcp_session(),
                self.start_socket_server()
            )
        except Exception as e:
            print(f"❌ Daemon 發生錯誤：{e}", file=sys.stderr)
        finally:
            # 清理
            if PID_FILE.exists():
                PID_FILE.unlink()
            if SOCKET_FILE.exists():
                SOCKET_FILE.unlink()
            print("✅ Daemon 已關閉", file=sys.stderr)


# CLI Commands

@click.group()
def cli():
    """Heptabase Daemon 管理"""
    pass


@cli.command()
def start():
    """啟動 Daemon（前景執行）"""
    
    # 檢查是否已在執行
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        try:
            os.kill(pid, 0)  # 檢查 process 是否存在
            click.echo(f"❌ Daemon 已在執行中（PID: {pid}）")
            sys.exit(1)
        except OSError:
            # Process 不存在，清理舊檔案
            PID_FILE.unlink()
    
    # 啟動 Daemon
    daemon = HeptabaseDaemon()
    asyncio.run(daemon.run())


@cli.command()
def stop():
    """停止 Daemon"""
    
    if not PID_FILE.exists():
        click.echo("❌ Daemon 未在執行")
        sys.exit(1)
    
    pid = int(PID_FILE.read_text())
    
    try:
        os.kill(pid, signal.SIGTERM)
        click.echo(f"✅ 已發送停止信號給 Daemon（PID: {pid}）")
    except OSError:
        click.echo(f"❌ 無法停止 Daemon（PID: {pid}）")
        # 清理殘留檔案
        PID_FILE.unlink()
        if SOCKET_FILE.exists():
            SOCKET_FILE.unlink()


@cli.command()
def status():
    """檢查 Daemon 狀態"""
    
    if not PID_FILE.exists():
        click.echo("❌ Daemon 未在執行")
        sys.exit(1)
    
    pid = int(PID_FILE.read_text())
    
    try:
        os.kill(pid, 0)  # 檢查 process 是否存在
        click.echo(f"✅ Daemon 正在執行（PID: {pid}）")
        click.echo(f"   Socket: {SOCKET_FILE}")
    except OSError:
        click.echo(f"❌ Daemon 異常（PID 檔案存在但 process 不存在）")
        # 清理殘留檔案
        PID_FILE.unlink()
        if SOCKET_FILE.exists():
            SOCKET_FILE.unlink()


async def call_daemon(tool_name: str, tool_args: dict) -> dict:
    """透過 Daemon 呼叫工具"""
    
    if not SOCKET_FILE.exists():
        raise RuntimeError("Daemon 未啟動，請先執行 `heptabase daemon start`")
    
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
        
        return response
    finally:
        writer.close()
        await writer.wait_closed()


if __name__ == "__main__":
    cli()
