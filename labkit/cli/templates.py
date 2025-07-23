LABBOOK_YAML_TMPL = '''
apiVersion: "labbook.io/v1"
kind: "Labbook"
metadata:
  name: "{name}"
  description: "A new labbook experiment."
  author: "{author}"
'''

TOPOLOGY_YAML_TMPL = '''
images:
  ubuntu:
    type: registry
    repo: ubuntu
    tag: "20.04"
nodes:
  - name: node1
    image: ubuntu:20.04
    interfaces: []
switches:
  - id: sw1
links: []
'''

PLAYBOOK_YAML_TMPL = '''
description: "Experiment playbook."
conditions: []
timeline:
  steps: []
procedures: []
'''

README_TMPL = '''# {name}

This is a Labbook experiment project initialized by labbook CLI.
''' 