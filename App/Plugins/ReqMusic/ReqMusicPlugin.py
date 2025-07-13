from Plugins._Tools import Tools
from Config.logger import logger
import Config.ConfigServer as Cs
from Core.PluginBase import PluginBase
from WeChatApi import WeChatApi
import os

class ReqMusicPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.dp = WeChatApi()
        self.tools = Tools()
        self.name = "ReqMusic"
        self.description = "点歌插件"
        self.version = "1.0.0"
        self.author = "大鹏"
        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.musicword = self.configData.get('musicword')
        self.dpApi = self.configData.get('dpApi')
        self.dpKey = self.configData.get('dpKey')

    async def get_music_info(self, songname: str):
        """获取音乐信息
        Args:
            songname: 歌曲名称
        Returns:
            dict: 音乐信息，获取失败返回None
        """
        try:
            url = f"{self.dpApi}&AppSecret={self.dpKey}&songname={songname}"
            logger.debug(f"请求的URL: {url}")
            
            data = await self.tools.async_get(url, return_json=True)
            if not data:
                logger.warning("获取音乐数据失败: 请求失败")
                return None
                
            if data.get('code') != 200:
                logger.warning(f"获取音乐数据失败: {data.get('msg')}")
                return None
                
            logger.debug(f"获取到的数据: {data}")
            return data.get('data')
        except Exception as e:
            logger.error(f"获取音乐数据出错: {e}")
            return None

    async def handle_message(self, msg) -> bool:
        """处理消息"""
        try:
            if not self.tools.judgeSplitAllEqualWord(msg.content, self.musicword):
                return False
                
            logger.debug(f"接收到的消息: {msg.content}")
            parts = msg.content.split(' ', 1)
            if len(parts) < 2:
                await self.dp.sendText("请输入要点播的歌曲名称", msg.roomid, msg.self_wxid)
                return True
                
            songname = parts[1].strip()
            if not songname:
                await self.dp.sendText("请输入要点播的歌曲名称", msg.roomid, msg.self_wxid)
                return True
                
            music_data = await self.get_music_info(songname)
            if not music_data:
                await self.dp.sendText("获取歌曲信息失败，请稍后重试", msg.roomid, msg.self_wxid)
                return True
                
            await self.dp.sendMusic(
                title=music_data.get('title'),
                singer=music_data.get('author'),
                url=music_data.get('link'),
                music_url=music_data.get('url'),
                cover_url=music_data.get('pic'),
                lyric=music_data.get('lrc'),
                toWxid=msg.roomid,
                selfWxid=msg.self_wxid
            )
            return True
            
        except Exception as e:
            logger.error(f"处理点歌消息失败: {e}")
            await self.dp.sendText("点歌过程出现错误，请稍后重试", msg.roomid, msg.self_wxid)
            return True

        
