# daemons 配置生成相关函数 
class FrrDaemonsConfig:
    """
    用于生成 frr daemons 文件的配置类

    属性:
        bgpd (bool): 是否启用 BGP 守护进程
        ospfd (bool): 是否启用 OSPFv2 守护进程
        ospf6d (bool): 是否启用 OSPFv3 (OSPF6) 守护进程
        ripd (bool): 是否启用 RIP 守护进程
        ripngd (bool): 是否启用 RIPng 守护进程
        isisd (bool): 是否启用 ISIS 守护进程
        pimd (bool): 是否启用 PIM 守护进程
        ldpd (bool): 是否启用 LDP 守护进程
        nhrpd (bool): 是否启用 NHRP 守护进程
        eigrpd (bool): 是否启用 EIGRP 守护进程
        babeld (bool): 是否启用 Babel 守护进程
        sharpd (bool): 是否启用 SharpD 守护进程
        pbrd (bool): 是否启用 PBR 守护进程
        bfdd (bool): 是否启用 BFD 守护进程
        fabricd (bool): 是否启用 Fabric 守护进程
        vrrpd (bool): 是否启用 VRRP 守护进程
        pathd (bool): 是否启用 PathD 守护进程
        watchfrr_enable (bool): 是否启用 watchfrr
        zebra (bool): 是否启用 zebra
        vtysh_enable (bool): 是否启用 vtysh
        options (dict): 各守护进程的启动参数（如 {"zebra": "-A 127.0.0.1"}）
        max_fds (int): 最大文件描述符数
        extra_lines (list): 额外的自定义配置行
    """

    DAEMONS = [
        "bgpd", "ospfd", "ospf6d", "ripd", "ripngd", "isisd", "pimd", "ldpd",
        "nhrpd", "eigrpd", "babeld", "sharpd", "pbrd", "bfdd", "fabricd", "vrrpd", "pathd"
    ]

    def __init__(
        self,
        bgpd=False,
        ospfd=False,
        ospf6d=True,
        ripd=False,
        ripngd=False,
        isisd=False,
        pimd=False,
        ldpd=False,
        nhrpd=False,
        eigrpd=False,
        babeld=False,
        sharpd=False,
        pbrd=False,
        bfdd=True,
        fabricd=False,
        vrrpd=False,
        pathd=False,
        watchfrr_enable=True,
        zebra=True,
        vtysh_enable=True,
        options=None,
        max_fds=12288,
        extra_lines=None
    ):
        self.bgpd = bgpd
        self.ospfd = ospfd
        self.ospf6d = ospf6d
        self.ripd = ripd
        self.ripngd = ripngd
        self.isisd = isisd
        self.pimd = pimd
        self.ldpd = ldpd
        self.nhrpd = nhrpd
        self.eigrpd = eigrpd
        self.babeld = babeld
        self.sharpd = sharpd
        self.pbrd = pbrd
        self.bfdd = bfdd
        self.fabricd = fabricd
        self.vrrpd = vrrpd
        self.pathd = pathd
        self.watchfrr_enable = watchfrr_enable
        self.zebra = zebra
        self.vtysh_enable = vtysh_enable
        self.options = options or {
            "zebra":    "-A 127.0.0.1 -s 90000000",
            "bgpd":     "-A 127.0.0.1",
            "ospfd":    "-A 127.0.0.1",
            "ospf6d":   "-A ::1",
            "ripd":     "-A 127.0.0.1",
            "ripngd":   "-A ::1",
            "isisd":    "-A 127.0.0.1",
            "pimd":     "-A 127.0.0.1",
            "ldpd":     "-A 127.0.0.1",
            "nhrpd":    "-A 127.0.0.1",
            "eigrpd":   "-A 127.0.0.1",
            "babeld":   "-A 127.0.0.1",
            "sharpd":   "-A 127.0.0.1",
            "pbrd":     "-A 127.0.0.1",
            "staticd":  "-A 127.0.0.1",
            "bfdd":     "-A 127.0.0.1",
            "fabricd":  "-A 127.0.0.1",
            "vrrpd":    "-A 127.0.0.1",
            "pathd":    "-A 127.0.0.1"
        }
        self.max_fds = max_fds
        self.extra_lines = extra_lines or []

    def to_config(self) -> str:
        """
        生成 daemons 文件的配置字符串（包含官方注释头）
        """
        header = [
            "# This file tells the frr package which daemons to start.",
            "#",
            "# Sample configurations for these daemons can be found in",
            "# /usr/share/doc/frr/examples/.",
            "#",
            "# ATTENTION:",
            "#",
            "# When activating a daemon for the first time, a config file, even if it is",
            "# empty, has to be present *and* be owned by the user and group \"frr\", else",
            "# the daemon will not be started by /etc/init.d/frr. The permissions should",
            "# be u=rw,g=r,o=.",
            "# When using \"vtysh\" such a config file is also needed. It should be owned by",
            "# group \"frrvty\" and set to ug=rw,o= though. Check /etc/pam.d/frr, too.",
            "#",
            "# The watchfrr, zebra and staticd daemons are always started.",
            "#"
        ]
        lines = []
        # 守护进程开关
        for daemon in self.DAEMONS:
            enabled = getattr(self, daemon)
            lines.append(f"{daemon}={'yes' if enabled else 'no'}")
        # watchfrr, zebra, vtysh
        lines.append(f"watchfrr_enable={'yes' if self.watchfrr_enable else 'no'}")
        lines.append(f"zebra={'yes' if self.zebra else 'no'}")
        lines.append("#")
        lines.append("# If this option is set the /etc/init.d/frr script automatically loads")
        lines.append("# the config via \"vtysh -b\" when the servers are started.")
        lines.append("# Check /etc/pam.d/frr if you intend to use \"vtysh\"!")
        lines.append("#")
        lines.append(f"vtysh_enable={'yes' if self.vtysh_enable else 'no'}")
        # 各守护进程 options
        for daemon, opt in self.options.items():
            if opt is not None and opt != "":
                lines.append(f"{daemon}_options=\"{opt}\"")
        # 最大文件描述符数
        if self.max_fds is not None:
            lines.append("# configuration profile")
            lines.append("#")
            lines.append("#frr_profile=\"traditional\"")
            lines.append("#frr_profile=\"datacenter\"")
            lines.append("#")
            lines.append("# This is the maximum number of FD's that will be available.")
            lines.append("# Upon startup this is read by the control files and ulimit")
            lines.append("# is called.  Uncomment and use a reasonable value for your")
            lines.append("# setup if you are expecting a large number of peers in")
            lines.append("# say BGP.")
            lines.append(f"MAX_FDS={self.max_fds}")
        # 额外自定义行
        if self.extra_lines:
            lines.extend(self.extra_lines)
        # 追加尾部注释
        tail = [
            "# The list of daemons to watch is automatically generated by the init script.",
            "#watchfrr_options=\"\"",
            "# To make watchfrr create/join the specified netns, use the following option:",
            "#watchfrr_options=\"--netns\"",
            "# This only has an effect in /etc/frr/<somename>/daemons, and you need to",
            "# start FRR with \"/usr/lib/frr/frrinit.sh start <somename>\".",
            "# for debugging purposes, you can specify a \"wrap\" command to start instead",
            "# of starting the daemon directly, e.g. to use valgrind on ospfd:",
            "#   ospfd_wrap=\"/usr/bin/valgrind\"",
            "# or you can use \"all_wrap\" for all daemons, e.g. to use perf record:",
            "#   all_wrap=\"/usr/bin/perf record --call-graph -\"",
            "# the normal daemon command is added to this at the end.",
        ]
        return "\n".join(header + lines + tail)
