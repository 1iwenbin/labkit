"""
远程管理模块使用示例

展示如何使用 labkit.remote 模块进行远程服务器管理。
"""

from labkit.remote import RemoteManager, RemoteCommands, FileOperations, SystemMonitor


def basic_usage_example():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 创建远程管理器
    manager = RemoteManager()
    
    # 添加服务器配置
    manager.add_server(
        name="web-server",
        host="192.168.1.100",
        user="admin",
        port=22,
        password="your_password"  # 或使用 key_filename
    )
    
    # 列出所有服务器
    manager.list_servers()
    
    # 连接到服务器
    if manager.connect("web-server"):
        # 执行命令
        result = manager.execute("web-server", "uname -a")
        if result:
            print(f"系统信息: {result.stdout}")
    
    # 断开连接
    manager.disconnect_all()


def commands_example():
    """命令执行示例"""
    print("\n=== 命令执行示例 ===")
    
    manager = RemoteManager()
    commands = RemoteCommands(manager)
    
    # 添加测试服务器
    manager.add_server(
        name="test-server",
        host="192.168.1.101",
        user="admin",
        password="password"
    )
    
    # 获取系统信息
    info = commands.get_system_info("test-server")
    print("系统信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # 检查服务状态
    status = commands.check_service_status("test-server", "nginx")
    print(f"Nginx 服务状态: {status}")
    
    # 批量执行命令
    results = commands.batch_execute("echo 'Hello from $(hostname)'")
    for server, result in results.items():
        print(f"{server}: {result.stdout}")


def file_operations_example():
    """文件操作示例"""
    print("\n=== 文件操作示例 ===")
    
    manager = RemoteManager()
    file_ops = FileOperations(manager)
    
    # 添加服务器
    manager.add_server(
        name="file-server",
        host="192.168.1.102",
        user="admin",
        password="password"
    )
    
    # 上传文件
    success = file_ops.upload_file(
        "file-server",
        "local_file.txt",
        "/tmp/remote_file.txt"
    )
    print(f"文件上传: {'成功' if success else '失败'}")
    
    # 下载文件
    success = file_ops.download_file(
        "file-server",
        "/var/log/syslog",
        "local_syslog.txt"
    )
    print(f"文件下载: {'成功' if success else '失败'}")
    
    # 列出远程文件
    files = file_ops.list_remote_files("file-server", "/tmp")
    print("远程文件列表:")
    for file_info in files:
        print(f"  {file_info['name']} ({file_info['size']} bytes)")


def monitoring_example():
    """监控示例"""
    print("\n=== 监控示例 ===")
    
    manager = RemoteManager()
    monitor = SystemMonitor(manager)
    
    # 添加服务器
    manager.add_server(
        name="monitor-server",
        host="192.168.1.103",
        user="admin",
        password="password"
    )
    
    # 收集一次指标
    metrics = monitor.collect_metrics("monitor-server")
    print(f"CPU 使用率: {metrics.cpu_usage:.1f}%")
    print(f"内存使用率: {metrics.memory_usage:.1f}%")
    print(f"磁盘使用率: {metrics.disk_usage:.1f}%")
    
    # 显示指标表格
    monitor.display_metrics()
    
    # 监控日志文件
    # monitor.monitor_log_file("monitor-server", "/var/log/nginx/access.log", "ERROR")


def advanced_example():
    """高级功能示例"""
    print("\n=== 高级功能示例 ===")
    
    manager = RemoteManager()
    commands = RemoteCommands(manager)
    file_ops = FileOperations(manager)
    monitor = SystemMonitor(manager)
    
    # 添加多个服务器
    servers = [
        {"name": "web1", "host": "192.168.1.110", "user": "admin", "password": "pass1"},
        {"name": "web2", "host": "192.168.1.111", "user": "admin", "password": "pass2"},
        {"name": "db1", "host": "192.168.1.112", "user": "admin", "password": "pass3"},
    ]
    
    for server_config in servers:
        manager.add_server(**server_config)
    
    # 批量更新系统
    print("批量更新系统...")
    for server_name in manager.servers.keys():
        success = commands.update_system(server_name)
        print(f"{server_name}: {'成功' if success else '失败'}")
    
    # 批量安装软件包
    print("批量安装软件包...")
    for server_name in manager.servers.keys():
        success = commands.install_package(server_name, "htop")
        print(f"{server_name} 安装 htop: {'成功' if success else '失败'}")
    
    # 同步配置文件
    print("同步配置文件...")
    for server_name in manager.servers.keys():
        success = file_ops.sync_directory(
            server_name,
            "local_configs",
            "/etc/app/config",
            exclude=[".git", "*.tmp"]
        )
        print(f"{server_name} 配置同步: {'成功' if success else '失败'}")
    
    # 生成监控报告
    print("生成监控报告...")
    monitor.generate_report()


def configuration_example():
    """配置管理示例"""
    print("\n=== 配置管理示例 ===")
    
    # 使用自定义配置文件
    manager = RemoteManager("custom_servers.json")
    
    # 添加服务器配置
    manager.add_server(
        name="production-web",
        host="prod.example.com",
        user="deploy",
        key_filename="~/.ssh/id_rsa",
        connect_timeout=30,
        command_timeout=600
    )
    
    manager.add_server(
        name="staging-web",
        host="staging.example.com",
        user="deploy",
        key_filename="~/.ssh/id_rsa"
    )
    
    # 列出配置
    manager.list_servers()
    
    # 移除服务器
    # manager.remove_server("staging-web")


def context_manager_example():
    """上下文管理器示例"""
    print("\n=== 上下文管理器示例 ===")
    
    # 使用 with 语句自动管理连接
    with RemoteManager() as manager:
        manager.add_server(
            name="temp-server",
            host="192.168.1.200",
            user="admin",
            password="password"
        )
        
        if manager.connect("temp-server"):
            result = manager.execute("temp-server", "hostname")
            if result:
                print(f"服务器主机名: {result.stdout.strip()}")
    
    # 连接会在退出时自动断开


if __name__ == "__main__":
    print("Labkit 远程管理模块使用示例")
    print("=" * 50)
    
    # 运行各种示例
    basic_usage_example()
    commands_example()
    file_operations_example()
    monitoring_example()
    advanced_example()
    configuration_example()
    context_manager_example()
    
    print("\n示例运行完成！") 