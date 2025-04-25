import FileCache.FileCacheServer as Fcs
import xml.etree.ElementTree as ET
from OutPut.outPut import op
import requests
import time
import os
import re

def getUserLabel(wcf, sender):
    """
    获取用户所属的标签列表
    :param sender:
    :return:
    """
    try:
        userInfos = wcf.query_sql("MicroMsg.db", f'SELECT * FROM Contact WHERE UserName ="{sender}"')
        if not userInfos:
            return []
        userInfo = userInfos[0]
        labelLists = wcf.query_sql("MicroMsg.db", f"SELECT * FROM ContactLabel")
        userLabelIds = userInfo.get('LabelIDList').split(',')
        userLabels = []
        for labelDict in labelLists:
            labelId = labelDict.get('LabelId')
            labelName = labelDict.get('LabelName')
            for userLabelId in userLabelIds:
                if not userLabelId:
                    continue
                if int(userLabelId) == int(labelId):
                    userLabels.append(labelName)
        return userLabelIds
    except Exception as e:
        op(f'[-]: 获取用户所属的标签列表出现错误, 错误信息: {e}')

def getQuoteImageData(content):
    """
    提取引用图片消息的ID和 Type 以及 用户发送的内容
    :return:
    """
    try:
        root = ET.fromstring(content)
        refermsg = root.find('.//refermsg')
        title = root.find('.//title')
        if refermsg is not None:
            # 提取type和svrid
            typeValue = refermsg.find('type').text
            srvId = refermsg.find('svrid').text
            titleValue = title.text
            if typeValue and srvId:
                return int(typeValue), int(srvId), titleValue
            return None, None, None
    except Exception:
        return 0, None, None

def getQuoteMsgData(content):
    """
    提取引用消息 内容 引用内容 Type
    :param content:
    :return:
    """
    try:
        root = ET.fromstring(content)
        refermsg = root.find('.//refermsg')
        title = root.find('.//title')
        if refermsg is not None:
            # 提取type和引用Content
            typeValue = refermsg.find('type').text
            srvContent = refermsg.find('content').text
            titleValue = title.text
            if typeValue and srvContent:
                return int(typeValue), srvContent, titleValue
            return 0, None, None
    except Exception:
        return 0, None, None

def downloadQuoteImage(wcf, imageMsgId, extra):
    """
    下载引用消息的图片
    :param wcf:
    :param imageMsgId:
    :param extra:
    :return:
    """
    try:
        for i in range(0, 4):
            dbName = f'MSG{i}.db'
            data = wcf.query_sql(dbName, f'SELECT * FROM MSG WHERE MsgSvrID= {imageMsgId}')
            if not data:
                continue
            bytesExtra = data[0]['BytesExtra']
            bytesExtraStr = bytesExtra.decode('utf-8', errors='ignore')
            userHome = re.search(r'(?P<userHome>.*?/)wxid_', extra).group('userHome')
            datPath = re.search(r'}(?P<datPath>.*?.dat)', bytesExtraStr).group('datPath').replace('\\', '/')
            imgDatPath = userHome + datPath
            imgSavePath = wcf.download_image(imageMsgId, imgDatPath, Fcs.returnPicCacheFolder())
            return imgSavePath
    except Exception:
        return None


def getWithdrawMsgData(content):
    """
    提取撤回消息的 ID
    :param content:
    :return:
    """
    root = ET.fromstring(content)
    try:
        newMsgId = root.find(".//newmsgid").text
        replaceMsg = root.find(".//replacemsg").text
        if newMsgId and replaceMsg:
            if '撤回了一条消息' in replaceMsg:
                return newMsgId
    except Exception:
        return None

def getWechatVideoData(content):
    """
    处理微信视频号 提取objectId objectNonceId
    :param content:
    :return: objectId objectNonceId
    """
    try:
        root = ET.fromstring(content)
        finderFeed = root.find('.//finderFeed')
        objectId = finderFeed.find('./objectId').text
        objectNonceId = finderFeed.find('./objectNonceId').text
        return objectId, objectNonceId
    except Exception as e:
        op(f'[~]: 提取微信视频号ID出现错误, 错误信息: {e}, 不用管此报错 ~~~')
        return '', ''


def getAtData(msg):
    """
    处理@信息
    :param msg:
    :param wcf:
    :return:
    """
    noAtMsg = msg.noAtMsg
    atUserLists = msg.atusers
    return atUserLists, noAtMsg.strip()


def getIdName(wcf, wxid=None, roomid=None):
    """
    获取好友或者群聊昵称
    :param wcf: 微信框架对象
    :param wxid: 用户ID
    :param roomid: 群聊ID
    :return:
    """
    if not wxid and not roomid:
        return {"error": "参数错误", "message": "wxid 和 roomid 不能同时为空"}
    try:
        if wxid and roomid:
            name_list = wcf.get_alias_in_chatroom(wxid, roomid)
            if name_list:
                return name_list['nickname']
        elif wxid and not roomid:
            info = wcf.get_info_by_wxid(wxid)
            if "nickname" in info and info["nickname"]:
                return info["nickname"] 
        elif roomid and not wxid:
            group_info = wcf.get_info_by_roomid(roomid)
            if "group_name" in group_info and group_info["group_name"]:
                return group_info["group_name"]
        return wxid
    except Exception as e:
        op(f'[~]: 获取好友或者群聊昵称出现错误, 错误信息: {e}')
        return wxid


def getUserPicUrl(wcf, sender):
    """
    获取好友头像下载地址
    :param sender:
    :param wcf:
    :return:
    """
    imgName = str(sender) + '.jpg'
    save_path = Fcs.returnAvatarFolder() + '/' + imgName

    if imgName in os.listdir(Fcs.returnAvatarFolder()):
        return save_path

    headImgData = wcf.query_sql("MicroMsg.db", f"SELECT * FROM ContactHeadImgUrl WHERE usrName = '{sender}';")
    try:
        if headImgData:
            if headImgData[0]:
                bigHeadImgUrl = headImgData[0]['bigHeadImgUrl']
                content = requests.get(url=bigHeadImgUrl, timeout=30).content
                with open(save_path, mode='wb') as f:
                    f.write(content)
                return save_path
    except Exception as e:
        op(f'[-]: 获取好友头像下载地址出现错误, 错误信息: {e}')
        return None


if __name__ == '__main__':
    getWithdrawMsgData('<sysmsg type="revokemsg"><revokemsg><session>47555703573@chatroom</session><msgid>1387587956</msgid><newmsgid>6452489353190914412</newmsgid><replacemsg><![CDATA["Vcnnn8h" 撤回了一条消息]]></replacemsg><announcement_id><![CDATA[]]></announcement_id></revokemsg></sysmsg>')
