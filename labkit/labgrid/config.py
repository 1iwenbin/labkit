#!/usr/bin/env python3
"""
LabGrid 配置管理

负责配置文件的加载、解析、验证和默认值设置
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .types import (
    ServerConfig, 
    FrameworkConfig, 
    ExperimentConfig,
    ServerStatus
)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
        
        # 默认配置
        self.default_framework_config = FrameworkConfig()
        
        # 加载的配置
        self.servers_config: Dict[str, ServerConfig] = {}
        self.framework_config = FrameworkConfig()  # 创建新的实例
    
    def load_servers_config(self, config_file: str) -> Dict[str, ServerConfig]:
        """
        加载服务器配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            服务器配置字典
        """
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            self.logger.error(f"服务器配置文件不存在: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 解析服务器配置
            servers = {}
            for server_name, server_data in config_data.items():
                try:
                    server_config = ServerConfig(
                        name=server_name,
                        host=server_data['host'],
                        user=server_data['user'],
                        port=server_data.get('port', 22),
                        password=server_data.get('password'),
                        key_filename=server_data.get('key_filename'),
                        max_concurrent_tasks=server_data.get('max_concurrent_tasks', 1),
                        description=server_data.get('description')
                    )
                    servers[server_name] = server_config
                    self.logger.info(f"加载服务器配置: {server_name} -> {server_data['host']}")
                    
                except KeyError as e:
                    self.logger.error(f"服务器 {server_name} 配置缺少必要字段: {e}")
                except Exception as e:
                    self.logger.error(f"解析服务器 {server_name} 配置时出错: {e}")
            
            self.servers_config = servers
            self.logger.info(f"成功加载 {len(servers)} 个服务器配置")
            return servers
            
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件 {config_file} JSON 格式错误: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"加载配置文件 {config_file} 时出错: {e}")
            return {}
    
    def load_framework_config(self, config_file: Optional[str] = None) -> FrameworkConfig:
        """
        加载框架配置文件
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
            
        Returns:
            框架配置
        """
        if config_file is None:
            self.logger.info("使用默认框架配置")
            return self.default_framework_config
        
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            self.logger.warning(f"框架配置文件不存在: {config_path}，使用默认配置")
            return self.default_framework_config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新默认配置
            framework_config = FrameworkConfig()  # 创建新的实例
            for key, value in config_data.items():
                if hasattr(framework_config, key):
                    setattr(framework_config, key, value)
                    self.logger.debug(f"更新配置: {key} = {value}")
            
            self.framework_config = framework_config
            self.logger.info("成功加载框架配置")
            return framework_config
            
        except Exception as e:
            self.logger.error(f"加载框架配置文件时出错: {e}，使用默认配置")
            return self.default_framework_config
    
    def validate_server_config(self, server_config: ServerConfig) -> bool:
        """
        验证服务器配置
        
        Args:
            server_config: 服务器配置
            
        Returns:
            配置是否有效
        """
        errors = []
        
        # 检查必要字段
        if not server_config.host:
            errors.append("host 字段不能为空")
        
        if not server_config.user:
            errors.append("user 字段不能为空")
        
        # 检查端口范围
        if not (1 <= server_config.port <= 65535):
            errors.append("port 必须在 1-65535 范围内")
        
        # 检查认证方式
        if not server_config.password and not server_config.key_filename:
            errors.append("必须提供 password 或 key_filename 中的一种")
        
        # 检查并发任务数
        if server_config.max_concurrent_tasks < 1:
            errors.append("max_concurrent_tasks 必须大于 0")
        
        if errors:
            self.logger.error(f"服务器 {server_config.name} 配置验证失败: {'; '.join(errors)}")
            return False
        
        return True
    
    def validate_experiment_config(self, config: ExperimentConfig) -> bool:
        """
        验证实验配置
        
        Args:
            config: 实验配置
            
        Returns:
            配置是否有效
        """
        errors = []
        
        # 检查必要字段
        if not config.experiment_type:
            errors.append("experiment_type 字段不能为空")
        
        if not config.output_dir:
            errors.append("output_dir 字段不能为空")
        
        # 检查超时时间
        if config.timeout <= 0:
            errors.append("timeout 必须大于 0")
        
        # 检查重试次数
        if config.retry_count < 0:
            errors.append("retry_count 不能为负数")
        
        # 检查优先级
        if config.priority < 0:
            errors.append("priority 不能为负数")
        
        if errors:
            self.logger.error(f"实验配置验证失败: {'; '.join(errors)}")
            return False
        
        return True
    
    def get_server_config(self, server_name: str) -> Optional[ServerConfig]:
        """
        获取指定服务器的配置
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器配置，如果不存在则返回 None
        """
        return self.servers_config.get(server_name)
    
    def get_all_server_configs(self) -> Dict[str, ServerConfig]:
        """
        获取所有服务器配置
        
        Returns:
            所有服务器配置的字典
        """
        return self.servers_config.copy()
    
    def get_framework_config(self) -> FrameworkConfig:
        """
        获取框架配置
        
        Returns:
            框架配置
        """
        return self.framework_config
    
    def create_experiment_config(self, 
                                experiment_type: str,
                                output_dir: str,
                                **kwargs) -> ExperimentConfig:
        """
        创建实验配置
        
        Args:
            experiment_type: 实验类型
            output_dir: 输出目录
            **kwargs: 其他配置参数
            
        Returns:
            实验配置对象
        """
        return ExperimentConfig(
            experiment_type=experiment_type,
            output_dir=output_dir,
            **kwargs
        )
    
    def save_servers_config(self, config_file: str = "servers.json"):
        """
        保存服务器配置到文件
        
        Args:
            config_file: 配置文件名
        """
        config_path = self.config_dir / config_file
        
        # 确保配置目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为字典格式
        config_data = {}
        for name, config in self.servers_config.items():
            config_data[name] = {
                'host': config.host,
                'user': config.user,
                'port': config.port,
                'password': config.password,
                'key_filename': config.key_filename,
                'max_concurrent_tasks': config.max_concurrent_tasks,
                'description': config.description
            }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"服务器配置已保存到: {config_path}")
            
        except Exception as e:
            self.logger.error(f"保存服务器配置时出错: {e}")
    
    def save_framework_config(self, config_file: str = "framework.json"):
        """
        保存框架配置到文件
        
        Args:
            config_file: 配置文件名
        """
        config_path = self.config_dir / config_file
        
        # 确保配置目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为字典格式
        config_data = {
            'max_worker_threads': self.framework_config.max_worker_threads,
            'max_workers_per_server': self.framework_config.max_workers_per_server,
            'max_total_workers': self.framework_config.max_total_workers,
            'experiment_timeout': self.framework_config.experiment_timeout,
            'task_queue_size': self.framework_config.task_queue_size,
            'log_level': self.framework_config.log_level,
            'log_dir': self.framework_config.log_dir,
            'result_retention_days': self.framework_config.result_retention_days,
            'enable_monitoring': self.framework_config.enable_monitoring
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"框架配置已保存到: {config_path}")
            
        except Exception as e:
            self.logger.error(f"保存框架配置时出错: {e}")
