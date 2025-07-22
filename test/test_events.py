#!/usr/bin/env python3
"""
Simple test script to verify the new event models work correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from labkit.models.events import (
    Event, EventType, NodeExecArgs, NodeCreateArgs, LinkCreateArgs,
    LinkProperties, InterfaceCreateArgs
)
from labkit.models.network import Node, Interface, InterfaceMode

def test_event_models():
    """Test creating various event models"""
    
    # Test NodeExecArgs
    exec_args = NodeExecArgs(
        key="test-command",
        shellcodes=["echo 'Hello World'", "ls -la"],
        daemon=False,
        output="/tmp/output.log",
        timeout=30
    )
    print("✓ NodeExecArgs created successfully")
    
    # Test LinkProperties
    link_props = LinkProperties(
        mode="up",
        bandwidth="100Mbps",
        loss="0.01%",
        delay="10ms"
    )
    print("✓ LinkProperties created successfully")
    
    # Test LinkCreateArgs
    link_create = LinkCreateArgs(
        id="link-1",
        endpoints=["node1:eth0", "node2:eth0"],
        l2_switch_id="switch-1",
        static_neigh=False,
        no_arp=False
    )
    print("✓ LinkCreateArgs created successfully")
    
    # Test InterfaceCreateArgs
    intf_create = InterfaceCreateArgs(
        name="eth0",
        mode=InterfaceMode.HOST,
        ip=["192.168.1.10/24"],
        mac="00:11:22:33:44:55",
        vlan=100
    )
    print("✓ InterfaceCreateArgs created successfully")
    
    # Test NodeCreateArgs
    node = Node(
        name="test-node",
        image="ubuntu:20.04",
        interfaces=[Interface(name="eth0", mode=InterfaceMode.HOST)]
    )
    node_create = NodeCreateArgs(
        node=node,
        mount_path="/host/path:/container/path"
    )
    print("✓ NodeCreateArgs created successfully")
    
    # Test Event with netfunc-exec
    event1 = Event(
        type=EventType.NETFUNC_EXEC,
        node_name="test-node",
        node_exec_args=exec_args
    )
    print("✓ Event with netfunc-exec created successfully")
    
    # Test Event with network-link-create
    event2 = Event(
        type=EventType.NETWORK_LINK_CREATE,
        link_create_args=link_create
    )
    print("✓ Event with network-link-create created successfully")
    
    # Test Event with network-interface-create
    event3 = Event(
        type=EventType.NETWORK_INTERFACE_CREATE,
        node_name="test-node",
        intf_name="eth0",
        interface_create=intf_create
    )
    print("✓ Event with network-interface-create created successfully")
    
    print("\n🎉 All event models created successfully!")

if __name__ == "__main__":
    test_event_models() 