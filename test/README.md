# Labkit Test Suite

这个目录包含了 labkit 库的完整测试套件，用于验证各个组件的功能和正确性。

## 📁 目录结构

```
test/
├── Makefile              # 测试管理工具
├── README.md             # 本文件
├── test_events.py        # 事件模型测试
├── test_labkit.py        # 完整功能测试
├── test_network_config.py # 网络配置测试
├── test_validator.py     # YAML 验证器测试
└── labkit_validate.py    # YAML 验证命令行工具
```

## 🧪 测试文件说明

### 1. `test_events.py` - 事件模型测试
**用途**: 验证事件系统模型的功能
**测试内容**:
- EventType 枚举值验证
- NodeExecArgs 参数验证
- LinkProperties 属性验证
- InterfaceCreateArgs 接口创建参数验证
- Event 事件对象创建和验证

**运行方式**:
```bash
make test-events
# 或
python3 test_events.py
```

### 2. `test_labkit.py` - 完整功能测试
**用途**: 验证 labkit SDK 的完整功能
**测试内容**:
- 基础模型创建和验证
- 剧本模型系统
- 时间表达式验证
- 完整实验创建

**运行方式**:
```bash
make test-labkit
# 或
python3 test_labkit.py
```

### 3. `test_network_config.py` - 网络配置测试
**用途**: 验证网络配置模型和 YAML 生成
**测试内容**:
- NetworkConfig 模型创建
- YAML 序列化和反序列化
- 字段顺序固定
- 复杂网络拓扑配置

**运行方式**:
```bash
make test-network
# 或
python3 test_network_config.py
```

### 4. `test_validator.py` - 验证器测试
**用途**: 验证 YAML 文件验证器功能
**测试内容**:
- 有效文件验证
- 无效文件错误检测
- 详细错误报告
- 实验目录验证

**运行方式**:
```bash
make test-validator
# 或
python3 test_validator.py
```

### 5. `labkit_validate.py` - YAML 验证工具
**用途**: 命令行工具，用于验证 YAML 文件
**功能**:
- 单文件验证
- 实验目录验证
- 自动类型检测
- 详细错误报告

**使用方式**:
```bash
# 验证单个文件
python3 labkit_validate.py network_config.yaml

# 验证实验目录
python3 labkit_validate.py --experiment ./my_experiment

# 显示详细错误
python3 labkit_validate.py --verbose invalid_file.yaml
```

## 🛠️ Makefile 命令

### 测试命令
```bash
make all              # 运行所有测试
make test-models      # 测试基础模型
make test-events      # 测试事件模型
make test-network     # 测试网络配置
make test-validator   # 测试验证器
make test-labkit      # 测试完整功能
```

### 工具命令
```bash
make validate-file FILE=path/to/file.yaml  # 验证单个文件
make validate-dir DIR=path/to/experiment   # 验证实验目录
```

### 清理命令
```bash
make clean            # 清理所有测试文件
make clean-test-files # 清理临时文件
```

### 信息命令
```bash
make help             # 显示帮助信息
make status           # 显示测试状态
```

## 🚀 快速开始

### 1. 运行所有测试
```bash
cd test
make all
```

### 2. 运行特定测试
```bash
cd test
make test-network     # 只测试网络配置
```

### 3. 验证 YAML 文件
```bash
cd test
make validate-file FILE=../network_config_ordered.yaml
```

### 4. 验证实验目录
```bash
cd test
make validate-dir DIR=../test_experiment
```

## 📊 测试覆盖范围

- ✅ **模型验证**: Pydantic 模型创建、字段验证、类型检查
- ✅ **事件系统**: 事件类型、执行参数、属性设置
- ✅ **网络配置**: 拓扑定义、节点配置、链路设置
- ✅ **YAML 处理**: 序列化、反序列化、字段排序
- ✅ **验证器**: 文件验证、错误报告、目录验证
- ✅ **集成测试**: 完整功能流程测试

## 🔧 开发说明

### 添加新测试
1. 在 `test/` 目录下创建新的测试文件
2. 在 `Makefile` 中添加对应的测试目标
3. 更新 `README.md` 文档

### 测试最佳实践
- 每个测试文件专注于一个功能模块
- 包含有效和无效数据的测试用例
- 提供清晰的错误信息和调试信息
- 使用描述性的测试函数名称

### 环境要求
- Python 3.8+
- 虚拟环境已激活
- 依赖包已安装 (`pip install -r requirements.txt`)

## 🐛 故障排除

### 常见问题
1. **导入错误**: 确保在项目根目录运行测试
2. **依赖缺失**: 运行 `pip install -r requirements.txt`
3. **权限问题**: 确保有文件读写权限

### 调试技巧
- 使用 `--verbose` 参数获取详细输出
- 检查生成的临时文件
- 查看错误报告中的字段路径

## 📝 更新日志

- **v1.0.0**: 初始测试套件
  - 基础模型测试
  - 事件系统测试
  - 网络配置测试
  - YAML 验证器测试
  - 命令行工具 