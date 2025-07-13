from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from Config.logger import logger
import asyncio

class PluginBase(ABC):
    """
    插件基类，所有插件都必须继承此类
    提供插件的基本属性和方法
    """
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = "插件描述"
        self.version = "1.0.0"
        self.author = "作者"
        self.commands = {}  # 命令列表
        self.dp = None  # 初始化为None，等待PluginManager设置
        
    async def should_handle_message(self, msg) -> bool:
        """
        判断是否应该处理该消息
        子类可以重写此方法以提供更具体的判断逻辑
        
        Args:
            msg: 消息对象
        Returns:
            bool: 是否应该处理该消息
        """
        # 基础判断逻辑
        if msg.sender == msg.self_wxid:  # 自己发送的消息
            return False
            
        # 默认处理所有消息
        return True
        
    @abstractmethod
    async def handle_message(self, msg) -> bool:
        """
        处理消息的抽象方法
        Args:
            msg: 消息对象
        Returns:
            bool: 是否处理了消息
        """
        pass

    async def handle_private_message(self, msg) -> bool:
        """
        处理私聊消息的方法
        默认实现调用 handle_message，插件可以重写此方法以提供不同的私聊处理逻辑
        Args:
            msg: 消息对象
        Returns:
            bool: 是否处理了消息
        """
        return await self.handle_message(msg)
    
    async def handle_admin_message(self, msg) -> bool:
        """
        处理管理员消息的方法
        默认实现调用 handle_message，Admin插件应该重写此方法
        Args:
            msg: 消息对象
        Returns:
            bool: 是否处理了消息
        """
        return await self.handle_message(msg)
    
    def register_command(self, command: str, handler: callable, description: str = "") -> None:
        """
        注册命令处理器
        Args:
            command: 命令名称
            handler: 处理函数（可以是同步或异步函数）
            description: 命令描述
        """
        self.commands[command] = {
            "handler": handler,
            "description": description
        }
    
    def get_help(self) -> str:
        """
        获取插件帮助信息
        Returns:
            str: 帮助信息文本
        """
        help_text = f"【{self.name}】v{self.version}\n"
        help_text += f"作者：{self.author}\n"
        help_text += f"描述：{self.description}\n"
        help_text += "支持的命令：\n"
        for cmd, info in self.commands.items():
            help_text += f"- {cmd}: {info['description']}\n"
        return help_text

    async def call_command(self, command: str, *args, **kwargs) -> Optional[Any]:
        """
        调用命令处理器
        Args:
            command: 命令名称
            *args: 位置参数
            **kwargs: 关键字参数
        Returns:
            Optional[Any]: 命令处理结果
        """
        if command not in self.commands:
            return None
            
        handler = self.commands[command]["handler"]
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(*args, **kwargs)
            else:
                return handler(*args, **kwargs)
        except Exception as e:
            logger.error(f"执行命令 {command} 失败: {e}")
            return None 