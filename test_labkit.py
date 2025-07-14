#!/usr/bin/env python3
"""
Simple test for labkit SDK
"""

import sys
import os
import re
from labkit.models.base import TIME_EXPR_REGEX

# Add labkit to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'labkit'))

try:
    from labkit import (
        Labbook, Topology, Node, Interface, Switch, Link, ImageSource,
        Playbook, Timeline, Procedure, Step, Action, Condition,
        InterfaceMode, ConditionType, LabbookGenerator
    )
    print("✅ Successfully imported labkit modules")
except ImportError as e:
    print(f"❌ Failed to import labkit: {e}")
    sys.exit(1)

def test_basic_models():
    """Test basic model creation"""
    try:
        # Test ImageSource
        image = ImageSource(registry="ubuntu:20.04")
        print("✅ ImageSource created successfully")
        
        # Test Interface
        interface = Interface(name="eth0", mode=InterfaceMode.HOST, ip="192.168.1.10")
        print("✅ Interface created successfully")
        
        # Test Node
        node = Node(
            id="test-node",
            image="ubuntu",
            interfaces=[interface]
        )
        print("✅ Node created successfully")
        
        # Test Switch
        switch = Switch(id="test-switch", description="Test switch")
        print("✅ Switch created successfully")
        
        # Test Link
        link = Link(endpoints=["test-node", "test-node"], switch="test-switch")
        print("✅ Link created successfully")
        
        # Test Topology
        topology = Topology(
            images={"ubuntu": image},
            nodes=[node],
            switches=[switch],
            links=[link]
        )
        print("✅ Topology created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False

def test_playbook_models():
    """Test playbook model creation"""
    try:
        # Test Condition
        condition = Condition(
            id="test-condition",
            type=ConditionType.COMMAND,
            command="echo 'test'",
            target="test-node"
        )
        print("✅ Condition created successfully")
        
        # Test Action
        action = Action(source="events/test.yaml")
        print("✅ Action created successfully")
        
        # Test Step
        step = Step(
            description="Test step",
            action=action
        )
        print("✅ Step created successfully")
        
        # Test Procedure
        procedure = Procedure(
            id="test-procedure",
            trigger_at="10s",
            steps=[step]
        )
        print("✅ Procedure created successfully")
        
        # Test Playbook
        playbook = Playbook(
            conditions=[condition],
            procedures=[procedure]
        )
        print("✅ Playbook created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Playbook model creation failed: {e}")
        return False

def test_time_expressions():
    """Test time expression validation"""
    try:
        # Test valid expressions
        valid_expressions = ["10s", "1m30s", "2h", "40ms", "2h10m5s40ms"]
        for expr in valid_expressions:
            if not re.fullmatch(TIME_EXPR_REGEX, expr):
                print(f"❌ Valid time expression failed: {expr}")
                return False
            print(f"✅ Valid time expression: {expr}")
        
        # Test invalid expressions
        invalid_expressions = ["10", "1.5s", "invalid", "h", "0"]
        for expr in invalid_expressions:
            if re.fullmatch(TIME_EXPR_REGEX, expr):
                print(f"❌ Invalid expression should have failed: {expr}")
                return False
            print(f"✅ Correctly rejected invalid expression: {expr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Time expression test failed: {e}")
        return False

def test_labbook_creation():
    """Test complete labbook creation"""
    try:
        # Create minimal topology
        topology = Topology(
            images={"ubuntu": ImageSource(registry="ubuntu:20.04")},
            nodes=[
                Node(
                    id="test-node",
                    image="ubuntu",
                    interfaces=[Interface(name="eth0", mode=InterfaceMode.HOST)]
                )
            ],
            switches=[],
            links=[]
        )
        
        # Create minimal playbook
        playbook = Playbook(
            procedures=[
                Procedure(
                    id="test-proc",
                    trigger_at="10s",
                    steps=[Step(description="Test")]
                )
            ]
        )
        
        # Create labbook
        labbook = Labbook(
            name="test-experiment",
            description="Test experiment",
            topology=topology,
            playbook=playbook
        )
        
        print("✅ Complete labbook created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Labbook creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running labkit tests...\n")
    
    tests = [
        ("Basic Models", test_basic_models),
        ("Playbook Models", test_playbook_models),
        ("Time Expressions", test_time_expressions),
        ("Complete Labbook", test_labbook_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 