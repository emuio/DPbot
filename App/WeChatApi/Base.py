from Config.ConfigServer import *
from Config.logger import logger
import httpx
from typing import Optional, Dict, Any


DPBotConfig = returnLoginData().get('DPBotConfig')
DPBotApi = DPBotConfig.get('DPBotApi')
DPBotPort = DPBotConfig.get('DPBotPort')

# 全局client对象
_client: Optional[httpx.AsyncClient] = None

async def get_client() -> httpx.AsyncClient:
    """
    获取或创建全局client对象
    """
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=None,  # 默认不设置超时，由具体请求控制
            http2=False,   # 禁用 HTTP/2，使用 HTTP/1.1
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=30)  # 连接池设置
        )
    return _client

async def close_client() -> None:
    """
    关闭client
    """
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None

async def cleanup() -> None:
    """
    清理资源
    """
    await close_client()

async def sendPostReq(reqPath: str, data: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """
    发送通用POST异步请求
    :param reqPath: API路径
    :param data: 请求数据
    :param timeout: 超时时间（秒）
    :return: JSON响应数据
    :raises: httpx.RequestError: 当HTTP请求失败时
    :raises: ValueError: 当JSON解析失败时
    """
    api = f'http://{DPBotApi.replace("0.0.0.0", "127.0.0.1")}:{DPBotPort}/api/{reqPath}'
    
    logger.debug(f"发送请求: {api}")
    try:
        client = await get_client()
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        response = await client.post(
            api, 
            json=data, 
            headers=headers, 
            timeout=timeout
        )
        response.raise_for_status()  # 确保响应状态码是 2xx
        jsonData = response.json()
        logger.debug(f"请求返回: {jsonData}")
        return jsonData
    except httpx.RequestError as e:
        logger.error(f"HTTP请求失败: {str(e)}, API: {api}")
        raise
    except ValueError as e:
        logger.error(f"JSON解析失败: {str(e)}, API: {api}")
        raise
    except Exception as e:
        logger.error(f"未预期的错误: {str(e)}, API: {api}")
        raise 