# zebra 配置生成相关函数 
def generate_zebra_config(
    loopback_ipv6="fd01::0:2:1/128",
    log_file="/var/log/frr",
    log_precision=6,
    extra_comment="这是 zebra.conf 配置"
) -> str:
    """
    生成 zebra.conf 配置内容

    参数:
        loopback_ipv6 (str): Loopback 接口的 IPv6 地址，默认为 "fd01::0:2:1/128"
        log_file (str): 日志文件路径，默认为 "/var/log/frr"
        log_precision (int): 日志时间戳精度，默认为 6
        extra_comment (str): 配置文件结尾的注释

    返回:
        str: 完整的 zebra.conf 配置内容
    """
    lines = [
        "interface lo",
        f"  ipv6 address {loopback_ipv6}",
        "ip forwarding",
        "ipv6 forwarding",
        f"log timestamp precision {log_precision}",
        f"log file {log_file} debug",
        extra_comment
    ]
    return "\n".join(lines)
