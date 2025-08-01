# Labkit 远程管理模块

基于 Fabric 的远程服务器管理工具，提供完整的远程管理功能。

## 功能特性

- 🔗 **连接管理**: 支持密码和密钥认证，自动连接管理
- ⚡ **命令执行**: 单机和批量命令执行
- 📁 **文件操作**: 文件上传下载、目录同步
- 📊 **系统监控**: 实时监控、指标收集、日志分析
- 🔧 **服务管理**: 服务启停、软件包安装、用户管理
- 📋 **配置管理**: JSON 配置文件支持，持久化配置

## 安装依赖

```bash
pip install fabric>=3.0.0
```

## 快速开始

### 基础使用

```python
from labkit.remote import RemoteManager

# 创建管理器
manager = RemoteManager()

# 添加服务器
manager.add_server(
    name="web-server",
    host="192.168.1.100",
    user="admin",
    password="your_password"
)

# 连接并执行命令
if manager.connect("web-server"):
    result = manager.execute("web-server", "uname -a")
    print(result.stdout)
```

### 命令执行

```python
from labkit.remote import RemoteCommands

manager = RemoteManager()
commands = RemoteCommands(manager)

# 获取系统信息
info = commands.get_system_info("web-server")

# 检查服务状态
status = commands.check_service_status("web-server", "nginx")

# 批量执行命令
results = commands.batch_execute("echo 'Hello from $(hostname)'")
```

### 文件操作

```python
from labkit.remote import FileOperations

manager = RemoteManager()
file_ops = FileOperations(manager)

# 上传文件
file_ops.upload_file("web-server", "local.txt", "/tmp/remote.txt")

# 下载文件
file_ops.download_file("web-server", "/var/log/syslog", "local_syslog.txt")

# 同步目录
file_ops.sync_directory("web-server", "local_configs", "/etc/app/config")
```

### 系统监控

```python
from labkit.remote import SystemMonitor

manager = RemoteManager()
monitor = SystemMonitor(manager)

# 收集指标
metrics = monitor.collect_metrics("web-server")
print(f"CPU: {metrics.cpu_usage:.1f}%")
print(f"内存: {metrics.memory_usage:.1f}%")

# 实时监控
monitor.start_monitoring(interval=5)

# 监控日志
monitor.monitor_log_file("web-server", "/var/log/nginx/access.log")
```

## 详细功能

### RemoteManager

远程管理器主类，负责连接管理和基础操作。

#### 主要方法

- `add_server(name, **kwargs)`: 添加服务器配置
- `connect(name)`: 连接到指定服务器
- `disconnect(name)`: 断开连接
- `execute(name, command)`: 执行命令
- `execute_all(command)`: 在所有服务器上执行命令
- `list_servers()`: 列出所有服务器

#### 服务器配置参数

```python
manager.add_server(
    name="server-name",
    host="192.168.1.100",
    user="admin",
    port=22,
    password="password",           # 密码认证
    key_filename="~/.ssh/id_rsa", # 密钥认证
    connect_timeout=10,           # 连接超时
    command_timeout=300           # 命令超时
)
```

### RemoteCommands

命令执行类，提供常用的系统管理命令。

#### 主要方法

- `get_system_info(name)`: 获取系统信息
- `get_process_info(name, pattern)`: 获取进程信息
- `check_service_status(name, service)`: 检查服务状态
- `start_service(name, service)`: 启动服务
- `stop_service(name, service)`: 停止服务
- `install_package(name, package)`: 安装软件包
- `update_system(name)`: 更新系统
- `create_user(name, username, password, sudo)`: 创建用户
- `batch_execute(command, servers)`: 批量执行命令
- `monitor_servers(servers, interval)`: 监控服务器状态

### FileOperations

文件操作类，提供文件传输和管理功能。

#### 主要方法

- `upload_file(name, local_path, remote_path)`: 上传文件
- `download_file(name, remote_path, local_path)`: 下载文件
- `upload_directory(name, local_dir, remote_dir)`: 上传目录
- `download_directory(name, remote_dir, local_dir)`: 下载目录
- `list_remote_files(name, remote_path)`: 列出远程文件
- `delete_remote_file(name, remote_path)`: 删除远程文件
- `create_remote_directory(name, remote_path)`: 创建远程目录
- `sync_directory(name, local_dir, remote_dir)`: 同步目录

### SystemMonitor

系统监控类，提供实时监控和日志分析。

#### 主要方法

- `collect_metrics(name)`: 收集系统指标
- `start_monitoring(servers, interval)`: 开始监控
- `display_metrics(servers)`: 显示指标表格
- `monitor_log_file(name, log_file, grep_pattern)`: 监控日志文件
- `analyze_logs(name, log_file, hours)`: 分析日志
- `export_metrics(filename)`: 导出指标数据
- `generate_report(servers)`: 生成监控报告

## 配置文件

服务器配置可以保存到 JSON 文件中：

```json
{
  "web-server": {
    "host": "192.168.1.100",
    "user": "admin",
    "port": 22,
    "password": "password",
    "connect_timeout": 10,
    "command_timeout": 300
  },
  "db-server": {
    "host": "192.168.1.101",
    "user": "admin",
    "key_filename": "~/.ssh/id_rsa",
    "connect_timeout": 30,
    "command_timeout": 600
  }
}
```

使用配置文件：

```python
manager = RemoteManager("servers.json")
```

## 使用示例

### 批量部署

```python
from labkit.remote import RemoteManager, RemoteCommands, FileOperations

manager = RemoteManager()
commands = RemoteCommands(manager)
file_ops = FileOperations(manager)

# 添加多个服务器
servers = ["web1", "web2", "web3"]
for server in servers:
    manager.add_server(
        name=server,
        host=f"192.168.1.{100 + int(server[-1])}",
        user="admin",
        password="password"
    )

# 批量更新系统
for server in servers:
    commands.update_system(server)

# 批量安装软件包
for server in servers:
    commands.install_package(server, "nginx")

# 同步配置文件
for server in servers:
    file_ops.sync_directory(server, "configs", "/etc/nginx")

# 重启服务
for server in servers:
    commands.restart_service(server, "nginx")
```

### 实时监控

```python
from labkit.remote import RemoteManager, SystemMonitor

manager = RemoteManager()
monitor = SystemMonitor(manager)

# 添加监控服务器
manager.add_server(name="monitor-server", host="192.168.1.100", user="admin", password="password")

# 开始实时监控
monitor.start_monitoring(interval=5)

# 监控特定日志
monitor.monitor_log_file("monitor-server", "/var/log/nginx/error.log", "ERROR")
```

### 文件备份

```python
from labkit.remote import RemoteManager, FileOperations

manager = RemoteManager()
file_ops = FileOperations(manager)

# 添加服务器
manager.add_server(name="backup-server", host="192.168.1.100", user="admin", password="password")

# 备份重要文件
backup_files = [
    ("/etc/nginx/nginx.conf", "backups/nginx.conf"),
    ("/etc/mysql/my.cnf", "backups/mysql.cnf"),
    ("/var/log/syslog", "backups/syslog")
]

for remote_file, local_file in backup_files:
    file_ops.download_file("backup-server", remote_file, local_file)
```

## 注意事项

1. **安全性**: 不要在代码中硬编码密码，建议使用 SSH 密钥认证
2. **权限**: 某些命令需要 sudo 权限，确保用户有相应权限
3. **网络**: 确保网络连接稳定，设置合适的超时时间
4. **并发**: 大量并发操作可能影响服务器性能，建议控制并发数量

## 错误处理

模块提供了完善的错误处理机制：

```python
try:
    result = manager.execute("server", "some_command")
    if result and result.ok:
        print("命令执行成功")
    else:
        print(f"命令执行失败: {result.stderr}")
except Exception as e:
    print(f"发生错误: {e}")
```

## 扩展功能

模块设计为可扩展的，你可以：

1. 继承现有类添加自定义功能
2. 创建新的监控指标
3. 添加自定义命令执行器
4. 实现特定的文件传输协议

## 许可证

本模块遵循项目的整体许可证。 