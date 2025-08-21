#!/usr/bin/env python3
"""
LabGrid 结果管理器

处理实验结果的存储、检索、分析和版本管理
"""

import os
import json
import shutil
import logging
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

from .types import ExperimentResult, ExperimentStatus, ExperimentConfig


class ResultManager:
    """
    结果管理器
    
    负责实验结果的存储、检索、分析、版本管理和清理
    """
    
    def __init__(self, base_dir: str = "results", max_retention_days: int = 30):
        """
        初始化结果管理器
        
        Args:
            base_dir: 结果存储基础目录
            max_retention_days: 结果最大保留天数
        """
        self.base_dir = Path(base_dir)
        self.max_retention_days = max_retention_days
        self.logger = logging.getLogger(__name__)
        
        # 确保基础目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 结果索引
        self.result_index: Dict[str, ExperimentResult] = {}
        
        # 结果元数据存储
        self.metadata_file = self.base_dir / "metadata.json"
        
        # 线程安全
        self.lock = threading.RLock()
        
        # 加载现有结果索引
        self._load_result_index()
        
        # 清理过期结果
        self._cleanup_expired_results()
        
        self.logger.info("🔧 结果管理器初始化完成")
    
    def _load_result_index(self):
        """加载结果索引"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # 重建结果索引
                for result_data in metadata.get('results', []):
                    try:
                        result = ExperimentResult(**result_data)
                        self.result_index[result.experiment_id] = result
                    except Exception as e:
                        self.logger.warning(f"⚠️  加载结果元数据时出错: {e}")
                
                self.logger.info(f"📚 加载了 {len(self.result_index)} 个结果记录")
                
            except Exception as e:
                self.logger.error(f"❌ 加载结果元数据文件时出错: {e}")
    
    def _save_result_index(self):
        """保存结果索引"""
        try:
            metadata = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'results': []
            }
            
            # 转换结果为可序列化的格式
            for result in self.result_index.values():
                result_dict = {
                    'experiment_id': result.experiment_id,
                    'status': result.status.value,  # 枚举值
                    'start_time': result.start_time.isoformat() if result.start_time else None,
                    'end_time': result.end_time.isoformat() if result.end_time else None,
                    'duration': result.duration,
                    'output_dir': result.output_dir,
                    'result_files': result.result_files,
                    'metrics': result.metrics,
                    'error_message': result.error_message,
                    'logs': result.logs
                }
                metadata['results'].append(result_dict)
            
            # 保存到文件
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("💾 结果索引已保存")
            
        except Exception as e:
            self.logger.error(f"❌ 保存结果索引时出错: {e}")
    
    def store_result(self, result: ExperimentResult) -> bool:
        """
        存储实验结果
        
        Args:
            result: 实验结果
            
        Returns:
            是否成功存储
        """
        try:
            with self.lock:
                # 添加到索引
                self.result_index[result.experiment_id] = result
                
                # 保存索引
                self._save_result_index()
                
                self.logger.info(f"💾 存储结果: {result.experiment_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 存储结果时出错: {e}")
            return False
    
    def get_result(self, experiment_id: str) -> Optional[ExperimentResult]:
        """
        获取实验结果
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            实验结果，如果不存在则返回 None
        """
        with self.lock:
            return self.result_index.get(experiment_id)
    
    def get_all_results(self) -> List[ExperimentResult]:
        """
        获取所有实验结果
        
        Returns:
            所有实验结果列表
        """
        with self.lock:
            return list(self.result_index.values())
    
    def get_results_by_status(self, status: ExperimentStatus) -> List[ExperimentResult]:
        """
        根据状态获取实验结果
        
        Args:
            status: 实验状态
            
        Returns:
            匹配的实验结果列表
        """
        with self.lock:
            return [result for result in self.result_index.values() 
                   if result.status == status]
    
    def get_results_by_type(self, experiment_type: str) -> List[ExperimentResult]:
        """
        根据实验类型获取结果
        
        Args:
            experiment_type: 实验类型
            
        Returns:
            匹配的实验结果列表
        """
        with self.lock:
            # 这里需要从实验配置中获取类型信息
            # 暂时返回所有结果，后续可以扩展
            return list(self.result_index.values())
    
    def get_results_by_date_range(self, start_date: datetime, 
                                 end_date: datetime) -> List[ExperimentResult]:
        """
        根据日期范围获取实验结果
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            匹配的实验结果列表
        """
        with self.lock:
            results = []
            for result in self.result_index.values():
                if result.start_time and start_date <= result.start_time <= end_date:
                    results.append(result)
            return results
    
    def search_results(self, query: str) -> List[ExperimentResult]:
        """
        搜索实验结果
        
        Args:
            query: 搜索查询
            
        Returns:
            匹配的实验结果列表
        """
        query = query.lower()
        results = []
        
        with self.lock:
            for result in self.result_index.values():
                # 搜索实验ID
                if query in result.experiment_id.lower():
                    results.append(result)
                    continue
                
                # 搜索错误信息
                if result.error_message and query in result.error_message.lower():
                    results.append(result)
                    continue
                
                # 搜索日志
                for log in result.logs:
                    if query in log.lower():
                        results.append(result)
                        break
        
        return results
    
    def delete_result(self, experiment_id: str) -> bool:
        """
        删除实验结果
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            是否成功删除
        """
        try:
            with self.lock:
                if experiment_id not in self.result_index:
                    self.logger.warning(f"⚠️  结果 {experiment_id} 不存在")
                    return False
                
                result = self.result_index[experiment_id]
                
                # 删除结果文件
                if os.path.exists(result.output_dir):
                    try:
                        shutil.rmtree(result.output_dir)
                        self.logger.info(f"🗑️  删除结果目录: {result.output_dir}")
                    except Exception as e:
                        self.logger.warning(f"⚠️  删除结果目录时出错: {e}")
                
                # 从索引中移除
                del self.result_index[experiment_id]
                
                # 保存索引
                self._save_result_index()
                
                self.logger.info(f"🗑️  删除结果: {experiment_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 删除结果时出错: {e}")
            return False
    
    def archive_result(self, experiment_id: str, archive_dir: str) -> bool:
        """
        归档实验结果
        
        Args:
            experiment_id: 实验ID
            archive_dir: 归档目录
            
        Returns:
            是否成功归档
        """
        try:
            with self.lock:
                if experiment_id not in self.result_index:
                    self.logger.warning(f"⚠️  结果 {experiment_id} 不存在")
                    return False
                
                result = self.result_index[experiment_id]
                
                # 创建归档目录
                archive_path = Path(archive_dir) / f"{experiment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                archive_path.mkdir(parents=True, exist_ok=True)
                
                # 复制结果文件
                if os.path.exists(result.output_dir):
                    shutil.copytree(result.output_dir, archive_path / "results")
                
                # 保存元数据
                metadata = {
                    'experiment_id': result.experiment_id,
                    'status': result.status.value,
                    'start_time': result.start_time.isoformat() if result.start_time else None,
                    'end_time': result.end_time.isoformat() if result.end_time else None,
                    'duration': result.duration,
                    'metrics': result.metrics,
                    'error_message': result.error_message,
                    'logs': result.logs,
                    'archived_at': datetime.now().isoformat()
                }
                
                with open(archive_path / "metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"📦 归档结果: {experiment_id} -> {archive_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 归档结果时出错: {e}")
            return False
    
    def export_results(self, output_file: str, 
                      experiment_ids: Optional[List[str]] = None,
                      format: str = "json") -> bool:
        """
        导出实验结果
        
        Args:
            output_file: 输出文件路径
            experiment_ids: 要导出的实验ID列表，None表示导出所有
            format: 导出格式 ("json", "csv")
            
        Returns:
            是否成功导出
        """
        try:
            with self.lock:
                if experiment_ids:
                    results = [self.result_index[exp_id] for exp_id in experiment_ids 
                              if exp_id in self.result_index]
                else:
                    results = list(self.result_index.values())
                
                if format.lower() == "json":
                    return self._export_to_json(results, output_file)
                elif format.lower() == "csv":
                    return self._export_to_csv(results, output_file)
                else:
                    self.logger.error(f"❌ 不支持的导出格式: {format}")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ 导出结果时出错: {e}")
            return False
    
    def _export_to_json(self, results: List[ExperimentResult], output_file: str) -> bool:
        """导出为JSON格式"""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_results': len(results),
                'results': []
            }
            
            for result in results:
                result_dict = {
                    'experiment_id': result.experiment_id,
                    'status': result.status.value,
                    'start_time': result.start_time.isoformat() if result.start_time else None,
                    'end_time': result.end_time.isoformat() if result.end_time else None,
                    'duration': result.duration,
                    'output_dir': result.output_dir,
                    'result_files': result.result_files,
                    'metrics': result.metrics,
                    'error_message': result.error_message,
                    'logs': result.logs
                }
                export_data['results'].append(result_dict)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📤 导出 {len(results)} 个结果到: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 导出JSON时出错: {e}")
            return False
    
    def _export_to_csv(self, results: List[ExperimentResult], output_file: str) -> bool:
        """导出为CSV格式"""
        try:
            import csv
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow([
                    'experiment_id', 'status', 'start_time', 'end_time', 'duration',
                    'output_dir', 'result_files_count', 'error_message'
                ])
                
                # 写入数据
                for result in results:
                    writer.writerow([
                        result.experiment_id,
                        result.status.value,
                        result.start_time.isoformat() if result.start_time else '',
                        result.end_time.isoformat() if result.end_time else '',
                        result.duration or '',
                        result.output_dir,
                        len(result.result_files),
                        result.error_message or ''
                    ])
            
            self.logger.info(f"📤 导出 {len(results)} 个结果到: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 导出CSV时出错: {e}")
            return False
    
    def get_result_statistics(self) -> Dict[str, Any]:
        """
        获取结果统计信息
        
        Returns:
            统计信息字典
        """
        with self.lock:
            total_results = len(self.result_index)
            
            # 按状态统计
            status_counts = {}
            for result in self.result_index.values():
                status = result.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # 按日期统计
            date_counts = {}
            for result in self.result_index.values():
                if result.start_time:
                    date = result.start_time.date().isoformat()
                    date_counts[date] = date_counts.get(date, 0) + 1
            
            # 计算平均执行时间
            durations = [r.duration for r in self.result_index.values() if r.duration is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # 计算成功率
            successful = len([r for r in self.result_index.values() 
                            if r.status == ExperimentStatus.COMPLETED])
            success_rate = (successful / total_results * 100) if total_results > 0 else 0
            
            return {
                'total_results': total_results,
                'status_counts': status_counts,
                'date_counts': date_counts,
                'average_duration': avg_duration,
                'success_rate': success_rate,
                'successful_count': successful,
                'failed_count': len([r for r in self.result_index.values() 
                                   if r.status == ExperimentStatus.FAILED])
            }
    
    def compare_results(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """
        比较多个实验结果
        
        Args:
            experiment_ids: 要比较的实验ID列表
            
        Returns:
            比较结果字典
        """
        try:
            with self.lock:
                results = [self.result_index[exp_id] for exp_id in experiment_ids 
                          if exp_id in self.result_index]
                
                if len(results) < 2:
                    self.logger.warning("⚠️  需要至少2个结果进行比较")
                    return {}
                
                comparison = {
                    'compared_results': len(results),
                    'experiment_ids': experiment_ids,
                    'execution_times': [],
                    'statuses': [],
                    'metrics_comparison': {},
                    'file_counts': []
                }
                
                for result in results:
                    comparison['execution_times'].append(result.duration or 0)
                    comparison['statuses'].append(result.status.value)
                    comparison['file_counts'].append(len(result.result_files))
                    
                    # 比较指标
                    for metric_name, metric_value in result.metrics.items():
                        if metric_name not in comparison['metrics_comparison']:
                            comparison['metrics_comparison'][metric_name] = []
                        comparison['metrics_comparison'][metric_name].append(metric_value)
                
                # 计算统计信息
                if comparison['execution_times']:
                    comparison['execution_time_stats'] = {
                        'min': min(comparison['execution_times']),
                        'max': max(comparison['execution_times']),
                        'average': sum(comparison['execution_times']) / len(comparison['execution_times'])
                    }
                
                self.logger.info(f"📊 比较了 {len(results)} 个实验结果")
                return comparison
                
        except Exception as e:
            self.logger.error(f"❌ 比较结果时出错: {e}")
            return {}
    
    def _cleanup_expired_results(self):
        """清理过期的实验结果"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_retention_days)
            expired_results = []
            
            with self.lock:
                for experiment_id, result in self.result_index.items():
                    if result.start_time and result.start_time < cutoff_date:
                        expired_results.append(experiment_id)
                
                # 删除过期结果
                for experiment_id in expired_results:
                    self.delete_result(experiment_id)
                
                if expired_results:
                    self.logger.info(f"🧹 清理了 {len(expired_results)} 个过期结果")
                    
        except Exception as e:
            self.logger.error(f"❌ 清理过期结果时出错: {e}")
    
    def cleanup_old_results(self, days: int):
        """
        清理指定天数前的旧结果
        
        Args:
            days: 天数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            old_results = []
            
            with self.lock:
                for experiment_id, result in self.result_index.items():
                    if result.start_time and result.start_time < cutoff_date:
                        old_results.append(experiment_id)
                
                # 删除旧结果
                for experiment_id in old_results:
                    self.delete_result(experiment_id)
                
                if old_results:
                    self.logger.info(f"🧹 清理了 {len(old_results)} 个旧结果")
                    
        except Exception as e:
            self.logger.error(f"❌ 清理旧结果时出错: {e}")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储信息
        
        Returns:
            存储信息字典
        """
        try:
            total_size = 0
            file_count = 0
            
            # 计算总大小和文件数
            for result in self.result_index.values():
                if os.path.exists(result.output_dir):
                    for root, dirs, files in os.walk(result.output_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                total_size += os.path.getsize(file_path)
                                file_count += 1
                            except OSError:
                                pass
            
            return {
                'total_results': len(self.result_index),
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'total_size_gb': total_size / (1024 * 1024 * 1024),
                'total_files': file_count,
                'base_directory': str(self.base_dir),
                'max_retention_days': self.max_retention_days
            }
            
        except Exception as e:
            self.logger.error(f"❌ 获取存储信息时出错: {e}")
            return {}
    
    def shutdown(self):
        """关闭结果管理器"""
        self.logger.info("🛑 关闭结果管理器")
        
        # 保存索引
        self._save_result_index()
        
        self.logger.info("✅ 结果管理器已关闭")
