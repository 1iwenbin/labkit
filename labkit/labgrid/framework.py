#!/usr/bin/env python3
"""
LabGrid 框架主类

协调各个组件的协作，提供高级API接口
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

from .types import (
    ServerConfig, 
    FrameworkConfig, 
    ExperimentConfig,
    ExperimentResult,
    ExperimentStatus
)
from .config import ConfigManager
from .labx import LabX
from .experiment import Lab
from .registry import ExperimentRegistry
from .task_manager import TaskManager
from .resource_manager import ResourceManager
from .result_manager import ResultManager


class LabGrid:
    """
    LabGrid 框架主类
    
    协调各个组件的协作，提供高级API接口
    """
    
    def __init__(self, servers_config_file: str = "servers.json", 
                 framework_config_file: Optional[str] = None,
                 config_dir: str = "configs"):
        """
        初始化 LabGrid 框架
        
        Args:
            servers_config_file: 服务器配置文件
            framework_config_file: 框架配置文件
            config_dir: 配置目录
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 初始化 LabGrid 框架")
        
        # 配置管理
        self.config_manager = ConfigManager(config_dir)
        
        # 加载配置
        self.servers_config = self.config_manager.load_servers_config(servers_config_file)
        self.framework_config = self.config_manager.load_framework_config(framework_config_file)
        
        if not self.servers_config:
            raise ValueError("没有可用的服务器配置")
        
        # 初始化组件
        self._init_components()
        
        # 框架状态
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        self.logger.info("✅ LabGrid 框架初始化完成")
    
    def _init_components(self):
        """初始化各个组件"""
        # 创建 LabX 实例
        self.labx = LabX(self.servers_config)
        
        # 创建实验注册器
        self.registry = ExperimentRegistry()
        
        # 创建任务管理器
        self.task_manager = TaskManager(
            max_queue_size=self.framework_config.task_queue_size
        )
        
        # 创建资源管理器
        self.resource_manager = ResourceManager(
            labx=self.labx,
            framework_config=self.framework_config
        )
        
        # 创建结果管理器
        self.result_manager = ResultManager(
            base_dir=self.framework_config.log_dir,
            max_retention_days=self.framework_config.result_retention_days
        )
        
        # 工作线程
        self.worker_threads: List[threading.Thread] = []
        self.worker_threads_active = False
        
        self.logger.info("🔧 所有组件初始化完成")
    
    def start(self):
        """启动框架"""
        if self.is_running:
            self.logger.warning("⚠️  框架已在运行")
            return
        
        self.logger.info("🚀 启动 LabGrid 框架")
        
        try:
            # 启动工作线程
            self._start_worker_threads()
            
            # 更新状态
            self.is_running = True
            self.start_time = datetime.now()
            
            self.logger.info("✅ LabGrid 框架启动成功")
            
        except Exception as e:
            self.logger.error(f"❌ 启动框架时出错: {e}")
            raise
    
    def stop(self):
        """停止框架"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 停止 LabGrid 框架")
        
        try:
            # 停止工作线程
            self._stop_worker_threads()
            
            # 关闭组件
            self._shutdown_components()
            
            # 更新状态
            self.is_running = False
            
            self.logger.info("✅ LabGrid 框架已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止框架时出错: {e}")
    
    def _start_worker_threads(self):
        """启动工作线程"""
        if self.worker_threads_active:
            return
        
        self.worker_threads_active = True
        
        # 根据配置启动工作线程
        worker_count = min(
            self.framework_config.max_worker_threads,
            len(self.servers_config) * self.framework_config.max_workers_per_server,
            self.framework_config.max_total_workers
        )
        
        for i in range(worker_count):
            worker = threading.Thread(
                target=self._worker_thread,
                name=f"LabGridWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        self.logger.info(f"🚀 启动了 {worker_count} 个工作线程")
    
    def _stop_worker_threads(self):
        """停止工作线程"""
        if not self.worker_threads_active:
            return
        
        self.worker_threads_active = False
        
        # 等待所有工作线程结束
        for worker in self.worker_threads:
            worker.join(timeout=5)
        
        self.worker_threads.clear()
        self.logger.info("🛑 所有工作线程已停止")
    
    def _worker_thread(self):
        """工作线程主函数"""
        thread_name = threading.current_thread().name
        self.logger.info(f"🚀 {thread_name} 启动")
        
        while self.worker_threads_active:
            try:
                # 获取下一个任务
                task = self.task_manager.get_next_task()
                if not task:
                    time.sleep(1)  # 没有任务时短暂休眠
                    continue
                
                self.logger.info(f"🔄 {thread_name} 开始处理任务: {task.task_id}")
                
                # 执行任务
                self._execute_task(task)
                
            except Exception as e:
                self.logger.error(f"❌ {thread_name} 工作线程出错: {e}")
                time.sleep(5)  # 出错后等待一段时间
        
        self.logger.info(f"🛑 {thread_name} 退出")
    
    def _execute_task(self, task):
        """执行单个任务"""
        try:
            # 分配服务器
            server_name = self.resource_manager.allocate_server(task.config.priority)
            if not server_name:
                self.task_manager.fail_task(task.task_id, "无法分配服务器")
                return
            
            # 开始任务
            if not self.task_manager.start_task(task.task_id, server_name):
                self.resource_manager.release_server(server_name)
                return
            
            # 创建实验实例
            experiment = self.registry.create_experiment(
                task.experiment_type,
                task.config,
                self.labx
            )
            
            if not experiment:
                self.task_manager.fail_task(task.task_id, "无法创建实验实例")
                self.resource_manager.release_server(server_name)
                return
            
            # 分配服务器给实验
            experiment.assign_server(server_name)
            
            try:
                # 运行实验
                result = experiment.run()
                
                # 存储结果
                self.result_manager.store_result(result)
                
                # 完成任务
                if result.status == ExperimentStatus.COMPLETED:
                    self.task_manager.complete_task(task.task_id, result)
                else:
                    self.task_manager.fail_task(task.task_id, result.error_message or "实验执行失败")
                
            finally:
                # 释放服务器
                experiment.release_server()
                self.resource_manager.release_server(server_name)
            
        except Exception as e:
            self.logger.error(f"❌ 执行任务 {task.task_id} 时出错: {e}")
            self.task_manager.fail_task(task.task_id, str(e))
            
            # 确保服务器被释放
            if hasattr(experiment, 'assigned_server') and experiment.assigned_server:
                self.resource_manager.release_server(experiment.assigned_server)
    
    def _shutdown_components(self):
        """关闭各个组件"""
        try:
            self.task_manager.shutdown()
            self.resource_manager.shutdown()
            self.result_manager.shutdown()
            self.labx.close()
        except Exception as e:
            self.logger.error(f"❌ 关闭组件时出错: {e}")
    
    # ==================== 实验管理 API ====================
    
    def register_experiment(self, experiment_type: str, experiment_class: type, 
                          description: str = "", tags: Optional[List[str]] = None):
        """
        注册实验类型
        
        Args:
            experiment_type: 实验类型标识
            experiment_class: 实验类
            description: 实验类型描述
            tags: 实验类型标签列表
        """
        self.registry.register(experiment_type, experiment_class, description, tags)
    
    def run_experiment(self, experiment_type: str, config: ExperimentConfig) -> str:
        """
        运行单个实验
        
        Args:
            experiment_type: 实验类型
            config: 实验配置
            
        Returns:
            任务ID
        """
        # 验证实验类型
        if not self.registry.validate_experiment_type(experiment_type):
            raise ValueError(f"实验类型 {experiment_type} 未注册")
        
        # 验证配置
        if not self.config_manager.validate_experiment_config(config):
            raise ValueError("实验配置验证失败")
        
        # 创建任务
        task_id = self.task_manager.create_task(
            experiment_type=experiment_type,
            config=config,
            priority=config.priority,
            max_retries=config.retry_count
        )
        
        # 提交任务
        if not self.task_manager.submit_task(task_id):
            raise RuntimeError("无法提交任务到队列")
        
        self.logger.info(f"📋 提交实验任务: {task_id} ({experiment_type})")
        return task_id
    
    def run_batch_experiments(self, experiments: List[tuple]) -> List[str]:
        """
        批量运行多个实验
        
        Args:
            experiments: 实验列表，每个元素是 (experiment_type, config) 元组
            
        Returns:
            任务ID列表
        """
        task_ids = []
        
        for experiment_type, config in experiments:
            try:
                task_id = self.run_experiment(experiment_type, config)
                task_ids.append(task_id)
            except Exception as e:
                self.logger.error(f"❌ 提交实验失败: {experiment_type}, 错误: {e}")
        
        self.logger.info(f"📋 批量提交了 {len(task_ids)} 个实验任务")
        return task_ids
    
    def wait_for_experiment(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """
        等待实验完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            
        Returns:
            是否在超时前完成
        """
        return self.task_manager.wait_for_task_completion(task_id, timeout)
    
    def get_experiment_status(self, task_id: str) -> Optional[str]:
        """
        获取实验状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            实验状态
        """
        task = self.task_manager.get_task(task_id)
        return task.status.value if task else None
    
    def get_experiment_result(self, task_id: str) -> Optional[ExperimentResult]:
        """
        获取实验结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            实验结果
        """
        task = self.task_manager.get_task(task_id)
        if task and task.result:
            return task.result
        return None
    
    # ==================== 查询和监控 API ====================
    
    def list_experiments(self) -> List[str]:
        """列出所有已注册的实验类型"""
        return self.registry.list_experiments()
    
    def get_experiment_info(self, experiment_type: str) -> Optional[Dict[str, Any]]:
        """获取实验类型信息"""
        return self.registry.get_experiment_info(experiment_type)
    
    def get_all_tasks(self) -> Dict[str, List]:
        """获取所有任务，按状态分组"""
        return self.task_manager.get_all_tasks()
    
    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        return self.task_manager.get_stats()
    
    def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """获取服务器信息"""
        return self.resource_manager.get_server_info(server_name)
    
    def get_all_server_info(self) -> Dict[str, Any]:
        """获取所有服务器信息"""
        return self.resource_manager.get_all_server_info()
    
    def get_cluster_summary(self) -> Dict[str, Any]:
        """获取集群摘要信息"""
        return self.resource_manager.get_cluster_summary()
    
    def get_all_results(self) -> List[ExperimentResult]:
        """获取所有实验结果"""
        return self.result_manager.get_all_results()
    
    def get_result(self, experiment_id: str) -> Optional[ExperimentResult]:
        """获取指定实验结果"""
        return self.result_manager.get_result(experiment_id)
    
    def get_result_statistics(self) -> Dict[str, Any]:
        """获取结果统计信息"""
        return self.result_manager.get_result_statistics()
    
    def search_results(self, query: str) -> List[ExperimentResult]:
        """搜索实验结果"""
        return self.result_manager.search_results(query)
    
    def compare_results(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """比较多个实验结果"""
        return self.result_manager.compare_results(experiment_ids)
    
    # ==================== 配置和管理 API ====================
    
    def get_framework_config(self) -> FrameworkConfig:
        """获取框架配置"""
        return self.framework_config
    
    def update_framework_config(self, **kwargs):
        """更新框架配置"""
        for key, value in kwargs.items():
            if hasattr(self.framework_config, key):
                setattr(self.framework_config, key, value)
                self.logger.info(f"🔧 更新配置: {key} = {value}")
    
    def set_allocation_strategy(self, strategy: str):
        """设置资源分配策略"""
        self.resource_manager.set_allocation_strategy(strategy)
    
    def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        return {
            'framework_status': 'running' if self.is_running else 'stopped',
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'servers': self.resource_manager.health_check(),
            'tasks': self.task_manager.get_stats(),
            'results': self.result_manager.get_result_statistics()
        }
    
    def cleanup_old_results(self, days: int):
        """清理旧结果"""
        self.result_manager.cleanup_old_results(days)
    
    def export_results(self, output_file: str, format: str = "json"):
        """导出结果"""
        return self.result_manager.export_results(output_file, format=format)
    
    # ==================== 上下文管理器支持 ====================
    
    def __enter__(self):
        """进入上下文"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.stop()
    
    # ==================== 框架信息 ====================
    
    def get_framework_info(self) -> Dict[str, Any]:
        """获取框架信息"""
        return {
            'name': 'LabGrid',
            'version': '1.0.0',
            'status': 'running' if self.is_running else 'stopped',
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'components': {
                'config_manager': 'initialized',
                'labx': 'initialized',
                'registry': 'initialized',
                'task_manager': 'initialized',
                'resource_manager': 'initialized',
                'result_manager': 'initialized'
            },
            'servers': len(self.servers_config),
            'registered_experiments': len(self.registry.list_experiments()),
            'worker_threads': len(self.worker_threads)
        }
    
    def print_status(self):
        """打印框架状态"""
        info = self.get_framework_info()
        
        self.logger.info("📊 LabGrid 框架状态:")
        self.logger.info(f"  - 状态: {info['status']}")
        self.logger.info(f"  - 运行时间: {info['uptime']:.1f} 秒")
        self.logger.info(f"  - 服务器数量: {info['servers']}")
        self.logger.info(f"  - 已注册实验类型: {info['registered_experiments']}")
        self.logger.info(f"  - 工作线程数: {info['worker_threads']}")
        
        # 打印任务状态
        task_stats = self.task_manager.get_stats()
        self.logger.info(f"  - 任务队列大小: {task_stats['queue_size']}")
        self.logger.info(f"  - 运行中任务: {task_stats['running_count']}")
        self.logger.info(f"  - 已完成任务: {task_stats['completed_count']}")
        self.logger.info(f"  - 失败任务: {task_stats['failed_count']}")
        
        # 打印集群状态
        cluster_summary = self.resource_manager.get_cluster_summary()
        self.logger.info(f"  - 可用服务器: {cluster_summary['available_servers']}")
        self.logger.info(f"  - 忙碌服务器: {cluster_summary['busy_servers']}")
        self.logger.info(f"  - 集群负载: {cluster_summary['cluster_load']:.2f}")
