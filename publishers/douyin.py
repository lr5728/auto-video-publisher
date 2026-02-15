#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音发布模块
负责视频上传到抖音创作者平台
"""

import os
import sys
import json
import time
import threading
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# 抖音上传页面
UPLOAD_URL = 'https://creator.douyin.com/creator-micro/content/upload'


def upload_video(page, video_path):
    """上传视频文件"""
    print("\n    上传视频...")
    file_input = page.locator('input[type="file"]').first
    if file_input.count() == 0:
        raise Exception("未找到文件上传输入框")
    video_path = str(Path(video_path).absolute())
    file_input.set_input_files(video_path)
    print(f"      视频已选择: {Path(video_path).name}")
    time.sleep(3)


def fill_title(page, title):
    """填写标题"""
    print("    填写标题...")
    title_input = page.locator('.semi-input').first
    if title_input.count() == 0:
        raise Exception("未找到标题输入框")
    title_input.click()
    title_input.fill(title)
    print(f"      标题: {title}")
    time.sleep(1)


def fill_description(page, description, topics):
    """填写简介并添加话题"""
    print("    填写简介...")
    editor = page.locator('.editor-kit-container').first
    if editor.count() == 0:
        raise Exception("未找到简介编辑器")

    editor.click()
    time.sleep(0.5)
    page.keyboard.type(description)
    time.sleep(1)

    if topics:
        print("    添加话题...")
        for topic in topics:
            page.keyboard.type(f'#{topic}')
            time.sleep(0.5)
            page.keyboard.press('Enter')
            print(f"      话题: #{topic}")
            time.sleep(0.5)


def set_schedule(page, scheduled_time):
    """设置定时发布"""
    print(f"    设置定时发布: {scheduled_time}")

    schedule_label = page.locator('label:has-text("定时发布")').first
    if schedule_label.count() == 0:
        raise Exception("未找到定时发布选项")

    schedule_label.click()
    time.sleep(1)

    time_input = page.locator('input[placeholder="日期和时间"]').first
    if time_input.count() == 0:
        raise Exception("未找到时间输入框")

    time_input.click()
    time.sleep(0.5)
    page.keyboard.press('Meta+A')
    time.sleep(0.3)
    page.keyboard.type(scheduled_time)
    time.sleep(0.5)
    page.keyboard.press('Enter')
    time.sleep(0.5)


def click_publish(page):
    """点击发布按钮"""
    print("    点击发布...")
    publish_btn = page.locator('button.button-dhlUZE.primary-cECiOJ').first
    if publish_btn.count() == 0:
        publish_btn = page.locator('button:has-text("发布")').first
    if publish_btn.count() == 0:
        raise Exception("未找到发布按钮")

    publish_btn.click()
    time.sleep(2)
    print("      等待发布处理...")
    time.sleep(3)
    print("      >> 发布成功")


def publish_single_task(browser, task, video_data, account_state_file):
    """
    发布单个任务
    :param browser: 浏览器对象
    :param task: 任务字典
    :param video_data: 视频数据（来自videos.json）
    :param account_state_file: 账号状态文件路径
    :return: 是否成功
    """
    try:
        print(f"\n{'='*60}")
        print(f"  发布任务: {task['task_id']}")
        print(f"  账号: {task['account_name']}")
        print(f"  定时: {task['scheduled_time']}")
        print(f"{'='*60}")

        # 创建上下文并加载登录状态
        context = browser.new_context(storage_state=account_state_file)
        page = context.new_page()

        # 跳转到上传页面
        print("\n    打开上传页面...")
        page.goto(UPLOAD_URL)
        time.sleep(3)

        # 上传视频
        upload_video(page, video_data['video_path'])

        # 标题
        title = video_data['title']
        if len(title) > 30:
            title = title[:30]
        fill_title(page, title)

        # 简介 + 话题
        description = video_data.get('description', video_data['title'])
        topics = video_data.get('topics', [])
        fill_description(page, description, topics)

        # 定时发布
        scheduled_time = task['scheduled_time'][:16]  # 去掉秒
        set_schedule(page, scheduled_time)

        # 发布
        click_publish(page)

        print("\n  >> 任务发布成功!")

        page.close()
        context.close()
        return True

    except Exception as e:
        print(f"\n  !! 任务发布失败: {e}")
        return False


def _execute_tasks_internal():
    """内部执行函数：执行所有待发布的抖音任务"""
    from playwright.sync_api import sync_playwright

    print(f"\n{'='*60}")
    print("  开始执行抖音发布任务")
    print(f"{'='*60}")

    # 加载任务表
    if not os.path.exists(config.DOUYIN_TASKS_FILE):
        print("\n  !! 任务表不存在，请先生成任务")
        return

    with open(config.DOUYIN_TASKS_FILE, 'r', encoding='utf-8') as f:
        task_table = json.load(f)

    tasks = task_table['tasks']
    pending_tasks = [t for t in tasks if t['status'] in ['pending', 'failed']]

    if not pending_tasks:
        print("\n  没有待发布的任务")
        return

    print(f"\n  待处理任务: {len(pending_tasks)} 个")

    # 加载视频数据
    import videos
    all_videos = videos.load_videos()
    video_dict = {v['id']: v for v in all_videos}

    # 启动浏览器
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        accounts = task_table['accounts']
        for account in accounts:
            account_id = account['account_id']
            account_name = account['account_name']
            state_file = os.path.join(config.BROWSER_STATE_DIR, account['state_file'])

            account_tasks = [t for t in pending_tasks if t['account_id'] == account_id]
            if not account_tasks:
                continue

            print(f"\n\n{'='*60}")
            print(f"  账号: {account_name}")
            print(f"  任务数: {len(account_tasks)}")
            print(f"{'='*60}")

            for idx, task in enumerate(account_tasks, 1):
                print(f"\n  进度: {idx}/{len(account_tasks)}")

                # 更新状态
                _update_task_status(task['task_id'], 'processing')

                video_data = video_dict.get(task['video_id'])
                if not video_data:
                    print(f"  !! 未找到视频: {task['video_id']}")
                    _update_task_status(task['task_id'], 'failed', '视频数据不存在')
                    continue

                success = publish_single_task(browser, task, video_data, state_file)

                if success:
                    _update_task_status(task['task_id'], 'completed')
                    videos.mark_published(task['video_id'], 'douyin')
                else:
                    _update_task_status(task['task_id'], 'failed', '发布失败')

                if idx < len(account_tasks):
                    print("\n  等待5秒后继续...")
                    time.sleep(5)

        browser.close()

    print(f"\n{'='*60}")
    print("  >> 所有任务执行完成")
    print(f"{'='*60}")


def _update_task_status(task_id, status, error_message=None):
    """更新任务状态"""
    if not os.path.exists(config.DOUYIN_TASKS_FILE):
        return

    with open(config.DOUYIN_TASKS_FILE, 'r', encoding='utf-8') as f:
        task_table = json.load(f)

    for task in task_table['tasks']:
        if task['task_id'] == task_id:
            task['status'] = status
            task['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
            if error_message:
                task['error'] = error_message
            break

    with open(config.DOUYIN_TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(task_table, f, ensure_ascii=False, indent=2)


def execute_douyin_tasks():
    """执行抖音发布任务（外部接口）"""
    thread = threading.Thread(target=_execute_tasks_internal)
    thread.start()
    thread.join()
