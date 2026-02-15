#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动发布系统 - 主程序
支持抖音和视频号的自动发布
"""

import sys
import os
import json
from datetime import datetime

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import videos
import tasks


def load_json(file_path):
    """加载JSON文件"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return None
        return json.loads(content)


def save_json(file_path, data):
    """保存JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 发布功能 ====================

def publish_douyin():
    """发布到抖音"""
    print(f"\n{'='*60}")
    print("  发布到抖音")
    print(f"{'='*60}")

    date_str = input("\n  发布日期 (YYYY-MM-DD，回车=今天): ").strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
        print(f"  使用今天: {date_str}")

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print("  !! 日期格式错误")
        return

    if target_date < datetime.now().date():
        print("  !! 不能选择过去的日期")
        return

    # 检查是否已有任务
    existing = load_json(config.DOUYIN_TASKS_FILE)
    if existing and existing.get('target_date') == date_str:
        t = existing.get('tasks', [])
        pending = [x for x in t if x['status'] in ['pending', 'failed']]
        done = [x for x in t if x['status'] in ['completed']]

        print(f"\n  发现已有任务:")
        print(f"    已完成: {len(done)} 条")
        print(f"    待发布: {len(pending)} 条")

        if not pending:
            print("\n  所有任务已完成")
            return

        choice = input("\n  继续执行未完成的任务? (y/n): ").strip().lower()
        if choice != 'y':
            return
    else:
        # 生成新任务
        task_data = tasks.generate_douyin_tasks(date_str)
        if not task_data:
            return

        choice = input("\n  立即执行发布? (y/n): ").strip().lower()
        if choice != 'y':
            print("  >> 任务已保存，稍后可执行")
            return

    # 执行发布
    from publishers.douyin import execute_douyin_tasks
    execute_douyin_tasks()


def publish_wechat():
    """发布到视频号"""
    print(f"\n{'='*60}")
    print("  发布到视频号")
    print(f"{'='*60}")

    date_str = input("\n  发布日期 (YYYY-MM-DD，回车=今天): ").strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
        print(f"  使用今天: {date_str}")

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print("  !! 日期格式错误")
        return

    if target_date < datetime.now().date():
        print("  !! 不能选择过去的日期")
        return

    # 检查是否已有任务
    existing = load_json(config.WECHAT_TASKS_FILE)
    if existing and existing.get('target_date') == date_str:
        t = existing.get('tasks', [])
        pending = [x for x in t if x['status'] in ['pending', 'failed']]
        done = [x for x in t if x['status'] in ['published', 'completed']]

        print(f"\n  发现已有任务:")
        print(f"    已完成: {len(done)} 条")
        print(f"    待发布: {len(pending)} 条")

        if not pending:
            print("\n  所有任务已完成")
            return

        choice = input("\n  继续执行未完成的任务? (y/n): ").strip().lower()
        if choice != 'y':
            return
    else:
        task_data = tasks.generate_wechat_tasks(date_str)
        if not task_data:
            return

        choice = input("\n  立即执行发布? (y/n): ").strip().lower()
        if choice != 'y':
            print("  >> 任务已保存，稍后可执行")
            return

    # 执行发布
    _execute_wechat_publish()


def _execute_wechat_publish():
    """执行视频号发布"""
    from publishers.wechat import WeChatPublisher

    task_data = load_json(config.WECHAT_TASKS_FILE)
    if not task_data:
        print("  !! 没有任务数据")
        return

    all_tasks = task_data.get('tasks', [])
    pending = [t for t in all_tasks if t['status'] in ['pending', 'failed']]

    if not pending:
        print("  没有待发布的任务")
        return

    all_videos = videos.load_videos()
    video_dict = {v['id']: v for v in all_videos}

    publisher = WeChatPublisher()
    success_count = 0
    failed_count = 0

    for idx, task in enumerate(pending, 1):
        video_id = task['video_id']
        video_data = video_dict.get(video_id)

        if not video_data:
            print(f"\n  [{idx}/{len(pending)}] !! 视频不存在: {video_id}")
            task['status'] = 'failed'
            task['error'] = '视频数据不存在'
            failed_count += 1
            continue

        print(f"\n  [{idx}/{len(pending)}] 处理任务")
        print(f"    时间: {task['scheduled_time']}")
        print(f"    标题: {video_data['title']}")

        task['status'] = 'publishing'
        save_json(config.WECHAT_TASKS_FILE, task_data)

        result = publisher.upload_video(
            video_path=video_data['video_path'],
            title=video_data['title'],
            description=video_data.get('description', ''),
            topics=video_data.get('topics', []),
            scheduled_time=task['scheduled_time']
        )

        if result['success']:
            task['status'] = 'published'
            task['published_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            videos.mark_published(video_id, 'wechat')
            success_count += 1
            print(f"    >> 发布成功")
        else:
            task['status'] = 'failed'
            task['error'] = result.get('error_message', '')
            failed_count += 1
            print(f"    !! 发布失败: {result.get('error_message', '')}")

        save_json(config.WECHAT_TASKS_FILE, task_data)

    # 清理
    WeChatPublisher.cleanup()

    print(f"\n{'='*60}")
    print(f"  发布完成!")
    print(f"  成功: {success_count} 条")
    if failed_count > 0:
        print(f"  失败: {failed_count} 条")
    print(f"{'='*60}")


def show_task_status():
    """查看任务状态"""
    print(f"\n{'='*60}")
    print("  任务状态")
    print(f"{'='*60}")

    for name, filepath in [("抖音", config.DOUYIN_TASKS_FILE), ("视频号", config.WECHAT_TASKS_FILE)]:
        data = load_json(filepath)
        if not data:
            print(f"\n  [{name}] 无任务")
            continue

        t = data.get('tasks', [])
        pending = len([x for x in t if x['status'] == 'pending'])
        done = len([x for x in t if x['status'] in ['completed', 'published']])
        failed = len([x for x in t if x['status'] == 'failed'])
        processing = len([x for x in t if x['status'] in ['processing', 'publishing']])

        print(f"\n  [{name}] 日期: {data.get('target_date', '未知')}")
        print(f"    总计: {len(t)} | 完成: {done} | 待发布: {pending} | 失败: {failed} | 进行中: {processing}")


# ==================== 主菜单 ====================

def show_menu():
    """显示主菜单"""
    print(f"\n{'='*60}")
    print("  视频自动发布系统")
    print(f"{'='*60}")
    print("\n  【视频发布】")
    print("    1. 发布到视频号")
    print("    2. 发布到抖音")
    print("\n  【视频管理】")
    print("    3. 添加视频")
    print("    4. 查看视频列表")
    print("    5. 删除视频")
    print("\n  【账号管理】")
    print("    6. 添加抖音账号")
    print("    7. 查看/管理抖音账号")
    print("    8. 打开抖音账号")
    print("    9. 视频号账号管理")
    print("\n  【配置】")
    print("   10. 抖音发布配置")
    print("   11. 查看任务状态")
    print("\n    0. 退出")
    print(f"{'='*60}")


def main():
    """主程序入口"""
    while True:
        show_menu()
        choice = input("\n  请输入功能编号: ").strip()

        if choice == '0':
            print("\n  再见!")
            break

        elif choice == '1':
            publish_wechat()
            input("\n  按回车返回...")

        elif choice == '2':
            publish_douyin()
            input("\n  按回车返回...")

        elif choice == '3':
            videos.interactive_add()
            input("\n  按回车返回...")

        elif choice == '4':
            videos.show_videos()
            input("\n  按回车返回...")

        elif choice == '5':
            videos.interactive_remove()
            input("\n  按回车返回...")

        elif choice == '6':
            from accounts.douyin_manager import add_douyin_account
            add_douyin_account()
            input("\n  按回车返回...")

        elif choice == '7':
            from accounts.douyin_manager import view_douyin_accounts
            view_douyin_accounts()
            input("\n  按回车返回...")

        elif choice == '8':
            from accounts.douyin_manager import open_douyin_account
            open_douyin_account()
            input("\n  按回车返回...")

        elif choice == '9':
            from accounts.wechat_manager import manage_wechat_account
            manage_wechat_account()
            input("\n  按回车返回...")

        elif choice == '10':
            tasks.manage_douyin_config()
            input("\n  按回车返回...")

        elif choice == '11':
            show_task_status()
            input("\n  按回车返回...")

        else:
            print("\n  !! 无效选择")
            input("\n  按回车返回...")


if __name__ == "__main__":
    main()
