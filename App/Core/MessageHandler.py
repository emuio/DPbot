import Config.ConfigServer as Cs
from WeChatApi.WsClient import WsClient
from WeChatApi import WeChatApi
from .msg import WxMsg
from Config.logger import logger
import json
from Plugins._Tools import Tools
from .PluginManager import PluginManager
import asyncio
from datetime import datetime
from typing import Optional, Dict

class MessageHandler(WsClient):
    """
    消息处理器类，负责接收和分发各类消息
    """
    def __init__(self):
        """同步初始化基本配置"""
        self._init_config()
        super().__init__(self.bot_api, self.bot_port, self.self_wxid)
        
        # 记录启动时间，用于跳过历史消息
        self.startup_time = datetime.now().timestamp()
        logger.info(f"机器人启动时间: {datetime.fromtimestamp(self.startup_time).strftime('%Y-%m-%d %H:%M:%S')}")
        if self.skip_history_messages:
            logger.info("已启用跳过历史消息功能，将自动跳过启动时间之前的历史消息")
        else:
            logger.info("已禁用跳过历史消息功能，将处理所有接收到的消息")

        # 初始化组件
        self.wechat_api = WeChatApi()
        self.tools = Tools()
        self.plugin_manager = PluginManager(wechat_api=self.wechat_api)
        
        # 创建初始化标志
        self._initialized = False
        
        # 创建初始化任务
        self._init_task = asyncio.create_task(self._async_init())

    def _init_config(self):
        """初始化配置"""
        loginconfig = Cs.returnLoginData().get('DPBotConfig', {})
        self.bot_api = loginconfig.get('DPBotApi')
        self.bot_port = loginconfig.get('DPBotPort')
        self.self_wxid = loginconfig.get('selfWxid')
        config = Cs.returnConfigData().get('DPBotConfig', {})
        self.Administrators = config.get('Administrators', [])
        self.skip_history_messages = config.get('skip_history_messages', True)

        # 验证必要的配置
        missing_configs = []
        if not self.bot_api:
            missing_configs.append("DPBotApi")
        if not self.bot_port:
            missing_configs.append("DPBotPort")
        if not self.self_wxid:
            missing_configs.append("selfWxid")
            
        if missing_configs:
            error_msg = f"缺少必要的配置项：{', '.join(missing_configs)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def _async_init(self):
        """异步初始化组件"""
        try:
            # 初始化数据库
            db_results = await self.tools.init_all_databases()
            if not all(db_results.values()):
                failed_dbs = [db for db, success in db_results.items() if not success]
                error_msg = f"数据库初始化失败: {', '.join(failed_dbs)}"
                logger.error(error_msg)
                return False
            
            self._initialized = True
            logger.info("MessageHandler 初始化完成")
            return True
        except Exception as e:
            logger.error(f"MessageHandler 初始化失败: {e}", exc_info=True)
            return False

    async def wait_for_initialized(self) -> bool:
        """等待初始化完成"""
        try:
            return await self._init_task
        except Exception as e:
            logger.error(f"等待初始化完成时出错: {e}", exc_info=True)
            return False

    def is_admin(self, wxid: str) -> bool:
        """检查是否为超级管理员"""
        return wxid in self.Administrators

    async def handle_message(self, message: str) -> None:
        """处理接收到的消息"""
        try:
            # 确保已经初始化
            if not self._initialized:
                logger.debug("MessageHandler 未初始化，等待初始化完成...")
                # 等待初始化完成
                if not await self.wait_for_initialized():
                    logger.error("MessageHandler 初始化失败，无法处理消息")
                    return

            data = json.loads(message)
            logger.debug(f"收到原始消息: {data}")
            msg = WxMsg(data, self.self_wxid)

            if self.skip_history_messages and msg.create_time and msg.create_time < self.startup_time:
                logger.debug(f"跳过历史消息: {msg.formatted_time}")
                return

            logger.info(f"开始处理消息: {msg}")
            asyncio.create_task(self.process_message(msg))
            
        except json.JSONDecodeError as e:
            logger.error(f"消息解析失败: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"消息处理错误: {e}", exc_info=True)

    async def process_message(self, msg):
        """处理消息"""
        try:
            # 查询群组模式
            group_mode = await self.tools.query_group_mode(msg.roomid)
            logger.debug(f"群组 {msg.roomid} 的模式查询结果: {group_mode}")
            
            # 设置消息模式
            msg.mode = group_mode if group_mode else "OTHER"
            logger.debug(f"消息模式设置为: {msg.mode}")
            
            # 交给插件管理器处理
            logger.debug("开始调用插件管理器处理消息...")
            result = await self.plugin_manager.handle_message(msg)
            logger.debug(f"插件管理器处理消息结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"处理消息时出错: {e}", exc_info=True)
            return False

    async def close(self) -> None:
        """关闭连接和清理资源"""
        try:
            # 取消初始化任务（如果还在运行）
            if self._init_task and not self._init_task.done():
                self._init_task.cancel()
                try:
                    await self._init_task
                except asyncio.CancelledError:
                    pass

            # 关闭数据库连接
            if self.tools:
                await self.tools.close()  # 需要在Tools类中添加此方法

            # 关闭插件管理器
            if self.plugin_manager:
                await self.plugin_manager.close()  # 需要在PluginManager中添加此方法

            # 关闭 WebSocket 连接
            await super().close()
            
            # 关闭其他连接
            if self.wechat_api:
                await self.wechat_api.close()
            
            # 清理资源
            self.plugin_manager = None
            self.tools = None
            self.wechat_api = None
            self._initialized = False
            
            logger.info("MessageHandler 已关闭并清理资源")
        except Exception as e:
            logger.error(f"关闭 MessageHandler 时发生错误: {e}")
            raise  # 重新抛出异常，确保调用者知道关闭过程中出现了错误

    async def run(self):
        """运行消息处理器"""
        try:
            # 等待初始化完成
            if not await self.wait_for_initialized():
                error_msg = "MessageHandler 初始化失败"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            logger.info("开始连接 WebSocket...")
            await self.connect()  # 调用父类的connect方法
            
        except Exception as e:
            logger.error(f"运行消息处理器失败: {e}", exc_info=True)
            raise 
   