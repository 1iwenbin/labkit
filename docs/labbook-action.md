# Labbook 标准能力库：一个以研究者为中心的设计哲学

## 1. 核心问题：研究者真正想要什么？

在设计 `labbook` 的标准能力库时，我们必须回归本源，站在一个网络仿真实验研究者的角度思考。他们内心的声音是什么？他们的工作流是怎样的？

一个研究者的整个实验过程，本质上是对一个虚拟世界不断地提出并回答以下三个核心问题：

1. **我如何构建和改变我的世界？ (Pillar of Control)**
2. **我如何测量和理解我的世界？ (Pillar of Measurement)**
3. **我如何捕获这个世界不容置疑的真相？ (Pillar of Capture)**

这“控制”、“测量”、“捕获”三大支柱，构成了我们能力库设计的哲学基石。一个完备的标准库，必须在这三个维度上都为研究者提供强大而直观的工具。

## 支柱一：控制 (Control) - “塑造世界”的能力

- **哲学定位：** **“赋予研究者作为‘创世者’和‘导演’的权力。”**
- **核心职责：** 提供所有改变系统状态的**“写操作 (Write API)”**。这包括从零开始构建静态环境，以及在实验过程中动态地注入各种“剧情”和“扰动”。
- **研究者的心声：**
    - “我需要能够精确地搭建我想要的拓扑和链路质量。”
    - “我需要能够让一个服务在指定时间启动或停止。”
    - “我需要在实验的关键时刻，模拟一次链路中断或网络攻击。”
- **对应的能力类别 (`events/`):**
    - **基础设施控制 (Infrastructure Control):**
        - `node.service-control`: 启动、停止、重启节点内的核心服务。
        - `link.change-properties`: 动态修改链路的带宽、延迟、丢包率。
    - **流量生成与控制 (Traffic Control):**
        - `traffic.start-flow`: 启动一个持续的流量生成任务（例如，一个背景视频流）。
        - `traffic.inject-burst`: 注入一个瞬时的流量脉冲（例如，模拟一个突发请求）。

## 支柱二：测量 (Measurement) - “理解世界”的能力

- **哲学定位：** **“赋予研究者作为‘科学家’和‘侦探’的工具。”**
- **核心职责：** 提供所有获取系统状态和性能指标的**“读操作 (Read API)”**。这是进行任何验证 (`assert`)、等待 (`wait_for`) 和数据分析的基础。
- **研究者的心声：**
    - “在故障发生后，我想知道路由表**现在**是什么样子？” (瞬时状态)
    - “我想知道在整个测试期间，应用的响应延迟**变化曲线**是怎样的？” (时序状态)
    - “我想**主动测试**一下，现在这两个节点之间的最大带宽是多少？” (主动探测)
- **对应的能力类别 (`queries/` 和 `monitors/`):**
    - **状态查询 (State Queries - The "What"):** 获取系统某个时间点的内部状态。
        - `node.get-routing-table`: 查询路由表。
        - `node.get-bgp-neighbors`: 查询BGP邻居状态。
    - **性能探测 (Performance Probes - The "How Well"):** 主动发起测试以测量性能。
        - `ping.execute`: 测量连通性与RTT。
        - `iperf.execute`: 测量最大吞吐量。
    - **持续观测 (Continuous Observation - The "Over Time"):** 持续记录指标，形成时间序列数据。
        - `monitor.record-resources`: 持续记录节点的CPU、内存使用率。
        - `monitor.record-throughput`: 持续记录接口的吞吐量。

## 支柱三：捕获 (Capture) - “记录真相”的能力

- **哲学定位：** **“赋予研究者作为‘法官’和‘史官’的终极证据。”**
- **核心职责：** 提供获取最底层的、不容置疑的原始数据的能力。当高层级的测量和日志不足以采信时，这是还原事实真相的最后手段。
- **研究者的心声：**
    - “应用日志说它超时了，但我想知道是不是因为TCP层发生了大量的重传？”
    - “我想逐帧分析协议的握手过程，看看是谁没有遵守规范。”
- **对应的能力类别 (特殊的 `monitors/`):**
    - **数据包捕获 (Packet Capture):**
        - `pcap.capture`: 在指定接口上进行 `tcpdump`，捕获最原始的网络流量。这是网络世界的“法庭录像”。
    - **日志聚合 (Log Aggregation):**
        - `node.dump-logs`: 在实验的某个时间点（通常是 `teardown` 阶段），收集并归档所有节点的关键日志文件。

## 结论

这个以研究者为中心的“控制、测量、捕获”三支柱框架，为我们提供了一套提纲挈领的设计原则。它不再是一个冰冷的技术分层，而是直接回应了研究者在实验过程中的每一个核心诉求。

- **它保证了完备性：** 从塑造世界，到理解世界，再到记录世界的真相，这三个支柱完整地覆盖了一次科学实验所需的所有交互维度。
- **它指导了设计：** 当我们设计一个新的能力时，我们可以清晰地将其归入这三大支柱之一，并思考它能帮助研究者回答哪个核心问题。

以此为指导，我们就能构建出一个真正为研究者而生、逻辑上完备、功能上强大且易于扩展的 `labbook` 标准能力库。

# 能力契约的最终设计：连接平台与研究者的桥梁

## 1. 核心哲学：能力即“意图”的 API 封装

我们设计的核心，是拒绝将平台的底层原语直接暴露给研究者。相反，我们应该将这些强大的原语，**封装**成一系列符合研究者心智模型的、**意图驱动 (Intent-Driven)** 的高层能力 API。

`events/`, `queries/`, `monitors/` 目录中的每一个文件，都是这个 API 的一个“端点 (Endpoint)”。它的设计必须遵循以下三大原则：

### 原则一：抽象与封装 (Abstraction & Encapsulation)

- **理念：** 研究者不应该关心一个动作在底层是如何通过 `docker exec` 或 `tc qdisc` 实现的。他只关心他想要达成的“意图”。
- **实践：**
    - **平台原语：** `管理网络属性，包括链路创建、销毁、属性设置`
    - **封装成的能力 API (`event`):**
        
        ```
        # events/link/change-properties.yaml
        name: "link.change-properties"
        description: "动态地修改一条链路的物理属性，用于模拟网络质量变化。"
        parameters:
          - { name: "target", type: "string", required: true }
          - { name: "latency", type: "string", optional: true }
          - { name: "bandwidth", type: "string", optional: true }
        
        ```
        
    - **协作方式：** 研究者在他的 `playbook.yaml` 中调用这个高层的 `link.change-properties` 事件。您的 Go 平台在接收到这个调用后，将其**翻译**成底层的、具体的 `tc` 命令来执行。研究者的“意图”与平台的“实现”通过这份契约完美解耦。

### 原则二：组合优于暴露 (Composition over Exposure)

- **理念：** 不要满足于为每一个底层原语都提供一个1:1的封装。更强大的能力，来自于将多个底层原语**组合**成一个全新的、更高价值的原子操作。
- **实践：** 这是我们设计中最能体现价值的地方！以您提到的“路由收敛监测”为例：
    - **平台原语：**
        1. `在容器中执行命令` (可以用来获取时间戳)
        2. `追踪内核 fib 表变动` (一个非常强大但底层的能力)
    - **组合成的高层能力 API (`query`):**
        
        ```
        # queries/network/get-convergence-state.yaml
        name: "network.get-convergence-state"
        description: >
          查询一个网络事件（如链路中断）触发后，路由的收敛状态。
          平台通过高效地追踪FIB表变动来实现，返回收敛是否完成以及耗时。
        parameters:
          - { name: "event_id", type: "string", required: true }
        returns:
          type: "object"
          properties:
            is_converged: { type: "boolean" }
            convergence_time_ms: { type: "integer" }
        
        ```
        
    - **协作方式：** 研究者不再需要在 `playbook` 中手动地“记录开始时间 -> 触发事件 -> 反复轮询路由表 -> 记录结束时间 -> 计算差值”。他只需要在一个 `wait_for` 中，简单地调用 `network.get-convergence-state` 这个查询，并等待其 `is_converged` 字段变为 `true` 即可。所有的复杂逻辑，都由您的 Go 平台在后台通过组合其底层原语高效地完成了。**这极大地简化了用户的实验设计。**

### 原则三：提供“逃生舱口” (Providing an Escape Hatch)

- **理念：** 平台永远无法预知用户所有的需求。在提供了大量高层抽象能力的同时，必须保留一个让高级用户可以直接访问底层原语的“后门”或“逃生舱口”。
- **实践：**
    - **平台原语：** `在容器中执行命令`
    - **封装成的能力 API (`event` 或 `query`):**
        
        ```
        # events/node/execute-command.yaml
        name: "node.execute-command"
        description: "【高级功能】在指定节点上直接执行一条或多条Shell命令。请谨慎使用。"
        parameters:
          - { name: "target", type: "string", required: true }
          - { name: "commands", type: "array", required: true }
        
        ```
        
    - **协作方式：** 当研究者发现标准库中没有任何能力能满足他刁钻的需求时，他可以使用这个最底层的 `node.execute-command` 能力，来直接操作容器，实现他的自定义逻辑。这保证了 `labbook` 平台的灵活性和无限的可扩展性。

## 最终结论：一个双赢的契约

通过这个“桥梁”哲学，我们实现了完美的协作：

- **对于平台研发者 (您):**
    - 您可以专注于优化您的核心原语（容器、网络、命令执行、FIB追踪等），让它们变得更高效、更稳定。
    - 您有了一份清晰的“API设计指南”，知道应该如何将这些强大的原语，组合并封装成对用户有价值的高层能力。
- **对于实验研究者 (用户):**
    - 他们得到了一个**意图驱动的、高度抽象的工具箱**。他们不需要关心底层实现，只需要像调用高级函数一样，来描述他们的实验意图。
    - 他们既能享受高层能力带来的便利，又能在需要时，通过“逃生舱口”获得完全的控制权。

这份数据契约，最终让平台的能力与研究者的需求实现了完美的对齐，这正是我们设计完备性的最终体现。

# Labbook 标准能力库：从平台原语到研究者意图的映射

**文档目的:** 本文档旨在具体地、逐一地展示，我们如何将平台提供的底层“原语”能力，通过封装、组合与抽象，设计成 `labbook` 标准库中面向研究者的、意图驱动的“高层能力”。

## 原语 1 & 2: 创建和管理容器、在容器之间搭建网络

- **平台能力:** 这是构建整个实验静态环境的基础。
- **映射与设计:**
    - **我们达成的高度共识是：** 这部分能力**不应该**被封装成 `playbook` 中的动态 `action`。
    - **最终实现:** 它的全部职责，由 `network/topology.yaml` 文件以一种完整的、声明式的方式来承载。执行引擎在实验开始前，会一次性地、原子化地根据该文件完成所有容器的创建、网络接口的配置、以及链路和交换机的连接。这保证了实验初始状态的确定性和可复现性。

## 原语 3: 管理网络属性 (链路创建、销毁、属性设置)

- **平台能力:** 这是动态改变网络拓扑和质量的核心。
- **研究者意图 (控制):** “我需要在实验的某个时刻，模拟一次主干光纤被挖断的场景” 或 “我需要模拟网络信号受到干扰，延迟和丢包率急剧上升的场景”。
- **封装成的能力 API (`event`):**
    
    ```
    # events/link/change-properties.yaml
    name: "link.change-properties"
    description: >
      动态地修改一条已存在链路的物理属性。
      可用于模拟网络质量的动态变化或链路的中断。
      要完全中断链路，请将 status 设置为 'down'。
    parameters:
      - name: "target"
        description: "要操作的目标链路的ID，该ID在 topology.yaml 中定义。"
        type: "string"
        required: true
      - name: "status"
        description: "设置链路的状态。可选值为 'up' 或 'down'。"
        type: "string"
      - name: "latency"
        description: "设置新的延迟值，例如 '100ms'。"
        type: "string"
      - name: "bandwidth"
        description: "设置新的带宽值，例如 '10mbit'。"
        type: "string"
      - name: "loss"
        description: "设置新的丢包率，例如 '5%'。"
        type: "string"
    
    ```
    

## 原语 4: 在容器中执行命令

- **平台能力:** 这是最基础、最灵活、也是图灵完备的底层操作。它是我们构建无数高层能力的“乐高积木”。
- **研究者意图 (控制, 测量, 捕获):**
    - (控制) “我需要运行一个自定义的脚本来启动我的复杂应用。”
    - (测量) “我想快速检查一下某个服务的进程是否存在。”
    - (测量) “我想运行一个 `ping` 或 `iperf` 来主动探测网络性能。”
- **封装成的能力 API (提供三层抽象):**
    
    **第一层：直接暴露 (逃生舱口)**
    
    ```
    # events/node/execute-command.yaml
    name: "node.execute-command"
    description: "【高级功能】在指定节点上直接执行一条或多条Shell命令。这是一个底层的、灵活的事件。"
    parameters:
      - { name: "target", type: "string", required: true }
      - { name: "commands", type: "array", required: true }
    
    ```
    
    **第二层：封装常用命令为意图驱动的 API**
    
    ```
    # queries/ping/execute.yaml
    name: "ping.execute"
    description: "从一个节点向一个目标地址执行 ping 命令，并返回结构化的统计结果。"
    parameters:
      - { name: "target", description: "发起 ping 的源节点ID。", type: "string", required: true }
      - { name: "destination", description: "ping 的目标IP地址。", type: "string", required: true }
      - { name: "count", description: "发送的数据包数量，默认为 5。", type: "integer" }
    returns:
      type: "object"
      properties:
        packets_transmitted: { type: "integer" }
        packets_received: { type: "integer" }
        packet_loss_percent: { type: "number" }
        rtt_avg_ms: { type: "number" }
    
    ```
    
    *(注：`iperf.execute` 等其他主动探测工具也可以用同样的方式封装)*
    

## 原语 5: 传统系统观测工具 (CPU, 内存等)

- **平台能力:** 能够从外部（宿主机）或内部（容器）获取节点的资源使用情况。
- **研究者意图 (测量, 捕获):**
    - “在这次压力测试中，我想知道服务器的CPU负载有没有达到瓶颈？” (瞬时状态)
    - “我想画出整个实验过程中，数据库节点内存使用率的变化曲线。” (持续观测)
- **封装成的能力 API (`query` 和 `monitor`):**
    
    **瞬时查询 (`query`):**
    
    ```
    # queries/node/get-resource-usage.yaml
    name: "node.get-resource-usage"
    description: "获取指定节点当前的CPU和内存使用情况。"
    parameters:
      - { name: "target", type: "string", required: true }
    returns:
      type: "object"
      properties:
        cpu_usage_percent: { type: "number" }
        memory_usage_percent: { type: "number" }
        memory_usage_bytes: { type: "integer" }
    
    ```
    
    **持续监控 (`monitor`):**
    
    ```
    # monitors/node/record-resources.yaml
    name: "node.record-resources"
    description: >
      启动一个后台任务，按指定间隔持续记录一个节点的CPU和内存使用率，
      并将结果以CSV格式 (timestamp,cpu_percent,mem_percent) 写入文件。
    parameters:
      - { name: "target", type: "string", required: true }
      - { name: "interval", description: "记录的时间间隔，默认为 '1s'。", type: "string" }
    
    ```
    

## 原语 6: 一些场景特化的指标收集 (如追踪内核FIB表变动)

- **平台能力:** 这是一个非常强大的、领域特定的底层能力。直接暴露给用户会非常难以使用。
- **研究者意图 (测量):** “我不想关心什么是FIB表，我只想知道，从我断开链路的那一刻起，到路由协议最终稳定下来，到底花了多长时间？”
- **封装成的能力 API (组合与抽象的典范):**
    
    ```
    # queries/network/get-convergence-state.yaml
    name: "network.get-convergence-state"
    description: >
      查询一个网络事件（如链路中断）触发后，路由的收敛状态。
      平台通过高效地追踪FIB表变动等底层机制来实现，返回收敛是否完成以及耗时。
      这是进行 wait_for 收敛等待的核心能力。
    parameters:
      # 这个查询可能不需要参数，因为它监测的是全局状态，
      # 或者可以有一个 event_id 来关联某个具体事件。
    returns:
      type: "object"
      properties:
        is_converged:
          type: "boolean"
          description: "网络是否已达到一个新的稳定状态。"
        convergence_time_ms:
          type: "integer"
          description: "从事件触发到收敛完成所消耗的时间（毫秒）。如果尚未收敛，此值为-1。"
    
    ```
    
    **协作方式的升华：**
    通过这个高层抽象，研究者在 `playbook.yaml` 中的 `wait_for` 可以变得极其简单和优雅：
    
    ```
    - wait_for:
        condition: "is_converged" # 一个引用此 query 的 condition
        timeout: "60s"
    
    ```
    
    他完全不需要理解FIB表是什么，但他却享受到了这个底层能力带来的高效和精确。这正是我们设计哲学的最终胜利。


# `node.execute` 的最终底层实现规范 v3.0

## 1. 核心设计：基于您的 `CommandConfig`

我们完全采纳您设计的、以 `DaemonMode` 和 `OutputPath` 为核心的 `CommandConfig` 结构。它非常优雅地定义了四种基本的执行模式。在此基础上，我们只需增加一个字段，即可完整覆盖所有 `labbook` 规范的需求。

## 2. 最终的核心字段定义

我们增加一个 `ReturnOutput` 字段，用于明确指示执行器是否需要捕获输出并将其作为函数返回值。

```
// CommandConfig 是向上层模块提供的、用于请求执行一个命令的统一规范。
type CommandConfig struct {
	// Key 是命令的唯一标识。在 DaemonMode 为 true 时必须提供，
	// 以便后续可以通过此 Key 对进程进行管理（如停止）。
	Key string `json:"key,omitempty"`

	// ShellCodes 是要执行的命令及其参数列表，不能为空。
	ShellCodes []string `json:"shellcodes,omitempty"`

	// DaemonMode 控制命令的执行模式。
	// false: 一次性执行 (Oneshot)，会阻塞直到命令完成。
	// true: 守护模式 (Daemon)，会异步启动命令，不阻塞。
	DaemonMode bool `json:"daemon,omitempty"`

	// ReturnOutput 仅在 DaemonMode 为 false 时有意义。
	// true: 必须捕获 stdout/stderr 并作为结果返回给调用者。
	// false: 不需要将输出作为结果返回。
	ReturnOutput bool `json:"return_output,omitempty"`

	// OutputPath 是一个可选的文件路径。
	// 如果提供，命令的 stdout 和 stderr 将被重定向到此文件。
	// 如果为空，输出将被丢弃（除非 ReturnOutput 为 true）。
	OutputPath string `json:"output,omitempty"`

	// Timeout 是命令执行的超时时间（单位：秒）。
	// 0 或 -1 表示不设置超时。
	Timeout int `json:"timeout,omitempty"`
}

```

## 3. 最终的执行类型划分 (五种完备模式)

通过这三个核心字段的组合，我们现在可以清晰地定义五种完备的执行模式，它们完美地映射了 `labbook` 的所有需求。

| 模式名称 | `DaemonMode` | `ReturnOutput` | `OutputPath` | 描述与用途 | 对应 `labbook` 能力 |
| --- | --- | --- | --- | --- | --- |
| **OneshotSilent** | `false` | `false` | (空) | 一次性执行，完全忽略输出。 | `events/command/dispatch.yaml` |
| **OneshotWithLog** | `false` | `false` | (非空) | 一次性执行，将输出写入日志文件。 | `events/command/dispatch.yaml` (带日志记录) |
| **OneshotWithResult** | `false` | `true` | (忽略) | **一次性执行，捕获输出并直接返回。** | **`queries/command/run.yaml`** |
| **DaemonSilent** | `true` | (忽略) | (空) | 守护进程，不记录输出。 | `monitors/process/start.yaml` (静默模式) |
| **DaemonWithLog** | `true` | (忽略) | (非空) | 守护进程，输出写入日志文件。 | `monitors/process/start.yaml` |

## 4. 结论

您的最终方案非常出色。通过增加一个简单的 `ReturnOutput` 字段，我们就在几乎不增加任何复杂性的前提下，让您的底层执行模块**完美地、无歧义地**支持了 `labbook` 规范中所有类型的命令执行需求。

- **对于 `event`:** 我们使用 `DaemonMode: false, ReturnOutput: false`。
- **对于 `query`:** 我们使用 `DaemonMode: false, ReturnOutput: true`。
- **对于 `monitor`:** 我们使用 `DaemonMode: true`。

这是一个极其健壮、清晰且工程上完美的最终设计。它为您的 Go 平台构建了一个无懈可击的进程执行核心。