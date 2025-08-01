#!/usr/bin/env python3
"""
Labkit 远程管理器使用示例

展示如何使用 RemoteManager 进行远程服务器管理
"""

from server import RemoteManager


def basic_usage_example():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建远程管理器（无UI模式，适合编程调用）
    manager = RemoteManager(enable_ui=False)
    
    # 添加服务器
    success = manager.add_server(
        name="example-server",
        host="192.168.1.100",
        user="admin",
        password="password123"
    )
    print(f"添加服务器: {'成功' if success else '失败'}")
    
    # 连接服务器
    if manager.connect_server("example-server"):
        print("连接服务器: 成功")
        
        # 执行命令
        result = manager.execute_command("example-server", "uname -a")
        if result and result['success']:
            print(f"系统信息: {result['stdout']}")
        else:
            print("获取系统信息失败")
    else:
        print("连接服务器: 失败")


def batch_operation_example():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===")
    
    manager = RemoteManager(enable_ui=False)
    
    # 批量添加服务器
    servers = [
        {"name": "web1", "host": "192.168.1.101", "user": "admin"},
        {"name": "web2", "host": "192.168.1.102", "user": "admin"},
        {"name": "db1", "host": "192.168.1.103", "user": "admin"},
    ]
    
    for server in servers:
        manager.add_server(**server)
        print(f"添加服务器: {server['name']}")
    
    # 批量执行命令
    results = manager.batch_execute("echo 'Hello from $(hostname)'")
    print("\n批量执行结果:")
    for server, result in results.items():
        if result['success']:
            print(f"{server}: {result['stdout'].strip()}")
        else:
            print(f"{server}: 执行失败")


def service_management_example():
    """服务管理示例"""
    print("\n=== 服务管理示例 ===")
    
    manager = RemoteManager(enable_ui=False)
    
    # 假设已经添加了服务器
    server_name = "web-server"
    
    # 检查服务状态
    status = manager.manage_service(server_name, "nginx", "status")
    print(f"Nginx 服务状态: {status}")
    
    # 重启服务
    success = manager.manage_service(server_name, "nginx", "restart")
    print(f"重启 Nginx: {'成功' if success else '失败'}")


def file_operation_example():
    """文件操作示例"""
    print("\n=== 文件操作示例 ===")
    
    manager = RemoteManager(enable_ui=False)
    
    server_name = "web-server"
    
    # 上传文件
    success = manager.upload_file(
        server_name,
        "/local/path/config.conf",
        "/etc/nginx/config.conf"
    )
    print(f"上传文件: {'成功' if success else '失败'}")
    
    # 下载文件
    success = manager.download_file(
        server_name,
        "/var/log/nginx/access.log",
        "/local/access.log"
    )
    print(f"下载文件: {'成功' if success else '失败'}")


def system_info_example():
    """系统信息示例"""
    print("\n=== 系统信息示例 ===")
    
    manager = RemoteManager(enable_ui=False)
    
    server_name = "web-server"
    
    # 获取系统信息
    info = manager.get_system_info(server_name)
    if info:
        print("系统信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("获取系统信息失败")
    
    # 获取进程信息
    processes = manager.get_process_info(server_name, "nginx")
    if processes:
        print(f"\nNginx 进程信息:\n{processes}")
    else:
        print("获取进程信息失败")


def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    manager = RemoteManager(enable_ui=False)
    
    # 尝试执行命令
    result = manager.execute_command("non-existent-server", "echo 'test'")
    
    if result is None:
        print("服务器不存在或连接失败")
    elif not result['success']:
        print(f"命令执行失败: {result['stderr']}")
    else:
        print(f"命令执行成功: {result['stdout']}")


def interactive_mode_example():
    """交互模式示例"""
    print("\n=== 交互模式示例 ===")
    
    # 创建带UI的管理器
    manager = RemoteManager(enable_ui=True)
    
    # 显示横幅
    manager.show_banner()
    
    # 显示帮助
    manager.show_help()
    
    # 注意：interactive_mode() 会启动交互式会话
    # 在实际使用中，你可能想要注释掉这行
    # manager.interactive_mode()


def main():
    """主函数"""
    print("Labkit 远程管理器使用示例")
    print("=" * 50)
    
    # 运行各种示例
    basic_usage_example()
    batch_operation_example()
    service_management_example()
    file_operation_example()
    system_info_example()
    error_handling_example()
    interactive_mode_example()
    
    print("\n" + "=" * 50)
    print("示例运行完成！")


if __name__ == '__main__':
    main() 