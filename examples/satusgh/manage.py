#!/usr/bin/env python3
"""
SATuSGH 实验管理器 - LabGrid 版本

使用 LabGrid 框架重新实现 SATuSGH 实验管理功能，包括：
- 基于 LabGrid 的实验生命周期管理
- 多服务器并发执行
- 自动负载均衡和资源管理
- 实验结果分析和存储
"""

import os
import sys
import time
import json
import logging
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# 添加 workspace 目录到 Python 路径
workspace_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, workspace_path)

from labkit.labgrid import (
    create_labgrid, 
    create_experiment_config,
    Lab,
    ExperimentConfig,
    ExperimentResult,
    ExperimentStatus
)
from labkit.labgrid.types import ServerConfig
from util import SATuSGHLabGen, analyze_labbook_output


# ==================== 日志配置 ====================

def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """设置日志配置"""
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"satusgh_labgrid_{timestamp}.log")
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('SATuSGH.LabGrid')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        console_handler = logging.StreamHandler(sys.stdout)
        
        formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger, log_file


# ==================== 常量定义 ====================

# 实验相关常量
DELTA_MAX = 5000  # 最大时间偏移量（毫秒）
LABX_PATH = "/home/cnic/reals/bin/kinexlabx"  # 实验执行器路径
SERVER_PORT = 8080  # 服务器端口

# 实验类型标识
EXPERIMENT_TYPE = "satusgh_experiment"


# ==================== SATuSGH 实验类 ====================

class SATuSGHExperiment(Lab):
    """
    SATuSGH 实验类
    
    继承自 LabGrid 的 Lab 基类，实现完整的实验生命周期管理
    """
    
    def __init__(self, config: ExperimentConfig, labx):
        super().__init__(config, labx)
        self.logger = logging.getLogger('SATuSGH.Experiment')
        self.log("🔬 初始化 SATuSGH 实验")
        
        # 实验参数
        self.delta_t1 = config.parameters.get('delta_t1', 0)
        self.delta_t2 = config.parameters.get('delta_t2', 0)
        self.output_dir = config.output_dir
        
        # 实验状态
        self.labbook_output_dir = None
        self.remote_labbook_dir = None
        
    def initialize(self) -> bool:
        """初始化实验环境"""
        self.log("📋 阶段1: 初始化实验环境")
        
        try:
            # 确保输出目录存在
            if not self.ensure_output_dir():
                return False
            
            # 生成实验环境
            self.labbook_output_dir = self.output_dir
            
            # 检查目录是否存在且包含必要的文件
            if not os.path.exists(self.labbook_output_dir) or not os.path.exists(os.path.join(self.labbook_output_dir, 'network', 'config.yaml')):
                self.log(f"🔧 生成实验环境: delta_t1={self.delta_t1}, delta_t2={self.delta_t2}")
                
                labgen = SATuSGHLabGen(
                    output_dir=self.labbook_output_dir,
                    link_delete_offset=self.delta_t1,
                    link_create_offset=self.delta_t2
                )
                labgen.init_network()
                labgen.add_core_network_actions()
                labgen.build()
                
                self.log("✅ 实验环境生成成功")
            else:
                self.log("✅ 实验环境已存在")
            
            return True
            
        except Exception as e:
            self.log(f"❌ 初始化实验环境失败: {e}", "ERROR")
            return False
    
    def execute(self) -> bool:
        """执行实验"""
        self.log("🔬 阶段2: 执行实验")
        
        if not self.assigned_server:
            self.log("❌ 没有分配服务器", "ERROR")
            return False
        
        try:
            server_name = self.assigned_server
            self.log(f"🚀 在服务器 {server_name} 上执行实验")
            
            # 1. 上传实验文件
            self.remote_labbook_dir = f"/tmp/{os.path.basename(self.labbook_output_dir)}"
            
            if not self.labx.upload_directory(server_name, self.labbook_output_dir, self.remote_labbook_dir):
                self.log("❌ 实验文件上传失败", "ERROR")
                return False
            
            self.log("✅ 实验文件上传成功")
            
            # 2. 验证远程文件和环境
            self.log("🔍 验证远程实验环境...")
            
            # 检查远程目录是否存在
            check_dir_cmd = f"ls -la {self.remote_labbook_dir}"
            dir_result = self.labx.execute_command(server_name, check_dir_cmd, timeout=30)
            if not dir_result or not dir_result.get('success'):
                self.log(f"❌ 远程目录检查失败: {dir_result.get('stderr', '未知错误') if dir_result else '执行失败'}", "ERROR")
                return False
            
            self.log(f"📁 远程目录内容: {dir_result.get('stdout', '')}")
            
            # 检查 kinexlabx 是否存在且有执行权限
            check_labx_cmd = f"ls -la {LABX_PATH}"
            labx_result = self.labx.execute_command(server_name, check_labx_cmd, timeout=30)
            if not labx_result or not labx_result.get('success'):
                self.log(f"❌ kinexlabx 文件检查失败: {labx_result.get('stderr', '未知错误') if labx_result else '执行失败'}", "ERROR")
                return False
            
            self.log(f"🔧 kinexlabx 文件信息: {labx_result.get('stdout', '')}")
            
            # 3. 执行实验命令
            server_ip = self._get_server_ip(server_name)
            if not server_ip:
                self.log("❌ 无法获取服务器IP", "ERROR")
                return False
            
            command = f"{LABX_PATH} -ip {server_ip} -port {SERVER_PORT} -book {self.remote_labbook_dir}"
            self.log(f"🔧 执行命令: {command}")
            
            # 增加命令执行的详细日志
            self.log(f"📍 在服务器 {server_name} ({server_ip}) 上执行")
            self.log(f"📂 实验目录: {self.remote_labbook_dir}")
            
            result = self.labx.execute_command(server_name, command, timeout=self.config.timeout)
            if not result or not result.get('success'):
                error_msg = result.get('stderr', '未知错误') if result else '执行失败'
                stdout_msg = result.get('stdout', '') if result else ''
                exit_code = result.get('exit_code', '未知') if result else '未知'
                self.log(f"❌ 实验执行失败: {error_msg}", "ERROR")
                self.log(f"📤 标准输出: {stdout_msg}")
                self.log(f"🔢 退出码: {exit_code}")
                return False
            
            self.log("✅ 实验执行成功")
            
            # 3. 下载实验结果
            if not self.labx.sync_directory(server_name, self.remote_labbook_dir, self.labbook_output_dir):
                self.log("❌ 结果下载失败", "ERROR")
                return False
            
            self.log("✅ 实验结果下载成功")
            
            return True
            
        except Exception as e:
            self.log(f"❌ 执行实验时出错: {e}", "ERROR")
            return False
    
    def collect_data(self) -> bool:
        """收集实验数据"""
        self.log("📊 阶段3: 收集实验数据")
        
        try:
            # 清理远程文件
            if self.assigned_server and self.remote_labbook_dir:
                self.labx.execute_command(self.assigned_server, f"rm -rf {self.remote_labbook_dir}")
                self.log("✅ 远程文件清理完成")
            
            # 清理本地临时文件
            self._cleanup_local_files()
            
            return True
            
        except Exception as e:
            self.log(f"❌ 收集数据时出错: {e}", "ERROR")
            return False
    
    def analyze_data(self) -> dict:
        """分析实验数据"""
        self.log("📈 阶段4: 分析实验数据")
        
        try:
            # 分析实验结果
            metrics = analyze_labbook_output(self.labbook_output_dir)
            
            self.log(f"✅ 数据分析完成: {metrics}")
            return metrics
            
        except Exception as e:
            self.log(f"❌ 数据分析失败: {e}", "ERROR")
            return {'error': str(e)}
    
    def save_data(self) -> bool:
        """保存实验结果"""
        self.log("💾 阶段5: 保存实验结果")
        
        try:
            # 创建结果摘要文件
            summary_file = os.path.join(self.output_dir, "experiment_summary.json")
            summary = {
                'experiment_id': self.result.experiment_id,
                'delta_t1': self.delta_t1,
                'delta_t2': self.delta_t2,
                'server_name': self.assigned_server,
                'start_time': self.result.start_time.isoformat() if self.result.start_time else None,
                'end_time': self.result.end_time.isoformat() if self.result.end_time else None,
                'duration': self.result.duration,
                'status': self.result.status.value,
                'metrics': self.result.metrics
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            self.log("✅ 实验结果保存成功")
            return True
            
        except Exception as e:
            self.log(f"❌ 保存结果失败: {e}", "ERROR")
            return False
    
    def cleanup(self):
        """清理实验环境"""
        self.log("🧹 阶段6: 清理实验环境")
        
        try:
            # 清理本地文件
            self._cleanup_local_files()
            
            # 调用父类清理方法
            super().cleanup()
            
            self.log("✅ 实验环境清理完成")
            
        except Exception as e:
            self.log(f"❌ 清理环境时出错: {e}", "ERROR")
    
    def _get_server_ip(self, server_name: str) -> Optional[str]:
        """获取服务器IP地址"""
        try:
            # 直接从配置中获取服务器IP
            for name, config in self.labx.servers_config.items():
                if name == server_name:
                    return config.host
            
            return None
            
        except Exception as e:
            self.log(f"❌ 获取服务器IP失败: {e}", "ERROR")
            return None
    
    def _cleanup_local_files(self):
        """清理本地临时文件"""
        try:
            if os.path.exists(self.labbook_output_dir):
                # 保留结果文件，只清理临时文件
                temp_files = ['temp', 'tmp', '.tmp']
                for temp_dir in temp_files:
                    temp_path = os.path.join(self.labbook_output_dir, temp_dir)
                    if os.path.exists(temp_path):
                        import shutil
                        shutil.rmtree(temp_path)
                        self.log(f"✅ 清理临时目录: {temp_dir}")
        except Exception as e:
            self.log(f"⚠️  清理临时文件时出错: {e}", "WARNING")


# ==================== SATuSGH LabGrid 管理器 ====================

class SATuSGHLabGridManager:
    """
    SATuSGH LabGrid 管理器
    
    基于 LabGrid 框架的 SATuSGH 实验管理器
    """
    
    def __init__(self, servers_config_file: str = "configs/servers.json", 
                 framework_config_file: str = None,
                 config_dir: str = "configs"):
        """
        初始化管理器
        
        Args:
            servers_config_file: 服务器配置文件
            framework_config_file: 框架配置文件
            config_dir: 配置目录
        """
        self.logger = logging.getLogger('SATuSGH.LabGridManager')
        self.logger.info("🚀 初始化 SATuSGH LabGrid 管理器")
        
        # 创建 LabGrid 框架实例
        self.labgrid = create_labgrid(
            servers_config_file=servers_config_file,
            framework_config_file=framework_config_file,
            config_dir=config_dir,
            auto_start=True
        )
        
        # 注册实验类型
        self._register_experiment_type()
        
        # 实验统计
        self.total_experiments = 0
        self.completed_experiments = 0
        self.failed_experiments = 0
        
        self.logger.info("✅ SATuSGH LabGrid 管理器初始化完成")
    
    def _register_experiment_type(self):
        """注册实验类型"""
        self.labgrid.register_experiment(
            experiment_type=EXPERIMENT_TYPE,
            experiment_class=SATuSGHExperiment,
            description="SATuSGH 卫星网络拓扑实验",
            tags=["satellite", "network", "topology", "satusgh"]
        )
        self.logger.info(f"✅ 注册实验类型: {EXPERIMENT_TYPE}")
    
    def submit_experiment(self, output_dir: str, delta_t1: int, delta_t2: int, 
                         timeout: int = 3600, priority: int = 0) -> str:
        """
        提交实验任务
        
        Args:
            output_dir: 输出目录
            delta_t1: 链路删除时间偏移量（毫秒）
            delta_t2: 链路创建时间偏移量（毫秒）
            timeout: 超时时间（秒）
            priority: 优先级
            
        Returns:
            任务ID
        """
        try:
            # 创建实验配置
            config = create_experiment_config(
                experiment_type=EXPERIMENT_TYPE,
                output_dir=output_dir,
                parameters={
                    'delta_t1': delta_t1,
                    'delta_t2': delta_t2
                },
                timeout=timeout,
                priority=priority,
                description=f"SATuSGH实验: delta_t1={delta_t1}, delta_t2={delta_t2}"
            )
            
            # 运行实验
            task_id = self.labgrid.run_experiment(EXPERIMENT_TYPE, config)
            
            self.total_experiments += 1
            self.logger.info(f"📋 提交实验任务 {task_id}: delta_t1={delta_t1}, delta_t2={delta_t2}")
            
            return task_id
            
        except Exception as e:
            self.logger.error(f"❌ 提交实验任务失败: {e}")
            raise
    
    def submit_batch_experiments(self, experiments: List[Dict[str, Any]]) -> List[str]:
        """
        批量提交实验任务
        
        Args:
            experiments: 实验配置列表，每个元素包含 output_dir, delta_t1, delta_t2
            
        Returns:
            任务ID列表
        """
        task_ids = []
        
        for exp in experiments:
            try:
                task_id = self.submit_experiment(
                    output_dir=exp['output_dir'],
                    delta_t1=exp['delta_t1'],
                    delta_t2=exp['delta_t2'],
                    timeout=exp.get('timeout', 3600),
                    priority=exp.get('priority', 0)
                )
                task_ids.append(task_id)
                
            except Exception as e:
                self.logger.error(f"❌ 提交实验 {exp} 失败: {e}")
        
        self.logger.info(f"📋 批量提交了 {len(task_ids)} 个实验任务")
        return task_ids
    
    def wait_for_experiment(self, task_id: str, timeout: int = None) -> bool:
        """
        等待实验完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            
        Returns:
            是否在超时前完成
        """
        try:
            return self.labgrid.wait_for_experiment(task_id, timeout=timeout)
        except Exception as e:
            self.logger.error(f"❌ 等待实验 {task_id} 时出错: {e}")
            return False
    
    def get_experiment_result(self, task_id: str) -> Optional[ExperimentResult]:
        """
        获取实验结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            实验结果，如果不存在则返回 None
        """
        try:
            return self.labgrid.get_experiment_result(task_id)
        except Exception as e:
            self.logger.error(f"❌ 获取实验结果 {task_id} 时出错: {e}")
            return None
    
    def get_all_tasks(self) -> Dict[str, List]:
        """获取所有任务状态"""
        try:
            return self.labgrid.get_all_tasks()
        except Exception as e:
            self.logger.error(f"❌ 获取任务状态时出错: {e}")
            return {}
    
    def get_framework_status(self) -> Dict[str, Any]:
        """获取框架状态"""
        try:
            return self.labgrid.get_framework_info()
        except Exception as e:
            self.logger.error(f"❌ 获取框架状态时出错: {e}")
            return {}
    
    def print_status(self):
        """打印框架状态"""
        try:
            self.labgrid.print_status()
        except Exception as e:
            self.logger.error(f"❌ 打印状态时出错: {e}")
    
    def stop(self):
        """停止管理器"""
        self.logger.info("🛑 停止 SATuSGH LabGrid 管理器")
        try:
            self.labgrid.stop()
            self.logger.info("✅ 管理器已停止")
        except Exception as e:
            self.logger.error(f"❌ 停止管理器时出错: {e}")


# ==================== 主函数和示例 ====================

def main():
    """主函数示例"""
    # 设置日志
    logger, log_file = setup_logging()
    logger.info("🚀 启动 SATuSGH LabGrid 示例")
    
    try:
        # 创建管理器
        manager = SATuSGHLabGridManager(
            servers_config_file="servers.json",
            config_dir="configs"
        )
        
        # 打印框架状态
        manager.print_status()
        
        # 批量提交20组实验
        logger.info("📋 开始提交20组实验...")
        
        # 定义实验参数组合
        experiments = []
        
        # 基础网络拓扑实验 (5组)
        for i in range(5):
            experiments.append({
                "output_dir": f"results/basic_topology_{i+1}",
                "delta_t1": 0,
                "delta_t2": 0,
                "timeout": 1800,
                "priority": 5
            })
        
        # 链路切换实验 (8组) - 不同的时间偏移组合
        time_offsets = [
            (500, 1000), (1000, 2000), (1500, 3000), (2000, 4000),
            (1000, 1500), (2000, 3000), (3000, 4500), (4000, 6000)
        ]
        
        for i, (t1, t2) in enumerate(time_offsets):
            experiments.append({
                "output_dir": f"results/link_switch_{i+1}",
                "delta_t1": t1,
                "delta_t2": t2,
                "timeout": 1800,
                "priority": 6
            })
        
        # 负载测试实验 (4组) - 快速切换
        for i in range(4):
            experiments.append({
                "output_dir": f"results/load_test_{i+1}",
                "delta_t1": 200 + i * 100,
                "delta_t2": 500 + i * 200,
                "timeout": 2400,
                "priority": 7
            })
        
        # 稳定性测试实验 (3组) - 长时间运行
        for i in range(3):
            experiments.append({
                "output_dir": f"results/stability_test_{i+1}",
                "delta_t1": 1000 + i * 500,
                "delta_t2": 2000 + i * 1000,
                "timeout": 3600,
                "priority": 4
            })
        
        # 批量提交实验
        submitted_tasks = []
        for i, exp_config in enumerate(experiments):
            try:
                task_id = manager.submit_experiment(**exp_config)
                submitted_tasks.append({
                    "task_id": task_id,
                    "config": exp_config,
                    "index": i + 1
                })
                logger.info(f"✅ 实验 {i+1}/20 已提交: {task_id} - {exp_config['output_dir']}")
                
                # 避免同时提交过多任务，给系统一些缓冲时间
                if (i + 1) % 5 == 0:
                    logger.info(f"⏸️  已提交 {i+1} 个实验，暂停2秒...")
                    import time
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ 实验 {i+1}/20 提交失败: {e}")
        
        logger.info(f"🎯 总共提交了 {len(submitted_tasks)} 个实验任务")
        
        # 监控所有实验的执行状态
        logger.info("⏳ 开始监控所有实验的执行状态...")
        
        completed_tasks = []
        failed_tasks = []
        
        # 定期检查任务状态
        import time
        check_interval = 15  # 每15秒检查一次，提高响应速度
        max_wait_time = 7200  # 最大等待时间2小时
        early_exit_threshold = 0.8  # 如果80%的任务都失败了，提前退出
        
        start_time = time.time()
        consecutive_failures = 0  # 连续失败计数
        last_failure_time = time.time()  # 最后一次失败时间
        
        while time.time() - start_time < max_wait_time:
            # 获取当前任务状态
            all_tasks = manager.get_all_tasks()
            running_count = len(all_tasks["running"])
            completed_count = len(all_tasks["completed"])
            failed_count = len(all_tasks["failed"])
            
            logger.info(f"📊 当前状态 - 运行中: {running_count}, 已完成: {completed_count}, 失败: {failed_count}")
            
            # 检查是否有新完成的任务
            new_failures = 0
            for task_info in submitted_tasks:
                task_id = task_info["task_id"]
                result = manager.get_experiment_result(task_id)
                
                if result and result.status.value in [8, 9]:  # 8=completed, 9=failed
                    if task_info not in completed_tasks and task_info not in failed_tasks:
                        if result.status.value == 8:  # completed
                            completed_tasks.append(task_info)
                            logger.info(f"🎉 实验 {task_info['index']}/20 完成: {task_info['config']['output_dir']}")
                            if result.metrics:
                                logger.info(f"   📊 指标: {result.metrics}")
                            # 重置连续失败计数
                            consecutive_failures = 0
                        else:  # failed
                            failed_tasks.append(task_info)
                            new_failures += 1
                            logger.error(f"❌ 实验 {task_info['index']}/20 失败: {task_info['config']['output_dir']}")
                            if result.error_message:
                                logger.error(f"   💥 错误: {result.error_message}")
            
            # 更新连续失败计数
            if new_failures > 0:
                consecutive_failures += new_failures
                last_failure_time = time.time()
            else:
                # 如果没有新失败，检查是否长时间没有失败
                if time.time() - last_failure_time > 300:  # 5分钟没有新失败
                    consecutive_failures = max(0, consecutive_failures - 1)
            
            # 检查是否所有任务都完成了
            if len(completed_tasks) + len(failed_tasks) == len(submitted_tasks):
                logger.info("🎯 所有实验任务已完成！")
                break
            
            # 检查是否应该提前退出（大量任务失败）
            if len(failed_tasks) > 0 and len(failed_tasks) / len(submitted_tasks) >= early_exit_threshold:
                logger.warning(f"⚠️  失败率过高 ({len(failed_tasks)}/{len(submitted_tasks)} = {len(failed_tasks)/len(submitted_tasks)*100:.1f}%)，提前退出监控")
                break
            
            # 直接使用 manager 的状态来判断退出条件
            if failed_count > 0 and failed_count / len(submitted_tasks) >= early_exit_threshold:
                logger.warning(f"⚠️  失败率过高 ({failed_count}/{len(submitted_tasks)} = {failed_count/len(submitted_tasks)*100:.1f}%)，提前退出监控")
                break
            
            # 检查连续失败是否过多
            if consecutive_failures >= 10:  # 连续失败10次
                logger.warning(f"⚠️  连续失败次数过多 ({consecutive_failures})，提前退出监控")
                break
            
            # 检查是否长时间没有进展
            if len(completed_tasks) + len(failed_tasks) > 0:
                time_since_last_progress = time.time() - last_failure_time
                if time_since_last_progress > 600:  # 10分钟没有新进展
                    logger.warning(f"⚠️  长时间没有新进展 ({time_since_last_progress/60:.1f} 分钟)，提前退出监控")
                    break
            
            # 额外检查：如果所有任务都失败了，立即退出
            if failed_count == len(submitted_tasks) and running_count == 0:
                logger.warning(f"⚠️  所有任务都失败了 ({failed_count}/{len(submitted_tasks)})，立即退出监控")
                break
            
            # 等待一段时间再检查
            time.sleep(check_interval)
        
        # 打印最终统计结果
        logger.info("=" * 60)
        logger.info("📈 实验执行完成统计")
        logger.info("=" * 60)
        logger.info(f"📋 总提交任务: {len(submitted_tasks)}")
        logger.info(f"✅ 成功完成: {len(completed_tasks)}")
        logger.info(f"❌ 执行失败: {len(failed_tasks)}")
        logger.info(f"⏱️  总耗时: {(time.time() - start_time) / 60:.1f} 分钟")
        
        if completed_tasks:
            logger.info("\n🎉 成功完成的实验:")
            for task_info in completed_tasks:
                logger.info(f"  - {task_info['index']}/20: {task_info['config']['output_dir']}")
        
        if failed_tasks:
            logger.info("\n❌ 失败的实验:")
            for task_info in failed_tasks:
                logger.info(f"  - {task_info['index']}/20: {task_info['config']['output_dir']}")
            
            # 分析失败原因
            logger.info("\n🔍 失败原因分析:")
            if len(failed_tasks) == len(submitted_tasks):
                logger.error("💥 所有实验都失败了！可能的原因:")
                logger.error("  1. 服务器配置问题")
                logger.error("  2. kinexlabx 可执行文件不存在或无权限")
                logger.error("  3. 网络连接问题")
                logger.error("  4. 实验参数配置错误")
            elif len(failed_tasks) > len(submitted_tasks) * 0.5:
                logger.warning("⚠️  超过一半的实验失败了！建议检查:")
                logger.warning("  1. 服务器资源是否充足")
                logger.warning("  2. 实验配置是否正确")
                logger.warning("  3. 系统环境是否正常")
            else:
                logger.info("📊 部分实验失败，属于正常范围")
        
        logger.info("=" * 60)
        
        # 打印最终状态
        manager.print_status()
        
        # 停止管理器
        manager.stop()
        
    except Exception as e:
        logger.error(f"❌ 主函数执行出错: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    logger.info("🏁 SATuSGH LabGrid 示例结束")


if __name__ == "__main__":
    main()
