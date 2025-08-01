"""
远程管理器主类

提供基于 Fabric 的远程连接管理和基础操作功能。
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
from fabric import Connection
from fabric.runners import Result
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str
    user: str
    port: int = 22
    password: Optional[str] = None
    key_filename: Optional[str] = None
    connect_timeout: int = 10
    command_timeout: int = 300
    name: Optional[str] = None
    
    def __post_init__(self):
        if self.name is None:
            self.name = f"{self.user}@{self.host}:{self.port}"


class ConnectionManager:
    """连接管理器主类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化连接管理器
        
        Args:
            config_file: 服务器配置文件路径
        """
        self.servers: Dict[str, ServerConfig] = {}
        self.connections: Dict[str, Connection] = {}
        self.config_file = config_file or "servers.json"
        self._load_config()
    
    def _load_config(self):
        """加载服务器配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                    for name, config in configs.items():
                        # 移除可能存在的 name 字段，避免参数冲突
                        config_copy = config.copy()
                        config_copy.pop('name', None)
                        self.add_server(name, **config_copy)
                console.print(f"✅ 已加载 {len(self.servers)} 个服务器配置")
            except Exception as e:
                console.print(f"❌ 加载配置文件失败: {e}")
    
    def _save_config(self):
        """保存服务器配置"""
        configs = {}
        for name, server in self.servers.items():
            configs[name] = {
                'host': server.host,
                'user': server.user,
                'port': server.port,
                'password': server.password,
                'key_filename': server.key_filename,
                'connect_timeout': server.connect_timeout,
                'command_timeout': server.command_timeout,
                'name': server.name
            }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=2, ensure_ascii=False)
            console.print(f"✅ 配置已保存到 {self.config_file}")
        except Exception as e:
            console.print(f"❌ 保存配置文件失败: {e}")
    
    def add_server(self, name: str, **kwargs) -> None:
        """
        添加服务器配置
        
        Args:
            name: 服务器名称
            **kwargs: 服务器配置参数
        """
        server = ServerConfig(**kwargs)
        self.servers[name] = server
        console.print(f"✅ 已添加服务器: {name} ({server.name})")
        self._save_config()
    
    def remove_server(self, name: str) -> None:
        """
        移除服务器配置
        
        Args:
            name: 服务器名称
        """
        if name in self.servers:
            del self.servers[name]
            if name in self.connections:
                self.connections[name].close()
                del self.connections[name]
            console.print(f"✅ 已移除服务器: {name}")
            self._save_config()
        else:
            console.print(f"❌ 服务器 {name} 不存在")
    
    def connect(self, name: str) -> bool:
        """
        连接到指定服务器
        
        Args:
            name: 服务器名称
            
        Returns:
            连接是否成功
        """
        if name not in self.servers:
            console.print(f"❌ 服务器 {name} 不存在")
            return False
        
        server = self.servers[name]
        
        try:
            # 创建连接参数
            connect_kwargs = {}
            
            if server.password:
                connect_kwargs['password'] = server.password
            if server.key_filename:
                connect_kwargs['key_filename'] = server.key_filename
            
            # 创建连接
            conn = Connection(
                host=server.host,
                user=server.user,
                port=server.port,
                connect_kwargs=connect_kwargs
            )
            
            # 测试连接
            result = conn.run('echo "Connection test"', hide=True)
            if result.ok:
                self.connections[name] = conn
                console.print(f"✅ 已连接到服务器: {name}")
                return True
            else:
                console.print(f"❌ 连接测试失败: {name}")
                return False
                
        except Exception as e:
            console.print(f"❌ 连接失败 {name}: {e}")
            return False
    
    def disconnect(self, name: str) -> None:
        """
        断开指定服务器的连接
        
        Args:
            name: 服务器名称
        """
        if name in self.connections:
            self.connections[name].close()
            del self.connections[name]
            console.print(f"✅ 已断开连接: {name}")
        else:
            console.print(f"⚠️  服务器 {name} 未连接")
    
    def disconnect_all(self) -> None:
        """断开所有连接"""
        for name in list(self.connections.keys()):
            self.disconnect(name)
    
    def list_servers(self) -> None:
        """列出所有服务器"""
        if not self.servers:
            console.print("📝 暂无服务器配置")
            return
        
        table = Table(title="服务器列表")
        table.add_column("名称", style="cyan")
        table.add_column("连接信息", style="green")
        table.add_column("状态", style="yellow")
        table.add_column("端口", style="blue")
        
        for name, server in self.servers.items():
            status = "🟢 已连接" if name in self.connections else "🔴 未连接"
            table.add_row(name, server.name, status, str(server.port))
        
        console.print(table)
    
    def execute(self, name: str, command: str, hide: bool = False) -> Optional[Result]:
        """
        在指定服务器上执行命令
        
        Args:
            name: 服务器名称
            command: 要执行的命令
            hide: 是否隐藏输出
            
        Returns:
            执行结果
        """
        if name not in self.connections:
            if not self.connect(name):
                return None
        
        try:
            result = self.connections[name].run(command, hide=hide)
            return result
        except Exception as e:
            console.print(f"❌ 执行命令失败: {e}")
            return None
    
    def execute_stream(self, name: str, command: str) -> bool:
        """
        流式执行命令（实时输出）
        
        Args:
            name: 服务器名称
            command: 要执行的命令
            
        Returns:
            是否执行成功
        """
        if name not in self.connections:
            if not self.connect(name):
                return False
        
        try:
            console.print(f"🔄 在 {name} 上执行: {command}")
            console.print("─" * 50)
            
            # 使用 pty=True 来获取实时输出
            result = self.connections[name].run(command, pty=True, echo=True)
            
            console.print("─" * 50)
            if result.ok:
                console.print(f"✅ 命令执行完成")
            else:
                console.print(f"❌ 命令执行失败，退出码: {result.exited}")
            
            return result.ok
        except Exception as e:
            console.print(f"❌ 流式执行失败: {e}")
            return False
    
    def interactive_shell(self, name: str) -> bool:
        """
        启动交互式 shell 会话
        
        Args:
            name: 服务器名称
            
        Returns:
            是否成功启动
        """
        try:
            import readline
            import os
            
            # 设置历史文件
            history_file = os.path.expanduser(f"~/.labkit_history_{name}")
            
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
                    'ls', 'cd', 'pwd', 'cat', 'grep', 'find', 'ps', 'top', 'htop',
                    'vim', 'nano', 'less', 'more', 'head', 'tail', 'wc', 'sort',
                    'uniq', 'cut', 'awk', 'sed', 'tr', 'tee', 'chmod', 'chown',
                    'mkdir', 'rmdir', 'cp', 'mv', 'rm', 'ln', 'tar', 'gzip',
                    'ssh', 'scp', 'rsync', 'wget', 'curl', 'ping', 'netstat',
                    'ifconfig', 'ip', 'route', 'iptables', 'systemctl', 'service',
                    'journalctl', 'logrotate', 'cron', 'at', 'screen', 'tmux',
                    'git', 'svn', 'docker', 'kubectl', 'python', 'node', 'npm',
                    'java', 'maven', 'gradle', 'make', 'cmake', 'gcc', 'g++',
                    'exit', 'quit', 'clear', 'history', 'help'
                ]
                
                matches = [cmd for cmd in commands if cmd.startswith(text)]
                if state < len(matches):
                    return matches[state]
                else:
                    return None
            
            readline.set_completer(completer)
            
            console.print(f"🚀 启动增强交互式 shell 会话: {name}")
            console.print("💡 支持 Tab 补全和命令历史 (上下箭头键)")
            console.print("💡 输入 'exit' 或 'quit' 退出会话")
            console.print("💡 输入 'help' 查看帮助")
            console.print("💡 输入 'history' 查看命令历史")
            console.print("─" * 50)
            
            # 启动增强的交互式循环
            while True:
                try:
                    command = input(f"[{name}] $ ").strip()
                    
                    # 处理特殊命令
                    if command.lower() in ['exit', 'quit']:
                        break
                    elif command.lower() == 'help':
                        self._show_shell_help()
                        continue
                    elif command.lower() == 'history':
                        self._show_command_history()
                        continue
                    elif command.lower() == 'clear':
                        os.system('clear')
                        continue
                    elif not command:
                        continue
                    
                    # 执行远程命令
                    console.print(f"🔄 执行: {command}")
                    result = self.execute(name, command)
                    if result and result.ok:
                        if result.stdout.strip():
                            console.print(f"✅ 输出: {result.stdout.strip()}")
                    else:
                        console.print(f"❌ 命令执行失败")
                        
                except KeyboardInterrupt:
                    console.print("\n👋 会话已中断")
                    break
                except EOFError:
                    console.print("\n👋 会话已结束")
                    break
            
            # 保存历史记录
            try:
                readline.write_history_file(history_file)
            except Exception:
                pass
            
            console.print("─" * 50)
            console.print(f"✅ 会话已结束: {name}")
            return True
        except Exception as e:
            console.print(f"❌ 启动交互式会话失败: {e}")
            return False
    
    def _show_shell_help(self):
        """显示 shell 帮助信息"""
        help_text = """
Shell 帮助信息:
===============

基本命令:
  ls, cd, pwd, cat, grep, find, ps, top, htop
  vim, nano, less, more, head, tail, wc, sort
  cp, mv, rm, mkdir, rmdir, chmod, chown
  tar, gzip, wget, curl, ping, netstat

系统管理:
  systemctl, service, journalctl, logrotate
  cron, at, screen, tmux, docker, kubectl

开发工具:
  git, svn, python, node, npm, java
  maven, gradle, make, cmake, gcc, g++

Shell 功能:
  Tab 键: 命令补全
  上下箭头: 浏览命令历史
  Ctrl+C: 中断当前命令
  exit/quit: 退出会话
  help: 显示此帮助
  history: 显示命令历史
  clear: 清屏

提示: 使用 Tab 键可以自动补全命令名称
        """
        console.print(Panel(help_text, title="Shell 帮助", style="blue"))
    
    def _show_command_history(self):
        """显示命令历史"""
        try:
            import readline
            history_length = readline.get_current_history_length()
            console.print(f"📜 命令历史 (共 {history_length} 条):")
            console.print("─" * 30)
            
            for i in range(1, min(history_length + 1, 21)):  # 显示最近20条
                try:
                    command = readline.get_history_item(i)
                    if command:
                        console.print(f"{i:2d}: {command}")
                except Exception:
                    pass
                    
            console.print("─" * 30)
        except Exception as e:
            console.print(f"❌ 无法获取命令历史: {e}")
    
    def execute_all(self, command: str, hide: bool = False) -> Dict[str, Result]:
        """
        在所有连接的服务器上执行命令
        
        Args:
            command: 要执行的命令
            hide: 是否隐藏输出
            
        Returns:
            各服务器的执行结果
        """
        results = {}
        for name in self.servers.keys():
            result = self.execute(name, command, hide)
            if result:
                results[name] = result
        return results
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect_all() 