# Labkit Test Suite Makefile
# 用于管理和运行 labkit 的所有测试

.PHONY: help all test-models test-events test-network test-validator test-labkit test-builders clean clean-test-files

# 默认目标
help:
	@echo "Labkit Test Suite 命令:"
	@echo ""
	@echo "🧪 测试命令:"
	@echo "  make all              - 运行所有测试"
	@echo "  make test-models      - 测试基础模型创建和验证"
	@echo "  make test-events      - 测试事件模型系统"
	@echo "  make test-network     - 测试网络配置模型和 YAML 生成"
	@echo "  make test-validator   - 测试 YAML 文件验证器"
	@echo "  make test-labkit      - 测试完整的 labkit 功能"
	@echo "  make test-builders    - 测试网络拓扑构建器"
	@echo ""
	@echo "🔧 工具命令:"
	@echo "  make validate-file    - 验证单个 YAML 文件"
	@echo "  make validate-dir     - 验证实验目录"
	@echo ""
	@echo "🧹 清理命令:"
	@echo "  make clean            - 清理测试生成的文件"
	@echo "  make clean-test-files - 清理测试创建的临时文件"
	@echo ""
	@echo "📋 测试说明:"
	@echo "  test-models:    验证 Pydantic 模型创建、字段验证、类型检查"
	@echo "  test-events:    验证事件系统模型（EventType、NodeExecArgs 等）"
	@echo "  test-network:   验证网络配置模型、YAML 序列化、字段排序"
	@echo "  test-validator: 验证 YAML 文件验证器功能"
	@echo "  test-labkit:    验证完整的 labkit SDK 功能"
	@echo "  test-builders:  验证网络拓扑构建器功能"
	@echo ""
	@echo "💡 使用示例:"
	@echo "  # 运行所有测试"
	@echo "  make all"
	@echo ""
	@echo "  # 只测试网络配置"
	@echo "  make test-network"
	@echo ""
	@echo "  # 验证特定文件"
	@echo "  make validate-file FILE=../network_config_ordered.yaml"
	@echo ""
	@echo "  # 验证实验目录"
	@echo "  make validate-dir DIR=../test_experiment"

# 运行所有测试
all: test-models test-events test-network test-validator test-labkit test-builders
	@echo ""
	@echo "🎉 所有测试完成！"

# 测试基础模型
test-models:
	@echo "🧪 测试基础模型..."
	@cd .. && python3 -c "from labkit.models import *; print('✅ 模型导入成功')"
	@echo "✅ 基础模型测试通过"

# 测试事件模型
test-events:
	@echo "🧪 测试事件模型..."
	@cd .. && python3 test/test_events.py
	@echo "✅ 事件模型测试通过"

# 测试网络配置
test-network:
	@echo "🧪 测试网络配置..."
	@cd .. && python3 test/test_network_config.py
	@echo "✅ 网络配置测试通过"

# 测试验证器
test-validator:
	@echo "🧪 测试 YAML 验证器..."
	@cd .. && python3 test/test_validator.py
	@echo "✅ 验证器测试通过"

# 测试完整 labkit 功能
test-labkit:
	@echo "🧪 测试完整 labkit 功能..."
	@cd .. && python3 test/test_labkit.py
	@echo "✅ labkit 功能测试通过"

# 测试网络拓扑构建器
test-builders:
	@echo "🧪 测试网络拓扑构建器..."
	@cd .. && python3 test/test_builders.py
	@echo "✅ 网络拓扑构建器测试通过"

# 验证单个 YAML 文件
validate-file:
	@if [ -z "$(FILE)" ]; then \
		echo "❌ 请指定文件路径: make validate-file FILE=path/to/file.yaml"; \
		exit 1; \
	fi
	@echo "🔍 验证文件: $(FILE)"
	@cd .. && python3 test/labkit_validate.py "$(FILE)" --verbose

# 验证实验目录
validate-dir:
	@if [ -z "$(DIR)" ]; then \
		echo "❌ 请指定目录路径: make validate-dir DIR=path/to/experiment"; \
		exit 1; \
	fi
	@echo "🔍 验证实验目录: $(DIR)"
	@cd .. && python3 test/labkit_validate.py --experiment "$(DIR)" --verbose

# 清理测试生成的文件
clean:
	@echo "🧹 清理测试文件..."
	@rm -f ../*.yaml
	@rm -f ../invalid_*.yaml
	@rm -rf ../test_experiment
	@echo "✅ 清理完成"

# 清理测试创建的临时文件
clean-test-files:
	@echo "🧹 清理测试临时文件..."
	@rm -f ../labbook.yaml
	@rm -f ../playbook.yaml
	@rm -f ../invalid_*.yaml
	@rm -rf ../test_experiment
	@echo "✅ 临时文件清理完成"

# 显示测试状态
status:
	@echo "📊 测试文件状态:"
	@echo "  test_models.py     - 基础模型测试"
	@echo "  test_events.py     - 事件模型测试"
	@echo "  test_network_config.py - 网络配置测试"
	@echo "  test_validator.py  - 验证器测试"
	@echo "  test_labkit.py     - 完整功能测试"
	@echo "  labkit_validate.py - YAML 验证工具"
	@echo ""
	@echo "📁 测试文件位置: $(PWD)"
	@echo "🐍 Python 环境: $(shell which python3)" 