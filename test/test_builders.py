#!/usr/bin/env python3
"""
Test script for Network Topology Builder
演示高级网络拓扑构建抽象的使用
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from labkit import (
    NetworkBuilder, NodeBuilder, PlaybookBuilder, ProcedureBuilder, LabbookBuilder,
    create_simple_network, create_labbook,
    build_star_topology, build_linear_topology, build_mesh_topology,
    save_experiment, InterfaceMode
)
from labkit.models.playbook import ConditionType

def test_network_builder():
    """测试网络构建器"""
    print("🧪 测试网络构建器...")
    
    # 创建网络构建器
    builder = NetworkBuilder()
    
    # 添加镜像
    builder.add_image("ubuntu", "library/ubuntu", "20.04")
    builder.add_image("router", "frrouting/frr", "latest")
    
    # 添加节点
    client = builder.add_node("client", "ubuntu")
    client.add_interface("eth0", InterfaceMode.SWITCHED, ["192.168.1.10/24"])
    client.add_volume("/data/client", "/mnt/data", "rw")
    client.set_ext(role="client")
    client.done()
    
    router = builder.add_node("router", "router")
    router.add_interface("eth0", InterfaceMode.SWITCHED, ["192.168.1.1/24"])
    router.add_interface("eth1", InterfaceMode.SWITCHED, ["10.0.0.1/24"])
    router.set_ext(role="router")
    router.done()
    
    server = builder.add_node("server", "ubuntu")
    server.add_interface("eth0", InterfaceMode.SWITCHED, ["10.0.0.10/24"])
    server.add_volume("/data/server", "/mnt/data", "rw")
    server.set_ext(role="server")
    server.done()
    
    # 添加交换机
    builder.add_switch("lan1", static_neigh=True)
    builder.add_switch("lan2", static_neigh=True)
    
    # 连接节点
    builder.connect("client", "eth0", "router", "eth0", "lan1")
    builder.connect("router", "eth1", "server", "eth0", "lan2")
    
    # 构建网络配置
    network_config = builder.build()
    print("✅ 网络构建器测试通过")
    return network_config

def test_playbook_builder():
    """测试剧本构建器"""
    print("🧪 测试剧本构建器...")
    
    builder = PlaybookBuilder()
    
    # 添加条件
    builder.add_condition(
        "network_ready",
        ConditionType.COMMAND,
        "ping -c 1 8.8.8.8",
        "client"
    )
    
    # 添加流程
    proc = builder.add_procedure("connectivity_test", "10s")
    proc.add_step("等待网络就绪", wait_for="network_ready")
    proc.add_step("测试连通性", action_source="events/test_connectivity.yaml")
    proc.done()
    
    playbook = builder.build()
    print("✅ 剧本构建器测试通过")
    return playbook

def test_labbook_builder():
    """测试实验构建器"""
    print("🧪 测试实验构建器...")
    
    # 创建实验构建器
    labbook_builder = create_labbook(
        "simple_connectivity_test",
        "A simple connectivity test between client and server"
    )
    
    # 设置元数据
    labbook_builder.set_metadata(
        version="1.0",
        author="Test User",
        created_at="2024-01-01T00:00:00Z"
    )
    
    # 构建网络
    network = test_network_builder()
    labbook_builder.network_builder = NetworkBuilder()
    # 这里需要手动设置网络配置，因为构建器是独立的
    
    # 构建剧本
    playbook = test_playbook_builder()
    labbook_builder.playbook_builder = PlaybookBuilder()
    # 这里需要手动设置剧本配置
    
    # 构建完整实验
    labbook = labbook_builder.build()
    print("✅ 实验构建器测试通过")
    return labbook

def test_topology_templates():
    """测试拓扑模板"""
    print("🧪 测试拓扑模板...")
    
    # 星型拓扑
    star_network = build_star_topology(
        center_node="hub",
        edge_nodes=["node1", "node2", "node3"]
    )
    print("✅ 星型拓扑构建成功")
    
    # 线性拓扑
    linear_network = build_linear_topology(
        nodes=["node1", "node2", "node3", "node4"]
    )
    print("✅ 线性拓扑构建成功")
    
    # 网状拓扑
    mesh_network = build_mesh_topology(
        nodes=["node1", "node2", "node3"]
    )
    print("✅ 网状拓扑构建成功")
    
    return star_network, linear_network, mesh_network

def test_fluent_api():
    """测试流式 API"""
    print("🧪 测试流式 API...")
    
    # 使用流式 API 构建网络
    network = (NetworkBuilder()
               .add_image("ubuntu", "library/ubuntu", "20.04")
               .add_node("node1", "ubuntu")
               .add_interface("eth0", InterfaceMode.HOST, ["192.168.1.10/24"])
               .done()
               .add_node("node2", "ubuntu")
               .add_interface("eth0", InterfaceMode.HOST, ["192.168.1.11/24"])
               .done()
               .connect("node1", "eth0", "node2", "eth0")
               .build())
    
    print("✅ 流式 API 测试通过")
    return network

def test_save_experiment():
    """测试保存实验"""
    print("🧪 测试保存实验...")
    
    # 创建简单实验
    labbook_builder = create_labbook("test_experiment", "Test experiment")
    labbook = labbook_builder.build()
    
    # 保存到 fixtures 目录
    output_dir = save_experiment(labbook, "fixtures/test_builder_experiment")
    print(f"✅ 实验已保存到: {output_dir}")
    
    return output_dir

def main():
    """运行所有构建器测试"""
    print("🔨 Network Topology Builder Tests\n")
    
    # 测试各个构建器
    test_network_builder()
    test_playbook_builder()
    test_labbook_builder()
    test_topology_templates()
    test_fluent_api()
    test_save_experiment()
    
    print("\n🎉 所有构建器测试完成！")
    print("\n💡 使用示例:")
    print("""
# 创建简单网络
builder = NetworkBuilder()
builder.add_image("ubuntu", "library/ubuntu", "20.04")
node = builder.add_node("test-node", "ubuntu")
node.add_interface("eth0", InterfaceMode.HOST, ["192.168.1.10/24"])
node.done()
network = builder.build()

# 使用拓扑模板
star_network = build_star_topology("hub", ["node1", "node2", "node3"])

# 创建完整实验
labbook = create_labbook("my_experiment", "My test experiment")
labbook.set_metadata(author="Me")
experiment = labbook.build()

# 保存实验
save_experiment(experiment, "./my_experiment")
    """)

if __name__ == "__main__":
    main() 