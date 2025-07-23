# Labkit

Labkit 是一个用于网络实验配置、可视化和自动化的 Python 工具库，支持命令行和 Jupyter Notebook 两种使用方式。

---

## 目录结构

```
labkit/               # Labkit 主代码库
  ├── cli/            # 命令行相关模块
  ├── generators/     # 配置生成器
  ├── jupyter/        # Jupyter 相关代码与文档
  │     ├── nbformat_examples.py
  │     ├── nbformat_guide.md
  │     ├── fix_chinese_fonts.py
  │     └── JUPYTER_README.md
  ├── models/         # 数据模型
  ├── visualization.py
  ├── ...
labkit.py             # Labkit CLI 入口脚本
requirements.txt      # 所有依赖（主依赖+开发+Jupyter）
docs/                 # 项目文档
README.md             # 项目说明
```

---

## 安装依赖

建议使用 Python 虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 命令行用法

Labkit 提供统一入口脚本 `labkit.py`：

```bash
python labkit.py cli <命令参数>
# 例如
python labkit.py cli init mylabdir
```

详细命令请见 `labkit/cli/` 或使用 `python labkit.py` 查看帮助。

---

## Jupyter Notebook 支持

Jupyter 相关代码和文档已全部迁移至 `labkit/jupyter/` 目录。

- 详细用法、可视化示例、实验剧本等请参考：
  - `labkit/jupyter/JUPYTER_README.md`
  - `labkit/jupyter/nbformat_examples.py`
  - `labkit/jupyter/nbformat_guide.md`
  - `labkit/jupyter/fix_chinese_fonts.py`

### 快速开始 Jupyter

```bash
# 启动 Jupyter Notebook
jupyter notebook
# 或
jupyter lab
```

---

## 贡献与支持

- 贡献建议、问题反馈请提交 Issue 或 PR
- 详细文档见 docs/
- Jupyter 相关问题见 labkit/jupyter/JUPYTER_README.md

---

**Happy Experimenting! 🧪**
