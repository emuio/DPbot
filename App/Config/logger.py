from loguru import logger
import sys
import os
from pathlib import Path
import tomlkit


def get_config():
    """
    读取配置文件
    """
    config_path = Path(__file__).parent / "Config.toml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = tomlkit.load(f)
            return config.get("LogConfig", {})
    except Exception as e:
        print(f"读取日志配置失败: {str(e)}")
        return {}

def setup_logger():
    """
    设置logger配置
    """
    # 获取配置
    config = get_config()
    
    # 清除默认的处理器
    logger.remove()
    
    # 日志文件路径
    log_path = Path("Config/logs")
    log_path.mkdir(exist_ok=True)
    
    # 默认日志格式
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    # 从配置中获取参数
    debug_mode = config.get("debug", False)
    retention_days = str(config.get("retention_days", 10)) + " days"
    max_file_size = str(config.get("max_file_size", 500)) + " MB"
    encoding = config.get("encoding", "utf-8")
    
    # 添加控制台输出
    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG" if debug_mode else "INFO",
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        log_path / "app.log",
        format=log_format,
        level="DEBUG" if debug_mode else "INFO",
        rotation=max_file_size,
        retention=retention_days,
        encoding=encoding
    )
    
    # 添加错误日志文件
    logger.add(
        log_path / "error.log",
        format=log_format,
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        encoding=encoding
    )

def set_debug_mode(enable: bool = True):
    """
    切换调试模式
    :param enable: True开启debug模式，False关闭
    """
    logger.remove()  # 移除所有处理器
    setup_logger()  # 重新设置logger

# 初始化时自动设置logger
setup_logger() 