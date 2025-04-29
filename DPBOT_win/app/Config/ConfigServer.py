import yaml
import os


def returnConfigPath():
    """
    返回配置文件夹路径
    :return:
    """
    # 获取当前文件的绝对路径
    current_file = os.path.abspath(__file__)
    # 获取当前文件所在目录
    current_dir = os.path.dirname(current_file)
    # 标准化路径，确保路径分隔符正确
    config_dir = os.path.normpath(current_dir)
    # 在日志中输出路径，便于调试
   # print(f"Config目录路径: {config_dir}")
    return config_dir


def returnConfigData():
    """
    返回配置文件数据（YAML格式）
    :return:
    """
    current_path = returnConfigPath()
    config_file = os.path.join(current_path, 'Config.yaml')
    # 检查文件是否存在并可读
    if not os.path.exists(config_file):
        print(f"错误: 配置文件不存在: {config_file}")
        return {}
    try:
        with open(config_file, mode='r', encoding='UTF-8') as f:
            configData = yaml.safe_load(f)
        return configData
    except Exception as e:
        print(f"读取配置文件错误: {e}")
        return {}

def returnRoomMsgDbPath():
    return os.path.join(returnConfigPath(), 'RoomMsg.db')

def returnUserDbPath():
    return os.path.join(returnConfigPath(), 'User.db')


def returnRoomDbPath():
    return os.path.join(returnConfigPath(), 'Room.db')


def returnGhDbPath():
    return os.path.join(returnConfigPath(), 'Gh.db')


def returnPointDbPath():
    return os.path.join(returnConfigPath(), 'Point.db')
