from Plugins._Tools import Tools
from Config.logger import logger
import Config.ConfigServer as Cs
from Core.PluginBase import PluginBase
from WeChatApi import WeChatApi
import os
import asyncio
import random 
class ShortVideoParsePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.dp = WeChatApi()         
        self.name = "ShortVideoParse"
        self.description = "短视频解析插件"
        self.version = "1.0.0"
        self.author = "大鹏"
        self.tools = Tools()        
              
        self.configData = self.tools.returnConfigData(os.path.dirname(__file__))
        self.dpApi = self.configData.get('dpApi')
        self.dpKey = self.configData.get('dpKey')
        self.dyWord = self.configData.get('dyWord')

    async def handleShortVideo(self, shortVideoUrl: str) -> dict:
        """解析短视频链接
        Args:
            shortVideoUrl: 短视频链接
        Returns:
            dict: 解析结果，失败返回空字典
        """
        try:
            params = {
                'AppSecret': self.dpKey,
                'text': shortVideoUrl
            }
            jsonData = await self.tools.async_get(self.dpApi, params=params, return_json=True)
            if not jsonData:
                logger.warning(f'{self.name} 请求API失败')
                return {}

            # 检查API返回状态
            if jsonData.get('code') != 200:
                logger.warning(f'{self.name} API返回错误: {jsonData.get("msg")}')
                return {}

            parseData = jsonData.get('data')
            # 确保parseData不是None
            if not parseData:
                logger.warning(f'{self.name} API返回数据data字段为空')
                return {}

            parseDicts = {
                'title': parseData.get('title'),
                'author': parseData.get('author', {}).get('name'),  # 安全地获取嵌套字典的值
                'cover_url': parseData.get('cover_url'),
                'video_url': parseData.get('video_url'),
                'images': parseData.get('images', [])
            }
            return parseDicts
        except Exception as e:
            logger.warning(f'{self.name} 解析短视频出现错误: {e}')
            return {}

    async def handle_message(self, msg) -> bool:
        """处理消息"""
        try:
            if msg.type != 1:  # 只处理文本消息
                return False
                
            if not self.tools.judgeInListWord(msg.content, self.dyWord):
                return False
                
            logger.debug(f'{msg.content} 收到短视频视频链接, 开始解析短视频')
            parseDicts = await self.handleShortVideo(msg.content)
            logger.debug(f'短视频解析结果: {parseDicts}')
            
            if not parseDicts:
                await self.dp.sendText(f'{self.name} 解析短视频内容出现错误, 请稍后再试！', 
                                   msg.roomid, 
                                   msg.self_wxid)
                return True
                
            if parseDicts.get('video_url'):
                # 处理视频
                await self.dp.sendText(
                    f'✅ 短视频解析成功 ~ \n'
                    f'视频标题: {parseDicts.get("title")} \n'
                    f'视频链接: {parseDicts.get("video_url")} \n'
                    f'视频封面: {parseDicts.get("cover_url")}',
                    msg.roomid, 
                    msg.self_wxid
                )
                return True
                
            if parseDicts.get('images'):
                # 处理图片集
                images = parseDicts.get('images', [])
                logger.debug(f'图片集: {images}')
                images_count = len(images)
                if images_count == 0:
                    await self.dp.sendText(
                        f'❌ 图集解析失败: 未找到有效图片', 
                        msg.roomid, 
                        msg.self_wxid
                    )
                    return True

                await self.dp.sendText(
                    f'✅ 图集解析成功: {parseDicts.get("title")} (共{images_count}张图片)',
                    msg.roomid, 
                    msg.self_wxid
                )

                # 逐张发送图片
                success_count = 0
                failed_urls = []  # 记录失败的图片URL
                logger.debug(f'开始发送图片集，共{images_count}张')

                for index, image_url in enumerate(images):
                    try:
                        logger.debug(f'开始发送第{index+1}/{images_count}张图片: {image_url}')
                        result = await self.dp.sendImage(image_url, msg.roomid, msg.self_wxid)
                        if result:
                            success_count += 1
                            logger.info(f'第{index+1}/{images_count}张图片发送成功')
                        else:
                            failed_urls.append(image_url)
                            logger.warning(f'第{index+1}/{images_count}张图片发送失败')
                    except Exception as e:
                        failed_urls.append(image_url)
                        logger.error(f'第{index+1}/{images_count}张图片发送异常: {str(e)}')
                    finally:
                        if index < images_count - 1:  # 如果不是最后一张图片
                            await asyncio.sleep(random.uniform(0.5, 1))

                # 发送结果统计
                status = '✅' if success_count == images_count else '⚠️'
                result_msg = f'{status} 图集发送完成: 成功{success_count}张，失败{images_count-success_count}张'
                if failed_urls:  # 如果有失败的图片，添加失败链接列表
                    result_msg += f'\n\n失败图片链接:'
                    for i, url in enumerate(failed_urls, 1):
                        result_msg += f'\n{i}. {url}'

                await self.dp.sendText(result_msg, msg.roomid, msg.self_wxid)
                return True
                    
            return False
            
        except Exception as e:
            logger.error(f"处理短视频消息失败: {e}")
            await self.dp.sendText("处理短视频消息出现错误，请稍后重试", msg.roomid, msg.self_wxid)
            return True