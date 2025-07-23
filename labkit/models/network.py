"""
Network topology models for Labbook specification (aligned with Go version)

This module defines the network topology models for Labbook experiments:
- InterfaceMode: Virtual network interface working modes
- VolumeMount: Container volume mount configuration
- Interface: Network interface configuration
- Node: Network node configuration
- SwitchProperties: Switch properties configuration
- L2Switch: L2 switch configuration
- Link: Network link configuration
- ImageType: Image type enumeration
- Image: Image configuration
- NetworkConfig: Complete network configuration

The network models implement utility functions for:
- Creating objects from internal models
- Endpoint string handling
- YAML file I/O operations
- Network topology conversion
"""

from typing import List, Optional, Dict, Any
from enum import Enum
import os
from pydantic import Field, ConfigDict
from .base import BaseLabbookModel


class InterfaceMode(str, Enum):
    """Virtual network interface working modes"""
    
    DIRECT = "direct"    # Direct mode: directly connected to another interface
    SWITCHED = "switched"  # Switched mode: connected through a switch
    GATEWAY = "gateway"    # Gateway mode: acts as a gateway interface
    HOST = "host"          # Host mode: connected to host network


class VolumeMount(BaseLabbookModel):
    """Container volume mount configuration"""
    
    host_path: str = Field(..., alias="host_path", description="Host path")
    container_path: str = Field(..., alias="container_path", description="Container path")
    mode: str = Field(..., alias="mode", description="Mount mode (rw, ro, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "host_path": "/tmp/data",
                "container_path": "/data",
                "mode": "rw"
            }
        }


class Interface(BaseLabbookModel):
    """Network interface configuration"""
    
    name: str = Field(..., alias="name", description="Interface name")
    mode: InterfaceMode = Field(..., alias="mode", description="Interface working mode")
    ip_list: Optional[List[str]] = Field(None, alias="ip", description="IP address list")
    mac: Optional[str] = Field(None, alias="mac", description="MAC address")
    vlan: Optional[int] = Field(None, alias="vlan", description="VLAN ID, non-zero means external interface")

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


class Node(BaseLabbookModel):
    """Network node configuration"""
    
    name: str = Field(..., alias="name", description="Node name")
    image: str = Field(..., alias="image", description="Container image")
    interfaces: List[Interface] = Field(..., alias="interfaces", description="Network interfaces")
    volumes: Optional[List[VolumeMount]] = Field(None, alias="volumes", description="Volume mounts")
    ext: Optional[Dict[str, Any]] = Field(None, alias="ext", description="Extension config")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "client-1",
                "image": "ubuntu:20.04",
                "interfaces": [
                    {
                        "name": "eth0",
                        "mode": "direct",
                        "ip": ["192.168.1.10/24"]
                    }
                ],
                "volumes": [
                    {
                        "host_path": "/tmp/data",
                        "container_path": "/data",
                        "mode": "rw"
                    }
                ]
            }
        }


class SwitchProperties(BaseLabbookModel):
    """Switch properties configuration"""
    
    static_neigh: Optional[bool] = Field(False, alias="static_neigh", description="Use static neighbor table (true means L2 domain can have multiple links)")
    no_arp: Optional[bool] = Field(False, alias="no_arp", description="Disable ARP (true means can use eBPF N x N network)")

    class Config:
        json_schema_extra = {
            "example": {
                "static_neigh": False,
                "no_arp": False
            }
        }


class L2Switch(BaseLabbookModel):
    """L2 switch configuration"""
    
    id: str = Field(..., alias="id", description="Switch ID")
    properties: Optional[SwitchProperties] = Field(None, alias="properties", description="Switch properties")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "switch-1",
                "properties": {
                    "static_neigh": False,
                    "no_arp": False
                }
            }
        }


class Link(BaseLabbookModel):
    """Network link configuration"""
    
    id: str = Field(..., alias="id", description="Link ID")
    endpoints: List[str] = Field(..., alias="endpoints", description="Endpoint list (format: node:interface)")
    switch: Optional[str] = Field(None, alias="switch", description="Switch ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "link-1",
                "endpoints": ["client-1:eth0", "server-1:eth0"],
                "switch": "switch-1"
            }
        }


class ImageType(str, Enum):
    """Image type enumeration"""
    
    REGISTRY = "registry"           # Docker registry image
    DOCKER_ARCHIVE = "docker-archive"  # Docker archive image


class Image(BaseLabbookModel):
    """Image configuration"""
    
    type: ImageType = Field(..., alias="type", description="Image type")
    repo: str = Field(..., alias="repo", description="Repository")
    tag: str = Field(..., alias="tag", description="Tag")
    url: Optional[str] = Field(None, alias="url", description="URL")
    username: Optional[str] = Field(None, alias="username", description="Username")
    password: Optional[str] = Field(None, alias="password", description="Password")
    archive_path: Optional[str] = Field(None, alias="archive_path", description="Archive path")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "registry",
                "repo": "ubuntu",
                "tag": "20.04",
                "url": "docker.io"
            }
        }


class NetworkConfig(BaseLabbookModel):
    """Complete network configuration"""
    
    images: Optional[List[Image]] = Field(None, alias="images", description="Image list")
    nodes: Optional[List[Node]] = Field(None, alias="nodes", description="Node list")
    switches: Optional[List[L2Switch]] = Field(None, alias="switches", description="Switch list")
    links: Optional[List[Link]] = Field(None, alias="links", description="Link list")

    class Config:
        json_schema_extra = {
            "example": {
                "images": [
                    {
                        "type": "registry",
                        "repo": "ubuntu",
                        "tag": "20.04"
                    }
                ],
                "nodes": [
                    {
                        "name": "client-1",
                        "image": "ubuntu:20.04",
                        "interfaces": [
                            {
                                "name": "eth0",
                                "mode": "direct",
                                "ip": ["192.168.1.10/24"]
                            }
                        ]
                    }
                ],
                "switches": [
                    {
                        "id": "switch-1",
                        "properties": {
                            "static_neigh": False,
                            "no_arp": False
                        }
                    }
                ],
                "links": [
                    {
                        "id": "link-1",
                        "endpoints": ["client-1:eth0", "server-1:eth0"],
                        "switch": "switch-1"
                    }
                ]
            }
        }




