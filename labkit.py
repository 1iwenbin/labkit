#!/usr/bin/env python3
"""
Labkit CLI 入口脚本 (Python 版)
用法示例：
    python labkit.py cli <labkit命令参数>
"""
import sys
import subprocess

def cli_main(args):
    # 直接调用 labkit.cli.main 模块
    cmd = [sys.executable, "-m", "labkit.cli.main"] + args
    subprocess.run(cmd)

def print_help():
    print("Labkit CLI 脚本用法：")
    print(f"  python {sys.argv[0]} cli <命令参数>        # 执行 Labkit CLI 主命令")
    print(f"    例如: python {sys.argv[0]} cli init mylabdir")
    print(f"  请先激活虚拟环境: source .venv/bin/activate")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "cli":
        cli_main(sys.argv[2:])
    else:
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 