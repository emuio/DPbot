from .Base import *
from typing import Dict, Optional

class FriendApi:
    def __init__(self):
        pass

    async def getFriendList(self, wxid: str) -> Optional[Dict]:
        """
        获取好友列表
        :param wxid: 机器人ID
        :return: 好友列表信息
        """
        try:
            data = {
                "CurrentChatRoomContactSeq": 0,
                "CurrentWxcontactSeq": 0,
                "Wxid": wxid
            }
            return await sendPostReq("Friend/GetContractList", data)
        except Exception as e:
            logger.error(f"获取好友列表失败: {e}")
            return None

    async def getFriendInfo(self, towxid: str, selfWxid: str) -> Optional[Dict]:
        """
        获取好友信息
        :param towxid: 好友ID
        :param selfWxid: 机器人ID
        :return: 好友详细信息
        """
        try:
            data = {
                "ChatRoom": "",
                "Towxids": towxid,
                "Wxid": selfWxid
            }
            return await sendPostReq("Friend/GetContractDetail", data)
        except Exception as e:
            logger.error(f"获取好友信息失败: {e}")
            return None

    async def acceptFriend(self, v1: str, v2: str, selfWxid: str) -> Optional[Dict]:
        """
        接受好友请求
        :param v1: 验证信息v1
        :param v2: 验证信息v2
        :param selfWxid: 机器人ID
        :return: 接受结果
        """
        try:
            data = {
                "Scene": 0,
                "V1": v1,
                "V2": v2,
                "Wxid": selfWxid
            }
            return await sendPostReq("Friend/AcceptContract", data)
        except Exception as e:
            logger.error(f"接受好友请求失败: {e}")
            return None






