"""
远程管理模块测试

用于测试远程管理模块的基本功能。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from labkit.remote import RemoteManager, RemoteCommands, FileOperations, SystemMonitor


class TestRemoteManager(unittest.TestCase):
    """测试远程管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = RemoteManager()
    
    def test_add_server(self):
        """测试添加服务器"""
        self.manager.add_server(
            name="test-server",
            host="192.168.1.100",
            user="admin",
            password="password"
        )
        
        self.assertIn("test-server", self.manager.servers)
        server = self.manager.servers["test-server"]
        self.assertEqual(server.host, "192.168.1.100")
        self.assertEqual(server.user, "admin")
    
    def test_remove_server(self):
        """测试移除服务器"""
        self.manager.add_server(
            name="test-server",
            host="192.168.1.100",
            user="admin"
        )
        
        self.manager.remove_server("test-server")
        self.assertNotIn("test-server", self.manager.servers)
    
    def test_list_servers(self):
        """测试列出服务器"""
        self.manager.add_server(
            name="server1",
            host="192.168.1.100",
            user="admin"
        )
        self.manager.add_server(
            name="server2",
            host="192.168.1.101",
            user="admin"
        )
        
        # 这里只是测试方法不会抛出异常
        self.manager.list_servers()


class TestRemoteCommands(unittest.TestCase):
    """测试远程命令执行"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = RemoteManager()
        self.commands = RemoteCommands(self.manager)
        
        # 添加测试服务器
        self.manager.add_server(
            name="test-server",
            host="192.168.1.100",
            user="admin"
        )
    
    def test_get_system_info(self):
        """测试获取系统信息"""
        # 模拟连接和执行命令
        with patch.object(self.manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_result.stdout = "Linux test-server 5.4.0-generic"
            mock_execute.return_value = mock_result
            
            info = self.commands.get_system_info("test-server")
            self.assertIn('os', info)
    
    def test_check_service_status(self):
        """测试检查服务状态"""
        with patch.object(self.manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_result.stdout = "active"
            mock_execute.return_value = mock_result
            
            status = self.commands.check_service_status("test-server", "nginx")
            self.assertEqual(status, "active")


class TestFileOperations(unittest.TestCase):
    """测试文件操作"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = RemoteManager()
        self.file_ops = FileOperations(self.manager)
        
        # 添加测试服务器
        self.manager.add_server(
            name="test-server",
            host="192.168.1.100",
            user="admin"
        )
    
    def test_create_remote_directory(self):
        """测试创建远程目录"""
        with patch.object(self.manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_execute.return_value = mock_result
            
            success = self.file_ops.create_remote_directory("test-server", "/tmp/test")
            self.assertTrue(success)
    
    def test_delete_remote_file(self):
        """测试删除远程文件"""
        with patch.object(self.manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_execute.return_value = mock_result
            
            success = self.file_ops.delete_remote_file("test-server", "/tmp/test.txt")
            self.assertTrue(success)


class TestSystemMonitor(unittest.TestCase):
    """测试系统监控"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = RemoteManager()
        self.monitor = SystemMonitor(self.manager)
        
        # 添加测试服务器
        self.manager.add_server(
            name="test-server",
            host="192.168.1.100",
            user="admin"
        )
    
    def test_collect_metrics(self):
        """测试收集指标"""
        with patch.object(self.manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_result.stdout = "50.0"
            mock_execute.return_value = mock_result
            
            metrics = self.monitor.collect_metrics("test-server")
            self.assertIsNotNone(metrics)
            self.assertEqual(metrics.timestamp.__class__.__name__, 'datetime')
    
    def test_get_cpu_usage(self):
        """测试获取CPU使用率"""
        with patch.object(self.manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_result.stdout = "25.5"
            mock_execute.return_value = mock_result
            
            cpu_usage = self.monitor.get_cpu_usage("test-server")
            self.assertEqual(cpu_usage, 25.5)
    
    def test_get_memory_usage(self):
        """测试获取内存使用率"""
        with patch.object(self.manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_result.stdout = "65.2"
            mock_execute.return_value = mock_result
            
            memory_usage = self.monitor.get_memory_usage("test-server")
            self.assertEqual(memory_usage, 65.2)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_manager_with_commands(self):
        """测试管理器与命令执行器的集成"""
        manager = RemoteManager()
        commands = RemoteCommands(manager)
        
        # 添加服务器
        manager.add_server(
            name="test-server",
            host="192.168.1.100",
            user="admin"
        )
        
        # 测试批量执行
        with patch.object(manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_result.stdout = "Hello from test-server"
            mock_execute.return_value = mock_result
            
            results = commands.batch_execute("echo 'Hello from $(hostname)'")
            self.assertIsInstance(results, dict)
    
    def test_manager_with_file_ops(self):
        """测试管理器与文件操作的集成"""
        manager = RemoteManager()
        file_ops = FileOperations(manager)
        
        # 添加服务器
        manager.add_server(
            name="test-server",
            host="192.168.1.100",
            user="admin"
        )
        
        # 测试文件操作
        with patch.object(manager, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.ok = True
            mock_execute.return_value = mock_result
            
            success = file_ops.create_remote_directory("test-server", "/tmp/test")
            self.assertTrue(success)


def run_tests():
    """运行所有测试"""
    print("开始运行远程管理模块测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestRemoteManager,
        TestRemoteCommands,
        TestFileOperations,
        TestSystemMonitor,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    print(f"\n测试结果:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1) 