.PHONY: help install dev-install test lint format check clean run

help:  ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 安装生产依赖
	pip install -r requirements.txt

dev-install:  ## 安装开发依赖
	pip install -r requirements.txt

test:  ## 运行测试
	python -m pytest

lint:  ## 代码检查
	python -m ruff check .
	python -m mypy .

format:  ## 代码格式化
	python -m ruff format .

check: lint test  ## 完整的代码检查和测试

clean:  ## 清理缓存文件
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

run:  ## 运行开发服务器
	python -m app.main
