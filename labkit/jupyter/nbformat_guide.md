# nbformat 使用指南

`nbformat` 是 Jupyter 项目的一部分，用于以编程方式创建和操作 `.ipynb` 文件。

## 安装

```bash
pip install nbformat
```

## 基本用法

### 1. 创建新的 Notebook

```python
import nbformat as nbf

# 创建新的 notebook
notebook = nbf.v4.new_notebook()

# 设置元数据
notebook.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }
}
```

### 2. 添加单元格

```python
# 添加 Markdown 单元格
markdown_cell = nbf.v4.new_markdown_cell("# 标题\n\n这是 Markdown 内容")
notebook.cells.append(markdown_cell)

# 添加代码单元格
code_cell = nbf.v4.new_code_cell("print('Hello, World!')")
notebook.cells.append(code_cell)

# 添加原始单元格
raw_cell = nbf.v4.new_raw_cell("这是原始内容")
notebook.cells.append(raw_cell)
```

### 3. 保存 Notebook

```python
# 保存到文件
nbf.write(notebook, 'my_notebook.ipynb')
```

### 4. 读取现有 Notebook

```python
# 读取 notebook
loaded_notebook = nbf.read('my_notebook.ipynb', as_version=4)

# 获取信息
print(f"单元格数量: {len(loaded_notebook.cells)}")
print(f"内核: {loaded_notebook.metadata.get('kernelspec', {}).get('name', 'Unknown')}")
```

### 5. 修改 Notebook

```python
# 修改单元格内容
if loaded_notebook.cells:
    for cell in loaded_notebook.cells:
        if cell.cell_type == "code":
            cell.source = "print('Modified content!')"
            break

# 添加新单元格
new_cell = nbf.v4.new_code_cell("print('New cell')")
loaded_notebook.cells.append(new_cell)

# 保存修改
nbf.write(loaded_notebook, 'modified_notebook.ipynb')
```

## 高级功能

### 1. 带输出的代码单元格

```python
# 创建带输出的代码单元格
cell = nbf.v4.new_code_cell("print('Hello from cell with output')")

# 添加输出
output = nbf.v4.new_output("stream", text="Hello from cell with output\n")
cell.outputs = [output]
cell.execution_count = 1

notebook.cells.append(cell)
```

### 2. 不同类型的输出

```python
# 流输出
stream_output = nbf.v4.new_output("stream", text="这是流输出\n")

# 显示数据输出
display_output = nbf.v4.new_output("display_data", data={"text/plain": "这是显示数据"})

# 执行结果输出
execute_output = nbf.v4.new_output("execute_result", data={"text/plain": "这是执行结果"})

# 错误输出
error_output = nbf.v4.new_output("error", ename="ValueError", evalue="Invalid value")
```

### 3. 设置单元格元数据

```python
# 创建单元格并设置元数据
cell = nbf.v4.new_code_cell("print('Cell with metadata')")
cell.metadata = {
    "collapsed": False,
    "scrolled": True,
    "tags": ["important", "demo"]
}
```

## 实用工具类

### NotebookBuilder 类

```python
class NotebookBuilder:
    def __init__(self, title="Untitled", kernel="python3"):
        self.notebook = nbf.v4.new_notebook()
        self._setup_metadata()
    
    def add_markdown_cell(self, content):
        cell = nbf.v4.new_markdown_cell(content)
        self.notebook.cells.append(cell)
        return self  # 支持链式调用
    
    def add_code_cell(self, source):
        cell = nbf.v4.new_code_cell(source)
        self.notebook.cells.append(cell)
        return self
    
    def save(self, filepath):
        nbf.write(self.notebook, filepath)
        return filepath

# 使用示例
builder = NotebookBuilder("我的 Notebook")
builder.add_markdown_cell("# 标题").add_code_cell("print('Hello')").save("example.ipynb")
```

### NotebookReader 类

```python
class NotebookReader:
    @staticmethod
    def read(filepath):
        return nbf.read(filepath, as_version=4)
    
    @staticmethod
    def get_code_cells(notebook):
        return [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    
    @staticmethod
    def get_markdown_cells(notebook):
        return [cell.source for cell in notebook.cells if cell.cell_type == "markdown"]

# 使用示例
reader = NotebookReader()
notebook = reader.read("example.ipynb")
code_sources = reader.get_code_cells(notebook)
```

## 批量处理

### 批量创建 Notebook

```python
import os

def create_notebooks_from_templates(templates_dir, output_dir):
    """从模板批量创建 notebook"""
    os.makedirs(output_dir, exist_ok=True)
    
    for template_file in os.listdir(templates_dir):
        if template_file.endswith('.py'):
            # 读取 Python 文件作为代码
            with open(os.path.join(templates_dir, template_file), 'r') as f:
                code = f.read()
            
            # 创建 notebook
            notebook = nbf.v4.new_notebook()
            notebook.cells.append(nbf.v4.new_markdown_cell(f"# {template_file}"))
            notebook.cells.append(nbf.v4.new_code_cell(code))
            
            # 保存
            output_file = os.path.join(output_dir, f"{template_file[:-3]}.ipynb")
            nbf.write(notebook, output_file)
```

### 批量修改 Notebook

```python
def batch_clear_outputs(notebook_dir):
    """批量清除所有 notebook 的输出"""
    for filename in os.listdir(notebook_dir):
        if filename.endswith('.ipynb'):
            filepath = os.path.join(notebook_dir, filename)
            notebook = nbf.read(filepath, as_version=4)
            
            # 清除输出
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    cell.outputs = []
                    cell.execution_count = None
            
            # 保存
            nbf.write(notebook, filepath)
```

## 常见用例

### 1. 从 Python 脚本创建 Notebook

```python
def script_to_notebook(script_path, notebook_path):
    """将 Python 脚本转换为 notebook"""
    with open(script_path, 'r') as f:
        script_content = f.read()
    
    # 按行分割并创建代码单元格
    lines = script_content.split('\n')
    notebook = nbf.v4.new_notebook()
    
    current_cell = []
    for line in lines:
        if line.strip().startswith('#') and current_cell:
            # 遇到注释且当前有代码，创建代码单元格
            notebook.cells.append(nbf.v4.new_code_cell('\n'.join(current_cell)))
            current_cell = []
            # 创建 Markdown 单元格
            notebook.cells.append(nbf.v4.new_markdown_cell(line))
        else:
            current_cell.append(line)
    
    # 添加最后的代码单元格
    if current_cell:
        notebook.cells.append(nbf.v4.new_code_cell('\n'.join(current_cell)))
    
    nbf.write(notebook, notebook_path)
```

### 2. 创建教学 Notebook

```python
def create_tutorial_notebook(title, sections):
    """创建教学 notebook"""
    builder = NotebookBuilder(title)
    
    for section in sections:
        # 添加章节标题
        builder.add_markdown_cell(f"## {section['title']}\n\n{section['description']}")
        
        # 添加代码示例
        for example in section['examples']:
            builder.add_code_cell(example['code'])
            if example.get('output'):
                # 这里可以添加预期输出
                pass
    
    return builder
```

## 注意事项

1. **版本兼容性**: 使用 `as_version=4` 确保兼容性
2. **元数据设置**: 正确设置内核信息以确保 notebook 能正常运行
3. **输出格式**: 不同类型的输出有不同的格式要求
4. **文件路径**: 使用绝对路径或确保相对路径正确
5. **编码**: 确保文本内容使用正确的编码格式

## 相关资源

- [nbformat 官方文档](https://nbformat.readthedocs.io/)
- [Jupyter Notebook 格式规范](https://nbformat.readthedocs.io/en/latest/format_description.html)
- [nbconvert 工具](https://nbconvert.readthedocs.io/) - 用于 notebook 格式转换 