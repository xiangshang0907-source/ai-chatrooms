# AI Chatrooms (Multi-Agent Chat)

一个可创建房间并配置多 AI 角色的实时聊天应用。支持 AI 与 AI 自动对话，用户可随时加入互动。默认模型提供商为 Qwen，可插拔切换（OpenAI、Azure OpenAI、Bedrock 等）。

## 快速开始（本地）

前置：Python 3.11+。

```bash
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

## 项目状态

🎉 **Phase 1 已完成** - 核心域与 API 草案
- ✅ 完整的业务域模型设计（User、Room、Participant、Message、AgentProfile、ConversationRun）
- ✅ OpenAPI 3.0 规范草案（`docs/api-spec.yaml`）
- ✅ 数据库迁移方案（Alembic + PostgreSQL）
- ✅ 代码质量工具链（ruff、black、mypy）

**接下来**：开始 Phase 2 MVP 开发（用户认证、房间管理、基础消息功能）

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