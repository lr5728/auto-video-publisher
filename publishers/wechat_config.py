#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频号页面选择器配置
如果微信改版，只需修改这里的选择器
"""

# ==================== 页面选择器 ====================
SELECTORS = {
    # 上传相关
    'upload_area': '.upload-content',
    'file_input': 'input[type="file"]',

    # 表单相关
    'title_input': 'input.weui-desktop-form__input[placeholder*="概括视频主要内容"]',
    'description_editor': '.input-editor',

    # 定时发布
    'schedule_toggle': '.weui-desktop-form__check-label',

    # 位置选择
    'position_dropdown': '.position-display',
    'position_option': '.option-item',

    # 原创声明
    'original_checkbox_1': '.declare-original-checkbox label.ant-checkbox-wrapper',
    'original_checkbox_1_text': '声明后，作品将展示原创标记，有机会获得广告收入。',
    'original_checkbox_1_checked': '.declare-original-checkbox label.ant-checkbox-wrapper-checked',
    'original_dialog': '.weui-desktop-dialog__wrp:not([style*="display: none"])',
    'original_checkbox_2': '.original-proto-wrapper label.ant-checkbox-wrapper',
    'original_checkbox_2_checked': '.original-proto-wrapper label.ant-checkbox-wrapper-checked',
    'original_confirm_btn': 'button.weui-desktop-btn.weui-desktop-btn_primary',
    'original_confirm_text': '声明原创',
    'original_confirm_btn_not_disabled': ':not(.weui-desktop-btn_disabled)',

    # 发布按钮
    'publish_button': 'button.weui-desktop-btn.weui-desktop-btn_primary',
    'publish_button_text': '发表',
}

# ==================== 超时设置（毫秒）====================
TIMEOUT = {
    'upload': 60000,
    'page_load': 30000,
    'element_wait': 10000,
    'login_wait': 300000,
}

# ==================== 等待时间（秒）====================
WAIT_TIME = {
    'after_upload': 2,
    'after_fill': 1,
    'after_click': 1,
    'after_page_load': 3,
}
