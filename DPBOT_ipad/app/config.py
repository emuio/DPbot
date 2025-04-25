#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# 基本配置
ENV = os.environ.get("ENV", "development")

# WebSocket配置
WXAPI_HOST = os.environ.get("WXAPI_HOST", "wxapi")
WXAPI_WS_PORT = int(os.environ.get("WXAPI_WS_PORT", 8899))
#WXAPI_WS_URL = f"ws://localhost:8899/ws"  #本地测试
WXAPI_PORT = int(os.environ.get("WXAPI_PORT", 8057))

WXAPI_URL = f"http://{WXAPI_HOST}:{WXAPI_PORT}"  #docker
#WXAPI_URL = f"http://localhost:8057" #本地测试
SELFWXID = os.environ.get("WXID", "wxid_yby6o1jbfqyd12")
#WXAPI_WS_URL = f"ws://{WXAPI_HOST}:{WXAPI_WS_PORT}/ws"   #docker
# 用户配置
DEFAULT_WXID = os.environ.get("WXID", "wxid_yby6o1jbfqyd12")# 机器人的wxid

# 日志配置
LOG_DIR = os.environ.get("LOG_DIR", "/python-app/logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
WECHAT_LOG_LEVEL = os.environ.get("WECHAT_LOG_LEVEL", "DEBUG")
WECHAT_LOG_FORMAT = os.environ.get("WECHAT_LOG_FORMAT", 
                                 "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")

# 管理员用户列表
ADMIN_USERS = os.environ.get("ADMIN_USERS", "").split(",") if os.environ.get("ADMIN_USERS") else [] 