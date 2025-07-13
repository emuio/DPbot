import os
import asyncio
import tomlkit
from typing import Optional, Dict
from Config.logger import logger
from WeChatApi import WeChatApi
import aiohttp
import qrcode
from qrcode.main import QRCode
from qrcode import constants
from io import StringIO
from urllib.parse import urlparse, parse_qs

class LoginManager:
    def __init__(self):
        self.config_path = "Config/Login.toml"
        self.config = self._load_or_create_config()
        self.api_url = f"http://{self.config['DPBotConfig']['DPBotApi']}:{self.config['DPBotConfig']['DPBotPort']}"
        self.api = WeChatApi()

    def _extract_weixin_url(self, url: str) -> str:
        """从完整 URL 中提取微信登录链接
        Args:
            url: 完整的 URL
        Returns:
            str: 微信登录链接
        """
        try:
            parsed = urlparse(url)
            if parsed.query:
                params = parse_qs(parsed.query)
                if 'data' in params:
                    return params['data'][0]
            return url
        except Exception as e:
            logger.error(f"提取微信登录链接失败: {e}")
            return url

    def _print_qr_in_terminal(self, url: str) -> None:
        """在终端中显示二维码
        Args:
            url: 二维码URL
        """
        # 提取实际的微信登录链接
        weixin_url = self._extract_weixin_url(url)
        logger.debug(f"生成二维码的实际链接: {weixin_url}")

        # 创建优化的二维码实例
        qr = QRCode(
            version=1,
            error_correction=constants.ERROR_CORRECT_L,
            box_size=2,
            border=1
        )
        qr.add_data(weixin_url)
        qr.make(fit=True)
        
        # 在终端中显示二维码（反色显示，提高可读性）
        qr.print_ascii(invert=True)

    def _load_or_create_config(self) -> Dict:
        """加载或创建配置文件"""
        if not os.path.exists(self.config_path):
            default_config = {
                'DPBotConfig': {
                    'DPBotApi': '127.0.0.1',
                    'DPBotPort': '8059',
                    'selfWxid': '',
                    'nickName': '',
                    'alias': '',
                    'bindMobile': ''
                }
            }
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                tomlkit.dump(default_config, f)
            return default_config
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return tomlkit.load(f)
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            return self._load_or_create_config()

    def _save_config(self, user_info: Dict) -> None:
        """保存用户信息到配置文件"""
        try:
            self.config['DPBotConfig'].update({
                'selfWxid': user_info.get('userName', ''),
                'nickName': user_info.get('nickName', ''),
                'alias': user_info.get('alias', ''),
                'bindMobile': user_info.get('bindMobile', '')
            })
            with open(self.config_path, 'w', encoding='utf-8') as f:
                tomlkit.dump(self.config, f)
        except Exception as e:
            logger.error(f'保存配置文件失败: {e}')

    async def check_server(self) -> bool:
        """检查服务器连接状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"检查服务器连接失败: {e}")
            return False

    async def twice_login(self) -> bool:
        """二次登录"""
        wxid = self.config["DPBotConfig"].get("selfWxid")
        logger.debug(f"二次登录的wxid: {wxid}")
        if not wxid:
            logger.error("未找到wxid，无法进行二次登录")
            return False

        try:
            result = await self.api.TwiceLogin(wxid)
            return result
        except Exception as e:
            logger.error(f"二次登录失败: {e}")
            return False

    async def get_qr_code(self) -> Optional[Dict]:
        """获取登录二维码"""
        try:
            result = await self.api.getIpadQr()
            if result and result.get("Code") == 1:
                return result.get("Data")
            return None
        except Exception as e:
            logger.error(f"获取二维码失败: {e}")
            return None

    async def check_qr_status(self, uuid: str) -> Optional[Dict]:
        """检查二维码状态"""
        try:
            result = await self.api.checkqr(uuid)
            if result and result.get('Code') == 0:
                return result.get('Data', {}).get('acctSectResp', {})
            return None
        except Exception as e:
            logger.error(f'检查二维码状态失败: {e}')
            return None

    async def login_process(self) -> bool:
        """登录流程处理"""
        # 检查服务器连接
        if not await self.check_server():
            logger.error("无法连接到框架服务器")
            return False

        # ANSI 颜色代码
        CYAN = "\033[36m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RESET = "\033[0m"
        BOLD = "\033[1m"

        logger.success("框架正常运行")
        print(f"\n{CYAN}┌──────────── 登录选项 ────────────┐{RESET}")
        print(f"{CYAN}│{RESET}                                  {CYAN}│{RESET}")
        print(f"{CYAN}│  {YELLOW}(1) {GREEN}>>{RESET} 跳过登录                 {CYAN}│{RESET}")
        print(f"{CYAN}│  {YELLOW}(2) {GREEN}>>{RESET} 重新登录                 {CYAN}│{RESET}")
        print(f"{CYAN}│  {YELLOW}(3) {GREEN}>>{RESET} 二次登录                 {CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}                                  {CYAN}│{RESET}")
        print(f"{CYAN}│        {BOLD}请输入对应数字{RESET}            {CYAN}│{RESET}")
        print(f"{CYAN}└──────────────────────────────────┘{RESET}")

        choice = input(f"\n{BOLD}请输入选择(1-3): {RESET}")

        if choice == "1":
            return True
        elif choice == "3":
            result = await self.twice_login()
            logger.debug(f"二次登录结果: {result}")
            if result and result.get('Code') == 0:
                logger.info("二次登录成功")
                return True
            else:
                logger.error("二次登录失败")
                return False
        
        elif choice == "2":
            # 获取二维码
            qr_data = await self.get_qr_code()
            logger.info(f'获取二维码: {qr_data}')
            if not qr_data:
                logger.error('获取二维码失败')
                return False

            print('请使用微信扫描以下二维码登录:')
            self._print_qr_in_terminal(qr_data['QrUrl'])
            uuid = qr_data['Uuid']
            logger.info(f'获取二维码UUID: {uuid}')
            # 循环检查二维码状态
            while True:
                await asyncio.sleep(2)
                logger.info(f'检查二维码状态: {uuid}')
                user_info = await self.check_qr_status(uuid)
                logger.info(f'再检查二维码状态: {user_info}')
                if user_info:
                    print(f'登录成功！')
                    print(f'昵称: {user_info.get("nickName", "未知")}')
                    print(f'别名: {user_info.get("alias", "未知")}')
                    print(f'手机: {user_info.get("bindMobile", "未知")}')
                    
                    # 保存用户信息
                    self._save_config(user_info)
                    return True

        return False
