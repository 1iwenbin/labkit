#!/usr/bin/env python3
"""
LabGrid 实验基类

定义所有实验类必须实现的标准接口和生命周期方法
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

from .types import ExperimentConfig, ExperimentResult, ExperimentStatus


class Lab(ABC):
    """
    实验基类
    
    所有实验类必须继承此类并实现必要的方法
    """
    
    def __init__(self, config: ExperimentConfig, labx):
        """
        初始化实验
        
        Args:
            config: 实验配置
            labx: LabX 服务器能力封装实例
        """
        self.config = config
        self.labx = labx
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # 实验状态
        self.assigned_server: Optional[str] = None
        self.result: Optional[ExperimentResult] = None
        
        # 创建实验结果对象
        self._create_result()
    
    def _create_result(self):
        """创建实验结果对象"""
        self.result = ExperimentResult(
            experiment_id=f"exp_{int(datetime.now().timestamp() * 1000)}",
            status=ExperimentStatus.PENDING,
            output_dir=self.config.output_dir
        )
    
    def assign_server(self, server_name: str):
        """
        分配服务器给实验
        
        Args:
            server_name: 服务器名称
        """
        self.assigned_server = server_name
        self.log(f"🔧 分配服务器: {server_name}")
    
    def release_server(self):
        """释放分配的服务器"""
        if self.assigned_server:
            self.log(f"🔌 释放服务器: {self.assigned_server}")
            self.assigned_server = None
    
    def ensure_output_dir(self) -> bool:
        """
        确保输出目录存在
        
        Returns:
            是否成功创建目录
        """
        try:
            os.makedirs(self.config.output_dir, exist_ok=True)
            self.log(f"📁 输出目录已准备: {self.config.output_dir}")
            return True
        except Exception as e:
            self.log(f"❌ 创建输出目录失败: {e}", "ERROR")
            return False
    
    def log(self, message: str, level: str = "INFO"):
        """
        记录日志
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{self.__class__.__name__}] {message}")
    
    def run(self) -> ExperimentResult:
        """
        运行实验的完整流程
        
        Returns:
            实验结果
        """
        try:
            self.log("🚀 开始运行实验")
            self.result.status = ExperimentStatus.INITIALIZING
            self.result.start_time = datetime.now()
            
            # 1. 初始化阶段
            if not self.initialize():
                self.result.status = ExperimentStatus.FAILED
                self.result.error_message = "初始化失败"
                return self.result
            
            # 2. 执行阶段
            self.result.status = ExperimentStatus.RUNNING
            if not self.execute():
                self.result.status = ExperimentStatus.FAILED
                self.result.error_message = "执行失败"
                return self.result
            
            # 3. 数据收集阶段
            self.result.status = ExperimentStatus.COLLECTING
            if not self.collect_data():
                self.result.status = ExperimentStatus.FAILED
                self.result.error_message = "数据收集失败"
                return self.result
            
            # 4. 数据分析阶段
            self.result.status = ExperimentStatus.ANALYZING
            metrics = self.analyze_data()
            self.result.metrics = metrics
            
            # 5. 数据保存阶段
            self.result.status = ExperimentStatus.SAVING
            if not self.save_data():
                self.log("⚠️  数据保存失败，但实验继续", "WARNING")
            
            # 6. 清理阶段
            self.result.status = ExperimentStatus.CLEANING
            self.cleanup()
            
            # 7. 完成
            self.result.status = ExperimentStatus.COMPLETED
            self.result.end_time = datetime.now()
            if self.result.start_time:
                self.result.duration = (self.result.end_time - self.result.start_time).total_seconds()
            
            self.log("✅ 实验运行完成")
            return self.result
            
        except Exception as e:
            self.log(f"❌ 实验运行出错: {e}", "ERROR")
            self.result.status = ExperimentStatus.FAILED
            self.result.error_message = str(e)
            self.result.end_time = datetime.now()
            if self.result.start_time:
                self.result.duration = (self.result.end_time - self.result.start_time).total_seconds()
            return self.result
    
    # ==================== 抽象方法 ====================
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化实验环境
        
        Returns:
            是否初始化成功
        """
        pass
    
    @abstractmethod
    def execute(self) -> bool:
        """
        执行实验
        
        Returns:
            是否执行成功
        """
        pass
    
    @abstractmethod
    def collect_data(self) -> bool:
        """
        收集实验数据
        
        Returns:
            是否收集成功
        """
        pass
    
    @abstractmethod
    def analyze_data(self) -> dict:
        """
        分析实验数据
        
        Returns:
            分析结果字典
        """
        pass
    
    @abstractmethod
    def save_data(self) -> bool:
        """
        保存实验结果
        
        Returns:
            是否保存成功
        """
        pass
    
    def cleanup(self):
        """
        清理实验环境
        
        默认实现为空，子类可以重写此方法
        """
        pass
