# Labkit 远程服务器管理工具

基于 labkit.remote 库的命令行管理工具，提供：
- 服务器配置管理
- 远程命令执行
- 文件传输操作
- 系统监控
- 批量操作

## 概述

`RemoteManager` 是一个规范化的远程管理器类，提供了完整的远程服务器管理功能。该类支持两种使用模式：

1. **交互模式**：保留原有的交互式命令行界面
2. **编程模式**：以方法调用的方式被其他代码使用

## 架构设计

### 类层次结构

```
外部调用 → RemoteManager (主要入口)
    ↓
RemoteManager 内部使用 → ConnectionManager (底层实现)
    ↓
ConnectionManager 使用 → RemoteCommands, FileOperations, SystemMonitor
```

### 职责分离

- **RemoteManager**: 高层封装，提供完整的远程管理功能，包括UI交互和编程接口
- **ConnectionManager**: 底层实现，负责具体的远程连接管理和基础操作
- **RemoteCommands**: 远程命令执行功能
- **FileOperations**: 文件传输操作
- **SystemMonitor**: 系统监控功能

## 重构成果

### 1. 规范化的方法接口

所有功能都被重构为具有明确参数和返回值的方法：

```python
# 服务器管理
add_server(name, host, user, port=22, password=None, key_filename=None) -> bool
remove_server(name) -> bool
list_servers() -> Dict[str, Any]
connect_server(name) -> bool
disconnect_server(name) -> bool

# 命令执行
execute_command(name, command) -> Optional[Dict[str, Any]]
execute_stream_command(name, command) -> bool
start_interactive_shell(name) -> bool
batch_execute(command, servers=None) -> Dict[str, Any]

# 系统信息
get_system_info(name) -> Optional[Dict[str, str]]
get_process_info(name, pattern="") -> Optional[str]

# 服务管理
manage_service(name, service, action) -> Optional[bool]

# 文件操作
upload_file(name, local_path, remote_path) -> bool
download_file(name, remote_path, local_path) -> bool

# 监控
monitor_servers(servers=None) -> bool
```

### 2. UI控制机制

通过 `enable_ui` 参数控制是否显示界面输出：

```python
# 带UI的管理器（保留原有交互体验）
manager = RemoteManager(enable_ui=True)

# 无UI的管理器（用于编程调用）
manager = RemoteManager(enable_ui=False)
```

### 3. 完整的类型提示

所有方法都有完整的类型提示，便于IDE支持和代码维护：

```python
def add_server(self, name: str, host: str, user: str, port: int = 22, 
               password: Optional[str] = None, key_filename: Optional[str] = None) -> bool:
```

### 4. 统一的错误处理

所有方法都有统一的错误处理机制：

- 返回 `None` 表示操作失败或服务器不存在
- 返回 `False` 表示操作失败
- 返回 `True` 表示操作成功
- 返回字典表示操作结果数据

### 5. 保留原有功能

- ✅ 保留了所有原有的交互模式功能
- ✅ 命令行参数处理保持不变
- ✅ 交互式界面完全兼容
- ✅ Tab补全和命令历史功能保留
- ✅ 所有原有的命令和选项都可用

## API 文档

### 初始化

```python
from server import RemoteManager

# 创建带UI的管理器（默认）
manager = RemoteManager(enable_ui=True)

# 创建无UI的管理器（用于编程调用）
manager = RemoteManager(enable_ui=False)
```

### 服务器管理方法

#### 添加服务器

```python
success = manager.add_server(
    name="web-server",
    host="192.168.1.100",
    user="admin",
    port=22,
    password="password123",
    key_filename=None  # 可选，私钥文件路径
)
# 返回: bool - 是否添加成功
```

#### 删除服务器

```python
success = manager.remove_server("web-server")
# 返回: bool - 是否删除成功
```

#### 列出服务器

```python
servers = manager.list_servers()
# 返回: Dict[str, Any] - 服务器信息字典
# 格式: {
#   "server_name": {
#     "name": "显示名称",
#     "host": "主机地址",
#     "user": "用户名",
#     "port": 22,
#     "status": "connected|disconnected"
#   }
# }
```

#### 连接服务器

```python
connected = manager.connect_server("web-server")
# 返回: bool - 是否连接成功
```

#### 断开服务器连接

```python
disconnected = manager.disconnect_server("web-server")
# 返回: bool - 是否断开成功
```

### 命令执行方法

#### 执行命令

```python
result = manager.execute_command("web-server", "uname -a")
# 返回: Optional[Dict[str, Any]] - 执行结果
# 格式: {
#   "stdout": "标准输出",
#   "stderr": "标准错误",
#   "return_code": 0,
#   "success": True
# }
```

#### 流式执行命令

```python
success = manager.execute_stream_command("web-server", "tail -f /var/log/syslog")
# 返回: bool - 是否执行成功
# 注意：此方法会实时显示输出
```

#### 启动交互式Shell

```python
success = manager.start_interactive_shell("web-server")
# 返回: bool - 是否启动成功
# 注意：此方法会启动交互式会话
```

#### 批量执行命令

```python
results = manager.batch_execute("echo 'Hello from $(hostname)'", ["web1", "web2"])
# 返回: Dict[str, Any] - 各服务器的执行结果
# 格式: {
#   "web1": {"stdout": "...", "stderr": "...", "return_code": 0, "success": True},
#   "web2": {"stdout": "...", "stderr": "...", "return_code": 0, "success": True}
# }
```

### 系统信息方法

#### 获取系统信息

```python
info = manager.get_system_info("web-server")
# 返回: Optional[Dict[str, str]] - 系统信息
# 格式: {
#   "hostname": "服务器主机名",
#   "os": "操作系统信息",
#   "kernel": "内核版本",
#   "cpu": "CPU信息",
#   "memory": "内存信息",
#   "disk": "磁盘信息"
# }
```

#### 获取进程信息

```python
processes = manager.get_process_info("web-server", "nginx")
# 返回: Optional[str] - 进程信息字符串
```

### 服务管理方法

#### 管理服务

```python
# 检查服务状态
status = manager.manage_service("web-server", "nginx", "status")

# 启动服务
success = manager.manage_service("web-server", "nginx", "start")

# 停止服务
success = manager.manage_service("web-server", "nginx", "stop")

# 重启服务
success = manager.manage_service("web-server", "nginx", "restart")

# 返回: Optional[bool] - 操作是否成功
```

### 文件操作方法

#### 上传文件

```python
success = manager.upload_file("web-server", "/local/path/file.txt", "/remote/path/file.txt")
# 返回: bool - 是否上传成功
```

#### 下载文件

```python
success = manager.download_file("web-server", "/remote/path/config.conf", "/local/path/config.conf")
# 返回: bool - 是否下载成功
```

### 监控方法

#### 监控服务器

```python
success = manager.monitor_servers(["web1", "web2"])
# 返回: bool - 是否启动监控成功
# 注意：此方法会启动实时监控界面
```

### UI相关方法

#### 显示横幅

```python
manager.show_banner()
# 显示欢迎横幅（仅在enable_ui=True时有效）
```

#### 显示帮助

```python
manager.show_help()
# 显示帮助信息（仅在enable_ui=True时有效）
```

#### 交互模式

```python
manager.interactive_mode()
# 启动交互式命令行界面（仅在enable_ui=True时有效）
```

## 新增功能

### 1. 编程式API

现在可以通过方法调用的方式使用所有功能：

```python
from server import RemoteManager

manager = RemoteManager(enable_ui=False)

# 添加服务器
manager.add_server("web-server", "192.168.1.100", "admin", password="secret")

# 连接并执行命令
if manager.connect_server("web-server"):
    result = manager.execute_command("web-server", "uname -a")
    if result and result['success']:
        print(f"系统信息: {result['stdout']}")
```

### 2. 批量操作支持

支持对多个服务器进行批量操作：

```python
# 批量执行命令
results = manager.batch_execute("echo 'Hello from $(hostname)'", ["web1", "web2", "db1"])

# 批量获取系统信息
for server_name in manager.list_servers().keys():
    info = manager.get_system_info(server_name)
    if info:
        print(f"{server_name}: {info['hostname']}")
```

### 3. 错误处理改进

更好的错误处理和返回值：

```python
# 执行命令并处理错误
result = manager.execute_command("web-server", "some_command")
if result is None:
    print("服务器不存在或连接失败")
elif not result['success']:
    print(f"命令执行失败: {result['stderr']}")
else:
    print(f"命令执行成功: {result['stdout']}")
```

## 使用示例

### 基本使用

```python
from server import RemoteManager

# 创建管理器
manager = RemoteManager(enable_ui=False)

# 添加服务器
manager.add_server("prod-web", "192.168.1.100", "admin", password="secret")

# 连接并执行命令
if manager.connect_server("prod-web"):
    result = manager.execute_command("prod-web", "uname -a")
    if result and result['success']:
        print(f"系统信息: {result['stdout']}")
```

### 批量操作

```python
# 批量添加服务器
servers = [
    {"name": "web1", "host": "192.168.1.101", "user": "admin"},
    {"name": "web2", "host": "192.168.1.102", "user": "admin"},
    {"name": "db1", "host": "192.168.1.103", "user": "admin"},
]

for server in servers:
    manager.add_server(**server)

# 批量执行命令
results = manager.batch_execute("echo 'Server: $(hostname)'")
for server, result in results.items():
    if result['success']:
        print(f"{server}: {result['stdout']}")
```

### 服务管理

```python
# 检查服务状态
status = manager.manage_service("web-server", "nginx", "status")

# 重启服务
success = manager.manage_service("web-server", "nginx", "restart")
```

### 文件操作

```python
# 上传文件
success = manager.upload_file("web-server", "/local/config.conf", "/etc/nginx/config.conf")

# 下载文件
success = manager.download_file("web-server", "/var/log/nginx/access.log", "/local/access.log")
```

### 错误处理

```python
# 执行命令并处理错误
result = manager.execute_command("web-server", "some_command")
if result is None:
    print("服务器不存在或连接失败")
elif not result['success']:
    print(f"命令执行失败: {result['stderr']}")
else:
    print(f"命令执行成功: {result['stdout']}")
```

## 交互模式使用

### 启动交互模式

```bash
python server.py
```

### 可用命令

服务器管理:
- `list` - 列出所有服务器
- `add <name> <host> <user> [options]` - 添加服务器
- `remove <name>` - 删除服务器
- `connect <name>` - 连接到服务器
- `disconnect <name>` - 断开服务器连接

命令执行:
- `exec <name> <command>` - 在指定服务器执行命令
- `stream <name> <command>` - 流式执行命令（实时输出）
- `shell <name>` - 启动交互式 shell 会话
- `batch <command>` - 在所有服务器执行命令
- `info <name>` - 获取服务器系统信息
- `ps <name> [pattern]` - 查看进程信息

服务管理:
- `service <name> <service> <action>` - 管理服务 (start/stop/restart/status)

文件操作:
- `upload <name> <local> <remote>` - 上传文件
- `download <name> <remote> <local>` - 下载文件

监控功能:
- `monitor [servers]` - 实时监控服务器

交互功能:
- `help` - 显示帮助信息
- `history` - 显示命令历史
- `clear` - 清屏
- `exit/quit` - 退出程序

### 命令行使用示例

```bash
# 添加服务器
python server.py add web-server 192.168.1.100 admin --password secret

# 执行命令
python server.py exec web-server "uname -a"

# 批量执行
python server.py batch "echo 'Hello from $(hostname)'"

# 监控服务器
python server.py monitor web-server,db-server
```

## 兼容性

### 向后兼容

- ✅ 所有原有的命令行参数都保持不变
- ✅ 交互模式的功能完全保留
- ✅ 配置文件格式保持不变
- ✅ 命令历史文件格式保持不变

### 新增功能

- ✅ 编程式API调用
- ✅ 更好的错误处理
- ✅ 完整的类型提示
- ✅ 批量操作支持
- ✅ UI控制机制

## 注意事项

1. **UI控制**：通过 `enable_ui` 参数控制是否显示界面输出
2. **返回值**：所有方法都有明确的返回值类型，便于编程调用
3. **错误处理**：方法会返回 `None` 或 `False` 表示操作失败
4. **连接管理**：方法会自动处理服务器连接，无需手动连接
5. **类型提示**：所有方法都有完整的类型提示，便于IDE支持

## 测试验证

创建了完整的测试套件来验证重构后的功能：

- `test_api.py` - API功能测试
- `example_usage.py` - 使用示例

## 文件结构

```
labkit/remote/
├── server.py              # 重构后的主文件 (RemoteManager)
├── manager.py             # 底层连接管理 (ConnectionManager)
├── commands.py            # 远程命令执行
├── file_ops.py            # 文件传输操作
├── monitoring.py          # 系统监控
├── example_usage.py       # 使用示例
├── test_api.py           # API测试
└── README.md             # 完整文档
```

## 总结

这次重构成功地将原有的交互式服务器管理工具转换为规范化的API，同时保留了所有原有功能。主要成果包括：

1. **规范化接口**：所有功能都有明确的方法接口
2. **类型安全**：完整的类型提示支持
3. **错误处理**：统一的错误处理机制
4. **UI控制**：可选的UI输出控制
5. **向后兼容**：完全保留原有功能
6. **编程友好**：支持编程式调用
7. **批量操作**：支持批量服务器操作
8. **完整文档**：详细的API文档和使用示例
9. **架构清晰**：明确的职责分离和类层次结构

重构后的代码既保持了原有的易用性，又增加了编程调用的灵活性，可以更好地集成到其他系统中。 