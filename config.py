#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局配置文件
所有路径基于项目根目录，方便移植和分享
"""

import os

# ==================== 路径配置 ====================
# 项目根目录（自动获取，不需要手动修改）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
VIDEOS_DIR = os.path.join(DATA_DIR, 'videos')
TASKS_DIR = os.path.join(DATA_DIR, 'tasks')
CONFIG_DIR = os.path.join(DATA_DIR, 'config')
BROWSER_STATE_DIR = os.path.join(DATA_DIR, 'browser_state')

# 核心数据文件
VIDEOS_FILE = os.path.join(DATA_DIR, 'videos.json')
DOUYIN_TASKS_FILE = os.path.join(TASKS_DIR, 'douyin_tasks.json')
WECHAT_TASKS_FILE = os.path.join(TASKS_DIR, 'wechat_tasks.json')
PUBLISH_HISTORY_FILE = os.path.join(TASKS_DIR, 'publish_history.json')

# 账号相关
DOUYIN_ACCOUNTS_FILE = os.path.join(BROWSER_STATE_DIR, 'douyin_accounts.json')
WECHAT_STATE_FILE = os.path.join(BROWSER_STATE_DIR, 'wechat_browser_state.json')

# 抖音发布配置
DOUYIN_CONFIG_FILE = os.path.join(CONFIG_DIR, 'douyin_config.json')

# ==================== 抖音默认配置 ====================
DOUYIN_DEFAULT_CONFIG = {
    "videos_per_account": 7,
    "start_hour": 8,
    "interval_hours": 2
}

# ==================== 视频号配置 ====================
# 位置设置
WECHAT_SHOW_LOCATION = False
WECHAT_LOCATION_TEXT = "不显示位置"

# 原创声明
WECHAT_DECLARE_ORIGINAL = True

# 定时发布
WECHAT_ENABLE_SCHEDULE = True

# 浏览器设置
WECHAT_HEADLESS = False
WECHAT_STATE_VALID_DAYS = 7

# 视频号目标页面
WECHAT_TARGET_URL = "https://channels.weixin.qq.com/platform/post/create"

# 视频号每次发布数量
WECHAT_PUBLISH_COUNT = 8
WECHAT_START_HOUR = 8
WECHAT_INTERVAL_HOURS = 2


# ==================== 初始化目录 ====================
def ensure_dirs():
    """确保所有必要目录存在"""
    dirs = [DATA_DIR, VIDEOS_DIR, TASKS_DIR, CONFIG_DIR, BROWSER_STATE_DIR]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


# 导入时自动创建目录
ensure_dirs()
