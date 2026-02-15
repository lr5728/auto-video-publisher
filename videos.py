#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频管理模块
负责 videos.json 的增删查改操作
"""

import os
import json
from datetime import datetime

import config


def load_videos():
    """加载视频列表"""
    if not os.path.exists(config.VIDEOS_FILE):
        return []
    with open(config.VIDEOS_FILE, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def save_videos(videos):
    """保存视频列表"""
    with open(config.VIDEOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)


def get_next_id(videos):
    """获取下一个视频ID"""
    if not videos:
        return "v001"
    max_num = 0
    for v in videos:
        try:
            num = int(v['id'].lstrip('v'))
            if num > max_num:
                max_num = num
        except (ValueError, KeyError):
            pass
    return f"v{max_num + 1:03d}"


def add_video(video_path, title, description, category="", topics=None):
    """
    添加视频到列表
    :param video_path: 视频文件路径
    :param title: 短标题
    :param description: 详细描述
    :param category: 分类（可选）
    :param topics: 话题标签列表（可选）
    :return: 新添加的视频信息
    """
    videos = load_videos()

    # 处理视频路径：如果是相对路径，基于项目目录
    if not os.path.isabs(video_path):
        video_path = os.path.join(config.BASE_DIR, video_path)

    if not os.path.exists(video_path):
        print(f"  !! 警告: 视频文件不存在: {video_path}")

    new_video = {
        "id": get_next_id(videos),
        "video_path": video_path,
        "title": title,
        "description": description,
        "category": category,
        "topics": topics or [],
        "published_douyin": False,
        "published_wechat": False,
        "publish_time_douyin": None,
        "publish_time_wechat": None,
        "added_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    videos.append(new_video)
    save_videos(videos)
    return new_video


def remove_video(video_id):
    """
    删除视频
    :param video_id: 视频ID
    :return: 是否成功
    """
    videos = load_videos()
    original_len = len(videos)
    videos = [v for v in videos if v['id'] != video_id]

    if len(videos) == original_len:
        return False

    save_videos(videos)
    return True


def get_video_by_id(video_id):
    """根据ID获取视频"""
    videos = load_videos()
    for v in videos:
        if v['id'] == video_id:
            return v
    return None


def get_unpublished(platform):
    """
    获取未发布到指定平台的视频
    :param platform: 'douyin' 或 'wechat'
    :return: 视频列表
    """
    videos = load_videos()
    field = 'published_douyin' if platform == 'douyin' else 'published_wechat'
    return [v for v in videos if not v.get(field, False)]


def mark_published(video_id, platform):
    """
    标记视频为已发布
    :param video_id: 视频ID
    :param platform: 'douyin' 或 'wechat'
    """
    videos = load_videos()
    field = 'published_douyin' if platform == 'douyin' else 'published_wechat'
    time_field = 'publish_time_douyin' if platform == 'douyin' else 'publish_time_wechat'

    for v in videos:
        if v['id'] == video_id:
            v[field] = True
            v[time_field] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break

    save_videos(videos)


def show_videos():
    """显示视频列表"""
    videos = load_videos()

    if not videos:
        print("\n  暂无视频，请先添加视频")
        return

    print(f"\n{'='*60}")
    print(f"  视频列表 (共 {len(videos)} 个)")
    print(f"{'='*60}")

    for v in videos:
        dy = "Y" if v.get('published_douyin') else "N"
        wx = "Y" if v.get('published_wechat') else "N"

        print(f"\n  [{v['id']}] {v['title']}")
        print(f"       文件: {os.path.basename(v['video_path'])}")
        if v.get('category'):
            print(f"       分类: {v['category']}")
        if v.get('topics'):
            print(f"       话题: {' '.join('#' + t for t in v['topics'])}")
        print(f"       抖音: {dy}  视频号: {wx}")

    print(f"\n{'='*60}")


def interactive_add():
    """交互式添加视频"""
    print(f"\n{'='*60}")
    print("  添加视频")
    print(f"{'='*60}")

    video_path = input("\n  视频文件路径: ").strip()
    if not video_path:
        print("  !! 路径不能为空")
        return None

    title = input("  短标题: ").strip()
    if not title:
        print("  !! 标题不能为空")
        return None

    description = input("  详细描述: ").strip()
    if not description:
        description = title

    category = input("  分类 (直接回车跳过): ").strip()

    topics_str = input("  话题标签 (用空格分隔，直接回车跳过): ").strip()
    topics = topics_str.split() if topics_str else []

    video = add_video(video_path, title, description, category, topics)
    print(f"\n  >> 视频已添加: [{video['id']}] {video['title']}")
    return video


def interactive_remove():
    """交互式删除视频"""
    show_videos()

    videos = load_videos()
    if not videos:
        return

    video_id = input("\n  输入要删除的视频ID: ").strip()
    if not video_id:
        return

    video = get_video_by_id(video_id)
    if not video:
        print(f"  !! 未找到视频: {video_id}")
        return

    confirm = input(f"  确认删除 [{video_id}] {video['title']}? (y/n): ").strip().lower()
    if confirm == 'y':
        remove_video(video_id)
        print(f"  >> 已删除: {video_id}")
    else:
        print("  >> 已取消")
