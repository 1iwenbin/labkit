# SATuSGH LabGrid 用户手册

基于实际案例的完整使用指南

## 📖 目录

- [系统概述](#系统概述)
- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [实验管理](#实验管理)
- [故障排除](#故障排除)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 🚀 系统概述

### 什么是 SATuSGH LabGrid？

SATuSGH LabGrid 是一个基于 LabGrid 框架的卫星网络实验管理系统，专门用于执行 SATuSGH（Satellite Network Topology Generator）实验。

### 核心特性

- **分布式实验执行**：支持多服务器并行执行实验
- **完整的实验生命周期**：从生成到分析的全流程管理
- **智能资源调度**：自动分配和释放服务器资源
- **结果自动分析**：内置 ping 数据分析和网络拓扑验证
- **可扩展架构**：支持添加新的实验类型

### 系统架构

```
SATuSGH LabGrid Manager
├── LabGrid Framework (核心框架)
│   ├── Resource Manager (资源管理)
│   ├── Task Manager (任务管理)
│   ├── Result Manager (结果管理)
│   └── Registry (实验注册)
├── LabX (远程操作接口)
│   ├── SSH 连接管理
│   ├── 文件上传下载
│   └── 命令执行
└── SATuSGH Experiment (实验实现)
    ├── 网络拓扑生成
    ├── 实验执行
    └── 结果分析
```

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装：
- Python 3.8+
- SSH 客户端
- rsync 工具

### 2. 配置文件设置

#### 服务器配置 (`servers.json`)

```json
{
  "ss8": {
    "host": "172.20.64.8",
    "user": "root",
    "port": 22,
    "key_filename": "/path/to/your/key",
    "max_concurrent_tasks": 2,
    "description": "主实验服务器"
  },
  "ss10": {
    "host": "172.20.64.10",
    "user": "root", 
    "port": 22,
    "key_filename": "/path/to/your/key",
    "max_concurrent_tasks": 2,
    "description": "备用实验服务器"
  }
}
```

#### 框架配置 (`configs/framework.json`)

```json
{
  "max_workers": 4,
  "task_queue_size": 100,
  "heartbeat_interval": 30,
  "server_timeout": 300
}
```

### 3. 基本使用

#### 创建管理器

```python
from manage import SATuSGHLabGridManager

# 创建管理器实例
manager = SATuSGHLabGridManager(
    servers_config_file="servers.json",
    config_dir="configs"
)
```

#### 提交实验

```python
# 提交单个实验
task_id = manager.submit_experiment(
    output_dir="results/my_experiment",
    delta_t1=1000,      # 链路删除时间偏移（毫秒）
    delta_t2=2000,      # 链路创建时间偏移（毫秒）
    timeout=1800,       # 超时时间（秒）
    priority=5          # 优先级
)
```

#### 监控实验状态

```python
# 等待实验完成
if manager.wait_for_experiment(task_id, timeout=1800):
    # 获取结果
    result = manager.get_experiment_result(task_id)
    print(f"实验完成！状态: {result.status}")
    print(f"结果指标: {result.metrics}")
```

## 🧠 核心概念

### 实验生命周期

每个 SATuSGH 实验都遵循以下生命周期：

```
1. 初始化 (Initialize)
   ├── 创建输出目录
   ├── 生成网络拓扑配置
   └── 准备实验环境

2. 执行 (Execute)  
   ├── 分配服务器资源
   ├── 上传实验文件
   ├── 运行 kinexlabx 命令
   └── 下载实验结果

3. 收集数据 (Collect Data)
   ├── 清理远程文件
   └── 整理本地数据

4. 分析数据 (Analyze Data)
   ├── 分析网络拓扑
   ├── 处理 ping 数据
   └── 生成分析报告

5. 保存数据 (Save Data)
   ├── 保存实验摘要
   ├── 记录性能指标
   └── 生成结果文件

6. 清理 (Cleanup)
   ├── 释放服务器资源
   └── 清理临时文件
```

### 资源管理

系统自动管理服务器资源：

- **资源分配**：根据负载自动选择可用服务器
- **负载均衡**：避免单台服务器过载
- **资源释放**：实验完成后自动释放资源
- **故障转移**：服务器故障时自动切换到备用服务器

### 任务调度

- **优先级队列**：高优先级任务优先执行
- **依赖管理**：支持任务间的依赖关系
- **并发控制**：限制同时运行的任务数量
- **超时处理**：自动处理超时任务

## 🔬 实验管理

### 实验类型

目前支持的主要实验类型：

#### 1. 基础网络拓扑实验

```python
# 生成 3x3 卫星网格网络
task_id = manager.submit_experiment(
    output_dir="results/grid_3x3",
    delta_t1=0,        # 无链路删除
    delta_t2=0,        # 无链路创建
    timeout=3600
)
```

#### 2. 链路切换实验

```python
# 模拟链路故障和恢复
task_id = manager.submit_experiment(
    output_dir="results/link_switch",
    delta_t1=1000,     # 1秒后删除链路
    delta_t2=2000,     # 2秒后创建新链路
    timeout=3600
)
```

#### 3. 负载测试实验

```python
# 高负载测试
task_id = manager.submit_experiment(
    output_dir="results/load_test",
    delta_t1=500,      # 快速链路切换
    delta_t2=1000,
    timeout=7200,
    priority=10         # 高优先级
)
```

### 批量实验

```python
# 批量提交多个实验
experiments = [
    {"delta_t1": 0, "delta_t2": 0, "output_dir": "results/exp_1"},
    {"delta_t1": 1000, "delta_t2": 2000, "output_dir": "results/exp_2"},
    {"delta_t1": 2000, "delta_t2": 4000, "output_dir": "results/exp_3"}
]

for exp in experiments:
    task_id = manager.submit_experiment(**exp)
    print(f"提交实验: {task_id}")
```

### 实验监控

#### 实时状态监控

```python
# 获取所有任务状态
all_tasks = manager.get_all_tasks()
print("运行中任务:", len(all_tasks["running"]))
print("已完成任务:", len(all_tasks["completed"]))

# 获取框架状态
status = manager.get_framework_status()
print(f"可用服务器: {status['available_servers']}")
print(f"集群负载: {status['cluster_load']:.2f}")
```

#### 结果分析

```python
# 获取实验结果
result = manager.get_experiment_result(task_id)

# 分析结果
if result and result.metrics:
    metrics = result.metrics
    print(f"节点数量: {metrics.get('nodes_count', 0)}")
    print(f"链路数量: {metrics.get('links_count', 0)}")
    print(f"Ping 成功率: {metrics.get('overall_success_rate', 0):.2f}%")
    print(f"网络中断次数: {metrics.get('total_outages', 0)}")
```

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 实验初始化失败

**症状**：实验在初始化阶段失败
```
❌ 初始化实验环境失败: [错误信息]
```

**可能原因**：
- 输出目录权限不足
- SATuSGHLabGen 依赖缺失
- 磁盘空间不足

**解决方案**：
```bash
# 检查目录权限
ls -la results/
chmod 755 results/

# 检查磁盘空间
df -h

# 验证依赖
python3 -c "from util import SATuSGHLabGen; print('依赖正常')"
```

#### 2. 文件上传失败

**症状**：实验文件无法上传到服务器
```
❌ 实验文件上传失败
```

**可能原因**：
- SSH 连接问题
- 服务器磁盘空间不足
- 网络连接不稳定

**解决方案**：
```bash
# 测试 SSH 连接
ssh -i /path/to/key root@server_ip

# 检查服务器磁盘空间
ssh root@server_ip "df -h /tmp"

# 检查网络连通性
ping server_ip
```

#### 3. 实验执行失败

**症状**：kinexlabx 命令执行失败
```
❌ 实验执行失败: [错误信息]
```

**可能原因**：
- kinexlabx 命令不存在
- 配置文件缺失
- 权限不足

**解决方案**：
```bash
# 检查命令是否存在
ssh root@server_ip "which /home/cnic/reals/bin/kinexlabx"

# 检查配置文件
ssh root@server_ip "ls -la /tmp/experiment/network/"

# 检查权限
ssh root@server_ip "ls -la /home/cnic/reals/bin/kinexlabx"
```

#### 4. 资源分配失败

**症状**：无法获取可用服务器
```
⚠️ 没有可用的服务器
```

**可能原因**：
- 所有服务器都在忙碌
- 服务器状态异常
- 配置问题

**解决方案**：
```python
# 检查服务器状态
status = manager.get_framework_status()
print(f"服务器状态: {status}")

# 手动释放服务器（如果需要）
# 重启管理器
manager.stop()
manager = SATuSGHLabGridManager(...)
```

### 调试技巧

#### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 分步验证

```python
# 逐步验证每个阶段
manager = SATuSGHLabGridManager(...)

# 1. 验证连接
print("测试服务器连接...")
manager.print_status()

# 2. 验证文件上传
print("测试文件上传...")
# 手动测试上传功能

# 3. 验证命令执行
print("测试命令执行...")
# 手动测试命令执行
```

#### 3. 检查中间状态

```python
# 检查实验目录结构
import os
output_dir = "results/my_experiment"
if os.path.exists(output_dir):
    for root, dirs, files in os.walk(output_dir):
        print(f"{root}: {len(dirs)} dirs, {len(files)} files")
```

## 💡 最佳实践

### 1. 实验设计

- **合理设置超时时间**：根据实验复杂度设置适当的超时
- **使用有意义的输出目录**：便于结果管理和分析
- **设置合适的优先级**：重要实验设置高优先级

### 2. 资源管理

- **监控服务器负载**：避免单台服务器过载
- **合理设置并发数**：根据服务器性能调整 `max_concurrent_tasks`
- **定期清理结果**：及时清理旧的实验结果

### 3. 错误处理

- **实现重试机制**：对于网络相关的临时错误
- **记录详细日志**：便于问题诊断和复现
- **设置监控告警**：及时发现系统异常

### 4. 性能优化

- **批量提交实验**：减少管理开销
- **并行执行**：充分利用多服务器资源
- **结果缓存**：避免重复计算

## ❓ 常见问题

### Q1: 如何添加新的服务器？

**A**: 在 `servers.json` 中添加新的服务器配置：

```json
{
  "new_server": {
    "host": "192.168.1.100",
    "user": "root",
    "port": 22,
    "key_filename": "/path/to/key",
    "max_concurrent_tasks": 2
  }
}
```

### Q2: 如何修改实验参数？

**A**: 在提交实验时指定参数：

```python
task_id = manager.submit_experiment(
    output_dir="results/custom_exp",
    delta_t1=500,      # 自定义时间偏移
    delta_t2=1500,
    timeout=3600,      # 自定义超时
    priority=8         # 自定义优先级
)
```

### Q3: 如何查看实验历史？

**A**: 使用结果管理器查看：

```python
# 获取所有实验结果
results = manager.labgrid.result_manager.get_all_results()
for result in results:
    print(f"实验 {result.experiment_id}: {result.status}")
```

### Q4: 如何备份实验结果？

**A**: 定期备份 `results` 目录：

```bash
# 创建备份
tar -czf results_backup_$(date +%Y%m%d).tar.gz results/

# 或使用 rsync 同步到备份服务器
rsync -avz results/ backup_server:/backup/satusgh/
```

### Q5: 如何扩展新的实验类型？

**A**: 继承 `Lab` 基类并实现必要的方法：

```python
class MyCustomExperiment(Lab):
    def initialize(self) -> bool:
        # 实现初始化逻辑
        pass
    
    def execute(self) -> bool:
        # 实现执行逻辑
        pass
    
    # 实现其他必要方法...
```

## 📚 进阶主题

### 1. 自定义分析器

```python
from util import PingAnalyzer

# 创建自定义分析器
analyzer = PingAnalyzer(data_dir="my_data")
analyzer.parse_file("ping_results.out")
analyzer.print_summary()
```

### 2. 集成外部工具

```python
# 集成其他分析工具
import subprocess

def run_external_analysis(output_dir):
    result = subprocess.run([
        "external_tool", "--input", output_dir, "--output", "analysis.json"
    ], capture_output=True, text=True)
    return result.returncode == 0
```

### 3. 自动化工作流

```python
# 创建自动化实验流程
def automated_workflow():
    # 1. 提交实验
    task_id = manager.submit_experiment(...)
    
    # 2. 等待完成
    if manager.wait_for_experiment(task_id):
        # 3. 分析结果
        result = manager.get_experiment_result(task_id)
        
        # 4. 根据结果决定下一步
        if result.metrics.get('success_rate', 0) > 90:
            print("实验成功，继续下一步")
        else:
            print("实验失败，需要调整参数")
```

## 🔗 相关资源

- **项目文档**: `README.md`
- **配置示例**: `configs/` 目录
- **实验结果**: `results/` 目录
- **日志文件**: `logs/` 目录

## 📞 技术支持

如果遇到问题，请：

1. 查看日志文件获取详细错误信息
2. 参考故障排除章节的解决方案
3. 检查配置文件是否正确
4. 验证网络和服务器连接

---

*本手册基于实际案例编写，涵盖了从基础使用到高级功能的完整内容。如有疑问，请参考相关章节或查看源代码注释。*
