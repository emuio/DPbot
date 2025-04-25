FROM alpine:latest

# 安装基本工具和时区
RUN apk --no-cache add ca-certificates tzdata

# 设置时区为中国时区
ENV TZ=Asia/Shanghai

# 创建应用目录
WORKDIR /app

# 复制二进制文件和配置文件
COPY wxapi /app/
COPY conf/ /app/conf/
COPY swagger/ /app/swagger/

# 创建日志目录
RUN mkdir -p /app/logs

# 添加执行权限
RUN chmod +x /app/wxapi

# 暴露端口
EXPOSE 8057 8899

# 运行应用
CMD ["./wxapi"] 