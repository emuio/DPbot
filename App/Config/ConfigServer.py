import tomlkit
import os


def returnConfigPath():
    """
    返回配置文件夹路径
    :return:
    """
    current_path = os.path.dirname(__file__)
    if '\\' in current_path:
        current_list_path = current_path.split('\\')[0:-1]
        configPath = '/'.join(current_list_path) + '/Config/'
        return configPath
    else:
        return current_path


def returnConfigData():
    """
    返回配置文件数据（TOML格式）
    :return:
    """
    current_path = returnConfigPath()
    configData = tomlkit.load(open(current_path + 'Config.toml', mode='r', encoding='UTF-8'))
    return configData

def returnLoginData():
    """
    返回登录配置文件数据（TOML格式）
    :return:
    """
    current_path = returnConfigPath()
    configData = tomlkit.load(open(current_path + 'Login.toml', mode='r', encoding='UTF-8'))
    return configData


def returnAdminDbPath():
    """
    返回管理员数据库地址
    :return:
    """
    return returnConfigPath() + 'Admin.db'
