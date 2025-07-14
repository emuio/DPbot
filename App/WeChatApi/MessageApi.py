import asyncio
from typing import Any, Callable, Tuple, Dict, Optional, Union, List
from asyncio import Future
from WeChatApi.Base import sendPostReq
from Config.logger import logger
import os
import base64
from urllib.parse import urlparse
import aiofiles
from pathlib import Path
import tempfile
import cv2
import numpy as np
import math
from io import BytesIO
#import pysilk
from pydub import AudioSegment
import mimetypes
from PIL import Image
import random  # 添加到文件开头的导入部分
import httpx

class MessageApi:
    def __init__(self):
        # 普通消息队列(文本等)
        self._message_queue: asyncio.Queue = asyncio.Queue()
        # 视频消息专用队列
        self._video_queue: asyncio.Queue = asyncio.Queue()
        # 图片消息专用队列
        self._image_queue: asyncio.Queue = asyncio.Queue()
        
        self._is_processing: bool = False
        self._is_processing_video: bool = False
        self._is_processing_image: bool = False
        self._processing_task: Optional[asyncio.Task] = None
        self._video_processing_task: Optional[asyncio.Task] = None
        self._image_processing_task: Optional[asyncio.Task] = None

    async def _process_message_queue(self) -> None:
        """
        处理普通消息队列的异步方法
        """
        if self._is_processing:
            return

        self._is_processing = True
        try:
            while True:
                if self._message_queue.empty():
                    break

                func, args, kwargs, future = await self._message_queue.get()
                try:
                    result = await func(*args, **kwargs)
                    if not future.done():
                        future.set_result(result)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                finally:
                    self._message_queue.task_done()
                    await asyncio.sleep(1)  # 消息发送间隔1秒
        finally:
            self._is_processing = False
            self._processing_task = None

    async def _process_video_queue(self) -> None:
        """
        处理视频消息队列的异步方法
        """
        if self._is_processing_video:
            return

        self._is_processing_video = True
        try:
            while True:
                if self._video_queue.empty():
                    break

                func, args, kwargs, future = await self._video_queue.get()
                try:
                    result = await func(*args, **kwargs)
                    if not future.done():
                        future.set_result(result)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                finally:
                    self._video_queue.task_done()
                    await asyncio.sleep(2)  # 视频发送间隔2秒
        finally:
            self._is_processing_video = False
            self._video_processing_task = None

    async def _process_image_queue(self) -> None:
        """
        处理图片消息队列的异步方法
        """
        if self._is_processing_image:
            return

        self._is_processing_image = True
        try:
            while True:
                if self._image_queue.empty():
                    break

                func, args, kwargs, future = await self._image_queue.get()
                try:
                    result = await func(*args, **kwargs)
                    if not future.done():
                        future.set_result(result)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                finally:
                    self._image_queue.task_done()
                    await asyncio.sleep(random.uniform(0.5, 1))  # 随机延时2-4秒
        finally:
            self._is_processing_image = False
            self._image_processing_task = None

    async def _queue_message(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        将普通消息添加到队列
        """
        future = asyncio.Future()
        await self._message_queue.put((func, args, kwargs, future))

        if not self._is_processing:
            self._processing_task = asyncio.create_task(self._process_message_queue())

        return await future

    async def _queue_video(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        将视频消息添加到专用队列
        """
        future = asyncio.Future()
        await self._video_queue.put((func, args, kwargs, future))

        if not self._is_processing_video:
            self._video_processing_task = asyncio.create_task(self._process_video_queue())

        return await future

    async def _queue_image(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        将图片消息添加到专用队列
        """
        future = asyncio.Future()
        await self._image_queue.put((func, args, kwargs, future))

        if not self._is_processing_image:
            self._image_processing_task = asyncio.create_task(self._process_image_queue())

        return await future

    async def close(self) -> None:
        """
        优雅关闭，等待所有消息处理完成
        """
        # 等待普通消息队列完成
        if self._processing_task:
            await self._message_queue.join()
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        # 等待视频消息队列完成
        if self._video_processing_task:
            await self._video_queue.join()
            self._video_processing_task.cancel()
            try:
                await self._video_processing_task
            except asyncio.CancelledError:
                pass

        # 等待图片消息队列完成
        if self._image_processing_task:
            await self._image_queue.join()
            self._image_processing_task.cancel()
            try:
                await self._image_processing_task
            except asyncio.CancelledError:
                pass

    async def sendText(self, msg: str, toWxid: str, selfWxid: str, type: int = 0) -> Dict[str, Any]:
        """
        发送文本消息
        :param msg: 消息内容
        :param toWxid: 接收者wxid
        :param selfWxid: 发送者wxid
        :param type: 消息类型，默认为0
        :return: API响应结果
        """
        async def _do_send() -> Dict[str, Any]:
            data = {
                "At": "",
                "Content": msg,
                "ToWxid": toWxid,
                "Type": type,
                "Wxid": selfWxid
            }
            return await sendPostReq("Msg/SendTxt", data)

        return await self._queue_message(_do_send)

    async def sendImage(self, imagePath: str, toWxid: str, selfWxid: str):
        """
        发送图片消息
        :param imagePath: 图片路径（支持本地路径、URL、base64字符串或data URI格式的base64）
        :param toWxid: 接收者wxid
        :param selfWxid: 发送者wxid
        :return: 发送结果
        """
        async def _do_send():
            try:
                base64_image = None
                # 判断是否为base64数据
                if isinstance(imagePath, str):
                    # 检查是否为data URI格式的base64
                    if imagePath.startswith('data:image') and ';base64,' in imagePath:
                        base64_image = imagePath.split(';base64,')[-1]
                    # 检查是否为纯base64字符串（通过特征检测）
                    elif len(imagePath) > 100 and '/' in imagePath and '+' in imagePath:
                        base64_image = imagePath
                    else:
                        # 判断是否为URL
                        try:
                            result = urlparse(imagePath)
                            is_url = all([result.scheme, result.netloc])
                        except:
                            is_url = False

                        # 读取图片数据
                        if is_url:
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                                'Accept-Encoding': 'gzip, deflate',
                                'Cache-Control': 'no-cache',
                                'Pragma': 'no-cache'
                            }
                            async with httpx.AsyncClient(headers=headers, timeout=20) as client:
                                response = await client.get(imagePath)
                                if response.status_code != 200:
                                    raise Exception(f"下载图片失败，状态码: {response.status_code}")
                                
                                # 获取Content-Type
                                content_type = response.headers.get('Content-Type', '')
                                image_data = response.content
                                
                                # 检查是否为支持的图片格式
                                if not any(fmt in content_type.lower() for fmt in ['jpeg', 'jpg', 'png']):
                                    # 尝试转换图片格式
                                    try:
                                        img = Image.open(BytesIO(image_data))
                                        # 转换为RGB模式（处理RGBA等其他模式）
                                        if img.mode != 'RGB':
                                            img = img.convert('RGB')
                                        # 将图片保存为JPEG格式到BytesIO
                                        output = BytesIO()
                                        img.save(output, format='JPEG', quality=95)
                                        image_data = output.getvalue()
                                        logger.info(f"图片已转换为JPEG格式")
                                    except Exception as e:
                                        logger.error(f"图片格式转换失败: {e}")
                                        raise
                        else:
                            if not os.path.exists(imagePath):
                                raise FileNotFoundError(f'文件不存在: {imagePath}')
                                
                            # 检查本地文件格式
                            file_type = mimetypes.guess_type(imagePath)[0]
                            if not file_type or not any(fmt in file_type.lower() for fmt in ['jpeg', 'jpg', 'png']):
                                try:
                                    img = Image.open(imagePath)
                                    if img.mode != 'RGB':
                                        img = img.convert('RGB')
                                    output = BytesIO()
                                    img.save(output, format='JPEG', quality=95)
                                    image_data = output.getvalue()
                                    logger.info(f"本地图片已转换为JPEG格式")
                                except Exception as e:
                                    logger.error(f"本地图片格式转换失败: {e}")
                                    raise
                            else:
                                async with aiofiles.open(imagePath, "rb") as image_file:
                                    image_data = await image_file.read()

                        # 转换为base64
                        base64_image = base64.b64encode(image_data).decode('utf-8').replace('\n', '')

                if not base64_image:
                    raise Exception("获取图片base64编码失败")
        
                data = {
                    'Wxid': selfWxid,
                    'ToWxid': toWxid,
                    'base64': base64_image,
                }
                return await sendPostReq("Msg/UploadImg", data=data)
                
            except Exception as e:
                logger.error(f"发送图片失败: {e}")
                raise

        return await self._queue_image(_do_send)

    async def sendVideo(self, videoPath: str, toWxid: str, selfWxid: str):
        """
        发送视频消息(使用专用队列)
        :param videoPath: 视频文件路径（支持本地路径或URL）
        :param toWxid: 接收者wxid
        :param selfWxid: 发送者wxid
        :return: 发送结果
        """
        async def _do_send():
            try:
                first_frame_base64, video_data, duration = await self.get_video_info(videoPath)
                if not video_data:
                    raise ValueError("无法读取视频文件")

                video_size = len(video_data)
                size_mb = video_size / (1024 * 1024)
                logger.info(f"开始发送视频，大小: {size_mb:.2f}MB")

                # 计算预期上传时间（基于300KB/s的速度）
                upload_time = math.ceil(video_size / (300 * 1024))  # 秒
                # 额外添加60秒基础超时和30秒缓冲时间
                timeout = upload_time + 90
                
                logger.info(f"预计上传时间: {upload_time}秒，设置超时时间: {timeout}秒")

                data = {
                    'Wxid': selfWxid,
                    'ToWxid': toWxid,
                    'base64': base64.b64encode(video_data).decode('utf-8'),
                    'ImageBase64': first_frame_base64 or "",
                    'PlayLength': duration or 0
                }

                try:
                    return await sendPostReq("Msg/SendVideo", data=data, timeout=timeout)
                except Exception as e:
                    error_msg = (
                        f"发送视频失败: {str(e)}\n"
                        f"文件大小: {size_mb:.2f}MB\n"
                        f"预计上传时间: {upload_time}秒\n"
                        "建议：\n"
                        "1. 检查网络连接是否稳定\n"
                        "2. 尝试压缩视频文件\n"
                        "3. 如果视频较大，可能需要分段发送"
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            except Exception as e:
                logger.error(f"处理视频失败: {e}")
                raise

        # 使用视频专用队列
        return await self._queue_video(_do_send)

    async def get_video_info(self, video_source: str) -> Tuple[Optional[str], Optional[bytes], Optional[int]]:
        """
        获取视频信息，包括第一帧图片、视频数据和时长
        :param video_source: 视频源（本地文件路径或URL）
        :return: (第一帧base64, 视频数据, 时长(秒))
        """
        first_frame_base64: Optional[str] = None
        video_data: Optional[bytes] = None
        duration_seconds: Optional[int] = None
        temp_file_path: Optional[str] = None

        try:
            # 1. 验证和读取视频文件
            if video_source.startswith(('http://', 'https://')):
                # 清理URL，移除换行符和空白字符
                video_source = video_source.strip()
                
                # 使用异步下载
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                }
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    response = await client.get(video_source, headers=headers)
                    if response.status_code != 200:
                        raise Exception(f"下载视频失败，状态码: {response.status_code}")
                    video_data = response.content
                    
                    # 创建临时文件用于OpenCV处理
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    temp_file_path = temp_file.name
                    temp_file.close()
                    
                    # 写入临时文件
                    async with aiofiles.open(temp_file_path, 'wb') as f:
                        await f.write(video_data)
            else:
                if not os.path.exists(video_source):
                    raise FileNotFoundError(f"视频文件未找到: {video_source}")
                # 读取本地文件
                async with aiofiles.open(video_source, 'rb') as f:
                    video_data = await f.read()
                temp_file_path = video_source

            # 2. 使用OpenCV处理视频
            cap = cv2.VideoCapture(temp_file_path)
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")

            try:
                # 获取视频信息
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if fps > 0 and frame_count > 0:
                    duration_seconds = int(round(frame_count / fps))
                else:
                    cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
                    duration_seconds = int(round(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0))
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                # 提取第一帧
                ret, frame = cap.read()
                if ret:
                    # JPEG编码参数
                    encode_params = [
                        cv2.IMWRITE_JPEG_QUALITY, 100,
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1
                    ]
                    success, buffer = cv2.imencode('.jpg', frame, encode_params)
                    if success:
                        first_frame_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
            finally:
                cap.release()

        except Exception as e:
            logger.error(f"处理视频时发生错误: {str(e)}")
            return None, None, None
        finally:
            # 清理临时文件
            if temp_file_path and temp_file_path != video_source and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass

        return first_frame_base64, video_data, duration_seconds    

    async def uploadFile(self, filePath: str = "", selfWxid: str = ""):
        """
        上传文件
        :param filePath:
        :param selfWxid:
        :return:
        """
        try:
            if not os.path.exists(filePath):
                raise FileNotFoundError(f'文件不存在: {filePath}')
            
            logger.debug(f"开始上传文件: {filePath}")
            async with aiofiles.open(filePath, "rb") as file_file:
                file_data = await file_file.read()
            file_size = len(file_data)
            logger.debug(f"文件大小: {file_size} 字节")
            
            base64_file = base64.b64encode(file_data).decode('utf-8')
            base64_file = base64_file.replace('\n', '')
            
            data = {
                'Base64': base64_file,
                'Wxid': selfWxid,
            }
            logger.debug(f"发送上传请求到: Tools/UploadFile")
            jsonData = await sendPostReq('Tools/UploadFile', data=data)
            logger.debug(f"上传文件响应: {jsonData}")
            return jsonData
        except Exception as e:
            logger.error(f'上传文件出现错误, 错误信息: {str(e)}')
            return {}

    async def sendFile(self, filePath: str, toWxid: str, selfWxid: str) -> dict:
        """
        发送文件
        :param filePath: 文件路径
        :param toWxid: 接收者ID
        :param selfWxid: 机器人ID
        :return: dict
        """
        async def _do_send():
            logger.debug(f"开始处理文件发送: {filePath}")
            file_name = os.path.basename(filePath)
            file_extension = os.path.splitext(file_name)[1].replace('.', '')
            logger.debug(f"文件名: {file_name}, 扩展名: {file_extension}")
            
            # 上传文件
            logger.debug(f"开始上传文件...")
            upload_result = await self.uploadFile(filePath, selfWxid)
            logger.debug(f"上传结果: {upload_result}")
            
            if not upload_result or not upload_result.get('Success'):
                logger.error(f"文件上传失败: {upload_result}")
                raise ValueError('上传文件失败')
            
            # 获取上传结果中的信息
            file_info = upload_result.get('Data', {})
            media_id = file_info.get('mediaId')
            total_len = file_info.get('totalLen', 0)
            
            logger.debug(f"获取到的mediaId: {media_id}")
            logger.debug(f"文件大小: {total_len}")
            
            if not media_id:
                logger.error("mediaId为空")
                raise ValueError('获取mediaId失败')

            xml = f"""<appmsg appid="" sdkver="0">
    <title>{file_name}</title>
    <des></des>
    <action></action>
    <type>6</type>
    <showtype>0</showtype>
    <content></content>
    <url></url>
    <appattach>
        <totallen>{total_len}</totallen>
        <attachid>{media_id}</attachid>
        <fileext>{file_extension}</fileext>
    </appattach>
    <md5></md5>
</appmsg>"""
            logger.debug(f"构建的XML: {xml}")

            data = {
                'Wxid': selfWxid,
                'ToWxid': toWxid,
                'Content': xml
            }
            logger.debug(f"发送CDN文件请求: {data}")
            return await sendPostReq('Msg/SendCDNFile', data=data)

        return await self._queue_message(_do_send)

    async def sendMusic(self, title: str = "", singer: str = "", url: str = "", 
                     music_url: str = "", cover_url: str = "", lyric: str = "", 
                     toWxid: str = "", selfWxid: str = ""):
        """发送音乐消息"""
        async def _do_send():
            xml = f"""<appmsg appid="wx79f2c4418704b4f8" sdkver="0"><title>{title}</title><des>{singer}</des><action>view</action><type>3</type><showtype>0</showtype><content/><url>{url}</url><dataurl>{music_url}</dataurl><lowurl>{url}</lowurl><lowdataurl>{music_url}</lowdataurl><recorditem/><thumburl>{cover_url}</thumburl><messageaction/><laninfo/><extinfo/><sourceusername/><sourcedisplayname/><songlyric>{lyric}</songlyric><commenturl/><appattach><totallen>0</totallen><attachid/><emoticonmd5/><fileext/><aeskey/></appattach><webviewshared><publisherId/><publisherReqId>0</publisherReqId></webviewshared><weappinfo><pagepath/><username/><appid/><appservicetype>0</appservicetype></weappinfo><websearch/><songalbumurl>{cover_url}</songalbumurl></appmsg><fromusername>{selfWxid}</fromusername><scene>0</scene><appinfo><version>1</version><appname/></appinfo><commenturl/>"""
            data = {
                'Wxid': selfWxid,
                'ToWxid': toWxid,
                'Xml': xml,
                'Type': 5
            }
            return await sendPostReq('Msg/SendApp', data=data)

        return await self._queue_message(_do_send)

    async def sendRich(self, title: str = "", 
                    description: str = "", url: str = "", thumb_url: str = "", toWxid: str = "", selfWxid: str = ""):
        """发送卡片消息"""
        async def _do_send():
            simple_xml = f"""<appmsg><title>{title}</title><des>{description}</des><type>5</type><url>{url}</url><thumburl>{thumb_url}</thumburl></appmsg>"""
            data = {
                'Wxid': selfWxid,
                'ToWxid': toWxid,
                'Xml': simple_xml,
                'Type': 5,
            }
            return await sendPostReq('Msg/SendApp', data=data)

        return await self._queue_message(_do_send)

    async def sendXml(self, selfWxid: str = "", toWxid: str = "", xml: str = "", Type: int = 5):
        """发送XML消息"""
        async def _do_send():
            data = {
                'Wxid': selfWxid,
                'ToWxid': toWxid,
                'Xml': xml,
                'Type': Type,
            }
            return await sendPostReq('Msg/SendApp', data=data)

        return await self._queue_message(_do_send)

    async def sendCard(self, selfWxid: str = "", toWxid: str = "", friendWxId: str = "",
                    CardNickName: str = ""):
        """发送好友名片"""
        async def _do_send():
            data = {
                'Wxid': selfWxid,
                'ToWxid': toWxid,
                'CardWxId': friendWxId,
                'CardNickName': CardNickName,
                'CardAlias': "",
            }
            return await sendPostReq('Msg/ShareCard', data=data)

        return await self._queue_message(_do_send)



