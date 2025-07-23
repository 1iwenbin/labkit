#!/usr/bin/env python3
"""
nbformat 使用指南 - 创建和操作 .ipynb 文件

这个文件展示了如何使用 nbformat 库来：
1. 创建新的 Jupyter notebook
2. 读取现有的 notebook
3. 修改 notebook 内容
4. 添加不同类型的单元格
5. 设置元数据和内核信息
"""

import nbformat as nbf
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class NotebookBuilder:
    """Jupyter Notebook 构建器"""
    
    def __init__(self, title: str = "Untitled", kernel: str = "python3"):
        """
        初始化 notebook 构建器
        
        Args:
            title: notebook 标题
            kernel: 内核名称 (python3, python2, r, julia 等)
        """
        self.title = title
        self.kernel = kernel
        self.notebook = nbf.v4.new_notebook()
        self._setup_metadata()
    
    def _setup_metadata(self):
        """设置 notebook 元数据"""
        self.notebook.metadata = {
            "kernelspec": {
                "display_name": f"Python 3 ({self.kernel})",
                "language": "python",
                "name": self.kernel
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.0"
            }
        }
    
    def add_markdown_cell(self, content: str, cell_id: Optional[str] = None) -> 'NotebookBuilder':
        """
        添加 Markdown 单元格
        
        Args:
            content: Markdown 内容
            cell_id: 单元格 ID (可选)
        
        Returns:
            self: 支持链式调用
        """
        cell = nbf.v4.new_markdown_cell(content)
        if cell_id:
            cell.id = cell_id
        self.notebook.cells.append(cell)
        return self
    
    def add_code_cell(self, source: str, outputs: Optional[List] = None, 
                      execution_count: Optional[int] = None, cell_id: Optional[str] = None) -> 'NotebookBuilder':
        """
        添加代码单元格
        
        Args:
            source: Python 代码
            outputs: 输出列表 (可选)
            execution_count: 执行计数 (可选)
            cell_id: 单元格 ID (可选)
        
        Returns:
            self: 支持链式调用
        """
        cell = nbf.v4.new_code_cell(source)
        if outputs:
            cell.outputs = outputs
        if execution_count is not None:
            cell.execution_count = execution_count
        if cell_id:
            cell.id = cell_id
        self.notebook.cells.append(cell)
        return self
    
    def add_raw_cell(self, content: str, cell_id: Optional[str] = None) -> 'NotebookBuilder':
        """
        添加原始单元格
        
        Args:
            content: 原始内容
            cell_id: 单元格 ID (可选)
        
        Returns:
            self: 支持链式调用
        """
        cell = nbf.v4.new_raw_cell(content)
        if cell_id:
            cell.id = cell_id
        self.notebook.cells.append(cell)
        return self
    
    def add_cell_with_output(self, source: str, output_text: str, 
                           output_type: str = "stream", cell_id: Optional[str] = None) -> 'NotebookBuilder':
        """
        添加带有输出的代码单元格
        
        Args:
            source: Python 代码
            output_text: 输出文本
            output_type: 输出类型 (stream, display_data, execute_result 等)
            cell_id: 单元格 ID (可选)
        
        Returns:
            self: 支持链式调用
        """
        cell = nbf.v4.new_code_cell(source)
        
        if output_type == "stream":
            output = nbf.v4.new_output("stream", text=output_text)
        elif output_type == "display_data":
            output = nbf.v4.new_output("display_data", data={"text/plain": output_text})
        elif output_type == "execute_result":
            output = nbf.v4.new_output("execute_result", data={"text/plain": output_text})
        else:
            output = nbf.v4.new_output("stream", text=output_text)
        
        cell.outputs = [output]
        if cell_id:
            cell.id = cell_id
        self.notebook.cells.append(cell)
        return self
    
    def build(self) -> nbf.NotebookNode:
        """构建并返回 notebook 对象"""
        return self.notebook
    
    def save(self, filepath: str) -> str:
        """
        保存 notebook 到文件
        
        Args:
            filepath: 文件路径
        
        Returns:
            str: 保存的文件路径
        """
        nbf.write(self.notebook, filepath)
        return filepath


class NotebookReader:
    """Jupyter Notebook 读取器"""
    
    @staticmethod
    def read(filepath: str) -> nbf.NotebookNode:
        """
        读取 notebook 文件
        
        Args:
            filepath: notebook 文件路径
        
        Returns:
            nbf.NotebookNode: notebook 对象
        """
        return nbf.read(filepath, as_version=4)
    
    @staticmethod
    def get_cells(notebook: nbf.NotebookNode) -> List[Dict[str, Any]]:
        """
        获取所有单元格信息
        
        Args:
            notebook: notebook 对象
        
        Returns:
            List[Dict]: 单元格信息列表
        """
        cells_info = []
        for i, cell in enumerate(notebook.cells):
            cell_info = {
                "index": i,
                "cell_type": cell.cell_type,
                "id": getattr(cell, 'id', None),
                "source": cell.source,
                "metadata": cell.metadata
            }
            
            if cell.cell_type == "code":
                cell_info.update({
                    "execution_count": cell.execution_count,
                    "outputs": cell.outputs
                })
            
            cells_info.append(cell_info)
        
        return cells_info
    
    @staticmethod
    def get_code_cells(notebook: nbf.NotebookNode) -> List[str]:
        """
        获取所有代码单元格的源代码
        
        Args:
            notebook: notebook 对象
        
        Returns:
            List[str]: 代码列表
        """
        return [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    
    @staticmethod
    def get_markdown_cells(notebook: nbf.NotebookNode) -> List[str]:
        """
        获取所有 Markdown 单元格的内容
        
        Args:
            notebook: notebook 对象
        
        Returns:
            List[str]: Markdown 内容列表
        """
        return [cell.source for cell in notebook.cells if cell.cell_type == "markdown"]


class NotebookModifier:
    """Jupyter Notebook 修改器"""
    
    @staticmethod
    def add_cell(notebook: nbf.NotebookNode, cell: nbf.NotebookNode, position: Optional[int] = None) -> nbf.NotebookNode:
        """
        在指定位置添加单元格
        
        Args:
            notebook: notebook 对象
            cell: 要添加的单元格
            position: 插入位置 (None 表示末尾)
        
        Returns:
            nbf.NotebookNode: 修改后的 notebook
        """
        if position is None:
            notebook.cells.append(cell)
        else:
            notebook.cells.insert(position, cell)
        return notebook
    
    @staticmethod
    def remove_cell(notebook: nbf.NotebookNode, index: int) -> nbf.NotebookNode:
        """
        删除指定索引的单元格
        
        Args:
            notebook: notebook 对象
            index: 单元格索引
        
        Returns:
            nbf.NotebookNode: 修改后的 notebook
        """
        if 0 <= index < len(notebook.cells):
            del notebook.cells[index]
        return notebook
    
    @staticmethod
    def update_cell(notebook: nbf.NotebookNode, index: int, new_source: str) -> nbf.NotebookNode:
        """
        更新指定单元格的内容
        
        Args:
            notebook: notebook 对象
            index: 单元格索引
            new_source: 新的内容
        
        Returns:
            nbf.NotebookNode: 修改后的 notebook
        """
        if 0 <= index < len(notebook.cells):
            notebook.cells[index].source = new_source
        return notebook
    
    @staticmethod
    def clear_outputs(notebook: nbf.NotebookNode) -> nbf.NotebookNode:
        """
        清除所有代码单元格的输出
        
        Args:
            notebook: notebook 对象
        
        Returns:
            nbf.NotebookNode: 修改后的 notebook
        """
        for cell in notebook.cells:
            if cell.cell_type == "code":
                cell.outputs = []
                cell.execution_count = None
        return notebook


def create_labkit_demo_notebook() -> str:
    """
    创建一个 Labkit 演示 notebook
    
    Returns:
        str: 保存的文件路径
    """
    builder = NotebookBuilder("Labkit 演示", "python3")
    
    # 添加标题
    builder.add_markdown_cell("# Labkit 网络实验演示\n\n这个 notebook 展示了如何使用 Labkit 创建网络实验。")
    
    # 添加导入语句
    builder.add_code_cell("""# 导入必要的库
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from labkit import create_labbook, NetworkBuilder, InterfaceMode
from labkit import build_star_topology, build_linear_topology
from labkit import visualize_network, print_network_summary
from labkit import PlaybookBuilder, ConditionType
from labkit import save_experiment

print("Labkit 导入成功！")""")
    
    # 添加网络拓扑示例
    builder.add_markdown_cell("## 1. 创建基础网络拓扑\n\n让我们创建一个简单的星型网络拓扑。")
    
    builder.add_code_cell("""# 创建星型拓扑
star_config = build_star_topology("hub", ["client1", "client2", "client3"])

# 打印网络配置摘要
print_network_summary(star_config)""")
    
    # 添加可视化示例
    builder.add_markdown_cell("## 2. 网络拓扑可视化\n\n使用 Matplotlib 可视化网络拓扑。")
    
    builder.add_code_cell("""# 使用 Matplotlib 可视化
import matplotlib.pyplot as plt

fig = visualize_network(star_config, method='matplotlib', figsize=(10, 8))
plt.title("星型网络拓扑")
plt.show()""")
    
    # 添加实验创建示例
    builder.add_markdown_cell("## 3. 创建完整实验\n\n创建一个包含网络配置和实验剧本的完整实验。")
    
    builder.add_code_cell("""# 创建实验
labbook = create_labbook("网络连通性测试", "测试客户端与服务器之间的网络连通性")

# 构建网络
network = labbook.network()
network.add_image("ubuntu", "library/ubuntu", "20.04")

# 添加客户端节点
client = network.add_node("client", "ubuntu")
client.add_interface("eth0", InterfaceMode.SWITCHED, ["192.168.1.10/24"])
client.done()

# 添加服务器节点
server = network.add_node("server", "ubuntu")
server.add_interface("eth0", InterfaceMode.SWITCHED, ["192.168.1.11/24"])
server.done()

# 添加交换机
network.add_switch("switch1")

# 连接节点
network.connect("client", "eth0", "server", "eth0", "switch1")

# 构建实验
experiment = labbook.build()

print("实验创建成功！")""")
    
    # 添加实验剧本示例
    builder.add_markdown_cell("## 4. 创建实验剧本\n\n添加条件触发和流程控制。")
    
    builder.add_code_cell("""# 创建实验剧本
playbook = PlaybookBuilder()

# 添加网络就绪条件
playbook.add_condition(
    id="network_ready",
    type=ConditionType.COMMAND,
    command="ping -c 1 192.168.1.11",
    target="client"
)

# 添加测试流程
procedure = playbook.add_procedure("test_connectivity", "network_ready")
procedure.add_step("等待网络就绪", wait_for="network_ready")
procedure.add_step("测试连通性", action_source="ping -c 3 192.168.1.11")
procedure.done()

# 构建剧本
playbook_config = playbook.build()

print("实验剧本创建成功！")""")
    
    # 添加保存示例
    builder.add_markdown_cell("## 5. 保存实验\n\n将实验保存到文件。")
    
    builder.add_code_cell("""# 保存实验
output_dir = Path("my_network_experiment")
saved_path = save_experiment(experiment, str(output_dir))

print(f"实验已保存到: {saved_path}")""")
    
    # 添加总结
    builder.add_markdown_cell("""## 总结

这个演示展示了 Labkit 的主要功能：

1. **网络拓扑构建**: 使用预定义函数快速创建常见拓扑
2. **可视化**: 支持 Matplotlib 和 Plotly 两种可视化方式
3. **实验创建**: 完整的实验配置和节点管理
4. **实验剧本**: 条件触发和流程控制
5. **保存导出**: YAML 格式配置文件

### 下一步

- 尝试创建更复杂的网络拓扑
- 添加更多的实验步骤和条件
- 集成网络性能测试工具
- 探索故障注入功能""")
    
    # 保存 notebook
    filepath = "labkit_demo_generated.ipynb"
    return builder.save(filepath)


def create_tutorial_notebook() -> str:
    """
    创建一个 nbformat 教程 notebook
    
    Returns:
        str: 保存的文件路径
    """
    builder = NotebookBuilder("nbformat 使用教程", "python3")
    
    # 添加标题
    builder.add_markdown_cell("""# nbformat 使用教程

这个 notebook 展示了如何使用 `nbformat` 库来创建和操作 Jupyter notebook 文件。

## 什么是 nbformat？

`nbformat` 是 Jupyter 项目的一部分，用于处理 `.ipynb` 文件的读写操作。它提供了：

- 创建新的 notebook 文件
- 读取现有的 notebook 文件
- 修改 notebook 内容
- 添加不同类型的单元格
- 设置元数据和内核信息""")
    
    # 添加导入示例
    builder.add_code_cell("""# 导入 nbformat
import nbformat as nbf
import json
from pathlib import Path

print("nbformat 版本:", nbf.__version__)""")
    
    # 添加创建 notebook 示例
    builder.add_markdown_cell("## 1. 创建新的 Notebook")
    
    builder.add_code_cell("""# 创建新的 notebook
notebook = nbf.v4.new_notebook()

# 设置元数据
notebook.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }
}

print("Notebook 创建成功！")""")
    
    # 添加单元格示例
    builder.add_markdown_cell("## 2. 添加不同类型的单元格")
    
    builder.add_code_cell("""# 添加 Markdown 单元格
markdown_cell = nbf.v4.new_markdown_cell("# 这是一个标题\\n\\n这是 Markdown 内容")
notebook.cells.append(markdown_cell)

# 添加代码单元格
code_cell = nbf.v4.new_code_cell("print('Hello, World!')")
notebook.cells.append(code_cell)

# 添加原始单元格
raw_cell = nbf.v4.new_raw_cell("这是原始内容")
notebook.cells.append(raw_cell)

print(f"添加了 {len(notebook.cells)} 个单元格")""")
    
    # 添加保存示例
    builder.add_markdown_cell("## 3. 保存 Notebook")
    
    builder.add_code_cell("""# 保存 notebook
nbf.write(notebook, 'example_notebook.ipynb')
print("Notebook 已保存到 example_notebook.ipynb")""")
    
    # 添加读取示例
    builder.add_markdown_cell("## 4. 读取现有的 Notebook")
    
    builder.add_code_cell("""# 读取 notebook
loaded_notebook = nbf.read('example_notebook.ipynb', as_version=4)

print("Notebook 信息:")
print(f"- 单元格数量: {len(loaded_notebook.cells)}")
print(f"- 内核: {loaded_notebook.metadata.get('kernelspec', {}).get('name', 'Unknown')}")

# 显示所有单元格类型
for i, cell in enumerate(loaded_notebook.cells):
    print(f"- 单元格 {i}: {cell.cell_type}")""")
    
    # 添加修改示例
    builder.add_markdown_cell("## 5. 修改 Notebook 内容")
    
    builder.add_code_cell("""# 修改代码单元格
if loaded_notebook.cells:
    # 找到第一个代码单元格
    for cell in loaded_notebook.cells:
        if cell.cell_type == "code":
            cell.source = "print('Modified content!')"
            break

# 添加新的单元格
new_cell = nbf.v4.new_code_cell("print('This is a new cell')")
loaded_notebook.cells.append(new_cell)

# 保存修改后的 notebook
nbf.write(loaded_notebook, 'modified_notebook.ipynb')
print("修改后的 notebook 已保存")""")
    
    # 添加高级功能示例
    builder.add_markdown_cell("## 6. 高级功能")
    
    builder.add_code_cell("""# 创建带有输出的代码单元格
cell_with_output = nbf.v4.new_code_cell("print('Hello from cell with output')")

# 添加输出
output = nbf.v4.new_output("stream", text="Hello from cell with output\\n")
cell_with_output.outputs = [output]
cell_with_output.execution_count = 1

notebook.cells.append(cell_with_output)

# 保存
nbf.write(notebook, 'advanced_notebook.ipynb')
print("高级 notebook 已保存")""")
    
    # 添加总结
    builder.add_markdown_cell("""## 总结

通过这个教程，我们学习了：

1. **基本操作**: 创建、读取、保存 notebook
2. **单元格类型**: Markdown、代码、原始单元格
3. **内容修改**: 添加、删除、修改单元格
4. **高级功能**: 输出、执行计数、元数据

### 实用技巧

- 使用 `nbf.v4.new_notebook()` 创建新 notebook
- 使用 `nbf.read()` 读取现有 notebook
- 使用 `nbf.write()` 保存 notebook
- 设置适当的元数据以确保兼容性
- 使用单元格 ID 进行精确定位

### 下一步

- 探索更多 nbformat 功能
- 集成到自动化脚本中
- 创建 notebook 模板
- 批量处理多个 notebook 文件""")
    
    # 保存 notebook
    filepath = "nbformat_tutorial.ipynb"
    return builder.save(filepath)


def demonstrate_notebook_operations():
    """演示各种 notebook 操作"""
    print("=== nbformat 操作演示 ===\n")
    
    # 1. 创建简单的 notebook
    print("1. 创建简单的 notebook...")
    builder = NotebookBuilder("简单示例", "python3")
    builder.add_markdown_cell("# 简单示例\n\n这是一个使用 nbformat 创建的 notebook。")
    builder.add_code_cell("print('Hello, nbformat!')")
    builder.add_code_cell("import numpy as np\nimport matplotlib.pyplot as plt\n\nx = np.linspace(0, 10, 100)\ny = np.sin(x)\nplt.plot(x, y)\nplt.title('正弦波')\nplt.show()")
    
    simple_notebook = builder.save("simple_example.ipynb")
    print(f"   保存到: {simple_notebook}")
    
    # 2. 读取和修改 notebook
    print("\n2. 读取和修改 notebook...")
    reader = NotebookReader()
    notebook = reader.read(simple_notebook)
    
    # 获取单元格信息
    cells_info = reader.get_cells(notebook)
    print(f"   找到 {len(cells_info)} 个单元格:")
    for info in cells_info:
        print(f"   - 类型: {info['cell_type']}, 内容长度: {len(info['source'])}")
    
    # 修改 notebook
    modifier = NotebookModifier()
    modifier.add_cell(notebook, nbf.v4.new_markdown_cell("## 新添加的内容\n\n这是后来添加的 Markdown 单元格。"))
    modifier.add_cell(notebook, nbf.v4.new_code_cell("print('这是新添加的代码单元格')"))
    
    nbf.write(notebook, "modified_example.ipynb")
    print("   修改后的 notebook 已保存到: modified_example.ipynb")
    
    # 3. 创建复杂的 notebook
    print("\n3. 创建复杂的 notebook...")
    complex_builder = NotebookBuilder("复杂示例", "python3")
    
    # 添加多个单元格
    complex_builder.add_markdown_cell("""# 复杂示例

这个 notebook 展示了更复杂的 nbformat 用法。

## 功能列表

1. 多种单元格类型
2. 带输出的代码单元格
3. 自定义元数据
4. 链式调用""")
    
    complex_builder.add_code_cell("""# 导入库
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

print("库导入完成")""")
    
    complex_builder.add_code_cell("""# 创建示例数据
data = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100),
    'category': np.random.choice(['A', 'B', 'C'], 100)
})

print("数据创建完成")
print(f"数据形状: {data.shape}")""")
    
    complex_builder.add_code_cell("""# 数据可视化
plt.figure(figsize=(10, 6))
sns.scatterplot(data=data, x='x', y='y', hue='category')
plt.title('散点图示例')
plt.show()""")
    
    complex_notebook = complex_builder.save("complex_example.ipynb")
    print(f"   保存到: {complex_notebook}")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    # 运行演示
    demonstrate_notebook_operations()
    
    # 创建示例 notebook
    print("\n创建示例 notebook...")
    labkit_demo_path = create_labkit_demo_notebook()
    tutorial_path = create_tutorial_notebook()
    
    print(f"Labkit 演示 notebook: {labkit_demo_path}")
    print(f"nbformat 教程 notebook: {tutorial_path}")
    
    print("\n所有 notebook 文件已创建完成！") 