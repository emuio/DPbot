import json
import re
from datetime import datetime
from xml.etree import ElementTree as ET
from typing import Optional, Dict, List, Any, Union
from loguru import logger

class WxMsg:
    """封装 WebSocket 接收到的 JSON 格式微信消息"""

    def __init__(self, msg: Dict[str, Any], self_wxid: str):
        """初始化 Msg 对象

        Args:
            msg (dict): WebSocket 接收到的 JSON 格式消息
            self_wxid (str): 当前用户的微信 ID，用于判断是否自己发的消息
        """
        self.id = msg.get("MsgId")
        self.from_user_name = msg.get("FromUserName", {}).get("string", "")
        self.to_user_name = msg.get("ToUserName", {}).get("string", "")       
        self.type = msg.get("MsgType")
        self._raw_content = msg.get("Content", {}).get("string", "")
        self._is_group = "@chatroom" in self.from_user_name or "@chatroom" in self.to_user_name
        self._processed_content = self._process_content()
        self.content = self._processed_content
        self.status = msg.get("Status")
        self.img_status = msg.get("ImgStatus")
        self.img_buf = msg.get("ImgBuf", {}).get("iLen", 0)
        self.create_time = msg.get("CreateTime")
        self.msg_source = msg.get("MsgSource", "")
        self.push_content = msg.get("PushContent", "")
        self.new_id = msg.get("NewMsgId")
        self.msg_seq = msg.get("MsgSeq")
        self.self_wxid = self_wxid  # 当前用户 ID
        self._parsed_msg_source = None  # 缓存解析后的msg_source
        self.roomid = self.from_user_name if "@chatroom" in self.from_user_name else self.to_user_name if "@chatroom" in self.to_user_name else None
        self.sender= self._determine_sender()
        self.atusers = self._determine_atusers()  
        self.noAtMsg = self._process_no_at_msg()  # 新增 noAtMsg 属性

    def _process_no_at_msg(self) -> str:
        """处理无@的文本内容"""
        # 匹配 @ 开头，后接非空格/换行/特殊空格的字符，直到遇到这些分隔符
        pattern = r'@[^ \n\u2005]+[ \n\u2005]*'
        return re.sub(pattern, '', self.content).strip()   
    def _process_content(self) -> str:
        """优化后的内容处理方法"""
        content = self._raw_content.strip()
        
        # 群消息处理
        if self.from_group():
            if ':' in content:
                _, sep, text = content.partition(':')
            elif '：' in content:
                _, sep, text = content.partition('：')
            else:
                return content
            return text.strip() if sep else content
        
        # 私聊消息处理
        else:
            return content.split("\n", 1)[-1].strip() if "\n" in content else content    

    def _determine_atusers(self) -> List[str]:
        """从消息源中提取@用户的 wxid 列表，兼容 CDATA 和非 CDATA 格式"""
        if not self.from_group() or not self.msg_source:
            return []
    
    # 优先尝试匹配 CDATA 格式
        match = re.search(r"<atuserlist><!\[CDATA\[(.*?)\]\]></atuserlist>", self.msg_source)
        if not match:
        # 回退匹配非 CDATA 格式
            match = re.search(r"<atuserlist>(.*?)</atuserlist>", self.msg_source)
    
        return [user for user in match.group(1).split(",") if user] if match and match.group(1) else []
    def _determine_sender(self) -> Optional[str]:
        if self.from_self():
            return self.self_wxid
        if not self.from_group():
            return self.from_user_name
        if self._raw_content and "\n" in self._raw_content:
            first_line = self._raw_content.split("\n")[0]
            if first_line.endswith(":"):  # 兼容昵称和wxid
                return first_line[:-1]  # 去掉末尾冒号
        return None
      
                
    def __str__(self) -> str:
        """将 Msg 对象转换为易读字符串"""
        return f"""
        roomid: {self.roomid}
        sender: {self.sender}
        MsgId: {self.id}
        type: {self.type}
        content: {self.content}
        atusers: {', '.join(self.atusers) if self.atusers else 'None'}
        Status: {self.status}
        ImgStatus: {self.img_status}
        ImgBuf Length: {self.img_buf}
        CreateTime: {self.formatted_time}
        MsgSource: {self.msg_source}
        PushContent: {self.push_content}
        NewMsgId: {self.new_id}
        MsgSeq: {self.msg_seq}
        IsGroup: {self.from_group()}
        IsFromSelf: {self.from_self()}
        """

    @property
    def formatted_time(self) -> Optional[str]:
        """返回格式化的消息时间"""
        if self.create_time:
            return datetime.fromtimestamp(self.create_time).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def from_self(self) -> bool:
        """是否自己发的消息

        Returns:
            bool: 如果 FromUserName 等于当前用户 wxid 返回 True
        """
        return self.from_user_name == self.self_wxid

    def from_group(self) -> bool:
        """是否群聊消息

        Returns:
            bool: 如果 FromUserName 或 ToUserName 包含 @chatroom 返回 True
        """
        return self._is_group

    def is_from_friend(self) -> bool:
        """是否来自好友消息(非群聊且非自己发送)"""
        return not self.from_group() and not self.from_self() and "gh_" not in self.sender

    def is_at(self, wxid: str, include_all: bool = False) -> bool:
        """是否被 @

        Args:
            wxid (str): 要检查的微信 ID
            include_all (bool): 是否包含@所有人的情况
            
        Returns:
            bool: 如果消息@了指定 wxid 返回 True
        """
        if not self.from_group():
            return False

        if not self.msg_source:
            return False

        # 检查是否在@列表中
        at_users = re.search(r"<atuserlist>(.*?)</atuserlist>", self.msg_source)
        if not at_users:
            return False

        # 检查是否是@所有人
        if not include_all and re.search(r"@(?:所有人|all|All)", self.content):
            return False

        return wxid in at_users.group(1).split(",")

    def parse_msg_source(self) -> Dict[str, str]:
        """解析 MsgSource 中的 XML 信息
        
        Returns:
            Dict[str, str]: 解析后的键值对，若解析失败返回空字典
        """
        if self._parsed_msg_source is not None:
            return self._parsed_msg_source
            
        if not self.msg_source:
            self._parsed_msg_source = {}
            return {}

        try:
            root = ET.fromstring(self.msg_source)
            result = {}
            for elem in root:
                result[elem.tag] = elem.text or ""
            self._parsed_msg_source = result
            return result
        except ET.ParseError:
            self._parsed_msg_source = {}
            return {}

    def is_from_admin(self, admin_users: List[str]) -> bool:
        """判断消息是否来自管理员
        
        Args:
            admin_users (list): 管理员用户 ID 列表
            
        Returns:
            bool: 如果发送者是管理员返回 True
        """
        sender = self.get_sender()
        return sender in admin_users if sender else False

    def is_text(self) -> bool:
        """是否是文本消息"""
        return self.type == self.MsgType.TEXT

    def is_image(self) -> bool:
        """是否是图片消息"""
        return self.type == self.MsgType.IMAGE

    def is_voice(self) -> bool:
        """是否是语音消息"""
        return self.type == self.MsgType.VOICE

    def is_video(self) -> bool:
        """是否是视频消息"""
        return self.type == self.MsgType.VIDEO


# 示例使用
if __name__ == "__main__":
    # 别人发的群消息，@一个用户
    msg_other = {
        "MsgId": 1748092571,
        "FromUserName": {"string": "53152120103@chatroom"},
        "ToUserName": {"string": "peng729831790"},
        "MsgType": 1,
        "Content": {"string": "wxid_i73nrnun919k12:\n@大鹏 你好"},
        "Status": 3,
        "ImgStatus": 1,
        "ImgBuf": {"iLen": 0},
        "CreateTime": 1743690816,
        "MsgSource": "<msgsource>\n\t<atuserlist>peng729831790</atuserlist>\n\t<bizflag>0</bizflag>\n\t<pua>1</pua>\n\t<silence>0</silence>\n\t<membercount>10</membercount>\n\t<signature>N0_V1_vJkLlL+Y|v1_PU9yDlpz</signature>\n\t<tmp_node>\n\t\t<publisher-id></publisher-id>\n\t</tmp_node>\n</msgsource>\n",
        "PushContent": "佐助在群聊中@了你",
        "NewMsgId": 2188228373154375582,
        "MsgSeq": 830276883
    }

    # 自己发的群消息，@两个用户
    msg_self = {
        "MsgId": 957005197,
        "FromUserName": {"string": "peng729831790"},
        "ToUserName": {"string": "53152120103@chatroom"},
        "MsgType": 1,
        "Content": {"string": "@佐助 @小明 你无语"},
        "Status": 3,
        "ImgStatus": 1,
        "ImgBuf": {"iLen": 0},
        "CreateTime": 1743690857,
        "MsgSource": "<msgsource>\n\t<atuserlist>wxid_i73nrnun919k12,wxid_xiaoming123</atuserlist>\n\t<bizflag>0</bizflag>\n\t<pua>1</pua>\n\t<eggIncluded>1</eggIncluded>\n\t<signature>N0_V1_ecuCG2Ie|v1_fEm56org</signature>\n\t<tmp_node>\n\t\t<publisher-id></publisher-id>\n\t</tmp_node>\n</msgsource>\n",
        "NewMsgId": 7372527516126807637,
        "MsgSeq": 830276888
    }

    # 私聊消息，无@用户
    msg_private = {
        "MsgId": 123456789,
        "FromUserName": {"string": "wxid_abcdefghijk"},
        "ToUserName": {"string": "peng729831790"},
        "MsgType": 1,
        "Content": {"string": "你好，这是私聊消息"},
        "Status": 3,
        "ImgStatus": 1,
        "CreateTime": 1743690900,
        "NewMsgId": 1234567890123456789,
        "MsgSeq": 123456
    }

    # 群消息，@所有人
    msg_all = {
        "MsgId": 987654321,
        "FromUserName": {"string": "53152120103@chatroom"},
        "ToUserName": {"string": "peng729831790"},
        "MsgType": 1,
        "Content": {"string": "wxid_i73nrnun919k12:\n@所有人 集合"},
        "Status": 3,
        "ImgStatus": 1,
        "ImgBuf": {"iLen": 0},
        "CreateTime": 1743690950,
        "MsgSource": "<msgsource>\n\t<atuserlist></atuserlist>\n\t<bizflag>0</bizflag>\n\t<pua>1</pua>\n\t<silence>0</silence>\n\t<membercount>10</membercount>\n\t<signature>N0_V1_vJkLlL+Y|v1_PU9yDlpz</signature>\n</msgsource>\n",
        "PushContent": "佐助在群聊中@了所有人",
        "NewMsgId": 9876543210987654321,
        "MsgSeq": 830276890
    }

    self_wxid = "peng729831790"
    wxmsg_other = WxMsg(msg_other, self_wxid)
    wxmsg_self = WxMsg(msg_self, self_wxid)
    wxmsg_private = WxMsg(msg_private, self_wxid)
    wxmsg_all = WxMsg(msg_all, self_wxid)

    print("=== 别人发的群消息 ===")
    print(wxmsg_other)
    print("From Self:", wxmsg_other.from_self())
    print("From Group:", wxmsg_other.from_group())
    print("Is At (peng729831790):", wxmsg_other.is_at("peng729831790"))
    print("At Users:", wxmsg_other.atusers)
    print("Text Content:", wxmsg_other.get_text_content())
    print("Parsed MsgSource:", wxmsg_other.parse_msg_source())

    print("\n=== 自己发的群消息 ===")
    print(wxmsg_self)
    print("From Self:", wxmsg_self.from_self())
    print("From Group:", wxmsg_self.from_group())
    print("Is At (wxid_i73nrnun919k12):", wxmsg_self.is_at("wxid_i73nrnun919k12"))
    print("Is At (wxid_xiaoming123):", wxmsg_self.is_at("wxid_xiaoming123"))
    print("At Users:", wxmsg_self.atusers)
    print("Text Content:", wxmsg_self.get_text_content())

    print("\n=== 私聊消息 ===")
    print(wxmsg_private)
    print("From Self:", wxmsg_private.from_self())
    print("From Group:", wxmsg_private.from_group())
    print("Is From Friend:", wxmsg_private.is_from_friend())
    print("At Users:", wxmsg_private.atusers)
    print("Text Content:", wxmsg_private.get_text_content())

    print("\n=== 群消息 (@所有人) ===")
    print(wxmsg_all)
    print("From Self:", wxmsg_all.from_self())
    print("From Group:", wxmsg_all.from_group())
    print("Is At (peng729831790):", wxmsg_all.is_at("peng729831790"))
    print("Is At (peng729831790, include_all=True):", wxmsg_all.is_at("peng729831790", include_all=True))
    print("At Users:", wxmsg_all.atusers)
    print("Text Content:", wxmsg_all.get_text_content())