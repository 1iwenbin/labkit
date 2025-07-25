# Labkit 动态事件类型与动作类型说明

## 简介

本文件整理了 Labkit 实验环境中涉及的动态事件类型和动作类型，便于查阅和理解 Playbook 动态流程编排的核心事件与动作。

---

## 1. 网络事件类型（NetworkEventType）

定义于 `labkit/models/events.py`，用于描述实验运行过程中的网络相关动态事件：

| 枚举值                        | 说明                                   |
|-------------------------------|----------------------------------------|
| `network-link-create`         | 创建链路事件                           |
| `network-link-attr-set`       | 设置链路属性事件（如带宽、延迟、丢包等）|
| `network-link-destroy`        | 销毁链路事件                           |
| `network-node-create`         | 创建节点事件                           |
| `network-node-destroy`        | 销毁节点事件                           |
| `network-interface-create`    | 创建网络接口事件                       |
| `network-interface-destroy`   | 销毁网络接口事件                       |

---

## 2. 动作类型（ActionType）

定义于 `labkit/models/action.py`，用于 Playbook 的流程编排，描述不同类型的动态事件动作：

| 枚举值                | 说明                                         |
|-----------------------|----------------------------------------------|
| `network-events`      | 网络事件动作（如链路、节点、接口的创建/销毁/属性设置等） |
| `netfunc-events`      | 网络功能函数事件动作（如节点上执行脚本、命令等）         |
| `netfunc-exec-output` | 网络功能函数执行输出事件动作（如采集节点命令输出）       |

---

## 3. 事件的宏观分类

Labkit 网络实验环境中，事件可宏观分为三大类：

### 3.1 网络动态事件（可聚合）
- **定义**：涉及网络结构和属性的动态变更，如链路的创建/销毁、属性（带宽、延迟、丢包等）调整、节点/接口的增删等。
- **典型事件类型**：
  - 链路属性调控（如带宽、延迟、丢包率调整）
  - 链路连接关系变动（链路/节点/接口的创建与销毁）
- **聚合性**：可以将多个网络动态事件合并为一个批量事件，一次性下发和执行，提高效率。
- **对应 ActionType**：`network-events`

#### 示例代码
```python
from labkit.builder.labbook_builder import Builder

builder = Builder(output_dir="exp1")

# 构建链路属性调控和链路连接变动事件
link_args = builder.new_link_create_args(id="link1", endpoints=["node1:eth0", "node2:eth0"])
link_props = builder.new_link_properties(mode="up", bandwidth="100Mbps", delay="10ms")
event1 = builder.new_network_link_create_event(id="link1", link_create_args=link_args, link_properties=link_props)
event2 = builder.new_network_link_attr_set_event(id="link1", link_properties=link_props)

# 聚合多个事件生成 network-events 动作
action = builder.build_network_events_action([event1, event2], name="batch_network_events")
```

### 3.2 后台节点命令执行事件（可聚合）
- **定义**：在节点上后台（异步）执行的命令或脚本，通常用于环境准备、服务启动、监控等，不影响主流程的推进。
- **典型事件类型**：
  - 节点后台运行脚本（如守护进程、数据采集、环境初始化等）
- **聚合性**：可以将多个后台命令事件合并为一个批量事件，一次性下发和执行。
- **对应 ActionType**：`netfunc-events`

#### 示例代码
```python
from labkit.builder.labbook_builder import Builder

builder = Builder(output_dir="exp1")

# 构建后台节点命令事件
daemon_args1 = builder.new_node_exec_args(shellcodes=["python3 server.py"], daemon=True)
daemon_args2 = builder.new_node_exec_args(shellcodes=["tcpdump -i eth0 -w out.pcap"], daemon=True)
event1 = builder.new_netfunc_event(node_name="node1", exec_args=daemon_args1)
event2 = builder.new_netfunc_event(node_name="node2", exec_args=daemon_args2)

# 聚合多个事件生成 netfunc-events 动作
action = builder.build_netfunc_events_action([event1, event2], name="batch_daemon_events")
```

### 3.3 前台节点命令执行事件（不可聚合，只能单个执行）
- **定义**：在节点上前台（同步）执行的命令或脚本，通常用于测试步骤、关键操作，需要等待其完成后才能继续后续流程。
- **典型事件类型**：
  - 节点前台运行测试命令（如 ping、iperf、功能验证等）
- **聚合性**：**不能聚合**，每个前台命令事件需单独执行，确保流程的可控性和结果的可追溯性。
- **对应 ActionType**：`netfunc-exec-output`

#### 示例代码
```python
from labkit.builder.labbook_builder import Builder

builder = Builder(output_dir="exp1")

# 构建前台节点命令事件
exec_args = builder.new_node_exec_args(shellcodes=["ping -c 4 192.168.1.2"], daemon=False)
event = builder.new_netfunc_exec_output_event(node_name="node1", exec_args=exec_args)

# 生成单个 netfunc-exec-output 动作
action = builder.build_netfunc_exec_output_event_action(event, name="ping_test")
```

#### 总结表

| 分类   | 说明 | 是否可聚合 | 典型 ActionType |
|--------|------|------------|-----------------|
| 网络动态事件 | 网络结构/属性变更 | 可聚合 | network-events |
| 后台节点命令 | 节点异步命令 | 可聚合 | netfunc-events |
| 前台节点命令 | 节点同步命令 | 不可聚合 | netfunc-exec-output |

---

## 4. 相关数据结构

- **NetworkEvent**：统一的网络事件结构体，包含事件类型及其参数（如节点名、链路ID、接口名等）。
- **NetFuncEvent**：网络功能函数执行事件，描述节点上执行的操作。
- **NetFuncExecOutputEvent**：网络功能函数执行输出事件，描述节点上命令输出的采集。

---

## 5. 参考

- 事件类型定义：`labkit/models/events.py`
- 动作类型定义：`labkit/models/action.py`
- 事件与动作的使用：见 `labkit/builder` 相关构建器和 Playbook 生成逻辑 