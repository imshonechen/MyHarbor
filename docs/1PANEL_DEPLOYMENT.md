# MyHarbor 1Panel 部署指南

## 📋 概述

本文档介绍如何将 MyHarbor 项目集成到 1Panel 面板中进行管理。1Panel 是一个现代化的 Linux 服务器运维管理面板，支持 Docker 容器管理。

## 🚀 部署方式

### 方式一：通过 1Panel 容器管理（推荐）

#### 步骤 1: 创建项目目录

**重要：必须先创建目录，再上传文件！**

1. 在 1Panel 中进入 **文件** → **文件管理**
2. 导航到 `/opt/1panel/apps/` 目录
3. 点击 **新建文件夹**，创建 `myharbor` 目录
4. 或者通过 SSH 终端创建：
   ```bash
   mkdir -p /opt/1panel/apps/myharbor
   ```

#### 步骤 2: 上传项目文件

使用以下任一方式上传：

**方式 A: 通过 1Panel 文件管理**
1. 进入 `/opt/1panel/apps/myharbor/` 目录
2. 点击 **上传** 按钮
3. 上传所有项目文件（backend、frontend、docker-compose.yml、Dockerfile 等）

**方式 B: 通过 FTP/SFTP 客户端**
```bash
# 使用 FileZilla、WinSCP 等工具
# 上传到: /opt/1panel/apps/myharbor/
```

**方式 C: 通过 SCP 命令**
```bash
# 从本地上传到服务器
scp -r MyHarbor/* root@your-server-ip:/opt/1panel/apps/myharbor/
```

上传完成后，确保目录结构如下：
```
/opt/1panel/apps/myharbor/
├── backend/
├── frontend/
├── docker-compose.yml
├── Dockerfile
└── .dockerignore
```

#### 步骤 3: 修改配置文件

在 1Panel 文件管理中编辑 `docker-compose.yml`，修改 JWT_SECRET：

```yaml
environment:
  - JWT_SECRET=your-generated-strong-secret-key-here
```

生成强密钥（在服务器终端执行）：
```bash
openssl rand -base64 32
```

#### 步骤 4: 在 1Panel 中创建编排

1. 登录 1Panel 面板
2. 进入 **容器** → **编排**
3. 点击 **创建编排**
4. 填写信息：
   - **名称**: `myharbor`
   - **路径**: `/opt/1panel/apps/myharbor`（必须是已存在的目录）
   - **描述**: `个人站点导航系统`

5. 点击 **确认**，1Panel 会自动读取该目录下的 `docker-compose.yml` 文件

**注意事项：**
- 路径必须是绝对路径
- 目录必须已存在且包含 `docker-compose.yml` 文件
- 确保文件权限正确（可执行 `chmod -R 755 /opt/1panel/apps/myharbor`）

#### 步骤 5: 启动容器

1. 在编排列表中找到 `myharbor`
2. 点击 **启动** 按钮
3. 等待容器构建和启动（首次启动需要构建镜像，可能需要几分钟）

**如果启动失败，请检查：**
- 查看日志：点击编排名称 → 查看日志
- 检查端口占用：`netstat -tulpn | grep 24041`
- 检查文件权限：`ls -la /opt/1panel/apps/myharbor`
- 验证 docker-compose.yml 语法：
  ```bash
  cd /opt/1panel/apps/myharbor
  docker-compose config
  ```

#### 步骤 6: 查看日志获取后台路由码

1. 在编排列表中找到 `myharbor`
2. 点击编排名称进入详情
3. 点击 **日志** 标签
4. 搜索 `Default admin config initialized` 或 `Backend URL` 关键字
5. 记录后台访问路由码

或通过终端查看：
```bash
# 查看完整日志
docker-compose -f /opt/1panel/apps/myharbor/docker-compose.yml logs

# 或直接查看容器日志
docker logs myharbor

# 搜索路由码关键字
docker logs myharbor 2>&1 | grep -Ei "Default admin config initialized|Backend URL"
```

**如果日志中没有路由码信息：**

可能是容器启动时间较早，日志已被清理。可以通过以下方式查看：

```bash
# 方法 1: 进入容器查看路由码
docker exec -it myharbor python manage.py show-route

# 方法 2: 进入容器查看管理员信息
docker exec -it myharbor python manage.py show-admin
```

或者在 1Panel 容器终端中执行：
1. 在编排详情中，点击容器名称
2. 点击 **终端** 按钮
3. 执行命令：
   ```bash
   python manage.py show-route
   ```

#### 步骤 7: 访问应用

**重要：查看实际端口号**

应用启动后，日志中会显示实际的访问地址。端口号可能是：
- `24041` - 默认端口
- `24043` 或其他端口 - 如果 1Panel 检测到端口冲突，会自动分配新端口

**查看实际访问地址：**

1. 在容器日志中查找 "后台访问地址" 或 "Backend URL"
2. 或者检查 docker-compose.yml 中的端口映射：
   ```bash
   # 在 1Panel 文件管理中查看
   cat /opt/1panel/apps/myharbor/docker-compose.yml | grep -A 2 "ports:"
   ```

**访问方式：**

假设日志显示端口为 `24043`：

1. 浏览器访问前台：`http://your-server-ip:24043`
2. 访问后台：`http://your-server-ip:24043/{路由码}`
3. 默认账号：`admin` / `admin123`
4. **立即修改默认密码！**

**如果无法访问，检查防火墙：**

```bash
# 在 1Panel 安全设置中开放对应端口
# 或通过命令行开放
sudo ufw allow 24043/tcp
sudo ufw reload
```

#### 步骤 8: 配置网站访问（可选）

如果需要通过域名访问，可以在 1Panel 中配置反向代理：

1. 进入 **网站** → **创建网站**
2. 选择 **反向代理**
3. 填写信息：
   - **域名**: `harbor.yourdomain.com`
   - **代理地址**: `http://127.0.0.1:24041`
4. 保存后即可通过域名访问

---

## 🆘 常见问题排查

### 问题 1: 创建编排时报错 "no such file or directory"

**原因**: 目录不存在或路径错误

**解决方法**:
```bash
# 1. 确认目录是否存在
ls -la /opt/1panel/apps/myharbor

# 2. 如果不存在，创建目录
mkdir -p /opt/1panel/apps/myharbor

# 3. 上传文件后，验证 docker-compose.yml 存在
ls -la /opt/1panel/apps/myharbor/docker-compose.yml

# 4. 测试 docker-compose 配置
cd /opt/1panel/apps/myharbor
docker-compose config
```

### 问题 2: 容器构建失败

**可能原因**:
- 网络问题导致依赖下载失败
- 磁盘空间不足
- Docker 镜像拉取失败

**解决方法**:
```bash
# 1. 检查磁盘空间
df -h

# 2. 清理 Docker 缓存
docker system prune -a

# 3. 手动构建查看详细错误
cd /opt/1panel/apps/myharbor
docker-compose build --no-cache

# 4. 查看构建日志
docker-compose logs --tail=100
```

### 问题 3: 端口被占用

**解决方法**:
```bash
# 1. 查看端口占用
netstat -tulpn | grep 24041

# 2. 停止占用端口的进程
kill -9 <PID>

# 3. 或修改 docker-compose.yml 使用其他端口
ports:
  - "24042:24041"  # 改用 24042 端口
```

### 问题 4: 无法访问网站

**检查清单**:
```bash
# 1. 容器是否运行
docker ps | grep myharbor

# 2. 检查容器日志
docker logs myharbor

# 3. 测试容器内部访问
docker exec myharbor curl http://localhost:24041/api/health

# 4. 检查防火墙
ufw status
# 或
firewall-cmd --list-ports

# 5. 在 1Panel 安全设置中开放端口 24041
```

---

### 方式二：通过 1Panel 应用商店（自定义应用）

#### 步骤 1: 准备应用配置

创建应用配置文件 `app.json`：

```json
{
  "name": "MyHarbor",
  "version": "1.0.0",
  "description": "个人站点导航系统",
  "icon": "",
  "author": "Your Name",
  "category": "tools",
  "docker_compose": "docker-compose.yml",
  "env": [
    {
      "key": "JWT_SECRET",
      "name": "JWT密钥",
      "description": "用于JWT令牌加密的密钥（至少32位）",
      "required": true,
      "default": "change-this-secret-in-production-min-32-chars"
    },
    {
      "key": "JWT_EXPIRE_HOURS",
      "name": "JWT过期时间（小时）",
      "description": "JWT令牌的有效期",
      "required": false,
      "default": "24"
    },
    {
      "key": "CHECK_TIMEOUT_SECONDS",
      "name": "检测超时时间（秒）",
      "description": "站点状态检测的超时时间",
      "required": false,
      "default": "5"
    }
  ],
  "ports": [
    {
      "container": 24041,
      "host": 24041,
      "protocol": "tcp",
      "description": "Web访问端口"
    }
  ],
  "volumes": [
    {
      "container": "/app/data",
      "host": "./data",
      "description": "数据持久化目录"
    }
  ]
}
```

#### 步骤 2: 打包应用

将以下文件打包成 zip：
```
myharbor.zip
├── app.json
├── docker-compose.yml
├── Dockerfile
├── backend/
├── frontend/
└── README.md
```

#### 步骤 3: 安装应用

1. 在 1Panel 中进入 **应用商店** → **本地应用**
2. 点击 **上传应用**
3. 上传 `myharbor.zip`
4. 填写环境变量（特别是 JWT_SECRET）
5. 点击安装

---

## 🔧 1Panel 管理功能

### 容器管理

在 1Panel 容器管理界面可以进行：

- **启动/停止/重启** 容器
- **查看日志** - 实时查看应用日志
- **进入终端** - 执行命令（如重置密码）
- **查看资源** - CPU、内存、网络使用情况
- **更新镜像** - 重新构建容器

### 常用操作

#### 1. 查看后台路由码

```bash
# 在容器终端中执行
python manage.py show-route
```

或在 1Panel 日志中搜索 `route`

#### 2. 重置管理员密码

```bash
# 在容器终端中执行
python manage.py reset-admin
```

#### 3. 修改管理员凭证

```bash
# 在容器终端中执行
python manage.py set-admin --username admin --password NewPassword123!
```

#### 4. 备份数据

在 1Panel 文件管理中：
1. 进入 `/opt/1panel/apps/myharbor/data/`
2. 下载 `myharbor.db` 文件
3. 或打包整个 `data` 目录

#### 5. 更新应用

```bash
# 方法1: 在编排管理中
1. 停止容器
2. 上传新版本文件（覆盖旧文件）
3. 点击"重建"按钮
4. 启动容器

# 方法2: 在容器终端中
docker-compose down
docker-compose up -d --build
```

---

## 🌐 配置反向代理和 HTTPS

### 使用 1Panel 内置 Nginx

#### 步骤 1: 创建网站

1. 进入 **网站** → **创建网站**
2. 选择 **反向代理**
3. 填写配置：
   - **主域名**: `harbor.yourdomain.com`
   - **代理地址**: `http://127.0.0.1:24041`
   - **启用缓存**: 否
   - **启用 WebSocket**: 否（MyHarbor 不需要）

#### 步骤 2: 申请 SSL 证书

1. 在网站列表中找到刚创建的网站
2. 点击 **SSL** 按钮
3. 选择 **Let's Encrypt**
4. 点击 **申请证书**
5. 等待证书申请完成

#### 步骤 3: 修改 docker-compose.yml

将端口映射改为仅监听本地：

```yaml
ports:
  - "127.0.0.1:24041:24041"
```

然后重建容器。

---

## 📊 监控和告警

### 使用 1Panel 监控功能

1. 进入 **监控** 页面
2. 查看容器资源使用情况：
   - CPU 使用率
   - 内存使用量
   - 网络流量
   - 磁盘 I/O

### 配置告警（如果 1Panel 支持）

1. 设置 CPU 使用率告警阈值：80%
2. 设置内存使用率告警阈值：80%
3. 设置磁盘使用率告警阈值：85%

---

## 🔐 安全建议

### 1. 修改默认端口（可选）

如果不使用反向代理，建议修改默认端口：

```yaml
ports:
  - "自定义端口:24041"
```

### 2. 限制访问 IP

在 1Panel 防火墙中：
1. 进入 **安全** → **防火墙**
2. 添加规则：
   - **端口**: 24041
   - **协议**: TCP
   - **策略**: 允许
   - **来源**: 指定 IP 或 IP 段

### 3. 定期备份

在 1Panel 中设置定时任务：

1. 进入 **计划任务** → **创建任务**
2. 选择 **Shell 脚本**
3. 填写脚本：
   ```bash
   #!/bin/bash
   cd /opt/1panel/apps/myharbor
   tar -czf /backup/myharbor-$(date +%Y%m%d).tar.gz data/
   find /backup -name "myharbor-*.tar.gz" -mtime +7 -delete
   ```
4. 设置执行时间：每天凌晨 2:00

---

## 🆘 故障排查

### 容器无法启动

1. 在 1Panel 中查看容器日志
2. 检查端口是否被占用：
   ```bash
   netstat -tulpn | grep 24041
   ```
3. 检查磁盘空间：
   ```bash
   df -h
   ```

### 无法访问网站

1. 检查容器状态是否为 Running
2. 检查防火墙规则是否正确
3. 检查反向代理配置是否正确
4. 测试容器内部访问：
   ```bash
   curl http://localhost:24041/api/health
   ```

### 数据丢失

1. 检查 volume 挂载是否正确
2. 查看 `/opt/1panel/apps/myharbor/data/` 目录
3. 从备份恢复数据

---

## 📝 注意事项

1. **数据持久化**: 确保 `data` 目录正确挂载，否则容器重启后数据会丢失
2. **JWT_SECRET**: 生产环境必须修改为强密钥
3. **备份策略**: 建议每天自动备份数据库文件
4. **资源限制**: 如果服务器资源有限，可以在 docker-compose.yml 中添加资源限制
5. **日志管理**: 定期清理容器日志，避免占用过多磁盘空间

---

## 🔗 相关链接

- [1Panel 官方文档](https://1panel.cn/docs/)
- [MyHarbor 部署文档](../DEPLOYMENT.md)
- [MyHarbor 运维手册](./RUNBOOK.md)

---

**祝部署顺利！🎉**
