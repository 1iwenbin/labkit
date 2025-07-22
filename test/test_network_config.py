import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from labkit.models.network import (
    NetworkConfig, Image, ImageType, Node, Interface, InterfaceMode,
    VolumeMount, L2Switch, SwitchProperties, Link
)
from pydantic_yaml import to_yaml_str
import yaml

def to_ordered_yaml(model_instance):
    """将 Pydantic 模型转换为有序的 YAML 字符串"""
    # 获取模型数据
    data = model_instance.model_dump(by_alias=True, exclude_none=True)
    
    # 定义字段顺序
    field_order = {
        'NetworkConfig': ['images', 'nodes', 'switches', 'links'],
        'Image': ['type', 'repo', 'tag', 'url', 'username', 'password', 'archive_path'],
        'Node': ['name', 'image', 'interfaces', 'volumes', 'ext'],
        'Interface': ['name', 'mode', 'ip', 'mac', 'vlan'],
        'VolumeMount': ['host_path', 'container_path', 'mode'],
        'L2Switch': ['id', 'properties'],
        'SwitchProperties': ['static_neigh', 'no_arp'],
        'Link': ['id', 'endpoints', 'switch']
    }
    
    def order_dict(d, model_name):
        """递归排序字典字段"""
        if not isinstance(d, dict):
            return d
        
        if model_name in field_order:
            # 按预定义顺序排序
            ordered = {}
            for key in field_order[model_name]:
                if key in d:
                    ordered[key] = d[key]
            # 添加其他字段
            for key, value in d.items():
                if key not in ordered:
                    ordered[key] = value
            return ordered
        return d
    
    def recursive_order(obj, model_name):
        """递归处理嵌套对象"""
        if isinstance(obj, dict):
            ordered_obj = order_dict(obj, model_name)
            for key, value in ordered_obj.items():
                ordered_obj[key] = recursive_order(value, key)
            return ordered_obj
        elif isinstance(obj, list):
            return [recursive_order(item, model_name) for item in obj]
        else:
            return obj
    
    # 排序数据
    ordered_data = recursive_order(data, 'NetworkConfig')
    
    # 转换为 YAML
    return yaml.dump(ordered_data, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main():
    example = NetworkConfig(
        images=[
            Image(
                type=ImageType.REGISTRY,
                repo="library/ubuntu",
                tag="22.04",
                url="https://registry-1.docker.io",
                username="user",
                password="pass"
            ),
            Image(
                type=ImageType.DOCKER_ARCHIVE,
                repo="custom/image",
                tag="latest",
                archive_path="/images/custom-image.tar"
            )
        ],
        nodes=[
            Node(
                name="node1",
                image="library/ubuntu:22.04",
                interfaces=[
                    Interface(
                        name="eth0",
                        mode=InterfaceMode.DIRECT,
                        ip=["10.0.0.2/24"],
                        mac="00:11:22:33:44:55",
                        vlan=0
                    ),
                    Interface(
                        name="eth1",
                        mode=InterfaceMode.SWITCHED,
                        ip=["192.168.1.2/24"],
                        mac="00:11:22:33:44:66",
                        vlan=100
                    )
                ],
                volumes=[
                    VolumeMount(
                        host_path="/data",
                        container_path="/mnt/data",
                        mode="rw"
                    )
                ],
                ext={"role": "compute"}
            ),
            Node(
                name="node2",
                image="library/ubuntu:22.04",
                interfaces=[
                    Interface(
                        name="eth0",
                        mode=InterfaceMode.DIRECT,
                        ip=["10.0.0.3/24"],
                        mac="00:11:22:33:44:77",
                        vlan=0
                    )
                ],
                volumes=[],
                ext=None
            )
        ],
        switches=[
            L2Switch(
                id="sw1",
                properties=SwitchProperties(
                    static_neigh=True,
                    no_arp=False
                )
            )
        ],
        links=[
            Link(
                id="link1",
                endpoints=["node1:eth0", "node2:eth0"],
                switch=None
            ),
            Link(
                id="link2",
                endpoints=["node1:eth1", "node2:eth0"],
                switch="sw1"
            )
        ]
    )
    
    # 使用自定义的有序 YAML 序列化
    yaml_content = to_ordered_yaml(example)
    
    # 保存为 YAML 文件
    with open("network_config_ordered.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    print("✅ NetworkConfig 已保存为 network_config_ordered.yaml (字段已排序)")
    print("📄 文件内容预览:")
    print("=" * 50)
    print(yaml_content)

if __name__ == "__main__":
    main() 