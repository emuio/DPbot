from .Base import *
from typing import Dict, Optional

class ToolsApi:
    def __init__(self):
        pass

    async def downloadFile(self, AttachId: str, DataLen: int, selfWxid: str) -> Optional[Dict]:
        """
        下载文件
        :param AttachId: 文件ID
        :param DataLen: 文件大小
        :param selfWxid: 机器人ID
        :return: 下载结果
        """
        try:
            data = {
                "AppID": "",
                "AttachId": AttachId,
                "DataLen": DataLen,
                "Section": {
                    "DataLen": DataLen,
                    "StartPos": 0
                },
                "UserName": "",
                "Wxid": selfWxid   
            }
            return await sendPostReq("Tools/DownloadFile", data)
        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return None

    async def downloadImage(self, FileAesKey: str, FileNo: str, selfWxid: str) -> Optional[Dict]:
        """
        下载图片
        :param FileAesKey: 文件AES密钥
        :param FileNo: 文件编号
        :param selfWxid: 机器人ID
        :return: 下载结果
        """
        try:
            data = {
                "FileAesKey": FileAesKey,
                "FileNo": FileNo,
                "Wxid": selfWxid
            }
            return await sendPostReq("Tools/CdnDownloadImage", data)
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            return None

    async def downloadVideo(self, CompressType: int, DataLen: int, MsgId: str, 
                          Towxid: str, selfWxid: str) -> Optional[Dict]:
        """
        下载视频
        :param CompressType: 压缩类型
        :param DataLen: 数据长度
        :param MsgId: 消息ID
        :param Towxid: 接收者ID
        :param selfWxid: 机器人ID
        :return: 下载结果
        """
        try:
            data = {
                "CompressType": CompressType,
                "DataLen": DataLen,
                "MsgId": MsgId,
                "Section": {
                    "DataLen": DataLen,
                    "StartPos": 0
                },
                "ToWxid": Towxid,
                "Wxid": selfWxid
            }
            return await sendPostReq("Tools/DownloadVideo", data)
        except Exception as e:
            logger.error(f"下载视频失败: {e}")
            return None

    async def downloadVoice(self, Bufid: str, FromUserName: str, Length: int, 
                          MsgId: str, selfWxid: str) -> Optional[Dict]:
        """
        下载语音
        :param Bufid: 缓冲区ID
        :param FromUserName: 发送者用户名
        :param Length: 语音长度
        :param MsgId: 消息ID
        :param selfWxid: 机器人ID
        :return: 下载结果
        """
        try:
            data = {
                "Bufid": Bufid,
                "FromUserName": FromUserName,
                "Length": Length,
                "MsgId": MsgId,
                "Wxid": selfWxid
            }
            return await sendPostReq("Tools/DownloadVoice", data)
        except Exception as e:
            logger.error(f"下载语音失败: {e}")
            return None

