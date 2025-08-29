# 安全配置指南

## 数据库密码安全

### 当前问题
- ❌ 硬编码的默认密码在配置文件中
- ❌ Docker Compose 中包含明文密码
- ❌ 测试文件中包含硬编码密码

### 解决方案

#### 1. 使用环境变量（推荐方式）
创建 `.env` 文件（不要提交到版本控制）：

**方式一：使用单独的数据库参数（推荐）**
```bash
# 数据库基础配置 - 程序会自动构建 DATABASE_URL
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=ai_chatrooms
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# 应用密钥
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

**方式二：直接设置完整的 DATABASE_URL**
```bash
# 数据库连接字符串
DATABASE_URL=postgresql://your_db_user:your_strong_password@localhost:5432/ai_chatrooms

# 应用密钥
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

**推荐使用方式一**，因为：
- 避免重复配置
- 更容易管理和修改
- Docker Compose 可以复用这些参数
- 程序会自动构建完整的连接字符串

#### 2. 生成强密码
使用以下命令生成强密码：
```bash
# 生成随机密码
openssl rand -base64 32

# 或使用 Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 3. 生产环境建议
- 使用密钥管理服务（如 AWS Secrets Manager、Azure Key Vault）
- 使用 Docker Secrets（在 Swarm 模式下）
- 使用 Kubernetes Secrets
- 定期轮换密码

## 其他安全措施

### JWT 密钥
- 使用强随机密钥
- 定期轮换
- 不同环境使用不同密钥

### API 密钥
- 所有 LLM 提供商的 API 密钥都应通过环境变量配置
- 不要在代码中硬编码
- 定期轮换

### 数据库连接
- 使用 SSL/TLS 连接
- 限制数据库访问权限
- 使用连接池
- 定期备份

## 开发环境设置

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入实际值

3. 启动服务：
```bash
docker-compose up -d
```

## 安全检查清单

- [ ] 所有密码都通过环境变量配置
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 生产环境使用强密码
- [ ] 数据库连接使用 SSL
- [ ] API 密钥定期轮换
- [ ] 日志中不包含敏感信息
- [ ] 错误信息不泄露系统信息
