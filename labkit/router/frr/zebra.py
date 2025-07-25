# zebra 配置生成相关函数

class ZebraInterfaceConfig:
    """
    用于生成 zebra.conf 接口配置的类

    属性:
        interface (str): 接口名称，如 "lo"
        ipv6_address (str): IPv6 地址，如 "fd01::0:2:1/128"
    """
    def __init__(self, interface: str = "lo", ipv6_address: str = "fd01::0:2:1/128"):
        self.interface = interface
        self.ipv6_address = ipv6_address

    def to_config(self) -> str:
        """
        生成接口相关的配置字符串
        """
        lines = [
            f"interface {self.interface}",
            f"  ipv6 address {self.ipv6_address}"
        ]
        return "\n".join(lines)


class ZebraConfig:
    """
    用于生成 zebra.conf 全局配置的类

    属性:
        interface_config (ZebraInterfaceConfig): 接口配置对象
        ip_forwarding (bool): 是否启用 IPv4 转发
        ipv6_forwarding (bool): 是否启用 IPv6 转发
        log_precision (int): 日志时间戳精度
        log_file (str): 日志文件路径
        extra_comment (str): 额外说明
    """
    def __init__(
        self,
        interface_config: ZebraInterfaceConfig = None,
        ip_forwarding: bool = True,
        ipv6_forwarding: bool = True,
        log_precision: int = 6,
        log_file: str = "/var/log/frr debug",
        extra_comment: str = "这是 zebra.conf ，帮我生成相应配置类"
    ):
        self.interface_config = interface_config or ZebraInterfaceConfig()
        self.ip_forwarding = ip_forwarding
        self.ipv6_forwarding = ipv6_forwarding
        self.log_precision = log_precision
        self.log_file = log_file
        self.extra_comment = extra_comment

    def to_config(self) -> str:
        """
        生成 zebra.conf 配置字符串
        """
        lines = []
        # 接口配置
        lines.append(self.interface_config.to_config())
        # 全局配置
        if self.ip_forwarding:
            lines.append("ip forwarding")
        if self.ipv6_forwarding:
            lines.append("ipv6 forwarding")
        lines.append(f"log timestamp precision {self.log_precision}")
        lines.append(f"log file {self.log_file}")
        if self.extra_comment:
            lines.append(self.extra_comment)
        return "\n".join(lines)