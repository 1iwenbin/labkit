#!/usr/bin/env python3
"""
Labkit 远程服务器管理工具

基于 labkit.remote 库的命令行管理工具，提供：
- 服务器配置管理
- 远程命令执行
- 文件传输操作
- 系统监控
- 批量操作
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union


from .connection import ConnectionManager
from .commands import RemoteCommands
from .file_ops import FileOperations
from .monitoring import SystemMonitor

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class RemoteManager:
    """远程管理器主类 - 规范化版本"""
    
    def __init__(self, config_file: Optional[str] = None, enable_ui: bool = True):
        """
        初始化远程管理器
        
        Args:
            config_file: 服务器配置文件路径
            enable_ui: 是否启用UI输出，如果为False则只返回数据不显示界面
        """
        self.manager = ConnectionManager(config_file=config_file)
        self.commands = RemoteCommands(self.manager)
        self.file_ops = FileOperations(self.manager)
        self.monitor = SystemMonitor(self.manager)
        self.enable_ui = enable_ui
    
    # ==================== 服务器管理方法 ====================
    
    def add_server(self, name: str, host: str, user: str, port: int = 22, 
                   password: Optional[str] = None, key_filename: Optional[str] = None) -> bool:
        """
        添加服务器
        
        Args:
            name: 服务器名称
            host: 主机地址
            user: 用户名
            port: 端口号
            password: 密码
            key_filename: 私钥文件路径
            
        Returns:
            bool: 是否添加成功
        """
        try:
            config = {
                'name': name,
                'host': host,
                'user': user,
                'port': port,
                'password': password,
                'key_filename': key_filename
            }
            
            # 移除 None 值
            config = {k: v for k, v in config.items() if v is not None}
            
            self.manager.add_server(**config)
            
            if self.enable_ui:
                console.print(f"✅ 服务器 {name} 添加成功")
            
            return True
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 添加服务器失败: {e}")
            return False
    
    def remove_server(self, name: str) -> bool:
        """
        删除服务器
        
        Args:
            name: 服务器名称
            
        Returns:
            bool: 是否删除成功
        """
        try:
            self.manager.remove_server(name)
            
            if self.enable_ui:
                console.print(f"✅ 已删除服务器 {name}")
            
            return True
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 删除服务器失败: {e}")
            return False
    
    def list_servers(self) -> Dict[str, Any]:
        """
        列出所有服务器
        
        Returns:
            Dict[str, Any]: 服务器信息字典
        """
        servers_info = {}
        
        for name, server in self.manager.servers.items():
            status = "connected" if name in self.manager.connections else "disconnected"
            servers_info[name] = {
                'name': server.name,
                'host': server.host,
                'user': server.user,
                'port': server.port,
                'status': status
            }
        
        if self.enable_ui:
            if not servers_info:
                console.print("📝 暂无配置的服务器")
            else:
                table = Table(title="服务器列表")
                table.add_column("名称", style="cyan")
                table.add_column("连接信息", style="green")
                table.add_column("状态", style="yellow")
                
                for name, info in servers_info.items():
                    status_icon = "🟢 已连接" if info['status'] == "connected" else "🔴 未连接"
                    table.add_row(name, info['name'], status_icon)
                
                console.print(table)
        
        return servers_info
    
    def connect_server(self, name: str) -> bool:
        """
        连接到服务器
        
        Args:
            name: 服务器名称
            
        Returns:
            bool: 是否连接成功
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        try:
            if self.enable_ui:
                with console.status(f"正在连接到 {name}..."):
                    success = self.manager.connect(name)
            else:
                success = self.manager.connect(name)
            
            if success:
                if self.enable_ui:
                    console.print(f"✅ 成功连接到 {name}")
                return True
            else:
                if self.enable_ui:
                    console.print(f"❌ 连接 {name} 失败")
                return False
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 连接失败: {e}")
            return False
    
    def disconnect_server(self, name: str) -> bool:
        """
        断开服务器连接
        
        Args:
            name: 服务器名称
            
        Returns:
            bool: 是否断开成功
        """
        try:
            self.manager.disconnect(name)
            
            if self.enable_ui:
                console.print(f"✅ 已断开 {name} 的连接")
            
            return True
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 断开连接失败: {e}")
            return False
    
    # ==================== 命令执行方法 ====================
    
    def execute_command(self, name: str, command: str) -> Optional[Dict[str, Any]]:
        """
        在指定服务器执行命令
        
        Args:
            name: 服务器名称
            command: 要执行的命令
            
        Returns:
            Optional[Dict[str, Any]]: 执行结果，包含stdout、stderr、return_code等
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return None
        
        if name not in self.manager.connections:
            if not self.connect_server(name):
                return None
        
        try:
            if self.enable_ui:
                with console.status(f"在 {name} 执行命令..."):
                    result = self.manager.execute(name, command)
            else:
                result = self.manager.execute(name, command)
            
            if result:
                if self.enable_ui:
                    if result.ok:
                        console.print(f"✅ 命令执行成功:")
                        console.print(f"[bold green]{result.stdout}[/bold green]")
                        if result.stderr:
                            console.print(f"[yellow]警告: {result.stderr}[/yellow]")
                    else:
                        console.print(f"❌ 命令执行失败:")
                        console.print(f"[red]{result.stderr}[/red]")
                
                return {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.return_code,
                    'success': result.ok
                }
            else:
                if self.enable_ui:
                    console.print("❌ 命令执行失败")
                return None
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 执行命令失败: {e}")
            return None
    
    def execute_stream_command(self, name: str, command: str) -> bool:
        """
        流式执行命令（实时输出）
        
        Args:
            name: 服务器名称
            command: 要执行的命令
            
        Returns:
            bool: 是否执行成功
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        try:
            success = self.manager.execute_stream(name, command)
            if not success and self.enable_ui:
                console.print(f"❌ 流式执行失败")
            return success
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 流式执行失败: {e}")
            return False
    

    

    
    # ==================== 系统信息方法 ====================
    
    def get_system_info(self, name: str) -> Optional[Dict[str, str]]:
        """
        获取系统信息
        
        Args:
            name: 服务器名称
            
        Returns:
            Optional[Dict[str, str]]: 系统信息字典
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return None
        
        if name not in self.manager.connections:
            if not self.connect_server(name):
                return None
        
        try:
            info = self.commands.get_system_info(name)
            
            if self.enable_ui:
                console.print(f"\n📊 {name} 系统信息")
                console.print("=" * 60)
                
                # 操作系统信息
                if 'os' in info:
                    os_info = info['os']
                    console.print(f"🖥️  操作系统: {os_info.get('system', 'N/A')} {os_info.get('kernel', 'N/A')} ({os_info.get('architecture', 'N/A')})")
                
                # CPU信息
                if 'cpu' in info:
                    cpu_info = info['cpu']
                    console.print(f"🔧 CPU: {cpu_info.get('Model name', 'N/A')}")
                    console.print(f"   核心数: {cpu_info.get('CPU(s)', 'N/A')} | 架构: {cpu_info.get('Architecture', 'N/A')}")
                
                # 内存信息
                if 'memory' in info:
                    mem_info = info['memory']
                    console.print(f"💾 内存: {mem_info.get('total', 'N/A')} | 已用: {mem_info.get('used', 'N/A')} | 可用: {mem_info.get('available', 'N/A')}")
                
                # 负载信息
                if 'load' in info:
                    load_info = info['load']
                    console.print(f"📈 负载: 1分钟 {load_info.get('1min', 'N/A')} | 5分钟 {load_info.get('5min', 'N/A')} | 15分钟 {load_info.get('15min', 'N/A')}")
                
                # 磁盘信息
                if 'disk' in info:
                    console.print(f"💿 磁盘:")
                    for disk in info['disk'][:3]:  # 只显示前3个磁盘
                        console.print(f"   {disk['device']} ({disk['filesystem']}) {disk['size']} 已用{disk['use_percent']} 挂载{disk['mount_point']}")
                
                # 网络信息
                if 'network' in info:
                    console.print(f"🌐 网络:")
                    for net in info['network']:
                        if net['state'] == 'UP':
                            console.print(f"   {net['interface']}: {net['address']}")
                
                # 系统时间
                if 'datetime' in info:
                    console.print(f"🕐 时间: {info['datetime']}")
                
                console.print("=" * 60)
            
            return info
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 获取系统信息失败: {e}")
            return None
    

    

    

    
    # ==================== 文件操作方法 ====================
    
    def upload_file(self, name: str, local_path: str, remote_path: str) -> bool:
        """
        上传文件
        
        Args:
            name: 服务器名称
            local_path: 本地文件路径
            remote_path: 远程文件路径
            
        Returns:
            bool: 是否上传成功
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        if name not in self.manager.connections:
            if not self.connect_server(name):
                return False
        
        try:
            if self.enable_ui:
                with console.status(f"正在上传文件到 {name}..."):
                    success = self.file_ops.upload_file(name, local_path, remote_path)
            else:
                success = self.file_ops.upload_file(name, local_path, remote_path)
            
            if success:
                if self.enable_ui:
                    console.print(f"✅ 文件上传成功: {local_path} -> {remote_path}")
                return True
            else:
                if self.enable_ui:
                    console.print(f"❌ 文件上传失败")
                return False
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 文件上传失败: {e}")
            return False
    
    def download_file(self, name: str, remote_path: str, local_path: str) -> bool:
        """
        下载文件
        
        Args:
            name: 服务器名称
            remote_path: 远程文件路径
            local_path: 本地文件路径
            
        Returns:
            bool: 是否下载成功
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        if name not in self.manager.connections:
            if not self.connect_server(name):
                return False
        
        try:
            if self.enable_ui:
                with console.status(f"正在从 {name} 下载文件..."):
                    success = self.file_ops.download_file(name, remote_path, local_path)
            else:
                success = self.file_ops.download_file(name, remote_path, local_path)
            
            if success:
                if self.enable_ui:
                    console.print(f"✅ 文件下载成功: {remote_path} -> {local_path}")
                return True
            else:
                if self.enable_ui:
                    console.print(f"❌ 文件下载失败")
                return False
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 文件下载失败: {e}")
            return False
    
    def download_directory(self, name: str, remote_dir: str, local_dir: str) -> bool:
        """
        下载目录
        
        Args:
            name: 服务器名称
            remote_dir: 远程目录路径
            local_dir: 本地目录路径
            
        Returns:
            bool: 是否下载成功
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        if name not in self.manager.connections:
            if not self.connect_server(name):
                return False
        
        try:
            if self.enable_ui:
                with console.status(f"正在从 {name} 下载目录..."):
                    success = self.file_ops.download_directory(name, remote_dir, local_dir)
            else:
                success = self.file_ops.download_directory(name, remote_dir, local_dir)
            
            if success:
                if self.enable_ui:
                    console.print(f"✅ 目录下载成功: {remote_dir} -> {local_dir}")
                return True
            else:
                if self.enable_ui:
                    console.print(f"❌ 目录下载失败")
                return False
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 目录下载失败: {e}")
            return False
    
    def upload_directory(self, name: str, local_dir: str, remote_dir: str) -> bool:
        """
        上传目录到远程服务器
        
        Args:
            name: 服务器名称
            local_dir: 本地目录路径
            remote_dir: 远程目录路径
            
        Returns:
            bool: 是否上传成功
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        if name not in self.manager.connections:
            if not self.connect_server(name):
                return False
        
        try:
            if self.enable_ui:
                with console.status(f"正在上传目录到 {name}..."):
                    success = self.file_ops.upload_directory(name, local_dir, remote_dir)
            else:
                success = self.file_ops.upload_directory(name, local_dir, remote_dir)
            
            if success:
                if self.enable_ui:
                    console.print(f"✅ 目录上传成功: {local_dir} -> {remote_dir}")
                return True
            else:
                if self.enable_ui:
                    console.print(f"❌ 目录上传失败")
                return False
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 目录上传失败: {e}")
            return False
    
    def sync_directory(self, name: str, remote_dir: str, local_dir: str) -> bool:
        """
        同步目录（从远程下载到本地）
        
        Args:
            name: 服务器名称
            remote_dir: 远程目录路径
            local_dir: 本地目录路径
            
        Returns:
            bool: 是否同步成功
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        if name not in self.manager.connections:
            if not self.connect_server(name):
                return False
        
        try:
            if self.enable_ui:
                with console.status(f"正在从 {name} 同步目录..."):
                    success = self.file_ops.download_directory(name, remote_dir, local_dir)
            else:
                success = self.file_ops.download_directory(name, remote_dir, local_dir)
            
            if success:
                if self.enable_ui:
                    console.print(f"✅ 目录同步成功: {remote_dir} -> {local_dir}")
                return True
            else:
                if self.enable_ui:
                    console.print(f"❌ 目录同步失败")
                return False
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 目录同步失败: {e}")
            return False
    
    def upload_directory(self, name: str, local_dir: str, remote_dir: str) -> bool:
        """
        上传目录到远程服务器
        
        Args:
            name: 服务器名称
            local_dir: 本地目录路径
            remote_dir: 远程目录路径
            
        Returns:
            bool: 是否上传成功
        """
        if name not in self.manager.servers:
            if self.enable_ui:
                console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        if name not in self.manager.connections:
            if not self.connect_server(name):
                return False
        
        try:
            if self.enable_ui:
                with console.status(f"正在上传目录到 {name}..."):
                    success = self.file_ops.upload_directory(name, local_dir, remote_dir)
            else:
                success = self.file_ops.upload_directory(name, local_dir, remote_dir)
            
            if success:
                if self.enable_ui:
                    console.print(f"✅ 目录上传成功: {local_dir} -> {remote_dir}")
                return True
            else:
                if self.enable_ui:
                    console.print(f"❌ 目录上传失败")
                return False
        except Exception as e:
            if self.enable_ui:
                console.print(f"❌ 目录上传失败: {e}")
            return False
    

    

    
    # ==================== UI 相关方法 ====================
    
    def show_banner(self):
        """显示欢迎横幅"""
        if not self.enable_ui:
            return
            
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Labkit 远程服务器管理工具                    ║
║                                                              ║
║  提供服务器配置、远程命令执行、文件传输、系统监控等功能          ║
╚══════════════════════════════════════════════════════════════╝
        """
        console.print(Panel(banner, style="bold blue"))
    
    def show_help(self):
        """显示帮助信息"""
        if not self.enable_ui:
            return
            
        help_text = """
可用命令:

服务器管理:
  list                    - 列出所有服务器
  add <name> <host> <user> [options] - 添加服务器
  remove <name>          - 删除服务器
  connect <name>         - 连接到服务器
  disconnect <name>      - 断开服务器连接

命令执行:
  exec <name> <command>  - 在指定服务器执行命令
  stream <name> <command> - 流式执行命令（实时输出）
  info <name>           - 获取服务器系统信息



文件操作:
  upload <name> <local> <remote> - 上传文件
  download <name> <remote> <local> - 下载文件
  sync <name> <remote_dir> <local_dir> - 同步目录（从远程下载到本地）
  push <name> <local_dir> <remote_dir> - 推送目录（从本地上传到远程）



交互功能:
  help                   - 显示此帮助信息
  history                - 显示命令历史
  clear                  - 清屏
  exit/quit              - 退出程序

增强功能:
  Tab 键                 - 命令补全
  上下箭头键             - 浏览命令历史
  Ctrl+C                 - 中断当前操作

示例:
  add web-server 192.168.1.100 admin
  connect web-server
  exec web-server "uname -a"
  stream web-server "tail -f /var/log/syslog"
  sync web-server /remote/dir/ /local/dir/
  push web-server /local/dir/ /remote/dir/

提示: 使用 Tab 键可以自动补全命令和服务器名称
        """
        console.print(Panel(help_text, title="帮助信息", style="green"))
    
    def add_server_interactive(self) -> bool:
        """交互式添加服务器"""
        if not self.enable_ui:
            return False
            
        console.print("\n[bold cyan]添加新服务器[/bold cyan]")
        
        name = Prompt.ask("服务器名称")
        host = Prompt.ask("主机地址")
        user = Prompt.ask("用户名")
        port = Prompt.ask("端口", default="22")
        
        auth_method = Prompt.ask(
            "认证方式",
            choices=["password", "key"],
            default="password"
        )
        
        if auth_method == "password":
            password = Prompt.ask("密码", password=True)
            key_filename = None
        else:
            password = None
            key_filename = Prompt.ask("私钥文件路径")
        
        return self.add_server(name, host, user, int(port), password, key_filename)
    
    def add_server_from_args(self, args) -> bool:
        """从命令行参数添加服务器"""
        return self.add_server(
            name=args.name,
            host=args.host,
            user=args.user,
            port=args.port or 22,
            password=args.password,
            key_filename=args.key_file
        )
    
    def interactive_mode(self):
        """增强交互模式 - 支持 Tab 补全和命令历史"""
        if not self.enable_ui:
            return
            
        try:
            import readline
            import os
            
            # 设置历史文件
            history_file = os.path.expanduser("~/.labkit_interactive_history")
            
            # 加载历史记录
            try:
                readline.read_history_file(history_file)
            except FileNotFoundError:
                pass
            
            # 设置历史文件大小
            readline.set_history_length(1000)
            
            # 设置 Tab 补全
            readline.parse_and_bind("tab: complete")
            
            # 定义补全函数
            def completer(text, state):
                commands = [
                    # 基本命令
                    'help', 'list', 'add', 'exit', 'quit', 'clear', 'history',
                    # 连接管理
                    'connect', 'disconnect',
                    # 命令执行
                    'exec', 'stream', 'shell', 'batch',
                    # 系统信息
                    'info', 'ps',
                    # 服务管理
                    'service',
                    # 文件操作
                    'upload', 'download',
                    # 监控
                    'monitor',
                    # 服务器管理
                    'remove'
                ]
                
                # 获取当前可用的服务器名称
                server_names = list(self.manager.servers.keys())
                
                # 获取当前输入的行
                line = readline.get_line_buffer()
                parts = line.split()
                
                # 如果只有一个词，补全命令
                if len(parts) <= 1:
                    matches = [cmd for cmd in commands if cmd.startswith(text)]
                # 如果是服务器相关的命令，补全服务器名称
                elif len(parts) >= 2 and parts[0] in ['connect', 'disconnect', 'exec', 'stream', 'shell', 'info', 'ps', 'service', 'upload', 'download', 'remove']:
                    matches = [server for server in server_names if server.startswith(text)]
                # 如果是 service 命令，补全服务名称
                elif len(parts) >= 3 and parts[0] == 'service':
                    service_actions = ['start', 'stop', 'restart', 'status', 'enable', 'disable']
                    matches = [action for action in service_actions if action.startswith(text)]
                else:
                    matches = []
                
                if state < len(matches):
                    return matches[state]
                else:
                    return None
            
            readline.set_completer(completer)
            
        except ImportError:
            console.print("⚠️  readline 模块不可用，将使用基本交互模式")
        
        self.show_banner()
        self.show_help()
        
        console.print("💡 提示: 支持 Tab 补全和命令历史 (上下箭头键)")
        console.print("💡 输入 'help' 查看帮助，'history' 查看命令历史")
        
        while True:
            try:
                # 使用 input 而不是 Prompt.ask 来支持 readline
                command = input("\nlabkit> ").strip()
                
                if not command:
                    continue
                
                # 处理特殊命令
                if command in ['exit', 'quit']:
                    console.print("👋 再见!")
                    break
                
                if command == 'help':
                    self.show_help()
                    continue
                
                if command == 'clear':
                    os.system('clear')
                    self.show_banner()
                    continue
                
                if command == 'history':
                    self._show_interactive_history()
                    continue
                
                if command == 'list':
                    self.list_servers()
                    continue
                
                if command == 'add':
                    self.add_server_interactive()
                    continue
                
                # 解析其他命令
                parts = command.split()
                if len(parts) < 2:
                    console.print("❌ 命令格式错误，输入 'help' 查看帮助")
                    continue
                
                cmd, *args = parts
                
                if cmd == 'connect' and len(args) >= 1:
                    self.connect_server(args[0])
                elif cmd == 'disconnect' and len(args) >= 1:
                    self.disconnect_server(args[0])
                elif cmd == 'exec' and len(args) >= 2:
                    self.execute_command(args[0], ' '.join(args[1:]))
                elif cmd == 'stream' and len(args) >= 2:
                    self.execute_stream_command(args[0], ' '.join(args[1:]))
                elif cmd == 'info' and len(args) >= 1:
                    self.get_system_info(args[0])
                elif cmd == 'upload' and len(args) >= 3:
                    self.upload_file(args[0], args[1], args[2])
                elif cmd == 'download' and len(args) >= 3:
                    self.download_file(args[0], args[1], args[2])
                elif cmd == 'sync' and len(args) >= 3:
                    # 从远程同步到本地
                    remote_dir = args[1].rstrip('/')
                    local_dir = args[2].rstrip('/')
                    self.sync_directory(args[0], remote_dir, local_dir)
                elif cmd == 'push' and len(args) >= 3:
                    # 从本地上传到远程
                    local_dir = args[1].rstrip('/')
                    remote_dir = args[2].rstrip('/')
                    self.upload_directory(args[0], local_dir, remote_dir)
                elif cmd == 'remove' and len(args) >= 1:
                    if Confirm.ask(f"确定要删除服务器 {args[0]} 吗?"):
                        self.remove_server(args[0])
                else:
                    console.print("❌ 未知命令，输入 'help' 查看帮助")
                    
            except KeyboardInterrupt:
                console.print("\n👋 再见!")
                break
            except Exception as e:
                console.print(f"❌ 错误: {e}")
        
        # 保存历史记录
        try:
            readline.write_history_file(history_file)
        except Exception:
            pass
    
    def _show_interactive_history(self):
        """显示交互模式命令历史"""
        if not self.enable_ui:
            return
            
        try:
            import readline
            history_length = readline.get_current_history_length()
            console.print(f"📜 命令历史 (共 {history_length} 条):")
            console.print("─" * 40)
            
            for i in range(1, min(history_length + 1, 21)):  # 显示最近20条
                try:
                    command = readline.get_history_item(i)
                    if command:
                        console.print(f"{i:2d}: {command}")
                except Exception:
                    pass
                    
            console.print("─" * 40)
        except Exception as e:
            console.print(f"❌ 无法获取命令历史: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Labkit 远程服务器管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                           # 启动交互模式
  %(prog)s add web-server 192.168.1.100 admin  # 添加服务器
  %(prog)s exec web-server "uname -a"           # 执行命令
  %(prog)s batch "echo 'Hello'"                 # 批量执行
  %(prog)s monitor web-server,db-server        # 监控服务器
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加服务器命令
    add_parser = subparsers.add_parser('add', help='添加服务器')
    add_parser.add_argument('name', help='服务器名称')
    add_parser.add_argument('host', help='主机地址')
    add_parser.add_argument('user', help='用户名')
    add_parser.add_argument('--port', type=int, default=22, help='端口 (默认: 22)')
    add_parser.add_argument('--password', help='密码')
    add_parser.add_argument('--key-file', help='私钥文件路径')
    
    # 执行命令
    exec_parser = subparsers.add_parser('exec', help='执行命令')
    exec_parser.add_argument('server', help='服务器名称')
    exec_parser.add_argument('cmd', help='要执行的命令')
    
    # 流式执行命令
    stream_parser = subparsers.add_parser('stream', help='流式执行命令（实时输出）')
    stream_parser.add_argument('server', help='服务器名称')
    stream_parser.add_argument('cmd', help='要执行的命令')
    
    # 获取系统信息
    info_parser = subparsers.add_parser('info', help='获取系统信息')
    info_parser.add_argument('server', help='服务器名称')
    


    
    # 文件操作
    upload_parser = subparsers.add_parser('upload', help='上传文件')
    upload_parser.add_argument('server', help='服务器名称')
    upload_parser.add_argument('local', help='本地文件路径')
    upload_parser.add_argument('remote', help='远程文件路径')
    
    download_parser = subparsers.add_parser('download', help='下载文件')
    download_parser.add_argument('server', help='服务器名称')
    download_parser.add_argument('remote', help='远程文件路径')
    download_parser.add_argument('local', help='本地文件路径')
    
    # 列出服务器
    subparsers.add_parser('list', help='列出所有服务器')
    
    # 删除服务器
    remove_parser = subparsers.add_parser('remove', help='删除服务器')
    remove_parser.add_argument('name', help='服务器名称')
    
    args = parser.parse_args()
    
    # 创建远程管理器
    manager = RemoteManager()
    
    # 如果没有指定命令，启动交互模式
    if not args.command:
        manager.interactive_mode()
        return
    
    # 处理命令行参数
    try:
        if args.command == 'add':
            manager.add_server_from_args(args)
        elif args.command == 'list':
            manager.list_servers()
        elif args.command == 'exec':
            manager.execute_command(args.server, args.cmd)
        elif args.command == 'stream':
            manager.execute_stream_command(args.server, args.cmd)
        elif args.command == 'info':
            manager.get_system_info(args.server)
        elif args.command == 'upload':
            manager.upload_file(args.server, args.local, args.remote)
        elif args.command == 'download':
            manager.download_file(args.server, args.remote, args.local)
        elif args.command == 'remove':
            if Confirm.ask(f"确定要删除服务器 {args.name} 吗?"):
                manager.remove_server(args.name)
    
    except KeyboardInterrupt:
        console.print("\n👋 再见!")
    except Exception as e:
        console.print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
