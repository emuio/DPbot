#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "8.0.5.7"  # 更新版本号

import json
import time
import threading
from queue import Queue, Empty
from typing import Dict, Optional
import websockets.sync.client
from wcfriend.wxmsg import WxMsg
#from logger import logger
from loguru import logger
import requests
import random
import base64
import os


class Wcf:
    """微信通信框架（WeChatFriend）"""

    def __init__(self, self_wxid, base_url, ws_url, max_retries: int = 3, retry_delay: int = 5):
        """
        初始化微信通信框架
        
        Args:
            self_wxid (str): 当前用户的微信ID
            base_url (str): API基础URL
            max_retries (int): 最大重试次数
            retry_delay (int): 初始重试延迟（秒）
        """
        logger.info(f"wcfriend version: {__version__}")
        self.self_wxid = self_wxid
        self.uri = f"{ws_url}?wxid={self_wxid}"
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._is_receiving_msg = False
        self.msgQ = Queue()  # 消息队列
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        self._msg_thread = None
        self._stop_event = threading.Event()

    def _request(self, endpoint: str, payload: Dict = None, timeout: float = 10.0) -> Dict:
        try:
            resp = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self.headers,
                timeout=timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_qrcode(self, device_id: str = "5211314", device_name: str = "dpbot") -> Dict:
        response = self._request("/api/Login/GetQRx", {
            "DeviceID": device_id,
            "DeviceName": device_name,
            "Proxy": {"ProxyIp": "", "ProxyPassword": "", "ProxyUser": ""}
        })
    # 提取所需字段
        data = response.get("Data", {})
        return {
            "Uuid": data.get("Uuid", ""),
            "QrUrl": data.get("QrUrl", ""),
            "QrBase64":data.get("QrBase64", "")
        }
    def checkQR(self, uuid: str) -> Dict:
        response = self._request("/api/Login/CheckQR", {"uuid": uuid})
        logger.debug(f"CheckQR response: {response}")
        if not isinstance(response, dict):
            logger.error(f"Invalid response type: {type(response)}, response: {response}")
            return {
                "Code": -1,
                "Message": "Invalid API response",
                "userName": "",
                "nickName": "",
                "alias": ""
            }
        if not response.get("Success", False):
            logger.error(f"API request failed: {response.get('Message', 'Unknown error')}")
            return {
                "Code": response.get("Code", -1),
                "Message": response.get("Message", "API request failed"),
                "userName": "",
                "nickName": "",
                "alias": ""
            }
        data = response.get("Data") or {}
        acct_sect_resp = data.get("acctSectResp", {})
        return {
            "Code": response.get("Code", 0),
            "Message": response.get("Message", ""),
            "userName": acct_sect_resp.get("userName", ""),
            "nickName": acct_sect_resp.get("nickName", ""),
            "alias": acct_sect_resp.get("alias", "")
        }
    def send_image(self, path: str, receiver: str) -> Dict:
        """
        发送图片消息，自动将图片转为base64格式

        Args:
            path (str): 图片文件的路径
            receiver (str): 接收者的Wxid

        Returns:
            Dict: 来自API的响应，如果发生错误则返回错误信息
        """
        try:
            logger.info(f"准备发送图片: {path} 到 {receiver}")
            
            # 检查文件是否存在
            if not os.path.exists(path):
                logger.error(f"文件未找到: {path}")
                return {"status": "error", "message": "文件未找到"}
                
            # 读取图片文件并转为base64
            with open(path, "rb") as image_file:
                image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 发送请求
            return self._request("/api/Msg/UploadImg", {
                "Base64": base64_image,
                "ToWxid": receiver,
                "Wxid": self.self_wxid
            })
        except FileNotFoundError:
            logger.error(f"文件未找到: {path}")
            return {"status": "error", "message": "文件未找到"}
        except Exception as e:
            logger.error(f"发送图片时发生错误: {e}")
            return {"status": "error", "message": str(e)}
    def accept_new_friend(self, v3: str, v4: str, scene: int) -> Dict:
        return self._request("/api/Friend/PassVerify", {
            "v1": v3,
            "v2": v4,
            "scene": scene,
            "Wxid": self.self_wxid
        })
    def send_text(self, msg: str, receiver: str, at: str = None) -> Dict:
        return self._request("/api/Msg/SendTxt", {
            "At": at or "",
            "Content": msg,
            "ToWxid": receiver,
            "Type": 0,
            "Wxid": self.self_wxid
        })
    def invite_chatroom_members(self, roomid: str, wxid: str) -> int:
        return self._request("/api/Group/InviteChatRoomMember", {
            "ChatRoomName": roomid,
            "ToWxids": wxid,
            "Wxid": self.self_wxid
        })  

    def get_alias_in_chatroom(self, wxid: str, roomid: str) -> Dict:
        """
        获取指定用户在聊天室中的别名（昵称）及其他相关信息。

        Args:
            wxid (str): 要查找的用户的微信ID。
            roomid (str): 聊天室的ID。

        Returns:
            Dict: 包含用户详细信息（昵称、用户名等）的字典，如果未找到用户或请求失败则返回错误信息。
        """
        response = self._request("/api/Group/GetChatRoomMemberDetail", {
            "QID": roomid,
            "Wxid": self.self_wxid
        })
        
        # 检查响应是否成功
        if response.get("Code") != 0 or not response.get("Success"):
            return {"error": "请求失败", "message": response.get("Message", "未知错误")}
        
        # 提取聊天室成员列表
        member_list = response.get("Data", {}).get("NewChatroomData", {}).get("ChatRoomMember", [])
        #logger.debug(response)
        # 遍历成员列表，查找匹配的 wxid
        for member in member_list:
            if member.get("UserName") == wxid:
                return {
                    "wxid": member.get("UserName"),
                    "nickname": member.get("NickName"),
                    "big_head_img": member.get("BigHeadImgUrl", ""),
                    "small_head_img": member.get("SmallHeadImgUrl", ""),
                    "chatroom_member_flag": member.get("ChatroomMemberFlag"),
                    "inviter_username": member.get("InviterUserName", "")
                }
        
        # 如果未找到匹配的用户
        return {"error": "用户未找到", "message": f"wxid {wxid} 在聊天室 {roomid} 中不存在"}
    def get_info_by_roomid(self, roomid: str) -> dict:
        resp = self._request("/api/Group/GetChatRoomInfo", {"QID": roomid, "Wxid": self.self_wxid})
        if resp.get("Code") != 0 or not resp.get("Success"):
            return {"error": "请求失败", "message": resp.get("Message", "未知错误")}
        
        data = resp.get("Data", {}).get("ContactList", [{}])[0]
        group_name = data.get("NickName", {}).get("string", "")
        members = data.get("NewChatroomData", {}).get("ChatRoomMember", [])
        
        member_list = [{"username": m.get("UserName", ""), "nickname": m.get("NickName", "")} for m in members]
        
        return {
            "group_name": group_name,
            "members": member_list,
            "member_count": len(member_list)
        }
    def get_info_by_wxid(self, wxid: str) -> dict:
        resp = self._request("/api/Friend/GetContractDetail", {"ChatRoom": "string","Towxids": wxid, "Wxid": self.self_wxid})
        if resp.get("Code") != 0 or not resp.get("Success"):
            return {"error": "请求失败", "message": resp.get("Message", "未知错误")}
        #logger.debug(resp)
        data = resp.get("Data", {}).get("ContactList", [{}])[0]
        return {
            "nickname": data.get("NickName", {}).get("string", ""),
            "avatar": data.get("BigHeadImgUrl", ""),
            "country": data.get("Country", ""),
            "city": data.get("City", ""),
            "province": data.get("Province", ""),
            "alias": data.get("Alias", "")
        }
        
    def is_receiving_msg(self) -> bool:
        """检查是否已启动消息接收功能"""
        return self._is_receiving_msg

    def enable_receiving_msg(self) -> bool:
        """启用消息接收功能"""
        if self._is_receiving_msg:
            return True

        self._is_receiving_msg = True
        self._stop_event.clear()
        self._msg_thread = threading.Thread(
            target=self._message_loop,
            name=f"MessageReceiver_{self.self_wxid}",
            daemon=True
        )
        self._msg_thread.start()
        return True

    def disable_receiving_msg(self) -> None:
        """禁用消息接收功能"""
        self._is_receiving_msg = False
        self._stop_event.set()
        if self._msg_thread:
            self._msg_thread.join(timeout=2.0)  # 设置超时避免长时间等待
            self._msg_thread = None

    def get_msg(self, block: bool = True, timeout: float = None) -> Optional[WxMsg]:
        """从消息队列获取消息
        
        Args:
            block (bool): 是否阻塞等待消息
            timeout (float): 阻塞超时时间（秒）
        
        Returns:
            Optional[WxMsg]: 消息对象或 None
        """
        try:
            return self.msgQ.get(block=block, timeout=timeout)
        except Empty:
            return None

    def _message_loop(self):
        """消息接收主循环"""
        retries = 0
        while self._is_receiving_msg and retries < self.max_retries:
            try:
                with websockets.sync.client.connect(self.uri, open_timeout=10) as ws:
                    logger.info("WebSocket连接成功")
                    retries = 0  # 重置重试计数
                    while self._is_receiving_msg:
                        try:
                            message = ws.recv()
                            self._process_raw_message(message)
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket连接已关闭")
                            break
                        except Exception as e:
                            logger.error(f"接收消息错误: {e}")
            except Exception as e:
                retries += 1
                delay = self.retry_delay * (2 ** retries) + random.uniform(0, 1)  # 指数退避 + 随机抖动
                logger.error(f"连接失败: {e}，将在 {delay:.2f} 秒后重试（第 {retries}/{self.max_retries} 次）")
                if self._is_receiving_msg:
                    time.sleep(delay)

        if retries >= self.max_retries:
            logger.error("达到最大重试次数，停止尝试")
            self.disable_receiving_msg()

    def _process_raw_message(self, message: str):
        """处理原始消息，仅解析并放入队列"""
        try:
            msg_json = json.loads(message)
            msg = WxMsg(msg_json, self.self_wxid)
            self.msgQ.put(msg)  # 将消息放入队列
        except json.JSONDecodeError as e:
            logger.error(f"无效的JSON消息: {message}，错误: {e}")

    def start(self):
        """启动服务"""
        self.enable_receiving_msg()

    def stop(self):
        """停止服务"""
        self.disable_receiving_msg()
        logger.info("服务已停止")