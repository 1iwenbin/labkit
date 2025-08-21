#!/usr/bin/env python3
"""
LabGrid 实验框架

一个可扩展的分布式实验执行框架，支持多服务器并发执行和实验生命周期管理。
"""

__version__ = "1.0.0"
__author__ = "LabGrid Team"
__description__ = "A scalable distributed experiment execution framework"

# 导出主要类
from .framework import LabGrid
from .experiment import Lab
from .labx import LabX
from .types import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentStatus,
    ServerConfig,
    FrameworkConfig,
    TaskStatus,
    ServerStatus
)
from .config import ConfigManager
from .registry import ExperimentRegistry, register_experiment, get_experiment_class, list_experiments
from .task_manager import TaskManager
from .resource_manager import ResourceManager
from .result_manager import ResultManager

# 导出便捷函数
from .config import ConfigManager as create_config_manager

# 版本信息
__all__ = [
    # 主要类
    'LabGrid',
    'Lab',
    'LabX',
    
    # 类型定义
    'ExperimentConfig',
    'ExperimentResult',
    'ExperimentStatus',
    'ServerConfig',
    'FrameworkConfig',
    'TaskStatus',
    'ServerStatus',
    
    # 管理器类
    'ConfigManager',
    'ExperimentRegistry',
    'TaskManager',
    'ResourceManager',
    'ResultManager',
    
    # 便捷函数
    'create_labgrid',
    'create_experiment_config',
    'register_experiment',
    'get_experiment_class',
    'list_experiments',
    'create_config_manager'
]


def create_labgrid(servers_config_file: str = "servers.json",
                   framework_config_file: str = None,
                   config_dir: str = "configs",
                   auto_start: bool = True) -> LabGrid:
    """
    创建 LabGrid 框架实例的便捷函数
    
    Args:
        servers_config_file: 服务器配置文件
        framework_config_file: 框架配置文件
        config_dir: 配置目录
        auto_start: 是否自动启动框架
        
    Returns:
        LabGrid 实例
    """
    labgrid = LabGrid(
        servers_config_file=servers_config_file,
        framework_config_file=framework_config_file,
        config_dir=config_dir
    )
    
    if auto_start:
        labgrid.start()
    
    return labgrid


def create_experiment_config(experiment_type: str,
                           output_dir: str,
                           **kwargs) -> ExperimentConfig:
    """
    创建实验配置的便捷函数
    
    Args:
        experiment_type: 实验类型
        output_dir: 输出目录
        **kwargs: 其他配置参数
        
    Returns:
        ExperimentConfig 实例
    """
    from .config import ConfigManager
    
    config_manager = ConfigManager()
    return config_manager.create_experiment_config(
        experiment_type=experiment_type,
        output_dir=output_dir,
        **kwargs
    )


# 框架信息
def get_framework_info() -> dict:
    """获取框架信息"""
    return {
        'name': 'LabGrid',
        'version': __version__,
        'description': __description__,
        'author': __author__,
        'components': [
            'LabGrid - 框架主类',
            'Lab - 实验抽象基类',
            'LabX - 服务器能力封装',
            'ConfigManager - 配置管理',
            'ExperimentRegistry - 实验注册',
            'TaskManager - 任务管理',
            'ResourceManager - 资源管理',
            'ResultManager - 结果管理'
        ]
    }


def print_framework_info():
    """打印框架信息"""
    info = get_framework_info()
    
    print("=" * 60)
    print(f"🚀 {info['name']} v{info['version']}")
    print("=" * 60)
    print(f"📝 {info['description']}")
    print(f"👨‍💻 {info['author']}")
    print()
    print("🔧 主要组件:")
    for component in info['components']:
        print(f"  - {component}")
    print("=" * 60)


# 快速开始示例
def quick_start_example():
    """快速开始示例"""
    print("🚀 LabGrid 快速开始示例")
    print()
    print("1. 创建框架:")
    print("   labgrid = create_labgrid('configs/servers.json')")
    print()
    print("2. 定义实验类:")
    print("   class MyExperiment(Lab):")
    print("       def initialize(self): ...")
    print("       def execute(self): ...")
    print("       def collect_data(self): ...")
    print("       def analyze_data(self): ...")
    print("       def save_data(self): ...")
    print()
    print("3. 注册实验:")
    print("   labgrid.register_experiment('my_experiment', MyExperiment)")
    print()
    print("4. 运行实验:")
    print("   config = create_experiment_config('my_experiment', 'output_dir')")
    print("   task_id = labgrid.run_experiment('my_experiment', config)")
    print()
    print("5. 等待结果:")
    print("   labgrid.wait_for_experiment(task_id)")
    print("   result = labgrid.get_experiment_result(task_id)")
    print()
    print("6. 关闭框架:")
    print("   labgrid.stop()")


# 当模块被导入时，打印框架信息
if __name__ == "__main__":
    print_framework_info()
    print()
    quick_start_example()
else:
    # 模块被导入时，只打印基本信息
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 LabGrid v{__version__} 已加载")
