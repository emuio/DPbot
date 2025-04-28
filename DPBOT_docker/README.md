# DPbot
NGCBOT 的ipad协议适配版本

# 需要同城服务器、或者本地nas搭建

# 启动顺序

`cd DPBOT_ipad` 

`docker compose up -d`

# 登录
多数redis和DPBOT-IPAD855启动没问题

## 访问`http://localhost:8057`
调用` /Login/GetQRx` 传参(参数必传，不然凌晨掉线)
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
### 获取登录二维码url和uuid，访问url扫码登录

### uuid传入`/Login/CheckQR`接口中，手机顶部出现ipad登录则成功
没成功再调一次`/Login/CheckQR接口`
### 获取到自己的wxid记录到/app/config.py

## 再次启动DPBOT
应该没啥问题了


# 我是nas部署，感觉很简单


