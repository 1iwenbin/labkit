# Intent 到代码指导（Intent-to-Code Guide）

## 简介

本文件汇总了实验环境常见操作意图（Intent）与推荐 builder API 及代码示例，帮助用户和 AI 助手快速将需求转化为高效、规范的代码。

---

| 意图（Intent） | 推荐 API | 代码示例 | 说明/注意事项 |
|----------------|----------|----------|--------------|
| 创建单个节点 | `add_node` | `builder.add_node(node)` | 需先构造 Node 实例 |
| 批量添加节点 | `add_node` (循环) | `for node in nodes: builder.add_node(node)` | nodes 为 Node 实例列表 |
| 创建单条链路事件 | `new_network_link_create_event` | `event = builder.new_network_link_create_event(id="link1", endpoints=["node1:eth0", "node2:eth0"], bandwidth="100Mbps")` | 支持一步式参数，返回 NetworkEvent |
| 批量创建链路事件 | `new_network_link_create_event` (循环/聚合) | `events = [builder.new_network_link_create_event(**link) for link in links]` | links 为参数字典列表 |
| 聚合网络事件为动作 | `build_network_events_action` | `action = builder.build_network_events_action(events, name="batch_links")` | events 为 NetworkEvent 列表 |
| 节点后台运行命令 | `new_netfunc_event` | `event = builder.new_netfunc_event(node_name="node1", exec_args=builder.new_node_exec_args(shellcodes=["tcpdump ..."], daemon=True))` | daemon=True 表示后台 |
| 批量后台命令事件 | `new_netfunc_event` (循环/聚合) | `events = [builder.new_netfunc_event(node_name=n, exec_args=builder.new_node_exec_args(shellcodes=["cmd"], daemon=True)) for n in node_names]` | 适合所有节点批量操作 |
| 聚合后台命令为动作 | `build_netfunc_events_action` | `action = builder.build_netfunc_events_action(events, name="all_tcpdump")` | events 为 NetFuncEvent 列表 |
| 节点前台运行命令 | `new_netfunc_exec_output_event` | `event = builder.new_netfunc_exec_output_event(node_name="node1", exec_args=builder.new_node_exec_args(shellcodes=["ping ..."]))` | 前台命令需单独执行 |
| 前台命令生成动作 | `build_netfunc_exec_output_event_action` | `action = builder.build_netfunc_exec_output_event_action(event, name="ping_test")` | 每个前台命令单独生成动作 |

---

## 典型意图代码片段

### 1. 批量创建节点并添加到实验
```python
nodes = [Node(name=f"node{i}", ...) for i in range(3)]
for node in nodes:
    builder.add_node(node)
```

### 2. 批量创建链路并聚合为 network-events 动作
```python
links = [
    {"id": "link1", "endpoints": ["node1:eth0", "node2:eth0"], "bandwidth": "100Mbps"},
    {"id": "link2", "endpoints": ["node2:eth0", "node3:eth0"], "bandwidth": "50Mbps"},
]
events = [builder.new_network_link_create_event(**link) for link in links]
action = builder.build_network_events_action(events, name="batch_links")
```

### 3. 所有节点后台运行 tcpdump
```python
events = [
    builder.new_netfunc_event(
        node_name=node.name,
        exec_args=builder.new_node_exec_args(shellcodes=["tcpdump -i eth0 -w out.pcap"], daemon=True)
    )
    for node in nodes
]
action = builder.build_netfunc_events_action(events, name="all_tcpdump")
```

### 4. 单节点前台运行 ping 并生成动作
```python
exec_args = builder.new_node_exec_args(shellcodes=["ping -c 4 192.168.1.2"])
event = builder.new_netfunc_exec_output_event(node_name="node1", exec_args=exec_args)
action = builder.build_netfunc_exec_output_event_action(event, name="ping_test")
```

---

## 说明
- 推荐将本文件与 actions.md、README.md 配合使用，便于 AI 和用户查找最佳实践。
- 新增意图时只需补充表格和代码片段。 