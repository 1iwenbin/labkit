# Labkit Makefile
# 用于管理 Python 虚拟环境、依赖安装和项目构建

.PHONY: help venv install install-dev test clean clean-venv lint format check

# 默认目标
help:
	@echo "Labkit Makefile 命令:"
	@echo "  make venv        - 创建 Python 虚拟环境"
	@echo "  make install     - 安装生产依赖"
	@echo "  make install-dev - 安装开发依赖"
	@echo "  make test        - 运行测试"
	@echo "  make lint        - 运行代码检查"
	@echo "  make format      - 格式化代码"
	@echo "  make check       - 运行完整检查（lint + test）"
	@echo "  make clean       - 清理生成的文件"
	@echo "  make clean-venv  - 删除虚拟环境"
	@echo "  make help        - 显示此帮助信息"

# 虚拟环境配置
VENV_NAME = .venv
VENV_PATH = $(VENV_NAME)/bin/activate
PYTHON = python3
PIP = . $(VENV_PATH) && pip

# 创建虚拟环境
venv:
	@echo "创建 Python 虚拟环境..."
	$(PYTHON) -m venv $(VENV_NAME)
	@echo "虚拟环境创建完成: $(VENV_NAME)"
	@echo "激活虚拟环境: source $(VENV_PATH)"

# 安装生产依赖
install: venv
	@echo "安装生产依赖..."
	$(PIP) install -r requirements.txt
	@echo "依赖安装完成"

# 安装开发依赖（如果有 requirements-dev.txt）
install-dev: install
	@if [ -f requirements-dev.txt ]; then \
		echo "安装开发依赖..."; \
		$(PIP) install -r requirements-dev.txt; \
		echo "开发依赖安装完成"; \
	else \
		echo "requirements-dev.txt 不存在，跳过开发依赖安装"; \
	fi

# 运行测试
test: install
	@echo "运行测试..."
	. $(VENV_PATH) && python3 test_labkit.py

# 代码检查（如果安装了 flake8）
lint: install
	@if . $(VENV_PATH) && command -v flake8 >/dev/null 2>&1; then \
		echo "运行代码检查..."; \
		. $(VENV_PATH) && flake8 labkit/ --max-line-length=100 --ignore=E501,W503; \
	else \
		echo "flake8 未安装，跳过代码检查"; \
		echo "安装 flake8: make install-dev 或 pip install flake8"; \
	fi

# 代码格式化（如果安装了 black）
format: install
	@if . $(VENV_PATH) && command -v black >/dev/null 2>&1; then \
		echo "格式化代码..."; \
		. $(VENV_PATH) && black labkit/ --line-length=100; \
	else \
		echo "black 未安装，跳过代码格式化"; \
		echo "安装 black: make install-dev 或 pip install black"; \
	fi

# 运行完整检查
check: lint test
	@echo "所有检查完成"

# 清理生成的文件
clean:
	@echo "清理生成的文件..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@echo "清理完成"

# 删除虚拟环境
clean-venv:
	@echo "删除虚拟环境..."
	@rm -rf $(VENV_NAME)
	@echo "虚拟环境已删除"

# 完全清理（包括虚拟环境）
clean-all: clean clean-venv
	@echo "完全清理完成"

# 显示虚拟环境状态
status:
	@echo "虚拟环境状态:"
	@if [ -d "$(VENV_NAME)" ]; then \
		echo "✅ 虚拟环境存在: $(VENV_NAME)"; \
		if [ -f "$(VENV_PATH)" ]; then \
			echo "✅ 虚拟环境可激活"; \
		else \
			echo "❌ 虚拟环境损坏"; \
		fi; \
	else \
		echo "❌ 虚拟环境不存在"; \
	fi
	@echo ""
	@echo "Python 版本:"
	@$(PYTHON) --version
	@echo ""
	@echo "已安装的包:"
	@if [ -d "$(VENV_NAME)" ]; then \
		. $(VENV_PATH) && pip list; \
	else \
		echo "虚拟环境不存在，无法显示已安装的包"; \
	fi

# 重新创建虚拟环境（清理后重新创建）
rebuild: clean-venv install
	@echo "虚拟环境重建完成"

# 更新依赖
update: install
	@echo "更新依赖包..."
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements.txt
	@echo "依赖更新完成" 