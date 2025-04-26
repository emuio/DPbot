# DPbot
NGCBOT 的ipad协议适配版本
# 启动顺序

## 一 启动redis
双击/Redis/redis-sever.exe
## 二 启动wxapi
双击 wxapi.exe
## 三 登录机器人
### 访问`http://localhost:8057`
调用` /Login/GetQRx` 传参
```{
  "DeviceID": "123456789",
  "DeviceName": "pingguo",
  "Proxy": {
    "ProxyIp": "string",
    "ProxyPassword": "string",
    "ProxyUser": "string"
  }
}
```
获取登录二维码url和uuid，访问url扫码登录
uuid传入`/Login/CheckQR`接口中，手机顶部出现ipad登录则成功，没成功再调一次`/Login/CheckQR接口`
获取到自己的wxid记录到/app/config.py
## 运行机器人
cd  进入app文件夹，首次运行先`python test.py`,避免初始消息过多，造成其他群爆炸
泄完消息，`python main.py`
# NGCBOT 复活成功
匆忙上线，接口陆续适配，逐渐恢复至NGCBOT原样

