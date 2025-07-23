# `network/config.yaml` 规范定义 v1.4 (最终版)

**文档目的:** 本文档为 `Labbook` 规范的一部分，旨在精确定义 `network/config.yaml` 文件的结构与字段。该文件是描述实验静态网络环境的核心。v1.4版本是经过深入讨论和反复迭代后的最终版本，它在保证功能强大的同时，追求极致的简洁、直观和逻辑严谨性。

## 1. 设计哲学

- **接口优先原则:** 接口（vnic）的能力由其 `mode` 静态地、预先地定义。接口的属性决定了链路（link）如何被创建，而非反之。
- **以用户为中心:** 规范的设计应符合研究者对网络拓扑的直观心智模型，使用易于理解、无歧义的命名，并提供熟悉的简写方式。
- **声明式与高可读性:** 使用 YAML 格式，清晰地声明网络环境的最终状态。
- **职责分离:** `images`, `nodes`, `switches`, `links` 各司其职，共同构成一个完整的网络拓扑定义。
- **可验证性:** 规范的设计应允许执行引擎在仿真开始前，对拓扑的逻辑正确性进行完整校验。

## 2. 文件结构

`config.yaml` 文件由四个可选的顶层字段组成：`images`, `nodes`, `switches`, 和 `links`。

```
# 顶层结构
images:
  # ... 镜像别名定义 ...

nodes:
  # ... 所有节点的定义 ...

switches:
  # ... 所有虚拟交换机的定义 ...

links:
  # ... 所有网络连接的定义 ...

```

## 3. 组件规范

### 3.1. `images` 对象

- **功能:** 定义实验所使用的容器镜像的别名。支持从 `registry` 或本地 `tar` 包两种来源。
- **格式:** 键为别名，值为**字符串（简写，默认从registry获取）或对象（全写）**。
    - `source` (string, 必需): `registry` 或 `tar`。
    - `path` (string, 必需): 镜像路径或本地tar文件路径。

### 3.2. `nodes` 对象

`nodes` 字段用于定义实验中所有的计算节点及其能力。

**节点属性字段:**

- `image` (string, 必需): 引用在 `images` 对象中定义的别名。
- `interfaces` (array of objects, 必需): 定义节点的网络接口列表。
    - `name` (string, 必需): 接口名称。
    - `mode` (string, 必需): 接口工作模式，必须是 `direct`, `switched`, `gateway`, `host` 之一。
    - `ip` (string or array of strings, 可选): 接口的IP地址。可以是一个单独的CIDR格式字符串，也可以是一个字符串列表以配置多个IP地址。
    - `mac` (string, 可选): 接口的MAC地址。
    - `gateway` (string, 可选): **仅当 `mode` 为 `host` 时有效且必需**。其值必须是同一个节点内另一个 `mode: gateway` 接口的 `name`。
- `resources` (object, 可选): 定义节点的计算资源限制。
- `volumes` (array, 可选): 定义需要挂载到节点内部的卷。**列表的成员可以是字符串（简写）或对象（全写）**。
    - **简写形式:** `"[源路径]:[目标路径]:[模式]"`
        - `[源路径]` 相对于 `network/files/[节点ID]/`。
        - `[目标路径]` 是容器内的绝对路径。
        - `[模式]` (可选) `ro` 或 `rw` (默认)。
    - **全写形式:**
        - `source` (string, 必需): 源路径。
        - `destination` (string, 必需): 目标路径。
        - `mode` (string, 可选): 挂载模式。

### 3.3. `switches` 列表

- **功能:** 显式定义实验中使用的所有虚拟交换机（L2广播域）。
- **结构:** 一个对象列表，每个对象代表一个交换机。
- **交换机对象字段:**
    - `id` (string, 必需): 交换机的唯一标识符。
    - `properties` (object, 可选): 定义交换机本身的属性。

### 3.4. `links` 列表

`links` 列表的结构定义不变，但其**有效性**现在受到 `interfaces` 中 `mode` 字段的严格约束。

## 4. 完整示例
```yaml
# network/config.yaml (v1.4 最终版)

images:
  nginx_img: "nginx:1.21"
  ubuntu_img: "ubuntu:22.04"

nodes:
  web-server:
    image: nginx_img
    interfaces:
      - name: eth0
        mode: switched
        # ip 字段现在可以是一个列表，以支持多IP配置
        ip:
          - "192.168.1.10/24"  # 主 IP
          - "192.168.1.11/24"  # 辅助 IP
    volumes:
      # 使用 Docker 风格的简写形式挂载配置文件 (只读)
      - "nginx.conf:/etc/nginx/nginx.conf:ro"
      # 使用简写形式挂载网站内容 (读写，模式省略)
      - "html:/usr/share/nginx/html"

  client-host:
    image: ubuntu_img
    interfaces:
      - name: eth0
        mode: switched
        ip: "192.168.1.20/24" # 也可以是单个IP
    volumes:
      # 使用全写形式挂载日志目录，更清晰
      - source: "logs"
        destination: "/var/log/app"
        mode: "rw"

switches:
  - id: office-lan

links:
  - id: link-server-to-lan
    endpoints: ["web-server:eth0", "client-host:eth0"]
    switch: "office-lan"

