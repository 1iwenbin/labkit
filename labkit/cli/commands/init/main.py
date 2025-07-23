import typer
from pathlib import Path
from labkit.cli.utils import get_git_author, print_dir_tree
from labkit.cli.templates import LABBOOK_YAML_TMPL, TOPOLOGY_YAML_TMPL, PLAYBOOK_YAML_TMPL, README_TMPL
from rich import print

app = typer.Typer()

@app.command()
def init(
    path: str = typer.Argument(..., help="要初始化的文件路径")
):
    """初始化一个新的 Labbook 项目目录"""
    root = Path(path)
    if root.exists():
        print(f"[red]目录 {path} 已存在，无法初始化。[/red]")
        raise typer.Exit(1)
    # 创建目录结构
    root.mkdir(parents=True)
    (root / "network" / "mounts").mkdir(parents=True)
    for sub in ["events", "queries", "monitors", "scripts"]:
        (root / sub).mkdir(parents=True)
    # 自动获取项目名
    name = root.name
    author = get_git_author()
    (root / "labbook.yaml").write_text(LABBOOK_YAML_TMPL.format(name=name, author=author), encoding="utf-8")
    (root / "network" / "config.yaml").write_text(TOPOLOGY_YAML_TMPL, encoding="utf-8")
    (root / "playbook.yaml").write_text(PLAYBOOK_YAML_TMPL, encoding="utf-8")
    (root / "README.md").write_text(README_TMPL.format(name=name), encoding="utf-8")
    print(f"[green]✅ 成功创建 Labbook: {name}[/green]")
    print("[cyan]目录结构已生成：[/cyan]")
    print_dir_tree(root)
    print("\n[yellow]下一步建议:[/yellow]")
    print(f"1. cd {path}")
    print("2. labbook view topology  # 查看初始拓扑")
    print("3. labbook validate       # 验证初始配置的正确性") 