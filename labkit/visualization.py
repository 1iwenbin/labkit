"""
Network Topology Visualization for Labkit
提供网络拓扑的可视化功能
"""

import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from typing import Dict, List, Optional
from .models.network import NetworkConfig, Node, Link, L2Switch


class NetworkVisualizer:
    """网络拓扑可视化器"""
    
    def __init__(self, network_config: NetworkConfig):
        self.network_config = network_config
        self.graph = self._build_graph()
    
    def _build_graph(self) -> nx.Graph:
        """构建 NetworkX 图"""
        G = nx.Graph()
        
        # 添加节点
        for node in self.network_config.nodes:
            G.add_node(node.name, type='node', image=node.image)
        
        # 添加交换机
        for switch in self.network_config.switches:
            G.add_node(switch.id, type='switch')
        
        # 添加连接
        for link in self.network_config.links:
            node1, interface1 = link.endpoints[0].split(':')
            node2, interface2 = link.endpoints[1].split(':')
            
            G.add_edge(node1, node2, 
                      interface1=interface1, 
                      interface2=interface2,
                      switch=link.switch)
        
        return G
    
    def plot_matplotlib(self, figsize: tuple = (12, 8), 
                       node_size: int = 3000,
                       font_size: int = 10) -> None:
        """使用 Matplotlib 绘制网络拓扑"""
        plt.figure(figsize=figsize)
        
        # 设置布局
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # 绘制节点
        node_colors = []
        node_labels = {}
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            if node_data.get('type') == 'switch':
                node_colors.append('lightblue')
                node_labels[node] = f"SW:{node}"
            else:
                node_colors.append('lightgreen')
                node_labels[node] = node
        
        nx.draw_networkx_nodes(self.graph, pos, 
                              node_color=node_colors,
                              node_size=node_size)
        
        # 绘制边
        nx.draw_networkx_edges(self.graph, pos, 
                              edge_color='gray',
                              width=2)
        
        # 绘制标签
        nx.draw_networkx_labels(self.graph, pos, 
                               labels=node_labels,
                               font_size=font_size)
        
        # 绘制边标签
        edge_labels = {}
        for edge in self.graph.edges():
            edge_data = self.graph.edges[edge]
            edge_labels[edge] = f"{edge_data['interface1']}-{edge_data['interface2']}"
        
        nx.draw_networkx_edge_labels(self.graph, pos, 
                                    edge_labels=edge_labels,
                                    font_size=8)
        
        plt.title("Network Topology", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def plot_plotly(self, height: int = 600) -> go.Figure:
        """使用 Plotly 绘制交互式网络拓扑"""
        # 设置布局
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # 准备节点数据
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = self.graph.nodes[node]
            if node_data.get('type') == 'switch':
                node_text.append(f"Switch: {node}")
                node_colors.append('lightblue')
            else:
                image = node_data.get('image', 'Unknown')
                node_text.append(f"{node}<br>Image: {image}")
                node_colors.append('lightgreen')
        
        # 准备边数据
        edge_x = []
        edge_y = []
        edge_text = []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            edge_data = self.graph.edges[edge]
            edge_text.append(f"{edge_data['interface1']} ↔ {edge_data['interface2']}")
        
        # 创建图形
        fig = go.Figure()
        
        # 添加边
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='gray'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        ))
        
        # 添加节点
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=30,
                color=node_colors,
                line=dict(width=2, color='black')
            ),
            showlegend=False
        ))
        
        # 更新布局
        fig.update_layout(
            title={"text": "Interactive Network Topology", "font": {"size": 16}},
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=height
        )
        
        return fig
    
    def get_network_info(self) -> Dict:
        """获取网络信息摘要"""
        return {
            'total_nodes': len(self.network_config.nodes),
            'total_switches': len(self.network_config.switches),
            'total_links': len(self.network_config.links),
            'total_images': len(self.network_config.images),
            'node_names': [node.name for node in self.network_config.nodes],
            'switch_names': [switch.id for switch in self.network_config.switches],
            'image_names': [f"{img.repo}:{img.tag}" for img in self.network_config.images]
        }


def visualize_network(network_config: NetworkConfig, 
                     method: str = 'matplotlib',
                     **kwargs) -> Optional[go.Figure]:
    """
    可视化网络拓扑
    
    Args:
        network_config: 网络配置
        method: 可视化方法 ('matplotlib' 或 'plotly')
        **kwargs: 其他参数
    
    Returns:
        Plotly 图形对象（如果使用 plotly 方法）
    """
    visualizer = NetworkVisualizer(network_config)
    
    if method.lower() == 'matplotlib':
        visualizer.plot_matplotlib(**kwargs)
        return None
    elif method.lower() == 'plotly':
        return visualizer.plot_plotly(**kwargs)
    else:
        raise ValueError(f"Unsupported visualization method: {method}")


def print_network_summary(network_config: NetworkConfig) -> None:
    """打印网络配置摘要"""
    print("🌐 网络拓扑摘要")
    print("=" * 50)
    
    print(f"\n📊 统计信息:")
    print(f"  - 节点数量: {len(network_config.nodes)}")
    print(f"  - 交换机数量: {len(network_config.switches)}")
    print(f"  - 连接数量: {len(network_config.links)}")
    print(f"  - 镜像数量: {len(network_config.images)}")
    
    print(f"\n🐳 Docker 镜像:")
    for img in network_config.images:
        print(f"  - {img.repo}:{img.tag}")
    
    print(f"\n🖥️ 网络节点:")
    for node in network_config.nodes:
        print(f"  - {node.name} ({node.image})")
        for interface in node.interfaces:
            ip_str = ", ".join(interface.ip) if interface.ip else "无IP"
            print(f"    └─ {interface.name}: {interface.mode.value} - {ip_str}")
    
    print(f"\n🔗 网络连接:")
    for link in network_config.links:
        print(f"  - {link.id}: {link.endpoints[0]} ↔ {link.endpoints[1]}")
        if link.switch:
            print(f"    通过交换机: {link.switch}") 