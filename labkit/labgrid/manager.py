#!/usr/bin/env python3
"""
SATuSGH 实验管理器

这个模块提供了 SATuSGH 实验的完整管理功能，包括：
- 远程服务器管理
- 实验环境构建
- 实验执行和监控
- 结果分析
- 多线程并发执行

主要组件：
- SATuSGHManager: 远程服务器管理器
- 实验执行流程
- 结果分析功能
- 多线程任务调度
"""

import sys
import os
import time
import json
import threading
import shutil
import queue
import logging
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

# 添加 workspace 目录到 Python 路径
workspace_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, workspace_path)

from labkit.remote import RemoteManager
from util import SATuSGHLabGen, PingAnalyzer


# ==================== 日志配置 ====================

def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """
    设置日志配置
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别
    """
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"satusgh_{timestamp}.log")
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # 同时输出到控制台
        ]
    )
    
    # 创建SATuSGH专用的日志记录器
    logger = logging.getLogger('SATuSGH')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 避免重复输出
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        console_handler = logging.StreamHandler(sys.stdout)
        
        formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger, log_file

# 初始化日志
logger, log_file_path = setup_logging()

# ==================== 常量定义 ====================

# 实验相关常量
DELTA_MAX = 5000  # 最大时间偏移量（毫秒）
LABX_PATH = "/home/cnic/reals/bin/kinexlabx"  # 实验执行器路径
SERVER_PORT = 8080  # 服务器端口

# 多线程相关常量
MAX_WORKER_THREADS = 4  # 默认最大工作线程数
MAX_WORKERS_PER_SERVER = 2  # 每个服务器对应的工作线程数
MAX_TOTAL_WORKERS = 16  # 最大总工作线程数
EXPERIMENT_TIMEOUT = 86400 * 7  # 实验超时时间（秒），默认7天


@dataclass
class ExperimentTask:
    """实验任务数据类"""
    task_id: str
    output_dir: str
    delta_t1: int
    delta_t2: int
    created_time: datetime
    status: str = "pending"  # pending, running, completed, failed
    server_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


def get_cluster_config(master_ip: str = "172.20.64.6", agent_ip: str = "172.20.64.6") -> str:
    """
    获取集群配置
    
    Args:
        master_ip: master 节点的 IP 地址
        agent_ip: agent 节点的 IP 地址
        
    Returns:
        JSON 格式的集群配置字符串
    """
    return json.dumps({
        "global": {
            "dev_mode": False,
            "master_image": "harbor.fir.ac.cn/1iwenbin/reals-master:v1.0.0",
            "agent_image": "harbor.fir.ac.cn/1iwenbin/reals-agent:v1.0.0",
            "log_dir": "/home/cnic/reals/log",
            "driver_nfs_dir": "/mnt/reals-driver/nfs",
            "user": "root",
            "reals_dir": "/home/cnic/reals"
        },
        "monitor": {
            "prometheus_image": "harbor.fir.ac.cn/library/prom/prometheus:v2.55.0",
            "grafana_image": "harbor.fir.ac.cn/library/grafana/grafana:11.3.0-ubuntu",
            "loki_image": "harbor.fir.ac.cn/library/grafana/loki:3.1.2",
            "node_exporter_image": "harbor.fir.ac.cn/library/quay.io/prometheus/node-exporter:v1.8.2",
            "promtail_image": "harbor.fir.ac.cn/library/grafana/promtail:3.1.2"
        },
        "master": {
            "ip": master_ip,
            "http_port": 8080,
            "rpc_port": 50051,
            "tcp_port": 8088,
            "keepalive": 30
        },
        "agents": [
            {
                "id": 1,
                "ip": agent_ip,
                "rpc_port": 50052,
                "phy_nic": "enp1s0",
                "semi_phy_nic": "vlan-ac"
            }
        ]
    })


class SATuSGHManager:
    """
    SATuSGH 远程管理器
    
    负责管理远程服务器连接、实验执行和结果分析。
    支持多服务器并发执行，自动负载均衡。
    新增多线程支持，提高实验执行效率。
    """
    
    def __init__(self, config_file: str = "configs/servers.json", enable_ui: bool = False, 
                 max_workers: int = MAX_WORKER_THREADS):
        """
        初始化管理器
        
        Args:
            config_file: 服务器配置文件路径
            enable_ui: 是否启用UI界面
            max_workers: 最大工作线程数
        """
        self.config_file = config_file
        self.manager = RemoteManager(config_file=config_file, enable_ui=enable_ui)
        self.servers = self._load_servers()
        self.max_workers = max_workers
        
        # 设置日志记录器
        self.logger = logging.getLogger('SATuSGH.Manager')
        
        # 服务器状态管理（线程安全）
        self.server_status_lock = threading.Lock()
        self.server_status = {}
        for server_name in self.servers.keys():
            with self.server_status_lock:
                self.server_status[server_name] = "idle"  # 初始都为空闲
        
        # 多线程任务管理
        self.task_queue = queue.Queue()
        self.running_tasks: Dict[str, ExperimentTask] = {}
        self.completed_tasks: Dict[str, ExperimentTask] = {}
        self.task_lock = threading.Lock()
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.worker_threads = []
        
        # 控制标志
        self.shutdown_event = threading.Event()
        self.is_running = False

    # ==================== 多线程任务管理 ====================
    
    def start_worker_threads(self):
        """启动工作线程"""
        if self.is_running:
            self.logger.warning("⚠️  工作线程已在运行")
            return
        
        self.is_running = True
        self.shutdown_event.clear()
        
        # 清空之前的线程列表
        self.worker_threads.clear()
        
        # 启动工作线程
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_thread,
                name=f"Worker-{i+1}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        self.logger.info(f"🚀 启动了 {self.max_workers} 个工作线程")
    
    def stop_worker_threads(self):
        """停止工作线程"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 正在停止工作线程...")
        self.is_running = False
        self.shutdown_event.set()
        
        # 等待所有工作线程结束
        for worker in self.worker_threads:
            worker.join(timeout=5)
        
        self.executor.shutdown(wait=True)
        self.logger.info("✅ 所有工作线程已停止")
    
    def _worker_thread(self):
        """工作线程主函数"""
        thread_name = threading.current_thread().name
        self.logger.info(f"🚀 {thread_name} 启动")
        
        while not self.shutdown_event.is_set():
            try:
                # 从队列中获取任务，超时1秒
                task = self.task_queue.get(timeout=1)
                if task is None:  # 停止信号
                    break
                
                self.logger.info(f"🔄 {thread_name} 开始处理任务 {task.task_id}")
                
                # 执行任务
                self._execute_experiment_task(task)
                
                # 标记任务完成
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"❌ {thread_name} 工作线程出错: {e}")
                import traceback
                self.logger.error(f"详细错误信息: {traceback.format_exc()}")
        
        self.logger.info(f"🛑 {thread_name} 退出")
    
    def _execute_experiment_task(self, task: ExperimentTask):
        """
        执行单个实验任务
        
        Args:
            task: 实验任务
        """
        try:
            # 更新任务状态
            with self.task_lock:
                task.status = "running"
                task.start_time = datetime.now()
                self.running_tasks[task.task_id] = task
            
            self.logger.info(f"🔬 开始执行任务 {task.task_id}: delta_t1={task.delta_t1}, delta_t2={task.delta_t2}")
            
            # 执行实验
            success = self._run_single_experiment(task)
            
            # 更新任务状态
            with self.task_lock:
                task.end_time = datetime.now()
                if success:
                    task.status = "completed"
                    self.completed_tasks[task.task_id] = task
                    self.logger.info(f"✅ 任务 {task.task_id} 执行完成")
                else:
                    task.status = "failed"
                    self.completed_tasks[task.task_id] = task
                    self.logger.error(f"❌ 任务 {task.task_id} 执行失败, error_message: {task.error_message}")
                
                if task.task_id in self.running_tasks:
                    del self.running_tasks[task.task_id]
            
        except Exception as e:
            with self.task_lock:
                task.status = "failed"
                task.error_message = str(e)
                task.end_time = datetime.now()
                self.completed_tasks[task.task_id] = task
                if task.task_id in self.running_tasks:
                    del self.running_tasks[task.task_id]
            
            self.logger.error(f"❌ 任务 {task.task_id} 执行出错: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    def _run_single_experiment(self, task: ExperimentTask) -> bool:
        """
        运行单个实验（线程安全版本）
        
        Args:
            task: 实验任务
            
        Returns:
            是否执行成功
        """
        try:
            # 1. 构建实验环境
            labbook_output_dir = task.output_dir
            
            if not os.path.exists(labbook_output_dir):
                labgen = SATuSGHLabGen(
                    output_dir=labbook_output_dir,
                    link_delete_offset=task.delta_t1,
                    link_create_offset=task.delta_t2
                )
                labgen.init_network()
                labgen.add_core_network_actions()
                labgen.build()
            
            # 2. 分配服务器
            selected_server = self._wait_for_idle_server()
            if not selected_server:
                task.error_message = "无法获取可用服务器"
                return False
            
            task.server_name = selected_server
            selected_server_ip = self.servers[selected_server].get("host")
            if not selected_server_ip:
                task.error_message = f"无法获取服务器 {selected_server} 的 IP"
                self.release_server(selected_server)
                return False
            
            # 3. 上传实验文件
            remote_labbook_dir = f"/tmp/{os.path.basename(labbook_output_dir)}"
            upload_success = self.manager.upload_directory(selected_server, labbook_output_dir, remote_labbook_dir)
            
            if not upload_success:
                task.error_message = "实验文件上传失败"
                self.release_server(selected_server)
                return False
            
            # 4. 清理本地文件
            self._cleanup_local_files(labbook_output_dir)
            
            # 5. 执行实验（异步）
            command = f"{LABX_PATH} -ip {selected_server_ip} -port {SERVER_PORT} -book {remote_labbook_dir}"
            
            # 使用线程池执行命令
            future = self.executor.submit(self._execute_command_async, selected_server, command)
            
            # 等待执行完成或超时
            try:
                result = future.result(timeout=EXPERIMENT_TIMEOUT)
                if not result:
                    task.error_message = "实验执行失败"
                    self.release_server(selected_server)
                    return False
            except Exception as e:
                task.error_message = f"实验执行超时或出错: {e}"
                self.release_server(selected_server)
                return False
            
            # 6. 下载实验结果
            download_success = self.manager.sync_directory(selected_server, remote_labbook_dir, labbook_output_dir)
            if not download_success:
                task.error_message = "结果下载失败"
                self.release_server(selected_server)
                return False
            
            # 7. 释放服务器
            self.release_server(selected_server)
            
            # 8. 分析结果
            analyze_labbook_output(labbook_output_dir)
            
            return True
            
        except Exception as e:
            task.error_message = str(e)
            if task.server_name:
                self.release_server(task.server_name)
            return False
    
    def _execute_command_async(self, server_name: str, command: str) -> bool:
        """
        异步执行命令
        
        Args:
            server_name: 服务器名称
            command: 要执行的命令
            
        Returns:
            是否执行成功
        """
        try:
            if self.manager.connect_server(server_name):
                result = self.manager.execute_command(server_name, command)
                return result and result.get('success', False)
            return False
        except Exception:
            return False
    
    def submit_experiment(self, output_dir: str, delta_t1: int, delta_t2: int) -> str:
        """
        提交实验任务到队列
        
        Args:
            output_dir: 输出目录
            delta_t1: 链路删除时间偏移量（毫秒）
            delta_t2: 链路创建时间偏移量（毫秒）
            
        Returns:
            任务ID
        """
        # 使用更精确的时间戳和随机数避免重复
        import random
        task_id = f"exp_{int(time.time() * 1000)}_{random.randint(1000, 9999)}_{delta_t1}_{delta_t2}"
        task = ExperimentTask(
            task_id=task_id,
            output_dir=output_dir,
            delta_t1=delta_t1,
            delta_t2=delta_t2,
            created_time=datetime.now()
        )
        
        self.task_queue.put(task)
        self.logger.info(f"📋 提交任务 {task_id} 到队列")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[ExperimentTask]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回 None
        """
        with self.task_lock:
            # 检查运行中的任务
            if task_id in self.running_tasks:
                return self.running_tasks[task_id]
            
            # 检查已完成的任务
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            
            return None
    
    def get_all_tasks(self) -> Dict[str, List[ExperimentTask]]:
        """
        获取所有任务状态
        
        Returns:
            任务状态字典
        """
        with self.task_lock:
            return {
                "running": list(self.running_tasks.values()),
                "completed": list(self.completed_tasks.values())
            }
    
    def wait_for_task_completion(self, task_id: str, timeout: int = 86400 * 7) -> bool:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），默认7天
            
        Returns:
            是否在超时前完成
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            task = self.get_task_status(task_id)
            if task and task.status in ["completed", "failed"]:
                return True
            time.sleep(1)
        return False
    
    def get_debug_info(self) -> Dict[str, Any]:
        """
        获取调试信息
        
        Returns:
            调试信息字典
        """
        with self.task_lock:
            return {
                "queue_size": self.task_queue.qsize(),
                "running_tasks_count": len(self.running_tasks),
                "completed_tasks_count": len(self.completed_tasks),
                "worker_threads_count": len(self.worker_threads),
                "max_workers": self.max_workers,
                "server_count": len(self.servers),
                "is_running": self.is_running,
                "shutdown_event_set": self.shutdown_event.is_set(),
                "running_tasks": list(self.running_tasks.keys()),
                "completed_tasks": [t.task_id for t in self.completed_tasks.values()]
            }
    
    def adjust_worker_threads(self, new_max_workers: int):
        """
        动态调整工作线程数量
        
        Args:
            new_max_workers: 新的最大工作线程数
        """
        if new_max_workers <= 0:
            print("❌ 工作线程数必须大于0")
            return
        
        if new_max_workers == self.max_workers:
            print(f"ℹ️  工作线程数已经是 {new_max_workers}")
            return
        
        print(f"🔄 调整工作线程数: {self.max_workers} → {new_max_workers}")
        
        # 停止当前工作线程
        self.stop_worker_threads()
        
        # 更新配置
        self.max_workers = new_max_workers
        self.executor = ThreadPoolExecutor(max_workers=new_max_workers)
        
        # 重新启动工作线程
        self.start_worker_threads()
        
        print(f"✅ 工作线程数调整完成: {new_max_workers}")

    # ==================== 服务器状态管理 ====================
    
    def get_idle_server(self) -> Optional[str]:
        """
        获取一个空闲的服务器
        
        Returns:
            空闲服务器名称，如果没有则返回 None
        """
        with self.server_status_lock:
            for name, status in self.server_status.items():
                if status == "idle":
                    self.server_status[name] = "busy"
                    return name
            return None
    
    def release_server(self, server_name: str):
        """
        释放服务器，将其状态设置为空闲
        
        Args:
            server_name: 服务器名称
        """
        with self.server_status_lock:
            if server_name in self.server_status:
                self.server_status[server_name] = "idle"

    def get_busy_servers(self) -> List[str]:
        """
        获取所有正在执行任务的服务器列表
        
        Returns:
            忙碌服务器名称列表
        """
        with self.server_status_lock:
            return [name for name, status in self.server_status.items() if status == "busy"]

    def is_server_idle(self, server_name: str) -> bool:
        """
        判断服务器是否空闲
        
        Args:
            server_name: 服务器名称
            
        Returns:
            是否空闲
        """
        with self.server_status_lock:
            return self.server_status.get(server_name) == "idle"

    def is_server_busy(self, server_name: str) -> bool:
        """
        判断服务器是否正在执行任务
        
        Args:
            server_name: 服务器名称
            
        Returns:
            是否忙碌
        """
        with self.server_status_lock:
            return self.server_status.get(server_name) == "busy"
    
    # ==================== 配置管理 ====================
    
    def _load_servers(self) -> Dict[str, Any]:
        """
        加载服务器配置
        
        Returns:
            服务器配置字典
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"❌ 配置文件 {self.config_file} 不存在")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"❌ 配置文件 {self.config_file} 格式错误")
            return {}
        except Exception as e:
            self.logger.error(f"❌ 加载配置文件时出错: {e}")
            return {}
    
    def setup_servers(self) -> bool:
        """
        设置服务器连接
        
        Returns:
            是否成功设置
        """
        if not self.servers:
            self.logger.error("❌ 没有可用的服务器配置")
            return False
        
        success_count = 0
        for server_name, config in self.servers.items():
            try:
                success = self.manager.add_server(
                    name=server_name,
                    host=config['host'],
                    user=config['user'],
                    port=config.get('port', 22),
                    password=config.get('password'),
                    key_filename=config.get('key_filename')
                )
                
                if success:
                    success_count += 1
                    self.logger.info(f"✅ 服务器 {server_name} 添加成功")
                else:
                    self.logger.error(f"❌ 服务器 {server_name} 添加失败")
                    
            except Exception as e:
                self.logger.error(f"❌ 添加服务器 {server_name} 时出错: {e}")
        
        self.logger.info(f"📊 成功添加 {success_count}/{len(self.servers)} 个服务器")
        return success_count > 0
    
    # ==================== 远程命令执行 ====================
    
    def execute_command_on_all(self, command: str):
        """
        在所有服务器上执行命令
        
        Args:
            command: 要执行的命令
        """
        self.logger.info(f"🔄 在所有服务器上执行命令: {command}")
        
        for server_name in self.servers.keys():
            self.logger.info(f"\n🔸 服务器: {server_name}")
            
            if self.manager.connect_server(server_name):
                result = self.manager.execute_command(server_name, command)
                
                if result and result.get('success'):
                    self.logger.info(f"✅ 执行成功")
                    if result.get('stdout'):
                        self.logger.info(f"输出: {result['stdout'].strip()}")
                else:
                    error_msg = result.get('stderr', '未知错误') if result else '执行失败'
                    self.logger.error(f"❌ 执行失败: {error_msg}")
            else:
                self.logger.error(f"❌ 无法连接到服务器 {server_name}")
    
    def execute_command_on_server(self, server_name: str, command: str):
        """
        在指定服务器上执行命令
        
        Args:
            server_name: 服务器名称
            command: 要执行的命令
        """
        if server_name not in self.servers:
            print(f"❌ 服务器 {server_name} 不在配置文件中")
            return
        
        print(f"🔄 在服务器 {server_name} 上执行命令: {command}")
        
        if self.manager.connect_server(server_name):
            result = self.manager.execute_command(server_name, command)
            
            if result and result.get('success'):
                print(f"✅ 执行成功")
                if result.get('stdout'):
                    print(f"输出: {result['stdout'].strip()}")
            else:
                error_msg = result.get('stderr', '未知错误') if result else '执行失败'
                print(f"❌ 执行失败: {error_msg}")
        else:
            print(f"❌ 无法连接到服务器 {server_name}")
    
    # ==================== 系统信息获取 ====================
    
    def get_system_info(self):
        """获取所有服务器的系统信息"""
        print("📊 获取所有服务器系统信息...")
        
        for server_name in self.servers.keys():
            print(f"\n🔸 服务器: {server_name}")
            
            if self.manager.connect_server(server_name):
                info = self.manager.get_system_info(server_name)
                if info:
                    for key, value in info.items():
                        print(f"   {key}: {value}")
                else:
                    print("   ❌ 获取系统信息失败")
            else:
                print("   ❌ 连接失败")
    
    # ==================== 文件传输操作 ====================
    
    def upload_file(self, server_name: str, local_path: str, remote_path: str):
        """
        上传文件到指定服务器
        
        Args:
            server_name: 服务器名称
            local_path: 本地文件路径
            remote_path: 远程文件路径
        """
        if server_name not in self.servers:
            print(f"❌ 服务器 {server_name} 不在配置文件中")
            return
        
        print(f"🔄 上传文件到服务器 {server_name}: {local_path} -> {remote_path}")
        
        if self.manager.connect_server(server_name):
            success = self.manager.upload_file(server_name, local_path, remote_path)
            if success:
                print(f"✅ 文件上传成功")
            else:
                print(f"❌ 文件上传失败")
        else:
            print(f"❌ 无法连接到服务器 {server_name}")
    
    def upload_directory(self, server_name: str, local_dir: str, remote_dir: str):
        """
        上传目录到指定服务器
        
        Args:
            server_name: 服务器名称
            local_dir: 本地目录路径
            remote_dir: 远程目录路径
        """
        if server_name not in self.servers:
            print(f"❌ 服务器 {server_name} 不在配置文件中")
            return
        
        print(f"🔄 上传目录到服务器 {server_name}: {local_dir} -> {remote_dir}")

        if self.manager.connect_server(server_name):
            success = self.manager.upload_directory(server_name, local_dir, remote_dir)
            if success:
                print(f"✅ 目录上传成功")
            else:
                print(f"❌ 目录上传失败")
        else:
            print(f"❌ 无法连接到服务器 {server_name}")
    
    def download_file(self, server_name: str, remote_path: str, local_path: str):
        """
        从指定服务器下载文件
        
        Args:
            server_name: 服务器名称
            remote_path: 远程文件路径
            local_path: 本地文件路径
        """
        if server_name not in self.servers:
            print(f"❌ 服务器 {server_name} 不在配置文件中")
            return
        
        print(f"🔄 从服务器 {server_name} 下载文件: {remote_path} -> {local_path}")
        
        if self.manager.connect_server(server_name):
            success = self.manager.download_file(server_name, remote_path, local_path)
            if success:
                print(f"✅ 文件下载成功")
            else:
                print(f"❌ 文件下载失败")
        else:
            print(f"❌ 无法连接到服务器 {server_name}")
    
    def download_directory(self, server_name: str, remote_dir: str, local_dir: str):
        """
        从指定服务器下载目录
        
        Args:
            server_name: 服务器名称
            remote_dir: 远程目录路径
            local_dir: 本地目录路径
        """
        if server_name not in self.servers:
            print(f"❌ 服务器 {server_name} 不在配置文件中")
            return
        
        print(f"🔄 从服务器 {server_name} 下载目录: {remote_dir} -> {local_dir}")
        
        if self.manager.connect_server(server_name):
            success = self.manager.sync_directory(server_name, remote_dir, local_dir)
            if success:
                print(f"✅ 目录下载成功")
            else:
                print(f"❌ 目录下载失败")
        else:
            print(f"❌ 无法连接到服务器 {server_name}")
    
    # ==================== 实验执行（兼容旧版本） ====================
    
    def run_experiment(self, output_dir: str, delta_t1: int, delta_t2: int):
        """
        运行完整的实验流程（串行版本，保持向后兼容）
        
        Args:
            output_dir: 输出目录
            delta_t1: 链路删除时间偏移量（毫秒）
            delta_t2: 链路创建时间偏移量（毫秒）
        """
        self.logger.info(f"🚀 开始运行实验: delta_t1={delta_t1}, delta_t2={delta_t2}")
        self.logger.info("=" * 60)
        
        # 1. 构建实验环境
        self.logger.info("📋 构建实验环境...")
        labbook_output_dir = output_dir

        # 检查是否已存在，避免重复生成
        if os.path.exists(labbook_output_dir):
            self.logger.info(f"📁 实验目录已存在: {labbook_output_dir}，跳过生成步骤")
        else:
            self.logger.info(f"📁 创建实验目录: {labbook_output_dir}")
            
            # 初始化实验生成器
            labgen = SATuSGHLabGen(
                output_dir=labbook_output_dir,
                link_delete_offset=delta_t1,
                link_create_offset=delta_t2
            )
            
            # 构建实验环境
            labgen.init_network()
            labgen.add_core_network_actions()
            labgen.build()
            self.logger.info("✅ 实验环境构建完成")

        # 2. 分配服务器并执行实验
        print("\n🖥️  分配服务器...")
        selected_server = self._wait_for_idle_server()
        if not selected_server:
            print("❌ 无法获取可用服务器，实验终止")
            return
        
        selected_server_ip = self.servers[selected_server].get("host")
        if not selected_server_ip:
            print(f"❌ 无法获取服务器 {selected_server} 的 IP，实验终止")
            self.release_server(selected_server)
            return
        
        print(f"✅ 分配到服务器: {selected_server} ({selected_server_ip})")
        
        # 3. 上传实验文件
        print("\n📤 上传实验文件...")
        remote_labbook_dir = f"/tmp/{os.path.basename(labbook_output_dir)}"
        upload_success = self.manager.upload_directory(selected_server, labbook_output_dir, remote_labbook_dir)
        
        if not upload_success:
            print(f"❌ 实验文件上传失败")
            self.release_server(selected_server)
            return
        
        print(f"✅ 实验文件上传成功: {remote_labbook_dir}")
        
        # 4. 清理本地文件
        self._cleanup_local_files(labbook_output_dir)
        
        # 5. 执行实验
        print(f"\n🔬 在服务器 {selected_server} 上执行实验...")
        start_time = time.time()
        
        self.execute_command_on_server(
            selected_server, 
            f"{LABX_PATH} -ip {selected_server_ip} -port {SERVER_PORT} -book {remote_labbook_dir}"
        )
        
        execution_time = time.time() - start_time
        print(f"✅ 实验执行完成，耗时: {execution_time:.2f} 秒")
        
        # 6. 下载实验结果
        print(f"\n📥 下载实验结果...")
        start_time = time.time()
        self.download_directory(selected_server, remote_labbook_dir, labbook_output_dir)
        download_time = time.time() - start_time
        print(f"✅ 结果下载完成，耗时: {download_time:.2f} 秒")
        
        # 7. 释放服务器
        self.release_server(selected_server)
        print(f"✅ 释放服务器: {selected_server}")
        
        # 8. 分析结果
        print("\n📊 分析实验结果...")
        analyze_labbook_output(labbook_output_dir)
        
        print("=" * 60)
        print("🎉 实验完成！")
    
    def _wait_for_idle_server(self) -> Optional[str]:
        """
        等待直到有空闲服务器可用
        
        Returns:
            空闲服务器名称，如果超时则返回 None
        """
        wait_time = 0
        max_wait_time = 86400 * 7  # 最大等待7天（一周）
        
        while wait_time < max_wait_time:
            selected_server = self.get_idle_server()
            if selected_server:
                return selected_server
            
            print("⏳ 没有空闲的服务器可用，等待中...")
            time.sleep(5)
            wait_time += 5
        
        print(f"❌ 等待超时（{max_wait_time}秒），没有可用服务器")
        return None
    
    def _cleanup_local_files(self, labbook_output_dir: str):
        """
        清理本地实验文件
        
        Args:
            labbook_output_dir: 实验输出目录
        """
        # 确保本地目录在安全路径下
        if not os.path.abspath(labbook_output_dir).startswith("/home/cnic/"):
            print(f"⚠️  本地实验目录 {labbook_output_dir} 不在安全路径下，跳过清理")
            return
        
        try:
            if os.path.exists(labbook_output_dir):
                shutil.rmtree(labbook_output_dir)
                print(f"🗑️  已删除本地实验目录: {labbook_output_dir}")
        except Exception as e:
            print(f"⚠️  删除本地实验目录时出错: {e}")


def analyze_labbook_output(labbook_output_dir: str):
    """
    分析实验输出结果
    
    使用 PingAnalyzer 分析 ping 数据，生成详细的统计报告
    
    Args:
        labbook_output_dir: 实验输出目录
    """
    import glob
    import gc
    
    # 获取日志记录器
    logger = logging.getLogger('SATuSGH.Analyzer')
    
    logger.info(f"🔍 开始分析实验输出: {labbook_output_dir}")
    
    # 查找 ping 输出文件
    outputs_dir = os.path.join(labbook_output_dir, "outputs")
    if not os.path.exists(outputs_dir):
        logger.error(f"❌ 输出目录不存在: {outputs_dir}")
        return
    
    # 查找所有 .out 文件
    ping_files = glob.glob(os.path.join(outputs_dir, "*.out"))
    if not ping_files:
        logger.error(f"❌ 在 {outputs_dir} 中没有找到 .out 文件")
        return
    
    logger.info(f"📄 找到 {len(ping_files)} 个 ping 输出文件:")
    for f in ping_files:
        logger.info(f"  - {os.path.basename(f)}")
    
    # 分析所有 ping 文件
    all_results = {}
    total_stats = {
        'total_files': len(ping_files),
        'total_outages': 0,
        'total_outage_duration': 0,
        'total_data_points': 0,
        'total_success_points': 0,
        'total_error_points': 0
    }
    
    # 逐个分析文件
    for ping_file in ping_files:
        filename = os.path.basename(ping_file)
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 分析文件: {filename}")
        logger.info(f"{'='*60}")
        
        try:
            # 创建分析器实例
            analyzer = PingAnalyzer()
            if analyzer.parse_file(ping_file):
                analyzer.analyze_outages(min_outage_duration=1.0)
                analyzer.print_summary()
                
                # 保存单个文件结果
                all_results[filename] = {
                    'stats': analyzer.stats,
                    'outages': analyzer.outages,
                    'data_points_count': len(analyzer.data_points)
                }
                
                # 累计统计
                total_stats['total_outages'] += analyzer.stats.get('outage_count', 0)
                total_stats['total_outage_duration'] += analyzer.stats.get('total_outage_duration', 0)
                total_stats['total_data_points'] += analyzer.stats.get('total_points', 0)
                total_stats['total_success_points'] += analyzer.stats.get('success_points', 0)
                total_stats['total_error_points'] += analyzer.stats.get('error_points', 0)
            
            # 清理分析器资源
            del analyzer
            gc.collect()
            
        except Exception as e:
            logger.error(f"❌ 分析文件 {filename} 时出错: {e}")
            continue
    
    # 计算总体统计
    if total_stats['total_data_points'] > 0:
        total_stats['overall_success_rate'] = total_stats['total_success_points'] / total_stats['total_data_points'] * 100
    else:
        total_stats['overall_success_rate'] = 0
    
    if total_stats['total_outages'] > 0:
        total_stats['avg_outage_duration'] = total_stats['total_outage_duration'] / total_stats['total_outages']
    else:
        total_stats['avg_outage_duration'] = 0
    
    # 打印总体摘要
    logger.info(f"\n{'='*60}")
    logger.info("📈 实验分析总体摘要")
    logger.info(f"{'='*60}")
    
    logger.info(f"📁 分析文件数: {total_stats['total_files']}")
    logger.info(f"📊 总数据点: {total_stats['total_data_points']}")
    logger.info(f"✅ 总成功响应: {total_stats['total_success_points']}")
    logger.info(f"❌ 总错误响应: {total_stats['total_error_points']}")
    logger.info(f"📈 总体成功率: {total_stats['overall_success_rate']:.2f}%")
    logger.info(f"🔴 总中断次数: {total_stats['total_outages']}")
    logger.info(f"⏱️  总中断时间: {total_stats['total_outage_duration']:.2f} 秒")
    logger.info(f"📊 平均中断时间: {total_stats['avg_outage_duration']:.2f} 秒")
    
    # 保存分析结果
    results = {
        'labbook_dir': labbook_output_dir,
        'summary': total_stats,
        'files': all_results
    }
    
    # 生成结果文件名
    labbook_name = os.path.basename(labbook_output_dir)
    results_file = os.path.join(labbook_output_dir, f"{labbook_name}_ping_analysis.json")
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 分析结果已保存到: {results_file}")
    except Exception as e:
        logger.error(f"❌ 保存分析结果时出错: {e}")
    
    # 强制垃圾回收
    gc.collect()


# ==================== 主函数 ====================

if __name__ == "__main__":
    """
    主函数 - 多线程批量实验执行示例
    
    演示如何使用多线程功能执行批量实验
    """
    
    logger.info("🚀 SATuSGH 多线程实验管理器启动")
    logger.info(f"📝 日志文件路径: {log_file_path}")
    logger.info("=" * 60)
    
    # 创建管理器（启用多线程）
    # 根据服务器数量设置工作线程数，每个服务器可以运行一个实验
    manager = SATuSGHManager(config_file="configs/servers.json", enable_ui=False)
    
    # 获取服务器数量并设置工作线程数
    server_count = len(manager.servers)
    if server_count > 0:
        # 根据服务器数量动态设置工作线程数
        max_workers = min(server_count * MAX_WORKERS_PER_SERVER, MAX_TOTAL_WORKERS)
        logger.info(f"📊 检测到 {server_count} 个服务器，设置 {max_workers} 个工作线程")
        manager.max_workers = max_workers
        manager.executor = ThreadPoolExecutor(max_workers=max_workers)
    else:
        logger.warning("⚠️  没有检测到服务器，使用默认4个工作线程")
    
    # 设置服务器连接
    if not manager.setup_servers():
        logger.error("❌ 服务器设置失败，退出")
        exit(1)
    
    # 启动工作线程
    manager.start_worker_threads()
    
    try:
        # 执行批量实验（多线程版本）
        logger.info("\n🔬 开始执行批量实验（多线程）...")
        # DELTA_MAX_1000 = 1000
        # DELTA_MAX_2000 = 2000
        # DELTA_MAX_3000 = 3000
        # DELTA_MAX_4000 = 4000
        # DELTA_MAX_5000 = 5000
        # SLOT_COUNT = 20
        groups = []
        # for delta_max in [DELTA_MAX_5000]:
        #     sub_groups = [(f"ospf_1_bfd/book_{delta_max}/book_{delta_max}_{int(i * delta_max / SLOT_COUNT)}_{int(j * delta_max / SLOT_COUNT)}_{z}", int(i * delta_max / SLOT_COUNT), int(j * delta_max / SLOT_COUNT)) for z in range(3) for i in range(SLOT_COUNT + 1) for j in range(SLOT_COUNT + 1)]
        #     groups.extend(sub_groups)
        for i in range(380):
            groups.append((f"ospf_1_bfd/book_0/book_0_{620+i}", 0, 0))
        submitted_tasks = []
        
        # 提交所有任务
        for i, group in enumerate(groups):
            task_id = manager.submit_experiment(
                f"labbooks/{group[0]}", 
                group[1], 
                group[2]    
            )
            submitted_tasks.append(task_id)
            logger.info(f"📋 已提交任务 {i+1}/{len(groups)}: {task_id}")
        
        # 等待所有任务完成
        logger.info(f"\n⏳ 等待 {len(submitted_tasks)} 个任务完成...")
        completed_count = 0
        last_completed_count = 0
        stuck_count = 0
        
        while completed_count < len(submitted_tasks):
            tasks = manager.get_all_tasks()
            completed_count = len(tasks["completed"])
            running_count = len(tasks["running"])
            
            # 检查是否卡住
            if completed_count == last_completed_count:
                stuck_count += 1
                if stuck_count > 6:  # 1分钟后显示调试信息
                    logger.warning("⚠️  任务进度停滞，显示调试信息:")
                    debug_info = manager.get_debug_info()
                    logger.info(f"  - 服务器数量: {debug_info['server_count']}")
                    logger.info(f"  - 最大工作线程数: {debug_info['max_workers']}")
                    logger.info(f"  - 当前工作线程数: {debug_info['worker_threads_count']}")
                    logger.info(f"  - 队列大小: {debug_info['queue_size']}")
                    logger.info(f"  - 运行中任务: {debug_info['running_tasks_count']}")
                    logger.info(f"  - 已完成任务: {debug_info['completed_tasks_count']}")
                    logger.info(f"  - 线程池运行状态: {debug_info['is_running']}")
                    if debug_info['running_tasks']:
                        logger.info(f"  - 运行中的任务: {debug_info['running_tasks']}")
                    stuck_count = 0  # 重置计数器
            else:
                stuck_count = 0
            
            # 显示进度变化
            if completed_count > last_completed_count:
                logger.info(f"🎉 新完成 {completed_count - last_completed_count} 个任务!")
                last_completed_count = completed_count
            
            logger.info(f"📊 进度: {completed_count}/{len(submitted_tasks)} 完成, {running_count} 运行中")
            
            # 显示运行中的任务
            if tasks["running"]:
                logger.info("🔄 运行中的任务:")
                for task in tasks["running"]:
                    duration = (datetime.now() - task.start_time).total_seconds() if task.start_time else 0
                    logger.info(f"  - {task.task_id}: {duration:.1f}秒")
            
            # 显示已完成的任务状态
            if tasks["completed"]:
                recent_completed = [t for t in tasks["completed"] if (datetime.now() - t.end_time).total_seconds() < 60]
                if recent_completed:
                    logger.info("✅ 最近完成的任务:")
                    for task in recent_completed[-3:]:  # 显示最近3个
                        status_emoji = "✅" if task.status == "completed" else "❌"
                        logger.info(f"  {status_emoji} {task.task_id}: {task.status}")
                        if task.error_message:
                            logger.error(f"    错误: {task.error_message}")
            
            time.sleep(10)  # 每10秒检查一次
        
        logger.info("\n🎉 所有实验执行完成！")
        
        # 显示最终统计
        final_tasks = manager.get_all_tasks()
        successful = sum(1 for task in final_tasks["completed"] if task.status == "completed")
        failed = sum(1 for task in final_tasks["completed"] if task.status == "failed")
        
        logger.info(f"📈 最终统计: 成功 {successful} 个, 失败 {failed} 个")
        
    finally:
        # 停止工作线程
        manager.stop_worker_threads()