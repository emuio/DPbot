from Plugins._Tools import Tools
from Config.logger import logger
from Core.PluginBase import PluginBase
from WeChatApi import WeChatApi
import os
from typing import Optional

class RandomPicPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.dp = WeChatApi()         
        self.name = "RandomPic"
        self.description = "随机图片插件"
        self.version = "1.0.0"
        self.author = "大鹏"
        self.tools = Tools()        
              
        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.GirlPicApi = self.configData.get('GirlPicApi')
        self.PicWords = self.configData.get('PicWords')
        self.SeeLeg = self.configData.get('SeeLeg')
        self.LegWords = self.configData.get('LegWords')
        self.GirlBig = self.configData.get('GirlBig')
        self.GirlBigWords = self.configData.get('GirlBigWords')

    async def handleRandomPic(self) -> Optional[str]:
        """
        异步获取随机图片URL
        Returns:
            Optional[str]: 成功返回图片URL，失败返回None
        """
        data = await self.tools.async_get(self.GirlPicApi)
        if not data:
            return None
        return data.get('url') if data.get('code') == 200 else None

    async def handleLegPic(self) -> Optional[str]:
        """
        异步获取随机腿图URL
        Returns:
            Optional[str]: 成功返回图片URL，失败返回None
        """
        data = await self.tools.async_get(self.SeeLeg)
        if not data:
            return None
        return data.get('text')
        
    async def handleBigPic(self) -> Optional[str]:
        """
        异步获取随机大图数据
        Returns:
            Optional[str]: 成功返回base64编码的图片数据，失败返回None
        """
        return await self.tools.async_get(
            url=self.GirlBig,
            timeout=10,
            return_json=False,
            return_base64=True
        )
        
    async def handle_message(self, msg) -> bool:
        """
        异步处理消息
        Args:
            msg: 消息对象
        Returns:
            bool: 是否处理了消息
        """
        if msg.type != 1:  # 只处理文本消息
            logger.debug("不是文本消息，跳过处理")
            return False
            
        logger.debug(f"收到消息内容: {msg.content}")
        if self.tools.judgeEqualListWord(msg.content, self.PicWords):
            logger.debug("匹配到随机图片关键词")
            url = await self.handleRandomPic()
            if not url:
                logger.error("获取随机图片URL失败")
                await self.dp.sendText('获取美女图片失败，请稍后再试！', msg.roomid, msg.self_wxid)
                return True
            logger.debug(f"获取到随机图片URL: {url}")
            result = bool(await self.dp.sendImage(url, msg.roomid, msg.self_wxid))
            logger.debug(f"发送随机图片结果: {result}")
            return result
            
        elif self.tools.judgeEqualListWord(msg.content, self.LegWords):
            logger.debug("匹配到腿图关键词")
            url = await self.handleLegPic()
            if not url:
                logger.error("获取腿图URL失败")
                await self.dp.sendText('获取腿图失败，请稍后再试！', msg.roomid, msg.self_wxid)
                return True
            logger.debug(f"获取到腿图URL: {url}")
            result = bool(await self.dp.sendImage(url, msg.roomid, msg.self_wxid))
            logger.debug(f"发送腿图结果: {result}")
            return result
            
        elif self.tools.judgeEqualListWord(msg.content, self.GirlBigWords):
            logger.debug("匹配到女大图关键词")
            image_base64 = await self.handleBigPic()
            if not image_base64:
                logger.error("获取女大图base64数据失败")
                await self.dp.sendText('获取女大图失败，请稍后再试！', msg.roomid, msg.self_wxid)
                return True
            logger.debug("成功获取到女大图base64数据")
            result = bool(await self.dp.sendImage(image_base64, msg.roomid, msg.self_wxid))
            logger.debug(f"发送女大图结果: {result}")
            return result
        
        logger.debug("消息不匹配任何关键词")
        return False

    async def handle_private_message(self, msg) -> bool:
        """
        处理私聊消息，复用群聊消息处理逻辑
        Args:
            msg: 消息对象
        Returns:
            bool: 是否处理了消息
        """
        return await self.handle_message(msg)
