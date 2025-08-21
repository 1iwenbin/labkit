# LabGrid 实验框架

LabGrid 是一个可扩展的分布式实验执行框架，支持多服务器并发执行和实验生命周期管理。

## 🚀 特性

- **可扩展架构**: 用户只需继承 `Lab` 基类即可实现自己的实验
- **多服务器支持**: 自动管理多台服务器的资源分配和负载均衡
- **实验生命周期管理**: 完整的实验执行流程控制
- **任务调度**: 支持优先级队列、依赖管理和重试机制
- **结果管理**: 实验结果的存储、检索、分析和版本管理
- **资源监控**: 实时监控服务器状态和资源使用情况

## 📁 项目结构

```
labkit/labgrid/
├── __init__.py          # 框架入口和便捷函数
├── framework.py         # LabGrid 主类
├── experiment.py        # Lab 实验抽象基类
├── labx.py             # LabX 服务器能力封装
├── types.py             # 类型定义
├── config.py            # 配置管理
├── registry.py          # 实验注册器
├── task_manager.py      # 任务管理器
├── resource_manager.py  # 资源管理器
├── result_manager.py    # 结果管理器
├── example.py           # 使用示例
└── README.md            # 本文档
```

## 🔧 安装和配置

### 1. 服务器配置

创建 `configs/servers.json` 文件：

```json
{
  "server1": {
    "host": "192.168.1.100",
    "user": "username",
    "port": 22,
    "password": "password",
    "max_concurrent_tasks": 2,
    "description": "主服务器"
  },
  "server2": {
    "host": "192.168.1.101",
    "user": "username",
    "port": 22,
    "key_filename": "/path/to/private_key",
    "max_concurrent_tasks": 1,
    "description": "备用服务器"
  }
}
```

### 2. 框架配置（可选）

创建 `configs/framework.json` 文件：

```json
{
  "max_worker_threads": 8,
  "max_workers_per_server": 2,
  "max_total_workers": 16,
  "experiment_timeout": 86400,
  "task_queue_size": 1000,
  "log_level": "INFO",
  "log_dir": "logs",
  "result_retention_days": 30,
  "enable_monitoring": true
}
```

## 🚀 快速开始

### 1. 创建框架实例

```python
from labkit.labgrid import create_labgrid

# 创建框架实例
labgrid = create_labgrid(
    servers_config_file="configs/servers.json",
    framework_config_file="configs/framework.json"
)
```

### 2. 定义实验类

```python
from labkit.labgrid import Lab

class MyNetworkExperiment(Lab):
    """我的网络实验"""
    
    def initialize(self) -> bool:
        """初始化实验环境"""
        # 创建必要的目录和文件
        # 准备实验数据和配置
        return True
    
    def execute(self) -> bool:
        """执行实验"""
        # 使用 self.labx 在服务器上执行实验
        # self.labx.execute_command(server_name, command)
        # self.labx.upload_file(server_name, local_path, remote_path)
        return True
    
    def collect_data(self) -> bool:
        """收集实验数据"""
        # 从服务器下载实验结果
        # self.labx.download_file(server_name, remote_path, local_path)
        return True
    
    def analyze_data(self) -> dict:
        """分析实验数据"""
        # 分析实验结果，返回性能指标
        return {
            'success_rate': 95.5,
            'performance_score': 87.3
        }
    
    def save_data(self) -> bool:
        """保存实验结果"""
        # 保存分析结果和报告
        return True
    
    def cleanup(self):
        """清理实验环境（可选）"""
        # 清理临时文件和资源
        super().cleanup()  # 调用父类方法释放服务器
```

### 3. 注册实验类型

```python
# 注册实验类型
labgrid.register_experiment(
    experiment_type="my_network_experiment",
    experiment_class=MyNetworkExperiment,
    description="网络性能测试实验",
    tags=["network", "performance", "test"]
)
```

### 4. 运行实验

```python
from labkit.labgrid import create_experiment_config

# 创建实验配置
config = create_experiment_config(
    experiment_type="my_network_experiment",
    output_dir="results/my_experiment",
    parameters={
        "test_duration": 300,
        "packet_size": 1500
    },
    timeout=600,
    retry_count=2,
    priority=5
)

# 运行实验
task_id = labgrid.run_experiment("my_network_experiment", config)

# 等待实验完成
if labgrid.wait_for_experiment(task_id, timeout=600):
    # 获取实验结果
    result = labgrid.get_experiment_result(task_id)
    print(f"实验完成，状态: {result.status.value}")
else:
    print("实验执行超时")
```

### 5. 批量运行实验

```python
# 创建多个实验配置
experiments = []
for i in range(5):
    config = create_experiment_config(
        experiment_type="my_network_experiment",
        output_dir=f"results/experiment_{i}",
        parameters={"test_id": i}
    )
    experiments.append(("my_network_experiment", config))

# 批量运行
task_ids = labgrid.run_batch_experiments(experiments)
print(f"提交了 {len(task_ids)} 个实验任务")
```

## 📊 监控和查询

### 框架状态

```python
# 获取框架信息
info = labgrid.get_framework_info()
print(f"框架状态: {info['status']}")
print(f"运行时间: {info['uptime']:.1f} 秒")

# 打印详细状态
labgrid.print_status()
```

### 任务状态

```python
# 获取所有任务
all_tasks = labgrid.get_all_tasks()
print(f"等待中: {len(all_tasks['pending'])}")
print(f"运行中: {len(all_tasks['running'])}")
print(f"已完成: {len(all_tasks['completed'])}")

# 获取任务统计
stats = labgrid.get_task_stats()
print(f"总任务数: {stats['total_tasks']}")
print(f"成功率: {stats['total_completed'] / stats['total_tasks'] * 100:.1f}%")
```

### 服务器状态

```python
# 获取集群摘要
cluster_summary = labgrid.get_cluster_summary()
print(f"总服务器: {cluster_summary['total_servers']}")
print(f"可用服务器: {cluster_summary['available_servers']}")
print(f"集群负载: {cluster_summary['cluster_load']:.2f}")

# 获取特定服务器信息
server_info = labgrid.get_server_info("server1")
if server_info:
    print(f"服务器状态: {server_info.status.value}")
    print(f"当前任务数: {server_info.current_tasks}")
```

### 实验结果

```python
# 获取所有结果
all_results = labgrid.get_all_results()
print(f"总结果数: {len(all_results)}")

# 搜索结果
search_results = labgrid.search_results("network")
print(f"搜索结果: {len(search_results)}")

# 比较结果
comparison = labgrid.compare_results([result1.experiment_id, result2.experiment_id])
print(f"比较结果: {comparison}")

# 导出结果
labgrid.export_results("results_export.json", format="json")
```

## 🔧 高级功能

### 资源分配策略

```python
# 设置资源分配策略
labgrid.set_allocation_strategy("least_loaded")  # 最少负载
# 可选策略: "round_robin", "least_loaded", "priority_based"
```

### 健康检查

```python
# 执行健康检查
health = labgrid.health_check()
print(f"框架状态: {health['framework_status']}")
print(f"服务器健康: {health['servers']}")
```

### 配置管理

```python
# 更新框架配置
labgrid.update_framework_config(
    max_worker_threads=16,
    log_level="DEBUG"
)

# 获取当前配置
config = labgrid.get_framework_config()
print(f"最大工作线程: {config.max_worker_threads}")
```

## 🧹 清理和维护

### 清理旧结果

```python
# 清理7天前的旧结果
labgrid.cleanup_old_results(days=7)
```

### 关闭框架

```python
# 停止框架
labgrid.stop()

# 或者使用上下文管理器
with create_labgrid("configs/servers.json") as labgrid:
    # 框架会自动启动和停止
    labgrid.run_experiment("my_experiment", config)
```

## 📝 最佳实践

### 1. 实验类设计

- 继承 `Lab` 基类并实现所有必需的方法
- 在 `initialize()` 中验证环境要求
- 在 `execute()` 中使用 `self.labx` 操作服务器
- 在 `cleanup()` 中确保资源被正确释放
- 使用 `self.log()` 记录实验过程

### 2. 错误处理

- 在每个阶段都进行适当的错误检查
- 使用 `try-except` 块捕获异常
- 在出错时记录详细的错误信息
- 确保即使出错也能正确清理资源

### 3. 资源管理

- 合理设置超时时间
- 使用重试机制处理临时性错误
- 监控服务器负载，避免过载
- 定期清理过期结果

### 4. 性能优化

- 使用批量操作减少网络开销
- 合理设置工作线程数量
- 根据服务器性能调整并发任务数
- 使用优先级队列管理重要任务

## 🐛 故障排除

### 常见问题

1. **连接失败**: 检查服务器配置和网络连接
2. **权限错误**: 确保用户有足够的权限执行命令
3. **超时错误**: 调整超时设置或检查服务器性能
4. **资源不足**: 减少并发任务数或添加更多服务器

### 调试模式

```python
# 启用调试日志
labgrid.update_framework_config(log_level="DEBUG")

# 检查详细状态
labgrid.print_status()
```

## 📚 更多示例

查看 `example.py` 文件获取完整的使用示例。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进框架。

## 📄 许可证

本项目采用 MIT 许可证。
