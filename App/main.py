import asyncio
import signal
import sys
import platform
from Core.MessageHandler import MessageHandler
from WeChatApi import WeChatApi
from WeChatApi.Base import cleanup
from Config.logger import logger
from cprint import cprint
import traceback
from Core.LoginManager import LoginManager

Bot_Logo = """


 _______  .______   .______     ______   .___________.
|       \ |   _  \  |  |_)  | |  |  |  | `---|  |----`
|  .--.  ||  |_)  | |   _  <  |  |  |  |     |  |     
|  |  |  ||   ___/  |  |_)  | |  `--'  |     |  |     
|  '--'  ||  |      |______/   \______/      |__|     
|_______/ | _|      |______/   \______/      |__|     
                                                      
     Version: V1.0.1
     Author: 大鹏                                             

"""

# 全局变量用于存储消息处理器实例和关闭事件
_handler = None
_shutdown_event = None

async def shutdown(signal=None):
    """优雅关闭程序"""
    global _handler, _shutdown_event
    
    if signal:
        logger.info(f"收到信号 {signal}...")
    else:
        logger.info("开始关闭程序...")

    try:
        # 1. 取消所有运行中的任务
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            logger.info(f"正在取消 {len(tasks)} 个运行中的任务...")
            for task in tasks:
                task.cancel()
            # 等待任务取消（设置超时避免卡死）
            await asyncio.wait(tasks, timeout=5)

        # 2. 关闭消息处理器
        if _handler:
            logger.info("正在关闭消息处理器...")
            try:
                await asyncio.wait_for(_handler.close(), timeout=5)
            except asyncio.TimeoutError:
                logger.error("关闭消息处理器超时")

        # 3. 清理全局资源
        logger.info("正在清理全局资源...")
        await cleanup()

        logger.info("程序关闭完成")
        
        # 4. 设置关闭事件
        if _shutdown_event:
            _shutdown_event.set()
            
    except Exception as e:
        logger.error(f"关闭过程中出错: {e}", exc_info=True)
        raise

def setup_signal_handlers():
    """设置信号处理器"""
    try:
        if platform.system() == 'Windows':
            import win32api
            import win32con
            def handler_func(sig):
                if sig == win32con.CTRL_C_EVENT:
                    logger.info("收到 Ctrl+C 信号")
                    loop = asyncio.get_event_loop()
                    loop.create_task(shutdown())
                    return True
                return False
            win32api.SetConsoleCtrlHandler(handler_func, True)
            logger.info("Windows信号处理器已注册")
        else:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: loop.create_task(shutdown(s))
                )
            logger.info("Unix信号处理器已注册")
    except Exception as e:
        logger.warning(f"注册信号处理器失败: {e}", exc_info=True)

async def main():
    """主函数"""
    global _handler, _shutdown_event
    
    cprint.info(Bot_Logo.strip())
    _shutdown_event = asyncio.Event()
    
    try:
        # 初始化登录管理器
        login_manager = LoginManager()
        
        # 执行登录流程
        login_success = await login_manager.login_process()
        if not login_success:
            logger.error("登录失败，程序退出")
            return
            
        logger.success("登录成功，开始初始化消息处理器...")
        
        # 创建消息处理器
        _handler = MessageHandler()
        
        # 注册信号处理器
        setup_signal_handlers()
        
        # 运行消息处理器
        logger.info("正在启动消息处理器...")
        await _handler.run()
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        error_msg = f"运行时错误: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise
    finally:
        if not _shutdown_event or not _shutdown_event.is_set():
            await shutdown()

def run():
    """运行入口"""
    try:
        # Windows系统特殊处理
        if asyncio.get_event_loop_policy().__class__.__name__ == 'WindowsSelectorEventLoopPolicy':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # 运行主函数
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        error_msg = f"启动失败: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise

if __name__ == "__main__":
    run()