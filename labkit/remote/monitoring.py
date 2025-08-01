"""
系统监控模块

提供实时监控和日志分析功能。
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    load_average: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    network_rx: int = 0
    network_tx: int = 0
    uptime: str = ""
    processes: int = 0
    users: int = 0


class SystemMonitor:
    """系统监控类"""
    
    def __init__(self, manager):
        """
        初始化系统监控器
        
        Args:
            manager: RemoteManager 实例
        """
        self.manager = manager
        self.metrics_history: Dict[str, List[SystemMetrics]] = {}
        self.monitoring = False
    
    def get_cpu_usage(self, name: str) -> float:
        """
        获取CPU使用率
        
        Args:
            name: 服务器名称
            
        Returns:
            CPU使用率百分比
        """
        result = self.manager.execute(name, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1", hide=True)
        if result and result.ok:
            try:
                return float(result.stdout.strip())
            except ValueError:
                return 0.0
        return 0.0
    
    def get_memory_usage(self, name: str) -> float:
        """
        获取内存使用率
        
        Args:
            name: 服务器名称
            
        Returns:
            内存使用率百分比
        """
        result = self.manager.execute(name, "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'", hide=True)
        if result and result.ok:
            try:
                return float(result.stdout.strip())
            except ValueError:
                return 0.0
        return 0.0
    
    def get_disk_usage(self, name: str, path: str = "/") -> float:
        """
        获取磁盘使用率
        
        Args:
            name: 服务器名称
            path: 磁盘路径
            
        Returns:
            磁盘使用率百分比
        """
        result = self.manager.execute(name, f"df {path} | tail -1 | awk '{{print $5}}' | cut -d'%' -f1", hide=True)
        if result and result.ok:
            try:
                return float(result.stdout.strip())
            except ValueError:
                return 0.0
        return 0.0
    
    def get_load_average(self, name: str) -> Tuple[float, float, float]:
        """
        获取负载平均值
        
        Args:
            name: 服务器名称
            
        Returns:
            1分钟、5分钟、15分钟负载平均值
        """
        result = self.manager.execute(name, "uptime | awk -F'load average:' '{print $2}' | awk '{print $1, $2, $3}'", hide=True)
        if result and result.ok:
            try:
                parts = result.stdout.strip().split(',')
                if len(parts) == 3:
                    return (
                        float(parts[0].strip()),
                        float(parts[1].strip()),
                        float(parts[2].strip())
                    )
            except ValueError:
                pass
        return (0.0, 0.0, 0.0)
    
    def get_network_stats(self, name: str) -> Tuple[int, int]:
        """
        获取网络统计信息
        
        Args:
            name: 服务器名称
            
        Returns:
            (接收字节数, 发送字节数)
        """
        result = self.manager.execute(name, "cat /proc/net/dev | grep eth0 | awk '{print $2, $10}'", hide=True)
        if result and result.ok:
            try:
                parts = result.stdout.strip().split()
                if len(parts) == 2:
                    return (int(parts[0]), int(parts[1]))
            except ValueError:
                pass
        return (0, 0)
    
    def get_uptime(self, name: str) -> str:
        """
        获取系统运行时间
        
        Args:
            name: 服务器名称
            
        Returns:
            运行时间字符串
        """
        result = self.manager.execute(name, "uptime -p", hide=True)
        if result and result.ok:
            return result.stdout.strip()
        return ""
    
    def get_process_count(self, name: str) -> int:
        """
        获取进程数量
        
        Args:
            name: 服务器名称
            
        Returns:
            进程数量
        """
        result = self.manager.execute(name, "ps aux | wc -l", hide=True)
        if result and result.ok:
            try:
                return int(result.stdout.strip()) - 1  # 减去标题行
            except ValueError:
                pass
        return 0
    
    def get_user_count(self, name: str) -> int:
        """
        获取在线用户数量
        
        Args:
            name: 服务器名称
            
        Returns:
            在线用户数量
        """
        result = self.manager.execute(name, "who | wc -l", hide=True)
        if result and result.ok:
            try:
                return int(result.stdout.strip())
            except ValueError:
                pass
        return 0
    
    def collect_metrics(self, name: str) -> SystemMetrics:
        """
        收集系统指标
        
        Args:
            name: 服务器名称
            
        Returns:
            系统指标对象
        """
        metrics = SystemMetrics(timestamp=datetime.now())
        
        try:
            metrics.cpu_usage = self.get_cpu_usage(name)
            metrics.memory_usage = self.get_memory_usage(name)
            metrics.disk_usage = self.get_disk_usage(name)
            metrics.load_average = self.get_load_average(name)
            metrics.network_rx, metrics.network_tx = self.get_network_stats(name)
            metrics.uptime = self.get_uptime(name)
            metrics.processes = self.get_process_count(name)
            metrics.users = self.get_user_count(name)
        except Exception as e:
            console.print(f"❌ 收集指标失败 {name}: {e}")
        
        return metrics
    
    def start_monitoring(self, servers: List[str] = None, interval: int = 5, 
                        max_history: int = 100) -> None:
        """
        开始监控
        
        Args:
            servers: 服务器列表，None表示所有服务器
            interval: 监控间隔（秒）
            max_history: 最大历史记录数
        """
        if servers is None:
            servers = list(self.manager.servers.keys())
        
        self.monitoring = True
        
        try:
            while self.monitoring:
                for server in servers:
                    # 确保连接
                    if server not in self.manager.connections:
                        if not self.manager.connect(server):
                            continue
                    
                    # 收集指标
                    metrics = self.collect_metrics(server)
                    
                    # 保存到历史记录
                    if server not in self.metrics_history:
                        self.metrics_history[server] = []
                    
                    self.metrics_history[server].append(metrics)
                    
                    # 限制历史记录数量
                    if len(self.metrics_history[server]) > max_history:
                        self.metrics_history[server] = self.metrics_history[server][-max_history:]
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            console.print("\n🛑 监控已停止")
            self.monitoring = False
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        self.monitoring = False
    
    def display_metrics(self, servers: List[str] = None) -> None:
        """
        显示当前指标
        
        Args:
            servers: 服务器列表，None表示所有服务器
        """
        if servers is None:
            servers = list(self.manager.servers.keys())
        
        table = Table(title="系统指标")
        table.add_column("服务器", style="cyan")
        table.add_column("CPU%", style="red")
        table.add_column("内存%", style="yellow")
        table.add_column("磁盘%", style="green")
        table.add_column("负载", style="blue")
        table.add_column("进程", style="magenta")
        table.add_column("用户", style="white")
        
        for server in servers:
            if server not in self.metrics_history or not self.metrics_history[server]:
                table.add_row(server, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")
                continue
            
            metrics = self.metrics_history[server][-1]
            load_str = f"{metrics.load_average[0]:.2f}, {metrics.load_average[1]:.2f}, {metrics.load_average[2]:.2f}"
            
            table.add_row(
                server,
                f"{metrics.cpu_usage:.1f}%",
                f"{metrics.memory_usage:.1f}%",
                f"{metrics.disk_usage:.1f}%",
                load_str,
                str(metrics.processes),
                str(metrics.users)
            )
        
        console.print(table)
    
    def get_log_entries(self, name: str, log_file: str, lines: int = 100, 
                       grep_pattern: str = "") -> List[str]:
        """
        获取日志条目
        
        Args:
            name: 服务器名称
            log_file: 日志文件路径
            lines: 行数
            grep_pattern: 过滤模式
            
        Returns:
            日志条目列表
        """
        if grep_pattern:
            command = f"tail -n {lines} {log_file} | grep '{grep_pattern}'"
        else:
            command = f"tail -n {lines} {log_file}"
        
        result = self.manager.execute(name, command, hide=True)
        if result and result.ok:
            return result.stdout.strip().split('\n')
        return []
    
    def monitor_log_file(self, name: str, log_file: str, grep_pattern: str = "",
                        follow: bool = True) -> None:
        """
        监控日志文件
        
        Args:
            name: 服务器名称
            log_file: 日志文件路径
            grep_pattern: 过滤模式
            follow: 是否跟随新日志
        """
        if follow:
            if grep_pattern:
                command = f"tail -f {log_file} | grep '{grep_pattern}'"
            else:
                command = f"tail -f {log_file}"
        else:
            if grep_pattern:
                command = f"tail -n 50 {log_file} | grep '{grep_pattern}'"
            else:
                command = f"tail -n 50 {log_file}"
        
        try:
            console.print(f"📋 监控日志文件: {name}:{log_file}")
            if grep_pattern:
                console.print(f"🔍 过滤模式: {grep_pattern}")
            
            result = self.manager.execute(name, command)
            if result and result.ok:
                console.print(result.stdout)
            else:
                console.print(f"❌ 无法读取日志文件: {log_file}")
                
        except KeyboardInterrupt:
            console.print("\n🛑 日志监控已停止")
    
    def analyze_logs(self, name: str, log_file: str, hours: int = 24) -> Dict[str, Any]:
        """
        分析日志
        
        Args:
            name: 服务器名称
            log_file: 日志文件路径
            hours: 分析时间范围（小时）
            
        Returns:
            分析结果
        """
        # 获取指定时间范围内的日志
        since_time = datetime.now() - timedelta(hours=hours)
        since_str = since_time.strftime("%b %d %H:%M")
        
        command = f"sed -n '/{since_str}/,$p' {log_file}"
        result = self.manager.execute(name, command, hide=True)
        
        if not result or not result.ok:
            return {}
        
        logs = result.stdout.strip().split('\n')
        
        # 分析结果
        analysis = {
            'total_entries': len(logs),
            'error_count': 0,
            'warning_count': 0,
            'error_patterns': {},
            'hourly_distribution': {},
            'top_ips': {},
            'top_user_agents': {}
        }
        
        for log in logs:
            if not log.strip():
                continue
            
            # 统计错误和警告
            if 'ERROR' in log.upper():
                analysis['error_count'] += 1
            elif 'WARN' in log.upper():
                analysis['warning_count'] += 1
            
            # 按小时分布
            try:
                # 尝试提取时间信息（简化处理）
                if '[' in log and ']' in log:
                    time_part = log.split('[')[1].split(']')[0]
                    hour = time_part.split(':')[1] if ':' in time_part else '00'
                    analysis['hourly_distribution'][hour] = analysis['hourly_distribution'].get(hour, 0) + 1
            except:
                pass
        
        return analysis
    
    def export_metrics(self, filename: str = None) -> None:
        """
        导出指标数据
        
        Args:
            filename: 导出文件名
        """
        if filename is None:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {}
        for server, metrics_list in self.metrics_history.items():
            export_data[server] = []
            for metrics in metrics_list:
                export_data[server].append({
                    'timestamp': metrics.timestamp.isoformat(),
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'disk_usage': metrics.disk_usage,
                    'load_average': list(metrics.load_average),
                    'network_rx': metrics.network_rx,
                    'network_tx': metrics.network_tx,
                    'uptime': metrics.uptime,
                    'processes': metrics.processes,
                    'users': metrics.users
                })
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            console.print(f"✅ 指标数据已导出到: {filename}")
        except Exception as e:
            console.print(f"❌ 导出失败: {e}")
    
    def generate_report(self, servers: List[str] = None) -> None:
        """
        生成监控报告
        
        Args:
            servers: 服务器列表，None表示所有服务器
        """
        if servers is None:
            servers = list(self.manager.servers.keys())
        
        console.print("\n📊 系统监控报告")
        console.print("=" * 50)
        
        for server in servers:
            if server not in self.metrics_history or not self.metrics_history[server]:
                console.print(f"\n❌ {server}: 无可用数据")
                continue
            
            metrics_list = self.metrics_history[server]
            latest = metrics_list[-1]
            
            # 计算平均值
            avg_cpu = sum(m.cpu_usage for m in metrics_list) / len(metrics_list)
            avg_memory = sum(m.memory_usage for m in metrics_list) / len(metrics_list)
            avg_disk = sum(m.disk_usage for m in metrics_list) / len(metrics_list)
            
            # 找出最大值
            max_cpu = max(m.cpu_usage for m in metrics_list)
            max_memory = max(m.memory_usage for m in metrics_list)
            max_disk = max(m.disk_usage for m in metrics_list)
            
            panel = Panel(
                f"服务器: {server}\n"
                f"运行时间: {latest.uptime}\n"
                f"当前进程: {latest.processes}\n"
                f"在线用户: {latest.users}\n\n"
                f"CPU 使用率: {latest.cpu_usage:.1f}% (平均: {avg_cpu:.1f}%, 最大: {max_cpu:.1f}%)\n"
                f"内存使用率: {latest.memory_usage:.1f}% (平均: {avg_memory:.1f}%, 最大: {max_memory:.1f}%)\n"
                f"磁盘使用率: {latest.disk_usage:.1f}% (平均: {avg_disk:.1f}%, 最大: {max_disk:.1f}%)\n"
                f"负载平均值: {latest.load_average[0]:.2f}, {latest.load_average[1]:.2f}, {latest.load_average[2]:.2f}",
                title=f"📈 {server} 系统状态",
                border_style="blue"
            )
            
            console.print(panel) 