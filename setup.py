#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化脚本
首次使用时运行，安装依赖并初始化目录
"""

import os
import subprocess
import sys


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("="*60)
    print("  视频自动发布系统 - 初始化")
    print("="*60)

    # 1. 安装Python依赖
    print("\n  [1/3] 安装Python依赖...")
    req_file = os.path.join(base_dir, 'requirements.txt')
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', req_file],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("    >> 依赖安装成功")
    else:
        print(f"    !! 依赖安装失败: {result.stderr}")
        print("    请手动执行: pip install -r requirements.txt")

    # 2. 安装Playwright浏览器
    print("\n  [2/3] 安装Playwright浏览器...")
    print("    (首次运行需要下载Chromium，可能需要几分钟)")
    result = subprocess.run(
        [sys.executable, '-m', 'playwright', 'install', 'chromium'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("    >> 浏览器安装成功")
    else:
        print(f"    !! 浏览器安装失败: {result.stderr}")
        print("    请手动执行: playwright install chromium")

    # 3. 创建目录和初始文件
    print("\n  [3/3] 初始化目录...")
    dirs = [
        os.path.join(base_dir, 'data', 'videos'),
        os.path.join(base_dir, 'data', 'tasks'),
        os.path.join(base_dir, 'data', 'config'),
        os.path.join(base_dir, 'data', 'browser_state'),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 创建空的 videos.json
    videos_file = os.path.join(base_dir, 'data', 'videos.json')
    if not os.path.exists(videos_file):
        with open(videos_file, 'w', encoding='utf-8') as f:
            f.write('[]')
        print("    >> 已创建 data/videos.json")

    print("    >> 目录初始化完成")

    print(f"\n{'='*60}")
    print("  >> 初始化完成!")
    print(f"{'='*60}")
    print("\n  使用方式:")
    print(f"    cd {base_dir}")
    print(f"    python main.py")
    print()


if __name__ == "__main__":
    main()
