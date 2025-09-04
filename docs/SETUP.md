# 本地与容器化启动指南

## 一、准备环境
- Python 3.12+
- Node.js 18+（前端）
- Docker 与 Docker Compose（可选）

## 二、配置环境变量
```bash
cp .env.example .env
```

## 三、后端（本地运行）
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```
访问 http://localhost:8000/health

## 四、后端（Docker Compose 运行）
```bash
docker compose up -d postgres redis
# 等待数据库启动
docker compose up backend
```

## 五、前端（本地运行）
```bash
cd frontend
npm install
npm run dev
```
打开浏览器访问 http://localhost:5173

## 六、测试（后端）
```bash
cd backend
source .venv/bin/activate
pytest -q
```