#!/usr/bin/env python3
"""
LabGrid 资源管理器

管理服务器资源分配、负载均衡和监控
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .types import (
    ServerConfig, 
    ServerStatus, 
    ServerInfo,
    FrameworkConfig
)
from .labx import LabX


@dataclass
class ResourceMetrics:
    """资源指标数据类"""
    timestamp: datetime
    cpu_usage: float  # CPU使用率 (0.0-1.0)
    memory_usage: float  # 内存使用率 (0.0-1.0)
    disk_usage: float  # 磁盘使用率 (0.0-1.0)
    network_in: float  # 网络入流量 (MB/s)
    network_out: float  # 网络出流量 (MB/s)
    load_average: float  # 系统负载平均值


class ResourceManager:
    """
    资源管理器
    
    负责服务器资源分配、负载均衡和监控
    """
    
    def __init__(self, labx: LabX, framework_config: FrameworkConfig):
        """
        初始化资源管理器
        
        Args:
            labx: LabX 实例
            framework_config: 框架配置
        """
        self.labx = labx
        self.framework_config = framework_config
        self.logger = logging.getLogger(__name__)
        
        # 服务器资源信息
        self.server_resources: Dict[str, ServerInfo] = {}
        
        # 资源指标历史
        self.resource_history: Dict[str, List[ResourceMetrics]] = {}
        
        # 资源分配策略
        self.allocation_strategy = "round_robin"  # round_robin, least_loaded, priority_based
        
        # 线程安全
        self.lock = threading.RLock()
        
        # 监控线程
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.monitoring_interval = 30  # 监控间隔（秒）
        
        # 初始化服务器资源信息
        self._init_server_resources()
        
        # 启动监控
        if self.framework_config.enable_monitoring:
            self.start_monitoring()
        
        self.logger.info("🔧 资源管理器初始化完成")
    
    def _init_server_resources(self):
        """初始化服务器资源信息"""
        for server_name, config in self.labx.servers_config.items():
            self.server_resources[server_name] = ServerInfo(
                name=server_name,
                status=ServerStatus.OFFLINE,
                current_tasks=0,
                max_tasks=config.max_concurrent_tasks,
                cpu_usage=None,
                memory_usage=None,
                disk_usage=None,
                last_heartbeat=None
            )
            
            # 初始化资源历史
            self.resource_history[server_name] = []
    
    def start_monitoring(self):
        """启动资源监控"""
        if self.monitoring_active:
            self.logger.warning("⚠️  监控已在运行")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_worker,
            name="ResourceMonitor",
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("📊 资源监控已启动")
    
    def stop_monitoring(self):
        """停止资源监控"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("🛑 资源监控已停止")
    
    def _monitoring_worker(self):
        """监控工作线程"""
        self.logger.info("📊 资源监控线程启动")
        
        while self.monitoring_active:
            try:
                self._collect_resource_metrics()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"❌ 资源监控出错: {e}")
                time.sleep(5)  # 出错后短暂等待
        
        self.logger.info("📊 资源监控线程退出")
    
    def _collect_resource_metrics(self):
        """收集资源指标"""
        for server_name in self.server_resources.keys():
            try:
                # 获取系统信息
                system_info = self.labx.get_system_info(server_name)
                if system_info:
                    # 解析CPU使用率
                    cpu_usage = self._parse_cpu_usage(system_info)
                    memory_usage = self._parse_memory_usage(system_info)
                    disk_usage = self._parse_disk_usage(system_info)
                    load_average = self._parse_load_average(system_info)
                    
                    # 创建资源指标
                    metrics = ResourceMetrics(
                        timestamp=datetime.now(),
                        cpu_usage=cpu_usage or 0.0,
                        memory_usage=memory_usage or 0.0,
                        disk_usage=disk_usage or 0.0,
                        network_in=0.0,  # 暂时设为0，后续可以扩展
                        network_out=0.0,
                        load_average=load_average or 0.0
                    )
                    
                    # 更新服务器信息
                    with self.lock:
                        if server_name in self.server_resources:
                            server_info = self.server_resources[server_name]
                            server_info.cpu_usage = cpu_usage
                            server_info.memory_usage = memory_usage
                            server_info.disk_usage = disk_usage
                            server_info.last_heartbeat = datetime.now()
                            
                            # 更新状态
                            if server_info.status == ServerStatus.OFFLINE:
                                server_info.status = ServerStatus.IDLE
                    
                    # 添加到历史记录
                    self._add_resource_history(server_name, metrics)
                    
            except Exception as e:
                self.logger.debug(f"⚠️  收集服务器 {server_name} 资源指标时出错: {e}")
    
    def _parse_cpu_usage(self, system_info: Dict[str, Any]) -> Optional[float]:
        """解析CPU使用率"""
        # 这里需要根据实际的系统信息格式来解析
        # 暂时返回None，后续可以扩展
        return None
    
    def _parse_memory_usage(self, system_info: Dict[str, Any]) -> Optional[float]:
        """解析内存使用率"""
        # 这里需要根据实际的系统信息格式来解析
        # 暂时返回None，后续可以扩展
        return None
    
    def _parse_disk_usage(self, system_info: Dict[str, Any]) -> Optional[float]:
        """解析磁盘使用率"""
        # 这里需要根据实际的系统信息格式来解析
        # 暂时返回None，后续可以扩展
        return None
    
    def _parse_load_average(self, system_info: Dict[str, Any]) -> Optional[float]:
        """解析系统负载"""
        # 这里需要根据实际的系统信息格式来解析
        # 暂时返回None，后续可以扩展
        return None
    
    def _add_resource_history(self, server_name: str, metrics: ResourceMetrics):
        """添加资源历史记录"""
        with self.lock:
            if server_name in self.resource_history:
                history = self.resource_history[server_name]
                history.append(metrics)
                
                # 保留最近24小时的记录
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.resource_history[server_name] = [
                    m for m in history if m.timestamp > cutoff_time
                ]
    
    def allocate_server(self, task_priority: int = 0) -> Optional[str]:
        """
        分配服务器
        
        Args:
            task_priority: 任务优先级
            
        Returns:
            分配的服务器名称，如果没有可用服务器则返回 None
        """
        with self.lock:
            available_servers = self._get_available_servers()
            
            if not available_servers:
                self.logger.warning("⚠️  没有可用的服务器")
                return None
            
            # 根据分配策略选择服务器
            if self.allocation_strategy == "round_robin":
                selected_server = self._round_robin_allocation(available_servers)
            elif self.allocation_strategy == "least_loaded":
                selected_server = self._least_loaded_allocation(available_servers)
            elif self.allocation_strategy == "priority_based":
                selected_server = self._priority_based_allocation(available_servers, task_priority)
            else:
                selected_server = self._round_robin_allocation(available_servers)
            
            if selected_server:
                # 更新服务器状态
                server_info = self.server_resources[selected_server]
                server_info.current_tasks += 1
                
                # 检查是否需要更新状态
                if server_info.current_tasks >= server_info.max_tasks:
                    server_info.status = ServerStatus.BUSY
                
                self.logger.info(f"✅ 分配服务器: {selected_server} (当前任务: {server_info.current_tasks})")
                
                # 同时更新LabX中的服务器状态
                self.labx.update_server_task_count(selected_server, server_info.current_tasks)
            
            return selected_server
    
    def release_server(self, server_name: str):
        """
        释放服务器
        
        Args:
            server_name: 服务器名称
        """
        with self.lock:
            if server_name in self.server_resources:
                server_info = self.server_resources[server_name]
                server_info.current_tasks = max(0, server_info.current_tasks - 1)
                
                # 更新状态
                if server_info.current_tasks == 0:
                    server_info.status = ServerStatus.IDLE
                elif server_info.status == ServerStatus.BUSY:
                    server_info.status = ServerStatus.IDLE
                
                self.logger.info(f"🔓 释放服务器: {server_name} (当前任务: {server_info.current_tasks})")
                
                # 同时更新LabX中的服务器状态
                self.labx.update_server_task_count(server_name, server_info.current_tasks)
    
    def _get_available_servers(self) -> List[str]:
        """获取可用的服务器列表"""
        available = []
        
        for server_name, server_info in self.server_resources.items():
            # 检查服务器状态
            if server_info.status in [ServerStatus.OFFLINE, ServerStatus.ERROR]:
                continue
            
            # 检查任务数量
            if server_info.current_tasks >= server_info.max_tasks:
                continue
            
            # 检查心跳时间
            if server_info.last_heartbeat:
                time_since_heartbeat = datetime.now() - server_info.last_heartbeat
                if time_since_heartbeat > timedelta(minutes=5):  # 5分钟无心跳认为离线
                    server_info.status = ServerStatus.OFFLINE
                    continue
            
            available.append(server_name)
        
        return available
    
    def _round_robin_allocation(self, available_servers: List[str]) -> Optional[str]:
        """轮询分配策略"""
        if not available_servers:
            return None
        
        # 简单的轮询实现
        # 这里可以使用更复杂的轮询算法
        return available_servers[0]
    
    def _least_loaded_allocation(self, available_servers: List[str]) -> Optional[str]:
        """最少负载分配策略"""
        if not available_servers:
            return None
        
        # 选择当前任务数最少的服务器
        selected_server = min(
            available_servers,
            key=lambda name: self.server_resources[name].current_tasks
        )
        
        return selected_server
    
    def _priority_based_allocation(self, available_servers: List[str], task_priority: int) -> Optional[str]:
        """基于优先级的分配策略"""
        if not available_servers:
            return None
        
        # 高优先级任务分配给负载较低的服务器
        if task_priority > 5:  # 高优先级
            return self._least_loaded_allocation(available_servers)
        else:
            return self._round_robin_allocation(available_servers)
    
    def get_server_info(self, server_name: str) -> Optional[ServerInfo]:
        """
        获取服务器信息
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器信息，如果不存在则返回 None
        """
        with self.lock:
            return self.server_resources.get(server_name)
    
    def get_all_server_info(self) -> Dict[str, ServerInfo]:
        """
        获取所有服务器信息
        
        Returns:
            所有服务器信息的字典
        """
        with self.lock:
            return self.server_resources.copy()
    
    def get_server_status(self, server_name: str) -> Optional[ServerStatus]:
        """
        获取服务器状态
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器状态，如果不存在则返回 None
        """
        server_info = self.get_server_info(server_name)
        return server_info.status if server_info else None
    
    def is_server_available(self, server_name: str) -> bool:
        """
        检查服务器是否可用
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器是否可用
        """
        server_info = self.get_server_info(server_name)
        if not server_info:
            return False
        
        # 检查状态
        if server_info.status in [ServerStatus.OFFLINE, ServerStatus.ERROR]:
            return False
        
        # 检查任务数量
        if server_info.current_tasks >= server_info.max_tasks:
            return False
        
        # 检查心跳
        if server_info.last_heartbeat:
            time_since_heartbeat = datetime.now() - server_info.last_heartbeat
            if time_since_heartbeat > timedelta(minutes=5):
                return False
        
        return True
    
    def get_server_load(self, server_name: str) -> float:
        """
        获取服务器负载
        
        Args:
            server_name: 服务器名称
            
        Returns:
            负载值 (0.0-1.0)
        """
        server_info = self.get_server_info(server_name)
        if not server_info:
            return 1.0
        
        # 基于当前任务数和最大任务数计算负载
        task_load = server_info.current_tasks / server_info.max_tasks
        
        # 如果有资源指标，可以结合CPU、内存等计算综合负载
        resource_load = 0.0
        if server_info.cpu_usage is not None:
            resource_load = max(resource_load, server_info.cpu_usage)
        if server_info.memory_usage is not None:
            resource_load = max(resource_load, server_info.memory_usage)
        
        # 综合负载：任务负载和资源负载的加权平均
        return 0.7 * task_load + 0.3 * resource_load
    
    def get_cluster_load(self) -> float:
        """
        获取集群整体负载
        
        Returns:
            集群负载值 (0.0-1.0)
        """
        with self.lock:
            if not self.server_resources:
                return 0.0
            
            total_load = 0.0
            available_count = 0
            
            for server_name in self.server_resources.keys():
                if self.is_server_available(server_name):
                    total_load += self.get_server_load(server_name)
                    available_count += 1
            
            return total_load / available_count if available_count > 0 else 0.0
    
    def set_allocation_strategy(self, strategy: str):
        """
        设置资源分配策略
        
        Args:
            strategy: 分配策略 ("round_robin", "least_loaded", "priority_based")
        """
        valid_strategies = ["round_robin", "least_loaded", "priority_based"]
        if strategy not in valid_strategies:
            self.logger.warning(f"⚠️  无效的分配策略: {strategy}，使用默认策略")
            strategy = "round_robin"
        
        self.allocation_strategy = strategy
        self.logger.info(f"🔧 设置资源分配策略: {strategy}")
    
    def get_resource_history(self, server_name: str, 
                           hours: int = 24) -> List[ResourceMetrics]:
        """
        获取服务器资源历史
        
        Args:
            server_name: 服务器名称
            hours: 历史小时数
            
        Returns:
            资源指标历史列表
        """
        with self.lock:
            if server_name not in self.resource_history:
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            history = self.resource_history[server_name]
            
            return [m for m in history if m.timestamp > cutoff_time]
    
    def get_cluster_summary(self) -> Dict[str, Any]:
        """
        获取集群摘要信息
        
        Returns:
            集群摘要字典
        """
        with self.lock:
            total_servers = len(self.server_resources)
            available_servers = len([s for s in self.server_resources.values() 
                                   if self.is_server_available(s.name)])
            busy_servers = len([s for s in self.server_resources.values() 
                              if s.status == ServerStatus.BUSY])
            offline_servers = len([s for s in self.server_resources.values() 
                                 if s.status == ServerStatus.OFFLINE])
            
            total_tasks = sum(s.current_tasks for s in self.server_resources.values())
            max_tasks = sum(s.max_tasks for s in self.server_resources.values())
            
            return {
                'total_servers': total_servers,
                'available_servers': available_servers,
                'busy_servers': busy_servers,
                'offline_servers': offline_servers,
                'total_tasks': total_tasks,
                'max_tasks': max_tasks,
                'cluster_load': self.get_cluster_load(),
                'allocation_strategy': self.allocation_strategy
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查
        
        Returns:
            健康检查结果
        """
        health_results = {}
        
        for server_name in self.server_resources.keys():
            try:
                # 尝试连接服务器
                if self.labx.connect_server(server_name):
                    # 执行简单命令测试
                    result = self.labx.execute_command(server_name, "echo 'health_check'")
                    if result and result.get('success'):
                        health_results[server_name] = {
                            'status': 'healthy',
                            'response_time': 0.1,  # 简化处理
                            'last_check': datetime.now()
                        }
                    else:
                        health_results[server_name] = {
                            'status': 'unhealthy',
                            'error': 'command_execution_failed',
                            'last_check': datetime.now()
                        }
                else:
                    health_results[server_name] = {
                        'status': 'unhealthy',
                        'error': 'connection_failed',
                        'last_check': datetime.now()
                    }
                    
            except Exception as e:
                health_results[server_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.now()
                }
        
        return health_results
    
    def shutdown(self):
        """关闭资源管理器"""
        self.logger.info("🛑 关闭资源管理器")
        
        # 停止监控
        self.stop_monitoring()
        
        # 清理资源
        with self.lock:
            self.server_resources.clear()
            self.resource_history.clear()
        
        self.logger.info("✅ 资源管理器已关闭")
