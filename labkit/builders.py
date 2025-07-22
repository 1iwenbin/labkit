"""
Network Topology Builder for Labbook
提供高级的网络拓扑构建抽象
"""

from typing import List, Dict, Optional, Union
from pathlib import Path
from .models.network import (
    NetworkConfig, Image, ImageType, Node, Interface, InterfaceMode,
    VolumeMount, L2Switch, SwitchProperties, Link
)
from .models.labbook import Labbook
from .models.playbook import Playbook, Procedure, Step, Action, Condition, ConditionType
from .validators import validate_experiment


class NetworkBuilder:
    """网络拓扑构建器"""
    
    def __init__(self):
        self.images: Dict[str, Image] = {}
        self.nodes: Dict[str, Node] = {}
        self.switches: Dict[str, L2Switch] = {}
        self.links: List[Link] = []
        self._link_counter = 0
    
    def add_image(self, name: str, repo: str, tag: str = "latest", 
                  image_type: ImageType = ImageType.REGISTRY, **kwargs) -> 'NetworkBuilder':
        """添加 Docker 镜像"""
        self.images[name] = Image(
            type=image_type,
            repo=repo,
            tag=tag,
            **kwargs
        )
        return self
    
    def add_node(self, name: str, image: str, **kwargs) -> 'NodeBuilder':
        """添加网络节点"""
        if image not in self.images:
            raise ValueError(f"Image '{image}' not found. Add it first with add_image()")
        
        node = Node(
            name=name,
            image=f"{self.images[image].repo}:{self.images[image].tag}",
            interfaces=[],
            **kwargs
        )
        self.nodes[name] = node
        return NodeBuilder(self, node)
    
    def add_switch(self, name: str, static_neigh: bool = False, no_arp: bool = False) -> 'NetworkBuilder':
        """添加 L2 交换机"""
        self.switches[name] = L2Switch(
            id=name,
            properties=SwitchProperties(
                static_neigh=static_neigh,
                no_arp=no_arp
            )
        )
        return self
    
    def connect(self, node1: str, interface1: str, node2: str, interface2: str, 
                switch: Optional[str] = None) -> 'NetworkBuilder':
        """连接两个节点"""
        if node1 not in self.nodes:
            raise ValueError(f"Node '{node1}' not found")
        if node2 not in self.nodes:
            raise ValueError(f"Node '{node2}' not found")
        if switch and switch not in self.switches:
            raise ValueError(f"Switch '{switch}' not found")
        
        link_id = f"link-{self._link_counter}"
        self._link_counter += 1
        
        self.links.append(Link(
            id=link_id,
            endpoints=[f"{node1}:{interface1}", f"{node2}:{interface2}"],
            switch=switch
        ))
        return self
    
    def build(self) -> NetworkConfig:
        """构建网络配置"""
        return NetworkConfig(
            images=list(self.images.values()),
            nodes=list(self.nodes.values()),
            switches=list(self.switches.values()),
            links=self.links
        )


class NodeBuilder:
    """节点构建器"""
    
    def __init__(self, network_builder: NetworkBuilder, node: Node):
        self.network_builder = network_builder
        self.node = node
    
    def add_interface(self, name: str, mode: InterfaceMode, 
                     ip: Optional[Union[str, List[str]]] = None,
                     mac: Optional[str] = None, vlan: Optional[int] = None) -> 'NodeBuilder':
        """添加网络接口"""
        if isinstance(ip, str):
            ip = [ip]
        
        interface = Interface(
            name=name,
            mode=mode,
            ip=ip,
            mac=mac,
            vlan=vlan
        )
        self.node.interfaces.append(interface)
        return self
    
    def add_volume(self, host_path: str, container_path: str, mode: str = "rw") -> 'NodeBuilder':
        """添加卷挂载"""
        volume = VolumeMount(
            host_path=host_path,
            container_path=container_path,
            mode=mode
        )
        if self.node.volumes is None:
            self.node.volumes = []
        self.node.volumes.append(volume)
        return self
    
    def set_ext(self, **kwargs) -> 'NodeBuilder':
        """设置扩展属性"""
        self.node.ext = kwargs
        return self
    
    def done(self) -> NetworkBuilder:
        """完成节点配置"""
        return self.network_builder


class PlaybookBuilder:
    """实验剧本构建器"""
    
    def __init__(self):
        self.conditions: List[Condition] = []
        self.procedures: List[Procedure] = []
    
    def add_condition(self, id: str, type: ConditionType, command: str, target: str) -> 'PlaybookBuilder':
        """添加条件"""
        self.conditions.append(Condition(
            id=id,
            type=type,
            command=command,
            target=target
        ))
        return self
    
    def add_procedure(self, id: str, trigger_at: str) -> 'ProcedureBuilder':
        """添加实验流程"""
        procedure = Procedure(
            id=id,
            trigger_at=trigger_at,
            steps=[]
        )
        self.procedures.append(procedure)
        return ProcedureBuilder(self, procedure)
    
    def build(self) -> Playbook:
        """构建实验剧本"""
        return Playbook(
            conditions=self.conditions,
            procedures=self.procedures
        )


class ProcedureBuilder:
    """流程构建器"""
    
    def __init__(self, playbook_builder: PlaybookBuilder, procedure: Procedure):
        self.playbook_builder = playbook_builder
        self.procedure = procedure
    
    def add_step(self, description: str, action_source: Optional[str] = None, 
                 wait_for: Optional[str] = None) -> 'ProcedureBuilder':
        """添加步骤"""
        step = Step(description=description)
        
        if action_source:
            step.action = Action(source=action_source)
        elif wait_for:
            step.wait_for = wait_for
        
        self.procedure.steps.append(step)
        return self
    
    def done(self) -> PlaybookBuilder:
        """完成流程配置"""
        return self.playbook_builder


class LabbookBuilder:
    """实验构建器"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.version = "1.0"
        self.author: Optional[str] = None
        self.created_at: Optional[str] = None
        self.network_builder = NetworkBuilder()
        self.playbook_builder = PlaybookBuilder()
    
    def set_metadata(self, version: str = "1.0", author: Optional[str] = None, 
                    created_at: Optional[str] = None) -> 'LabbookBuilder':
        """设置元数据"""
        self.version = version
        self.author = author
        self.created_at = created_at
        return self
    
    def network(self) -> NetworkBuilder:
        """获取网络构建器"""
        return self.network_builder
    
    def playbook(self) -> PlaybookBuilder:
        """获取剧本构建器"""
        return self.playbook_builder
    
    def build(self) -> Labbook:
        """构建完整实验"""
        return Labbook(
            name=self.name,
            description=self.description,
            version=self.version,
            author=self.author,
            created_at=self.created_at,
            network=self.network_builder.build(),
            playbook=self.playbook_builder.build()
        )


# 便捷函数
def create_simple_network() -> NetworkBuilder:
    """创建简单网络拓扑"""
    return NetworkBuilder()


def create_labbook(name: str, description: str) -> LabbookBuilder:
    """创建实验构建器"""
    return LabbookBuilder(name, description)


def build_star_topology(center_node: str, edge_nodes: List[str], 
                       center_image: str = "ubuntu:20.04",
                       edge_image: str = "ubuntu:20.04") -> NetworkConfig:
    """构建星型拓扑"""
    builder = NetworkBuilder()
    
    # 添加镜像
    builder.add_image("ubuntu", "library/ubuntu", "20.04")
    
    # 添加交换机
    builder.add_switch("switch1")
    
    # 添加中心节点
    center = builder.add_node(center_node, "ubuntu")
    center.add_interface("eth0", InterfaceMode.SWITCHED, ["10.0.0.1/24"])
    center.done()
    
    # 添加边缘节点
    for i, node_name in enumerate(edge_nodes, 1):
        edge = builder.add_node(node_name, "ubuntu")
        edge.add_interface("eth0", InterfaceMode.SWITCHED, [f"10.0.0.{i+1}/24"])
        edge.done()
        
        # 连接到中心节点
        builder.connect(center_node, "eth0", node_name, "eth0", "switch1")
    
    return builder.build()


def build_linear_topology(nodes: List[str], 
                         base_image: str = "ubuntu:20.04") -> NetworkConfig:
    """构建线性拓扑"""
    builder = NetworkBuilder()
    
    # 添加镜像
    builder.add_image("ubuntu", "library/ubuntu", "20.04")
    
    # 添加节点
    for i, node_name in enumerate(nodes):
        node = builder.add_node(node_name, "ubuntu")
        node.add_interface("eth0", InterfaceMode.DIRECT, [f"10.0.0.{i+1}/24"])
        node.done()
        
        # 连接到下一个节点
        if i > 0:
            builder.connect(nodes[i-1], "eth0", node_name, "eth0")
    
    return builder.build()


def build_mesh_topology(nodes: List[str], 
                       base_image: str = "ubuntu:20.04") -> NetworkConfig:
    """构建网状拓扑"""
    builder = NetworkBuilder()
    
    # 添加镜像
    builder.add_image("ubuntu", "library/ubuntu", "20.04")
    
    # 添加节点
    for i, node_name in enumerate(nodes):
        node = builder.add_node(node_name, "ubuntu")
        node.add_interface("eth0", InterfaceMode.SWITCHED, [f"10.0.0.{i+1}/24"])
        node.done()
    
    # 添加交换机
    builder.add_switch("mesh_switch")
    
    # 所有节点连接到交换机
    for node_name in nodes:
        builder.connect(node_name, "eth0", nodes[0], "eth0", "mesh_switch")
    
    return builder.build()


def save_experiment(labbook: Labbook, output_dir: str = ".") -> Path:
    """保存实验到目录"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存 labbook.yaml
    labbook_file = output_path / "labbook.yaml"
    with open(labbook_file, "w") as f:
        import yaml
        yaml.dump(labbook.model_dump(by_alias=True), f, default_flow_style=False)
    
    # 保存网络配置
    network_dir = output_path / "network"
    network_dir.mkdir(exist_ok=True)
    
    topology_file = network_dir / "topology.yaml"
    with open(topology_file, "w") as f:
        yaml.dump(labbook.network.model_dump(by_alias=True), f, default_flow_style=False)
    
    # 保存剧本
    playbook_file = output_path / "playbook.yaml"
    with open(playbook_file, "w") as f:
        yaml.dump(labbook.playbook.model_dump(by_alias=True), f, default_flow_style=False)
    
    return output_path 