"""
文件操作模块

提供文件传输和远程文件管理功能。
"""

import os
import shutil
from typing import List, Optional, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()


class FileOperations:
    """文件操作类"""
    
    def __init__(self, manager):
        """
        初始化文件操作器
        
        Args:
            manager: ConnectionManager 实例
        """
        self.manager = manager
    
    def upload_file(self, name: str, local_path: str, remote_path: str, 
                   show_progress: bool = True) -> bool:
        """
        上传文件到远程服务器
        
        Args:
            name: 服务器名称
            remote_path: 远程路径
            local_path: 本地路径
            show_progress: 是否显示进度
            
        Returns:
            是否成功
        """
        if not os.path.exists(local_path):
            console.print(f"❌ 本地文件不存在: {local_path}")
            return False
        
        if name not in self.manager.connections:
            if not self.manager.connect(name):
                return False
        
        try:
            if show_progress:
                file_size = os.path.getsize(local_path)
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(f"上传文件到 {name}...", total=file_size)
                    
                    # 使用 fabric 的 put 方法上传文件
                    result = self.manager.connections[name].put(
                        local_path, 
                        remote_path,
                        preserve_mode=True
                    )
                    
                    if result.ok:
                        progress.update(task, completed=file_size)
                        console.print(f"✅ 文件上传成功: {local_path} -> {name}:{remote_path}")
                        return True
                    else:
                        console.print(f"❌ 文件上传失败: {result.stderr}")
                        return False
            else:
                result = self.manager.connections[name].put(
                    local_path, 
                    remote_path,
                    preserve_mode=True
                )
                
                if result.ok:
                    console.print(f"✅ 文件上传成功: {local_path} -> {name}:{remote_path}")
                    return True
                else:
                    console.print(f"❌ 文件上传失败: {result.stderr}")
                    return False
                    
        except Exception as e:
            console.print(f"❌ 上传文件时发生错误: {e}")
            return False
    
    def download_file(self, name: str, remote_path: str, local_path: str,
                     show_progress: bool = True) -> bool:
        """
        从远程服务器下载文件
        
        Args:
            name: 服务器名称
            remote_path: 远程路径
            local_path: 本地路径
            show_progress: 是否显示进度
            
        Returns:
            是否成功
        """
        if name not in self.manager.connections:
            if not self.manager.connect(name):
                return False
        
        try:
            # 确保本地目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            if show_progress:
                # 获取远程文件大小
                result = self.manager.execute(name, f"stat -c%s {remote_path}", hide=True)
                if result and result.ok:
                    file_size = int(result.stdout.strip())
                else:
                    file_size = 0
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(f"从 {name} 下载文件...", total=file_size)
                    
                    # 使用 fabric 的 get 方法下载文件
                    result = self.manager.connections[name].get(
                        remote_path, 
                        local_path
                    )
                    
                    if result.ok:
                        progress.update(task, completed=file_size)
                        console.print(f"✅ 文件下载成功: {name}:{remote_path} -> {local_path}")
                        return True
                    else:
                        console.print(f"❌ 文件下载失败: {result.stderr}")
                        return False
            else:
                result = self.manager.connections[name].get(
                    remote_path, 
                    local_path
                )
                
                if result.ok:
                    console.print(f"✅ 文件下载成功: {name}:{remote_path} -> {local_path}")
                    return True
                else:
                    console.print(f"❌ 文件下载失败: {result.stderr}")
                    return False
                    
        except Exception as e:
            console.print(f"❌ 下载文件时发生错误: {e}")
            return False
    
    def upload_directory(self, name: str, local_dir: str, remote_dir: str,
                        exclude: List[str] = None) -> bool:
        """
        上传目录到远程服务器
        
        Args:
            name: 服务器名称
            local_dir: 本地目录
            remote_dir: 远程目录
            exclude: 排除的文件/目录列表
            
        Returns:
            是否成功
        """
        if not os.path.exists(local_dir):
            console.print(f"❌ 本地目录不存在: {local_dir}")
            return False
        
        if exclude is None:
            exclude = ['.git', '__pycache__', '.pyc', '.DS_Store']
        
        try:
            # 创建远程目录
            self.manager.execute(name, f"mkdir -p {remote_dir}", hide=True)
            
            # 遍历本地目录
            for root, dirs, files in os.walk(local_dir):
                # 排除不需要的目录
                dirs[:] = [d for d in dirs if d not in exclude]
                
                # 计算相对路径
                rel_path = os.path.relpath(root, local_dir)
                if rel_path == '.':
                    remote_root = remote_dir
                else:
                    remote_root = os.path.join(remote_dir, rel_path)
                
                # 创建远程目录
                if rel_path != '.':
                    self.manager.execute(name, f"mkdir -p {remote_root}", hide=True)
                
                # 上传文件
                for file in files:
                    if any(file.endswith(ext) for ext in exclude):
                        continue
                    
                    local_file = os.path.join(root, file)
                    remote_file = os.path.join(remote_root, file)
                    
                    if not self.upload_file(name, local_file, remote_file, show_progress=False):
                        console.print(f"❌ 上传文件失败: {local_file}")
                        return False
            
            console.print(f"✅ 目录上传成功: {local_dir} -> {name}:{remote_dir}")
            return True
            
        except Exception as e:
            console.print(f"❌ 上传目录时发生错误: {e}")
            return False
    
    def download_directory(self, name: str, remote_dir: str, local_dir: str,
                          exclude: List[str] = None) -> bool:
        """
        从远程服务器下载目录
        
        Args:
            name: 服务器名称
            remote_dir: 远程目录
            local_dir: 本地目录
            exclude: 排除的文件/目录列表
            
        Returns:
            是否成功
        """
        if exclude is None:
            exclude = ['.git', '__pycache__', '.pyc', '.DS_Store']
        
        try:
            # 创建本地目录
            os.makedirs(local_dir, exist_ok=True)
            
            # 获取远程目录结构
            result = self.manager.execute(name, f"find {remote_dir} -type f", hide=True)
            if not result or not result.ok:
                console.print(f"❌ 无法获取远程目录结构: {remote_dir}")
                return False
            
            remote_files = result.stdout.strip().split('\n')
            
            for remote_file in remote_files:
                if not remote_file:
                    continue
                
                # 检查是否应该排除
                if any(ex in remote_file for ex in exclude):
                    continue
                
                # 计算相对路径
                rel_path = os.path.relpath(remote_file, remote_dir)
                local_file = os.path.join(local_dir, rel_path)
                
                # 创建本地目录
                os.makedirs(os.path.dirname(local_file), exist_ok=True)
                
                # 下载文件
                if not self.download_file(name, remote_file, local_file, show_progress=False):
                    console.print(f"❌ 下载文件失败: {remote_file}")
                    return False
            
            console.print(f"✅ 目录下载成功: {name}:{remote_dir} -> {local_dir}")
            return True
            
        except Exception as e:
            console.print(f"❌ 下载目录时发生错误: {e}")
            return False
    
    def list_remote_files(self, name: str, remote_path: str = ".") -> List[Dict[str, Any]]:
        """
        列出远程目录中的文件
        
        Args:
            name: 服务器名称
            remote_path: 远程路径
            
        Returns:
            文件信息列表
        """
        if name not in self.manager.connections:
            if not self.manager.connect(name):
                return []
        
        try:
            # 使用 ls -la 命令获取详细信息
            result = self.manager.execute(name, f"ls -la {remote_path}", hide=True)
            if not result or not result.ok:
                return []
            
            files = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines[1:]:  # 跳过总计行
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 9:
                    permissions = parts[0]
                    owner = parts[2]
                    group = parts[3]
                    size = parts[4]
                    date = ' '.join(parts[5:8])
                    name_part = parts[8]
                    
                    files.append({
                        'name': name_part,
                        'permissions': permissions,
                        'owner': owner,
                        'group': group,
                        'size': size,
                        'date': date,
                        'is_dir': permissions.startswith('d')
                    })
            
            return files
            
        except Exception as e:
            console.print(f"❌ 列出文件时发生错误: {e}")
            return []
    
    def delete_remote_file(self, name: str, remote_path: str) -> bool:
        """
        删除远程文件
        
        Args:
            name: 服务器名称
            remote_path: 远程路径
            
        Returns:
            是否成功
        """
        result = self.manager.execute(name, f"rm -f {remote_path}", hide=True)
        if result and result.ok:
            console.print(f"✅ 文件删除成功: {name}:{remote_path}")
            return True
        else:
            console.print(f"❌ 文件删除失败: {name}:{remote_path}")
            return False
    
    def delete_remote_directory(self, name: str, remote_path: str) -> bool:
        """
        删除远程目录
        
        Args:
            name: 服务器名称
            remote_path: 远程路径
            
        Returns:
            是否成功
        """
        result = self.manager.execute(name, f"rm -rf {remote_path}", hide=True)
        if result and result.ok:
            console.print(f"✅ 目录删除成功: {name}:{remote_path}")
            return True
        else:
            console.print(f"❌ 目录删除失败: {name}:{remote_path}")
            return False
    
    def create_remote_directory(self, name: str, remote_path: str) -> bool:
        """
        创建远程目录
        
        Args:
            name: 服务器名称
            remote_path: 远程路径
            
        Returns:
            是否成功
        """
        result = self.manager.execute(name, f"mkdir -p {remote_path}", hide=True)
        if result and result.ok:
            console.print(f"✅ 目录创建成功: {name}:{remote_path}")
            return True
        else:
            console.print(f"❌ 目录创建失败: {name}:{remote_path}")
            return False
    
    def change_remote_permissions(self, name: str, remote_path: str, permissions: str) -> bool:
        """
        修改远程文件权限
        
        Args:
            name: 服务器名称
            remote_path: 远程路径
            permissions: 权限字符串 (如 "755")
            
        Returns:
            是否成功
        """
        result = self.manager.execute(name, f"chmod {permissions} {remote_path}", hide=True)
        if result and result.ok:
            console.print(f"✅ 权限修改成功: {name}:{remote_path} -> {permissions}")
            return True
        else:
            console.print(f"❌ 权限修改失败: {name}:{remote_path}")
            return False
    
    def sync_directory(self, name: str, local_dir: str, remote_dir: str,
                      exclude: List[str] = None, direction: str = "upload") -> bool:
        """
        同步目录
        
        Args:
            name: 服务器名称
            local_dir: 本地目录
            remote_dir: 远程目录
            exclude: 排除的文件/目录列表
            direction: 同步方向 ("upload" 或 "download")
            
        Returns:
            是否成功
        """
        if direction == "upload":
            return self.upload_directory(name, local_dir, remote_dir, exclude)
        elif direction == "download":
            return self.download_directory(name, remote_dir, local_dir, exclude)
        else:
            console.print(f"❌ 不支持的同步方向: {direction}")
            return False 