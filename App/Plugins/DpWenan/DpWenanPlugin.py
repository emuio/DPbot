from Plugins._Tools import Tools
from Config.logger import logger
import Config.ConfigServer as Cs
from Core.PluginBase import PluginBase
import os

class DpWenanPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "DpWenan"
        self.description = "DP文案插件"
        self.version = "1.0.0"
        self.author = "大鹏"
        self.tools = Tools()        
              
        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.dpApi = self.configData.get('dpApi')
        self.dpKey = self.configData.get('dpKey')
        self.wenanWords = self.configData.get('wenanWords')
        self.wenan = self.configData.get('wenan', {})

    async def getDPWenan(self, content: str):
        """获取文案内容"""
        try:
            params = {
                'AppSecret': self.dpKey,
                'type': content
            }
            jsonData = await self.tools.async_get(self.dpApi, params=params, return_json=True)
            if not jsonData:
                logger.warning('获取文案失败: 请求失败')
                return None
                
            if jsonData.get('code') != 200:
                logger.warning(f'获取文案失败: {jsonData.get("msg")}')
                return None
                
            wenanData = jsonData.get('result')
            if not wenanData:
                return None
                
            return wenanData.get('content')
        except Exception as e:
            logger.warning(f'{self.name} 获取文案出现错误, 错误信息: {e}')
            return None

    async def handle_message(self, msg) -> bool:
        """处理消息"""
        try:
            if msg.type != 1:  # 只处理文本消息
                return False
                
            content = msg.content.strip()
            
            # 处理各类文案请求
            wenan_type = None
            
            # 舔狗日记
            if self.tools.judgeEqualListWord(content, self.wenan.get('tg', [])):
                wenan_type = '舔狗日记'
            # 骚话
            elif self.tools.judgeEqualListWord(content, self.wenan.get('sh', [])):
                wenan_type = '骚话'
            # 情话
            elif self.tools.judgeEqualListWord(content, self.wenan.get('qh', [])):
                wenan_type = '情话'
            # 毒鸡汤
            elif self.tools.judgeEqualListWord(content, self.wenan.get('djt', [])):
                wenan_type = '毒鸡汤'
            # 走心文案
            elif self.tools.judgeEqualListWord(content, self.wenan.get('zxwa', [])):
                wenan_type = '朋友圈文案'
            # 笑话
            elif self.tools.judgeEqualListWord(content, self.wenan.get('xh', [])):
                wenan_type = '笑话'
            # 早安
            elif self.tools.judgeEqualListWord(content, self.wenan.get('za', [])):
                wenan_type = '早安语录'
            # 晚安
            elif self.tools.judgeEqualListWord(content, self.wenan.get('wa', [])):
                wenan_type = '晚安语录'
            # 名人名言
            elif self.tools.judgeEqualListWord(content, self.wenan.get('mrmy', [])):
                wenan_type = '名人名言'
            # 渣男语录
            elif self.tools.judgeEqualListWord(content, self.wenan.get('zn', [])):
                wenan_type = '渣男语录'
            # 肯德基疯四
            elif self.tools.judgeEqualListWord(content, self.wenan.get('kfc', [])):
                wenan_type = '肯德基疯四'
                
            if wenan_type:
                wenan_content = await self.getDPWenan(wenan_type)
                if wenan_content:
                    await self.dp.sendText(wenan_content, msg.roomid if msg.roomid else msg.sender, msg.self_wxid)
                    return True
                else:
                    await self.dp.sendText(f"获取{wenan_type}失败，请稍后再试", 
                                   msg.roomid if msg.roomid else msg.sender, 
                                   msg.self_wxid)
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"处理文案消息失败: {e}")
            return False