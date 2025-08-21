#!/usr/bin/env python3
"""
LabGrid 实验注册器

管理实验类型的注册、查询和实例化
"""

import logging
from typing import Dict, List, Optional, Type, Any
from .experiment import Lab
from .types import ExperimentConfig


class ExperimentRegistry:
    """
    实验注册器
    
    负责管理所有已注册的实验类型，提供实验实例的创建和查询功能
    """
    
    def __init__(self):
        """初始化实验注册器"""
        self.logger = logging.getLogger(__name__)
        
        # 已注册的实验类型
        self._experiments: Dict[str, Type[Lab]] = {}
        
        # 实验类型描述信息
        self._descriptions: Dict[str, str] = {}
        
        # 实验类型标签
        self._tags: Dict[str, List[str]] = {}
        
        self.logger.info("🔧 实验注册器初始化完成")
    
    def register(self, experiment_type: str, experiment_class: Type[Lab], 
                description: str = "", tags: Optional[List[str]] = None):
        """
        注册实验类型
        
        Args:
            experiment_type: 实验类型标识
            experiment_class: 实验类（必须继承自 Lab）
            description: 实验类型描述
            tags: 实验类型标签列表
        """
        # 验证实验类
        if not issubclass(experiment_class, Lab):
            raise ValueError(f"实验类 {experiment_class.__name__} 必须继承自 Lab")
        
        # 注册实验类型
        self._experiments[experiment_type] = experiment_class
        self._descriptions[experiment_type] = description or experiment_class.__doc__ or ""
        self._tags[experiment_type] = tags or []
        
        self.logger.info(f"✅ 注册实验类型: {experiment_type} -> {experiment_class.__name__}")
        
        # 记录实验类的详细信息
        self.logger.debug(f"  - 类名: {experiment_class.__name__}")
        self.logger.debug(f"  - 描述: {self._descriptions[experiment_type]}")
        self.logger.debug(f"  - 标签: {self._tags[experiment_type]}")
    
    def unregister(self, experiment_type: str) -> bool:
        """
        注销实验类型
        
        Args:
            experiment_type: 实验类型标识
            
        Returns:
            是否成功注销
        """
        if experiment_type in self._experiments:
            experiment_class = self._experiments[experiment_type]
            del self._experiments[experiment_type]
            del self._descriptions[experiment_type]
            del self._tags[experiment_type]
            
            self.logger.info(f"🗑️  注销实验类型: {experiment_type} -> {experiment_class.__name__}")
            return True
        
        self.logger.warning(f"⚠️  尝试注销不存在的实验类型: {experiment_type}")
        return False
    
    def get_experiment_class(self, experiment_type: str) -> Optional[Type[Lab]]:
        """
        获取实验类
        
        Args:
            experiment_type: 实验类型标识
            
        Returns:
            实验类，如果不存在则返回 None
        """
        return self._experiments.get(experiment_type)
    
    def create_experiment(self, experiment_type: str, config: ExperimentConfig, 
                         labx: Any, **kwargs) -> Optional[Lab]:
        """
        创建实验实例
        
        Args:
            experiment_type: 实验类型标识
            config: 实验配置
            labx: LabX 实例
            **kwargs: 传递给实验类构造函数的额外参数
            
        Returns:
            实验实例，如果创建失败则返回 None
        """
        experiment_class = self.get_experiment_class(experiment_type)
        if not experiment_class:
            self.logger.error(f"❌ 实验类型 {experiment_type} 未注册")
            return None
        
        try:
            # 创建实验实例
            experiment = experiment_class(config, labx, **kwargs)
            self.logger.debug(f"✅ 创建实验实例: {experiment_type} -> {experiment.__class__.__name__}")
            return experiment
            
        except Exception as e:
            self.logger.error(f"❌ 创建实验实例失败: {experiment_type}, 错误: {e}")
            return None
    
    def list_experiments(self) -> List[str]:
        """
        列出所有已注册的实验类型
        
        Returns:
            实验类型标识列表
        """
        return list(self._experiments.keys())
    
    def get_experiment_info(self, experiment_type: str) -> Optional[Dict[str, Any]]:
        """
        获取实验类型信息
        
        Args:
            experiment_type: 实验类型标识
            
        Returns:
            实验类型信息字典，如果不存在则返回 None
        """
        if experiment_type not in self._experiments:
            return None
        
        experiment_class = self._experiments[experiment_type]
        
        return {
            'type': experiment_type,
            'class_name': experiment_class.__name__,
            'module': experiment_class.__module__,
            'description': self._descriptions.get(experiment_type, ""),
            'tags': self._tags.get(experiment_type, []),
            'doc': experiment_class.__doc__ or "",
            'methods': [method for method in dir(experiment_class) 
                       if not method.startswith('_') and callable(getattr(experiment_class, method))]
        }
    
    def get_all_experiment_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有实验类型信息
        
        Returns:
            所有实验类型信息的字典
        """
        return {
            exp_type: self.get_experiment_info(exp_type)
            for exp_type in self.list_experiments()
        }
    
    def search_experiments(self, query: str) -> List[str]:
        """
        搜索实验类型
        
        Args:
            query: 搜索查询（支持类型名、描述、标签搜索）
            
        Returns:
            匹配的实验类型标识列表
        """
        query = query.lower()
        results = []
        
        for exp_type in self.list_experiments():
            # 搜索类型名
            if query in exp_type.lower():
                results.append(exp_type)
                continue
            
            # 搜索描述
            description = self._descriptions.get(exp_type, "").lower()
            if query in description:
                results.append(exp_type)
                continue
            
            # 搜索标签
            tags = [tag.lower() for tag in self._tags.get(exp_type, [])]
            if any(query in tag for tag in tags):
                results.append(exp_type)
                continue
        
        return results
    
    def get_experiments_by_tag(self, tag: str) -> List[str]:
        """
        根据标签获取实验类型
        
        Args:
            tag: 标签
            
        Returns:
            包含指定标签的实验类型标识列表
        """
        tag = tag.lower()
        results = []
        
        for exp_type, tags in self._tags.items():
            if tag in [t.lower() for t in tags]:
                results.append(exp_type)
        
        return results
    
    def get_experiments_by_module(self, module_name: str) -> List[str]:
        """
        根据模块名获取实验类型
        
        Args:
            module_name: 模块名
            
        Returns:
            属于指定模块的实验类型标识列表
        """
        module_name = module_name.lower()
        results = []
        
        for exp_type in self.list_experiments():
            experiment_class = self._experiments[exp_type]
            if module_name in experiment_class.__module__.lower():
                results.append(exp_type)
        
        return results
    
    def validate_experiment_type(self, experiment_type: str) -> bool:
        """
        验证实验类型是否已注册
        
        Args:
            experiment_type: 实验类型标识
            
        Returns:
            是否已注册
        """
        return experiment_type in self._experiments
    
    def get_registered_count(self) -> int:
        """
        获取已注册的实验类型数量
        
        Returns:
            实验类型数量
        """
        return len(self._experiments)
    
    def clear(self):
        """清空所有注册的实验类型"""
        count = len(self._experiments)
        self._experiments.clear()
        self._descriptions.clear()
        self._tags.clear()
        
        self.logger.info(f"🗑️  清空所有实验类型，共 {count} 个")
    
    def export_registry_info(self) -> Dict[str, Any]:
        """
        导出注册器信息
        
        Returns:
            注册器信息字典
        """
        return {
            'total_count': self.get_registered_count(),
            'experiments': self.get_all_experiment_info(),
            'tags_summary': self._get_tags_summary(),
            'modules_summary': self._get_modules_summary()
        }
    
    def _get_tags_summary(self) -> Dict[str, int]:
        """获取标签统计信息"""
        tag_counts = {}
        for tags in self._tags.values():
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts
    
    def _get_modules_summary(self) -> Dict[str, int]:
        """获取模块统计信息"""
        module_counts = {}
        for exp_type in self.list_experiments():
            experiment_class = self._experiments[exp_type]
            module = experiment_class.__module__
            module_counts[module] = module_counts.get(module, 0) + 1
        return module_counts
    
    def print_registry_summary(self):
        """打印注册器摘要信息"""
        self.logger.info("📊 实验注册器摘要:")
        self.logger.info(f"  - 总实验类型数: {self.get_registered_count()}")
        
        if self._experiments:
            self.logger.info("  - 已注册的实验类型:")
            for exp_type in sorted(self.list_experiments()):
                info = self.get_experiment_info(exp_type)
                if info:
                    self.logger.info(f"    * {exp_type} ({info['class_name']})")
                    if info['description']:
                        self.logger.info(f"      {info['description']}")
                    if info['tags']:
                        self.logger.info(f"      标签: {', '.join(info['tags'])}")
        
        # 标签统计
        tag_summary = self._get_tags_summary()
        if tag_summary:
            self.logger.info("  - 标签统计:")
            for tag, count in sorted(tag_summary.items()):
                self.logger.info(f"    * {tag}: {count}")
        
        # 模块统计
        module_summary = self._get_modules_summary()
        if module_summary:
            self.logger.info("  - 模块统计:")
            for module, count in sorted(module_summary.items()):
                self.logger.info(f"    * {module}: {count}")


# 全局实验注册器实例
_global_registry: Optional[ExperimentRegistry] = None


def get_global_registry() -> ExperimentRegistry:
    """
    获取全局实验注册器实例
    
    Returns:
        全局实验注册器
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ExperimentRegistry()
    return _global_registry


def register_experiment(experiment_type: str, experiment_class: Type[Lab], 
                       description: str = "", tags: Optional[List[str]] = None):
    """
    注册实验类型到全局注册器
    
    Args:
        experiment_type: 实验类型标识
        experiment_class: 实验类
        description: 实验类型描述
        tags: 实验类型标签列表
    """
    registry = get_global_registry()
    registry.register(experiment_type, experiment_class, description, tags)


def get_experiment_class(experiment_type: str) -> Optional[Type[Lab]]:
    """
    从全局注册器获取实验类
    
    Args:
        experiment_type: 实验类型标识
        
    Returns:
        实验类，如果不存在则返回 None
    """
    registry = get_global_registry()
    return registry.get_experiment_class(experiment_type)


def list_experiments() -> List[str]:
    """
    从全局注册器列出所有实验类型
    
    Returns:
        实验类型标识列表
    """
    registry = get_global_registry()
    return registry.list_experiments()
