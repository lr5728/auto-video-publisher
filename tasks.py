#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务生成模块
为抖音和视频号生成发布任务
"""

import os
import json
from datetime import datetime

import config
import videos
from accounts.douyin_manager import DouyinAccountManager


def load_douyin_config():
    """加载抖音发布配置"""
    if not os.path.exists(config.DOUYIN_CONFIG_FILE):
        return dict(config.DOUYIN_DEFAULT_CONFIG)

    with open(config.DOUYIN_CONFIG_FILE, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return dict(config.DOUYIN_DEFAULT_CONFIG)
        return json.loads(content)


def save_douyin_config(cfg):
    """保存抖音发布配置"""
    os.makedirs(os.path.dirname(config.DOUYIN_CONFIG_FILE), exist_ok=True)
    with open(config.DOUYIN_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def generate_time_slots(target_date, count, start_hour, interval_hours):
    """
    生成时间序列
    :return: ['YYYY-MM-DD HH:00:00', ...]
    """
    slots = []
    hour = start_hour
    for _ in range(count):
        slots.append(f"{target_date} {hour:02d}:00:00")
        hour += interval_hours
        if hour >= 24:
            hour = hour % 24
    return slots


def generate_douyin_tasks(target_date=None):
    """
    生成抖音发布任务
    :param target_date: 'YYYY-MM-DD'，默认今天
    :return: 任务表字典
    """
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')

    print(f"\n{'='*60}")
    print("  生成抖音发布任务")
    print(f"{'='*60}")

    # 1. 加载配置
    cfg = load_douyin_config()
    videos_per_account = cfg['videos_per_account']
    start_hour = cfg['start_hour']
    interval_hours = cfg['interval_hours']

    print(f"\n  配置:")
    print(f"    每账号视频数: {videos_per_account}")
    print(f"    开始时间: {start_hour}:00")
    print(f"    间隔: {interval_hours}小时")

    # 2. 加载账号
    manager = DouyinAccountManager()
    accounts = manager.detect_accounts()
    if not accounts:
        print("\n  !! 未找到任何抖音账号，请先添加")
        return None

    print(f"\n  账号: {len(accounts)} 个")
    for acc in accounts:
        print(f"    - {acc['account_name']} (ID: {acc['account_id']})")

    # 3. 获取未发布的视频
    unpublished = videos.get_unpublished('douyin')
    total_needed = len(accounts) * videos_per_account

    print(f"\n  可用视频: {len(unpublished)} 个")
    print(f"  需要视频: {total_needed} 个")

    if len(unpublished) < total_needed:
        if len(unpublished) == 0:
            print("\n  !! 没有可用的视频，请先添加视频")
            return None
        print(f"\n  !! 视频不足，将按可用数量分配")
        videos_per_account = len(unpublished) // len(accounts)
        if videos_per_account == 0:
            videos_per_account = 1
        total_needed = min(len(unpublished), len(accounts) * videos_per_account)

    # 4. 生成任务
    tasks = []
    task_counter = 1
    video_offset = 0

    for account in accounts:
        count = min(videos_per_account, len(unpublished) - video_offset)
        if count <= 0:
            break

        account_videos = unpublished[video_offset:video_offset + count]
        video_offset += count

        time_slots = generate_time_slots(target_date, count, start_hour, interval_hours)

        for video_item, scheduled_time in zip(account_videos, time_slots):
            tasks.append({
                "task_id": f"task_douyin_{target_date.replace('-', '')}_{task_counter:03d}",
                "account_id": account['account_id'],
                "account_name": account['account_name'],
                "video_id": video_item['id'],
                "video_title": video_item['title'],
                "scheduled_time": scheduled_time,
                "status": "pending",
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            task_counter += 1

    # 5. 保存任务表
    task_table = {
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "target_date": target_date,
        "platform": "douyin",
        "accounts": accounts,
        "tasks": tasks,
        "summary": {
            "total_accounts": len(accounts),
            "total_tasks": len(tasks)
        }
    }

    os.makedirs(os.path.dirname(config.DOUYIN_TASKS_FILE), exist_ok=True)
    with open(config.DOUYIN_TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(task_table, f, ensure_ascii=False, indent=2)

    print(f"\n  >> 任务生成完成!")
    print(f"     总计: {len(tasks)} 个任务")
    print(f"     保存至: {config.DOUYIN_TASKS_FILE}")

    # 显示预览
    for t in tasks[:5]:
        print(f"     {t['account_name']} | {t['scheduled_time']} | {t['video_title']}")
    if len(tasks) > 5:
        print(f"     ... 还有 {len(tasks) - 5} 条")

    return task_table


def generate_wechat_tasks(target_date=None):
    """
    生成视频号发布任务
    :param target_date: 'YYYY-MM-DD'，默认今天
    :return: 任务表字典
    """
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')

    print(f"\n{'='*60}")
    print("  生成视频号发布任务")
    print(f"{'='*60}")

    publish_count = config.WECHAT_PUBLISH_COUNT
    start_hour = config.WECHAT_START_HOUR
    interval_hours = config.WECHAT_INTERVAL_HOURS

    # 获取未发布的视频
    unpublished = videos.get_unpublished('wechat')

    print(f"\n  可用视频: {len(unpublished)} 个")
    print(f"  计划发布: {publish_count} 个")

    if not unpublished:
        print("\n  !! 没有可用的视频，请先添加视频")
        return None

    actual_count = min(publish_count, len(unpublished))
    selected = unpublished[:actual_count]

    time_slots = generate_time_slots(target_date, actual_count, start_hour, interval_hours)

    tasks = []
    for idx, (video_item, scheduled_time) in enumerate(zip(selected, time_slots), 1):
        tasks.append({
            "task_id": f"task_wechat_{target_date.replace('-', '')}_{idx:03d}",
            "video_id": video_item['id'],
            "video_title": video_item['title'],
            "scheduled_time": scheduled_time,
            "status": "pending",
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    task_table = {
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "target_date": target_date,
        "platform": "wechat",
        "tasks": tasks,
        "summary": {
            "total_tasks": len(tasks)
        }
    }

    os.makedirs(os.path.dirname(config.WECHAT_TASKS_FILE), exist_ok=True)
    with open(config.WECHAT_TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(task_table, f, ensure_ascii=False, indent=2)

    print(f"\n  >> 任务生成完成!")
    print(f"     总计: {len(tasks)} 个任务")

    for t in tasks[:5]:
        print(f"     {t['scheduled_time']} | {t['video_title']}")
    if len(tasks) > 5:
        print(f"     ... 还有 {len(tasks) - 5} 条")

    return task_table


def manage_douyin_config():
    """管理抖音发布配置"""
    cfg = load_douyin_config()

    print(f"\n{'='*60}")
    print("  抖音发布配置")
    print(f"{'='*60}")

    while True:
        print(f"\n  当前配置:")
        print(f"    每账号视频数: {cfg.get('videos_per_account', 7)}")
        print(f"    开始时间: {cfg.get('start_hour', 8):02d}:00")
        print(f"    时间间隔: {cfg.get('interval_hours', 2)} 小时")

        print(f"\n  1. 修改配置")
        print(f"  2. 恢复默认")
        print(f"  0. 返回")

        choice = input("\n  请选择: ").strip()

        if choice == '1':
            print("\n  修改配置（直接回车跳过）:")

            val = input(f"    每账号视频数 [{cfg.get('videos_per_account', 7)}]: ").strip()
            if val:
                try:
                    cfg['videos_per_account'] = int(val)
                except ValueError:
                    print("    !! 无效输入")

            val = input(f"    开始时间 (0-23) [{cfg.get('start_hour', 8)}]: ").strip()
            if val:
                try:
                    h = int(val)
                    if 0 <= h <= 23:
                        cfg['start_hour'] = h
                except ValueError:
                    print("    !! 无效输入")

            val = input(f"    时间间隔 (小时) [{cfg.get('interval_hours', 2)}]: ").strip()
            if val:
                try:
                    cfg['interval_hours'] = int(val)
                except ValueError:
                    print("    !! 无效输入")

            save_douyin_config(cfg)
            print("\n  >> 配置已保存")

        elif choice == '2':
            cfg = dict(config.DOUYIN_DEFAULT_CONFIG)
            save_douyin_config(cfg)
            print("\n  >> 已恢复默认配置")

        elif choice == '0':
            break
