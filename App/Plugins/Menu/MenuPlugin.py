from Plugins._Tools import Tools
from Config.logger import logger
import Config.ConfigServer as Cs
from Core.PluginBase import PluginBase
import os

class MenuPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.tools = Tools()
        self.name = "Menu"
        self.description = "菜单插件"
        self.version = "1.0.0"
        self.author = "大鹏"

        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.menu = self.configData.get('menu')

    async def handle_message(self, msg):
        if self.tools.judgeEqualListWord(msg.content, self.menu):
            await self.dp.sendText(await self.menu_list(), msg.roomid, msg.self_wxid)
            return True
        return False

    async def menu_list(self):
        helpMsg = '========💌菜单💌========\n'
        helpMsg += '⛳签到 🥇排行榜 🧧领个低保\n'
        helpMsg += '👀找茬 💡猜成语 📃古诗答题\n'
        helpMsg += '🔫打劫 💖塔罗牌 🔮星座运势\n'
        helpMsg += '⛅天气 🔍查快递 🔎明星百科\n'
        helpMsg += '🎬️搜剧 📚️领教材 📱在线客服\n'
        helpMsg += '👙骚话 😄讲笑话 🐶舔狗日记\n'
        helpMsg += '🍒情话 🥘毒鸡汤 😄走心文案\n'
        helpMsg += '🔗短链 🏷️发卡片 🐴转二维码\n'
        helpMsg += '🚕打车 🍔饿了么 🍱美团外卖\n'
        helpMsg += '🚚货运 🥘霸王餐 🚗代驾加油\n'
        helpMsg += '🏪超市 🥬买蔬菜 🦐生鲜水果\n'
        helpMsg += '🌼晒单 🛍️返利购 💎兑换钻石\n'
        helpMsg += '【仅管理可用】\n'
        helpMsg += '======================\n'

        return helpMsg


if __name__ == "__main__":
    plugin = MenuPlugin()
    plugin.handle_message("123")

