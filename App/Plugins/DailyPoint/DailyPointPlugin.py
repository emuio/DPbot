from Plugins._Tools import Tools
from Config.logger import logger
import Config.ConfigServer as Cs
from Core.PluginBase import PluginBase
import os
import asyncio    
class DailyPointPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "DailyPoint"
        self.description = "签到积分"
        self.version = "1.0.0"
        self.author = "大鹏"
        self.tools = Tools()
        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.checkinword = self.configData.get('checkinword')
        self.dpApi = self.configData.get('dpApi')
        self.dpKey = self.configData.get('dpKey')

    async def handle_message(self, msg) -> bool:
        """处理消息
        格式1：签到
        示例1：签到
        """

        if msg.type != 1:  # 只处理文本消息
            return False
        if self.tools.judgeEqualWord(msg.content, '签到'):
            # 获取用户信息
            user_info = await self.dp.getIdName(msg.sender)
            reply = f"@{user_info} \n签到失败❌️\n回复：DP族人，前来部落"
            await self.dp.sendText(reply, msg.roomid, msg.self_wxid)
            return True
        elif self.tools.judgeEqualWord(msg.content, 'DP族人，前来部落'):
            # 获取用户信息
            user_info = await self.dp.getIdName(msg.sender)
            wenan = await self.getDPWenan('毒鸡汤')
            reply = f"@{user_info} \n签到成功✅️\n{wenan}\n开源地址：https://github.com/dpyyds/DPbot"
            await self.dp.sendText(reply, msg.roomid, msg.self_wxid)
            return True




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
