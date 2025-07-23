import subprocess
from pathlib import Path
from rich.tree import Tree
from rich import print

def get_git_author():
    try:
        return subprocess.check_output(['git', 'config', 'user.name']).decode().strip()
    except Exception:
        return ""

def print_dir_tree(root: Path):
    tree = Tree(str(root))
    def add_dir(node, path):
        for p in sorted(path.iterdir()):
            if p.is_dir():
                child = node.add(f"[bold blue]{p.name}/[/bold blue]")
                add_dir(child, p)
            else:
                node.add(f"{p.name}")
    add_dir(tree, root)
    print(tree) 