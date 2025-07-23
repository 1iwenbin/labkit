import typer
from pathlib import Path
from rich import print

app = typer.Typer()

@app.command()
def edit(path: str = typer.Argument(..., help="Labbook 项目目录路径")):
    """编辑 Labbook 项目"""
    root = Path(path)
    yaml_file = root / "labbook.yaml"
    if not yaml_file.exists():
        print(f"[red]目录 {path} 下未找到 labbook.yaml，不是有效的 Labbook 项目。[/red]")
        raise typer.Exit(1)
    print(f"[green]准备编辑 Labbook 项目: {path}[/green]") 