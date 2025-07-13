from Plugins._Tools import Tools
from Config.logger import logger
import Config.ConfigServer as Cs
from Core.PluginBase import PluginBase
import os

class DpToolsPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "DpTools"
        self.description = "DP工具插件"
        self.version = "1.0.0"
        self.author = "大鹏"
        self.tools = Tools()
        
        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.hot_news = self.configData.get('hotword')

    async def handle_message(self, msg) -> bool:
        """处理消息"""
        try:
            if msg.type != 1:  # 只处理文本消息
                return False
                
            if not self.tools.judgeEqualListWord(msg.content, self.hot_news):
                return False
                
            logger.debug(f'{self.name} 收到热搜查询请求')
            
            try:
                url = "https://hot.dudunas.top"
                title = "全网实时热搜"
                des = "火速围观"
                thumb_url = "https://mmbiz.qpic.cn/mmbiz_jpg/BUO9n59znKqhia3Nk2icSCz4jYXyVTTWURzC9TH9U0amDgBKAxtnVAD5O3enFzW3oDX3xtCEcibLx335lRlJxScXg/640?wx_fmt=jpeg&tp=webp&wxfrom=5&wx_lazy=1"
                
                # 发送卡片消息
                result = await self.dp.sendRich(                    
                    title=title,
                    description=des,
                    url=url,
                    thumb_url=thumb_url,
                    toWxid=msg.roomid,
                    selfWxid=msg.self_wxid
                )
                
                if result:
                    logger.info(f'{self.name} 热搜卡片发送成功')
                else:
                    logger.warning(f'{self.name} 热搜卡片发送失败')
                    await self.dp.sendText(
                        f'❌ 热搜卡片发送失败，请稍后重试',
                        msg.roomid,
                        msg.self_wxid
                    )
                
                return True
                
            except Exception as e:
                logger.error(f'{self.name} 发送热搜卡片失败: {e}')
                await self.dp.sendText(
                    f'❌ 发送热搜卡片出现错误: {str(e)}',
                    msg.roomid,
                    msg.self_wxid
                )
                return True
            
        except Exception as e:
            logger.error(f"{self.name} 处理消息失败: {e}")
            await self.dp.sendText(
                f"处理消息出现错误，请稍后重试",
                msg.roomid,
                msg.self_wxid
            )
            return True


