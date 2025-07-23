import typer
from pathlib import Path
from rich import print
from enum import Enum
from typing import List, Dict, Any
import yaml

app = typer.Typer()

class ValidationLevel(str, Enum):
    BASIC = "basic"
    FORMAT = "format"
    FULL = "full"

class ValidationResult:
    def __init__(self, level: str, message: str, severity: str = "ERROR"):
        self.level = level
        self.message = message
        self.severity = severity  # ERROR, WARNING, INFO

class BaseValidator:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.results: List[ValidationResult] = []
        self.fixes_applied: List[str] = []
    
    def add_error(self, message: str):
        self.results.append(ValidationResult("ERROR", message, "ERROR"))
    
    def add_warning(self, message: str):
        self.results.append(ValidationResult("WARNING", message, "WARNING"))
    
    def add_info(self, message: str):
        self.results.append(ValidationResult("INFO", message, "INFO"))
    
    def add_fix(self, message: str):
        self.fixes_applied.append(message)
    
    def validate(self, level: ValidationLevel) -> List[ValidationResult]:
        """子类需要重写此方法"""
        raise NotImplementedError
    
    def fix(self, level: ValidationLevel) -> List[str]:
        """子类需要重写此方法，返回修复的列表"""
        return []

class ProjectStructureValidator(BaseValidator):
    def validate(self, level: ValidationLevel) -> List[ValidationResult]:
        self.results.clear()
        
        # 检查项目目录是否存在
        if not self.project_path.exists():
            self.add_error(f"项目目录不存在: {self.project_path}")
            return self.results
        
        # 检查核心文件
        core_files = [
            self.project_path / "labbook.yaml",
            self.project_path / "network" / "config.yaml",
            self.project_path / "playbook.yaml"
        ]
        
        for file_path in core_files:
            if not file_path.exists():
                self.add_error(f"缺少核心文件: {file_path}")
        
        # 检查目录结构
        required_dirs = [
            self.project_path / "network",
            self.project_path / "events",
            self.project_path / "queries",
            self.project_path / "monitors",
            self.project_path / "scripts"
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                self.add_warning(f"缺少目录: {dir_path}")
        
        return self.results
    
    def fix(self, level: ValidationLevel) -> List[str]:
        """自动修复项目结构问题"""
        fixes = []
        
        # 创建缺失的目录
        required_dirs = [
            self.project_path / "network",
            self.project_path / "events",
            self.project_path / "queries",
            self.project_path / "monitors",
            self.project_path / "scripts"
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    fixes.append(f"创建目录: {dir_path}")
                except Exception as e:
                    self.add_error(f"无法创建目录 {dir_path}: {e}")
        
        return fixes

class YAMLFormatValidator(BaseValidator):
    def validate(self, level: ValidationLevel) -> List[ValidationResult]:
        self.results.clear()
        
        if level == ValidationLevel.BASIC:
            return self.results
        
        # 检查 YAML 文件格式
        yaml_files = [
            ("labbook.yaml", self.project_path / "labbook.yaml"),
            ("config.yaml", self.project_path / "network" / "config.yaml"),
            ("playbook.yaml", self.project_path / "playbook.yaml")
        ]
        
        for name, file_path in yaml_files:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                except yaml.YAMLError as e:
                    self.add_error(f"{name} YAML 格式错误: {e}")
                except Exception as e:
                    self.add_error(f"{name} 读取失败: {e}")
        
        return self.results
    
    def fix(self, level: ValidationLevel) -> List[str]:
        """自动修复 YAML 格式问题"""
        fixes = []
        
        if level == ValidationLevel.BASIC:
            return fixes
        
        # 尝试修复常见的 YAML 格式问题
        yaml_files = [
            ("labbook.yaml", self.project_path / "labbook.yaml"),
            ("config.yaml", self.project_path / "network" / "config.yaml"),
            ("playbook.yaml", self.project_path / "playbook.yaml")
        ]
        
        for name, file_path in yaml_files:
            if file_path.exists():
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 尝试修复常见的格式问题
                    fixed_content = self._fix_yaml_content(content)
                    
                    if fixed_content != content:
                        # 写回修复后的内容
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        fixes.append(f"修复 {name} 格式问题")
                        
                except Exception as e:
                    self.add_error(f"修复 {name} 失败: {e}")
        
        return fixes
    
    def _fix_yaml_content(self, content: str) -> str:
        """修复常见的 YAML 格式问题"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 修复缩进问题（将 tab 替换为空格）
            if '\t' in line:
                line = line.replace('\t', '  ')
            
            # 修复行尾空格
            line = line.rstrip()
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

class ContentLogicValidator(BaseValidator):
    def __init__(self, project_path: Path):
        super().__init__(project_path)
        # 在初始化时导入 models，避免在方法中重复导入
        try:
            from labkit.models import Labbook, NetworkConfig, Playbook
            self.Labbook = Labbook
            self.NetworkConfig = NetworkConfig
            self.Playbook = Playbook
            self.models_available = True
        except ImportError as e:
            self.models_available = False
            self.import_error = str(e)
    
    def validate(self, level: ValidationLevel) -> List[ValidationResult]:
        self.results.clear()
        
        if level != ValidationLevel.FULL:
            return self.results
        
        if not self.models_available:
            self.add_error(f"无法导入 models: {self.import_error}")
            return self.results
        
        # 验证 labbook.yaml
        self._validate_labbook_yaml()
        
        # 验证 config.yaml
        self._validate_config_yaml()
        
        # 验证 playbook.yaml
        self._validate_playbook_yaml()
        
        # 验证网络拓扑连通性
        self._validate_network_connectivity()
        
        # 验证 capability 文件引用
        self._validate_capability_references()
        
        return self.results
    
    def fix(self, level: ValidationLevel) -> List[str]:
        """自动修复内容逻辑问题"""
        fixes = []
        
        if level != ValidationLevel.FULL:
            return fixes
        
        # 修复 capability 文件引用问题
        fixes.extend(self._fix_capability_references())
        
        return fixes
    
    def _validate_labbook_yaml(self):
        """验证 labbook.yaml 内容"""
        labbook_file = self.project_path / "labbook.yaml"
        if not labbook_file.exists():
            return
        
        try:
            with open(labbook_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 处理 Kubernetes 风格的格式
            if 'metadata' in data:
                # 从 metadata 中提取字段
                metadata = data['metadata']
                labbook_data = {
                    'name': metadata.get('name', ''),
                    'description': metadata.get('description', ''),
                    'version': '1.0',  # 默认版本
                    'author': metadata.get('author', ''),
                    'created_at': None
                }
            else:
                # 直接使用数据
                labbook_data = data
            
            # 使用 Pydantic 模型验证
            labbook = self.Labbook(**labbook_data)
            self.add_info("labbook.yaml 内容验证通过")
            
        except Exception as e:
            self.add_error(f"labbook.yaml 内容验证失败: {e}")
    
    def _validate_config_yaml(self):
        """验证 config.yaml 内容"""
        config_file = self.project_path / "network" / "config.yaml"
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 处理 images 格式转换
            if 'images' in data and isinstance(data['images'], dict):
                # 将对象格式转换为列表格式
                images_list = []
                for name, image_data in data['images'].items():
                    if isinstance(image_data, dict):
                        image_data['name'] = name  # 添加名称字段
                        images_list.append(image_data)
                data['images'] = images_list
            
            # 使用 Pydantic 模型验证
            network_config = self.NetworkConfig(**data)
            self.add_info("config.yaml 内容验证通过")
            
        except Exception as e:
            self.add_error(f"config.yaml 内容验证失败: {e}")
    
    def _validate_playbook_yaml(self):
        """验证 playbook.yaml 内容"""
        playbook_file = self.project_path / "playbook.yaml"
        if not playbook_file.exists():
            return
        
        try:
            with open(playbook_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 使用 Pydantic 模型验证
            playbook = self.Playbook(**data)
            self.add_info("playbook.yaml 内容验证通过")
            
        except Exception as e:
            self.add_error(f"playbook.yaml 内容验证失败: {e}")
    
    def _validate_network_connectivity(self):
        """验证网络拓扑连通性"""
        config_file = self.project_path / "network" / "config.yaml"
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 检查节点和链路的连通性
            nodes = data.get('nodes', [])
            links = data.get('links', [])
            
            # 收集所有节点名称
            node_names = {node['name'] for node in nodes}
            
            # 检查链路端点是否指向存在的节点
            for link in links:
                endpoints = link.get('endpoints', [])
                for endpoint in endpoints:
                    if ':' in endpoint:
                        node_name = endpoint.split(':')[0]
                        if node_name not in node_names:
                            self.add_error(f"链路 {link.get('id', 'unknown')} 引用了不存在的节点: {node_name}")
            
            # 检查是否有孤立节点（没有链路的节点）
            connected_nodes = set()
            for link in links:
                endpoints = link.get('endpoints', [])
                for endpoint in endpoints:
                    if ':' in endpoint:
                        node_name = endpoint.split(':')[0]
                        connected_nodes.add(node_name)
            
            isolated_nodes = node_names - connected_nodes
            if isolated_nodes:
                self.add_warning(f"发现孤立节点: {', '.join(isolated_nodes)}")
            
        except Exception as e:
            self.add_error(f"网络连通性验证失败: {e}")
    
    def _validate_capability_references(self):
        """验证 capability 文件引用"""
        playbook_file = self.project_path / "playbook.yaml"
        if not playbook_file.exists():
            return
        
        try:
            with open(playbook_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 收集所有引用的 capability 文件
            capability_files = set()
            
            # 从 timeline 中收集
            timeline = data.get('timeline', {})
            if timeline:
                for step in timeline.get('steps', []):
                    action = step.get('action', {})
                    if 'source' in action:
                        capability_files.add(action['source'])
            
            # 从 procedures 中收集
            for procedure in data.get('procedures', []):
                for step in procedure.get('steps', []):
                    action = step.get('action', {})
                    if 'source' in action:
                        capability_files.add(action['source'])
            
            # 检查文件是否存在
            for capability_file in capability_files:
                file_path = self.project_path / capability_file
                if not file_path.exists():
                    self.add_error(f"引用的 capability 文件不存在: {capability_file}")
                else:
                    # 检查文件内容是否为有效的 YAML
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self.add_error(f"capability 文件格式错误 {capability_file}: {e}")
            
        except Exception as e:
            self.add_error(f"capability 引用验证失败: {e}")
    
    def _fix_capability_references(self) -> List[str]:
        """自动修复 capability 文件引用问题"""
        fixes = []
        playbook_file = self.project_path / "playbook.yaml"
        
        if not playbook_file.exists():
            return fixes
        
        try:
            with open(playbook_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 收集所有引用的 capability 文件
            capability_files = set()
            
            # 从 timeline 中收集
            timeline = data.get('timeline', {})
            if timeline:
                for step in timeline.get('steps', []):
                    action = step.get('action', {})
                    if 'source' in action:
                        capability_files.add(action['source'])
            
            # 从 procedures 中收集
            for procedure in data.get('procedures', []):
                for step in procedure.get('steps', []):
                    action = step.get('action', {})
                    if 'source' in action:
                        capability_files.add(action['source'])
            
            # 创建缺失的 capability 文件
            for capability_file in capability_files:
                file_path = self.project_path / capability_file
                if not file_path.exists():
                    try:
                        # 创建目录
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 创建基本的 capability 文件模板
                        template = self._get_capability_template(capability_file)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(template)
                        
                        fixes.append(f"创建缺失的 capability 文件: {capability_file}")
                    except Exception as e:
                        self.add_error(f"无法创建 capability 文件 {capability_file}: {e}")
            
        except Exception as e:
            self.add_error(f"修复 capability 引用失败: {e}")
        
        return fixes
    
    def _get_capability_template(self, capability_file: str) -> str:
        """根据文件路径生成 capability 模板"""
        if capability_file.startswith('events/'):
            return """name: event.example
description: Example event capability
type: event
target: node1
with:
  parameter1: value1
"""
        elif capability_file.startswith('queries/'):
            return """name: query.example
description: Example query capability
type: query
target: node1
with:
  parameter1: value1
assert:
  - path: result.status
    rule: equals
    value: success
"""
        elif capability_file.startswith('monitors/'):
            return """name: monitor.example
description: Example monitor capability
type: monitor
target: node1
with:
  metric: cpu_usage
interval: 5s
duration: 10m
max_samples: 120
"""
        else:
            return """name: capability.example
description: Example capability
type: event
target: node1
with:
  parameter1: value1
"""

def run_validation(project_path: Path, level: ValidationLevel, strict: bool = False, fix: bool = False) -> bool:
    """运行校验并返回是否通过"""
    validators = [
        ProjectStructureValidator(project_path),
        YAMLFormatValidator(project_path),
        ContentLogicValidator(project_path)
    ]
    
    # 如果启用修复模式，先尝试修复
    if fix:
        print("[cyan]尝试自动修复问题...[/cyan]")
        all_fixes = []
        for validator in validators:
            fixes = validator.fix(level)
            all_fixes.extend(fixes)
        
        if all_fixes:
            print("[green]自动修复完成：[/green]")
            for fix in all_fixes:
                print(f"  ✅ {fix}")
        else:
            print("[yellow]没有需要修复的问题[/yellow]")
    
    # 运行校验
    all_results = []
    for validator in validators:
        results = validator.validate(level)
        all_results.extend(results)
    
    # 按严重程度分类结果
    errors = [r for r in all_results if r.severity == "ERROR"]
    warnings = [r for r in all_results if r.severity == "WARNING"]
    infos = [r for r in all_results if r.severity == "INFO"]
    
    # 输出结果
    if errors:
        print("[bold red]校验失败：[/bold red]")
        for error in errors:
            print(f"  ❌ {error.message}")
    
    if warnings:
        print("[bold yellow]警告：[/bold yellow]")
        for warning in warnings:
            print(f"  ⚠️  {warning.message}")
    
    if infos:
        print("[bold blue]信息：[/bold blue]")
        for info in infos:
            print(f"  ℹ️  {info.message}")
    
    # 判断是否通过
    if strict:
        return len(errors) == 0 and len(warnings) == 0
    else:
        return len(errors) == 0

@app.command()
def validate(
    path: str = typer.Argument(..., help="Labbook 项目目录路径"),
    level: ValidationLevel = typer.Option(ValidationLevel.BASIC, "--level", "-l", help="校验级别"),
    strict: bool = typer.Option(False, "--strict", "-s", help="严格模式，警告也视为错误"),
    fix: bool = typer.Option(False, "--fix", "-f", help="自动修复简单问题")
):
    """分层校验 Labbook 项目"""
    project_path = Path(path)
    
    if not project_path.exists():
        print(f"[red]项目目录不存在: {path}[/red]")
        raise typer.Exit(1)
    
    print(f"[cyan]开始校验项目: {path}[/cyan]")
    print(f"[cyan]校验级别: {level.value}[/cyan]")
    if fix:
        print("[cyan]启用自动修复模式[/cyan]")
    
    success = run_validation(project_path, level, strict, fix)
    
    if success:
        print("[green]✅ 校验通过[/green]")
    else:
        print("[red]❌ 校验失败[/red]")
        raise typer.Exit(1) 