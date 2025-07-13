from Config.logger import logger
import websockets
import json
import asyncio
from typing import Optional, Dict, Any

class WsClient:
    def __init__(self, api: str, port: int, wxid: str):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected: bool = False
        self.reconnect_delay: int = 5  # 重连延迟时间（秒）
        self._reconnect_task: Optional[asyncio.Task] = None
        self.message_handlers = []
        self.ws_url = f'ws://{api}:{port}/ws/{wxid}'
        logger.debug(f"WebSocket URL: {self.ws_url}")

    async def handle_message(self, message: str) -> None:
        """
        处理接收到的消息
        """
        try:
            data = json.loads(message)
            logger.debug(f"ws收到消息: {data}")
            # 调用所有注册的消息处理器
            for handler in self.message_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"消息处理器错误: {e}", exc_info=True)
        except json.JSONDecodeError as e:
            logger.error(f"消息解析失败: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"消息处理错误: {e}", exc_info=True)

    def add_message_handler(self, handler):
        """
        添加消息处理器
        """
        self.message_handlers.append(handler)

    async def connect(self) -> None:
        """
        建立WebSocket连接
        """
        while True:
            try:
                # 启用内置的ping/pong机制，ping_interval=20表示每20秒发送一次ping
                self.ws = await websockets.connect(self.ws_url, ping_interval=20)
                self.is_connected = True
                logger.success("WS消息成功监听")
                
                # 开始消息接收循环
                async for message in self.ws:
                    await self.handle_message(message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket连接已关闭")
                self.is_connected = False
                await self._reconnect()
            except Exception as e:
                logger.error(f"WebSocket连接错误: {e}", exc_info=True)
                self.is_connected = False
                await self._reconnect()

    async def _reconnect(self) -> None:
        """
        重新连接
        """
        if not self.is_connected:
            logger.info(f"尝试在 {self.reconnect_delay} 秒后重新连接...")
            await asyncio.sleep(self.reconnect_delay)
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self.connect())

    async def close(self) -> None:
        """
        关闭连接
        """
        self.is_connected = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket连接已关闭")

# 使用示例
if __name__ == "__main__":
    async def main():
        client = WsClient('DPBotApi', DPBotPort, selfWxid)
        await client.connect()
        
        try:
            # 保持连接运行
            await asyncio.Future()  # 永久等待
        except KeyboardInterrupt:
            logger.info("程序正在退出...")
            await client.close()

    asyncio.run(main())






