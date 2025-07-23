import typer
from .tui import tui
from .node import node
from .link import link

app = typer.Typer()

@app.command()
def tui():
    """进入交互式 TUI 编辑器（占位实现）"""
    tui()

@app.command()
def node(id: str, image: str = typer.Option(None, help="新镜像")):
    """精确编辑 node（占位实现）"""
    node(id, image)

@app.command()
def link(id: str, latency: str = typer.Option(None, help="新延迟")):
    """精确编辑 link（占位实现）"""
    link(id, latency) 