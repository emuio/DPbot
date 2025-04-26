from BotServer.MsgHandleServer.FriendMsgHandle import FriendMsgHandle
from BotServer.MsgHandleServer.RoomMsgHandle import RoomMsgHandle
from PushServer.PushMainServer import PushMainServer
from DbServer.DbInitServer import DbInitServer
import FileCache.FileCacheServer as Fcs
import Config.ConfigServer as Cs
from threading import Thread
from OutPut.outPut import op
#from cprint import cprint
from queue import Empty
from wcfriend.client import Wcf
from wcfriend.wxmsg import WxMsg
from config import *
from loguru import logger
import requests
from loguru import logger
import time
import base64
from io import BytesIO
from PIL import Image
class MainServer:
    def __init__(self):
        self.wcf = Wcf(self_wxid=SELFWXID, base_url=WXAPI_URL, ws_url=WXAPI_WS_URL, max_retries=10, retry_delay=5)
        self.Dis = DbInitServer()
        # 开启全局接收
        self.wcf.start()
        self.Rmh = RoomMsgHandle(self.wcf)
        self.Fmh = FriendMsgHandle(self.wcf)
        self.Pms = PushMainServer(self.wcf)
        # 初始化服务以及配置
        Thread(target=self.initConfig, name='初始化服务以及配置').start()

    def islogin(self):        
        # 获取二维码
        qrcode = self.wcf.get_qrcode()
        # 打印二维码
        logger.success(qrcode)
        qr_base64 = qrcode.get("QrBase64", "").replace("data:image/jpg;base64,", "")
        if qr_base64:
            img_data = base64.b64decode(qr_base64)
            img = Image.open(BytesIO(img_data))
            img.show()
        # 检查二维码
        time.sleep(30)
        checkQR = self.wcf.checkQR(qrcode['Uuid'])
        logger.success(checkQR)


    
    def processMsg(self, ):
        # 判断是否登录
        self.islogin()
        while self.wcf.is_receiving_msg():
            try:
                msg = self.wcf.get_msg()
                
                # 调试专用
                logger.info(msg)
                self.process_message(msg)
                #op(f'[*]: 接收到消息\n[*]: 群聊ID: {msg.roomid}\n[*]: 发送人ID: {msg.sender}\n[*]: 发送内容: {msg.content}\n--------------------')
                # 群聊消息处理
            except Empty:
                continue
    def process_message(self, msg: WxMsg):
        sender = msg.sender
        content = msg.content
        roomid = msg.roomid

        # 群聊消息处理
        if roomid and '@chatroom' in roomid:
            Thread(target=self.Rmh.mainHandle, args=(msg,)).start()
        # 好友消息处理
        elif msg.is_from_friend():
            Thread(target=self.Fmh.mainHandle, args=(msg,)).start()


    def initConfig(self, ):
        """
        初始化数据库 缓存文件夹 开启定时推送服务
        :return:
        """
        self.Dis.initDb()
        Fcs.initCacheFolder()
        Thread(target=self.Pms.run, name='定时推送服务').start()



if __name__ == '__main__':
    Ms = MainServer()
    Ms.processMsg()
