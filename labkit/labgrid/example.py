#!/usr/bin/env python3
"""
LabGrid 使用示例

演示如何使用 LabGrid 框架创建和运行实验
"""

import os
import time
from datetime import datetime

from .framework import LabGrid
from .experiment import Lab
from .types import ExperimentConfig


class SimpleNetworkExperiment(Lab):
    """
    简单的网络实验示例
    
    演示如何实现一个具体的实验类
    """
    
    def __init__(self, config, labx):
        super().__init__(config, labx)
        self.log("🔬 初始化简单网络实验")
    
    def initialize(self) -> bool:
        """初始化实验环境"""
        self.log("📋 阶段1: 初始化实验环境")
        
        # 确保输出目录存在
        if not self.ensure_output_dir():
            return False
        
        # 创建一些测试文件
        test_file = os.path.join(self.config.output_dir, "test_config.txt")
        try:
            with open(test_file, 'w') as f:
                f.write(f"实验类型: {self.config.experiment_type}\n")
                f.write(f"开始时间: {datetime.now()}\n")
                f.write(f"参数: {self.config.parameters}\n")
            
            self.log("✅ 测试配置文件创建成功")
            return True
            
        except Exception as e:
            self.log(f"❌ 创建测试配置文件失败: {e}", "ERROR")
            return False
    
    def execute(self) -> bool:
        """执行实验"""
        self.log("🔬 阶段2: 执行实验")
        
        if not self.assigned_server:
            self.log("❌ 没有分配服务器", "ERROR")
            return False
        
        try:
            # 在服务器上执行一些命令
            server_name = self.assigned_server
            
            # 获取系统信息
            system_info = self.labx.get_system_info(server_name)
            if system_info:
                self.log(f"✅ 获取系统信息成功: {server_name}")
            else:
                self.log(f"⚠️  获取系统信息失败: {server_name}")
            
            # 创建远程目录
            remote_dir = f"/tmp/experiment_{self.result.experiment_id}"
            if self.labx.create_remote_directory(server_name, remote_dir):
                self.log(f"✅ 创建远程目录成功: {remote_dir}")
            else:
                self.log(f"❌ 创建远程目录失败: {remote_dir}")
            
            # 上传测试文件
            local_file = os.path.join(self.config.output_dir, "test_config.txt")
            remote_file = f"{remote_dir}/test_config.txt"
            
            if self.labx.upload_file(server_name, local_file, remote_file):
                self.log(f"✅ 上传文件成功: {local_file} -> {remote_file}")
            else:
                self.log(f"❌ 上传文件失败: {local_file} -> {remote_file}")
            
            # 在服务器上执行一些测试命令
            commands = [
                "echo '开始执行实验'",
                "date",
                "whoami",
                "pwd",
                "ls -la /tmp",
                "echo '实验执行完成'"
            ]
            
            for cmd in commands:
                result = self.labx.execute_command(server_name, cmd)
                if result and result.get('success'):
                    self.log(f"✅ 命令执行成功: {cmd}")
                else:
                    self.log(f"⚠️  命令执行失败: {cmd}")
            
            # 模拟实验执行时间
            time.sleep(2)
            
            self.log("✅ 实验执行完成")
            return True
            
        except Exception as e:
            self.log(f"❌ 实验执行失败: {e}", "ERROR")
            return False
    
    def collect_data(self) -> bool:
        """收集实验数据"""
        self.log("📥 阶段3: 收集实验数据")
        
        if not self.assigned_server:
            return False
        
        try:
            server_name = self.assigned_server
            remote_dir = f"/tmp/experiment_{self.result.experiment_id}"
            
            # 下载远程文件
            local_dir = os.path.join(self.config.output_dir, "remote_data")
            if self.labx.download_directory(server_name, remote_dir, local_dir):
                self.log(f"✅ 下载远程数据成功: {remote_dir} -> {local_dir}")
            else:
                self.log(f"❌ 下载远程数据失败: {remote_dir} -> {local_dir}")
            
            # 清理远程文件
            if self.labx.remove_remote_directory(server_name, remote_dir):
                self.log(f"✅ 清理远程文件成功: {remote_dir}")
            
            self.log("✅ 数据收集完成")
            return True
            
        except Exception as e:
            self.log(f"❌ 数据收集失败: {e}", "ERROR")
            return False
    
    def analyze_data(self) -> dict:
        """分析实验数据"""
        self.log("📊 阶段4: 分析实验数据")
        
        try:
            # 模拟数据分析
            analysis_result = {
                'total_files': len(self.result.result_files),
                'experiment_duration': self.result.duration or 0,
                'server_used': self.assigned_server or 'unknown',
                'analysis_timestamp': datetime.now().isoformat(),
                'success_rate': 95.5,  # 模拟成功率
                'performance_score': 87.3  # 模拟性能评分
            }
            
            self.log("✅ 数据分析完成")
            return analysis_result
            
        except Exception as e:
            self.log(f"❌ 数据分析失败: {e}", "ERROR")
            return {}
    
    def save_data(self) -> bool:
        """保存实验结果"""
        self.log("💾 阶段5: 保存实验结果")
        
        try:
            # 创建结果摘要文件
            summary_file = os.path.join(self.config.output_dir, "experiment_summary.txt")
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("=" * 50 + "\n")
                f.write("实验执行摘要\n")
                f.write("=" * 50 + "\n")
                f.write(f"实验ID: {self.result.experiment_id}\n")
                f.write(f"实验类型: {self.config.experiment_type}\n")
                f.write(f"开始时间: {self.result.start_time}\n")
                f.write(f"结束时间: {self.result.end_time}\n")
                f.write(f"执行时长: {self.result.duration:.2f} 秒\n")
                f.write(f"使用服务器: {self.assigned_server}\n")
                f.write(f"状态: {self.result.status.value}\n")
                
                if self.result.metrics:
                    f.write("\n性能指标:\n")
                    for key, value in self.result.metrics.items():
                        f.write(f"  {key}: {value}\n")
                
                if self.result.error_message:
                    f.write(f"\n错误信息: {self.result.error_message}\n")
                
                f.write("=" * 50 + "\n")
            
            self.log("✅ 实验结果保存成功")
            return True
            
        except Exception as e:
            self.log(f"❌ 保存实验结果失败: {e}", "ERROR")
            return False
    
    def cleanup(self):
        """清理实验环境"""
        self.log("🧹 阶段6: 清理实验环境")
        
        # 调用父类的清理方法
        super().cleanup()
        
        # 可以添加额外的清理逻辑
        self.log("✅ 实验环境清理完成")


def run_example():
    """运行示例实验"""
    print("🚀 开始运行 LabGrid 示例")
    
    try:
        # 1. 创建框架实例
        print("📋 步骤1: 创建 LabGrid 框架")
        labgrid = LabGrid(
            servers_config_file="configs/servers.json",
            auto_start=False  # 不自动启动，手动控制
        )
        
        # 2. 注册实验类型
        print("📋 步骤2: 注册实验类型")
        labgrid.register_experiment(
            experiment_type="simple_network",
            experiment_class=SimpleNetworkExperiment,
            description="简单的网络实验示例",
            tags=["network", "example", "demo"]
        )
        
        # 3. 启动框架
        print("📋 步骤3: 启动框架")
        labgrid.start()
        
        # 4. 创建实验配置
        print("📋 步骤4: 创建实验配置")
        config = ExperimentConfig(
            experiment_type="simple_network",
            output_dir="results/simple_network_experiment",
            parameters={
                "test_mode": True,
                "timeout": 300,
                "retry_count": 2
            },
            timeout=600,
            retry_count=2,
            priority=5,
            description="示例网络实验"
        )
        
        # 5. 运行实验
        print("📋 步骤5: 运行实验")
        task_id = labgrid.run_experiment("simple_network", config)
        print(f"✅ 实验任务已提交: {task_id}")
        
        # 6. 等待实验完成
        print("📋 步骤6: 等待实验完成")
        if labgrid.wait_for_experiment(task_id, timeout=300):
            print("✅ 实验执行完成")
            
            # 7. 获取实验结果
            result = labgrid.get_experiment_result(task_id)
            if result:
                print(f"📊 实验结果:")
                print(f"  - 状态: {result.status.value}")
                print(f"  - 执行时长: {result.duration:.2f} 秒")
                print(f"  - 输出目录: {result.output_dir}")
                print(f"  - 结果文件数: {len(result.result_files)}")
                
                if result.metrics:
                    print(f"  - 性能指标:")
                    for key, value in result.metrics.items():
                        print(f"    {key}: {value}")
            else:
                print("❌ 无法获取实验结果")
        else:
            print("❌ 实验执行超时")
        
        # 8. 显示框架状态
        print("\n📊 框架状态:")
        labgrid.print_status()
        
        # 9. 停止框架
        print("\n📋 步骤9: 停止框架")
        labgrid.stop()
        
        print("🎉 示例运行完成！")
        
    except Exception as e:
        print(f"❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_example()
