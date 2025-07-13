from Plugins._Tools import Tools
from Config.logger import logger
from Core.PluginBase import PluginBase
from WeChatApi import WeChatApi
import os
import random

class RandomVideoPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.dp = WeChatApi()         
        self.name = "RandomVideo"
        self.description = "随机视频插件"
        self.version = "1.0.0"
        self.author = "大鹏"
        self.tools = Tools()        
              
        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.GirlVideoApi = self.configData.get('GirlVideoApi', [])
        self.VideoWords = self.configData.get('VideoWords', [])

    async def handleRandomVideo(self):
        """获取随机视频URL"""
        try:
            api = random.choice(self.GirlVideoApi)
            resp = await self.tools.async_get(api, return_json=True)
            if not resp:
                logger.warning('获取视频失败: 请求失败')
                return None
                
            logger.debug(f'随机视频API返回数据: {resp}')
            return resp.get('data')
        except Exception as e:
            logger.warning(f'获取视频失败: {e}')
            return None

    async def handle_message(self, msg) -> bool:
        """处理消息"""
        if msg.type != 1 or not self.tools.judgeEqualListWord(msg.content, self.VideoWords):
            return False
            
        url = await self.handleRandomVideo()
        if not url or not await self.dp.sendVideo(url, msg.roomid, msg.self_wxid):
            await self.dp.sendText('获取或发送视频失败，请稍后再试！', msg.roomid, msg.self_wxid)
            
        return True
