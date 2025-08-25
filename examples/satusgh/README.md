# SATuSGH LabGrid 实验管理器

基于 LabGrid 框架重新实现的 SATuSGH 实验管理器，提供完整的实验生命周期管理、多服务器并发执行和自动负载均衡功能。

## 🚀 特性

- **基于 LabGrid 框架**: 利用成熟的分布式实验执行框架
- **完整的实验生命周期**: 初始化、执行、数据收集、分析、保存、清理
- **多服务器支持**: 自动管理多台服务器的资源分配和负载均衡
- **并发执行**: 支持多个实验同时在不同服务器上执行
- **自动资源管理**: 智能分配服务器资源，避免过载
- **结果管理**: 自动存储和分析实验结果
- **错误处理**: 完善的异常处理和重试机制

## 📁 项目结构

```
examples/satusgh/
├── manage.py              # LabGrid 版本的实验管理器
├── util.py                # SATuSGH 工具函数
├── configs/               # 配置文件目录
│   ├── servers.json       # 服务器配置
│   └── framework.json     # 框架配置
├── logs/                  # 日志目录（自动创建）
├── results/               # 实验结果目录（自动创建）
└── README.md              # 本文档
```

## 🔧 安装和配置

### 1. 依赖要求

- Python 3.7+
- LabGrid 框架
- SSH 密钥认证配置

### 2. 服务器配置

确保 `configs/servers.json` 文件配置正确：

```json
{
  "ss8": {
    "host": "172.20.64.8",
    "user": "root",
    "port": 22,
    "password": null,
    "key_filename": "/home/cnic/.ssh/id_rsa",
    "max_concurrent_tasks": 2,
    "description": "SS8服务器"
  }
}
```

### 3. 框架配置

`configs/framework.json` 包含框架运行参数：

```json
{
  "max_worker_threads": 8,
  "max_workers_per_server": 2,
  "max_total_workers": 16,
  "experiment_timeout": 86400,
  "log_level": "INFO"
}
```

## 🚀 使用方法

### 1. 基本使用

```python
from manage import SATuSGHLabGridManager

# 创建管理器
manager = SATuSGHLabGridManager(
    servers_config_file="configs/servers.json",
    config_dir="configs"
)

# 提交单个实验
task_id = manager.submit_experiment(
    output_dir="results/my_experiment",
    delta_t1=1000,    # 链路删除时间偏移量（毫秒）
    delta_t2=2000,    # 链路创建时间偏移量（毫秒）
    timeout=3600,     # 超时时间（秒）
    priority=5         # 优先级
)

# 等待实验完成
if manager.wait_for_experiment(task_id, timeout=3600):
    # 获取结果
    result = manager.get_experiment_result(task_id)
    print(f"实验完成: {result.status.value}")
    print(f"结果指标: {result.metrics}")
```

### 2. 批量实验

```python
# 批量提交实验
experiments = [
    {
        'output_dir': 'results/exp_1',
        'delta_t1': 1000,
        'delta_t2': 2000,
        'timeout': 1800,
        'priority': 5
    },
    {
        'output_dir': 'results/exp_2',
        'delta_t1': 1500,
        'delta_t2': 2500,
        'timeout': 1800,
        'priority': 3
    }
]

task_ids = manager.submit_batch_experiments(experiments)
print(f"提交了 {len(task_ids)} 个实验任务")
```

### 3. 监控和管理

```python
# 获取框架状态
status = manager.get_framework_status()
print(f"框架状态: {status}")

# 获取所有任务
tasks = manager.get_all_tasks()
print(f"运行中: {len(tasks['running'])}")
print(f"已完成: {len(tasks['completed'])}")

# 打印详细状态
manager.print_status()

# 停止管理器
manager.stop()
```

## 🔬 实验类详解

### SATuSGHExperiment 类

继承自 LabGrid 的 `Lab` 基类，实现完整的实验生命周期：

```python
class SATuSGHExperiment(Lab):
    def initialize(self) -> bool:      # 初始化实验环境
    def execute(self) -> bool:         # 执行实验
    def collect_data(self) -> bool:    # 收集数据
    def analyze_data(self) -> dict:    # 分析结果
    def save_data(self) -> bool:       # 保存结果
    def cleanup(self):                 # 清理环境
```

### 实验执行流程

1. **初始化阶段**: 生成网络拓扑和实验环境
2. **执行阶段**: 在远程服务器上运行实验
3. **数据收集**: 下载实验结果并清理临时文件
4. **数据分析**: 分析实验结果并生成指标
5. **结果保存**: 保存实验摘要和结果文件
6. **环境清理**: 清理临时文件和资源

## 📊 结果管理

### 实验结果结构

```
results/
└── my_experiment/
    ├── experiment_summary.json    # 实验摘要
    ├── network_topology/          # 网络拓扑文件
    ├── experiment_timeline/       # 实验时间线
    └── analysis_results/          # 分析结果
```

### 实验摘要格式

```json
{
  "experiment_id": "exp_1234567890_1234_1000_2000",
  "delta_t1": 1000,
  "delta_t2": 2000,
  "server_name": "ss8",
  "start_time": "2024-01-01T10:00:00",
  "end_time": "2024-01-01T10:30:00",
  "duration": 1800.5,
  "status": "COMPLETED",
  "metrics": {
    "success_rate": 95.5,
    "performance_score": 87.3
  }
}
```

## 🚀 高级功能

### 1. 优先级管理

```python
# 高优先级实验
high_priority_task = manager.submit_experiment(
    output_dir="results/urgent_exp",
    delta_t1=1000,
    delta_t2=2000,
    priority=10  # 高优先级
)

# 低优先级实验
low_priority_task = manager.submit_experiment(
    output_dir="results/background_exp",
    delta_t1=1000,
    delta_t2=2000,
    priority=1   # 低优先级
)
```

### 2. 超时控制

```python
# 设置实验超时时间
task_id = manager.submit_experiment(
    output_dir="results/timeout_exp",
    delta_t1=1000,
    delta_t2=2000,
    timeout=900  # 15分钟超时
)
```

### 3. 依赖管理

```python
# 创建依赖关系
config = create_experiment_config(
    experiment_type="satusgh_experiment",
    output_dir="results/dependent_exp",
    parameters={'delta_t1': 1000, 'delta_t2': 2000},
    dependencies=["exp_1234567890_1234_1000_2000"]  # 依赖其他实验
)
```

## 🐛 故障排除

### 常见问题

1. **连接失败**: 检查 SSH 密钥配置和网络连接
2. **权限错误**: 确保用户有足够的权限执行命令
3. **超时错误**: 调整超时设置或检查服务器性能
4. **资源不足**: 减少并发任务数或添加更多服务器

### 调试模式

```python
# 启用调试日志
import logging
logging.getLogger('SATuSGH').setLevel(logging.DEBUG)

# 检查详细状态
manager.print_status()
```

## 📈 性能优化

### 1. 并发设置

```python
# 根据服务器性能调整并发数
{
  "max_worker_threads": 16,        # 总工作线程数
  "max_workers_per_server": 4,     # 每台服务器最大线程数
  "max_total_workers": 32          # 最大总工作线程数
}
```

### 2. 资源分配策略

- **最少负载**: 优先选择负载较低的服务器
- **轮询分配**: 均匀分配任务到所有服务器
- **优先级分配**: 高优先级任务优先分配资源

## 🤝 扩展开发

### 1. 自定义实验类型

```python
class CustomExperiment(Lab):
    def initialize(self) -> bool:
        # 自定义初始化逻辑
        return True
    
    def execute(self) -> bool:
        # 自定义执行逻辑
        return True
    
    # ... 其他方法
```

### 2. 注册新实验类型

```python
manager.labgrid.register_experiment(
    experiment_type="custom_experiment",
    experiment_class=CustomExperiment,
    description="自定义实验类型",
    tags=["custom", "experiment"]
)
```

## 📚 示例代码

查看 `manage.py` 文件中的 `main()` 函数获取完整的使用示例。

## 🏁 总结

SATuSGH LabGrid 实验管理器提供了：

- **完整的实验管理**: 从提交到完成的完整流程
- **高效的资源利用**: 多服务器并发执行和负载均衡
- **灵活的配置**: 支持多种参数和策略配置
- **可靠的结果管理**: 自动存储和分析实验结果
- **易于扩展**: 基于 LabGrid 框架，易于添加新功能

通过使用 LabGrid 框架，SATuSGH 实验管理器获得了企业级的可靠性和可扩展性，同时保持了简单易用的接口。
