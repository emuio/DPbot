import tomlkit
import os
import httpx
import base64
from typing import Optional, Dict, Union, Any
from Config.logger import logger


class Tool:
    def __init__(self):
        pass

    def returnConfigData(self, pluginPath):
        """
        返回配置文件信息
        :param pluginPath:
        :return:
        """
        with open(os.path.join(pluginPath, 'config.toml'), mode='r', encoding='UTF-8') as f:
            data = tomlkit.load(f)
        return data

    def returnNoAtMsg(self, atWxIdList, content, groupMemberInfos):
        """ 处理@消息 返回没有@的消息 """
        for atWxId in atWxIdList:
            nickName = groupMemberInfos.get(atWxId, {}).get('nickname', '')
            if nickName:
                # 尝试替换多种可能的 @+昵称 组合
                patterns = [
                    f'@{nickName} ',  # 普通空格
                    f'@{nickName}\u3000',  # 全角空格
                    f'@{nickName}',  # 无空格
                ]
                for pattern in patterns:
                    content = content.replace(pattern, '')
            if '@' in content and ' ' in content:
                cList = content.replace('\u2005', ' ').replace('\u3000', '').split(' ')
                cList = [cl for cl in cList if not cl.startswith('@')]
                cList = [cl for cl in cList if cl]
                content = ' '.join(cList)
        return content.strip()

    async def async_get(self, 
                     url: str, 
                     params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None,
                     timeout: int = 10,
                     return_json: bool = True,
                     return_base64: bool = False) -> Optional[Union[Dict, str, bytes]]:
        """
        异步 GET 请求
        Args:
            url: 请求URL
            params: URL参数
            headers: 请求头
            timeout: 超时时间（秒）
            return_json: 是否返回JSON数据
            return_base64: 是否返回base64编码的数据
        Returns:
            Optional[Union[Dict, str, bytes]]: 
            - return_json=True: 返回字典或None
            - return_base64=True: 返回base64字符串或None
            - 其他情况: 返回bytes或None
        """
        try:
            if headers is None:
                headers = self._get_default_headers()
                
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code != 200:
                    logger.warning(f'GET请求失败 {url}, 状态码: {response.status_code}')
                    return None
                    
                if return_json:
                    return response.json()
                
                data = response.read()
                if return_base64:
                    return base64.b64encode(data).decode('utf-8')
                
                return data
                
        except Exception as e:
            logger.error(f'GET请求异常 {url}: {e}')
            return None

    async def async_post(self,
                      url: str,
                      data: Optional[Dict] = None,
                      json_data: Optional[Dict] = None,
                      headers: Optional[Dict] = None,
                      timeout: int = 10,
                      return_json: bool = True) -> Optional[Union[Dict, bytes]]:
        """
        异步 POST 请求
        Args:
            url: 请求URL
            data: 表单数据
            json_data: JSON数据
            headers: 请求头
            timeout: 超时时间（秒）
            return_json: 是否返回JSON数据
        Returns:
            Optional[Union[Dict, bytes]]: 返回字典/bytes或None
        """
        try:
            if headers is None:
                headers = self._get_default_headers()
                
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.post(url, 
                                    data=data,
                                    json=json_data,
                                    headers=headers)
                if response.status_code != 200:
                    logger.warning(f'POST请求失败 {url}, 状态码: {response.status_code}')
                    return None
                    
                if return_json:
                    return response.json()
                return response.read()
                    
        except Exception as e:
            logger.error(f'POST请求异常 {url}: {e}')
            return None

    def _get_default_headers(self) -> Dict[str, str]:
        """
        获取默认请求头
        Returns:
            Dict[str, str]: 默认请求头
        """
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        } 