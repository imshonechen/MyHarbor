# MyHarbor 生产环境部署指南

## 📋 部署前准备

### 1. 服务器要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+ / CentOS 8+)
- **内存**: 最低 1GB，推荐 2GB+
- **磁盘**: 最低 10GB 可用空间
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### 2. 安装 Docker 和 Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 3. 开放防火墙端口

```bash
# Ubuntu (ufw)
sudo ufw allow 24041/tcp
sudo ufw reload

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=24041/tcp
sudo firewall-cmd --reload
```

### 4. 云服务器安全组配置

如果使用云服务器（阿里云、腾讯云、AWS 等），需要在控制台添加安全组规则：
- 协议：TCP
- 端口：24041
- 来源：0.0.0.0/0（或指定 IP）

---

## 🚀 快速部署

### 方式一：FTP 上传部署（推荐）

#### 步骤 1: 本地准备文件

在本地项目目录下,确保以下文件和目录存在:

```
MyHarbor/
├── backend/           # 后端代码
├── frontend/          # 前端代码
├── docker-compose.yml # Docker 编排文件
├── Dockerfile         # Docker 镜像构建文件
└── .dockerignore      # Docker 忽略文件
```

**注意**: 不需要上传以下内容:
- `node_modules/` (会在 Docker 构建时安装)
- `frontend/dist/` (会在 Docker 构建时生成)
- `backend/__pycache__/` (Python 缓存)
- `.git/` (Git 仓库)
- `data/` (服务器上创建)

#### 步骤 2: 上传到服务器

使用 FTP 客户端(如 FileZilla、WinSCP)将项目文件上传到服务器:

```bash
# 服务器目标路径示例
/opt/MyHarbor/
```

或使用命令行 SCP:

```bash
# 从本地上传到服务器
scp -r MyHarbor/ user@your-server-ip:/opt/MyHarbor/
```

#### 步骤 3: 登录服务器

```bash
ssh user@your-server-ip
cd /opt/MyHarbor
```

#### 步骤 4: 配置环境变量

**重要：必须修改 JWT_SECRET！**

编辑 `docker-compose.yml` 文件:

```bash
nano docker-compose.yml
```

修改以下配置:

```yaml
environment:
  # 修改 JWT 密钥（必须！至少 32 位）
  - JWT_SECRET=your-super-secret-key-min-32-characters-long-change-this

  # 可选：修改其他配置
  - JWT_EXPIRE_HOURS=24
  - CHECK_TIMEOUT_SECONDS=5
```

**生成强密钥的方法：**

```bash
# 方法 1: 使用 openssl
openssl rand -base64 32

# 方法 2: 使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法 3: 使用 /dev/urandom
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
```

#### 步骤 5: 创建数据目录

```bash
# 创建持久化数据目录
mkdir -p data
chmod 755 data
```

#### 步骤 6: 启动服务

```bash
# 构建并启动容器（首次部署）
docker-compose up -d --build

# 查看启动日志
docker-compose logs -f
```

#### 步骤 7: 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查健康状态
curl http://localhost:24041/api/health

# 查看启动日志（获取后台入口/路由码）
docker-compose logs myharbor | grep -E "Default admin config initialized|Backend URL"

# 或进入容器直接查询（推荐）
docker-compose exec myharbor python manage.py show-route
```

#### 步骤 8: 首次登录

1. 访问 `http://your-server-ip:24041`
2. 查看日志获取后台路由码（或进入容器查询）:
   ```bash
   docker-compose logs myharbor | grep -E "Default admin config initialized|Backend URL"
   docker-compose exec myharbor python manage.py show-route
   ```
3. 访问后台: `http://your-server-ip:24041/{路由码}`
4. 默认账号: `admin` / `admin123`
5. **立即修改默认密码！**

---

### 方式二：Git 克隆部署

#### 步骤 1: 克隆项目

```bash
# 克隆代码到服务器
git clone https://github.com/yourusername/MyHarbor.git
cd MyHarbor
```

#### 步骤 2: 配置环境变量

**重要：必须修改 JWT_SECRET！**

编辑 `docker-compose.yml` 文件:

```bash
nano docker-compose.yml
```

修改以下配置:

```yaml
environment:
  # 修改 JWT 密钥（必须！至少 32 位）
  - JWT_SECRET=your-super-secret-key-min-32-characters-long-change-this

  # 可选：修改其他配置
  - JWT_EXPIRE_HOURS=24
  - CHECK_TIMEOUT_SECONDS=5
```

**生成强密钥的方法：**

```bash
# 方法 1: 使用 openssl
openssl rand -base64 32

# 方法 2: 使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法 3: 使用 /dev/urandom
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
```

#### 步骤 3: 创建数据目录

```bash
# 创建持久化数据目录
mkdir -p data
chmod 755 data
```

#### 步骤 4: 启动服务

```bash
# 构建并启动容器（首次部署）
docker-compose up -d --build

# 查看启动日志
docker-compose logs -f
```

#### 步骤 5: 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查健康状态
curl http://localhost:24041/api/health

# 查看启动日志（获取后台入口/路由码）
docker-compose logs myharbor | grep -E "Default admin config initialized|Backend URL"

# 或进入容器直接查询（推荐）
docker-compose exec myharbor python manage.py show-route
```

#### 步骤 6: 首次登录

1. 访问 `http://your-server-ip:24041`
2. 查看日志获取后台路由码（或进入容器查询）:
   ```bash
   docker-compose logs myharbor | grep -E "Default admin config initialized|Backend URL"
   docker-compose exec myharbor python manage.py show-route
   ```
3. 访问后台: `http://your-server-ip:24041/{路由码}`
4. 默认账号: `admin` / `admin123`
5. **立即修改默认密码！**

---

## 🔧 生产环境优化配置

### 1. 使用 Nginx 反向代理（推荐）

创建 Nginx 配置文件 `/etc/nginx/sites-available/myharbor`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 如果使用 HTTPS，添加 SSL 配置
    # listen 443 ssl http2;
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:24041;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/myharbor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. 配置 HTTPS（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 修改 docker-compose.yml 端口映射

如果使用 Nginx，可以只监听本地：

```yaml
ports:
  - "127.0.0.1:24041:24041"  # 只允许本地访问
```

### 4. 配置日志轮转

创建 `/etc/logrotate.d/myharbor`:

```
/path/to/MyHarbor/data/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## 📊 监控和维护

### 查看日志

```bash
# 实时查看日志
docker-compose logs -f

# 查看最近 100 行
docker-compose logs --tail=100

# 查看特定服务日志
docker-compose logs myharbor
```

### 查看资源使用

```bash
# 查看容器资源使用
docker stats myharbor

# 查看磁盘使用
du -sh data/
```

### 备份数据

```bash
# 方法 1: 备份整个 data 目录
tar -czf myharbor-backup-$(date +%Y%m%d).tar.gz data/

# 方法 2: 只备份数据库
cp data/myharbor.db data/myharbor.db.backup-$(date +%Y%m%d)

# 方法 3: 通过 API 导出（推荐）
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:24041/api/backup/export \
  -o myharbor-backup-$(date +%Y%m%d).json
```

### 定期备份脚本

创建 `/root/backup-myharbor.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/myharbor"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

# 备份数据目录
cd /path/to/MyHarbor
tar -czf $BACKUP_DIR/myharbor-$DATE.tar.gz data/

# 保留最近 7 天的备份
find $BACKUP_DIR -name "myharbor-*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/myharbor-$DATE.tar.gz"
```

添加到 crontab：

```bash
chmod +x /root/backup-myharbor.sh
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /root/backup-myharbor.sh >> /var/log/myharbor-backup.log 2>&1
```

---

## 🔄 更新升级

### 方式一：FTP 上传更新

```bash
# 1. 备份数据
tar -czf backup-before-upgrade-$(date +%Y%m%d).tar.gz data/

# 2. 停止服务
docker-compose down

# 3. 使用 FTP 上传新版本文件到服务器（覆盖旧文件）
#    注意：不要覆盖 data/ 目录和 docker-compose.yml（如果有自定义配置）

# 4. 重新构建并启动
docker-compose up -d --build

# 5. 查看日志确认启动成功
docker-compose logs -f

# 6. 验证功能
curl http://localhost:24041/api/health
```

### 方式二：Git 拉取更新

```bash
# 1. 备份数据
tar -czf backup-before-upgrade-$(date +%Y%m%d).tar.gz data/

# 2. 拉取最新代码
git pull origin main

# 3. 停止服务
docker-compose down

# 4. 重新构建并启动
docker-compose up -d --build

# 5. 查看日志确认启动成功
docker-compose logs -f

# 6. 验证功能
curl http://localhost:24041/api/health
```

### 回滚操作

#### FTP 部署回滚

```bash
# 1. 停止当前版本
docker-compose down

# 2. 使用 FTP 上传旧版本文件到服务器

# 3. 恢复数据（如果需要）
rm -rf data/
tar -xzf backup-before-upgrade-YYYYMMDD.tar.gz

# 4. 重新启动
docker-compose up -d --build
```

#### Git 部署回滚

```bash
# 1. 停止当前版本
docker-compose down

# 2. 切换到上一个版本
git checkout <previous-commit-hash>

# 3. 恢复数据（如果需要）
rm -rf data/
tar -xzf backup-before-upgrade-YYYYMMDD.tar.gz

# 4. 重新启动
docker-compose up -d --build
```

---

## 🔐 安全加固

### 1. 修改默认密码

```bash
# 进入容器
docker-compose exec myharbor bash

# 修改管理员密码
python manage.py set-admin --username admin --password NewStrongPassword123!
```

### 2. 定期更新系统

```bash
# Ubuntu
sudo apt update && sudo apt upgrade -y

# CentOS
sudo yum update -y
```

### 3. 配置防火墙规则

```bash
# 只允许特定 IP 访问
sudo ufw allow from YOUR_IP to any port 24041

# 或使用 Nginx + 基本认证
htpasswd -c /etc/nginx/.htpasswd admin
```

### 4. 启用 Docker 日志限制

编辑 `docker-compose.yml`:

```yaml
services:
  myharbor:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 🆘 故障排查

### 容器无法启动

```bash
# 查看详细错误
docker-compose logs myharbor

# 检查端口占用
sudo netstat -tulpn | grep 24041

# 检查磁盘空间
df -h
```

### 数据库锁定

```bash
# 进入容器
docker-compose exec myharbor bash

# 检查 WAL 模式
sqlite3 data/myharbor.db "PRAGMA journal_mode;"

# 如果不是 WAL，设置为 WAL
sqlite3 data/myharbor.db "PRAGMA journal_mode=WAL;"
```

### 忘记管理员密码

```bash
# 重置为默认密码
docker-compose exec myharbor python manage.py reset-admin

# 查看当前管理员用户名
docker-compose exec myharbor python manage.py show-admin
```

### 忘记后台路由码

```bash
# 查看路由码
docker-compose exec myharbor python manage.py show-route
```

---

## 📞 技术支持

- 文档：[docs/](./docs/)
- Issues: https://github.com/yourusername/MyHarbor/issues
- 运维手册：[docs/RUNBOOK.md](./docs/RUNBOOK.md)

---

## ✅ 部署检查清单

部署完成后，请确认以下项目：

- [ ] Docker 和 Docker Compose 已安装
- [ ] 防火墙端口 24041 已开放
- [ ] JWT_SECRET 已修改为强密钥
- [ ] 容器启动成功（`docker-compose ps` 显示 Up）
- [ ] 健康检查通过（`curl http://localhost:24041/api/health`）
- [ ] 前台页面可访问
- [ ] 后台可以登录
- [ ] 默认密码已修改
- [ ] 数据目录已配置备份
- [ ] （可选）Nginx 反向代理已配置
- [ ] （可选）HTTPS 证书已配置
- [ ] （可选）监控告警已配置

---

**祝部署顺利！🎉**
