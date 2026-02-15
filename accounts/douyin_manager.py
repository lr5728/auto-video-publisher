#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音账号管理模块
负责账号的添加、查看、启用/禁用、浏览器状态管理
"""

import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class DouyinAccountManager:
    """抖音账号管理器"""

    def __init__(self):
        self.state_dir = config.BROWSER_STATE_DIR
        self.accounts_file = config.DOUYIN_ACCOUNTS_FILE

    def get_accounts(self):
        """获取所有账号"""
        if not os.path.exists(self.accounts_file):
            return []
        with open(self.accounts_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)

    def get_active_accounts(self):
        """获取所有活跃账号"""
        accounts = self.get_accounts()
        return [acc for acc in accounts if acc.get('status') == 'active']

    def get_account_by_id(self, account_id):
        """根据ID获取账号"""
        for acc in self.get_accounts():
            if acc['account_id'] == account_id:
                return acc
        return None

    def get_account_state_path(self, account_id):
        """获取账号状态文件的绝对路径"""
        account = self.get_account_by_id(account_id)
        if not account:
            return None
        state_file = account.get('state_file')
        if not state_file:
            return None
        return os.path.join(self.state_dir, state_file)

    def verify_account_state(self, account_id):
        """验证账号状态文件是否存在"""
        state_path = self.get_account_state_path(account_id)
        return state_path and os.path.exists(state_path)

    def count_accounts(self):
        """统计账号数量 -> (总数, 活跃数)"""
        accounts = self.get_accounts()
        active = [a for a in accounts if a.get('status') == 'active']
        return len(accounts), len(active)

    def detect_accounts(self):
        """检测并返回所有可用账号"""
        if os.path.exists(self.accounts_file):
            accounts = self.get_accounts()
            if accounts:
                return self.get_active_accounts()

        detected = self._scan_state_files()
        if detected:
            self._save_accounts(detected)
        return detected

    def _scan_state_files(self):
        """扫描状态文件目录"""
        if not os.path.exists(self.state_dir):
            return []

        accounts = []
        for filename in os.listdir(self.state_dir):
            if filename.startswith('douyin_state_') and filename.endswith('.json'):
                account_id = filename.replace('douyin_state_', '').replace('.json', '')
                accounts.append({
                    'account_id': account_id,
                    'account_name': f'抖音账号{account_id}',
                    'state_file': filename,
                    'status': 'active',
                    'added_at': 'auto-detected'
                })

        accounts.sort(key=lambda x: x['account_id'])
        return accounts

    def show_accounts(self):
        """显示账号列表"""
        accounts = self.get_active_accounts()

        if not accounts:
            print("\n  未找到任何抖音账号")
            print("  请先添加账号")
            return False

        print(f"\n{'='*60}")
        print("  抖音账号列表")
        print(f"{'='*60}")

        for i, acc in enumerate(accounts, 1):
            state_ok = self.verify_account_state(acc['account_id'])
            icon = "[ok]" if state_ok else "[!!]"

            print(f"\n  {i}. {icon} {acc['account_name']}")
            print(f"     ID: {acc['account_id']}")
            print(f"     状态文件: {acc.get('state_file', 'N/A')}")
            print(f"     添加时间: {acc.get('added_at', 'N/A')}")

            if not state_ok:
                print(f"     !! 状态文件缺失，请重新登录")

        print(f"\n{'='*60}")
        print(f"  总计: {len(accounts)} 个账号")
        return True

    def disable_account(self, account_id):
        """禁用账号"""
        accounts = self.get_accounts()
        for acc in accounts:
            if acc['account_id'] == account_id:
                acc['status'] = 'disabled'
                self._save_accounts(accounts)
                return True
        return False

    def enable_account(self, account_id):
        """启用账号"""
        accounts = self.get_accounts()
        for acc in accounts:
            if acc['account_id'] == account_id:
                acc['status'] = 'active'
                self._save_accounts(accounts)
                return True
        return False

    def update_account_name(self, account_id, new_name):
        """更新账号名称"""
        accounts = self.get_accounts()
        for acc in accounts:
            if acc['account_id'] == account_id:
                acc['account_name'] = new_name
                self._save_accounts(accounts)
                return True
        return False

    def _save_accounts(self, accounts):
        """保存账号列表"""
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)


def _get_next_account_id(accounts):
    """获取下一个账号ID"""
    if not accounts:
        return "001"
    max_id = 0
    for acc in accounts:
        try:
            acc_id = int(acc['account_id'])
            if acc_id > max_id:
                max_id = acc_id
        except ValueError:
            pass
    return f"{max_id + 1:03d}"


def add_douyin_account():
    """交互式添加抖音账号"""
    from playwright.sync_api import sync_playwright

    manager = DouyinAccountManager()
    accounts = manager.get_accounts()

    print(f"\n{'='*60}")
    print("  添加抖音账号")
    print(f"{'='*60}")
    print(f"\n  当前已有账号: {len(accounts)} 个")

    if accounts:
        for acc in accounts:
            print(f"    {acc['account_id']}. {acc['account_name']}")

    account_id = _get_next_account_id(accounts)
    state_file = f"douyin_state_{account_id}.json"
    state_path = os.path.join(config.BROWSER_STATE_DIR, state_file)

    print(f"\n  准备添加账号: {account_id}")
    input("\n  按回车开始登录...")

    with sync_playwright() as p:
        print("\n  正在启动浏览器...")
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        print("  正在打开抖音创作者平台...")
        page.goto('https://creator.douyin.com/')
        time.sleep(3)

        print(f"\n{'='*60}")
        print("  请在浏览器中扫码登录")
        print(f"{'='*60}")
        print("\n  1. 使用抖音APP扫描二维码")
        print("  2. 在手机上确认登录")
        print("  3. 等待页面跳转到创作者中心")

        input("\n  登录完成后，按回车继续...")

        # 尝试获取账号名
        account_name = None
        try:
            time.sleep(3)
            for selector in ['.account-name', '.user-name', '[class*="user"]', '[class*="account"]']:
                try:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        name = el.inner_text()
                        if name and name.strip():
                            account_name = name.strip()
                            break
                except:
                    continue
        except:
            pass

        if not account_name:
            account_name = input("\n  请手动输入账号名称: ").strip()
            if not account_name:
                account_name = f"抖音账号{account_id}"

        print(f"  账号名称: {account_name}")

        # 保存登录状态
        print("\n  保存登录状态...")
        context.storage_state(path=state_path)

        new_account = {
            "account_id": account_id,
            "account_name": account_name,
            "state_file": state_file,
            "added_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "status": "active"
        }

        accounts.append(new_account)
        manager._save_accounts(accounts)

        browser.close()

        print(f"\n{'='*60}")
        print(f"  >> 账号添加成功!")
        print(f"     ID: {account_id}")
        print(f"     名称: {account_name}")
        print(f"{'='*60}")


def view_douyin_accounts():
    """查看和管理抖音账号"""
    manager = DouyinAccountManager()
    manager.detect_accounts()

    if not manager.show_accounts():
        return

    print("\n  操作选项:")
    print("  1. 修改账号名称")
    print("  2. 禁用账号")
    print("  3. 启用账号")
    print("  0. 返回")

    choice = input("\n  请选择 (0-3): ").strip()

    if choice == '1':
        account_id = input("\n  输入账号ID: ").strip()
        new_name = input("  输入新名称: ").strip()
        if new_name and manager.update_account_name(account_id, new_name):
            print(f"  >> 账号 {account_id} 已更名为: {new_name}")
        else:
            print(f"  !! 更新失败")

    elif choice == '2':
        account_id = input("\n  输入要禁用的账号ID: ").strip()
        if manager.disable_account(account_id):
            print(f"  >> 账号 {account_id} 已禁用")
        else:
            print(f"  !! 账号不存在")

    elif choice == '3':
        account_id = input("\n  输入要启用的账号ID: ").strip()
        if manager.enable_account(account_id):
            print(f"  >> 账号 {account_id} 已启用")
        else:
            print(f"  !! 账号不存在")


def open_douyin_account():
    """打开指定抖音账号的浏览器"""
    from playwright.sync_api import sync_playwright

    manager = DouyinAccountManager()
    accounts = manager.detect_accounts()

    if not accounts:
        print("\n  !! 未检测到任何抖音账号")
        return

    print(f"\n{'='*60}")
    print("  打开抖音账号")
    print(f"{'='*60}")

    for idx, acc in enumerate(accounts, 1):
        status = "[ok]" if acc['status'] == 'active' else "[!!]"
        print(f"  [{idx}] {acc['account_name']} (ID: {acc['account_id']}) {status}")

    try:
        choice = int(input(f"\n  选择账号序号 (1-{len(accounts)}): ").strip())
        if choice < 1 or choice > len(accounts):
            print("  !! 无效序号")
            return
        selected = accounts[choice - 1]
    except (ValueError, KeyboardInterrupt):
        print("\n  !! 已取消")
        return

    state_path = manager.get_account_state_path(selected['account_id'])
    if not state_path or not os.path.exists(state_path):
        print(f"\n  !! 状态文件不存在，请重新登录")
        return

    print(f"\n  正在打开: {selected['account_name']}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--start-fullscreen', '--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                storage_state=state_path,
                no_viewport=True,
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()

            print("  正在访问抖音创作者平台...")
            page.goto('https://creator.douyin.com/', wait_until='networkidle', timeout=30000)

            print("\n  >> 浏览器已打开!")
            print("  >> 关闭浏览器窗口或按 Ctrl+C 退出")

            try:
                page.wait_for_timeout(3600000)
            except KeyboardInterrupt:
                pass

            # 保存最新状态
            context.storage_state(path=state_path)
            browser.close()
            print("\n  >> 浏览器已关闭，状态已保存")

    except Exception as e:
        print(f"\n  !! 打开浏览器失败: {e}")
