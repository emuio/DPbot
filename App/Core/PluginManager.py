import os
import importlib
import inspect
from typing import Dict, Optional
from Config.logger import logger
from .PluginBase import PluginBase
from Plugins._Tools import Tools
from WeChatApi import WeChatApi

class PluginManager:
    def __init__(self, wechat_api: WeChatApi = None):
        self.plugins: Dict[str, PluginBase] = {}  # 插件字典
        self.tools = Tools()  # 工具类实例
        self.wechat_api = wechat_api  # 共享的WeChatApi实例
        self._load_plugins()  # 加载插件
        
    def _load_plugins(self) -> None:
        """加载插件目录下的所有插件"""
        try:
            plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Plugins")
            for item in os.listdir(plugins_dir):
                if item.startswith("_"):  # 跳过以_开头的目录
                    continue
                    
                plugin_dir = os.path.join(plugins_dir, item)
                if not os.path.isdir(plugin_dir):
                    continue
                    
                # 查找插件主文件
                plugin_file = os.path.join(plugin_dir, f"{item}Plugin.py")
                if not os.path.exists(plugin_file):
                    continue
                    
                try:
                    # 动态导入插件模块
                    module_path = f"Plugins.{item}.{item}Plugin"
                    module = importlib.import_module(module_path)
                    
                    # 查找插件类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and
                            issubclass(obj, PluginBase) and
                            obj != PluginBase):
                            # 实例化插件并存储
                            plugin = obj()

                            # 设置共享的WeChatApi实例
                            plugin.dp = self.wechat_api
                            #logger.debug(f"为插件 {plugin.name} 设置共享的WeChatApi实例")

                            self.plugins[plugin.name] = plugin
                            logger.info(f"成功加载插件：{plugin.name} v{plugin.version}")
                            break
                            
                except Exception as e:
                    logger.error(f"加载插件 {item} 失败: {e}")
                    
        except Exception as e:
            logger.error(f"加载插件目录失败: {e}")
            
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """获取指定名称的插件实例"""
        return self.plugins.get(plugin_name)
        
    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """获取所有插件"""
        return self.plugins
        
    async def handle_message(self, msg):
        """处理消息"""
        try:
            # 1. 基础消息过滤（自己发送的消息不处理）
            if msg.sender == msg.self_wxid:
                logger.debug("跳过自己发送的消息")
                return False

            # 2. 优先处理管理员插件的消息
            admin_plugin = self.plugins.get("Admin")
            if admin_plugin:
                # 检查是否应该由管理员插件处理
                if await admin_plugin.should_handle_message(msg):
                    logger.debug("尝试使用 Admin 插件处理消息")
                    if await admin_plugin.handle_admin_message(msg):
                        logger.debug("Admin 插件成功处理了消息")
                        return True

            # 3. 处理私聊消息
            if msg.is_private:
                logger.debug("开始处理私聊消息")
                for plugin_name, plugin in self.plugins.items():
                    if plugin_name == "Admin":  # 跳过管理员插件，因为已经处理过了
                        continue
                        
                    try:
                        logger.debug(f"检查插件 {plugin_name} 是否处理私聊消息")
                        # 检查插件是否应该处理该消息
                        if not await plugin.should_handle_message(msg):
                            logger.debug(f"插件 {plugin_name} 不处理该消息")
                            continue
                            
                        # 检查插件配置
                        if not await self.tools.judgePluginConfig("private", plugin_name):
                            logger.debug(f"插件 {plugin_name} 未启用私聊功能")
                            continue
                            
                        # 处理私聊消息
                        logger.debug(f"尝试使用插件 {plugin_name} 处理私聊消息")
                        if await plugin.handle_private_message(msg):
                            logger.debug(f"插件 {plugin_name} 成功处理了私聊消息")
                            return True
                    except Exception as e:
                        logger.error(f"插件 {plugin_name} 处理私聊消息时出错: {e}", exc_info=True)
                        continue

            # 4. 处理群聊消息
            else:
                logger.debug("开始处理群聊消息")
                for plugin_name, plugin in self.plugins.items():
                    if plugin_name == "Admin":  # 跳过管理员插件，因为已经处理过了
                        continue
                        
                    try:
                        logger.debug(f"检查插件 {plugin_name} 是否处理群聊消息")
                        # 检查插件是否应该处理该消息
                        if not await plugin.should_handle_message(msg):
                            logger.debug(f"插件 {plugin_name} 不处理该消息")
                            continue
                            
                        # 检查插件配置
                        if not await self.tools.judgePluginConfig(msg.mode[0], plugin_name):
                            logger.debug(f"插件 {plugin_name} 在模式 {msg.mode[0]} 下未启用")
                            continue
                        
                        # 处理消息
                        logger.debug(f"尝试使用插件 {plugin_name} 处理群聊消息")
                        if await plugin.handle_message(msg):
                            logger.debug(f"插件 {plugin_name} 成功处理了群聊消息")
                            return True
                    except Exception as e:
                        logger.error(f"插件 {plugin_name} 处理消息时出错: {e}", exc_info=True)
                        continue

            logger.debug("没有插件处理此消息")
            return False

        except Exception as e:
            logger.error(f"消息处理失败: {e}", exc_info=True)
            return False
        
    async def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载指定插件"""
        try:
            plugin = self.plugins.get(plugin_name)
            if not plugin:
                logger.error(f"插件 {plugin_name} 不存在")
                return False
                
            # 获取插件模块路径
            module_path = plugin.__class__.__module__
            # 重新加载模块
            module = importlib.reload(importlib.import_module(module_path))
            
            # 查找插件类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginBase) and 
                    obj != PluginBase):
                    # 实例化插件并更新
                    self.plugins[plugin_name] = obj()
                    logger.info(f"成功重新加载插件：{plugin_name}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"重新加载插件 {plugin_name} 失败: {e}")
            return False

    async def handle_admin_message(self, msg) -> bool:
        """专门处理管理员插件的消息，不受群组模式影响"""
        try:
            # 直接从插件字典中获取Admin插件
            admin_plugin = self.plugins.get("Admin")
            if admin_plugin:
                return await admin_plugin.handle_message(msg)
            return False
        except Exception as e:
            logger.error(f"处理管理员消息失败: {e}")
            return False

    async def handle_private_message(self, msg) -> bool:
        """处理私聊消息"""
        try:
            # 遍历所有插件处理消息
            for plugin_name, plugin in self.plugins.items():
                logger.debug(f"正在检查私聊插件: {plugin_name}")
                try:
                    # 检查插件是否支持私聊
                    if not hasattr(plugin, 'handle_private_message'):
                        logger.debug(f"插件 {plugin_name} 不支持私聊，跳过")
                        continue

                    # 检查插件是否启用（私聊模式下）
                    plugin_enabled = self.tools.judgePluginConfig("private", plugin_name)
                    logger.debug(f"插件 {plugin_name} 在私聊模式下的启用状态: {plugin_enabled}")
                    
                    if not plugin_enabled:
                        logger.debug(f"插件 {plugin_name} 在私聊模式下未启用，跳过")
                        continue
                        
                    # 让插件处理消息
                    if await plugin.handle_private_message(msg):
                        logger.debug(f"插件 {plugin_name} 成功处理了私聊消息")
                        return True
                    else:
                        logger.debug(f"插件 {plugin_name} 未处理私聊消息")
                        
                except Exception as e:
                    logger.error(f"插件 {plugin_name} 处理私聊消息时出错: {e}")
                    continue
                
            return False
            
        except Exception as e:
            logger.error(f"处理私聊消息失败: {e}")
            return False

    async def close(self):
        """关闭插件管理器，清理资源"""
        try:
            # 关闭所有插件
            for plugin_name, plugin in self.plugins.items():
                try:
                    if hasattr(plugin, 'close') and callable(plugin.close):
                        await plugin.close()
                except Exception as e:
                    logger.error(f"关闭插件 {plugin_name} 时出错: {e}")

            # 清理插件列表
            self.plugins.clear()
            
            # 关闭工具类
            if self.tools:
                await self.tools.close()
            self.tools = None
            
            # 清理API引用
            self.wechat_api = None
            
            logger.info("插件管理器已关闭")
        except Exception as e:
            logger.error(f"关闭插件管理器时出错: {e}")
            raise 