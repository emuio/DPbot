#from cprint import cprint
import time
from loguru import logger

def op(msg: str):
    """
    消息输出函数
    :param msg:
    :return:
    """
    now_time = time.strftime("%Y-%m-%d %X")
    if '[*]' in msg:
        logger.info(f'[{now_time}]: {msg}')
    elif '[+]' in msg:
        logger.success(f'[{now_time}]: {msg}')
    elif '[-]' in msg:
        logger.error(f'[{now_time}]: {msg}')
    elif '[~]' in msg:
        logger.warning(f'[{now_time}]: {msg}')
    else:
        logger.info(f'[{now_time}]: {msg}')
