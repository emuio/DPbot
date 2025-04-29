from BotServer.BotFunction.InterfaceFunction import *
from ApiServer.ApiMainServer import ApiMainServer
from BotServer.BotFunction.JudgeFuncion import *
from DbServer.DbMainServer import DbMainServer
import Config.ConfigServer as Cs


class PointFunction:
    def __init__(self, wcf):
        """
        积分功能
        :param wcf:
        """
        self.wcf = wcf
        self.Ams = ApiMainServer()
        self.Dms = DbMainServer()
        configData = Cs.returnConfigData()

        # 积分功能关键词配置
        self.aiWenKeyWords = configData['FunctionConfig']['PointFunctionConfig']['AiWenIpConfig']['AiWenKeyWords']
        self.md5KeyWords = configData['FunctionConfig']['PointFunctionConfig']['Cmd5Config']['Cmd5KeyWords']
        self.signKeyWord = configData['FunctionConfig']['PointFunctionConfig']['SignConfig']['SignKeyWord']
        self.aiPicKeyWords = configData['FunctionConfig']['PointFunctionConfig']['AiPicConfig']['AiPicKeyWords']
        self.searchPointKeyWord = configData['FunctionConfig']['PointFunctionConfig']['SearchPointConfig'][
            'SearchPointKeyWords']

    def mainHandle(self, message):
        content = message.content.strip()
        sender = message.sender
        roomId = message.roomid
        msgType = message.type
        atUserLists, noAtMsg = getAtData(message)
        if msgType == 1:
            # 埃文IPV4地址查询
            if judgeSplitAllEqualWord(content, self.aiWenKeyWords):
                ip = content.split(' ')[-1]
                aiWenData = self.Ams.getAiWen(ip)
                if not aiWenData:
                    self.wcf.send_text(
                        f'@{getIdName(self.wcf, sender, roomId)} 埃文IP地址查询接口出现错误, 请联系超管查看控制台输出日志',
                        receiver=roomId)
                    return
                mapsPaths = aiWenData['maps']
                for mapsPath in mapsPaths:
                    self.wcf.send_image(mapsPath, receiver=roomId)
                aiWenMessage = aiWenData['message']
                self.wcf.send_text(f'@{getIdName(self.wcf, sender, roomId)} 查询结果如下\n{aiWenMessage}',
                                   receiver=roomId)

            # CMD5查询
            elif judgeSplitAllEqualWord(content, self.md5KeyWords):
                ciphertext = content.split(' ')[-1]
                plaintext = self.Ams.getCmd5(ciphertext)
                if not plaintext:
                    self.wcf.send_text(
                        f'@{getIdName(self.wcf, sender, roomId)} MD5解密接口出现错误, 请联系超管查看控制台输出日志',
                        receiver=roomId)
                    return
                self.wcf.send_text(
                    f'@{getIdName(self.wcf, sender, roomId)}\n密文: {ciphertext}\n明文: {plaintext}',
                    receiver=roomId,
                    aters=sender)
            # 签到口令提示
            elif judgeEqualWord(content, '签到'):
                self.wcf.send_text(
                    f'@{getIdName(self.wcf, sender, roomId)} 签到失败\n签到口令已改为：{self.signKeyWord}',
                    receiver=roomId)
            # 签到
            elif judgeEqualWord(content, self.signKeyWord):
                if not self.Dms.sign(wxId=sender, roomId=roomId):
                    self.wcf.send_text(
                        f'@{getIdName(self.wcf, sender, roomId)} 签到失败, 当日已签到！！！\n当前剩余积分: {self.Dms.searchPoint(sender, roomId)}',
                        receiver=roomId)
                    return
                self.wcf.send_text(
                    f'@{getIdName(self.wcf, sender, roomId)} 签到成功, 当前剩余积分: {self.Dms.searchPoint(sender, roomId)}\n复活版👉https://github.com/dpyyds/DPbot',
                    receiver=roomId)
            # 查询积分
            elif judgeEqualListWord(content, self.searchPointKeyWord):
                userPoint = self.Dms.searchPoint(sender, roomId)
                if userPoint == False and not userPoint == 0:
                    self.wcf.send_text(
                        f'@{getIdName(self.wcf, sender, roomId)} 积分查询出现错误, 请联系超管查看控制台输出日志',
                        receiver=roomId)
                    return
                self.wcf.send_text(
                    f'@{getIdName(self.wcf, sender, roomId)} 当前剩余积分: {self.Dms.searchPoint(sender, roomId)}',
                    receiver=roomId)
            # Ai对话
            elif judgeAtMe(self.wcf.self_wxid, content, atUserLists):
                if not noAtMsg:
                    return
                self.getAiMsg(noAtMsg, sender, roomId)
            # Ai画图
            elif judgeSplitAllEqualWord(content, self.aiPicKeyWords):
                aiPicPath = self.Ams.getAiPic(content.split(' ')[-1])
                if aiPicPath:
                    self.wcf.send_image(path=aiPicPath, receiver=roomId)
                    return
                self.wcf.send_text(
                    f'@{getIdName(self.wcf, sender, roomId)} Ai画图接口出现错误, 请联系超管查看控制台输出日志',
                    receiver=roomId)
        elif msgType == 49:
            # Ai图文回复
            if judgeAtMe(self.wcf.self_wxid, noAtMsg, atUserLists):
                if 'cdnmidimgurl' in content:
                    srvType, srvId, srvContent = getQuoteImageData(message.content)
                    if srvType == 3:
                        srvImagePath = downloadQuoteImage(self.wcf, srvId, message.extra)
                        if srvImagePath:
                            aiMsg = self.Ams.getAiPicDia(srvContent, srvImagePath, sender)
                            if not aiMsg:
                                self.wcf.send_text(
                                    f'@{getIdName(self.wcf, sender, roomId)} Ai图文对话接口出现错误, 请联系超管查看控制台输出日志',
                                    receiver=roomId)
                                return 
                            if 'FileCache' in aiMsg:
                                self.wcf.send_image(aiMsg, receiver=roomId)
                                return
                            if aiMsg:
                                self.wcf.send_text(f'@{getIdName(self.wcf, sender, roomId)} {aiMsg}', receiver=roomId,
                                                   aters=sender)
                                
                else:
                    srvType, srvContent, srvTitle = getQuoteMsgData(content)
                    if srvType == 1:
                        content = f'用户描述的内容: {srvContent}\n以上是用户描述的内容, 请根据用户描述的内容和用户提问的内容给我回复！\n用户提问的内容: {srvTitle}'
                        self.getAiMsg(noAtMsg=content, sender=sender, roomId=roomId)

    def getAiMsg(self, noAtMsg, sender, roomId):
        """
        群聊Ai回复
        :param noAtMsg:
        :param sender:
        :param roomId:
        :return:
        """
        chatSender = f'room@{sender}'
        aiMsg = self.Ams.getAi(noAtMsg, chatSender)
        if not aiMsg:
            self.wcf.send_text(
                f'@{getIdName(self.wcf, sender, roomId)} Ai对话接口出现错误, 请联系超管查看控制台输出日志',
                receiver=roomId)
            return
        if 'FileCache' in aiMsg:
            self.wcf.send_image(aiMsg, receiver=roomId)
            return
        if aiMsg:
            self.wcf.send_text(f'@{getIdName(self.wcf, sender, roomId)} {aiMsg}',
                               receiver=roomId)
            return

