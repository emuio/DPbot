from Plugins._Tools import Tools
from Config.logger import logger
import Config.ConfigServer as Cs
from Core.PluginBase import PluginBase
import os
class DemoPlugin(PluginBase):
       def __init__(self):
           super().__init__()
           self.name = "DemoPlugin"
           self.description = "插件描述"
           self.version = "1.0.0"
           self.author = "作者名"
           self.tools = Tools()
           self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
           self.word = self.configData.get('word')
       async def handle_message(self, msg) -> bool:
           # 处理群聊消息的逻辑
           pass
       async def handle_private_message(self, msg):
           # 处理私聊消息的逻辑
           pass
