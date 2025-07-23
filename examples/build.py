from labkit.builder.labbook_builder import Builder
from labkit.models.labbook import Labbook
from labkit.models.network import Image, ImageType, Node, Interface, InterfaceMode, Link, VolumeMount
from labkit.models.events import NetFuncExecOutputEvent, NetFuncEvent, NetworkEvent, LinkPropertiesMode

def main():
    labbook_dir = "book1"
    # 创建 builder
    builder = Builder(output_dir=labbook_dir)
    # 设置 labbook
    builder.set_labbook(Labbook.template(name="book1", description="book1", author="book1", tags=["book1"]))
    # 设置网络配置
    # 配置镜像
    image = Image.template(type_=ImageType.REGISTRY, repo="ponedo/frr-ubuntu20", tag="tiny", url="harbor.fir.ac.cn")
    builder.add_image(image)
    volume_mount = VolumeMount.template(host_path="node1/data", container_path="data", mode="rw")
    volume_mount2 = VolumeMount.template(host_path="node2/data", container_path="data", mode="rw")
    # 配置节点
    node1 = Node.template(name="node1", image="ponedo/frr-ubuntu20:tiny", interfaces=[Interface.template(name="eth0", mode=InterfaceMode.DIRECT, ip_list=["192.168.1.100/24"])], volumes=[volume_mount])
    builder.add_node(node1)
    node2 = Node.template(name="node2", image="ponedo/frr-ubuntu20:tiny", interfaces=[Interface.template(name="eth0", mode=InterfaceMode.DIRECT, ip_list=["192.168.1.101/24"])], volumes=[volume_mount2])
    builder.add_node(node2)
    # 配置链路
    link1 = Link.template(id="link1", endpoints=["node1:eth0", "node2:eth0"])
    builder.add_link(link1)
    
    link_properties = builder.new_link_properties(mode=LinkPropertiesMode.UP, bandwidth="100Mbps", loss="0.00%", delay="10ms")
    link_attr_set_event = builder.new_network_link_attr_set_event(id="link1", link_properties=link_properties)
    link_attr_set_action = builder.build_network_events_action([link_attr_set_event], "link_attr_set_event")
    builder.add_timeline_item(at=1000, description="set link1 link properties up 100Mbps delay 10ms loss 0.00%", action=link_attr_set_action)
    

    exec_args = builder.new_node_exec_args(shellcodes=["ping -c 10 -i 0.1 192.168.1.101"], output="/tmp/output.log", timeout=30)
    netfunc_event = builder.new_netfunc_exec_output_event(node_name="node1", exec_args=exec_args)
    netfunc_action = builder.build_netfunc_exec_output_event_action(netfunc_event, "netfunc_exec_output_event")
    builder.add_timeline_item(at=2000, description="ping node1 10 times", action=netfunc_action)
    
    # 构建网络
    builder.build()

if __name__ == "__main__":
    main()