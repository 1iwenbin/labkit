#!/usr/bin/env python3
"""
Command-line tool for validating Labbook YAML files
"""

import argparse
import sys
from pathlib import Path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from labkit import YAMLValidator, validate_yaml_file, validate_experiment

def main():
    parser = argparse.ArgumentParser(
        description="Validate Labbook YAML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single file (auto-detect type)
  python labkit_validate.py fixtures/network_config.yaml
  
  # Validate a specific file type
  python labkit_validate.py --type network fixtures/topology.yaml
  
  # Validate an entire experiment directory
  python labkit_validate.py --experiment fixtures/my_experiment
  
  # Validate multiple files
  python labkit_validate.py fixtures/labbook.yaml fixtures/playbook.yaml
        """
    )
    
    parser.add_argument(
        "files",
        nargs="*",
        help="YAML files to validate"
    )
    
    parser.add_argument(
        "--type",
        choices=["labbook", "network", "playbook", "auto"],
        default="auto",
        help="File type (default: auto-detect)"
    )
    
    parser.add_argument(
        "--experiment",
        help="Validate an entire experiment directory"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed validation report"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress success messages"
    )
    
    args = parser.parse_args()
    
    # Validate experiment directory
    if args.experiment:
        if not args.quiet:
            print(f"🔍 Validating experiment directory: {args.experiment}")
        
        success = validate_experiment(args.experiment)
        return 0 if success else 1
    
    # Validate individual files
    if not args.files:
        parser.error("No files specified. Use --help for usage information.")
    
    validator = YAMLValidator()
    all_success = True
    
    for file_path in args.files:
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            all_success = False
            continue
        
        if not args.quiet:
            print(f"🔍 Validating: {file_path}")
        
        # Use the validator instance directly
        if args.type == "labbook":
            success = validator.validate_labbook_yaml(file_path)
        elif args.type == "network":
            success = validator.validate_network_config_yaml(file_path)
        elif args.type == "playbook":
            success = validator.validate_playbook_yaml(file_path)
        else:
            success = validate_yaml_file(file_path, args.type)
        
        if not success:
            all_success = False
    
    # Show detailed report if requested
    if args.verbose:
        validator.print_validation_report()
    
    if not args.quiet:
        if all_success:
            print("✅ All files validated successfully!")
        else:
            print("❌ Some files failed validation")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main()) 