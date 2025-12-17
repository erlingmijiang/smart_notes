"""
Smart Notes - B站视频转Obsidian笔记工具
ModelSpace创空间入口文件
"""

import os
import subprocess
import sys

def main():
    """主函数：启动Smart Notes工具"""
    print("=== Smart Notes - B站视频转Obsidian笔记工具 ===")
    print("这是一个本地运行的工具，需要在本地环境中执行")
    print()
    print("使用说明：")
    print("1. 请在本地克隆此仓库")
    print("2. 安装依赖：uv sync")
    print("3. 配置config.json文件")
    print("4. 运行：uv run main.py")
    print()
    print("项目地址：https://github.com/erlingmijiang/smart_notes")
    print("详细文档请查看README.md")

if __name__ == "__main__":
    main()