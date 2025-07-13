from .Base import *
from typing import Dict, Optional

class LoginApi:
    def __init__(self):
        pass

    async def getIpadQr(self) -> Optional[Dict]:
        """
        获取二维码
        """
        try:
            payload = {
                "DeviceID": "123456",
                "DeviceName": "Dpbot",
                "Proxy": {
                    "ProxyIp": "",
                    "ProxyPassword": "",
                    "ProxyUser": ""
                }
            }
            return await sendPostReq("/Login/LoginGetQR", payload)
        except Exception as e:
            logger.error(f"获取二维码失败: {e}")
            return None

    async def checkqr(self, uuid: str) -> Optional[Dict]:
        """
        检查二维码
        """
        try:
            # POST 请求，uuid 作为 query 参数
            return await sendPostReq(f"/Login/LoginCheckQR?uuid={uuid}",{})
        except Exception as e:
            logger.error(f"检查二维码失败: {e}")
            return None
            
    async def TwiceLogin(self, wxid: str) -> Optional[Dict]:
        """
        二次登录
        """
        try:
            return await sendPostReq(f"/Login/LoginTwiceAutoAuth?wxid={wxid}", {})
        except Exception as e:
            logger.error(f"二次登录失败: {e}")
            return None

