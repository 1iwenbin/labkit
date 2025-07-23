# Labkit Builder AI 驱动实验环境构建指南

## 简介

本指南面向希望通过 AI 脚本自动化构建 Labkit 实验环境的开发者，介绍如何使用 `Builder` 类及其相关 API 快速生成标准化的 labbook 目录结构和配置文件。通过本指南，AI 可自动完成网络实验环境的描述、节点与链路配置、动态流程编排等任务。

## 基本用法

1. **导入 Builder 及相关模型**
   ```python
   from labkit.builder.labbook_builder import Builder
   from labkit.models.labbook import Labbook
   from labkit.models.network import Image, ImageType, Node, Interface, InterfaceMode, Link, VolumeMount
   from labkit.models.events import LinkPropertiesMode
   ```
2. **创建 Builder 实例**
   ```python
   builder = Builder(output_dir="your_labbook_dir")
   ```
3. **设置实验元数据（labbook）**
   ```python
   builder.set_labbook(Labbook.template(name="实验名", description="描述", author="作者", tags=["标签1", "标签2"]))
   ```
4. **添加镜像、节点、链路等网络配置**
   ```python
   image = Image.template(type_=ImageType.REGISTRY, repo="your/repo", tag="tag", url="your.registry")
   builder.add_image(image)
   ...
   ```
5. **添加时间线事件（如链路属性设置、节点命令执行等）**
   ```python
   # 见下方完整示例
   ```
6. **构建实验环境**
   ```python
   builder.build()
   ```

## 主要 API 说明

- `Builder(output_dir)`: 构建器主类，负责协调 labbook、network、playbook 的生成。
- `set_labbook(labbook)`: 设置实验元数据。
- `add_image(image)`: 添加实验所需镜像。
- `add_node(node)`: 添加节点。
- `add_link(link)`: 添加链路。
- `add_timeline_item(at, description, action)`: 添加时间线事件。
- `new_link_properties(mode, bandwidth, loss, delay)`: 构造链路属性对象。
- `new_network_link_attr_set_event(id, link_properties)`: 构造链路属性设置事件。
- `build_network_events_action(events, name)`: 构造网络事件动作。
- `new_node_exec_args(shellcodes, output, timeout)`: 构造节点命令执行参数。
- `new_netfunc_exec_output_event(node_name, exec_args)`: 构造节点命令执行事件。
- `build_netfunc_exec_output_event_action(event, name)`: 构造节点命令执行动作。

> 更多高级 API 可参考 `labkit/builder/labbook_builder.py`。

## 完整示例

```python
from labkit.builder.labbook_builder import Builder
from labkit.models.labbook import Labbook
from labkit.models.network import Image, ImageType, Node, Interface, InterfaceMode, Link, VolumeMount
from labkit.models.events import LinkPropertiesMode

def main():
    labbook_dir = "book1"
    builder = Builder(output_dir=labbook_dir)
    builder.set_labbook(Labbook.template(name="book1", description="book1", author="book1", tags=["book1"]))
    image = Image.template(type_=ImageType.REGISTRY, repo="ponedo/frr-ubuntu20", tag="tiny", url="harbor.fir.ac.cn")
    builder.add_image(image)
    volume_mount = VolumeMount.template(host_path="node1/data", container_path="data", mode="rw")
    volume_mount2 = VolumeMount.template(host_path="node2/data", container_path="data", mode="rw")
    node1 = Node.template(name="node1", image="ponedo/frr-ubuntu20:tiny", interfaces=[Interface.template(name="eth0", mode=InterfaceMode.DIRECT, ip_list=["192.168.1.100/24"])], volumes=[volume_mount])
    builder.add_node(node1)
    node2 = Node.template(name="node2", image="ponedo/frr-ubuntu20:tiny", interfaces=[Interface.template(name="eth0", mode=InterfaceMode.DIRECT, ip_list=["192.168.1.101/24"])], volumes=[volume_mount2])
    builder.add_node(node2)
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
    builder.build()

if __name__ == "__main__":
    main()
```

## 常见问题与建议

- **目录结构自动生成**：`builder.build()` 会自动生成标准 labbook 目录及配置文件，无需手动创建。
- **参数模板化**：推荐使用各模型的 `template` 方法快速生成参数对象，减少出错。
- **AI 脚本自动化**：可将上述流程封装为函数，结合 AI 规划自动生成实验环境。
- **调试建议**：如遇到生成文件不符合预期，可逐步打印各对象内容，或查阅 `labkit/builder/labbook_builder.py` 及相关模型源码。
- **扩展性**：如需自定义更复杂的网络拓扑或事件，可参考 Builder 的更多 API 或直接扩展模型。

---

如有更多问题，建议查阅 Labkit 官方文档或源码，或联系开发团队。 