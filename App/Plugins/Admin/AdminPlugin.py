from Plugins._Tools import Tools
from Config.logger import logger
import Config.ConfigServer as Cs
from Core.PluginBase import PluginBase
import os

class AdminPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "Admin"
        self.description = "管理员管理插件"
        self.version = "1.0.0"
        self.author = "大鹏"
        self.tools = Tools()  
        
              
        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.adminConfig = self.configData.get('AdminConfig')
        self.DPBotConfig = Cs.returnConfigData().get('DPBotConfig')
        self.Administrators = self.DPBotConfig.get('Administrators')
        self.enablePlugin = self.configData.get('AdminPlugin').get('enablePlugin')
        self.unablePlugin = self.configData.get('AdminPlugin').get('unablePlugin')
        self.menuPlugin = self.configData.get('AdminPlugin').get('menuPlugin')
        self.restartPlugin = self.configData.get('AdminPlugin').get('restartPlugin')
        self.addPlugin = self.configData.get('AdminPlugin').get('addPlugin')
        self.delPlugin = self.configData.get('AdminPlugin').get('delPlugin')
        self.initPlugin = self.configData.get('AdminPlugin').get('initPlugin')
    async def _handle_admin_change(self, msg, is_add=True):
        """处理管理员添加或删除"""
        if not msg.atusers:
            await self.dp.sendText(f"请@要{'添加' if is_add else '删除'}的管理员", msg.sender, msg.self_wxid)
            return True
            
        for user in msg.atusers:
            try:
                is_admin = await self.tools.query_admin(msg.roomid, user)
                if is_add and is_admin:
                    await self.dp.sendText("该用户已经是管理员", msg.sender, msg.self_wxid)
                    return True
                if not is_add and not is_admin:
                    await self.dp.sendText("该用户不是管理员", msg.sender, msg.self_wxid)
                    return True
                    
                if is_add:
                    await self.tools.add_admin(msg.roomid, user)
                else:
                    await self.tools.del_admin(msg.roomid, user)
            except Exception as e:
                logger.error(f"{'添加' if is_add else '删除'}管理员 {user} 失败: {e}")
                await self.dp.sendText(f"{'添加' if is_add else '删除'}管理员失败", msg.sender, msg.self_wxid)
                return True
                
        await self.dp.sendText(f"{'添加' if is_add else '删除'}管理员成功", msg.sender, msg.self_wxid)
        return True

    async def _handle_mode_change(self, msg, mode=None):
        """处理群组模式设置或移除"""
        current_mode = await self.tools.query_group_mode(msg.roomid)
        
        # 移除模式
        if mode is None:
            if not current_mode:
                await self.dp.sendText("群组当前没有设置模式", msg.sender, msg.self_wxid)
                return True
            try:
                await self.tools.delete_group_mode(msg.roomid)
                await self.dp.sendText(f"成功移除群组{current_mode[0]}模式", msg.sender, msg.self_wxid)
            except Exception as e:
                logger.error(f"移除群组{current_mode[0]}模式失败: {e}")
                await self.dp.sendText(f"移除群组{current_mode[0]}模式失败", msg.sender, msg.self_wxid)
            return True
            
        # 设置模式
        if current_mode and current_mode[0] in ["admin", "custom"]:
            logger.debug(f"群组已经是{current_mode[0]}模式")
            await self.dp.sendText(f"群组已经是{current_mode[0]}模式", msg.sender, msg.self_wxid)
            return True
            
        try:
            await self.tools.set_group_mode(msg.roomid, mode)
            await self.dp.sendText(f"设置群组为{mode}模式成功", msg.sender, msg.self_wxid)
        except Exception as e:
            logger.error(f"设置群组{mode}模式失败: {e}")
            await self.dp.sendText(f"设置群组{mode}模式失败", msg.sender, msg.self_wxid)
        return True

    async def _handle_plugin_change(self, msg, operation: str):
        """处理插件变更
        Args:
            msg: 消息对象
            operation: 操作类型，可选值：'add', 'delete', 'enable', 'disable', 'query'
        """
        # 检查群组模式
        current_mode = await self.tools.query_group_mode(msg.roomid)
        logger.debug(f"当前群组模式:{current_mode[0]}")
        if current_mode[0] not in ["custom", "admin"]:
            await self.dp.sendText("当前群组模式不支持插件管理", msg.sender, msg.self_wxid)
            return False
        
        # 解析插件名称（去掉命令前缀）
        plugin_name = msg.content.split(' ', 1)[1] if ' ' in msg.content else None
        if not plugin_name and operation != 'query':
            await self.dp.sendText("请指定插件名称", msg.sender, msg.self_wxid)
            return True

        try:
            if operation == 'add':
                # 添加插件（默认禁用状态）
                success = await self.tools.set_plugin_config(current_mode[0], plugin_name, False)
                if success:
                    await self.dp.sendText(f"添加插件 {plugin_name} 成功", msg.sender, msg.self_wxid)
                else:
                    await self.dp.sendText(f"添加插件 {plugin_name} 失败", msg.sender, msg.self_wxid)

            elif operation == 'delete':
                # 删除插件配置
                success = await self.tools.delete_plugin_config(current_mode[0], plugin_name)
                if success:
                    await self.dp.sendText(f"删除插件 {plugin_name} 成功", msg.sender, msg.self_wxid)
                else:
                    await self.dp.sendText(f"删除插件 {plugin_name} 失败", msg.sender, msg.self_wxid)

            elif operation == 'enable':
                # 启用插件
                success = await self.tools.set_plugin_config(current_mode[0], plugin_name, True)
                if success:
                    await self.dp.sendText(f"启用插件 {plugin_name} 成功", msg.sender, msg.self_wxid)
                else:
                    await self.dp.sendText(f"启用插件 {plugin_name} 失败", msg.sender, msg.self_wxid)

            elif operation == 'disable':
                # 禁用插件
                success = await self.tools.set_plugin_config(current_mode[0], plugin_name, False)
                if success:
                    await self.dp.sendText(f"禁用插件 {plugin_name} 成功", msg.sender, msg.self_wxid)
                else:
                    await self.dp.sendText(f"禁用插件 {plugin_name} 失败", msg.sender, msg.self_wxid)

            elif operation == 'query':
                # 查询所有插件状态
                enabled_plugins = await self.tools.get_enabled_plugins(current_mode[0])
                all_plugins = await self.tools.list_plugin_configs()
                
                if not all_plugins:
                    await self.dp.sendText("当前没有配置任何插件", msg.sender, msg.self_wxid)
                    return True
                
                # 构建插件状态消息
                status_msg = "插件状态列表：\n"
                for plugin in all_plugins:
                    status = "✅ 已启用" if plugin in enabled_plugins else "❌ 已禁用"
                    status_msg += f"{plugin}: {status}\n"
                
                await self.dp.sendText(status_msg, msg.sender, msg.self_wxid)

        except Exception as e:
            logger.error(f"处理插件{operation}操作出错: {e}")
            await self.dp.sendText(f"处理插件操作失败", msg.sender, msg.self_wxid)
        
        return True
    
    async def plugin_init(self):
        """插件初始化，从 Excel 读取插件配置并写入数据库"""
        try:
            import pandas as pd
            from DbServer.DbAdminServer import DbAdminServer

            # 初始化数据库服务
            db_server = DbAdminServer()
            
            # 读取 Excel 文件
            excel_path = "Config/plugininit.xlsx"
            if not os.path.exists(excel_path):
                logger.error(f"插件配置文件不存在: {excel_path}")
                return
                
            df = pd.read_excel(excel_path)
            
            # 遍历每一行数据
            for _, row in df.iterrows():
                plugin_name = row['name']
                # 分别设置三种模式的配置
                # admin 模式 (群组模式, mode=1)
                await db_server.set_plugin_config('admin', plugin_name, bool(int(row['admin'])))
                # custom 模式 (自定义模式, mode=2)
                await db_server.set_plugin_config('custom', plugin_name, bool(int(row['custom'])))
                # private 模式 (私聊模式, mode=3)
                await db_server.set_plugin_config('private', plugin_name, bool(int(row['private'])))
                
            logger.success("插件配置初始化完成")
            
        except Exception as e:
            logger.error(f"插件初始化失败: {e}")

    async def should_handle_message(self, msg) -> bool:
        """判断是否应该处理消息
        Args:
            msg: 消息对象
        Returns:
            bool: 是否为管理员
        """
        # 检查是否为配置文件中的管理员
        if msg.sender in self.Administrators:
            return True
            
        # 检查是否为数据库中的管理员
        is_admin = await self.tools.query_admin(msg.roomid, msg.sender)
        return is_admin

    async def handle_admin_message(self, msg) -> bool:
        """处理管理员消息，这个方法会被优先调用，不受插件配置影响
        Args:
            msg: 消息对象
        Returns:
            bool: 是否处理成功
        """
        try:
            # 处理插件管理命令
            if msg.content == "测试":
                return await self.dp.sendImage("https://p26-sign.douyinpic.com/tos-cn-i-0813c001/oMAxt78xDQBsSfybAiFADo9PFCfUoAAIEUglAP~tplv-dy-lqen-new:1920:1440:q80.webp?lk3s=138a59ce&x-expires=1754038800&x-signature=ebvrnCI%2Fy6Bp32BpZDLzP2%2Bw2Xo%3D&from=327834062&s=PackSourceEnum_DOUYIN_REFLOW&se=false&sc=image&biz_tag=aweme_images&l=20250702173333E9A34C2182C106384D8A",msg.roomid,msg.self_wxid)
            if self.tools.judgeSplitAllEqualWord(msg.content, self.addPlugin):
                return await self._handle_plugin_change(msg, 'add')
            
            elif self.tools.judgeSplitAllEqualWord(msg.content, self.delPlugin):
                return await self._handle_plugin_change(msg, 'delete')
            
            elif self.tools.judgeSplitAllEqualWord(msg.content, self.enablePlugin):
                return await self._handle_plugin_change(msg, 'enable')
            
            elif self.tools.judgeSplitAllEqualWord(msg.content, self.unablePlugin):
                return await self._handle_plugin_change(msg, 'disable')
            
            elif self.tools.judgeEqualListWord(msg.content, self.menuPlugin):
                return await self._handle_plugin_change(msg, 'query')

            # 添加管理员
            if self.tools.judgeEqualListWord(msg.noAtMsg, self.adminConfig.get('addAdminSymbol')):
                return await self._handle_admin_change(msg, is_add=True)
            
            # 删除管理员
            elif self.tools.judgeEqualListWord(msg.noAtMsg, self.adminConfig.get('delAdminSymbol')):
                return await self._handle_admin_change(msg, is_add=False)
            
            # 设置群组模式
            elif self.tools.judgeEqualListWord(msg.content, self.adminConfig.get('setGroupAdminModeSymbol')):
                return await self._handle_mode_change(msg, "admin")
            
            elif self.tools.judgeEqualListWord(msg.content, self.adminConfig.get('setGroupCustomModeSymbol')):
                return await self._handle_mode_change(msg, "custom")
            
            # 移除群组模式
            elif self.tools.judgeEqualListWord(msg.content, self.adminConfig.get('delGroupmModeSymbol')):
                return await self._handle_mode_change(msg)
            
            # 重启插件
            elif self.tools.judgeEqualListWord(msg.content, self.restartPlugin):
                return await self._handle_plugin_restart(msg)

            # 插件初始化
            elif self.tools.judgeEqualListWord(msg.content, self.initPlugin):
                return await self.plugin_init()

            return False
            
        except Exception as e:
            logger.error(f"处理管理员消息出错: {e}")
            return False

    async def handle_message(self, msg) -> bool:
        """处理普通消息，这个方法会受到插件配置的影响
        Args:
            msg: 消息对象
        Returns:
            bool: 是否处理成功
        """
        # 管理员插件的普通消息处理逻辑
        # 由于核心功能都在 handle_admin_message 中，这里可以直接返回 False
        return False


    async def handle_private_message(self, msg) -> bool:
        """处理私聊消息
        Args:
            msg: 消息对象
        Returns:
            bool: 是否处理成功
        """
        