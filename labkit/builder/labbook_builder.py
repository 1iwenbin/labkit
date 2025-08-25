from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml

'''
[experiment-name]/
│
├── labbook.yaml            # [必需] 清单文件，实验的元数据
│
├── network/                # [必需] 静态环境定义
│   ├── config.yaml         #  - 网络的"蓝图"文件
│   └── mounts/             #  - [可选] 存放所有待挂载内容的"源目录"
│
├── playbook.yaml           # [必需] 动态流程编排文件，实验的"剧本"
│
└── actions/                # [必需] 动作定义库
'''

from labkit.models.labbook import Labbook
from labkit.models.network import NetworkConfig, Node, L2Switch, Link, Image
from labkit.models.playbook import Playbook, TimelineItem
from labkit.models.action import Action, ActionType
from labkit.models.events import (
    NetworkEvent, NetFuncEvent, NetFuncExecOutputEvent, InterfaceCreateArgs,
    LinkCreateArgs, LinkProperties, NodeCreateArgs, NetworkEventType,
    LinkPropertiesMode, NodeExecArgs, VolFetchEvent, VolFetchEntry
)

# =========================
# 统一的实验构建器
# =========================
class LabbookBuilder:
    """
    统一的实验构建器 - 通过命名规范区分不同类型的类方法
    
    命名规范：
    - set_*: 设置基本参数
    - add_*: 添加组件
    - create_*: 创建复杂对象
    - new_*: 创建事件和参数对象
    - build_*: 构建输出
    - validate_*: 验证配置
    """

    def __init__(self, output_dir: str = ".", name: str = "experiment"):
        """
        初始化 LabbookBuilder
        
        Args:
            output_dir (str): 输出目录
            name (str): 实验名称
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 实验元数据
        self.name = name
        self.description = ""
        self.author = ""
        self.tags = []
        self.labbook: Optional[Labbook] = None
        
        # 网络组件
        self.images = []
        self.nodes = []
        self.switches = []
        self.links = []
        
        # 流程编排
        self.actions = {}
        self.timeline = []
        
        # 验证错误
        self._validation_errors = []

    # ===== 配置类方法 (set_*) =====
    def set_name(self, name: str) -> 'LabbookBuilder':
        """设置实验名称"""
        self.name = name
        return self
    
    def set_description(self, description: str) -> 'LabbookBuilder':
        """设置实验描述"""
        self.description = description
        return self
    
    def set_author(self, author: str) -> 'LabbookBuilder':
        """设置实验作者"""
        self.author = author
        return self
    
    def set_tags(self, tags: List[str]) -> 'LabbookBuilder':
        """设置实验标签"""
        self.tags = tags
        return self
    
    def set_labbook(self, labbook: Labbook) -> 'LabbookBuilder':
        """设置完整的 labbook 对象"""
        self.labbook = labbook
        return self

    # ===== 添加组件方法 (add_*) =====
    def add_image(self, repo: str, tag: str = "latest") -> 'LabbookBuilder':
        """添加容器镜像"""
        image = Image(repo=repo, tag=tag)
        self.images.append(image)
        return self
    
    def add_node(self, node: Node) -> 'LabbookBuilder':
        """添加网络节点"""
        # 检查 node 的 image 是否存在于 images 中
        node_image_str = node.get_image_str()
        if not any(f"{img.repo}:{img.tag}" == node_image_str for img in self.images):
            raise ValueError(f"Node '{node.name}' references image '{node_image_str}', but it does not exist in images.")
        
        # 添加 interfaces 的 endpoint 到 endpoint_map 中
        for interface in node.interfaces:
            endpoint = f"{node.name}:{interface.name}"
            # 检查 endpoint 是否已存在
            for existing_node in self.nodes:
                for existing_interface in existing_node.interfaces:
                    if f"{existing_node.name}:{existing_interface.name}" == endpoint:
                        raise ValueError(f"Endpoint '{endpoint}' already exists.")
        
        self.nodes.append(node)
        return self
    
    def add_switch(self, switch: L2Switch) -> 'LabbookBuilder':
        """添加交换机"""
        self.switches.append(switch)
        return self
    
    def add_link(self, link: Link) -> 'LabbookBuilder':
        """添加网络链路"""
        # 判断 link 的 endpoint 是否存在
        for endpoint in link.endpoints:
            endpoint_exists = False
            for node in self.nodes:
                for interface in node.interfaces:
                    if f"{node.name}:{interface.name}" == endpoint:
                        endpoint_exists = True
                        break
                if endpoint_exists:
                    break
            
            if not endpoint_exists:
                raise ValueError(f"Link '{link.id}' references endpoint '{endpoint}', but it does not exist.")
        
        # 如果 link.switch 非空，则检查 switch 是否存在于 switches 中
        if link.switch:
            if not any(sw.id == link.switch for sw in self.switches):
                raise ValueError(f"Link '{link.id}' references switch '{link.switch}', but it does not exist.")
        
        self.links.append(link)
        return self
    
    def add_timeline_item(self, at: int, description: str, action: Action) -> 'LabbookBuilder':
        """添加时间线项"""
        timeline_item = TimelineItem(at=at, description=description, action=action)
        self.timeline.append(timeline_item)
        return self

    # ===== 创建事件和参数方法 (new_*) =====
    def new_link_create_args(
        self,
        id: str,
        endpoints: List[str],
        switch: Optional[str] = None,
        static_neigh: Optional[bool] = False,
        no_arp: Optional[bool] = False
    ) -> LinkCreateArgs:
        """创建链路创建参数"""
        return LinkCreateArgs.template(
            id=id, endpoints=endpoints, switch=switch, 
            static_neigh=static_neigh, no_arp=no_arp
        )
    
    def new_link_properties(
        self,
        mode: LinkPropertiesMode,
        bandwidth: Optional[str] = None,
        loss: Optional[str] = None,
        delay: Optional[str] = None
    ) -> LinkProperties:
        """创建链路属性"""
        return LinkProperties.template(
            mode=mode, bandwidth=bandwidth, loss=loss, delay=delay
        )
    
    def new_network_link_create_event(
        self,
        id: str,
        link_create_args: LinkCreateArgs,
        link_properties: LinkProperties
    ) -> NetworkEvent:
        """创建网络链路创建事件"""
        return NetworkEvent.template(
            type_=NetworkEventType.NETWORK_LINK_CREATE,
            link_create_args=link_create_args,
            link_properties=link_properties
        )
    
    def new_network_link_attr_set_event(
        self,
        id: str,
        link_properties: LinkProperties
    ) -> NetworkEvent:
        """创建网络链路属性设置事件"""
        return NetworkEvent.template(
            link_id=id,
            type_=NetworkEventType.NETWORK_LINK_ATTR_SET,
            link_properties=link_properties
        )
    
    def new_network_link_destroy_event(self, id: str) -> NetworkEvent:
        """创建网络链路销毁事件"""
        return NetworkEvent.template(
            type_=NetworkEventType.NETWORK_LINK_DESTROY,
            link_id=id
        )
    
    def new_node_exec_args(
        self,
        key: Optional[str] = None,
        shellcodes: Optional[List[str]] = None,
        daemon: Optional[bool] = False,
        output: Optional[str] = None,
        timeout: Optional[int] = 0
    ) -> NodeExecArgs:
        """创建节点执行参数"""
        return NodeExecArgs.template(
            key=key, shellcodes=shellcodes, daemon=daemon, 
            output=output, timeout=timeout
        )
    
    def new_netfunc_event(
        self,
        node_name: str,
        exec_args: NodeExecArgs
    ) -> NetFuncEvent:
        """创建网络函数事件"""
        return NetFuncEvent.template(
            node_name=node_name, exec_args=exec_args
        )
    
    def new_netfunc_exec_output_event(
        self,
        node_name: str,
        exec_args: NodeExecArgs
    ) -> NetFuncExecOutputEvent:
        """创建网络函数执行输出事件"""
        return NetFuncExecOutputEvent.template(
            node_name=node_name, exec_args=exec_args
        )
    
    def new_vol_fetch_event(
        self,
        saved_name: str,
        volume_fetch_entries: List[VolFetchEntry]
    ) -> VolFetchEvent:
        """创建卷获取事件"""
        return VolFetchEvent.template(
            saved_name=saved_name, volume_fetch_entries=volume_fetch_entries
        )
    
    def new_vol_fetch_entry(
        self,
        node_name: str,
        volumes: List[str]
    ) -> VolFetchEntry:
        """创建卷获取条目"""
        return VolFetchEntry.template(node_name=node_name, volumes=volumes)

    # ===== 创建动作方法 (create_*) =====
    def create_network_events_action(self, events: List[NetworkEvent], name: str) -> Action:
        """创建网络事件动作"""
        # 1. 创建 actions 目录
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 转为 dict
        events_dicts = [e.model_dump(by_alias=True, exclude_none=True) for e in events]
        # 3. 转为 YAML
        yaml_str = yaml.dump(events_dicts, allow_unicode=True, sort_keys=False)
        # 4. 写入文件
        event_file = actions_dir / f"{name}.yaml"
        with open(event_file, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        # 5. 添加动作
        source = f"actions/{name}.yaml"
        action = self.new_action(ActionType.NETWORK_EVENTS, source)
        return action
    
    def create_netfunc_events_action(self, events: List[NetFuncEvent], name: str) -> Action:
        """创建网络函数事件动作"""
        # 1. 创建 actions 目录
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 转为 dict
        events_dicts = [e.model_dump(by_alias=True, exclude_none=True) for e in events]
        # 3. 转为 YAML
        yaml_str = yaml.dump(events_dicts, allow_unicode=True, sort_keys=False)
        # 4. 写入文件
        event_file = actions_dir / f"{name}.yaml"
        with open(event_file, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        # 5. 添加动作
        source = f"actions/{name}.yaml"
        action = self.new_action(ActionType.NETFUNC_EVENTS, source)
        return action
    
    def create_netfunc_exec_output_event_action(self, event: NetFuncExecOutputEvent, name: str) -> Action:
        """创建网络函数执行输出事件动作"""
        # 1. 创建 actions 目录
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 转为 dict
        event_dict = event.model_dump(by_alias=True, exclude_none=True)
        # 3. 转为 YAML
        yaml_str = yaml.dump(event_dict, allow_unicode=True, sort_keys=False)
        # 4. 写入文件
        event_file = actions_dir / f"{name}.yaml"
        with open(event_file, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        # 5. 添加动作
        source = f"actions/{name}.yaml"
        action = self.new_action(ActionType.NETFUNC_EXEC_OUTPUT, source)
        return action
    
    def create_vol_fetch_event_action(self, event: VolFetchEvent, name: str) -> Action:
        """创建卷获取事件动作"""
        # 1. 创建 actions 目录
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 转为 dict
        event_dict = event.model_dump(by_alias=True, exclude_none=True)
        # 3. 转为 YAML
        yaml_str = yaml.dump(event_dict, allow_unicode=True, sort_keys=False)
        # 4. 写入文件
        event_file = actions_dir / f"{name}.yaml"
        with open(event_file, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        # 5. 添加动作
        source = f"actions/{name}.yaml"
        action = self.new_action(ActionType.VOL_FETCH, source)
        return action
    
    def new_action(
        self,
        type_: ActionType,
        source: str,
        with_: Optional[Dict[str, Any]] = None
    ) -> Action:
        """创建新动作"""
        # 判断 source 是否是一个合法的相对路径
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

    # ===== 验证方法 (validate_*) =====
    def validate_network(self) -> bool:
        """验证网络配置"""
        self._validation_errors = []
        
        # 验证节点镜像引用
        image_map = {f"{img.repo}:{img.tag}": img for img in self.images}
        for node in self.nodes:
            if node.get_image_str() not in image_map:
                self._validation_errors.append(f"Node '{node.name}' references non-existent image '{node.get_image_str()}'")
        
        # 验证链路端点引用
        endpoint_map = {}
        for node in self.nodes:
            for interface in node.interfaces:
                endpoint = f"{node.name}:{interface.name}"
                endpoint_map[endpoint] = True
        
        for link in self.links:
            for endpoint in link.endpoints:
                if endpoint not in endpoint_map:
                    self._validation_errors.append(f"Link '{link.id}' references non-existent endpoint '{endpoint}'")
        
        # 验证链路交换机引用
        switch_map = {sw.id: sw for sw in self.switches}
        for link in self.links:
            if link.switch and link.switch not in switch_map:
                self._validation_errors.append(f"Link '{link.id}' references non-existent switch '{link.switch}'")
        
        return len(self._validation_errors) == 0
    
    def validate_playbook(self) -> bool:
        """验证流程编排"""
        # 验证时间线动作引用
        for item in self.timeline:
            if item.action not in self.actions:
                self._validation_errors.append(f"Timeline item references non-existent action '{item.action}'")
        
        return len(self._validation_errors) == 0
    
    def validate_all(self) -> bool:
        """验证所有配置"""
        return self.validate_network() and self.validate_playbook()
    
    def get_validation_errors(self) -> List[str]:
        """获取验证错误信息"""
        return self._validation_errors.copy()

    # ===== 构建方法 (build_*) =====
    def build_network_config(self) -> NetworkConfig:
        """构建网络配置"""
        return NetworkConfig(
            nodes=self.nodes,
            switches=self.switches,
            links=self.links,
            images=self.images
        )
    
    def build_playbook(self) -> Playbook:
        """构建流程编排"""
        return Playbook(timeline=self.timeline)
    
    def build_labbook(self) -> Labbook:
        """构建实验元数据"""
        if self.labbook is not None:
            return self.labbook
        
        return Labbook.template(
            name=self.name,
            description=self.description,
            author=self.author,
            tags=self.tags
        )
    
    def build(self) -> None:
        """构建完整的实验环境"""
        # 验证配置
        if not self.validate_all():
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(self.get_validation_errors()))
        
        # 构建各个部分
        network_config = self.build_network_config()
        playbook = self.build_playbook()
        labbook = self.build_labbook()
        
        # 生成输出文件
        self._write_output(network_config, playbook, labbook)
    
    def _write_output(self, network_config: NetworkConfig, playbook: Playbook, labbook: Labbook):
        """写入输出文件"""
        # 1. labbook.yaml
        labbook_yaml = self.output_dir / "labbook.yaml"
        labbook_dict = labbook.model_dump(by_alias=True, exclude_none=True)
        yaml_str = yaml.dump(labbook_dict, sort_keys=False, allow_unicode=True)
        with open(labbook_yaml, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        
        # 2. network/config.yaml
        network_dir = self.output_dir / "network"
        network_dir.mkdir(exist_ok=True)
        network_config_yaml = network_dir / "config.yaml"
        network_config_dict = network_config.model_dump(by_alias=True, exclude_none=True)
        with open(network_config_yaml, "w", encoding="utf-8") as f:
            f.write(yaml.dump(network_config_dict, sort_keys=False, allow_unicode=True))
        
        # 3. 创建 network/mounts/ 目录
        mounts_dir = network_dir / "mounts"
        mounts_dir.mkdir(exist_ok=True, parents=True)
        
        # 4. 为节点的 volumes 创建挂载点目录
        for node in self.nodes:
            if node.volumes:
                for volume in node.volumes:
                    host_path_dir = mounts_dir / volume.host_path
                    host_path_dir.mkdir(exist_ok=True, parents=True)
        
        # 5. playbook.yaml
        playbook_yaml = self.output_dir / "playbook.yaml"
        playbook_dict = playbook.model_dump(by_alias=True, exclude_none=True)
        yaml_str = yaml.dump(playbook_dict, sort_keys=False, allow_unicode=True)
        with open(playbook_yaml, "w", encoding="utf-8") as f:
            f.write(yaml_str)
        
        # 6. 创建 actions/ 目录
        actions_dir = self.output_dir / "actions"
        actions_dir.mkdir(exist_ok=True, parents=True)

# =========================
# 向后兼容的别名
# =========================
Builder = LabbookBuilder
