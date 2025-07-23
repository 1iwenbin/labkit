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
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "host_path": "/tmp/data",
                "container_path": "/data",
                "mode": "rw"
            }
        }
    
    @classmethod
    def template(cls, host_path: str, container_path: str, mode: str) -> "VolumeMount":
        """
        Generate a template VolumeMount data structure with example fields.
        """
        return cls(host_path=host_path, container_path=container_path, mode=mode)


class Interface(BaseLabbookModel):
    """Network interface configuration"""
    
    name: str = Field(..., alias="name", description="Interface name")
    mode: InterfaceMode = Field(..., alias="mode", description="Interface working mode")
    ip_list: Optional[List[str]] = Field(None, alias="ip", description="IP address list")
    mac: Optional[str] = Field(None, alias="mac", description="MAC address")
    vlan: Optional[int] = Field(None, alias="vlan", description="VLAN ID, non-zero means external interface")

        
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "eth0",
                "mode": "direct",
                "ip": ["192.168.1.10/24"],
                "mac": "00:11:22:33:44:55",
                "vlan": 0
            }
        }
    
    @classmethod
    def template(cls, name: str, mode: InterfaceMode, ip_list: Optional[List[str]] = None, mac: Optional[str] = None, vlan: Optional[int] = None) -> "Interface":
        """
        Generate a template Interface data structure with example fields.
        """
        return cls(name=name, mode=mode, ip_list=ip_list, mac=mac, vlan=vlan)


class Node(BaseLabbookModel):
    """Network node configuration"""
    
    name: str = Field(..., alias="name", description="Node name")
    image: str = Field(..., alias="image", description="Container image")
    interfaces: List[Interface] = Field(..., alias="interfaces", description="Network interfaces")
    volumes: Optional[List[VolumeMount]] = Field(None, alias="volumes", description="Volume mounts")
    ext: Optional[Dict[str, Any]] = Field(None, alias="ext", description="Extension config")

    class Config:
        populate_by_name = True
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
    
    def get_image_str(self) -> str:
        """
        获取 node 的 image 字符串
        """
        return f"{self.image}"
    
    @classmethod
    def template(cls, name: str, image: str, interfaces: List[Interface], volumes: Optional[List[VolumeMount]] = None, ext: Optional[Dict[str, Any]] = None) -> "Node":
        """
        Generate a template Node data structure with example fields.
        """
        return cls(name=name, image=image, interfaces=interfaces, volumes=volumes, ext=ext)


class SwitchProperties(BaseLabbookModel):
    """Switch properties configuration"""
    
    static_neigh: Optional[bool] = Field(False, alias="static_neigh", description="Use static neighbor table (true means L2 domain can have multiple links)")
    no_arp: Optional[bool] = Field(False, alias="no_arp", description="Disable ARP (true means can use eBPF N x N network)")


    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "static_neigh": False,
                "no_arp": False
            }
        }
    
    @classmethod
    def template(cls, static_neigh: Optional[bool] = False, no_arp: Optional[bool] = False) -> "SwitchProperties":
        """
        Generate a template SwitchProperties data structure with example fields.
        """
        return cls(static_neigh=static_neigh, no_arp=no_arp)

class L2Switch(BaseLabbookModel):
    """L2 switch configuration"""
    
    id: str = Field(..., alias="id", description="Switch ID")
    properties: Optional[SwitchProperties] = Field(None, alias="properties", description="Switch properties")

        
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "switch-1",
                "properties": {
                    "static_neigh": False,
                    "no_arp": False
                }
            }
        }
    
    @classmethod
    def template(cls, id: str, properties: Optional[SwitchProperties] = None) -> "L2Switch":
        """
        Generate a template L2Switch data structure with example fields.
        """
        return cls(id=id, properties=properties)


class Link(BaseLabbookModel):
    """Network link configuration"""
    
    id: str = Field(..., alias="id", description="Link ID")
    endpoints: List[str] = Field(..., alias="endpoints", description="Endpoint list (format: node:interface)")
    switch: Optional[str] = Field(None, alias="switch", description="Switch ID, if not specified, the link is a point-to-point link")


        
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "link-1",
                "endpoints": ["client-1:eth0", "server-1:eth0"],
                "switch": "switch-1"
            }
        }
    
    @classmethod
    def template(cls, id: str, endpoints: List[str], switch: Optional[str] = None) -> "Link":
        """
        Generate a template Link data structure with example fields.
        """
        return cls(id=id, endpoints=endpoints, switch=switch)


class ImageType(str, Enum):
    """Image type enumeration"""
    
    REGISTRY = "registry"           # Docker registry image
    DOCKER_ARCHIVE = "docker-archive"  # Docker archive image


class Image(BaseLabbookModel):
    """Image configuration"""
    
    type_: ImageType = Field(..., alias="type", description="Image type")
    repo: str = Field(..., alias="repo", description="Repository")
    tag: str = Field(..., alias="tag", description="Tag")
    url: Optional[str] = Field(None, alias="url", description="URL")
    username: Optional[str] = Field(None, alias="username", description="Username")
    password: Optional[str] = Field(None, alias="password", description="Password")
    archive_path: Optional[str] = Field(None, alias="archive_path", description="Archive path")



    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "type": "registry",
                "repo": "ubuntu",
                "tag": "20.04",
                "url": "docker.io"
            }
        }
    
    @classmethod
    def template(cls, type_: ImageType, repo: str, tag: str, url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None, archive_path: Optional[str] = None) -> "Image":
        """
        Generate a template Image data structure with example fields.
        """
        return cls(type_=type_, repo=repo, tag=tag, url=url, username=username, password=password, archive_path=archive_path)


class NetworkConfig(BaseLabbookModel):
    """Complete network configuration"""
    
    images: Optional[List[Image]] = Field(None, alias="images", description="Image list")
    nodes: Optional[List[Node]] = Field(None, alias="nodes", description="Node list")
    switches: Optional[List[L2Switch]] = Field(None, alias="switches", description="Switch list")
    links: Optional[List[Link]] = Field(None, alias="links", description="Link list")

        
    class Config:
        populate_by_name = True
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
    
    @classmethod
    def template(cls, images: Optional[List[Image]] = None, nodes: Optional[List[Node]] = None, switches: Optional[List[L2Switch]] = None, links: Optional[List[Link]] = None) -> "NetworkConfig":
        """
        Generate a template NetworkConfig data structure with example fields.
        """
        return cls(
            images=images,
            nodes=nodes,
            switches=switches,
            links=links)




