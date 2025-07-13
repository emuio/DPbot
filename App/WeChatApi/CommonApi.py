from Config.logger import logger
from WeChatApi.FriendApi import FriendApi
import Config.ConfigServer as Cs
class CommonApi:
    def __init__(self):
        self.friendApi = FriendApi()
        loginconfig = Cs.returnLoginData().get('DPBotConfig', {})
        self.bot_api = loginconfig.get('DPBotApi')
        self.bot_port = loginconfig.get('DPBotPort')
        self.self_wxid = loginconfig.get('selfWxid')

    async def getIdName(self, wxid):
        """
        获取好友昵称
        :param wxid: 好友微信ID
        :return: 好友昵称，如果获取失败返回None
        """
        friend = await self.friendApi.getFriendInfo(wxid, self.self_wxid)
        if friend and friend.get('Data') and friend['Data'].get('ContactList'):
            contact = friend['Data']['ContactList'][0]
            if contact and contact.get('NickName', {}).get('string'):
                return contact['NickName']['string']
        return None

    async def getFriendHeadImg(self, wxid):
        """
        获取好友头像
        :param wxid: 好友微信ID
        :return: 好友大头像URL，如果获取失败返回None
        """
        friend = await self.friendApi.getFriendInfo(wxid, self.self_wxid)
        if friend and friend.get('Data') and friend['Data'].get('ContactList'):
            contact = friend['Data']['ContactList'][0]
            if contact and contact.get('BigHeadImgUrl'):
                return contact['BigHeadImgUrl']
        return None

