from Config.logger import logger
class JudgeTools:
    def __init__(self):
        pass

    def judgeOneEqualListWord(self, recvWord, systemListWord):
        """
        判断接收消息前面几个字是否跟 触发关键词列表中的相匹配
        :param recvWord:
        :param systemListWord:
        :return:
        """
        for systemWord in systemListWord:
            if recvWord.startswith(systemWord):
                return True
        return False

    def judgeEqualWord(self, recvWord, systemWord):
        """
        判断接收消息和触发关键字完全相同则返回True
        接收消息 == 触发关键字
        :param recvWord: 接收消息
        :param systemWord: 触发关键字
        :return:
        """
        if recvWord.strip() == systemWord.strip():
            return True
        return False

    def judgeEqualListWord(self, recvWord, systemListWord):
        """
        判断接收消息在触发关键字列表中则返回True
        接收消息 in ['触发关键字列表']
        :param recvWord: 接收消息
        :param systemListWord: 触发关键字列表
        :return:
        """
        for listWord in systemListWord:
            if listWord.strip() == recvWord.strip():
                return True
        return False

    def judgeInWord(self, recvWord, systemListWord):
        """
        判断接收消息在触发关键字中则返回True
        接收消息 in 触发关键字
        :param recvWord: 接收消息
        :param systemListWord: 触发关键字列表
        :return: bool
        """
        for systemWord in systemListWord:
            if systemWord in recvWord:
                return True
        return False

    def judgeInListWord(self, recvWord, systemListWord):
        """
        判断触发关键词列表中每一个关键字在接收消息中则返回True
        :param recvWord:
        :param systemListWord:
        :return:
        """
        for listWord in systemListWord:
            if listWord in recvWord:
                return True
        return False

    def judgeSplitAllEqualWord(self, recvWord, systemListWord):
        """
        接收消息以空格切割，判断第一个元素是否在触发关键字列表中则返回True
        :param recvWord:
        :param systemListWord:
        :return:
        """
        if ' ' in recvWord:
            recvWord = recvWord.split(' ')[0]
            for listWord in systemListWord:
                if recvWord == listWord:
                    return True
            return False
        return False

    def judgePointFunction(self, senderPoint, functionPoint):
        """
        判断用户积分是否大于功能积分
        :param senderPoint:
        :param functionPoint:
        :return:
        """
        if int(senderPoint) >= int(functionPoint):
            return True
        return False

    def judge_admin(self, sender: str, admin_list: list) -> bool:
        """
        判断用户是否在管理员列表中
        Args:
            sender: 发送者ID
            admin_list: 管理员列表
        Returns:
            bool: 是否是管理员
        """
        return sender in admin_list

    async def judgeGroupMode(self, roomId, target_mode):
        """
        判断群组是否处于指定模式
        Args:
            roomId: 群组ID
            target_mode: 目标群组模式
        Returns:
            bool: 是否匹配目标模式
        """
        try:
            current_mode = await self.query_group_mode(roomId)
            logger.debug(f"群组 {roomId} 当前模式: {current_mode}, 目标模式: {target_mode}")
            if current_mode is None:
                return False
            return current_mode == target_mode
        except Exception as e:
            logger.error(f"判断群组模式失败: {e}", exc_info=True)
            return False

    async def judgePluginConfig(self, mode, pluginName):
        """
        判断插件是否在插件配置中启用
        Args:
            mode: 模式（private/OTHER/GROUP/ADMIN）
            pluginName: 插件名称
        Returns:
            bool: 插件是否启用
        """
        try:
            enabled = await self.query_plugin_config(mode, pluginName)
            logger.debug(f"插件配置查询结果: {enabled}，模式: {mode}，插件: {pluginName}")
            return bool(enabled)  # 确保返回布尔值
        except Exception as e:
            logger.error(f"判断插件配置失败: {e}", exc_info=True)
            return False

    def judgeAtMe(self, selfId, content, atUserList):
        """
        判断有人@我, @所有人不算
        :param selfId:
        :param atUserList:
        :return:
        """
        if selfId in atUserList and '所有人' not in content:
            return True
        return False
    def judgeAtWho(self, selfId, content, atUserList):
        """
        判断有人@, 我和@所有人不算
        :param selfId:
        :param atUserList:
        :return:
        """
        if atUserList and selfId not in atUserList and '所有人' not in content:
            return True
        return False