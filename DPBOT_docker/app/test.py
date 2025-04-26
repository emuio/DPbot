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


    # 启动服务
    wcf.start()
    logger.info("服务已启动")
    try:
        # 主循环，获取并处理消息
        while wcf.is_receiving_msg():
            msg = wcf.get_msg(block=True, timeout=1.0)
            if msg:
                logger.info(msg)
                #process_message(wcf, msg)
    except KeyboardInterrupt:
        logger.info("收到中断信号，准备停止服务")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
    finally:
        wcf.stop()
        logger.info("服务已停止")

