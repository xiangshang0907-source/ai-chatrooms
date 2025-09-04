# AI Chatrooms (Multi-Agent Chat)

一个可创建房间并配置多 AI 角色的实时聊天应用。支持 AI 与 AI 自动对话，用户可随时加入互动。默认模型提供商为 Qwen，可插拔切换（OpenAI、Azure OpenAI、Bedrock 等）。

## 快速开始（本地）

前置：Python 3.11+。

### 1. 环境配置
首先配置环境变量（安全起见，请使用强密码）：

```bash
# 创建环境变量文件
cp .env.example .env

# 编辑 .env 文件，设置数据库密码和其他敏感信息
# 推荐仅设置 POSTGRES_*，程序会自动构建 DATABASE_URL（无需手动设置）
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=ai_chatrooms
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# 可选：如需覆盖自动构建行为，再设置 DATABASE_URL，需与上面保持一致
# DATABASE_URL=postgresql://your_db_user:your_strong_password@localhost:5432/ai_chatrooms

# 重要：请使用强密码，不要使用默认值
```

### 2. 启动服务
```bash
# 使用 Docker Compose（推荐）
docker-compose up -d postgres redis
docker-compose up -d backend

# 或直接运行后端
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

打开浏览器访问 `http://localhost:8000/health`，应返回：
```json
{"status":"ok","service":"ai-chatrooms","version":"0.1.0"}
```

运行测试：
```bash
cd backend
source .venv/bin/activate
pytest -q
```

### 3. 在 GitHub Actions 中运行测试（CI）
在 CI 环境中，建议使用服务容器提供 PostgreSQL，并通过环境变量注入连接串：

```yaml
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres" --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        env:
          # 测试文件会基于此默认连接创建临时数据库
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/postgres
        run: |
          cd backend
          pytest -q
```

说明：
- 测试代码会使用 `postgresql://postgres:postgres@localhost:5432/postgres` 连接默认库来创建临时测试库（见 `backend/tests`）。
- 如需与自定义凭据对齐，可设置 `POSTGRES_*` 或直接设置 `DATABASE_URL`。

## 项目状态

🎉 **Phase 1 已完成** - 核心域与 API 草案  
🚧 **Phase 2 进行中** - MVP 基础功能 (~40% 完成)

### ✅ 已完成功能
- ✅ 完整的业务域模型设计（User、Room、Participant、Message、AgentProfile、ConversationRun）
- ✅ OpenAPI 3.0 规范草案（`docs/api-spec.yaml`）
- ✅ 数据库迁移方案（Alembic + PostgreSQL）
- ✅ 代码质量工具链（ruff、black、mypy）
- ✅ **用户认证系统** (JWT注册/登录/权限管理)
- ✅ **PostgreSQL数据持久化** (所有核心表已创建)
- ✅ **千问API配置** (支持多LLM提供商)

### 🚧 开发中功能
- 🔄 房间管理功能 (创建/加入/配置房间)
- 🔄 消息系统 (用户→AI对话)
- 🔄 AI流式响应 (SSE/WebSocket)
- 🔄 前端聊天UI

**当前API端点**：
- `GET /health` - 健康检查
- `POST /auth/register` - 用户注册  
- `POST /auth/login` - 用户登录
- `POST /auth/refresh` - 刷新令牌
- `GET /auth/me` - 获取用户信息
- `PATCH /auth/me` - 更新用户信息

## 目录结构

```
backend/
  app/
    models/           # 数据模型（SQLAlchemy）
    routes/           # API 路由
    schemas/          # API 模式定义
    config.py         # 配置管理
    constants.py      # 应用常量
  alembic/           # 数据库迁移
    versions/        # 迁移脚本
  tests/             # 单元测试
  requirements.txt   # Python 依赖
  pyproject.toml     # 项目配置
  Makefile          # 开发工具命令
docs/
  api-spec.yaml     # OpenAPI 规范
  requirements.md   # 阶段性需求清单
frontend/
  src/
    App.tsx         # 前端入口
```

## 开发命令

```bash
# 后端开发
cd backend
make help          # 查看所有可用命令
make install       # 安装依赖
make test          # 运行测试
make lint          # 代码检查
make format        # 代码格式化
make run           # 运行开发服务器

# 数据库迁移
python -m alembic upgrade head    # 应用迁移
python -m alembic revision --autogenerate -m "描述"  # 创建新迁移
```

更多需求与阶段性清单见 `docs/requirements.md`。