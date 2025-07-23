import typer
from rich import print

app = typer.Typer()

@app.command()
def run(dry_run: bool = typer.Option(False, "--dry-run", help="预演执行流程"), output_dir: str = typer.Option(None, "--output-dir", help="结果输出目录")):
    """运行实验（占位实现）"""
    print("[yellow]Labbook run 命令尚未实现。[/yellow]") 