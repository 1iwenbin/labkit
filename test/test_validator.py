#!/usr/bin/env python3
"""
Test script for YAML file validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from labkit import YAMLValidator, validate_yaml_file, validate_experiment

def test_network_config_validation():
    """Test network_config.yaml validation"""
    print("🧪 Testing network_config.yaml validation...")
    
    # Test valid file
    success = validate_yaml_file("fixtures/network_config_ordered.yaml", "network")
    print(f"Valid file result: {success}")
    
    # Test invalid file (create one)
    create_invalid_network_config()
    success = validate_yaml_file("fixtures/invalid_network_config.yaml", "network")
    print(f"Invalid file result: {success}")
    
    print()

def test_labbook_validation():
    """Test labbook.yaml validation"""
    print("🧪 Testing labbook.yaml validation...")
    
    # Create a valid labbook.yaml
    create_valid_labbook()
    success = validate_yaml_file("fixtures/labbook.yaml", "labbook")
    print(f"Valid labbook result: {success}")
    
    # Create an invalid labbook.yaml
    create_invalid_labbook()
    success = validate_yaml_file("fixtures/invalid_labbook.yaml", "labbook")
    print(f"Invalid labbook result: {success}")
    
    print()

def test_playbook_validation():
    """Test playbook.yaml validation"""
    print("🧪 Testing playbook.yaml validation...")
    
    # Create a valid playbook.yaml
    create_valid_playbook()
    success = validate_yaml_file("fixtures/playbook.yaml", "playbook")
    print(f"Valid playbook result: {success}")
    
    # Create an invalid playbook.yaml
    create_invalid_playbook()
    success = validate_yaml_file("fixtures/invalid_playbook.yaml", "playbook")
    print(f"Invalid playbook result: {success}")
    
    print()

def test_experiment_directory_validation():
    """Test complete experiment directory validation"""
    print("🧪 Testing experiment directory validation...")
    
    # Create a valid experiment directory
    create_valid_experiment()
    success = validate_experiment("fixtures/test_experiment")
    print(f"Valid experiment result: {success}")
    
    print()

def create_invalid_network_config():
    """Create an invalid network_config.yaml for testing"""
    invalid_content = """
images:
  - type: invalid_type  # Invalid type
    repo: test
    tag: latest
nodes:
  - name: node1
    image: ubuntu:20.04
    interfaces:
      - name: eth0
        mode: invalid_mode  # Invalid mode
        ip: "not_a_list"    # Should be a list
"""
    
    with open("fixtures/invalid_network_config.yaml", "w") as f:
        f.write(invalid_content)

def create_valid_labbook():
    """Create a valid labbook.yaml"""
    valid_content = """
name: test-experiment
description: A test experiment
version: "1.0"
author: Test User
created_at: "2024-01-01T00:00:00Z"
network:
  images:
    - type: registry
      repo: library/ubuntu
      tag: "20.04"
  nodes:
    - name: test-node
      image: ubuntu:20.04
      interfaces:
        - name: eth0
          mode: host
          ip:
            - "192.168.1.10/24"
  switches: []
  links: []
playbook:
  procedures:
    - id: test-proc
      trigger_at: "10s"
      steps:
        - description: Test step
"""
    
    with open("fixtures/labbook.yaml", "w") as f:
        f.write(valid_content)

def create_invalid_labbook():
    """Create an invalid labbook.yaml"""
    invalid_content = """
name: test-experiment
# Missing required fields: description, network, playbook
version: "1.0"
"""
    
    with open("fixtures/invalid_labbook.yaml", "w") as f:
        f.write(invalid_content)

def create_valid_playbook():
    """Create a valid playbook.yaml"""
    valid_content = """
procedures:
  - id: test-procedure
    trigger_at: "10s"
    steps:
      - description: Test step
        action:
          source: test.yaml
"""
    
    with open("fixtures/playbook.yaml", "w") as f:
        f.write(valid_content)

def create_invalid_playbook():
    """Create an invalid playbook.yaml"""
    invalid_content = """
procedures:
  - id: test-procedure
    trigger_at: "invalid_time"  # Invalid time format
    steps:
      - description: Test step
        # Missing required action
"""
    
    with open("fixtures/invalid_playbook.yaml", "w") as f:
        f.write(invalid_content)

def create_valid_experiment():
    """Create a valid experiment directory structure"""
    import os
    import shutil
    
    # Create experiment directory
    os.makedirs("fixtures/test_experiment", exist_ok=True)
    os.makedirs("fixtures/test_experiment/network", exist_ok=True)
    
    # Copy valid files
    if os.path.exists("fixtures/labbook.yaml"):
        shutil.copy("fixtures/labbook.yaml", "fixtures/test_experiment/")
    if os.path.exists("fixtures/playbook.yaml"):
        shutil.copy("fixtures/playbook.yaml", "fixtures/test_experiment/")
    if os.path.exists("fixtures/network_config_ordered.yaml"):
        shutil.copy("fixtures/network_config_ordered.yaml", "fixtures/test_experiment/network/topology.yaml")

def main():
    """Run all validation tests"""
    print("🔍 YAML File Validation Tests\n")
    
    test_network_config_validation()
    test_labbook_validation()
    test_playbook_validation()
    test_experiment_directory_validation()
    
    print("✅ All validation tests completed!")

if __name__ == "__main__":
    main() 