from .JudgeTools import JudgeTools
from DbServer import DbServer
from .Tool import Tool
from Config.logger import logger


class Tools(Tool, DbServer, JudgeTools):
    def __init__(self):
        Tool.__init__(self)
        DbServer.__init__(self)
        JudgeTools.__init__(self)


    async def close(self):
        """关闭所有资源"""
        try:
            from DbServer.DbDomServer import db_manager
            await db_manager.close_all()  # 关闭所有数据库连接
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}", exc_info=True)

 