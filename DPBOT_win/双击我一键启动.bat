@echo off
rem 设置UTF-8编码
chcp 65001 >nul
color 0A

echo 正在启动服务...

echo 1. 启动Redis服务器...
start "" "%~dp0Redis\redis-server.exe" "%~dp0Redis\redis.windows.conf"
echo Redis服务器已启动，等待3秒...
timeout /t 3 /nobreak > nul

echo 2. 启动wxapi服务...
start "" "%~dp0wxapi\wxapi.exe"
echo wxapi服务已启动，等待3秒确保服务完全启动...
timeout /t 3 /nobreak > nul
echo wxapi服务应已完全启动

echo 3. 启动app中的main.py...
cd "%~dp0app"
echo =====================================================
echo "登录说明:"
echo "[1] 首次启动需登录"
echo "[2] 输入y扫码登录"
echo "[3] 输入n跳过登录"
echo =====================================================
echo 是否需要强制登录？(y/n): 
set /p force_login=
if /i "%force_login%"=="y" (
    echo 将使用强制登录模式启动...
    start "" cmd /k "chcp 65001 > nul && python main.py --force"
) else (
    echo 将使用普通模式启动...
    start "" cmd /k "chcp 65001 > nul && python main.py"
)

echo 所有服务已启动完成!
echo 请在控制台窗口中按照提示操作