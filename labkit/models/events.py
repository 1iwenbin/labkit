"""
Event models for Labbook experiment execution
"""

from typing import List, Optional
from enum import Enum
from pydantic import Field
from .base import BaseLabbookModel
from .network import Node, InterfaceMode


class EventType(str, Enum):
    """Event types for experiment execution"""

    NETFUNC_EXEC = "netfunc-exec"
    NETWORK_LINK_CREATE = "network-link-create"
    NETWORK_LINK_ATTR_SET = "network-link-attr-set"
    NETWORK_LINK_DESTROY = "network-link-destroy"
    NETWORK_NODE_CREATE = "network-node-create"
    NETWORK_NODE_DESTROY = "network-node-destroy"
    NETWORK_INTERFACE_CREATE = "network-interface-create"
    NETWORK_INTERFACE_DESTROY = "network-interface-destroy"





class NodeExecArgs(BaseLabbookModel):
    """Node execution arguments for netfunc-exec events"""

    key: Optional[str] = Field(None, description="Command unique identifier, if empty, uses default identifier or script content")
    shellcodes: Optional[List[str]] = Field(None, description="Script content, if empty, uses default script")
    daemon: Optional[bool] = Field(False, description="Whether to run in background for long-term execution, supports cancel and timeout")
    output: Optional[str] = Field(None, description="Output path, if empty, no output")
    timeout: Optional[int] = Field(0, description="Timeout in seconds, 0 means no timeout, -1 means no timeout")


class NodeCreateArgs(BaseLabbookModel):
    """Node creation arguments for network-node-create events"""

    node: Node = Field(..., description="Node configuration")
    mount_path: Optional[str] = Field(None, description="Mount path, if empty, no mount")


class LinkProperties(BaseLabbookModel):
    """Link properties for network-link-attr-set events"""

    mode: str = Field(..., description="Link mode: 'up' or 'down'")
    bandwidth: Optional[str] = Field(None, description="Bandwidth, e.g., '100Mbps'")
    loss: Optional[str] = Field(None, description="Packet loss rate, e.g., '0.00%'")
    delay: Optional[str] = Field(None, description="Delay, e.g., '10ms'")


class SwitchProperties(BaseLabbookModel):
    """L2 switch properties for link creation"""

    # Add switch properties as needed
    pass


class LinkCreateArgs(BaseLabbookModel):
    """Link creation arguments for network-link-create events"""

    id: str = Field(..., description="Link ID")
    endpoints: Optional[List[str]] = Field(None, description="Endpoint list")
    l2_switch_id: Optional[str] = Field(None, description="L2 switch ID")
    l2_properties: Optional[SwitchProperties] = Field(None, description="L2 switch properties")
    static_neigh: Optional[bool] = Field(False, description="Static neighbor, ignored if L2 switch is already acquired")
    no_arp: Optional[bool] = Field(False, description="No ARP resolution, ignored if L2 switch is already acquired")


class InterfaceCreateArgs(BaseLabbookModel):
    """Interface creation arguments for network-interface-create events"""

    name: str = Field(..., description="Interface name")
    mode: InterfaceMode = Field(..., description="Interface working mode")
    ip: Optional[List[str]] = Field(None, description="IP address list")
    mac: Optional[str] = Field(None, description="MAC address")
    vlan: Optional[int] = Field(None, description="VLAN ID, non-zero indicates external interface")


class Event(BaseLabbookModel):
    """Event definition for experiment execution"""

    type: EventType = Field(..., description="Event type")
    node_name: Optional[str] = Field(None, description="Node name for network-node and netfunc-node events")
    intf_name: Optional[str] = Field(None, description="Interface name for network-interface events")
    link_id: Optional[str] = Field(None, description="Link ID for network-link events")
    node_exec_args: Optional[NodeExecArgs] = Field(None, description="Node execution arguments for netfunc-exec events")
    node_create_args: Optional[NodeCreateArgs] = Field(None, description="Node creation arguments for network-node-create events")
    link_create_args: Optional[LinkCreateArgs] = Field(None, description="Link creation arguments for network-link-create events")
    link_attr: Optional[LinkProperties] = Field(None, description="Link properties for network-link-attr-set events")
    interface_create: Optional[InterfaceCreateArgs] = Field(None, description="Interface creation arguments for network-interface-create events") 