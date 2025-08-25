"""
SATuSGH (Satellite Network Topology Generator) 卫星网络拓扑生成器

该模块用于生成卫星网络实验环境，包含以下组件：
1. 用户节点 (user_1, user_2) - 模拟地面用户
2. 地面站节点 (gs_1, gs_2) - 连接用户和卫星网络
3. 卫星节点 (Sat0-Sat8) - 3x3网格拓扑的卫星网络
4. 背景网络 (BgNet) - 可选的扩展网络

主要功能：
- 生成网络拓扑结构
- 配置FRR路由协议
- 生成节点配置文件
- 创建实验时间线事件
"""

import os
import re
import sys
import glob
import json
import csv
from datetime import datetime
from labkit.builder.labbook_builder import Builder
from labkit.models.labbook import Labbook
from labkit.models.network import Image, ImageType, Node, Interface, InterfaceMode, Link, VolumeMount
from labkit.models.events import LinkCreateArgs
from labkit.router.frr.ospf import generate_ospf6d_config
from labkit.router.frr.zebra import ZebraInterfaceConfig, ZebraConfig
from labkit.router.frr.daemons import FrrDaemonsConfig
import yaml
from typing import Dict, Any, Optional, List, Tuple
import argparse

class BgNetConfig:
    def __init__(self, config_path: str):
        pass

class BgNet:
    
    
    def __init__(self, grid_h: int = 6, grid_w: int = 8, gs_count: int = 4, 
                 phase_shift: int = 1):
        self.sat_nodes: List[Node] = []
        self.gs_nodes: List[Node] = []
        self.s2s_links: List[Link] = []
        self.g2s_links: List[Link] = []
        self.grid_h = grid_h
        self.grid_w = grid_w
        self.gs_count = gs_count
        self.phase_shift = phase_shift
        self.sat_names = []
        self.gs_names = []
        
        self._generate_network()
        
    def _generate_network(self):
        """生成背景网络拓扑"""
        N = self.grid_h
        M = self.grid_w
        
        image_repo = "ponedo/frr-ubuntu20:tiny"
        
        # 生成背景网络卫星节点
        for i in range(N * M):
            sat_node = Node.template(
                name=f'bg_sat_{i}',
                image=image_repo,
                interfaces=[Interface.template(name=f'eth{j}', mode=InterfaceMode.DIRECT) for j in range(5)],
                volumes=[],
                ext={}
            )
            self.sat_nodes.append(sat_node)
        
        # 生成背景网络地面站节点
        for i in range(self.gs_count):
            gs_node = Node.template(
                name=f'bg_gs_{i}',
                image=image_repo,
                interfaces=[Interface.template(name='eth0', mode=InterfaceMode.DIRECT)],
                volumes=[],
                ext={}
            )
            self.gs_nodes.append(gs_node)
        
        # 生成背景网络twisted torus链路
        def bg_sat_idx(row, col):
            return row * M + col
        
        link_id = 0
        # 生成卫星节点之间的链路
        for row in range(N):
            for col in range(M):
                idx = bg_sat_idx(row, col)
                # 上邻居（垂直连接）
                up_row = (row - 1) % N
                up_col = (col + self.phase_shift) % M
                up_idx = bg_sat_idx(up_row, up_col)
                self.s2s_links.append(Link.template(
                    endpoints=[f'bg_sat_{idx}:eth0', f'bg_sat_{up_idx}:eth2'],
                    id=f'bg_link_{link_id}'
                ))
                link_id += 1
                
                # 右邻居（水平连接）
                right_row = (row + self.phase_shift) % N
                right_col = (col + 1) % M
                right_idx = bg_sat_idx(right_row, right_col)
                self.s2s_links.append(Link.template(
                    endpoints=[f'bg_sat_{idx}:eth1', f'bg_sat_{right_idx}:eth3'],
                    id=f'bg_link_{link_id}'
                ))
                link_id += 1
        
        # 连接背景网络地面站
        for i in range(self.gs_count):
            self.g2s_links.append(Link.template(
                endpoints=[f'bg_sat_{i}:eth4', f'bg_gs_{i}:eth0'],
                id=f'bg_link_{link_id}'
            ))
            link_id += 1
    
    def get_nodes(self) -> List[Node]:
        """获取所有节点"""
        return self.sat_nodes + self.gs_nodes
    
    def get_links(self) -> List[Link]:
        """获取所有链路"""
        return self.s2s_links + self.g2s_links
    

class SATuSGHConfig:
    """SATuSGH配置类（预留接口）"""
    def __init__(self, config_path: str):
        pass

class SATuSGHCoreNet:
    """
    核心网络拓扑生成器
    
    负责生成卫星网络的核心组件：
    - 用户节点：模拟地面用户
    - 地面站节点：连接用户和卫星网络
    - 卫星节点：3x3网格拓扑的卫星网络
    - 各种链路连接
    """
    
    
    def __init__(self):
        """初始化核心网络，生成所有网络组件"""
        # 网络组件存储
        self.images: List[Image] = [] # 容器镜像列表
        self.user_1: Node = None      # 用户节点1
        self.user_2: Node = None      # 用户节点2
        self.gs_nodes: List[Node] = [] # 地面站节点列表
        self.sat_nodes: List[Node] = [] # 卫星节点列表
        self.u2g_links: List[Link] = [] # 用户到地面站链路
        self.g2s_links: List[Link] = [] # 地面站到卫星链路
        self.s2s_links: List[Link] = [] # 卫星间链路
        self.configs: Dict[str, Dict[str, str]] = {} # 节点配置文件存储
        self._generate_network()
        
    @staticmethod
    def get_router_id(node_id):
        """
        根据节点ID生成路由器ID (IPv4格式)
        
        Args:
            node_id: 节点ID
            
        Returns:
            str: 路由器ID，格式为 192.0.x.y
        """
        high = (node_id + 1) // 256
        low = (node_id + 1) % 256
        return f"192.0.{high}.{low}"

    @staticmethod
    def get_lo_ipv6(node_id):
        """
        根据节点ID生成IPv6环回地址
        
        Args:
            node_id: 节点ID
            
        Returns:
            str: IPv6环回地址，格式为 fd01::0:x:y/128
        """
        high = (node_id + 1) // 256
        low = (node_id + 1) % 256
        return f"fd01::0:{high}:{low}/128"

    @staticmethod
    def get_sat_lo_ipv6(idx, grid_w):
        """
        根据卫星节点索引和网格宽度生成卫星IPv6环回地址
        
        Args:
            idx: 卫星节点索引
            grid_w: 网格宽度
            
        Returns:
            str: 卫星IPv6环回地址，格式为 fd01::col:row:1/128
        """
        row = idx // grid_w
        col = idx % grid_w
        return f"fd01::{col}:{row}:1/128"

    @staticmethod
    def get_gs_lo_ipv6(idx):
        """
        根据地面站索引生成地面站IPv6环回地址
        
        Args:
            idx: 地面站索引
            
        Returns:
            str: 地面站IPv6环回地址，格式为 fd02::idx:1/128
        """
        return f"fd02::{idx}:1/128"
    
    @staticmethod
    def generate_bfd_sh(interfaces):
        """
        生成BFD (Bidirectional Forwarding Detection) 配置脚本
        
        Args:
            interfaces: 接口列表
            
        Returns:
            str: BFD配置脚本内容
        """
        lines = [
            "vtysh <<EOF",
            "configure terminal",
            "bfd",
            " profile bfdd",
            "  transmit-interval 50", # 50ms -> 50 ms
            "  receive-interval 50", # 50ms -> 50 ms
            "  detect-multiplier 3",
            " exit"
        ]
        for iface in interfaces:
            lines.append(f"interface {iface}")
            lines.append(" ipv6 ospf6 bfd")
            lines.append(" ipv6 ospf6 bfd profile bfdd")
            lines.append("exit")
        lines.append("EOF")
        return "\n".join(lines)

    @classmethod
    def generate_ospf6d_node_configs(cls, node_type: str, node_id: int, sat_grid_N: int, node: Node):
        """
        生成节点的FRR (Free Range Routing) 配置文件
        
        Args:
            node_type: 节点类型 ('sat', 'gs', 'user')
            node_id: 节点ID
            sat_grid_N: 卫星网格宽度
            node: 节点对象
            
        Returns:
            Dict: 包含各种配置文件的字典
        """
        configs = {}
        name = node.name
        node_id = node_id
        router_id = cls.get_router_id(node_id)
        interfaces = []
        
        # 根据节点类型生成环回地址和接口列表
        if node_type == 'sat':
            lo_ipv6 = cls.get_sat_lo_ipv6(node_id, sat_grid_N)
            interfaces = [iface.name for iface in node.interfaces]
        elif node_type == 'gs':
            lo_ipv6 = cls.get_gs_lo_ipv6(node_id)
            interfaces = ["eth0"] # 地面站节点只有 eth0
        else:
            lo_ipv6 = cls.get_lo_ipv6(node_id)
            interfaces = [iface.name for iface in node.interfaces]
            
        # 生成OSPF6配置
        ospf6d_conf = generate_ospf6d_config(
                interfaces=interfaces,
                router_id=router_id,
                bfd_profile="",
                log_file="/var/log/frr/ospf6d.log",
                log_precision=6,
                hello_interval=3
            )
        ospf6d_conf = ospf6d_conf.replace("这是 ospf6d 的配置", "")
        ospf6d_conf = '\n'.join([
            line for line in ospf6d_conf.split('\n')
            if not line.strip().startswith('ipv6 ospf6 bfd') and not line.strip().startswith('bfd')
        ])
        
        # 生成Zebra配置
        zebra_iface = ZebraInterfaceConfig(interface="lo", ipv6_address=lo_ipv6)
        zebra_conf = ZebraConfig(interface_config=zebra_iface, extra_comment="").to_config()
        
        # 生成守护进程配置
        daemons_conf = FrrDaemonsConfig(ospf6d=True, bfdd=True).to_config()
        
        # 生成BFD脚本
        bfd_sh = cls.generate_bfd_sh(interfaces)
        
        configs = {
            'ospf6d.conf': ospf6d_conf,
            'zebra.conf': zebra_conf,
            'daemons': daemons_conf,
            'bfd.sh': bfd_sh
        }
        return configs

    
    def _generate_network(self):
        """
        生成核心网络拓扑
        
        网络结构：
        - 2个用户节点 (user_1, user_2)
        - 2个地面站节点 (gs_1, gs_2)
        - 9个卫星节点 (Sat0-Sat8) 形成3x3网格
        - 各种链路连接
        
        拓扑连接示意图：
        
        用户层:
        user_1 (fd04::1) ────┐
                              │
        user_2 (fd05::1) ────┘
                              │
        地面站层:              │
        gs_1 (fd04::2) ───────┼─── Sat0 (eth4)
        gs_2 (fd05::2) ───────┘   │
                                   │
        卫星网络层 (3x3 Twisted Torus):
        
        ┌─────────┬─────────┬─────────┐
        │  Sat0   │  Sat1   │  Sat2   │
        │eth0↑eth2│eth0↑eth2│eth0↑eth2│
        │eth1→eth3│eth1→eth3│eth1→eth3│
        ├─────────┼─────────┼─────────┤
        │  Sat3   │  Sat4   │  Sat5   │
        │eth0↑eth2│eth0↑eth2│eth0↑eth2│
        │eth1→eth3│eth1→eth3│eth1→eth3│
        ├─────────┼─────────┼─────────┤
        │  Sat6   │  Sat7   │  Sat8   │
        │eth0↑eth2│eth0↑eth2│eth0↑eth2│
        │eth1→eth3│eth1→eth3│eth1→eth3│
        └─────────┴─────────┴─────────┘
        
        卫星节点接口分配:
        - eth0: 向上连接 (垂直方向)
        - eth1: 向右连接 (水平方向)  
        - eth2: 被上方节点连接
        - eth3: 被右方节点连接
        - eth4: 连接地面站
        
        连接规则 (Twisted Torus):
        - 垂直连接: (row, col) → ((row-1)%N, (col+PHASE_SHIFT)%M)
        - 水平连接: (row, col) → ((row+PHASE_SHIFT)%N, (col+1)%M)
        - PHASE_SHIFT = 1 (相位偏移)
        
        示例连接:
        Sat0(0,0) ──垂直──→ Sat6(2,1)  (eth0→eth2)
        Sat0(0,0) ──水平──→ Sat1(1,1)  (eth1→eth3)
        Sat1(0,1) ──垂直──→ Sat7(2,2)  (eth0→eth2)
        Sat1(0,1) ──水平──→ Sat2(1,2)  (eth1→eth3)
        """
        # 网络参数
        N = 3  # 卫星网格高度
        M = 3  # 卫星网格宽度
        PHASE_SHIFT = 1  # 相位偏移，用于生成twisted torus拓扑
        
        # IPv6地址配置
        USER_1_IPV6 = "fd04::1/64"
        USER_2_IPV6 = "fd05::1/64"
        GS_1_ETH1_IPV6 = "fd04::2/64"
        GS_2_ETH1_IPV6 = "fd05::2/64"
        
        node_id = 0
        
        # 1. 生成容器镜像
        image = Image.template(type_=ImageType.REGISTRY, repo="ponedo/frr-ubuntu20", tag="tiny", url="harbor.fir.ac.cn")
        image_repo = "ponedo/frr-ubuntu20:tiny"
        self.images.append(image)
        
        # 2. 生成用户节点
        # user_1 - 连接到gs_1
        self.user_1 = Node.template(
            name='user_1',
            image=image_repo,
            interfaces=[Interface.template(name='eth0', mode=InterfaceMode.DIRECT, ip_list=[USER_1_IPV6])],
            volumes=[],
            ext={}
        )
        
        # user_2 - 连接到gs_2
        self.user_2 = Node.template(
            name='user_2',
            image=image_repo,
            interfaces=[Interface.template(name='eth0', mode=InterfaceMode.DIRECT, ip_list=[USER_2_IPV6])],
            volumes=[],
            ext={}
        )
        
        # 3. 生成卫星节点 (3x3网格)
        for i in range(N * M):
            node_id += 1
            sat_node = Node.template(
                name=f'Sat{i}',
                image=image_repo,
                interfaces=[Interface.template(name=f'eth{j}', mode=InterfaceMode.DIRECT) for j in range(5)],
                volumes=[
                    VolumeMount.template(host_path=f'Sat{i}/frr_conf', container_path='/etc/frr', mode='rw'),
                    VolumeMount.template(host_path=f'Sat{i}/frr_log', container_path='/var/log/frr', mode='rw'),
                ],
                ext={}
            )
            self.sat_nodes.append(sat_node)
            
            # 生成卫星节点配置
            node_cfg = self.generate_ospf6d_node_configs('sat', node_id, N, sat_node)
            self.configs[f'Sat{i}'] = node_cfg
            
        # 4. 生成地面站节点
        # gs_1 - 连接user_1和Sat0
        self.gs_nodes.append(Node.template(
            name='gs_1',
            image=image_repo,
            interfaces=[Interface.template(name='eth0', mode=InterfaceMode.DIRECT), Interface.template(name='eth1', mode=InterfaceMode.DIRECT, ip_list=[GS_1_ETH1_IPV6])],
            volumes=[
                VolumeMount.template(host_path=f'gs_1/frr_conf', container_path='/etc/frr', mode='rw'),
                VolumeMount.template(host_path=f'gs_1/frr_log', container_path='/var/log/frr', mode='rw'),
            ],
            ext={}
        ))
        
        # gs_2 - 连接user_2和Sat1
        self.gs_nodes.append(Node.template(
            name='gs_2',
            image=image_repo,
            interfaces=[Interface.template(name='eth0', mode=InterfaceMode.DIRECT), Interface.template(name='eth1', mode=InterfaceMode.DIRECT, ip_list=[GS_2_ETH1_IPV6])],
            volumes=[
                VolumeMount.template(host_path=f'gs_2/frr_conf', container_path='/etc/frr', mode='rw'),
                VolumeMount.template(host_path=f'gs_2/frr_log', container_path='/var/log/frr', mode='rw'),
            ],
            ext={}
        ))
        
        # 生成地面站节点配置
        for gs_node in self.gs_nodes:
            node_id += 1
            node_cfg = self.generate_ospf6d_node_configs('gs', node_id, N, gs_node)
            self.configs[gs_node.name] = node_cfg
        
        # 5. 生成卫星间链路 (Twisted Torus拓扑)
        def sat_idx(row, col):
            """计算卫星节点在网格中的索引"""
            return row * M + col
        
        # 生成卫星间连接
        # 每个卫星节点连接到其上方和右方的邻居节点
        # 由于是Twisted Torus拓扑，连接带有相位偏移
        for row in range(N):
            for col in range(M):
                idx = sat_idx(row, col)
                
                # 上邻居连接（垂直方向，带相位偏移）
                # 公式: (row, col) → ((row-1)%N, (col+PHASE_SHIFT)%M)
                up_row = (row - 1) % N
                up_col = (col + PHASE_SHIFT) % M
                up_idx = sat_idx(up_row, up_col)
                self.s2s_links.append(Link.template(
                    id=f's2s_link_{idx}_{up_idx}',
                    endpoints=[f'Sat{idx}:eth0', f'Sat{up_idx}:eth2']
                ))
                
                # 右邻居连接（水平方向，带相位偏移）
                # 公式: (row, col) → ((row+PHASE_SHIFT)%N, (col+1)%M)
                right_row = (row + PHASE_SHIFT) % N
                right_col = (col + 1) % M
                right_idx = sat_idx(right_row, right_col)
                self.s2s_links.append(Link.template(
                    id=f's2s_link_{idx}_{right_idx}',
                    endpoints=[f'Sat{idx}:eth1', f'Sat{right_idx}:eth3']
                ))
        
        # 6. 生成地面站到卫星的链路
        # 地面站通过eth0接口连接到卫星的eth4接口
        # gs_1 连接 sat_0 (左上角卫星)
        self.g2s_links.append(Link.template(
            id='g2s_link_0',
            endpoints=['gs_1:eth0', 'Sat0:eth4']
        ))
        # gs_2 连接 sat_1 (第一行中间卫星)
        self.g2s_links.append(Link.template(
            id='g2s_link_1',
            endpoints=['gs_2:eth0', 'Sat1:eth4']
        ))
        
        # 7. 生成用户到地面站的链路
        # 用户通过eth0接口连接到地面站的eth1接口
        # user_1 连接 gs_1 (IPv6: fd04::1 → fd04::2)
        self.u2g_links.append(Link.template(
            id='user1_gs1_link',
            endpoints=['user_1:eth0', 'gs_1:eth1']
        ))
        # user_2 连接 gs_2 (IPv6: fd05::1 → fd05::2)
        self.u2g_links.append(Link.template(
            id='user2_gs2_link',
            endpoints=['user_2:eth0', 'gs_2:eth1']
        ))
        
        # 网络拓扑总结:
        # 总节点数: 13个 (2用户 + 2地面站 + 9卫星)
        # 总链路数: 18个卫星间链路 + 2个地面站-卫星链路 + 2个用户-地面站链路 = 22个链路
        # 网络层次: 用户层 → 地面站层 → 卫星网络层
        # 路由协议: OSPF6 (IPv6)
        # 检测协议: BFD (双向转发检测)
    
    def get_nodes(self) -> List[Node]:
        """获取所有节点列表"""
        return [self.user_1, self.user_2] + self.gs_nodes + self.sat_nodes
    
    def get_links(self) -> List[Link]:
        """获取所有链路列表"""
        return self.u2g_links + self.g2s_links + self.s2s_links
    
    def get_images(self) -> List[Image]:
        """获取所有镜像列表"""
        return self.images
    
    def get_node_names(self) -> List[str]:
        """获取所有节点名称列表"""
        node_names = []
        if self.user_1:
            node_names.append(self.user_1.name)
        if self.user_2:
            node_names.append(self.user_2.name)
        node_names.extend([node.name for node in self.gs_nodes])
        node_names.extend([node.name for node in self.sat_nodes])
        return node_names
    
    def init_mounts(self, mounts_dir: str):
        """
        初始化节点挂载点和配置文件
        
        Args:
            mounts_dir: 挂载点根目录
        """
        # 生成卫星节点挂载点和配置文件
        for sat_node in self.sat_nodes:
            conf_dir = os.path.join(mounts_dir, sat_node.name, 'frr_conf')
            log_dir = os.path.join(mounts_dir, sat_node.name, 'frr_log')
            os.makedirs(conf_dir, exist_ok=True)
            os.makedirs(log_dir, exist_ok=True)
            
            # 写入配置文件
            node_cfg = self.configs[sat_node.name]
            for fname, content in node_cfg.items():
                with open(os.path.join(conf_dir, fname), 'w') as f:
                    f.write(content)
                    
        # 生成地面站节点挂载点和配置文件
        for gs_node in self.gs_nodes:
            conf_dir = os.path.join(mounts_dir, gs_node.name, 'frr_conf')
            log_dir = os.path.join(mounts_dir, gs_node.name, 'frr_log')
            os.makedirs(conf_dir, exist_ok=True)
            os.makedirs(log_dir, exist_ok=True)
            
            # 写入配置文件
            node_cfg = self.configs[gs_node.name]
            for fname, content in node_cfg.items():
                with open(os.path.join(conf_dir, fname), 'w') as f:
                    f.write(content)

class SATuSGHLabGen:
    """
    SATuSGH实验室生成器

    负责创建完整的网络实验环境，包括：
    - 网络拓扑初始化
    - 时间线事件配置
    - 实验环境构建
    """

    # 时间线事件常量定义
    TIMELINE_DEFAULT_ROUTE = 100                # 默认路由下发时间（毫秒）
    TIMELINE_LINK_ATTR_SET = 1000               # 链路属性（如延迟、带宽）设置时间（毫秒）
    TIMELINE_FRR_START = 1000                   # FRR（快速重路由）启动时间（毫秒）
    TIMELINE_BFD_CONFIG = 10000                 # BFD（双向转发检测）配置时间（毫秒）
    TIMELINE_PING_TEST = 82000                  # ping 测试时间（毫秒）
    TIMELINE_GSL_HANDOVER_DESTROY = 85000       # GSL（地面站链路）切换-断开旧链路时间（毫秒）
    TIMELINE_GSL_HANDOVER_CREATE = 90000        # GSL（地面站链路）切换-建立新链路时间（毫秒）

    def __init__(self, output_dir: str, link_delete_offset: int = 0, link_create_offset: int = 0):
        """
        初始化实验室生成器

        Args:
            output_dir: 输出目录
            link_delete_offset: 删除链路的时间偏移量（毫秒）
            link_create_offset: 创建链路的时间偏移量（毫秒）
        """
        self.output_dir = output_dir
        self.core_net = SATuSGHCoreNet()  # 核心网络
        self.bg_net = BgNet(grid_h=6, grid_w=8, gs_count=4, phase_shift=1)  # 背景网络
        self.builder = Builder(output_dir=output_dir)  # 实验构建器

        self.link_delete_offset = link_delete_offset  # 删除链路的时间偏移量
        self.link_create_offset = link_create_offset  # 创建链路的时间偏移量

    def set_labbook(self, labbook: Labbook):
        """设置实验手册"""
        self.builder.set_labbook(labbook)


    def init_network(self):
        """初始化网络拓扑"""
        # 合并所有节点和链路
        all_nodes = self.core_net.get_nodes()
        all_links = self.core_net.get_links()
        if self.bg_net:
            all_nodes.extend(self.bg_net.get_nodes())
            all_links.extend(self.bg_net.get_links())

        # 添加所有镜像到builder
        for image in self.core_net.get_images():
            self.builder.add_image(image)

        # 添加所有节点到builder
        for node in all_nodes:
            self.builder.add_node(node)

        # 添加所有链路到builder
        for link in all_links:
            self.builder.add_link(link)

        print(f"网络拓扑初始化完成: {len(all_nodes)} 节点, {len(all_links)} 链路")

    def add_link_control_events(self):
        """添加链路控制事件（设置链路延迟等属性）"""
        if not self.builder:
            raise ValueError("请先调用 init_network() 初始化网络")

        # 获取所有链路
        all_links = self.core_net.get_links()

        if self.bg_net:
            all_links.extend(self.bg_net.get_links())

        # 创建链路属性事件
        events = []
        for i, link in enumerate(all_links):
            link_id = link.id if hasattr(link, 'id') else f'link{i}'
            link_properties = self.builder.new_link_properties(mode="up", delay="0ms")
            link_attr_set_event = self.builder.new_network_link_attr_set_event(id=link_id, link_properties=link_properties)
            events.append(link_attr_set_event)

        # 添加链路属性设置事件到时间线
        link_attr_set_action = self.builder.build_network_events_action(events, "all_links_attr_set")
        self.builder.add_timeline_item(at=self.TIMELINE_LINK_ATTR_SET, description="set all links delay 0ms", action=link_attr_set_action)

        print("链路控制事件添加完成")

    def add_frr_start_events(self):
        """添加FRR启动事件"""
        if not self.builder:
            raise ValueError("请先调用 init_network() 初始化网络")

        # 为核心网络节点创建FRR启动命令
        core_node_names = self.core_net.get_node_names()
        netfunc_events = []
        for name in core_node_names:
            exec_args = self.builder.new_node_exec_args(shellcodes=['chown -R frr:frr /var/log/frr', '/usr/lib/frr/frrinit.sh start'])
            netfunc_event = self.builder.new_netfunc_event(node_name=name, exec_args=exec_args)
            netfunc_events.append(netfunc_event)
        netfunc_action = self.builder.build_netfunc_events_action(netfunc_events, "all_nodes_frr_start")
        self.builder.add_timeline_item(at=self.TIMELINE_FRR_START, description="start frr on all nodes", action=netfunc_action)

        print(f"FRR启动事件添加完成: {len(core_node_names)} 个核心网络节点")

    def add_bfd_config_events(self):
        """添加BFD配置事件"""
        if not self.builder:
            raise ValueError("请先调用 init_network() 初始化网络")

        # 为核心网络节点创建BFD配置命令
        core_node_names = self.core_net.get_node_names()
        bfd_events = []
        for name in core_node_names:
            exec_args = self.builder.new_node_exec_args(shellcodes=['bash /etc/frr/bfd.sh'])
            bfd_event = self.builder.new_netfunc_event(node_name=name, exec_args=exec_args)
            bfd_events.append(bfd_event)
        bfd_action = self.builder.build_netfunc_events_action(bfd_events, "all_nodes_bfd_config")
        self.builder.add_timeline_item(at=self.TIMELINE_BFD_CONFIG, description="configure bfd on all nodes", action=bfd_action)

        print(f"BFD配置事件添加完成: {len(core_node_names)} 个核心网络节点")

    def add_ping_test_events(self):
        """添加ping测试事件（验证网络连通性）"""
        if not self.builder:
            raise ValueError("请先调用 init_network() 初始化网络")

        user_1 = self.core_net.user_1
        user_2 = self.core_net.user_2

        user_2_eth0_ipv6 = user_2.interfaces[0].ip_list[0].split('/')[0]

        # 创建ping测试事件
        exec_args = self.builder.new_node_exec_args(shellcodes=[f'ping6 -D -c 10000 -i 0.003 {user_2_eth0_ipv6}'], daemon=False, output=None)
        netfunc_event = self.builder.new_netfunc_exec_output_event(node_name=user_1.name, exec_args=exec_args)
        action = self.builder.build_netfunc_exec_output_event_action(netfunc_event, name="user1_ping_gs1")
        self.builder.add_timeline_item(at=self.TIMELINE_PING_TEST, description=f"{user_1.name} ping {user_2.name} lo", action=action)
        print(f"Ping测试事件添加完成: {user_1.name} -> {user_2.name}")

    def add_gsl_handover_events(self):
        """添加地面站间切换事件"""
        if not self.builder:
            raise ValueError("请先调用 init_network() 初始化网络")
        # 7.5 添加链路切换事件：gs_1到sat0切换为gs_1到Sat2
        # 首先销毁原有链路（link1: gs_1:eth0 -> Sat0:eth4）
        link_destroy_event = self.builder.new_network_link_destroy_event(id='g2s_link_0')
        link_destroy_action = self.builder.build_network_events_action([link_destroy_event], "destroy_gs1_sat0_link")
        self.builder.add_timeline_item(at=self.TIMELINE_GSL_HANDOVER_DESTROY + self.link_delete_offset, description="destroy link gs_1:eth0 -> Sat0:eth4", action=link_destroy_action)

        # 然后创建新链路（gs_1:eth0 -> Sat2:eth4）
        # 创建链路创建参数
        link_create_args = LinkCreateArgs.template(
            id='link_new_gs1_sat2',
            endpoints=['gs_1:eth0', 'Sat2:eth4'],
            l2_switch_id=None,  # 不使用L2交换机
            static_neigh=False,
            no_arp=False
        )
        # 创建链路属性
        link_properties = self.builder.new_link_properties(mode="up", delay="0ms")
        # 创建链路创建事件
        link_create_event = self.builder.new_network_link_create_event(
            id='link_new_gs1_sat2',
            link_create_args=link_create_args,
            link_properties=link_properties
        )
        link_create_action = self.builder.build_network_events_action([link_create_event], "create_gs1_sat2_link")
        self.builder.add_timeline_item(at=self.TIMELINE_GSL_HANDOVER_CREATE + self.link_create_offset, description="create link gs_1:eth0 -> Sat2:eth4", action=link_create_action)

    def add_config_default_route_events(self):
        """添加默认路由配置事件"""
        if not self.builder:
            raise ValueError("请先调用 init_network() 初始化网络")

        user_events = []
        user_1 = self.core_net.user_1
        user_2 = self.core_net.user_2
        GS_1_ETH1_IPV6 = "fd04::2"
        GS_2_ETH1_IPV6 = "fd05::2"

        # 为用户节点配置默认路由
        exec_args = self.builder.new_node_exec_args(shellcodes=[f'ip -6 route add default via {GS_1_ETH1_IPV6}'])
        user_event = self.builder.new_netfunc_event(node_name=user_1.name, exec_args=exec_args)
        user_events.append(user_event)

        exec_args = self.builder.new_node_exec_args(shellcodes=[f'ip -6 route add default via {GS_2_ETH1_IPV6}'])
        user_event = self.builder.new_netfunc_event(node_name=user_2.name, exec_args=exec_args)
        user_events.append(user_event)

        user_action = self.builder.build_netfunc_events_action(user_events, "all_users_default_route_config")
        self.builder.add_timeline_item(at=self.TIMELINE_DEFAULT_ROUTE, description="configure default route on all users", action=user_action)
        print("路由配置事件添加完成")

    def add_core_network_actions(self):
        """添加核心网络的所有事件"""
        # 0. 配置默认路由
        self.add_config_default_route_events()
        # 1. 启动 frr
        self.add_frr_start_events()
        # 2. 启动 bfd
        self.add_bfd_config_events()
        # 3. 执行 ping 命令
        self.add_ping_test_events()
        # 4. 添加地面站间切换事件
        self.add_gsl_handover_events()

    def build(self):
        """构建完整的实验环境"""
        if not self.builder:
            raise ValueError("请先调用 init_network() 初始化网络")

        # 构建labbook
        self.builder.build()

        # 初始化挂载点和配置文件
        mounts_dir = os.path.join(self.output_dir, 'network', 'mounts')
        self.core_net.init_mounts(mounts_dir)


class PingDataPoint:
    """单个ping数据点"""
    
    def __init__(self, timestamp: float, seq_num: int, response_time: Optional[float] = None, 
                 is_success: bool = True, error_msg: str = ""):
        self.timestamp = timestamp
        self.seq_num = seq_num
        self.response_time = response_time
        self.is_success = is_success
        self.error_msg = error_msg
    
    def __str__(self):
        if self.is_success:
            return f"[{self.timestamp}] seq={self.seq_num}, time={self.response_time}ms"
        else:
            return f"[{self.timestamp}] seq={self.seq_num}, ERROR: {self.error_msg}"


class PingAnalyzer:
    """Ping数据分析器 - 支持单文件和批量分析"""
    
    def __init__(self, data_dir: str = "../data"):
        self.data_points: List[PingDataPoint] = []
        self.outages: List[Dict] = []
        self.stats: Dict = {}
        self.data_dir = data_dir
        self.batch_results: Dict = {}
    
    def parse_file(self, file_path: str) -> bool:
        """解析ping输出文件"""
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
        
        print(f"正在解析文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        parsed_count = 0
        error_count = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # 跳过标题行
            if line.startswith('PING '):
                continue
            
            # 解析成功响应: [timestamp] 64 bytes from fd05::1: icmp_seq=X ttl=59 time=Y ms
            success_match = re.match(r'\[(\d+\.\d+)\]\s+64\s+bytes\s+from\s+fd05::1:\s+icmp_seq=(\d+)\s+ttl=\d+\s+time=(\d+\.?\d*)\s+ms', line)
            if success_match:
                timestamp = float(success_match.group(1))
                seq_num = int(success_match.group(2))
                response_time = float(success_match.group(3))
                
                data_point = PingDataPoint(
                    timestamp=timestamp,
                    seq_num=seq_num,
                    response_time=response_time,
                    is_success=True
                )
                self.data_points.append(data_point)
                parsed_count += 1
                continue
            
            # 解析错误响应: [timestamp] From fd04::2 icmp_seq=X Destination unreachable: No route
            error_match = re.match(r'\[(\d+\.\d+)\]\s+From\s+fd04::2\s+icmp_seq=(\d+)\s+Destination\s+unreachable:\s+No\s+route', line)
            if error_match:
                timestamp = float(error_match.group(1))
                seq_num = int(error_match.group(2))
                
                data_point = PingDataPoint(
                    timestamp=timestamp,
                    seq_num=seq_num,
                    is_success=False,
                    error_msg="Destination unreachable: No route"
                )
                self.data_points.append(data_point)
                parsed_count += 1
                continue
            
            # 如果都不匹配，记录错误
            error_count += 1
            if error_count <= 10:  # 只显示前10个错误
                print(f"无法解析第{line_num}行: {line}")
        
        print(f"解析完成: 成功解析 {parsed_count} 行，无法解析 {error_count} 行")
        return True
    
    def analyze_outages(self, min_outage_duration: float = 1.0) -> None:
        """分析服务中断时间段"""
        if not self.data_points:
            print("没有数据点可供分析")
            return
        
        # 按时间戳排序
        self.data_points.sort(key=lambda x: x.timestamp)
        
        outages = []
        outage_start = None
        outage_end = None
        
        for i, point in enumerate(self.data_points):
            if not point.is_success:
                # 发现错误点
                if outage_start is None:
                    # 开始新的中断
                    outage_start = point.timestamp
                    outage_end = point.timestamp
                else:
                    # 继续当前中断
                    outage_end = point.timestamp
            else:
                # 发现成功点
                if outage_start is not None:
                    # 结束当前中断
                    duration = outage_end - outage_start
                    if duration >= min_outage_duration:
                        outages.append({
                            'start_time': outage_start,
                            'end_time': outage_end,
                            'duration': duration,
                            'start_seq': self._find_seq_at_time(outage_start),
                            'end_seq': self._find_seq_at_time(outage_end)
                        })
                    outage_start = None
                    outage_end = None
        
        # 处理最后一个中断（如果文件以错误结束）
        if outage_start is not None:
            duration = outage_end - outage_start
            if duration >= min_outage_duration:
                outages.append({
                    'start_time': outage_start,
                    'end_time': outage_end,
                    'duration': duration,
                    'start_seq': self._find_seq_at_time(outage_start),
                    'end_seq': self._find_seq_at_time(outage_end)
                })
        
        self.outages = outages
        self._calculate_stats()
    
    def _find_seq_at_time(self, timestamp: float) -> Optional[int]:
        """根据时间戳查找序列号"""
        for point in self.data_points:
            if abs(point.timestamp - timestamp) < 0.001:  # 允许小的误差
                return point.seq_num
        return None
    
    def _calculate_stats(self) -> None:
        """计算统计信息"""
        if not self.data_points:
            return
        
        total_points = len(self.data_points)
        success_points = sum(1 for p in self.data_points if p.is_success)
        error_points = total_points - success_points
        
        # 计算响应时间统计
        response_times = [p.response_time for p in self.data_points if p.is_success and p.response_time is not None]
        
        stats = {
            'total_points': total_points,
            'success_points': success_points,
            'error_points': error_points,
            'success_rate': success_points / total_points * 100 if total_points > 0 else 0,
            'outage_count': len(self.outages),
            'total_outage_duration': sum(o['duration'] for o in self.outages),
            'avg_outage_duration': sum(o['duration'] for o in self.outages) / len(self.outages) if self.outages else 0,
            'min_outage_duration': min(o['duration'] for o in self.outages) if self.outages else 0,
            'max_outage_duration': max(o['duration'] for o in self.outages) if self.outages else 0
        }
        
        if response_times:
            stats.update({
                'avg_response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times)
            })
        
        self.stats = stats
    
    def print_summary(self) -> None:
        """打印分析摘要"""
        if not self.stats:
            print("没有统计数据")
            return
        
        print("\n" + "="*60)
        print("PING数据分析摘要")
        print("="*60)
        
        print(f"总数据点: {self.stats['total_points']}")
        print(f"成功响应: {self.stats['success_points']}")
        print(f"错误响应: {self.stats['error_points']}")
        print(f"成功率: {self.stats['success_rate']:.2f}%")
        
        if 'avg_response_time' in self.stats:
            print(f"平均响应时间: {self.stats['avg_response_time']:.3f} ms")
            print(f"最小响应时间: {self.stats['min_response_time']:.3f} ms")
            print(f"最大响应时间: {self.stats['max_response_time']:.3f} ms")
        
        print(f"\n服务中断统计:")
        print(f"中断次数: {self.stats['outage_count']}")
        print(f"总中断时间: {self.stats['total_outage_duration']:.2f} 秒")
        print(f"平均中断时间: {self.stats['avg_outage_duration']:.2f} 秒")
        print(f"最短中断时间: {self.stats['min_outage_duration']:.2f} 秒")
        print(f"最长中断时间: {self.stats['max_outage_duration']:.2f} 秒")
        
        if self.outages:
            print(f"\n详细中断信息:")
            for i, outage in enumerate(self.outages, 1):
                start_time = datetime.fromtimestamp(outage['start_time']).strftime('%Y-%m-%d %H:%M:%S')
                end_time = datetime.fromtimestamp(outage['end_time']).strftime('%H:%M:%S')
                print(f"  中断 {i}: {start_time} - {end_time} (持续 {outage['duration']:.2f}秒, 序列 {outage['start_seq']}-{outage['end_seq']})")
    
    def save_results(self, output_file: str) -> None:
        """保存分析结果到JSON文件"""
        results = {
            'stats': self.stats,
            'outages': self.outages,
            'data_points_count': len(self.data_points)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存到: {output_file}")
    
    def export_to_csv(self, data_file: str, outage_file: str) -> None:
        """导出数据到CSV格式"""
        # 导出ping数据点
        with open(data_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Sequence', 'Response_Time', 'Success', 'Error_Message'])
            
            for point in self.data_points:
                writer.writerow([
                    point.timestamp,
                    point.seq_num,
                    point.response_time if point.response_time else '',
                    point.is_success,
                    point.error_msg
                ])
        
        # 导出中断信息
        with open(outage_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Start_Time', 'End_Time', 'Duration', 'Start_Seq', 'End_Seq'])
            
            for outage in self.outages:
                writer.writerow([
                    outage['start_time'],
                    outage['end_time'],
                    outage['duration'],
                    outage['start_seq'],
                    outage['end_seq']
                ])
        
        print(f"数据已导出到: {data_file}")
        print(f"中断信息已导出到: {outage_file}")
    
    # 批量分析相关方法
    def find_ping_files(self) -> List[str]:
        """查找所有ping数据文件"""
        pattern = os.path.join(self.data_dir, "*.out")
        files = glob.glob(pattern)
        return sorted(files)
    
    def analyze_all_files(self, min_duration: float = 1.0) -> Dict:
        """分析所有文件"""
        files = self.find_ping_files()
        
        if not files:
            print(f"在目录 {self.data_dir} 中没有找到 *.out 文件")
            return {}
        
        print(f"找到 {len(files)} 个ping数据文件:")
        for f in files:
            print(f"  - {os.path.basename(f)}")
        
        all_results = {}
        total_stats = {
            'total_files': len(files),
            'total_outages': 0,
            'total_outage_duration': 0,
            'total_data_points': 0,
            'total_success_points': 0,
            'total_error_points': 0
        }
        
        for file_path in files:
            filename = os.path.basename(file_path)
            print(f"\n{'='*60}")
            print(f"分析文件: {filename}")
            print(f"{'='*60}")
            
            # 创建新的分析器实例处理单个文件
            single_analyzer = PingAnalyzer()
            if single_analyzer.parse_file(file_path):
                single_analyzer.analyze_outages(min_duration)
                single_analyzer.print_summary()
                
                # 保存单个文件结果
                all_results[filename] = {
                    'stats': single_analyzer.stats,
                    'outages': single_analyzer.outages,
                    'data_points_count': len(single_analyzer.data_points)
                }
                
                # 累计统计
                total_stats['total_outages'] += single_analyzer.stats.get('outage_count', 0)
                total_stats['total_outage_duration'] += single_analyzer.stats.get('total_outage_duration', 0)
                total_stats['total_data_points'] += single_analyzer.stats.get('total_points', 0)
                total_stats['total_success_points'] += single_analyzer.stats.get('success_points', 0)
                total_stats['total_error_points'] += single_analyzer.stats.get('error_points', 0)
        
        # 计算总体统计
        if total_stats['total_data_points'] > 0:
            total_stats['overall_success_rate'] = total_stats['total_success_points'] / total_stats['total_data_points'] * 100
        else:
            total_stats['overall_success_rate'] = 0
        
        if total_stats['total_outages'] > 0:
            total_stats['avg_outage_duration'] = total_stats['total_outage_duration'] / total_stats['total_outages']
        else:
            total_stats['avg_outage_duration'] = 0
        
        all_results['_summary'] = total_stats
        self.batch_results = all_results
        
        return all_results
    
    def print_batch_summary(self) -> None:
        """打印批量分析总体摘要"""
        if not self.batch_results:
            print("没有批量分析结果")
            return
        
        summary = self.batch_results.get('_summary', {})
        
        print(f"\n{'='*60}")
        print("批量分析总体摘要")
        print(f"{'='*60}")
        
        print(f"分析文件数: {summary.get('total_files', 0)}")
        print(f"总数据点: {summary.get('total_data_points', 0)}")
        print(f"总成功响应: {summary.get('total_success_points', 0)}")
        print(f"总错误响应: {summary.get('total_error_points', 0)}")
        print(f"总体成功率: {summary.get('overall_success_rate', 0):.2f}%")
        print(f"总中断次数: {summary.get('total_outages', 0)}")
        print(f"总中断时间: {summary.get('total_outage_duration', 0):.2f} 秒")
        print(f"平均中断时间: {summary.get('avg_outage_duration', 0):.2f} 秒")
        
        # 显示每个文件的摘要
        print(f"\n各文件摘要:")
        for filename, result in self.batch_results.items():
            if filename == '_summary':
                continue
            
            stats = result.get('stats', {})
            print(f"  {filename}:")
            print(f"    数据点: {stats.get('total_points', 0)}, 成功率: {stats.get('success_rate', 0):.2f}%")
            print(f"    中断次数: {stats.get('outage_count', 0)}, 总中断时间: {stats.get('total_outage_duration', 0):.2f}秒")
    
    def save_batch_results(self, output_file: str) -> None:
        """保存批量分析结果到JSON文件"""
        if not self.batch_results:
            print("没有批量分析结果可保存")
            return
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.batch_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n批量分析结果已保存到: {output_file}")


def analyze_labbook_output(output_dir: str) -> dict:
    """
    分析 labbook 输出结果
    
    Args:
        output_dir: 输出目录路径
        
    Returns:
        分析结果字典
    """
    try:
        # 检查输出目录是否存在
        if not os.path.exists(output_dir):
            return {'error': '输出目录不存在'}
        
        # 检查关键文件是否存在
        network_dir = os.path.join(output_dir, 'network')
        if not os.path.exists(network_dir):
            return {'error': '网络配置目录不存在'}
        
        # 统计节点和链路数量
        nodes_count = 0
        links_count = 0
        
        # 检查节点配置
        nodes_dir = os.path.join(network_dir, 'nodes')
        if os.path.exists(nodes_dir):
            nodes_count = len([f for f in os.listdir(nodes_dir) if os.path.isdir(os.path.join(nodes_dir, f))])
        
        # 检查链路配置
        links_dir = os.path.join(network_dir, 'links')
        if os.path.exists(links_dir):
            links_count = len([f for f in os.listdir(links_dir) if f.endswith('.json')])
        
        # 检查时间线文件
        timeline_file = os.path.join(output_dir, 'timeline.json')
        timeline_exists = os.path.exists(timeline_file)
        
        # 检查ping结果文件并进行分析
        ping_results = {}
        ping_files = glob.glob(os.path.join(output_dir, "*.out"))
        
        if ping_files:
            analyzer = PingAnalyzer(output_dir)
            batch_results = analyzer.analyze_all_files()
            if batch_results:
                summary = batch_results.get('_summary', {})
                ping_results = {
                    'ping_files_count': summary.get('total_files', 0),
                    'total_data_points': summary.get('total_data_points', 0),
                    'overall_success_rate': summary.get('overall_success_rate', 0),
                    'total_outages': summary.get('total_outages', 0),
                    'total_outage_duration': summary.get('total_outage_duration', 0),
                    'avg_outage_duration': summary.get('avg_outage_duration', 0)
                }
        
        # 返回分析结果
        result = {
            'nodes_count': nodes_count,
            'links_count': links_count,
            'timeline_exists': timeline_exists,
            'output_dir': output_dir,
            'analysis_time': str(datetime.now()),
            'status': 'completed'
        }
        
        # 如果有ping分析结果，添加到返回结果中
        if ping_results:
            result.update(ping_results)
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed',
            'analysis_time': str(datetime.now())
        }