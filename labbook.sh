#!/bin/bash
# Labbook CLI 入口脚本
# 用法示例：
#   ./labbook.sh venv
#   ./labbook.sh install
#   ./labbook.sh cli <labbook命令参数>

set -e

VENV_DIR=".venv"
REQUIREMENTS="requirements.txt"

venv_create() {
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "[labbook] 未检测到虚拟环境，正在创建 $VENV_DIR ..."
        python3 -m venv "$VENV_DIR"
        echo "[labbook] 虚拟环境 $VENV_DIR 已创建"
    else
        echo "[labbook] 虚拟环境 $VENV_DIR 已存在"
    fi
    echo "[labbook] 如需激活请运行: source $VENV_DIR/bin/activate"
}

venv_install() {
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "[labbook] 未检测到虚拟环境，请先运行: ./labbook.sh venv"
        exit 1
    fi
    if [[ ! -f "$REQUIREMENTS" ]]; then
        echo "[labbook] 未找到 $REQUIREMENTS ，请先准备依赖文件。"
        exit 1
    fi
    echo "[labbook] 正在使用 $VENV_DIR 安装 $REQUIREMENTS ..."
    "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS"
    echo "[labbook] 依赖安装完成。要激活虚拟环境请运行: source $VENV_DIR/bin/activate"
}

cli_main() {
    shift # 移除 'cli'
    python -m labkit.cli.main "$@"
}

case "$1" in
    venv)
        venv_create
        ;;
    install)
        venv_install
        ;;
    cli)
        cli_main "$@"
        ;;
    *)
        echo "Labbook CLI 脚本用法："
        echo "  ./labbook.sh venv                  # 创建 .venv 虚拟环境（不激活、不安装依赖）"
        echo "  ./labbook.sh install               # 用 .venv 安装 requirements.txt 依赖（不激活）"
        echo "  ./labbook.sh cli <命令参数>        # 执行 Labbook CLI 主命令"
        echo "    例如: ./labbook.sh cli init mylabdir"
        echo "  激活虚拟环境请运行: source .venv/bin/activate"
        ;;
esac 