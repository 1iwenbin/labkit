# ospf 配置生成相关函数
# 本模块用于生成 FRR 的 OSPF6 (ospf6d) 配置文件相关的 Python 类和函数

class Ospf6InterfaceConfig:
    """
    用于生成 OSPF6 接口配置的类

    属性:
        interface (str): 接口名称，如 "eth0"
        area (str): OSPF6 区域，默认为 "0.0.0.0"
        bfd (bool): 是否启用 BFD，默认为 False
        bfd_profile (str): BFD profile 名称，默认为 "bfdd"
    """
    def __init__(self, interface: str, area: str = "0.0.0.0", bfd: bool = False, bfd_profile: str = "bfdd"):
        self.interface = interface
        self.area = area
        self.bfd = bfd
        self.bfd_profile = bfd_profile

    def to_config(self) -> str:
        """
        生成 OSPF6 接口的配置字符串

        Returns:
            str: 接口相关的配置片段
        """
        lines = [
            f"interface {self.interface}",
            f"    ipv6 ospf6 area {self.area}"
        ]
        if self.bfd:
            # 启用 BFD
            lines.append("ipv6 ospf6 bfd")
            if self.bfd_profile:
                # 指定 BFD profile
                lines.append(f"ipv6 ospf6 bfd profile {self.bfd_profile}")
        lines.append("exit")
        return "\n".join(lines)


class Ospf6RouterConfig:
    """
    用于生成 OSPF6 路由器配置的类

    属性:
        router_id (str): OSPF6 路由器 ID
        redistribute_connected (bool): 是否重分发直连路由，默认为 True
        bfd (bool): 是否启用 BFD，默认为 False
        log_file (str): 日志文件路径
        log_precision (int): 日志时间戳精度
    """
    def __init__(self, router_id: str, redistribute_connected: bool = True, bfd: bool = False, log_file: str = "/var/log/frr/ospf6d.log", log_precision: int = 6):
        self.router_id = router_id
        self.redistribute_connected = redistribute_connected
        self.bfd = bfd
        self.log_file = log_file
        self.log_precision = log_precision

    def to_config(self) -> str:
        """
        生成 OSPF6 路由器全局配置字符串

        Returns:
            str: 路由器全局配置片段
        """
        lines = [
            "router ospf6",
            f"    ospf6 router-id {self.router_id}"
        ]
        if self.redistribute_connected:
            # 重分发直连路由
            lines.append("    redistribute connected")
        if self.bfd:
            # 启用 BFD
            lines.append("bfd")
        lines.append("exit")
        # 日志相关配置
        lines.append(f"log timestamp precision {self.log_precision}")
        lines.append(f"log file {self.log_file} debug")
        return "\n".join(lines)


def generate_ospf6d_config(interfaces, router_id, bfd_profile="bfdd", log_file="/var/log/frr/ospf6d.log", log_precision=6):
    """
    生成 ospf6d.conf 配置内容

    参数:
        interfaces (list): 需要配置 OSPF6 的接口列表，如 ["eth0", "eth1", ...]
        router_id (str): OSPF6 路由器 ID，如 "192.0.2.1"
        bfd_profile (str): BFD profile 名称，默认为 "bfdd"
        log_file (str): 日志文件路径
        log_precision (int): 日志时间戳精度

    Returns:
        str: 完整的 ospf6d.conf 配置内容
    """
    config_lines = []
    for iface in interfaces:
        # 为每个接口生成 OSPF6 配置
        iface_cfg = Ospf6InterfaceConfig(interface=iface, bfd_profile=bfd_profile)
        config_lines.append("!")
        config_lines.append(iface_cfg.to_config())
    config_lines.append("!")
    # 生成全局路由器配置
    router_cfg = Ospf6RouterConfig(router_id=router_id, log_file=log_file, log_precision=log_precision)
    config_lines.append(router_cfg.to_config())
    config_lines.append("!")
    config_lines.append("这是 ospf6d 的配置")  # 额外说明，可根据需要移除
    return "\n".join(config_lines)
