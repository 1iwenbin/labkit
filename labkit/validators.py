"""
YAML file validators for Labbook specification
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from pydantic import ValidationError
from .models import (
    Labbook, NetworkConfig, Playbook,
    ValidationError as LabbookValidationError
)


class YAMLValidator:
    """Validator for Labbook YAML files"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def validate_labbook_yaml(self, file_path: Union[str, Path]) -> bool:
        """Validate labbook.yaml file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.errors.append({
                    "file": str(file_path),
                    "error": "File does not exist"
                })
                return False
            
            # Load YAML content
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
            
            if yaml_content is None:
                self.errors.append({
                    "file": str(file_path),
                    "error": "YAML file is empty or invalid"
                })
                return False
            
            # Validate against Labbook model
            try:
                labbook = Labbook(**yaml_content)
                print(f"✅ labbook.yaml validation passed")
                return True
            except ValidationError as e:
                for error in e.errors():
                    self.errors.append({
                        "file": str(file_path),
                        "field": " -> ".join(str(x) for x in error["loc"]),
                        "error": error["msg"],
                        "type": error["type"]
                    })
                return False
                
        except yaml.YAMLError as e:
            self.errors.append({
                "file": str(file_path),
                "error": f"YAML parsing error: {str(e)}"
            })
            return False
        except Exception as e:
            self.errors.append({
                "file": str(file_path),
                "error": f"Unexpected error: {str(e)}"
            })
            return False
    
    def validate_network_config_yaml(self, file_path: Union[str, Path]) -> bool:
        """Validate network_config.yaml file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.errors.append({
                    "file": str(file_path),
                    "error": "File does not exist"
                })
                return False
            
            # Load YAML content
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
            
            if yaml_content is None:
                self.errors.append({
                    "file": str(file_path),
                    "error": "YAML file is empty or invalid"
                })
                return False
            
            # Validate against NetworkConfig model
            try:
                network_config = NetworkConfig(**yaml_content)
                print(f"✅ network_config.yaml validation passed")
                return True
            except ValidationError as e:
                for error in e.errors():
                    self.errors.append({
                        "file": str(file_path),
                        "field": " -> ".join(str(x) for x in error["loc"]),
                        "error": error["msg"],
                        "type": error["type"]
                    })
                return False
                
        except yaml.YAMLError as e:
            self.errors.append({
                "file": str(file_path),
                "error": f"YAML parsing error: {str(e)}"
            })
            return False
        except Exception as e:
            self.errors.append({
                "file": str(file_path),
                "error": f"Unexpected error: {str(e)}"
            })
            return False
    
    def validate_playbook_yaml(self, file_path: Union[str, Path]) -> bool:
        """Validate playbook.yaml file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.errors.append({
                    "file": str(file_path),
                    "error": "File does not exist"
                })
                return False
            
            # Load YAML content
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
            
            if yaml_content is None:
                self.errors.append({
                    "file": str(file_path),
                    "error": "YAML file is empty or invalid"
                })
                return False
            
            # Validate against Playbook model
            try:
                playbook = Playbook(**yaml_content)
                # 新增：校验 action.source 文件是否存在
                base_dir = file_path.parent
                # 检查 timeline
                timeline = yaml_content.get("timeline", [])
                if isinstance(timeline, dict):
                    steps = timeline.get("steps", [])
                else:
                    steps = timeline
                for step in steps:
                    action = step.get("action")
                    if action and "source" in action:
                        source_path = base_dir / action["source"]
                        if not Path(source_path).exists():
                            self.errors.append({
                                "file": str(file_path),
                                "field": f"timeline -> action.source: {action['source']}",
                                "error": f"Referenced action file does not exist: {source_path}"
                            })
                # 检查 procedures
                procedures = yaml_content.get("procedures", [])
                for proc in procedures:
                    for step in proc.get("steps", []):
                        action = step.get("action")
                        if action and "source" in action:
                            source_path = base_dir / action["source"]
                            if not Path(source_path).exists():
                                self.errors.append({
                                    "file": str(file_path),
                                    "field": f"procedures -> {proc.get('id', '?')} -> action.source: {action['source']}",
                                    "error": f"Referenced action file does not exist: {source_path}"
                                })
                if self.errors:
                    return False
                print(f"✅ playbook.yaml validation passed")
                return True
            except ValidationError as e:
                for error in e.errors():
                    self.errors.append({
                        "file": str(file_path),
                        "field": " -> ".join(str(x) for x in error["loc"]),
                        "error": error["msg"],
                        "type": error["type"]
                    })
                return False
                
        except yaml.YAMLError as e:
            self.errors.append({
                "file": str(file_path),
                "error": f"YAML parsing error: {str(e)}"
            })
            return False
        except Exception as e:
            self.errors.append({
                "file": str(file_path),
                "error": f"Unexpected error: {str(e)}"
            })
            return False
    
    def validate_experiment_directory(self, experiment_dir: Union[str, Path]) -> bool:
        """Validate a complete experiment directory"""
        experiment_dir = Path(experiment_dir)
        if not experiment_dir.exists():
            self.errors.append({
                "file": str(experiment_dir),
                "error": "Experiment directory does not exist"
            })
            return False
        
        success = True
        
        # Validate labbook.yaml
        labbook_file = experiment_dir / "labbook.yaml"
        if labbook_file.exists():
            if not self.validate_labbook_yaml(labbook_file):
                success = False
        else:
            self.warnings.append({
                "file": str(labbook_file),
                "warning": "labbook.yaml not found"
            })
        
        # Validate network configuration
        network_dir = experiment_dir / "network"
        if network_dir.exists():
            network_config_file = network_dir / "topology.yaml"
            if network_config_file.exists():
                if not self.validate_network_config_yaml(network_config_file):
                    success = False
            else:
                self.warnings.append({
                    "file": str(network_config_file),
                    "warning": "network/topology.yaml not found"
                })
        else:
            self.warnings.append({
                "file": str(network_dir),
                "warning": "network directory not found"
            })
        
        # Validate playbook.yaml
        playbook_file = experiment_dir / "playbook.yaml"
        if playbook_file.exists():
            if not self.validate_playbook_yaml(playbook_file):
                success = False
        else:
            self.warnings.append({
                "file": str(playbook_file),
                "warning": "playbook.yaml not found"
            })
        
        return success
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report"""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "success": len(self.errors) == 0
        }
    
    def print_validation_report(self):
        """Print formatted validation report"""
        if not self.errors and not self.warnings:
            print("🎉 All validations passed!")
            return
        
        if self.errors:
            print(f"\n❌ Validation Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  📁 {error['file']}")
                if 'field' in error:
                    print(f"     Field: {error['field']}")
                print(f"     Error: {error['error']}")
                if 'type' in error:
                    print(f"     Type: {error['type']}")
                print()
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  📁 {warning['file']}")
                print(f"     Warning: {warning['warning']}")
                print()
        
        if self.errors:
            print(f"❌ Validation failed with {len(self.errors)} errors")
        else:
            print(f"✅ Validation passed with {len(self.warnings)} warnings")


def validate_yaml_file(file_path: Union[str, Path], file_type: str = "auto") -> bool:
    """Quick validation function for a single YAML file"""
    validator = YAMLValidator()
    
    if file_type == "auto":
        file_path = Path(file_path)
        if file_path.name == "labbook.yaml":
            file_type = "labbook"
        elif file_path.name in ["topology.yaml", "network_config.yaml", "network_config_ordered.yaml"]:
            file_type = "network"
        elif file_path.name == "playbook.yaml":
            file_type = "playbook"
        else:
            print(f"❌ Cannot auto-detect file type for {file_path.name}")
            return False
    
    if file_type == "labbook":
        return validator.validate_labbook_yaml(file_path)
    elif file_type == "network":
        return validator.validate_network_config_yaml(file_path)
    elif file_type == "playbook":
        return validator.validate_playbook_yaml(file_path)
    else:
        print(f"❌ Unknown file type: {file_type}")
        return False


def validate_experiment(experiment_dir: Union[str, Path]) -> bool:
    """Quick validation function for an experiment directory"""
    validator = YAMLValidator()
    success = validator.validate_experiment_directory(experiment_dir)
    validator.print_validation_report()
    return success 