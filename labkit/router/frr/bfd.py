# bfd 配置生成相关函数 
class BfdProfileConfig:
    """
    用于生成 bfdd.conf 配置的 BFD Profile 配置类
    """

    def __init__(self, profile_name="bfdd", detect_multiplier=3, receive_interval=10, transmit_interval=5):
        self.profile_name = profile_name
        self.detect_multiplier = detect_multiplier
        self.receive_interval = receive_interval
        self.transmit_interval = transmit_interval

    def to_config(self) -> str:
        """
        生成 bfdd.conf 格式的配置字符串
        """
        lines = [
            f"bfd profile {self.profile_name}",
            f"  detect-multiplier {self.detect_multiplier}",
            f"  receive-interval {self.receive_interval}",
            f"  transmit-interval {self.transmit_interval}",
        ]
        return "\n".join(lines)
