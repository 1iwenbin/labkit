"""
Network topology models for Labbook specification (aligned with Go version)
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import Field, ConfigDict
from .base import BaseLabbookModel

class InterfaceMode(str, Enum):
    DIRECT = "direct"
    SWITCHED = "switched"
    GATEWAY = "gateway"
    HOST = "host"

class VolumeMount(BaseLabbookModel):
    host_path: str = Field(..., alias="host_path", description="Host path")
    container_path: str = Field(..., alias="container_path", description="Container path")
    mode: str = Field(..., alias="mode", description="Mount mode (rw, ro, etc.)")

class Interface(BaseLabbookModel):
    name: str = Field(..., alias="name", description="Interface name")
    mode: InterfaceMode = Field(..., alias="mode", description="Interface working mode")
    ip_list: Optional[List[str]] = Field(None, alias="ip", description="IP address list")
    mac: Optional[str] = Field(None, alias="mac", description="MAC address")
    vlan: Optional[int] = Field(None, alias="vlan", description="VLAN ID, non-zero means external interface")

class Node(BaseLabbookModel):
    name: str = Field(..., alias="name", description="Node name")
    image: str = Field(..., alias="image", description="Container image")
    interfaces: List[Interface] = Field(..., alias="interfaces", description="Network interfaces")
    volumes: Optional[List[VolumeMount]] = Field(None, alias="volumes", description="Volume mounts")
    ext: Optional[Dict[str, Any]] = Field(None, alias="ext", description="Extension config")

class SwitchProperties(BaseLabbookModel):
    static_neigh: Optional[bool] = Field(False, alias="static_neigh", description="Use static neighbor table")
    no_arp: Optional[bool] = Field(False, alias="no_arp", description="Disable ARP")

class L2Switch(BaseLabbookModel):
    id: str = Field(..., alias="id", description="Switch ID")
    properties: Optional[SwitchProperties] = Field(None, alias="properties", description="Switch properties")

class Link(BaseLabbookModel):
    id: str = Field(..., alias="id", description="Link ID")
    endpoints: List[str] = Field(..., alias="endpoints", description="Endpoint list (format: node:interface)")
    switch: Optional[str] = Field(None, alias="switch", description="Switch ID")

class ImageType(str, Enum):
    REGISTRY = "registry"
    DOCKER_ARCHIVE = "docker-archive"

class Image(BaseLabbookModel):
    type: ImageType = Field(..., alias="type", description="Image type")
    repo: str = Field(..., alias="repo", description="Repository")
    tag: str = Field(..., alias="tag", description="Tag")
    url: Optional[str] = Field(None, alias="url", description="URL")
    username: Optional[str] = Field(None, alias="username", description="Username")
    password: Optional[str] = Field(None, alias="password", description="Password")
    archive_path: Optional[str] = Field(None, alias="archive_path", description="Archive path")

class NetworkConfig(BaseLabbookModel):
    model_config = ConfigDict(
        json_schema_extra={
            "properties": {
                "images": {},
                "nodes": {},
                "switches": {},
                "links": {}
            },
            "required": ["images", "nodes", "switches", "links"]
        }
    )
    
    images: Optional[List[Image]] = Field(None, alias="images", description="Image list")
    nodes: Optional[List[Node]] = Field(None, alias="nodes", description="Node list")
    switches: Optional[List[L2Switch]] = Field(None, alias="switches", description="Switch list")
    links: Optional[List[Link]] = Field(None, alias="links", description="Link list")
