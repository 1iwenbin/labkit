#!/usr/bin/env python3
"""
Example usage of labkit SDK for creating a Labbook experiment
"""

from labkit import (
    Labbook, Topology, Node, Interface, Switch, Link, ImageSource,
    Playbook, Timeline, Procedure, Step, Action, Condition,
    InterfaceMode, ConditionType, LabbookGenerator
)


def create_simple_experiment():
    """Create a simple network experiment"""
    
    # 1. Define network topology
    topology = Topology(
        images={
            "ubuntu": ImageSource(registry="ubuntu:20.04"),
            "router": ImageSource(registry="frrouting/frr:latest")
        },
        nodes=[
            Node(
                id="client-1",
                image="ubuntu",
                interfaces=[
                    Interface(name="eth0", mode=InterfaceMode.HOST, ip="192.168.1.10")
                ]
            ),
            Node(
                id="router-1", 
                image="router",
                interfaces=[
                    Interface(name="eth0", mode=InterfaceMode.GATEWAY, ip="192.168.1.1"),
                    Interface(name="eth1", mode=InterfaceMode.GATEWAY, ip="10.0.0.1")
                ]
            ),
            Node(
                id="server-1",
                image="ubuntu", 
                interfaces=[
                    Interface(name="eth0", mode=InterfaceMode.HOST, ip="10.0.0.10")
                ]
            )
        ],
        switches=[
            Switch(id="lan1", description="Client LAN"),
            Switch(id="lan2", description="Server LAN")
        ],
        links=[
            Link(endpoints=["client-1", "router-1"], switch="lan1"),
            Link(endpoints=["router-1", "server-1"], switch="lan2")
        ]
    )
    
    # 2. Define conditions
    conditions = [
        Condition(
            id="network_ready",
            type=ConditionType.COMMAND,
            command="ping -c 1 8.8.8.8",
            target="client-1"
        )
    ]
    
    # 3. Define timeline (background events)
    timeline = Timeline(steps=[
        Step(
            at="5s",
            description="Start background traffic",
            action=Action(source="events/start_background_traffic.yaml")
        )
    ])
    
    # 4. Define procedures (test sequences)
    procedures = [
        Procedure(
            id="connectivity_test",
            trigger_at="10s",
            steps=[
                Step(
                    description="Wait for network to be ready",
                    wait_for="network_ready"
                ),
                Step(
                    description="Test client to server connectivity",
                    action=Action(source="queries/test_connectivity.yaml")
                )
            ]
        )
    ]
    
    # 5. Create playbook
    playbook = Playbook(
        conditions=conditions,
        timeline=timeline,
        procedures=procedures
    )
    
    # 6. Create complete labbook
    labbook = Labbook(
        name="simple_connectivity_test",
        description="A simple network connectivity test between client and server",
        author="Labkit SDK",
        topology=topology,
        playbook=playbook
    )
    
    return labbook


def main():
    """Main function to demonstrate labkit usage"""
    
    # Create experiment
    labbook = create_simple_experiment()
    
    # Generate experiment directory
    generator = LabbookGenerator(output_dir="./experiments")
    experiment_dir = generator.generate(labbook)
    
    print(f"Experiment generated at: {experiment_dir}")
    print("Experiment structure:")
    print(f"  - {experiment_dir}/labbook.yaml")
    print(f"  - {experiment_dir}/network/topology.yaml")
    print(f"  - {experiment_dir}/playbook.yaml")
    print(f"  - {experiment_dir}/events/")
    print(f"  - {experiment_dir}/queries/")
    print(f"  - {experiment_dir}/monitors/")


if __name__ == "__main__":
    main() 