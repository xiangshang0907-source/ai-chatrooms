# 项目需求与阶段清单

> 将随着实现实时更新（复选框）。

## Phase 0｜项目基础
- [x] 选型与结构确认（Flask、PostgreSQL、React、WebSocket、Docker、Terraform、GitHub Actions）
- [x] 初始化 README（快速开始）
- [x] 健康检查 API（/health）
- [x] 本地开发脚手架（venv + requirements）
- [x] 单元测试基础（pytest）
- [x] 代码规范与静态检查（ruff/black/mypy + pyproject.toml + Makefile）

## Phase 1｜核心域与 API 草案
- [x] 业务域建模（User、Room、Participant、Message、AgentProfile、Provider 等）
- [x] OpenAPI 草案（docs/api-spec.yaml）
- [x] DB 迁移方案（Alembic + 初始迁移脚本）

## Phase 2｜MVP（单房间、单 AI、用户互动）
- [x] 注册/登录（JWT）- 完整实现用户认证系统
- [ ] 创建/加入房间 - 需要实现房间CRUD API
- [ ] 发送消息（用户→AI），AI 流式应答（SSE/WebSocket）
- [x] 持久化（PostgreSQL）- 数据库连接和模型已完成
- [ ] 前端基础聊天 UI

## Phase 3｜多智能体与回合编排
- [ ] 多 AI 角色配置（系统提示、温度等）
- [ ] 回合编排器（轮询、超时、循环检测）
- [ ] 用户插话与打断/重试

## Phase 4｜LLM 提供商可插拔
- [ ] Provider 抽象（同步/流式、重试/退避、超时）
- [ ] 默认集成 Qwen（环境变量配置）
- [ ] 扩展 OpenAI/Azure/Bedrock
- [ ] 前端/后端按房间或 Agent 选择模型

## Phase 5｜实时通信与房间体验
- [ ] WebSocket 或 SSE（在线成员、正在输入、断线重连）
- [ ] 权限与角色（房主/成员）

## Phase 6｜安全与合规
- [ ] Secrets 管理（.env + 云端）
- [ ] 速率限制、CORS/CSRF、防注入
- [ ] 日志脱敏、隐私保护

## Phase 7｜可观测性
- [ ] 结构化日志、指标
- [ ] Trace（OpenTelemetry）
- [ ] 审计日志

## Phase 8｜容器化与本地编排
- [x] Dockerfile、Docker Compose（Postgres、Redis）
- [x] 健康检查、非 root 运行

## Phase 9｜IaC（Terraform）与 AWS 上线（ECS Fargate）
- [ ] VPC/子网/ALB/ECS/ECR/ACM
- [ ] RDS PostgreSQL、Redis、Secrets Manager
- [ ] CloudWatch 告警
- [ ] GitHub OIDC 到 AWS

## Phase 10｜CI/CD 与质量
- [ ] GitHub Actions（lint/test/build/deploy）
- [ ] 单元/集成/端到端测试
- [ ] 依赖与代码扫描

## Phase 11｜数据与分析（OLTP/OLAP）
- [ ] OLTP 表结构与索引
- [ ] 导出到 S3 + Athena 基础查询
- [ ] 仪表盘（核心 KPI）

## Phase 12｜可选增强
- [ ] Kubernetes 轨道（kind/Helm/EKS）
- [ ] RAG/工具调用
- [ ] 多组织/多租户
- [ ] 国际化
- [ ] PWA