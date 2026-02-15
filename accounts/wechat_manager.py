#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频号账号管理模块
负责微信视频号的登录状态管理
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def check_wechat_state():
    """检查视频号登录状态"""
    state_file = config.WECHAT_STATE_FILE

    if not os.path.exists(state_file):
        return False, "未登录"

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)

        timestamp = state_data.get('timestamp', 0)
        age_hours = (time.time() - timestamp) / 3600
        age_days = age_hours / 24

        if age_days > config.WECHAT_STATE_VALID_DAYS:
            return False, f"登录已过期 ({age_days:.1f} 天前)"

        return True, f"已登录 ({age_hours:.1f} 小时前)"

    except Exception as e:
        return False, f"状态文件异常: {e}"


def login_wechat():
    """视频号扫码登录"""
    from playwright.sync_api import sync_playwright

    print(f"\n{'='*60}")
    print("  视频号登录")
    print(f"{'='*60}")

    valid, status = check_wechat_state()
    if valid:
        print(f"\n  当前状态: {status}")
        choice = input("  是否重新登录? (y/n): ").strip().lower()
        if choice != 'y':
            print("  >> 保持当前登录")
            return True

    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=config.WECHAT_HEADLESS,
            channel="chrome"
        )
        context = browser.new_context()
        page = context.new_page()

        print(f"\n  正在打开视频号后台...")
        page.goto(config.WECHAT_TARGET_URL, timeout=30000)
        time.sleep(2)

        print(f"\n{'='*60}")
        print("  请使用微信扫描浏览器中的二维码")
        print(f"{'='*60}")

        while True:
            user_input = input("\n  扫码完成了吗? (y/n): ").strip().lower()

            if user_input == 'y':
                time.sleep(3)

                # 验证登录
                login_ok = False
                try:
                    page.wait_for_selector('input[type="file"]', timeout=5000)
                    login_ok = True
                except:
                    current_url = page.url
                    if 'post/create' in current_url or 'platform' in current_url:
                        login_ok = True

                if login_ok:
                    # 保存状态
                    cookies = context.cookies()
                    storage_state = context.storage_state()

                    state_data = {
                        'cookies': cookies,
                        'storage_state': storage_state,
                        'timestamp': time.time()
                    }

                    os.makedirs(os.path.dirname(config.WECHAT_STATE_FILE), exist_ok=True)
                    with open(config.WECHAT_STATE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(state_data, f, indent=2, ensure_ascii=False)

                    print("\n  >> 登录成功! 状态已保存")
                    browser.close()
                    return True
                else:
                    print("  !! 登录验证失败，请重新扫码")

            elif user_input == 'n':
                print("  >> 已取消登录")
                browser.close()
                return False

    except Exception as e:
        print(f"  !! 登录失败: {e}")
        return False


def manage_wechat_account():
    """视频号账号管理入口"""
    print(f"\n{'='*60}")
    print("  视频号账号管理")
    print(f"{'='*60}")

    valid, status = check_wechat_state()
    print(f"\n  登录状态: {status}")

    print("\n  1. 扫码登录/更新登录")
    print("  0. 返回")

    choice = input("\n  请选择: ").strip()

    if choice == '1':
        login_wechat()
