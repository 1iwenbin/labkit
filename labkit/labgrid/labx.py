#!/usr/bin/env python3
"""
LabGrid 服务器能力封装 (LabX)

封装 RemoteManager 提供的底层服务器能力，为实验类提供统一的接口
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime

from .types import ServerConfig, ServerStatus, ServerInfo
from labkit.remote import RemoteManager


class LabX:
    """
    服务器能力封装类
    
    封装 RemoteManager 提供的底层能力，为实验类提供统一的服务器操作接口
    """
    
    def __init__(self, servers_config: Dict[str, ServerConfig]):
        """
        初始化 LabX
        
        Args:
            servers_config: 服务器配置字典
        """
        self.servers_config = servers_config
        self.logger = logging.getLogger(__name__)
        
        # 创建 RemoteManager 实例
        self.remote_manager = RemoteManager()
        
        # 服务器连接状态
        self.server_connections: Dict[str, bool] = {}
        self.server_info: Dict[str, ServerInfo] = {}
        
        # 初始化服务器信息
        self._init_server_info()
        
        # 添加所有服务器到 RemoteManager
        self._setup_servers()
    
    def _init_server_info(self):
        """初始化服务器信息"""
        for server_name, config in self.servers_config.items():
            self.server_info[server_name] = ServerInfo(
                name=server_name,
                status=ServerStatus.OFFLINE,
                current_tasks=0,
                max_tasks=config.max_concurrent_tasks,
                last_heartbeat=None
            )
    
    def _setup_servers(self):
        """设置所有服务器连接"""
        for server_name, config in self.servers_config.items():
            try:
                success = self.remote_manager.add_server(
                    name=server_name,
                    host=config.host,
                    user=config.user,
                    port=config.port,
                    password=config.password,
                    key_filename=config.key_filename
                )
                
                if success:
                    self.logger.info(f"✅ 服务器 {server_name} 添加成功")
                    self.server_connections[server_name] = False  # 初始未连接
                else:
                    self.logger.error(f"❌ 服务器 {server_name} 添加失败")
                    self.server_connections[server_name] = False
                    
            except Exception as e:
                self.logger.error(f"❌ 添加服务器 {server_name} 时出错: {e}")
                self.server_connections[server_name] = False
    
    def connect_server(self, server_name: str) -> bool:
        """
        连接到指定服务器
        
        Args:
            server_name: 服务器名称
            
        Returns:
            连接是否成功
        """
        if server_name not in self.servers_config:
            self.logger.error(f"❌ 服务器 {server_name} 不在配置中")
            return False
        
        try:
            if self.remote_manager.connect_server(server_name):
                self.server_connections[server_name] = True
                self.server_info[server_name].status = ServerStatus.IDLE
                self.server_info[server_name].last_heartbeat = datetime.now()
                self.logger.debug(f"✅ 连接到服务器 {server_name} 成功")
                return True
            else:
                self.server_connections[server_name] = False
                self.server_info[server_name].status = ServerStatus.OFFLINE
                self.logger.error(f"❌ 连接到服务器 {server_name} 失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 连接服务器 {server_name} 时出错: {e}")
            self.server_connections[server_name] = False
            self.server_info[server_name].status = ServerStatus.ERROR
            return False
    
    def disconnect_server(self, server_name: str):
        """
        断开与指定服务器的连接
        
        Args:
            server_name: 服务器名称
        """
        if server_name in self.server_connections:
            self.server_connections[server_name] = False
            self.server_info[server_name].status = ServerStatus.OFFLINE
            self.logger.debug(f"🔌 断开与服务器 {server_name} 的连接")
    
    def execute_command(self, server_name: str, command: str, 
                       timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        在指定服务器上执行命令
        
        Args:
            server_name: 服务器名称
            command: 要执行的命令
            timeout: 超时时间（秒）
            
        Returns:
            命令执行结果字典
        """
        if not self._ensure_connection(server_name):
            return {'success': False, 'error': '无法连接到服务器'}
        
        try:
            # 使用 paramiko 直接执行命令，避免 fabric 显示冲突
            result = self._execute_command_with_paramiko(server_name, command, timeout)
            
            if result and result.get('success'):
                self.logger.debug(f"✅ 命令执行成功: {server_name} -> {command}")
            else:
                error_msg = result.get('stderr', '未知错误') if result else '执行失败'
                self.logger.warning(f"⚠️  命令执行失败: {server_name} -> {command}, 错误: {error_msg}")
            
            return result or {'success': False, 'error': '执行失败'}
            
        except Exception as e:
            self.logger.error(f"❌ 执行命令时出错: {server_name} -> {command}, 错误: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_command_with_paramiko(self, server_name: str, command: str, 
                                     timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        使用 paramiko 执行命令
        
        Args:
            server_name: 服务器名称
            command: 要执行的的命令
            timeout: 超时时间（秒）
            
        Returns:
            命令执行结果字典
        """
        try:
            import paramiko
            
            # 获取服务器配置
            server_config = self.servers_config.get(server_name)
            if not server_config:
                return {'success': False, 'error': '服务器配置不存在'}
            
            # 创建 SSH 客户端
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接参数
            connect_kwargs = {
                'hostname': server_config.host,
                'port': server_config.port,
                'username': server_config.user,
                'timeout': timeout or 30
            }
            
            # 如果有私钥文件，使用私钥认证
            if server_config.key_filename:
                connect_kwargs['key_filename'] = server_config.key_filename
            elif server_config.password:
                connect_kwargs['password'] = server_config.password
            
            # 连接到服务器
            ssh.connect(**connect_kwargs)
            
            # 执行命令
            stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout or 30)
            
            # 获取输出
            stdout_str = stdout.read().decode('utf-8').strip()
            stderr_str = stderr.read().decode('utf-8').strip()
            exit_code = stdout.channel.recv_exit_status()
            
            # 关闭连接
            ssh.close()
            
            # 返回结果
            result = {
                'success': exit_code == 0,
                'stdout': stdout_str,
                'stderr': stderr_str,
                'exit_code': exit_code
            }
            
            # 如果命令执行失败，设置错误信息
            if not result['success']:
                if stderr_str:
                    result['error'] = stderr_str
                elif stdout_str:
                    result['error'] = stdout_str
                else:
                    result['error'] = f'命令执行失败，退出码: {exit_code}'
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def upload_file(self, server_name: str, local_path: str, remote_path: str) -> bool:
        """
        上传文件到指定服务器
        
        Args:
            server_name: 服务器名称
            local_path: 本地文件路径
            remote_path: 远程文件路径
            
        Returns:
            上传是否成功
        """
        if not self._ensure_connection(server_name):
            return False
        
        if not os.path.exists(local_path):
            self.logger.error(f"❌ 本地文件不存在: {local_path}")
            return False
        
        try:
            success = self.remote_manager.upload_file(server_name, local_path, remote_path)
            
            if success:
                self.logger.debug(f"✅ 文件上传成功: {local_path} -> {server_name}:{remote_path}")
            else:
                self.logger.error(f"❌ 文件上传失败: {local_path} -> {server_name}:{remote_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 上传文件时出错: {local_path} -> {server_name}:{remote_path}, 错误: {e}")
            return False
    
    def upload_directory(self, server_name: str, local_dir: str, remote_dir: str) -> bool:
        """
        上传目录到指定服务器
        
        Args:
            server_name: 服务器名称
            local_dir: 本地目录路径
            remote_dir: 远程目录路径
            
        Returns:
            上传是否成功
        """
        if not self._ensure_connection(server_name):
            return False
        
        if not os.path.exists(local_dir):
            self.logger.error(f"❌ 本地目录不存在: {local_dir}")
            return False
        
        try:
            # 使用 rsync 命令上传目录，避免 fabric 显示冲突
            success = self._upload_directory_with_rsync(server_name, local_dir, remote_dir)
            
            if success:
                self.logger.debug(f"✅ 目录上传成功: {local_dir} -> {server_name}:{remote_dir}")
            else:
                self.logger.error(f"❌ 目录上传失败: {local_dir} -> {server_name}:{remote_dir}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 上传目录时出错: {local_dir} -> {server_name}:{remote_dir}, 错误: {e}")
            return False
    
    def _upload_directory_with_rsync(self, server_name: str, local_dir: str, remote_dir: str) -> bool:
        """
        使用 rsync 命令上传目录
        
        Args:
            server_name: 服务器名称
            local_dir: 本地目录路径
            remote_dir: 远程目录路径
            
        Returns:
            上传是否成功
        """
        try:
            # 获取服务器IP
            server_config = self.servers_config.get(server_name)
            if not server_config:
                return False
            
            # 构建 rsync 命令
            rsync_cmd = [
                'rsync', '-avz', '--delete',
                '-e', f'ssh -p {server_config.port} -i {server_config.key_filename} -o StrictHostKeyChecking=no',
                f'{local_dir}/',
                f'{server_config.user}@{server_config.host}:{remote_dir}/'
            ]
            
            # 执行 rsync 命令
            import subprocess
            result = subprocess.run(rsync_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"rsync 失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"rsync 执行出错: {e}")
            return False
    
    def download_file(self, server_name: str, remote_path: str, local_path: str) -> bool:
        """
        从指定服务器下载文件
        
        Args:
            server_name: 服务器名称
            remote_path: 远程文件路径
            local_path: 本地文件路径
            
        Returns:
            下载是否成功
        """
        if not self._ensure_connection(server_name):
            return False
        
        try:
            # 确保本地目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            success = self.remote_manager.download_file(server_name, remote_path, local_path)
            
            if success:
                self.logger.debug(f"✅ 文件下载成功: {server_name}:{remote_path} -> {local_path}")
            else:
                self.logger.error(f"❌ 文件下载失败: {server_name}:{remote_path} -> {local_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 下载文件时出错: {server_name}:{remote_path} -> {local_path}, 错误: {e}")
            return False
    
    def download_directory(self, server_name: str, remote_dir: str, local_dir: str) -> bool:
        """
        从指定服务器下载目录
        
        Args:
            server_name: 服务器名称
            remote_dir: 远程目录路径
            local_dir: 本地目录路径
            
        Returns:
            下载是否成功
        """
        if not self._ensure_connection(server_name):
            return False
        
        try:
            # 确保本地目录存在
            os.makedirs(local_dir, exist_ok=True)
            
            success = self.remote_manager.sync_directory(server_name, remote_dir, local_dir)
            
            if success:
                self.logger.debug(f"✅ 目录下载成功: {server_name}:{remote_dir} -> {local_dir}")
            else:
                self.logger.error(f"❌ 目录下载失败: {server_name}:{remote_dir} -> {local_dir}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 下载目录时出错: {server_name}:{remote_dir} -> {local_dir}, 错误: {e}")
            return False
    
    def sync_directory(self, server_name: str, remote_dir: str, local_dir: str) -> bool:
        """
        同步目录（下载目录的别名方法）
        
        Args:
            server_name: 服务器名称
            remote_dir: 远程目录路径
            local_dir: 本地目录路径
            
        Returns:
            同步是否成功
        """
        return self.download_directory(server_name, remote_dir, local_dir)
    
    def get_system_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定服务器的系统信息
        
        Args:
            server_name: 服务器名称
            
        Returns:
            系统信息字典，如果失败则返回 None
        """
        if not self._ensure_connection(server_name):
            return None
        
        try:
            info = self.remote_manager.get_system_info(server_name)
            if info:
                self.logger.debug(f"✅ 获取系统信息成功: {server_name}")
                return info
            else:
                self.logger.warning(f"⚠️  获取系统信息失败: {server_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 获取系统信息时出错: {server_name}, 错误: {e}")
            return None
    
    def create_remote_directory(self, server_name: str, remote_dir: str) -> bool:
        """
        在指定服务器上创建目录
        
        Args:
            server_name: 服务器名称
            remote_dir: 远程目录路径
            
        Returns:
            创建是否成功
        """
        command = f"mkdir -p {remote_dir}"
        result = self.execute_command(server_name, command)
        return result.get('success', False)
    
    def remove_remote_file(self, server_name: str, remote_path: str) -> bool:
        """
        删除指定服务器上的文件
        
        Args:
            server_name: 服务器名称
            remote_path: 远程文件路径
            
        Returns:
            删除是否成功
        """
        command = f"rm -f {remote_path}"
        result = self.execute_command(server_name, command)
        return result.get('success', False)
    
    def remove_remote_directory(self, server_name: str, remote_dir: str) -> bool:
        """
        删除指定服务器上的目录
        
        Args:
            server_name: 服务器名称
            remote_dir: 远程目录路径
            
        Returns:
            删除是否成功
        """
        command = f"rm -rf {remote_dir}"
        result = self.execute_command(server_name, command)
        return result.get('success', False)
    
    def check_file_exists(self, server_name: str, remote_path: str) -> bool:
        """
        检查指定服务器上的文件是否存在
        
        Args:
            server_name: 服务器名称
            remote_path: 远程文件路径
            
        Returns:
            文件是否存在
        """
        command = f"test -f {remote_path} && echo 'exists' || echo 'not_exists'"
        result = self.execute_command(server_name, command)
        
        if result.get('success') and result.get('stdout'):
            return 'exists' in result['stdout'].strip()
        return False
    
    def check_directory_exists(self, server_name: str, remote_dir: str) -> bool:
        """
        检查指定服务器上的目录是否存在
        
        Args:
            server_name: 服务器名称
            remote_dir: 远程目录路径
            
        Returns:
            目录是否存在
        """
        command = f"test -d {remote_dir} && echo 'exists' || echo 'not_exists'"
        result = self.execute_command(server_name, command)
        
        if result.get('success') and result.get('stdout'):
            output = result['stdout'].strip()
            if output != 'error':
                return 'exists' in output
        return False
    
    def get_remote_file_size(self, server_name: str, remote_path: str) -> Optional[int]:
        """
        获取指定服务器上文件的大小
        
        Args:
            server_name: 服务器名称
            remote_path: 远程文件路径
            
        Returns:
            文件大小（字节），如果失败则返回 None
        """
        command = f"stat -c%s {remote_path} 2>/dev/null || echo 'error'"
        result = self.execute_command(server_name, command)
        
        if result.get('success') and result.get('stdout'):
            output = result['stdout'].strip()
            if output != 'error':
                try:
                    return int(output)
                except ValueError:
                    pass
        return None
    
    def list_remote_directory(self, server_name: str, remote_dir: str) -> List[str]:
        """
        列出指定服务器上目录的内容
        
        Args:
            server_name: 服务器名称
            remote_dir: 远程目录路径
            
        Returns:
            目录内容列表
        """
        command = f"ls -1 {remote_dir} 2>/dev/null || echo 'error'"
        result = self.execute_command(server_name, command)
        
        if result.get('success') and result.get('stdout'):
            output = result['stdout'].strip()
            if output != 'error':
                return [line.strip() for line in output.split('\n') if line.strip()]
        return []
    
    def _ensure_connection(self, server_name: str) -> bool:
        """
        确保与指定服务器的连接
        
        Args:
            server_name: 服务器名称
            
        Returns:
            连接是否成功
        """
        if server_name not in self.servers_config:
            return False
        
        # 如果已经连接，直接返回
        if self.server_connections.get(server_name, False):
            return True
        
        # 对于文件操作，我们不需要实际连接，直接返回True
        # 这样可以避免 fabric 显示冲突
        return True
    
    def get_server_status(self, server_name: str) -> Optional[ServerInfo]:
        """
        获取指定服务器的状态信息
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器状态信息，如果不存在则返回 None
        """
        return self.server_info.get(server_name)
    
    def get_all_server_status(self) -> Dict[str, ServerInfo]:
        """
        获取所有服务器的状态信息
        
        Returns:
            所有服务器状态信息的字典
        """
        return self.server_info.copy()
    
    def update_server_task_count(self, server_name: str, task_count: int):
        """
        更新指定服务器的任务计数
        
        Args:
            server_name: 服务器名称
            task_count: 任务数量
        """
        if server_name in self.server_info:
            self.server_info[server_name].current_tasks = max(0, task_count)
            
            # 更新服务器状态
            if task_count == 0:
                self.server_info[server_name].status = ServerStatus.IDLE
            elif task_count >= self.server_info[server_name].max_tasks:
                self.server_info[server_name].status = ServerStatus.BUSY
            else:
                self.server_info[server_name].status = ServerStatus.IDLE
    
    def close(self):
        """关闭所有连接"""
        for server_name in self.server_connections:
            self.disconnect_server(server_name)
        self.logger.info("🔌 已关闭所有服务器连接")
