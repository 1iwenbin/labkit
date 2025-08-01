"""
远程命令执行模块

提供常用的系统命令和批量操作功能。
"""

import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from fabric.runners import Result

console = Console()


class RemoteCommands:
    """远程命令执行类"""
    
    def __init__(self, manager):
        """
        初始化命令执行器
        
        Args:
            manager: ConnectionManager 实例
        """
        self.manager = manager
    
    def get_system_info(self, name: str) -> Dict[str, str]:
        """
        获取系统信息
        
        Args:
            name: 服务器名称
            
        Returns:
            系统信息字典
        """
        info = {}
        
        # 获取操作系统信息
        result = self.manager.execute(name, "uname -a", hide=True)
        if result and result.ok:
            info['os'] = result.stdout.strip()
        
        # 获取内存信息
        result = self.manager.execute(name, "free -h", hide=True)
        if result and result.ok:
            info['memory'] = result.stdout.strip()
        
        # 获取磁盘信息
        result = self.manager.execute(name, "df -h", hide=True)
        if result and result.ok:
            info['disk'] = result.stdout.strip()
        
        # 获取CPU信息
        result = self.manager.execute(name, "lscpu | grep 'Model name'", hide=True)
        if result and result.ok:
            info['cpu'] = result.stdout.strip()
        
        # 获取负载信息
        result = self.manager.execute(name, "uptime", hide=True)
        if result and result.ok:
            info['load'] = result.stdout.strip()
        
        return info
    
    def get_process_info(self, name: str, pattern: str = "") -> str:
        """
        获取进程信息
        
        Args:
            name: 服务器名称
            pattern: 进程名称模式
            
        Returns:
            进程信息
        """
        if pattern:
            command = f"ps aux | grep '{pattern}' | grep -v grep"
        else:
            command = "ps aux --sort=-%cpu | head -20"
        
        result = self.manager.execute(name, command, hide=True)
        if result and result.ok:
            return result.stdout.strip()
        return ""
    
    def check_service_status(self, name: str, service: str) -> str:
        """
        检查服务状态
        
        Args:
            name: 服务器名称
            service: 服务名称
            
        Returns:
            服务状态
        """
        # 尝试使用 systemctl
        result = self.manager.execute(name, f"systemctl is-active {service}", hide=True)
        if result and result.ok:
            return result.stdout.strip()
        
        # 尝试使用 service 命令
        result = self.manager.execute(name, f"service {service} status", hide=True)
        if result and result.ok:
            return "active" if "running" in result.stdout.lower() else "inactive"
        
        return "unknown"
    
    def start_service(self, name: str, service: str) -> bool:
        """
        启动服务
        
        Args:
            name: 服务器名称
            service: 服务名称
            
        Returns:
            是否成功
        """
        # 尝试使用 systemctl
        result = self.manager.execute(name, f"sudo systemctl start {service}", hide=True)
        if result and result.ok:
            return True
        
        # 尝试使用 service 命令
        result = self.manager.execute(name, f"sudo service {service} start", hide=True)
        return result and result.ok
    
    def stop_service(self, name: str, service: str) -> bool:
        """
        停止服务
        
        Args:
            name: 服务器名称
            service: 服务名称
            
        Returns:
            是否成功
        """
        # 尝试使用 systemctl
        result = self.manager.execute(name, f"sudo systemctl stop {service}", hide=True)
        if result and result.ok:
            return True
        
        # 尝试使用 service 命令
        result = self.manager.execute(name, f"sudo service {service} stop", hide=True)
        return result and result.ok
    
    def restart_service(self, name: str, service: str) -> bool:
        """
        重启服务
        
        Args:
            name: 服务器名称
            service: 服务名称
            
        Returns:
            是否成功
        """
        # 尝试使用 systemctl
        result = self.manager.execute(name, f"sudo systemctl restart {service}", hide=True)
        if result and result.ok:
            return True
        
        # 尝试使用 service 命令
        result = self.manager.execute(name, f"sudo service {service} restart", hide=True)
        return result and result.ok
    
    def install_package(self, name: str, package: str, package_manager: str = "auto") -> bool:
        """
        安装软件包
        
        Args:
            name: 服务器名称
            package: 包名称
            package_manager: 包管理器 (apt, yum, dnf, auto)
            
        Returns:
            是否成功
        """
        if package_manager == "auto":
            # 自动检测包管理器
            result = self.manager.execute(name, "which apt", hide=True)
            if result and result.ok:
                package_manager = "apt"
            else:
                result = self.manager.execute(name, "which yum", hide=True)
                if result and result.ok:
                    package_manager = "yum"
                else:
                    result = self.manager.execute(name, "which dnf", hide=True)
                    if result and result.ok:
                        package_manager = "dnf"
                    else:
                        console.print(f"❌ 无法检测包管理器: {name}")
                        return False
        
        if package_manager == "apt":
            command = f"sudo apt update && sudo apt install -y {package}"
        elif package_manager == "yum":
            command = f"sudo yum install -y {package}"
        elif package_manager == "dnf":
            command = f"sudo dnf install -y {package}"
        else:
            console.print(f"❌ 不支持的包管理器: {package_manager}")
            return False
        
        result = self.manager.execute(name, command)
        return result and result.ok
    
    def update_system(self, name: str) -> bool:
        """
        更新系统
        
        Args:
            name: 服务器名称
            
        Returns:
            是否成功
        """
        # 检测包管理器并更新
        result = self.manager.execute(name, "which apt", hide=True)
        if result and result.ok:
            command = "sudo apt update && sudo apt upgrade -y"
        else:
            result = self.manager.execute(name, "which yum", hide=True)
            if result and result.ok:
                command = "sudo yum update -y"
            else:
                result = self.manager.execute(name, "which dnf", hide=True)
                if result and result.ok:
                    command = "sudo dnf update -y"
                else:
                    console.print(f"❌ 无法检测包管理器: {name}")
                    return False
        
        result = self.manager.execute(name, command)
        return result and result.ok
    
    def create_user(self, name: str, username: str, password: str = None, sudo: bool = False) -> bool:
        """
        创建用户
        
        Args:
            name: 服务器名称
            username: 用户名
            password: 密码（可选）
            sudo: 是否给予sudo权限
            
        Returns:
            是否成功
        """
        commands = []
        
        # 创建用户
        if password:
            commands.append(f"echo '{username}:{password}' | sudo chpasswd")
        else:
            commands.append(f"sudo useradd -m {username}")
        
        # 给予sudo权限
        if sudo:
            commands.append(f"sudo usermod -aG sudo {username}")
        
        for command in commands:
            result = self.manager.execute(name, command, hide=True)
            if not result or not result.ok:
                return False
        
        return True
    
    def delete_user(self, name: str, username: str, remove_home: bool = True) -> bool:
        """
        删除用户
        
        Args:
            name: 服务器名称
            username: 用户名
            remove_home: 是否删除家目录
            
        Returns:
            是否成功
        """
        if remove_home:
            command = f"sudo userdel -r {username}"
        else:
            command = f"sudo userdel {username}"
        
        result = self.manager.execute(name, command, hide=True)
        return result and result.ok
    
    def execute_script(self, name: str, script_path: str, args: str = "") -> bool:
        """
        执行脚本
        
        Args:
            name: 服务器名称
            script_path: 脚本路径
            args: 脚本参数
            
        Returns:
            是否成功
        """
        command = f"chmod +x {script_path} && {script_path} {args}".strip()
        result = self.manager.execute(name, command)
        return result and result.ok
    
    def batch_execute(self, command: str, servers: List[str] = None, 
                     show_progress: bool = True) -> Dict[str, Result]:
        """
        批量执行命令
        
        Args:
            command: 要执行的命令
            servers: 服务器列表，None表示所有服务器
            show_progress: 是否显示进度
            
        Returns:
            各服务器的执行结果
        """
        if servers is None:
            servers = list(self.manager.servers.keys())
        
        results = {}
        
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("批量执行命令...", total=len(servers))
                
                for server in servers:
                    progress.update(task, description=f"正在执行: {server}")
                    result = self.manager.execute(server, command)
                    if result:
                        results[server] = result
                    progress.advance(task)
        else:
            for server in servers:
                result = self.manager.execute(server, command)
                if result:
                    results[server] = result
        
        return results
    
    def monitor_servers(self, servers: List[str] = None, interval: int = 30) -> None:
        """
        监控服务器状态
        
        Args:
            servers: 服务器列表，None表示所有服务器
            interval: 监控间隔（秒）
        """
        if servers is None:
            servers = list(self.manager.servers.keys())
        
        try:
            while True:
                console.clear()
                console.print(f"🔄 服务器监控 - 间隔: {interval}秒")
                console.print("按 Ctrl+C 停止监控\n")
                
                table = Table(title="服务器状态")
                table.add_column("服务器", style="cyan")
                table.add_column("状态", style="yellow")
                table.add_column("负载", style="green")
                table.add_column("内存", style="blue")
                table.add_column("磁盘", style="magenta")
                
                for server in servers:
                    # 检查连接状态
                    if server not in self.manager.connections:
                        if not self.manager.connect(server):
                            table.add_row(server, "🔴 连接失败", "N/A", "N/A", "N/A")
                            continue
                    
                    # 获取系统信息
                    try:
                        # 获取负载
                        result = self.manager.execute(server, "uptime | awk '{print $10}'", hide=True)
                        load = result.stdout.strip() if result and result.ok else "N/A"
                        
                        # 获取内存使用率
                        result = self.manager.execute(server, "free | grep Mem | awk '{printf \"%.1f%%\", $3/$2 * 100.0}'", hide=True)
                        memory = result.stdout.strip() if result and result.ok else "N/A"
                        
                        # 获取磁盘使用率
                        result = self.manager.execute(server, "df / | tail -1 | awk '{print $5}'", hide=True)
                        disk = result.stdout.strip() if result and result.ok else "N/A"
                        
                        table.add_row(server, "🟢 在线", load, memory, disk)
                        
                    except Exception as e:
                        table.add_row(server, f"🔴 错误: {e}", "N/A", "N/A", "N/A")
                
                console.print(table)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            console.print("\n🛑 监控已停止") 