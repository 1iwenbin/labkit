#!/usr/bin/env python3
"""
LabGrid 类型定义

定义框架中使用的各种数据类型、枚举和数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum, auto
from datetime import datetime


class ExperimentStatus(Enum):
    """实验状态枚举"""
    PENDING = auto()      # 等待中
    INITIALIZING = auto() # 初始化中
    RUNNING = auto()      # 运行中
    COLLECTING = auto()   # 收集数据中
    ANALYZING = auto()    # 分析数据中
    SAVING = auto()       # 保存数据中
    CLEANING = auto()     # 清理环境中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    CANCELLED = auto()    # 已取消


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = auto()      # 等待中
    RUNNING = auto()      # 运行中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    CANCELLED = auto()    # 已取消


class ServerStatus(Enum):
    """服务器状态枚举"""
    IDLE = auto()         # 空闲
    BUSY = auto()         # 忙碌
    OFFLINE = auto()      # 离线
    ERROR = auto()        # 错误


@dataclass
class ServerConfig:
    """服务器配置数据类"""
    name: str                     # 服务器名称
    host: str                     # 服务器IP地址
    user: str                     # 用户名
    port: int = 22                # SSH端口
    password: Optional[str] = None # 密码
    key_filename: Optional[str] = None # 私钥文件路径
    max_concurrent_tasks: int = 1 # 最大并发任务数
    description: Optional[str] = None # 服务器描述


@dataclass
class ExperimentConfig:
    """实验配置数据类"""
    experiment_type: str           # 实验类型标识
    output_dir: str               # 输出目录
    timeout: int = 3600           # 超时时间（秒）
    retry_count: int = 0          # 重试次数
    priority: int = 0             # 优先级（数字越大优先级越高）
    parameters: Dict[str, Any] = field(default_factory=dict) # 实验参数
    dependencies: List[str] = field(default_factory=list) # 依赖的实验ID
    tags: List[str] = field(default_factory=list) # 标签
    description: Optional[str] = None # 实验描述


@dataclass
class ExperimentResult:
    """实验结果数据类"""
    experiment_id: str            # 实验ID
    status: ExperimentStatus      # 实验状态
    output_dir: str               # 输出目录
    start_time: Optional[datetime] = None # 开始时间
    end_time: Optional[datetime] = None   # 结束时间
    duration: Optional[float] = None      # 执行时长（秒）
    result_files: List[str] = field(default_factory=list) # 结果文件列表
    metrics: Dict[str, Any] = field(default_factory=dict) # 性能指标
    error_message: Optional[str] = None  # 错误信息
    logs: List[str] = field(default_factory=list) # 日志信息


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str                  # 任务ID
    experiment_id: str            # 关联的实验ID
    status: TaskStatus            # 任务状态
    created_time: datetime        # 创建时间
    server_name: Optional[str] = None # 分配的服务器名称
    start_time: Optional[datetime] = None # 开始时间
    end_time: Optional[datetime] = None   # 结束时间
    progress: float = 0.0         # 进度（0.0-1.0）
    error_message: Optional[str] = None  # 错误信息


@dataclass
class ServerInfo:
    """服务器信息数据类"""
    name: str                     # 服务器名称
    status: ServerStatus          # 服务器状态
    current_tasks: int = 0        # 当前运行的任务数
    max_tasks: int = 1           # 最大任务数
    cpu_usage: Optional[float] = None # CPU使用率
    memory_usage: Optional[float] = None # 内存使用率
    disk_usage: Optional[float] = None  # 磁盘使用率
    last_heartbeat: Optional[datetime] = None # 最后心跳时间


@dataclass
class FrameworkConfig:
    """框架配置数据类"""
    max_worker_threads: int = 4   # 最大工作线程数
    max_workers_per_server: int = 2 # 每个服务器最大工作线程数
    max_total_workers: int = 16   # 最大总工作线程数
    experiment_timeout: int = 86400 * 7 # 实验超时时间（秒）
    task_queue_size: int = 1000   # 任务队列大小
    log_level: str = "INFO"       # 日志级别
    log_dir: str = "logs"         # 日志目录
    result_retention_days: int = 30 # 结果保留天数
    enable_monitoring: bool = True # 是否启用监控
