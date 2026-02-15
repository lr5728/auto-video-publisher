#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频号发布模块
负责视频上传到微信视频号
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from publishers import wechat_config as wc


class WeChatPublisher:
    """视频号发布器（单例模式，复用浏览器）"""

    _browser = None
    _context = None
    _page = None
    _uploaded_count = 0

    def upload_video(self, video_path, title, description, topics=None, scheduled_time=None):
        """
        上传视频到视频号
        :param video_path: 视频文件路径
        :param title: 短标题
        :param description: 描述
        :param topics: 话题列表
        :param scheduled_time: 定时时间 'YYYY-MM-DD HH:MM:SS'
        :return: {'success': True/False, 'error_message': '...'}
        """
        try:
            print(f"\n{'='*60}")
            print(f"  上传视频到视频号")
            print(f"{'='*60}")
            print(f"  视频: {Path(video_path).name}")
            print(f"  标题: {title}")
            if scheduled_time:
                print(f"  定时: {scheduled_time}")

            # 1. 确保已登录
            if not self._ensure_login():
                return {'success': False, 'error_message': '登录失败'}

            page = WeChatPublisher._page

            # 2. 非首次上传需要重新打开页面
            if WeChatPublisher._uploaded_count > 0:
                print("\n  重新打开创建页面...")
                try:
                    page.goto("https://channels.weixin.qq.com/platform/post",
                              wait_until='domcontentloaded')
                    time.sleep(1)
                    page.goto(config.WECHAT_TARGET_URL, wait_until='domcontentloaded')
                    time.sleep(wc.WAIT_TIME['after_page_load'])

                    upload_area = page.locator(wc.SELECTORS['upload_area']).first
                    upload_area.wait_for(state='visible', timeout=10000)
                except Exception as e:
                    raise Exception(f"页面刷新失败: {e}")

            # 3. 上传视频文件
            print("\n  [1/6] 上传视频...")
            self._upload_file(page, video_path)

            # 4. 填写标题
            print("  [2/6] 填写标题...")
            self._fill_title(page, title)

            # 5. 填写描述 + 话题
            print("  [3/6] 填写描述...")
            desc_with_topics = description
            if topics:
                desc_with_topics += ' ' + ' '.join(f'#{t}' for t in topics)
            self._fill_description(page, desc_with_topics)

            # 6. 设置定时发布
            if scheduled_time and config.WECHAT_ENABLE_SCHEDULE:
                print("  [4/6] 设置定时发布...")
                try:
                    self._set_schedule(page, scheduled_time)
                except Exception as e:
                    print(f"    !! 自动设置失败: {e}")
                    print(f"    目标时间: {scheduled_time}")
                    print("    请在浏览器中手动设置")
                    while True:
                        user_input = input("\n    手动设置完成了吗? (y=继续/n=取消): ").strip().lower()
                        if user_input == 'y':
                            break
                        elif user_input == 'n':
                            raise Exception("用户取消发布")
            else:
                print("  [4/6] 跳过定时发布")

            # 7. 设置位置
            print("  [5/6] 设置位置...")
            self._set_location(page)

            # 8. 声明原创
            if config.WECHAT_DECLARE_ORIGINAL:
                print("  [5.5/6] 声明原创...")
                self._declare_original(page)

            # 9. 等待上传完成
            print("  [6/6] 等待视频处理...")
            self._wait_for_upload_ready(page)

            # 10. 点击发布
            print("  发布中...")
            self._click_publish(page)
            time.sleep(3)

            print("  >> 发布成功!\n")
            WeChatPublisher._uploaded_count += 1
            return {'success': True}

        except Exception as e:
            error_msg = f"上传失败: {str(e)}"
            print(f"  !! {error_msg}\n")
            return {'success': False, 'error_message': error_msg}

    def _ensure_login(self):
        """确保已登录"""
        if WeChatPublisher._browser is not None:
            return True

        from playwright.sync_api import sync_playwright

        # 加载保存的登录状态
        storage_state = self._load_state()

        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=config.WECHAT_HEADLESS,
            channel="chrome"
        )

        if storage_state:
            context = browser.new_context(storage_state=storage_state)
            print("  使用保存的登录状态")
        else:
            context = browser.new_context()
            print("  !! 未找到登录状态，需要扫码登录")

        page = context.new_page()
        page.goto(config.WECHAT_TARGET_URL, timeout=wc.TIMEOUT['page_load'])
        time.sleep(2)

        # 检查登录状态
        login_ok = self._check_login(page)

        if not login_ok:
            print("\n  需要扫码登录...")
            print("  请使用微信扫描浏览器中的二维码")

            while True:
                user_input = input("\n  扫码完成了吗? (y/n): ").strip().lower()
                if user_input == 'y':
                    time.sleep(3)
                    if self._check_login(page):
                        self._save_state(context)
                        login_ok = True
                        break
                    else:
                        print("  !! 验证失败，请重试")
                elif user_input == 'n':
                    browser.close()
                    return False

        if login_ok:
            WeChatPublisher._browser = browser
            WeChatPublisher._context = context
            WeChatPublisher._page = page
            return True

        browser.close()
        return False

    def _check_login(self, page):
        """检查是否已登录"""
        try:
            page.wait_for_selector('input[type="file"]', timeout=5000)
            return True
        except:
            pass

        if 'post/create' in page.url or 'platform' in page.url:
            return True

        return False

    def _load_state(self):
        """加载登录状态"""
        try:
            if not os.path.exists(config.WECHAT_STATE_FILE):
                return None

            with open(config.WECHAT_STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            storage_state = state_data.get('storage_state')
            if not storage_state:
                return None

            age = time.time() - state_data.get('timestamp', 0)
            if age > config.WECHAT_STATE_VALID_DAYS * 24 * 3600:
                print("  !! 登录状态已过期")
                return None

            age_hours = age / 3600
            print(f"  加载登录状态 ({age_hours:.1f} 小时前保存)")
            return storage_state

        except Exception as e:
            print(f"  !! 加载状态失败: {e}")
            return None

    def _save_state(self, context):
        """保存登录状态"""
        try:
            state_data = {
                'cookies': context.cookies(),
                'storage_state': context.storage_state(),
                'timestamp': time.time()
            }
            with open(config.WECHAT_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            print("  >> 登录状态已保存")
        except Exception as e:
            print(f"  !! 保存状态失败: {e}")

    def _upload_file(self, page, video_path):
        """上传视频文件"""
        video_path = str(Path(video_path).absolute())
        file_input = page.locator('input[type="file"]').first
        if file_input.count() == 0:
            raise Exception("未找到文件上传输入框")
        file_input.set_input_files(video_path)
        time.sleep(wc.WAIT_TIME['after_upload'])

    def _fill_title(self, page, title):
        """填写标题"""
        title_input = page.locator(wc.SELECTORS['title_input']).first
        if title_input.count() == 0:
            raise Exception("未找到标题输入框")
        title_input.click()
        title_input.fill(title)
        time.sleep(wc.WAIT_TIME['after_fill'])

    def _fill_description(self, page, description):
        """填写描述"""
        editor = page.locator(wc.SELECTORS['description_editor']).first
        if editor.count() == 0:
            raise Exception("未找到描述编辑器")
        editor.click()
        editor.fill(description)
        time.sleep(wc.WAIT_TIME['after_fill'])

    def _set_schedule(self, page, scheduled_time):
        """设置定时发布"""
        try:
            dt = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            dt = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M')

        # 1. 点击定时发布开关
        toggle_locator = page.locator('.weui-desktop-form__check-label')
        toggle_count = toggle_locator.count()
        if toggle_count == 0:
            raise Exception("未找到定时发布选项")

        confirm_label = page.locator('.label').filter(has_text='发表时间')

        if not (confirm_label.count() > 0 and confirm_label.first.is_visible()):
            success = False
            for idx in range(toggle_count):
                toggle = toggle_locator.nth(idx)
                try:
                    toggle.wait_for(state='visible', timeout=5000)
                except:
                    continue
                toggle.click()
                page.wait_for_timeout(300)
                if confirm_label.count() > 0:
                    try:
                        if confirm_label.first.is_visible():
                            success = True
                            break
                    except:
                        pass
            if not success:
                raise Exception("无法开启定时发布")

        # 2. 打开日期选择面板
        date_input = page.locator(
            '.weui-desktop-picker__date-time input.weui-desktop-form__input'
        ).first
        if date_input.count() == 0:
            raise Exception("未找到日期输入框")
        date_input.click()
        time.sleep(0.5)

        # 3. 等待日期面板
        day_panel = page.locator('.weui-desktop-picker__panel_day:visible').first
        try:
            day_panel.wait_for(state='visible', timeout=5000)
        except:
            raise Exception("日期选择面板未打开")

        # 4. 导航到目标月份
        def get_current_ym():
            labels = day_panel.locator('.weui-desktop-picker__panel__label')
            year_text = labels.nth(0).inner_text().strip().rstrip('年')
            month_text = labels.nth(1).inner_text().strip().rstrip('月')
            return int(year_text), int(month_text)

        target_serial = dt.year * 12 + dt.month
        for _ in range(36):
            cy, cm = get_current_ym()
            current_serial = cy * 12 + cm
            if current_serial == target_serial:
                break
            elif current_serial < target_serial:
                btn = day_panel.locator(
                    '.weui-desktop-picker__panel__action.weui-desktop-picker__panel__action_next'
                )
                if btn.count() > 0:
                    btn.click()
                    time.sleep(0.3)
            else:
                btn = day_panel.locator(
                    '.weui-desktop-picker__panel__action.weui-desktop-picker__panel__action_prev'
                )
                if btn.count() > 0:
                    btn.click()
                    time.sleep(0.3)

        # 5. 选择日期
        day_text = str(dt.day)
        day_candidates = day_panel.locator(f'a:has-text("{day_text}")')
        found = False
        for idx in range(day_candidates.count()):
            candidate = day_candidates.nth(idx)
            classes = (candidate.get_attribute('class') or '')
            if 'disabled' in classes:
                continue
            candidate.click()
            page.wait_for_timeout(200)
            found = True
            break
        if not found:
            raise Exception(f"未找到日期: {dt.day}日")

        # 6. 设置时间
        time_input = day_panel.locator(
            '.weui-desktop-picker__time input.weui-desktop-form__input'
        ).first
        try:
            time_input.wait_for(state='visible', timeout=2000)
            time_input.click()
            page.wait_for_timeout(200)
        except:
            raise Exception("未找到时间输入框")

        time_panel = day_panel.locator('.weui-desktop-picker__dd__time:visible').first
        try:
            time_panel.wait_for(state='visible', timeout=2000)
        except:
            raise Exception("时间面板未展开")

        # 小时
        hour_text = f"{dt.hour:02d}"
        hour_option = time_panel.locator(
            '.weui-desktop-picker__time__hour li'
        ).filter(has_text=hour_text)
        if hour_option.count() == 0:
            raise Exception(f"未找到小时: {hour_text}")
        hour_option.first.click()
        page.wait_for_timeout(200)

        # 分钟
        minute_text = f"{dt.minute:02d}"
        minute_option = time_panel.locator(
            '.weui-desktop-picker__time__minute li'
        ).filter(has_text=minute_text)
        if minute_option.count() == 0:
            raise Exception(f"未找到分钟: {minute_text}")
        minute_option.first.click()
        page.wait_for_timeout(200)

        # 确认
        time_icon = day_panel.locator(
            '.weui-desktop-picker__time i.weui-desktop-icon__time'
        ).first
        try:
            if time_icon.is_visible():
                time_icon.click()
                page.wait_for_timeout(200)
        except:
            pass

    def _set_location(self, page):
        """设置位置（隐藏）"""
        if config.WECHAT_SHOW_LOCATION:
            return
        try:
            dropdown = page.locator(wc.SELECTORS['position_dropdown']).first
            if dropdown.count() > 0:
                dropdown.click()
                time.sleep(wc.WAIT_TIME['after_click'])
                option = page.locator(wc.SELECTORS['position_option']).filter(
                    has_text=config.WECHAT_LOCATION_TEXT
                ).first
                if option.count() > 0:
                    option.click()
                    time.sleep(wc.WAIT_TIME['after_click'])
        except:
            pass  # 位置设置失败不影响发布

    def _declare_original(self, page):
        """声明原创"""
        try:
            checkbox1 = page.locator(wc.SELECTORS['original_checkbox_1']).filter(
                has_text=wc.SELECTORS['original_checkbox_1_text']
            ).first
            if checkbox1.count() > 0:
                checked = page.locator(wc.SELECTORS['original_checkbox_1_checked']).count() > 0
                if not checked:
                    checkbox1.click()
                    time.sleep(wc.WAIT_TIME['after_click'])

            dialog = page.locator(wc.SELECTORS['original_dialog'])
            if dialog.count() > 0:
                checkbox2 = page.locator(wc.SELECTORS['original_checkbox_2']).first
                if checkbox2.count() > 0:
                    checked2 = page.locator(wc.SELECTORS['original_checkbox_2_checked']).count() > 0
                    if not checked2:
                        checkbox2.click()
                        time.sleep(wc.WAIT_TIME['after_click'])

                confirm_selector = (
                    f"{wc.SELECTORS['original_dialog']} "
                    f"{wc.SELECTORS['original_confirm_btn']}"
                    f"{wc.SELECTORS['original_confirm_btn_not_disabled']}"
                )
                confirm_btn = page.locator(confirm_selector).filter(
                    has_text=wc.SELECTORS['original_confirm_text']
                ).first
                if confirm_btn.count() > 0:
                    confirm_btn.click()
                    time.sleep(wc.WAIT_TIME['after_click'])
                    try:
                        dialog.first.wait_for(state='detached', timeout=5000)
                    except:
                        pass
        except:
            pass  # 原创声明失败不影响发布

    def _wait_for_upload_ready(self, page):
        """等待视频处理完成"""
        publish_btn = page.locator(
            f"{wc.SELECTORS['publish_button']}:not(.weui-desktop-btn_disabled)"
        ).filter(has_text=wc.SELECTORS['publish_button_text']).first
        publish_btn.wait_for(state='visible', timeout=wc.TIMEOUT['upload'])

    def _click_publish(self, page):
        """点击发布按钮"""
        publish_btn = page.locator(
            f"{wc.SELECTORS['publish_button']}:not(.weui-desktop-btn_disabled)"
        ).filter(has_text=wc.SELECTORS['publish_button_text']).first
        if publish_btn.count() == 0:
            raise Exception("未找到发布按钮")
        publish_btn.click()
        time.sleep(wc.WAIT_TIME['after_click'])
        time.sleep(3)

    @classmethod
    def cleanup(cls):
        """清理浏览器资源"""
        if cls._browser:
            print("\n  关闭浏览器...")
            cls._browser.close()
            cls._browser = None
            cls._context = None
            cls._page = None
            cls._uploaded_count = 0
