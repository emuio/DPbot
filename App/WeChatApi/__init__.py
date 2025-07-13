from .MessageApi import MessageApi
from .FriendApi import FriendApi
from .ChatRoomApi import ChatRoomApi
from .ToolsApi import ToolsApi
from .LoginApi import LoginApi
from .CommonApi import CommonApi
class WeChatApi(MessageApi, FriendApi, ChatRoomApi, ToolsApi, LoginApi, CommonApi):
    """
    微信API主类
    集成了所有功能模块
    """

    def __init__(self):
        MessageApi.__init__(self)
        FriendApi.__init__(self)
        ChatRoomApi.__init__(self)
        ToolsApi.__init__(self)
        LoginApi.__init__(self)
        CommonApi.__init__(self)
