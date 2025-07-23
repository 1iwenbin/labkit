from labkit.models.network import NetworkConfig, Node, Interface, InterfaceMode, Link, L2Switch, Image, ImageType
from labkit.visualization import NetworkVisualizer

# 构造 demo 网络拓扑
image = Image(type=ImageType.REGISTRY, repo="ubuntu", tag="20.04")

node1 = Node(
    name="client-1",
    image="ubuntu:20.04",
    interfaces=[
        Interface(name="eth0", mode=InterfaceMode.DIRECT, ip=["192.168.1.10/24"])
    ]
)
node2 = Node(
    name="server-1",
    image="ubuntu:20.04",
    interfaces=[
        Interface(name="eth0", mode=InterfaceMode.DIRECT, ip=["192.168.1.20/24"])
    ]
)

switch = L2Switch(id="switch-1")

link1 = Link(id="link-1", endpoints=["client-1:eth0", "switch-1:swp1"], switch="switch-1")
link2 = Link(id="link-2", endpoints=["server-1:eth0", "switch-1:swp2"], switch="switch-1")

net_cfg = NetworkConfig(
    images=[image],
    nodes=[node1, node2],
    switches=[switch],
    links=[link1, link2]
)

# 可视化
visualizer = NetworkVisualizer(net_cfg)

# 1. Matplotlib 静态图
visualizer.plot_matplotlib()

# 2. Plotly 交互式图（在 notebook 或支持的环境下显示）
try:
    fig = visualizer.plot_plotly()
    fig.show()
    # 保存为 HTML 文件
    fig.write_html("network_topology_demo.html")
    print("已保存为 network_topology_demo.html")
except Exception as e:
    print("Plotly 可视化失败：", e) 