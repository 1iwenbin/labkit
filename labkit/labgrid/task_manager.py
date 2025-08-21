#!/usr/bin/env python3
"""
LabGrid 任务管理器

管理实验任务的队列、状态跟踪和调度
"""

import os
import time
import logging
import threading
import queue
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass

from .types import (
    TaskInfo, 
    TaskStatus, 
    ExperimentConfig, 
    ExperimentResult,
    ExperimentStatus
)
from .experiment import Lab


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    experiment_type: str
    config: ExperimentConfig
    status: TaskStatus
    created_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    assigned_server: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    result: Optional[ExperimentResult] = None
    retry_count: int = 0
    max_retries: int = 0
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    callback: Optional[Callable[[Task], None]] = None


class TaskManager:
    """
    任务管理器
    
    负责任务的创建、队列管理、状态跟踪和调度
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """
        初始化任务管理器
        
        Args:
            max_queue_size: 任务队列最大大小
        """
        self.logger = logging.getLogger(__name__)
        self.max_queue_size = max_queue_size
        
        # 任务队列（优先级队列）
        self.task_queue = queue.PriorityQueue(maxsize=max_queue_size)
        
        # 任务存储
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        
        # 线程安全
        self.lock = threading.RLock()
        
        # 任务统计
        self.stats = {
            'total_created': 0,
            'total_completed': 0,
            'total_failed': 0,
            'total_retried': 0
        }
        
        # 任务ID生成器
        self._task_id_counter = 0
        self._task_id_lock = threading.Lock()
        
        self.logger.info("🔧 任务管理器初始化完成")
    
    def _generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        with self._task_id_lock:
            self._task_id_counter += 1
            timestamp = int(time.time() * 1000)
            return f"task_{timestamp}_{self._task_id_counter}"
    
    def create_task(self, experiment_type: str, config: ExperimentConfig, 
                   priority: int = 0, max_retries: int = 0,
                   dependencies: Optional[List[str]] = None,
                   callback: Optional[Callable[[Task], None]] = None) -> str:
        """
        创建新任务
        
        Args:
            experiment_type: 实验类型
            config: 实验配置
            priority: 优先级（数字越大优先级越高）
            max_retries: 最大重试次数
            dependencies: 依赖的任务ID列表
            callback: 任务完成回调函数
            
        Returns:
            任务ID
        """
        task_id = self._generate_task_id()
        
        task = Task(
            task_id=task_id,
            experiment_type=experiment_type,
            config=config,
            status=TaskStatus.PENDING,
            created_time=datetime.now(),
            max_retries=max_retries,
            priority=priority,
            dependencies=dependencies or [],
            callback=callback
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.stats['total_created'] += 1
        
        self.logger.info(f"📋 创建任务: {task_id} ({experiment_type})")
        self.logger.debug(f"  - 优先级: {priority}")
        self.logger.debug(f"  - 最大重试: {max_retries}")
        self.logger.debug(f"  - 依赖: {dependencies or []}")
        
        return task_id
    
    def submit_task(self, task_id: str) -> bool:
        """
        提交任务到队列
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功提交
        """
        with self.lock:
            if task_id not in self.tasks:
                self.logger.error(f"❌ 任务 {task_id} 不存在")
                return False
            
            task = self.tasks[task_id]
            
            # 检查依赖是否满足
            if not self._check_dependencies(task):
                self.logger.debug(f"⏳ 任务 {task_id} 依赖未满足，等待中")
                return False
            
            # 检查队列是否已满
            if self.task_queue.full():
                self.logger.warning(f"⚠️  任务队列已满，无法提交任务 {task_id}")
                return False
            
            try:
                # 使用负优先级，因为 PriorityQueue 是最小堆
                self.task_queue.put((-task.priority, task.created_time.timestamp(), task))
                self.logger.debug(f"✅ 任务 {task_id} 已提交到队列")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ 提交任务 {task_id} 到队列时出错: {e}")
                return False
    
    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个待执行的任务
        
        Returns:
            下一个任务，如果没有则返回 None
        """
        try:
            # 从队列中获取任务，非阻塞
            _, _, task = self.task_queue.get_nowait()
            return task
        except queue.Empty:
            return None
    
    def start_task(self, task_id: str, server_name: str) -> bool:
        """
        开始执行任务
        
        Args:
            task_id: 任务ID
            server_name: 分配的服务器名称
            
        Returns:
            是否成功开始
        """
        with self.lock:
            if task_id not in self.tasks:
                self.logger.error(f"❌ 任务 {task_id} 不存在")
                return False
            
            task = self.tasks[task_id]
            
            if task.status != TaskStatus.PENDING:
                self.logger.warning(f"⚠️  任务 {task_id} 状态不是 PENDING: {task.status}")
                return False
            
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            task.assigned_server = server_name
            
            # 移动到运行中任务列表
            self.running_tasks[task_id] = task
            
            self.logger.info(f"🚀 开始执行任务: {task_id} 在服务器 {server_name}")
            return True
    
    def complete_task(self, task_id: str, result: ExperimentResult) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 实验结果
            
        Returns:
            是否成功完成
        """
        with self.lock:
            if task_id not in self.running_tasks:
                self.logger.error(f"❌ 任务 {task_id} 不在运行中任务列表")
                return False
            
            task = self.running_tasks[task_id]
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            task.result = result
            task.progress = 1.0
            
            # 移动到已完成任务列表
            self.completed_tasks[task_id] = task
            del self.running_tasks[task_id]
            
            # 更新统计
            self.stats['total_completed'] += 1
            
            self.logger.info(f"✅ 任务完成: {task_id}")
            
            # 执行回调
            if task.callback:
                try:
                    task.callback(task)
                except Exception as e:
                    self.logger.error(f"❌ 执行任务回调时出错: {e}")
            
            return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            
        Returns:
            是否成功标记失败
        """
        with self.lock:
            if task_id not in self.running_tasks:
                self.logger.error(f"❌ 任务 {task_id} 不在运行中任务列表")
                return False
            
            task = self.running_tasks[task_id]
            
            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.start_time = None
                task.end_time = None
                task.assigned_server = None
                task.progress = 0.0
                task.error_message = None
                
                # 重新提交到队列
                self.task_queue.put((-task.priority, task.created_time.timestamp(), task))
                
                self.logger.info(f"🔄 任务 {task_id} 重试 {task.retry_count}/{task.max_retries}")
                self.stats['total_retried'] += 1
                
            else:
                # 重试次数用完，标记为失败
                task.status = TaskStatus.FAILED
                task.end_time = datetime.now()
                task.error_message = error_message
                
                # 移动到失败任务列表
                self.failed_tasks[task_id] = task
                del self.running_tasks[task_id]
                
                # 更新统计
                self.stats['total_failed'] += 1
                
                self.logger.error(f"❌ 任务失败: {task_id}, 错误: {error_message}")
            
            return True
    
    def update_task_progress(self, task_id: str, progress: float) -> bool:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度值 (0.0-1.0)
            
        Returns:
            是否成功更新
        """
        with self.lock:
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.progress = max(0.0, min(1.0, progress))
                return True
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if task.status == TaskStatus.PENDING:
                # 从队列中移除
                # 注意：PriorityQueue 不支持直接移除，这里只是标记状态
                task.status = TaskStatus.CANCELLED
                self.logger.info(f"🚫 取消任务: {task_id}")
                return True
            
            elif task.status == TaskStatus.RUNNING:
                # 标记为取消，等待执行器处理
                task.status = TaskStatus.CANCELLED
                self.logger.info(f"🚫 标记任务为取消: {task_id}")
                return True
            
            else:
                self.logger.warning(f"⚠️  无法取消已完成或失败的任务: {task_id}")
                return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回 None
        """
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态，如果不存在则返回 None
        """
        task = self.get_task(task_id)
        return task.status if task else None
    
    def get_all_tasks(self) -> Dict[str, List[Task]]:
        """
        获取所有任务，按状态分组
        
        Returns:
            任务状态分组字典
        """
        with self.lock:
            return {
                'pending': [task for task in self.tasks.values() 
                           if task.status == TaskStatus.PENDING],
                'running': list(self.running_tasks.values()),
                'completed': list(self.completed_tasks.values()),
                'failed': list(self.failed_tasks.values()),
                'cancelled': [task for task in self.tasks.values() 
                             if task.status == TaskStatus.CANCELLED]
            }
    
    def get_tasks_by_server(self, server_name: str) -> List[Task]:
        """
        获取指定服务器上的任务
        
        Args:
            server_name: 服务器名称
            
        Returns:
            任务列表
        """
        with self.lock:
            return [task for task in self.running_tasks.values() 
                   if task.assigned_server == server_name]
    
    def get_queue_size(self) -> int:
        """
        获取队列大小
        
        Returns:
            队列中的任务数量
        """
        return self.task_queue.qsize()
    
    def is_queue_empty(self) -> bool:
        """
        检查队列是否为空
        
        Returns:
            队列是否为空
        """
        return self.task_queue.empty()
    
    def is_queue_full(self) -> bool:
        """
        检查队列是否已满
        
        Returns:
            队列是否已满
        """
        return self.task_queue.full()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        with self.lock:
            stats = self.stats.copy()
            stats.update({
                'queue_size': self.get_queue_size(),
                'running_count': len(self.running_tasks),
                'completed_count': len(self.completed_tasks),
                'failed_count': len(self.failed_tasks),
                'total_tasks': len(self.tasks)
            })
            return stats
    
    def clear_completed_tasks(self, max_age_hours: int = 24):
        """
        清理已完成的任务
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            to_remove = []
            for task_id, task in self.completed_tasks.items():
                if task.end_time and task.end_time.timestamp() < cutoff_time:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.completed_tasks[task_id]
                if task_id in self.tasks:
                    del self.tasks[task_id]
            
            if to_remove:
                self.logger.info(f"🧹 清理了 {len(to_remove)} 个已完成的任务")
    
    def clear_failed_tasks(self, max_age_hours: int = 24):
        """
        清理失败的任务
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            to_remove = []
            for task_id, task in self.failed_tasks.items():
                if task.end_time and task.end_time.timestamp() < cutoff_time:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.failed_tasks[task_id]
                if task_id in self.tasks:
                    del self.tasks[task_id]
            
            if to_remove:
                self.logger.info(f"🧹 清理了 {len(to_remove)} 个失败的任务")
    
    def _check_dependencies(self, task: Task) -> bool:
        """
        检查任务依赖是否满足
        
        Args:
            task: 任务对象
            
        Returns:
            依赖是否满足
        """
        if not task.dependencies:
            return True
        
        with self.lock:
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    self.logger.warning(f"⚠️  任务 {task.task_id} 的依赖 {dep_id} 不存在")
                    return False
                
                dep_task = self.tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
        
        return True
    
    def wait_for_task_completion(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），None 表示无限等待
            
        Returns:
            是否在超时前完成
        """
        start_time = time.time()
        
        while True:
            task = self.get_task(task_id)
            if not task:
                return False
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.1)  # 短暂休眠，避免忙等待
    
    def shutdown(self):
        """关闭任务管理器"""
        self.logger.info("🛑 关闭任务管理器")
        
        # 清空队列
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except queue.Empty:
                break
        
        # 清理所有任务
        with self.lock:
            self.tasks.clear()
            self.running_tasks.clear()
            self.completed_tasks.clear()
            self.failed_tasks.clear()
        
        self.logger.info("✅ 任务管理器已关闭")
