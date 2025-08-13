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

## 目录结构（初版）

```
backend/
  app/
    routes/
  tests/
  requirements.txt
docs/
```

更多需求与阶段性清单见 `docs/requirements.md`。