"""
Event models for Labbook experiment execution

This module defines the event models for Labbook experiment execution:
- NetworkEventType: Network event type enumeration
- NetworkEvent: Unified network event structure
- NetFuncEvent: Network function execution event
- NetFuncExecOutputEvent: Network function execution output event
- NodeExecArgs: Node execution arguments
- NodeCreateArgs: Node creation arguments
- LinkProperties: Link properties with mode enumeration
- LinkCreateArgs: Link creation arguments
- InterfaceCreateArgs: Interface creation arguments

The events follow a unified structure where NetworkEvent contains all possible
event types and their associated arguments, making it easier to handle different
event types in a consistent manner.
"""

from typing import List, Optional, Union
from enum import Enum
from pydantic import Field
from .base import BaseLabbookModel
from .network import Node, InterfaceMode


class NetworkEventType(str, Enum):
    """Network event types for experiment execution"""
    
    NETWORK_LINK_CREATE = "network-link-create"        # Network link creation event
    NETWORK_LINK_ATTR_SET = "network-link-attr-set"    # Network link attribute setting event
    NETWORK_LINK_DESTROY = "network-link-destroy"      # Network link destruction event
    NETWORK_NODE_CREATE = "network-node-create"        # Network node creation event
    NETWORK_NODE_DESTROY = "network-node-destroy"      # Network node destruction event
    NETWORK_INTERFACE_CREATE = "network-interface-create"  # Network interface creation event
    NETWORK_INTERFACE_DESTROY = "network-interface-destroy"  # Network interface destruction event


class LinkPropertiesMode(str, Enum):
    """Link properties mode enumeration"""
    
    UP = "up"      # Enable link
    DOWN = "down"  # Disable link


class NodeExecArgs(BaseLabbookModel):
    """Node execution arguments for netfunc events"""
    
    key: Optional[str] = Field(None, alias="key", description="Command unique identifier, if empty, uses default identifier or script content")
    shellcodes: Optional[List[str]] = Field(None, alias="shellcodes", description="Script content, if empty, uses default script")
    daemon: Optional[bool] = Field(False, alias="daemon", description="Whether to run in background for long-term execution, supports cancel and timeout")
    output: Optional[str] = Field(None, alias="output", description="Output path, if empty, no output")
    timeout: Optional[int] = Field(0, alias="timeout", description="Timeout in seconds, 0 or -1 means no timeout")

    class Config:
        json_schema_extra = {
            "example": {
                "key": "test-command",
                "shellcodes": ["echo 'Hello World'", "ping -c 1 8.8.8.8"],
                "daemon": False,
                "output": "/tmp/output.log",
                "timeout": 30
            }
        }


class NodeCreateArgs(BaseLabbookModel):
    """Node creation arguments for network-node-create events"""
    
    node: Node = Field(..., alias="node", description="Node configuration")
    mount_path: Optional[str] = Field(None, alias="mount_path", description="Mount path, if empty, no mount")

    class Config:
        json_schema_extra = {
            "example": {
                "node": {
                    "name": "client-1",
                    "image": "ubuntu:20.04",
                    "interfaces": [
                        {
                            "name": "eth0",
                            "mode": "direct",
                            "ip": ["192.168.1.10/24"]
                        }
                    ]
                },
                "mount_path": "/tmp/mounts/client-1"
            }
        }


class LinkProperties(BaseLabbookModel):
    """Link properties for network-link-attr-set events"""
    
    mode: LinkPropertiesMode = Field(..., alias="mode", description="Link mode: 'up' or 'down'")
    bandwidth: Optional[str] = Field(None, alias="bandwidth", description="Bandwidth, e.g., '100Mbps'")
    loss: Optional[str] = Field(None, alias="loss", description="Packet loss rate, e.g., '0.00%'")
    delay: Optional[str] = Field(None, alias="delay", description="Delay, e.g., '10ms'")

    class Config:
        json_schema_extra = {
            "example": {
                "mode": "up",
                "bandwidth": "100Mbps",
                "loss": "0.00%",
                "delay": "10ms"
            }
        }


class LinkCreateArgs(BaseLabbookModel):
    """Link creation arguments for network-link-create events"""
    
    id: str = Field(..., alias="id", description="Link ID")
    endpoints: Optional[List[str]] = Field(None, alias="endpoints", description="Endpoint list")
    l2_switch_id: Optional[str] = Field(None, alias="l2_switch_id", description="L2 switch ID")
    static_neigh: Optional[bool] = Field(False, alias="static_neigh", description="Static neighbor, ignored if L2 switch is already acquired")
    no_arp: Optional[bool] = Field(False, alias="no_arp", description="No ARP resolution, ignored if L2 switch is already acquired")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "link-1",
                "endpoints": ["client-1:eth0", "server-1:eth0"],
                "l2_switch_id": "switch-1",
                "static_neigh": False,
                "no_arp": False
            }
        }


class InterfaceCreateArgs(BaseLabbookModel):
    """Interface creation arguments for network-interface-create events"""
    
    name: str = Field(..., alias="name", description="Interface name")
    mode: InterfaceMode = Field(..., alias="mode", description="Interface working mode")
    ip: Optional[List[str]] = Field(None, alias="ip", description="IP address list")
    mac: Optional[str] = Field(None, alias="mac", description="MAC address")
    vlan: Optional[int] = Field(None, alias="vlan", description="VLAN ID, non-zero indicates external interface")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "eth0",
                "mode": "direct",
                "ip": ["192.168.1.10/24"],
                "mac": "00:11:22:33:44:55",
                "vlan": 0
            }
        }


class NetworkEvent(BaseLabbookModel):
    """
    Unified network event structure
    
    Represents a network-related event with all possible event types and their
    associated arguments. The specific arguments are populated based on the event type.
    """
    
    type: NetworkEventType = Field(..., alias="type", description="Event type")
    node_name: Optional[str] = Field(None, alias="node_name", description="Node name (for network-node, netfunc-node events)")
    interface_name: Optional[str] = Field(None, alias="intf_name", description="Interface name (for network-interface events)")
    link_id: Optional[str] = Field(None, alias="link_id", description="Link ID (for network-link events)")
    node_create_args: Optional[NodeCreateArgs] = Field(None, alias="node_create_args", description="Node creation arguments")
    link_create_args: Optional[LinkCreateArgs] = Field(None, alias="link_create_args", description="Link creation arguments")
    link_properties: Optional[LinkProperties] = Field(None, alias="link_properties", description="Link properties")
    interface_create_args: Optional[InterfaceCreateArgs] = Field(None, alias="interface_create", description="Interface creation arguments")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "network-node-create",
                "node_name": "client-1",
                "node_create_args": {
                    "node": {
                        "name": "client-1",
                        "image": "ubuntu:20.04",
                        "interfaces": [
                            {
                                "name": "eth0",
                                "mode": "direct",
                                "ip": ["192.168.1.10/24"]
                            }
                        ]
                    },
                    "mount_path": "/tmp/mounts/client-1"
                }
            }
        }


class NetFuncEvent(BaseLabbookModel):
    """Network function execution event"""
    
    node_name: Optional[str] = Field(None, alias="node_name", description="Node name")
    exec_args: NodeExecArgs = Field(..., alias="exec_args", description="Execution arguments")

    class Config:
        json_schema_extra = {
            "example": {
                "node_name": "client-1",
                "exec_args": {
                    "key": "test-command",
                    "shellcodes": ["echo 'Hello World'"],
                    "daemon": False,
                    "timeout": 30
                }
            }
        }


class NetFuncExecOutputEvent(BaseLabbookModel):
    """Network function execution output event"""
    
    node_name: Optional[str] = Field(None, alias="node_name", description="Node name")
    exec_args: NodeExecArgs = Field(..., alias="exec_args", description="Execution arguments")

    class Config:
        json_schema_extra = {
            "example": {
                "node_name": "client-1",
                "exec_args": {
                    "key": "test-command",
                    "shellcodes": ["echo 'Hello World'"],
                    "daemon": False,
                    "output": "/tmp/output.log",
                    "timeout": 30
                }
            }
        } 