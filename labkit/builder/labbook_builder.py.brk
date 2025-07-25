from pathlib import Path
from typing import Optional
import yaml

'''
[experiment-name]/
│
├── labbook.yaml            # [必需] 清单文件，实验的元数据
│
├── network/                # [必需] 静态环境定义
│   ├── config.yaml         #  - 网络的“蓝图”文件
│   └── mounts/             #  - [可选] 存放所有待挂载内容的“源目录”
│
├── playbook.yaml           # [必需] 动态流程编排文件，实验的“剧本”
│
└── actions/                # [必需] 动作定义库
'''

from labkit.models.labbook import Labbook
from labkit.models.network import NetworkConfig, Node, L2Switch, Link, Image
from labkit.models.playbook import Playbook, TimelineItem
from labkit.models.action import Action, ActionType
from labkit.models.events import NetworkEvent, NetFuncEvent, NetFuncExecOutputEvent, InterfaceCreateArgs, LinkCreateArgs, LinkProperties, NodeCreateArgs, NetworkEventType, LinkPropertiesMode, NodeExecArgs
from typing import List, Dict, Any  

# =========================
# 构建器总控类
# =========================
class Builder:
    """
    构建器基类，负责协调 Labbook、Network、Playbook 的构建
    """
    labbook_builder: "LabbookBuilder" = None
    network_builder: "NetworkBuilder" = None
    playbook_builder: "PlaybookBuilder" = None
    
    def __init__(self, output_dir: str = "."):
        """
        初始化 Builder，创建输出目录和各子构建器
        """
        self.output_dir = Path(output_dir)
        # 创建 output_dir 目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 创建 labbook_builder, network_builder, playbook_builder
        self.labbook_builder = LabbookBuilder(output_dir=output_dir)
        self.network_builder = NetworkBuilder(output_dir=output_dir)
        self.playbook_builder = PlaybookBuilder(output_dir=output_dir)
    
    # ===== LabbookBuilder 相关方法 =====
    def set_labbook(self, labbook: Labbook):
        """
        设置 labbook
        """
        self.labbook_builder.set_labbook(labbook)
    
    # ===== NetworkBuilder 相关方法 =====
    def add_node(self, node: Node):
        """
        添加一个节点
        """
        self.network_builder.add_node(node)
    
    def add_switch(self, switch: L2Switch):
        """
        添加一个交换机
        """
        self.network_builder.add_switch(switch)
    
    def add_link(self, link: Link):
        """
        添加一个链路
        """
        self.network_builder.add_link(link)
    
    def add_image(self, image: Image):
        """
        添加一个镜像
        """
        self.network_builder.add_image(image)
        
    # ===== PlaybookBuilder 相关方法 =====
    def add_timeline_item(self, at: int, description: str, action: Action):
        """
        添加一个时间线项
        """
        self.playbook_builder.add_timeline_item(at, description, action)
    
    def build_network_events_action(self, events: List[NetworkEvent], name: str) -> Action:
        """
        生成 network/actions/ 目录结构
        """
        action = self.playbook_builder.build_network_events_action(events, name)
        return action
    
    def build_netfunc_events_action(self, events: List[NetFuncEvent], name: str) -> Action: 
        """
        生成 network/actions/ 目录结构
        """
        action = self.playbook_builder.build_netfunc_events_action(events, name)
        return action
    
    def build_netfunc_exec_output_event_action(self, event: NetFuncExecOutputEvent, name: str) -> Action:
        """
        生成 network/actions/ 目录结构
        """
        action = self.playbook_builder.build_netfunc_exec_output_event_action(event, name)
        return action   
    
    def new_action(self, type_: ActionType, source: str, with_: Optional[Dict[str, Any]] = None) -> Action:
        """
        添加一个动作, 动作的 source 是文件名, 不包含路径, 会自动添加到 actions 目录下
        """
        return self.playbook_builder.new_action(type_, source, with_)   
    
    # ===== Event 相关方法 =====
    def new_link_create_args(self, id: str, endpoints: List[str], switch: Optional[str] = None, static_neigh: Optional[bool] = False, no_arp: Optional[bool] = False) -> LinkCreateArgs:
        """
        添加一个链路创建参数
        """
        return self.network_builder.new_link_create_args(id=id, endpoints=endpoints, switch=switch, static_neigh=static_neigh, no_arp=no_arp)
    
    def new_link_properties(self, mode: LinkPropertiesMode, bandwidth: Optional[str] = None, loss: Optional[str] = None, delay: Optional[str] = None) -> LinkProperties:
        """
        添加一个链路属性
        """
        return self.network_builder.new_link_properties(mode=mode, bandwidth=bandwidth, loss=loss, delay=delay)

    def new_network_link_create_event(self, id: str, link_create_args: LinkCreateArgs, link_properties: LinkProperties) -> NetworkEvent:
        """
        添加一个链路创建事件
        """
        return self.network_builder.new_network_link_create_event(id=id, link_create_args=link_create_args, link_properties=link_properties)
    
    def new_network_link_attr_set_event(self, id: str, link_properties: LinkProperties) -> NetworkEvent:
        """
        添加一个链路属性设置事件
        """
        return self.network_builder.new_network_link_attr_set_event(id=id, link_properties=link_properties)
    
    def new_network_link_destroy_event(self, id: str) -> NetworkEvent:
        """
        添加一个链路销毁事件
        """
        return self.network_builder.new_network_link_destroy_event(id=id)
    
    # ===== NetFuncEvent 相关方法 =====
    def new_node_exec_args(self, key: Optional[str] = None, shellcodes: Optional[List[str]] = None, daemon: Optional[bool] = False, output: Optional[str] = None, timeout: Optional[int] = 0) -> NodeExecArgs:
        """
        添加一个节点执行参数
        """
        return self.network_builder.new_node_exec_args(key=key, shellcodes=shellcodes, daemon=daemon, output=output, timeout=timeout)
    
    def new_netfunc_event(self, node_name: str, exec_args: NodeExecArgs) -> NetFuncEvent:
        """
        添加一个网络函数事件
        """
        return self.network_builder.new_netfunc_event(node_name=node_name, exec_args=exec_args)
    
    def new_netfunc_exec_output_event(self, node_name: str, exec_args: NodeExecArgs) -> NetFuncExecOutputEvent:
        """
        添加一个网络函数执行输出事件
        """
        return self.network_builder.new_netfunc_exec_output_event(node_name=node_name, exec_args=exec_args)
    
    # ===== 构建总入口 =====
    def build(self):
        """
        构建 labbook 目录结构和基本文件
        """
        self.labbook_builder.build()
        self.network_builder.build()
        self.playbook_builder.build()
        

# =========================
# Labbook 构建器
# =========================
class LabbookBuilder:
    # 模板数据
    # labbook.yaml
    labbook: Labbook = None
    
    """
    LabbookBuilder 用于一键生成 labbook 目录结构和基本文件。
    """
    def __init__(self, output_dir: str = "."):
        """
        初始化 LabbookBuilder
        """
        self.output_dir = Path(output_dir)

    # ===== Labbook 相关方法 =====
    def set_labbook(self, labbook: Labbook):
        """
        设置 labbook
        """
        self.labbook = labbook
    
    # ===== Build 相关方法 =====
    def _build_labbook(self, labbook_yaml: Path):
        """
        生成 labbook.yaml
        """
        if self.labbook is None:
            self.labbook = Labbook.template(name="example-experiment", description="Describe your experiment here.", author="Your Name", tags=["example", "template"])
        
        # 1. 转为 dict
        labbook_dict = self.labbook.model_dump(by_alias=True, exclude_none=True)
        # 2. 序列化为 YAML
        yaml_str = yaml.dump(labbook_dict, sort_keys=False, allow_unicode=True)
        # 3. 写入文件
        with open(labbook_yaml, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        
    def build(self):
        """
        生成 labbook 目录结构和基本文件。
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 1. labbook.yaml
        labbook_yaml = self.output_dir / "labbook.yaml"
        self._build_labbook(labbook_yaml)

# =========================
# Network 构建器
# =========================
class NetworkBuilder:
    """
    网络配置构建器，负责 network/ 目录及其内容的生成
    """
    node_map: Dict[str, Node] = {}
    switch_map: Dict[str, L2Switch] = {}
    link_map: Dict[str, Link] = {}
    image_repo_map: Dict[str, Image] = {}
    endpoint_map: Dict[str, bool] = {}
    mounts_host_path_list: List[str] = []
    
    def __init__(self, output_dir: str = "."):
        """
        初始化 NetworkBuilder
        """
        self.output_dir = Path(output_dir) / "network"
        self.node_map = {}
        self.switch_map = {}
        self.link_map = {}
        self.image_repo_map = {}
        self.endpoint_map = {}
        self.mounts_host_path_list = []
        
    # ===== 节点、交换机、链路、镜像相关方法 =====
    def add_node(self, node: Node):
        """
        添加一个节点
        """
        # 检查 node 的 image 是否存在于 image_list 中（repo:tag 匹配）
        node_image_str = node.get_image_str()
        if node_image_str not in self.image_repo_map:
            raise ValueError(f"Node '{node.name}' references image '{node_image_str}', but it does not exist in image_list.")
        # 添加 interfaces 的 endpoint 到 endpoint_map 中
        for interface in node.interfaces:
            endpoint = f"{node.name}:{interface.name}"
            if endpoint in self.endpoint_map:
                raise ValueError(f"Endpoint '{endpoint}' already exists.")
            self.endpoint_map[endpoint] = True
        # 添加 volumes 的 host_path 到 mounts_host_path_map 中
        if node.volumes:
            for volume in node.volumes:
                self.mounts_host_path_list.append(volume.host_path)
        # 添加 node 到 node_map 中
        self.node_map[node.name] = node
    
    def add_switch(self, switch: L2Switch):
        """
        添加一个交换机
        """
        self.switch_map[switch.id] = switch
        
    def add_link(self, link: Link):
        """
        添加一个链路
        """
        # 判断 link 的 endpoint 是否存在
        for endpoint in link.endpoints:
            if endpoint not in self.endpoint_map:
                raise ValueError(f"Link '{link.id}' references endpoint '{endpoint}', but it does not exist in endpoint_map.")
        # 如果 link.switch 非空，则检查 switch 是否存在于 switch_map 中
        if link.switch:
            if link.switch not in self.switch_map:
                raise ValueError(f"Link '{link.id}' references switch '{link.switch}', but it does not exist in switch_map.")
        # 添加 link 到 link_map 中
        self.link_map[link.id] = link
        
    def add_image(self, image: Image):
        """
        添加一个镜像
        """
        # 检查 image 是否已经存在
        if f"{image.repo}:{image.tag}" in self.image_repo_map:
            raise ValueError(f"Image '{image.repo}:{image.tag}' already exists.")
        # 添加 image 到 image_repo_map 中
        self.image_repo_map[f"{image.repo}:{image.tag}"] = image
    
    # ===== Event 相关方法 =====
    def new_link_create_args(self, id: str, endpoints: List[str], switch: Optional[str] = None, static_neigh: Optional[bool] = False, no_arp: Optional[bool] = False) -> LinkCreateArgs:
        """
        添加一个链路创建参数
        """
        return LinkCreateArgs.template(id=id, endpoints=endpoints, switch=switch, static_neigh=static_neigh, no_arp=no_arp)
    
    def new_link_properties(self, mode: LinkPropertiesMode, bandwidth: Optional[str] = None, loss: Optional[str] = None, delay: Optional[str] = None) -> LinkProperties:
        """
        添加一个链路属性
        """
        return LinkProperties.template(mode=mode, bandwidth=bandwidth, loss=loss, delay=delay)
    
    def new_network_link_create_event(self, id: str, link_create_args: LinkCreateArgs, link_properties: LinkProperties) -> NetworkEvent:
        """
        添加一个链路创建事件
        """
        return NetworkEvent.template(type_=NetworkEventType.NETWORK_LINK_CREATE, link_create_args=link_create_args, link_properties=link_properties)
    
    def new_network_link_attr_set_event(self, id: str, link_properties: LinkProperties) -> NetworkEvent:
        """
        添加一个链路属性设置事件
        """
        return NetworkEvent.template(link_id=id, type_=NetworkEventType.NETWORK_LINK_ATTR_SET, link_properties=link_properties)
    
    def new_network_link_destroy_event(self, id: str) -> NetworkEvent:
        """
        添加一个链路销毁事件
        """
        return NetworkEvent.template(type_=NetworkEventType.NETWORK_LINK_DESTROY, link_id=id)
    
    # ===== NetFuncEvent 相关方法 =====
    def new_node_exec_args(self, key: Optional[str] = None, shellcodes: Optional[List[str]] = None, daemon: Optional[bool] = False, output: Optional[str] = None, timeout: Optional[int] = 0) -> NodeExecArgs:
        """
        添加一个节点执行参数
        """
        return NodeExecArgs.template(key=key, shellcodes=shellcodes, daemon=daemon, output=output, timeout=timeout)
    
    def new_netfunc_event(self, node_name: str, exec_args: NodeExecArgs) -> NetFuncEvent:
        """
        添加一个网络函数事件
        """
        return NetFuncEvent.template(node_name=node_name, exec_args=exec_args)
    
    def new_netfunc_exec_output_event(self, node_name: str, exec_args: NodeExecArgs) -> NetFuncExecOutputEvent:
        """
        添加一个网络函数执行输出事件
        """
        return NetFuncExecOutputEvent.template(node_name=node_name, exec_args=exec_args)
    
    # ===== Build 相关方法 =====
    def build(self):
        """
        生成 network/ 目录结构
        """
        # 创建 network/ 目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 1. network/config.yaml
        node_list = list(self.node_map.values())
        switch_list = list(self.switch_map.values())
        link_list = list(self.link_map.values())
        image_list = list(self.image_repo_map.values())
        mounts_host_path_list = self.mounts_host_path_list
        network_config = NetworkConfig(nodes=node_list, switches=switch_list, links=link_list, images=image_list)
        network_config_yaml = self.output_dir / "config.yaml"
        # 2. 转为 dict
        network_config_dict = network_config.model_dump(by_alias=True, exclude_none=True)
        # 3. 写入文件
        with open(network_config_yaml, "w", encoding="utf-8") as f:
            f.write(yaml.dump(network_config_dict, sort_keys=False, allow_unicode=True))
        # 4. 创建 network/mounts/ 目录
        mounts_dir = self.output_dir / "mounts"
        mounts_dir.mkdir(exist_ok=True, parents=True)
        # 5. 创建 network/mounts/ 目录
        for host_path in mounts_host_path_list:
            host_path_dir = mounts_dir / host_path
            host_path_dir.mkdir(exist_ok=True, parents=True)
            
# =========================
# Playbook 构建器
# =========================
class PlaybookBuilder:
    """
    流程编排构建器，负责 actions/ 目录和 playbook.yaml 的生成
    """
    timeline: List[TimelineItem] = []
    actions: Dict[str, Action] = {}
    events: Dict[str, NetworkEvent] = {}
    
    def __init__(self, output_dir: str = "."):
        """
        初始化 PlaybookBuilder
        """
        self.output_dir = Path(output_dir)
        self._build_actions()
    
    def _build_actions(self):
        """
        生成 actions/ 目录结构
        """
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(exist_ok=True, parents=True)
    
    # ===== Playbook 相关方法 =====
    def add_timeline_item(self, at: int, description: str, action: Action):
        """
        添加一个时间线项
        """
        timeline_item = TimelineItem.template(at, description, action)
        self.timeline.append(timeline_item)

    # ===== Event 相关方法 =====
    def new_event_source_path(self, name: str) -> str:
        """
        添加一个事件, 事件的 source 是文件名, 不包含路径, 会自动添加到 actions 目录下, 返回相对文件路径, 不包含 self.output_dir
        """
        event_file = self.output_dir / "actions" / f"{name}.yaml"
        return str(event_file.relative_to(self.output_dir)) # 返回相对文件路径, 不包含 self.output_dir

    def build_network_events_action(self, events: List[NetworkEvent], name: str) -> Action:
        """
        生成 network/actions/ 目录结构
        """
        # 1. 创建 actions 目录
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 转为 dict
        events_dicts = [e.model_dump(by_alias=True, exclude_none=True) for e in events]
        # 3. 转为 YAML
        yaml_str = yaml.dump(events_dicts, allow_unicode=True, sort_keys=False)
        # 4. 写入文件
        event_file = self.output_dir / "actions" / f"{name}.yaml"
        with open(event_file, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        # 5. 添加动作
        source = self.new_event_source_path(name)
        action = self.new_action(ActionType.NETWORK_EVENTS, source)
        return action
        
    def build_netfunc_events_action(self, events: List[NetFuncEvent], name: str) -> Action:
        """
        生成 network/actions/ 目录结构
        """
        # 1. 创建 actions 目录
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 转为 dict
        events_dicts = [e.model_dump(by_alias=True, exclude_none=True) for e in events]
        # 3. 转为 YAML
        yaml_str = yaml.dump(events_dicts, allow_unicode=True, sort_keys=False)
        # 4. 写入文件
        event_file = self.output_dir / "actions" /  f"{name}.yaml"
        with open(event_file, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        # 5. 添加动作
        source = self.new_event_source_path(name)
        action = self.new_action(ActionType.NETFUNC_EVENTS, source)
        return action

    def build_netfunc_exec_output_event_action(self, event: NetFuncExecOutputEvent, name: str) -> Action:
        """
        生成 network/events/ 目录结构, 并添加到 actions 目录下
        """
        # 1. 创建 actions 目录
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 转为 dict
        event_dict = event.model_dump(by_alias=True, exclude_none=True)
        # 3. 转为 YAML
        yaml_str = yaml.dump(event_dict, allow_unicode=True, sort_keys=False)
        # 4. 写入文件
        event_file = self.output_dir / "actions" / f"{name}.yaml"
        with open(event_file, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        # 5. 添加动作
        source = self.new_event_source_path(name)
        action = self.new_action(ActionType.NETFUNC_EXEC_OUTPUT, source)
        return action
    
    # ===== Action 相关方法 =====
    def new_action(self, type_: ActionType, source: str, with_: Optional[Dict[str, Any]] = None) -> Action:
        """
        添加一个动作, 动作的 source 是文件名, 不包含路径, 会自动添加到 actions 目录下
        """
        # 判断 source 是否是一个合法的相对路径，然后创建这个 source
        source_path = Path(source)
        if source_path.is_absolute() or ".." in source_path.parts or source_path.parts[0] in ("", "/"):
            raise ValueError(f"source '{source}' 必须是合法的相对路径，且不能包含上级目录引用")
        # 创建文件（如果不存在则创建空文件，包含父目录）
        full_path = self.output_dir / source_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.exists():
            full_path.touch()
        action = Action.template(type_, source, with_)
        self.actions[source] = action
        return action
    
    # ===== Build 相关方法 =====
    def build(self):
        """
        生成 playbook.yaml
        """
        playbook = Playbook.template(timeline=self.timeline)
        playbook_yaml = self.output_dir / "playbook.yaml"
        playbook_dict = playbook.model_dump(by_alias=True, exclude_none=True)
        yaml_str = yaml.dump(playbook_dict, sort_keys=False, allow_unicode=True)
        
        with open(playbook_yaml, "w", encoding="utf-8") as f:
            f.write(yaml_str)