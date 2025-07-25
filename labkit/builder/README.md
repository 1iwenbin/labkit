 # labkit/builder 使用说明

## 简介

本目录下包含实验环境自动化构建的核心类，主要用于一键生成实验的 labbook 目录结构、网络配置、流程编排等文件。核心为 `Builder` 总控类，配合 `LabbookBuilder`、`NetworkBuilder`、`PlaybookBuilder` 子构建器协同工作。

---

## 主要类和方法

### 1. Builder 总控类

#### 初始化
```python
from labkit.builder.labbook_builder import Builder

builder = Builder(output_dir="your_output_dir")
```

#### Labbook 相关
- 设置 Labbook 元数据
  ```python
  builder.set_labbook(labbook)
  # labbook: Labbook 实例
  ```

#### Network 相关
- 添加节点
  ```python
  builder.add_node(node)
  # node: Node 实例
  ```
- 添加交换机
  ```python
  builder.add_switch(switch)
  # switch: L2Switch 实例
  ```
- 添加链路
  ```python
  builder.add_link(link)
  # link: Link 实例
  ```
- 添加镜像
  ```python
  builder.add_image(image)
  # image: Image 实例
  ```

#### Playbook 相关
- 添加时间线项
  ```python
  builder.add_timeline_item(at, description, action)
  # at: int，时间点
  # description: str，描述
  # action: Action 实例
  ```
- 生成 network events 动作
  ```python
  action = builder.build_network_events_action(events, name)
  # events: List[NetworkEvent]
  # name: str，动作文件名（不带路径）
  ```
- 生成 netfunc events 动作
  ```python
  action = builder.build_netfunc_events_action(events, name)
  # events: List[NetFuncEvent]
  # name: str
  ```
- 生成 netfunc exec output event 动作
  ```python
  action = builder.build_netfunc_exec_output_event_action(event, name)
  # event: NetFuncExecOutputEvent
  # name: str
  ```
- 新建自定义动作
  ```python
  action = builder.new_action(type_, source, with_)
  # type_: ActionType
  # source: str，文件名（不带路径）
  # with_: dict，可选，附加参数
  ```

#### Event 相关（链路/节点/事件参数快速生成）
- 新建链路创建参数
  ```python
  link_args = builder.new_link_create_args(id, endpoints, switch, static_neigh, no_arp)
  ```
- 新建链路属性
  ```python
  link_props = builder.new_link_properties(mode, bandwidth, loss, delay)
  ```
- 新建链路创建事件
  ```python
  event = builder.new_network_link_create_event(id, link_args, link_props)
  ```
- 新建链路属性设置事件
  ```python
  event = builder.new_network_link_attr_set_event(id, link_props)
  ```
- 新建链路销毁事件
  ```python
  event = builder.new_network_link_destroy_event(id)
  ```
- 新建节点执行参数
  ```python
  exec_args = builder.new_node_exec_args(key, shellcodes, daemon, output, timeout)
  ```
- 新建网络函数事件
  ```python
  event = builder.new_netfunc_event(node_name, exec_args)
  ```
- 新建网络函数执行输出事件
  ```python
  event = builder.new_netfunc_exec_output_event(node_name, exec_args)
  ```

#### 构建输出
- 生成所有目录和文件
  ```python
  builder.build()
  # 会自动生成 labbook.yaml、network/config.yaml、playbook.yaml 及 actions/ 目录等
  ```

---

### 2. 典型使用流程

```python
from labkit.builder.labbook_builder import Builder
from labkit.models.labbook import Labbook
from labkit.models.network import Node, L2Switch, Link, Image
from labkit.models.action import ActionType

builder = Builder(output_dir="my_experiment")

# 1. 设置实验元数据
labbook = Labbook.template(name="test", description="desc", author="me", tags=["tag"])
builder.set_labbook(labbook)

# 2. 添加镜像、节点、交换机、链路
image = Image(repo="ubuntu", tag="20.04")
builder.add_image(image)
node = Node(...)  # 需按 Node 定义初始化
builder.add_node(node)
switch = L2Switch(id="sw1")
builder.add_switch(switch)
link = Link(...)  # 需按 Link 定义初始化
builder.add_link(link)

# 3. 添加 playbook 时间线项
action = builder.new_action(ActionType.NETWORK_EVENTS, "init.yaml")
builder.add_timeline_item(at=0, description="初始化", action=action)

# 4. 构建输出
builder.build()
```

---

### 3. 相关子构建器

- `LabbookBuilder`：生成 labbook.yaml
- `NetworkBuilder`：生成 network/ 目录及 config.yaml
- `PlaybookBuilder`：生成 playbook.yaml 和 actions/ 目录

---

## 说明与注意事项

- 具体模型类（如 `Labbook`, `Node`, `Link`, `Image`, `Action` 等）请参考 `labkit.models` 目录下的定义。
- 所有生成的文件和目录均以 `output_dir` 为根目录自动创建。
- 添加节点、链路等时需保证引用的镜像、端点、交换机等已先添加。
- 典型流程建议：先添加镜像、节点、交换机、链路，再添加 playbook 时间线项，最后调用 `build()` 一键生成全部内容。
