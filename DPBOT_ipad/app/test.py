#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from loguru import logger
from wcfriend.client import Wcf
from wcfriend.wxmsg import WxMsg
from config import *
import os
import requests
from datetime import datetime
from BotServer.BotFunction.InterfaceFunction import *
def process_message(wcf, msg: WxMsg):
    """
    处理接收到的消息
    参数:
        wcf: 微信客户端实例
        msg: 消息对象 (WxMsg 类型)
    """
    sender = msg.sender
    logger.info(f"消息发送者: {sender}")
    content = msg.content
    logger.info(f"消息内容: {content}")
    #s =getIdName(wcf,roomid="53152120103@chatroom")
   # s =getIdName(wcf,"peng729831790","53152120103@chatroom")
    #s =wcf.get_info_by_roomid("53152120103@chatroom")
    #s = wcf.get_info_by_wxid("peng729831790")
    # 获取二维码    
    qr_result = wcf.get_qrcode()
    logger.info(f"二维码获取结果: {qr_result}")
    # 检查二维码
    time.sleep(60)
    if qr_result['Uuid']:
        checkQR = wcf.checkQR(qr_result['Uuid'])
        logger.info(f"二维码检查结果: {checkQR}")
    #s = wcf.get_alias_in_chatroom("peng729831790","53152120103@chatroom")
    logger.info(s)
    # 检查消息是否来自好友
    if msg.is_from_friend():
        logger.info(f"好友消息内容: {content}")
        if content and content.strip() == "湖人总冠军":
            # 验证 sender 是否有效（非空且为字符串）
            if not sender or not isinstance(sender, str):
                logger.error("发送者 ID 无效或为空")
                return
            p = r"C:\Users\Administrator\Desktop\data\00test\8055v1\app\鱼.png"
            wcf.send_image(p, sender)  
            wcf.invite_chatroom_members("21410065073@chatroom", sender)
            # 构造 API 请求数据
           
               
    #if msg.from_group():
        #logger.info(f"收到群消息: {content}")

    #else:
        #logger.info(f"收到私聊消息: {content}")
if __name__ == "__main__":
#def main():
    """程序主入口"""
    # 初始化 Wcf 实例
    wcf = Wcf(self_wxid=SELFWXID, base_url=WXAPI_URL, ws_url=WXAPI_WS_URL, max_retries=10, retry_delay=5)
    
    # 获取二维码
    try:
        qr_result = wcf.get_qrcode()
        logger.info(f"二维码获取结果: {qr_result}")
    except Exception as e:
        logger.error(f"获取二维码失败: {e}")
        #return

    # 启动服务
    wcf.start()
    logger.info("服务已启动")
    try:
        # 主循环，获取并处理消息
        while wcf.is_receiving_msg():
            msg = wcf.get_msg(block=True, timeout=1.0)
            if msg:
                logger.info(msg)
                process_message(wcf, msg)
    except KeyboardInterrupt:
        logger.info("收到中断信号，准备停止服务")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
    finally:
        wcf.stop()
        logger.info("服务已停止")

