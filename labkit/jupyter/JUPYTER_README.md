# Labkit Jupyter Notebook 使用指南

这个目录包含了用于在 Jupyter 环境中使用 Labkit 的 Notebook 文件。

## 📁 文件说明

### `labkit_demo.ipynb`
**完整功能演示 Notebook**
- 展示 Labkit 的所有主要功能
- 包含详细的代码示例和说明
- 适合学习和深入了解项目功能
- 包含实用工具函数和最佳实践
- 包含网络拓扑可视化功能
- 支持 Matplotlib 和 Plotly 两种可视化方式

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装 Jupyter 环境依赖
pip install -r requirements-jupyter.txt

# 或者安装基础依赖
pip install -r requirements.txt
pip install jupyter notebook matplotlib plotly networkx
```

### 2. 启动 Jupyter

```bash
# 在项目根目录启动 Jupyter
jupyter notebook

# 或者启动 Jupyter Lab
jupyter lab
```

### 3. 运行 Demo

直接运行 `labkit_demo.ipynb` 即可体验所有功能：

- **网络拓扑构建**: 基础拓扑、预定义拓扑、高级配置
- **实验剧本编写**: 条件触发、流程控制、步骤管理
- **可视化功能**: Matplotlib 静态图、Plotly 交互图
- **配置验证**: 自动验证实验配置
- **保存导出**: YAML 格式配置文件

## 📊 可视化功能

### Matplotlib 可视化
```python
from labkit import visualize_network

# 创建网络配置
network_config = build_star_topology("hub", ["client1", "client2", "client3"])

# 使用 Matplotlib 可视化
visualize_network(network_config, method='matplotlib', figsize=(10, 8))
```

### Plotly 交互式可视化
```python
# 使用 Plotly 创建交互式可视化
fig = visualize_network(network_config, method='plotly', height=600)
fig.show()
```

### 网络分析
```python
from labkit import print_network_summary

# 打印网络配置摘要
print_network_summary(network_config)
```

## 🧪 实验构建示例

### 基础网络实验
```pyt
from labkit import create_labbook, NetworkBuilder

# 创建实验
labbook = create_labbook("基础网络实验", "测试网络连通性")

# 构建网络
network = labbook.network()
network.add_image("ubuntu", "library/ubuntu", "20.04")

node1 = network.add_node("client", "ubuntu")
node1.add_interface("eth0", InterfaceMode.SWITCHED, ["192.168.1.10/24"])
node1.done()

node2 = network.add_node("server", "ubuntu")
node2.add_interface("eth0", InterfaceMode.SWITCHED, ["192.168.1.11/24"])
node2.done()

network.add_switch("switch1")
network.connect("client", "eth0", "server", "eth0", "switch1")

# 构建实验
experiment = labbook.build()
```

### 预定义拓扑
```python
from labkit import build_star_topology, build_linear_topology, build_mesh_topology

# 星型拓扑
star_config = build_star_topology("hub", ["client1", "client2", "client3"])

# 线性拓扑
linear_config = build_linear_topology(["router1", "router2", "router3"])

# 网状拓扑
mesh_config = build_mesh_topology(["node1", "node2", "node3", "node4"])
```

## 📝 实验剧本示例

```python
from labkit import PlaybookBuilder, ConditionType

# 创建剧本
playbook = PlaybookBuilder()

# 添加条件
playbook.add_condition(
    id="network_ready",
    type=ConditionType.COMMAND,
    command="ping -c 1 192.168.1.11",
    target="client"
)

# 添加流程
procedure = playbook.add_procedure("test_connectivity", "network_ready")
procedure.add_step("等待网络就绪", wait_for="network_ready")
procedure.add_step("测试连通性", action_source="ping -c 3 192.168.1.11")
procedure.done()

# 构建剧本
playbook_config = playbook.build()
```

## 💾 保存和导出

```python
from labkit import save_experiment
from pathlib import Path

# 保存实验
output_dir = Path("my_experiment")
saved_path = save_experiment(experiment, str(output_dir))

print(f"实验已保存到: {saved_path}")
```

## 🔧 故障排除

### 导入错误
如果遇到导入错误，请确保：

1. **在项目根目录运行 Notebook**
   ```python
   import sys
   from pathlib import Path
   
   project_root = Path.cwd()
   if str(project_root) not in sys.path:
       sys.path.insert(0, str(project_root))
   ```

2. **安装所有依赖**
   ```bash
   pip install -r requirements-jupyter.txt
   ```

3. **检查 Python 路径**
   ```python
   import labkit
   print(labkit.__file__)
   ```

### 可视化问题
如果可视化不显示：

1. **Matplotlib 后端问题**
   ```python
   import matplotlib
   matplotlib.use('Agg')  # 或者 'TkAgg'
   ```

2. **Plotly 显示问题**
   ```python
   import plotly.io as pio
   pio.renderers.default = "notebook"
   ```

## 📚 学习路径

### 完整学习路径
1. `labkit_demo.ipynb` - 完整功能演示
2. 自定义网络拓扑
3. 复杂实验剧本编写
4. 网络性能测试集成
5. 故障注入实验

## 🎯 最佳实践

1. **模块化设计**: 将复杂的网络拓扑分解为多个模块
2. **版本控制**: 为实验配置添加版本信息
3. **文档化**: 为实验添加详细的描述和说明
4. **测试**: 在保存前验证实验配置
5. **可视化**: 使用可视化工具验证网络拓扑

## 📞 支持

- 查看项目 README: `README.md`
- 查看项目文档: `docs/` 目录
- 查看示例配置: `lab_book/` 目录
- 使用 CLI 工具: `labbook.sh`

## 🚀 下一步

1. 探索更多网络拓扑模式
2. 集成网络性能测试工具
3. 添加网络故障注入功能
4. 扩展可视化功能
5. 集成到 CI/CD 流程

---

**Happy Experimenting! 🧪** 