from labkit.builder.labbook_builder import Builder
from labkit.models.labbook import Labbook
from labkit.models.network import Image, ImageType, Node, Interface, InterfaceMode, Link, VolumeMount
from labkit.models.events import LinkPropertiesMode

def main():
    labbook_dir = "book2"
    builder = Builder(output_dir=labbook_dir)
    builder.set_labbook(Labbook.template(name="book2", description="Grid 3x3 topology", author="ai", tags=["grid", "3x3"]))

    # 镜像
    image = Image.template(type_=ImageType.REGISTRY, repo="ponedo/frr-ubuntu20", tag="tiny", url="harbor.fir.ac.cn")
    builder.add_image(image)

    grid_size = 3
    nodes = []
    node_interfaces = [{} for _ in range(grid_size * grid_size)]  # 记录每个节点每个接口的IP
    links = []  # (link_id, n1, eth1_idx, n2, eth2_idx, subnet, ip1, ip2)
    subnet_base = 10  # 10.0.x.0/24
    link_id = 0

    # 先分配链路和IP
    for row in range(grid_size):
        for col in range(grid_size):
            idx = row * grid_size + col
            # 右邻居
            if col < grid_size - 1:
                n1, n2 = idx, idx + 1
                subnet = f"10.0.{subnet_base}.0/24"
                ip1 = f"10.0.{subnet_base}.1/24"
                ip2 = f"10.0.{subnet_base}.2/24"
                node_interfaces[n1][1] = ip1  # eth1
                node_interfaces[n2][3] = ip2  # eth3
                links.append((f"link{link_id}", n1, 1, n2, 3, subnet, ip1, ip2))
                subnet_base += 1
                link_id += 1
            # 下邻居
            if row < grid_size - 1:
                n1, n2 = idx, idx + grid_size
                subnet = f"10.0.{subnet_base}.0/24"
                ip1 = f"10.0.{subnet_base}.1/24"
                ip2 = f"10.0.{subnet_base}.2/24"
                node_interfaces[n1][2] = ip1  # eth2
                node_interfaces[n2][0] = ip2  # eth0
                links.append((f"link{link_id}", n1, 2, n2, 0, subnet, ip1, ip2))
                subnet_base += 1
                link_id += 1

    # 创建节点
    for i in range(grid_size * grid_size):
        node_name = f"node{i}"
        interfaces = []
        for j in range(4):
            ip_list = [node_interfaces[i][j]] if j in node_interfaces[i] else None
            interfaces.append(
                Interface.template(name=f"eth{j}", mode=InterfaceMode.DIRECT, ip_list=ip_list)
            )
        node = Node.template(name=node_name, image="ponedo/frr-ubuntu20:tiny", interfaces=interfaces)
        builder.add_node(node)
        nodes.append(node_name)

    # 创建链路
    for (lid, n1, eth1_idx, n2, eth2_idx, subnet, ip1, ip2) in links:
        builder.add_link(Link.template(id=lid, endpoints=[f"node{n1}:eth{eth1_idx}", f"node{n2}:eth{eth2_idx}"]))

    # 聚合所有链路属性设置事件
    events = []
    for (lid, n1, eth1_idx, n2, eth2_idx, subnet, ip1, ip2) in links:
        link_properties = builder.new_link_properties(mode=LinkPropertiesMode.UP, delay="10ms")
        link_attr_set_event = builder.new_network_link_attr_set_event(id=lid, link_properties=link_properties)
        events.append(link_attr_set_event)
    link_attr_set_action = builder.build_network_events_action(events, "all_links_attr_set")
    builder.add_timeline_item(at=1000, description="set all links delay 10ms", action=link_attr_set_action)

    # 每个ping output事件单独action和timeline，ping命令目标IP不带mask
    ping_event_idx = 0
    for i in range(grid_size * grid_size):
        node_name = f"node{i}"
        for j in range(4):
            my_ip = node_interfaces[i].get(j)
            if my_ip is None:
                continue
            peer_ip = None
            for (lid, n1, eth1_idx, n2, eth2_idx, subnet, ip1, ip2) in links:
                if n1 == i and eth1_idx == j:
                    peer_ip = ip2
                    break
                if n2 == i and eth2_idx == j:
                    peer_ip = ip1
                    break
            if peer_ip:
                peer_ip_noprefix = peer_ip.split('/')[0]
                exec_args = builder.new_node_exec_args(
                    shellcodes=[f"ping -c 10 -i 0.1 {peer_ip_noprefix}"],
                    output=f"/tmp/{node_name}_eth{j}_ping.log",
                    timeout=30
                )
                netfunc_event = builder.new_netfunc_exec_output_event(node_name=node_name, exec_args=exec_args)
                netfunc_action = builder.build_netfunc_exec_output_event_action(netfunc_event, f"{node_name}_eth{j}_ping")
                builder.add_timeline_item(
                    at=2000 + ping_event_idx,
                    description=f"{node_name} eth{j} ping neighbor {peer_ip_noprefix}",
                    action=netfunc_action
                )
                ping_event_idx += 1

    builder.build()

if __name__ == "__main__":
    main() 