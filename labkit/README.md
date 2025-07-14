# Labkit - Python SDK for Labbook Experiments

Labkit is a Python SDK for creating and managing Labbook network experiment specifications. It implements the three-layer architecture model with focus on usability and flexibility.

## Features

- **Type-safe experiment definition** using Pydantic models
- **Strict validation** ensuring data contract compliance
- **Time expression support** (e.g., "10s", "1m30s", "2h", "40ms")
- **Fluent API** for building complex experiments
- **YAML generation** for downstream execution engines

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from labkit import (
    Labbook, Topology, Node, Interface, Switch, Link, ImageSource,
    Playbook, Timeline, Procedure, Step, Action, Condition,
    InterfaceMode, ConditionType, LabbookGenerator
)

# Create a simple network topology
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
        )
    ],
    switches=[
        Switch(id="lan1", description="Client LAN")
    ],
    links=[
        Link(endpoints=["client-1", "router-1"], switch="lan1")
    ]
)

# Create experiment playbook
playbook = Playbook(
    conditions=[
        Condition(
            id="network_ready",
            type=ConditionType.COMMAND,
            command="ping -c 1 8.8.8.8",
            target="client-1"
        )
    ],
    procedures=[
        Procedure(
            id="connectivity_test",
            trigger_at="10s",
            steps=[
                Step(
                    description="Wait for network to be ready",
                    wait_for="network_ready"
                ),
                Step(
                    description="Test connectivity",
                    action=Action(source="queries/test_connectivity.yaml")
                )
            ]
        )
    ]
)

# Create complete experiment
labbook = Labbook(
    name="simple_test",
    description="A simple connectivity test",
    topology=topology,
    playbook=playbook
)

# Generate experiment directory
generator = LabbookGenerator(output_dir="./experiments")
experiment_dir = generator.generate(labbook)
```

## Core Concepts

### 1. Three-Layer Architecture

- **Upstream (Python SDK)**: Focuses on usability and flexibility
- **Midstream (Data Contract)**: Pure, unambiguous specification
- **Downstream (Go Engine)**: Simple and robust execution

### 2. Network Topology

Define static network environment with:
- **Images**: Docker image sources
- **Nodes**: Compute nodes with interfaces
- **Switches**: L2 broadcast domains
- **Links**: Logical communication paths

### 3. Dynamic Flow

Define experiment execution with:
- **Conditions**: Reusable condition definitions
- **Timeline**: Background asynchronous events
- **Procedures**: Synchronous test sequences

### 4. Capabilities

Self-contained task definitions:
- **Events**: One-time actions
- **Queries**: Information retrieval with assertions
- **Monitors**: Continuous monitoring

## API Reference

### Topology Models

- `Topology`: Complete network topology
- `Node`: Compute node definition
- `Interface`: Network interface with mode
- `Switch`: Virtual switch (L2 domain)
- `Link`: Logical communication path
- `ImageSource`: Docker image source

### Playbook Models

- `Playbook`: Complete experiment flow
- `Timeline`: Background event timeline
- `Procedure`: Synchronous test sequence
- `Step`: Individual execution step
- `Condition`: Reusable condition
- `Action`: Capability execution

### Capability Models

- `Event`: One-time action capability
- `Query`: Information retrieval capability
- `Monitor`: Continuous monitoring capability
- `Assertion`: Result validation

### Interface Modes

- `DIRECT`: Direct point-to-point connection
- `SWITCHED`: Switch-based connection
- `GATEWAY`: Gateway/router interface
- `HOST`: Host/client interface

### Condition Types

- `DECLARATIVE`: Platform-provided efficient checks
- `COMMAND`: User-provided script execution

## Validation

The SDK provides strict validation ensuring:

- **Data integrity**: All required fields are present
- **Cross-field validation**: Links reference valid nodes/switches
- **Time expressions**: Valid time format (e.g., "10s", "1m30s")
- **Interface compatibility**: Links match interface modes
- **Condition references**: All referenced conditions exist

## Error Handling

The SDK uses strict error handling:

- **ValidationError**: Custom exception for validation failures
- **Immediate rejection**: Invalid data is rejected immediately
- **Detailed messages**: Clear error descriptions with context

## Examples

See `example.py` for a complete working example.

## Contributing

This SDK implements the Labbook specification defined in `docs/labbook.md`. Any changes should maintain compatibility with the three-layer architecture model. 