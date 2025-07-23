#!/usr/bin/env python3
"""
解决 Matplotlib 中文字体显示问题

这个脚本提供了多种方法来解决 Matplotlib 中文字体显示问题：
1. 设置中文字体
2. 安装字体包
3. 配置 Matplotlib 使用中文字体
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import subprocess
import sys
import os
from pathlib import Path


def check_system_fonts():
    """检查系统可用的中文字体"""
    print("=== 检查系统字体 ===")
    
    # 获取所有字体
    fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 查找中文字体
    chinese_fonts = []
    for font in fonts:
        if any(keyword in font.lower() for keyword in ['chinese', 'cjk', 'simsun', 'simhei', 'microsoft yahei', 'noto sans cjk']):
            chinese_fonts.append(font)
    
    print(f"找到 {len(chinese_fonts)} 个中文字体:")
    for font in chinese_fonts[:10]:  # 只显示前10个
        print(f"  - {font}")
    
    if len(chinese_fonts) > 10:
        print(f"  ... 还有 {len(chinese_fonts) - 10} 个字体")
    
    return chinese_fonts


def install_chinese_fonts():
    """安装中文字体包"""
    print("\n=== 安装中文字体包 ===")
    
    try:
        # 检测操作系统
        if os.name == 'posix':  # Linux/Unix
            # 尝试安装字体包
            packages = [
                'fonts-noto-cjk',
                'fonts-wqy-microhei',
                'fonts-wqy-zenhei',
                'fonts-arphic-uming',
                'fonts-arphic-ukai'
            ]
            
            for package in packages:
                try:
                    print(f"尝试安装 {package}...")
                    result = subprocess.run(['sudo', 'apt-get', 'install', '-y', package], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        print(f"✓ {package} 安装成功")
                        break
                    else:
                        print(f"✗ {package} 安装失败: {result.stderr}")
                except subprocess.TimeoutExpired:
                    print(f"✗ {package} 安装超时")
                except FileNotFoundError:
                    print("✗ 未找到 apt-get，可能不是 Ubuntu/Debian 系统")
                    break
                    
        elif os.name == 'nt':  # Windows
            print("Windows 系统通常已包含中文字体")
            
        else:
            print("未知操作系统，请手动安装中文字体")
            
    except Exception as e:
        print(f"安装字体时出错: {e}")


def configure_matplotlib_fonts():
    """配置 Matplotlib 使用中文字体"""
    print("\n=== 配置 Matplotlib 字体 ===")
    
    # 方法1: 使用 rcParams 设置
    print("方法1: 使用 rcParams 设置字体")
    
    # 尝试不同的中文字体
    chinese_fonts = [
        'SimHei',           # 黑体
        'SimSun',           # 宋体
        'Microsoft YaHei',  # 微软雅黑
        'WenQuanYi Micro Hei',  # 文泉驿微米黑
        'Noto Sans CJK SC',     # Noto Sans 中文简体
        'Noto Sans CJK TC',     # Noto Sans 中文繁体
        'WenQuanYi Zen Hei',    # 文泉驿正黑
        'AR PL UMing CN',       # AR PL UMing
        'AR PL UKai CN',        # AR PL UKai
        'DejaVu Sans'           # 回退字体
    ]
    
    # 检查哪些字体可用
    available_fonts = []
    for font in chinese_fonts:
        try:
            fm.findfont(font)
            available_fonts.append(font)
            print(f"  ✓ {font} 可用")
        except:
            print(f"  ✗ {font} 不可用")
    
    if available_fonts:
        # 使用第一个可用的中文字体
        selected_font = available_fonts[0]
        print(f"\n使用字体: {selected_font}")
        
        # 设置字体
        plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        return True
    else:
        print("未找到可用的中文字体")
        return False


def test_chinese_display():
    """测试中文显示"""
    print("\n=== 测试中文显示 ===")
    
    try:
        # 创建测试图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 测试数据
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 1, 5, 3]
        
        # 绘制图表
        ax.plot(x, y, 'o-', linewidth=2, markersize=8)
        ax.set_xlabel('X轴标签')
        ax.set_ylabel('Y轴标签')
        ax.set_title('中文标题测试')
        ax.grid(True, alpha=0.3)
        
        # 添加中文注释
        ax.text(3, 4, '这是中文注释', fontsize=12, ha='center')
        
        # 保存图片
        output_file = 'chinese_test.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✓ 测试图表已保存到: {output_file}")
        
        # 显示图表
        plt.show()
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def create_font_config_file():
    """创建字体配置文件"""
    print("\n=== 创建字体配置文件 ===")
    
    config_content = '''# Matplotlib 中文字体配置
# 将此文件保存为 ~/.matplotlib/matplotlibrc 或在代码中使用

# 设置中文字体
font.sans-serif: SimHei, SimSun, Microsoft YaHei, WenQuanYi Micro Hei, Noto Sans CJK SC, DejaVu Sans

# 解决负号显示问题
axes.unicode_minus: False

# 字体大小设置
font.size: 12
axes.titlesize: 14
axes.labelsize: 12
xtick.labelsize: 10
ytick.labelsize: 10
legend.fontsize: 10
figure.titlesize: 16
'''
    
    # 创建配置目录
    config_dir = Path.home() / '.matplotlib'
    config_dir.mkdir(exist_ok=True)
    
    # 保存配置文件
    config_file = config_dir / 'matplotlibrc'
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✓ 配置文件已保存到: {config_file}")
    print("重启 Python 或重新导入 matplotlib 后生效")


def setup_chinese_fonts_in_notebook():
    """在 Jupyter Notebook 中设置中文字体"""
    print("\n=== Jupyter Notebook 中文字体设置 ===")
    
    notebook_code = '''# 在 Jupyter Notebook 中设置中文字体
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 方法1: 使用 rcParams
plt.rcParams['font.sans-serif'] = ['SimHei', 'SimSun', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 方法2: 使用 fontproperties
# font_path = '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'
# font_prop = fm.FontProperties(fname=font_path)

# 方法3: 动态设置字体
def set_chinese_font():
    """设置中文字体"""
    # 查找可用的中文字体
    fonts = [f.name for f in fm.fontManager.ttflist]
    chinese_fonts = [f for f in fonts if any(keyword in f.lower() 
                   for keyword in ['chinese', 'cjk', 'simsun', 'simhei', 'microsoft yahei'])]
    
    if chinese_fonts:
        plt.rcParams['font.sans-serif'] = [chinese_fonts[0]] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        print(f"使用字体: {chinese_fonts[0]}")
    else:
        print("未找到中文字体，使用默认字体")

# 调用函数
set_chinese_font()

# 测试中文显示
import numpy as np
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y, 'b-', linewidth=2)
plt.title('正弦波函数')
plt.xlabel('X轴')
plt.ylabel('Y轴')
plt.grid(True, alpha=0.3)
plt.show()
'''
    
    # 保存到文件
    with open('notebook_chinese_font_setup.py', 'w', encoding='utf-8') as f:
        f.write(notebook_code)
    
    print("✓ Jupyter Notebook 字体设置代码已保存到: notebook_chinese_font_setup.py")


def main():
    """主函数"""
    print("Matplotlib 中文字体问题解决方案")
    print("=" * 50)
    
    # 1. 检查系统字体
    chinese_fonts = check_system_fonts()
    
    # 2. 如果没有中文字体，尝试安装
    if not chinese_fonts:
        install_chinese_fonts()
        chinese_fonts = check_system_fonts()
    
    # 3. 配置 Matplotlib
    if configure_matplotlib_fonts():
        # 4. 测试中文显示
        test_chinese_display()
    
    # 5. 创建配置文件
    create_font_config_file()
    
    # 6. 创建 Notebook 设置代码
    setup_chinese_fonts_in_notebook()
    
    print("\n=== 解决方案总结 ===")
    print("1. 检查了系统可用的中文字体")
    print("2. 配置了 Matplotlib 使用中文字体")
    print("3. 创建了字体配置文件")
    print("4. 生成了 Jupyter Notebook 设置代码")
    print("\n如果仍有问题，请尝试:")
    print("- 重启 Python 环境")
    print("- 重新导入 matplotlib")
    print("- 手动安装中文字体包")


if __name__ == "__main__":
    main() 