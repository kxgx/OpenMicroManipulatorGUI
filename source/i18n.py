"""
多语言翻译模块
支持中文 (zh_CN) 和英文 (en_US)
"""

TRANSLATIONS = {
    'zh_CN': {
        # 主窗口
        'window_title': 'OpenMicroManipulator - 微操作台控制系统',
        'menu_file': '文件 (&F)',
        'menu_tools': '工具 (&T)',
        'menu_help': '帮助 (&H)',
        'action_exit': '退出',
        'action_settings': '设置',
        'action_about': '关于',
        
        # 设备连接
        'device_group': '设备连接',
        'stage_device': '位移台设备:',
        'camera_device': '相机设备:',
        'connect_btn': '连接',
        'disconnect_btn': '断开',
        'refresh_btn': '刷新',
        'connected_status': '已连接',
        'disconnected_status': '未连接',
        
        # 运动控制
        'motion_group': '运动控制',
        'x_axis': 'X 轴:',
        'y_axis': 'Y 轴:',
        'z_axis': 'Z 轴:',
        'move_to': '移动到:',
        'move_btn': '移动',
        'home_btn': '回零',
        'current_pos': '当前位置:',
        
        # 速度控制
        'speed_group': '速度控制',
        'speed_label': '速度:',
        'speed_unit': 'mm/min',
        
        # 图像处理
        'image_group': '图像处理',
        'capture_btn': '采集图像',
        'save_btn': '保存图像',
        'align_btn': '图像对准',
        'track_btn': '目标跟踪',
        
        # 状态栏
        'status_ready': '就绪',
        'status_connecting': '正在连接...',
        'status_moving': '正在移动...',
        'status_error': '错误',
        
        # 消息提示
        'msg_connect_success': '设备连接成功',
        'msg_connect_failed': '设备连接失败',
        'msg_move_complete': '移动完成',
        'msg_save_success': '保存成功',
        'msg_save_failed': '保存失败',
        
        # 对话框
        'dlg_title_about': '关于',
        'dlg_title_settings': '设置',
        'dlg_title_error': '错误',
        'dlg_title_warning': '警告',
        
        # 通用按钮
        'btn_ok': '确定',
        'btn_cancel': '取消',
        'btn_close': '关闭',
        'btn_apply': '应用',
        
        # 语言设置
        'language_label': '界面语言:',
        'language_restart_info': '语言更改后需要重启应用程序才能完全生效。',
        'msg_language_change': '语言已更改，部分界面元素可能需要重启后才能完全更新。是否继续？',
    },
    
    'en_US': {
        # Main Window
        'window_title': 'OpenMicroManipulator - Micro Stage Control System',
        'menu_file': 'File(&F)',
        'menu_tools': 'Tools(&T)',
        'menu_help': 'Help(&H)',
        'action_exit': 'Exit',
        'action_settings': 'Settings',
        'action_about': 'About',
        
        # Device Connection
        'device_group': 'Device Connection',
        'stage_device': 'Stage Device:',
        'camera_device': 'Camera Device:',
        'connect_btn': 'Connect',
        'disconnect_btn': 'Disconnect',
        'refresh_btn': 'Refresh',
        'connected_status': 'Connected',
        'disconnected_status': 'Disconnected',
        
        # Motion Control
        'motion_group': 'Motion Control',
        'x_axis': 'X Axis:',
        'y_axis': 'Y Axis:',
        'z_axis': 'Z Axis:',
        'move_to': 'Move to:',
        'move_btn': 'Move',
        'home_btn': 'Home',
        'current_pos': 'Current Position:',
        
        # Speed Control
        'speed_group': 'Speed Control',
        'speed_label': 'Speed:',
        'speed_unit': 'mm/min',
        
        # Image Processing
        'image_group': 'Image Processing',
        'capture_btn': 'Capture Image',
        'save_btn': 'Save Image',
        'align_btn': 'Image Align',
        'track_btn': 'Target Track',
        
        # Status Bar
        'status_ready': 'Ready',
        'status_connecting': 'Connecting...',
        'status_moving': 'Moving...',
        'status_error': 'Error',
        
        # Messages
        'msg_connect_success': 'Device connected successfully',
        'msg_connect_failed': 'Failed to connect device',
        'msg_move_complete': 'Move completed',
        'msg_save_success': 'Saved successfully',
        'msg_save_failed': 'Failed to save',
        
        # Dialogs
        'dlg_title_about': 'About',
        'dlg_title_settings': 'Settings',
        'dlg_title_error': 'Error',
        'dlg_title_warning': 'Warning',
        
        # Common Buttons
        'btn_ok': 'OK',
        'btn_cancel': 'Cancel',
        'btn_close': 'Close',
        'btn_apply': 'Apply',
            
        # Language Settings
        'language_label': 'Language:',
        'language_restart_info': 'The application needs to be restarted for language changes to take full effect.',
        'msg_language_change': 'Language has been changed. Some interface elements may require a restart to fully update. Continue?',
    },
}


class Translator:
    """翻译器类"""
    
    def __init__(self):
        self.current_language = 'zh_CN'  # 默认中文
    
    def set_language(self, lang_code):
        """设置当前语言"""
        if lang_code in TRANSLATIONS:
            self.current_language = lang_code
    
    def get_current_language(self):
        """获取当前语言代码"""
        return self.current_language
    
    def tr(self, key):
        """翻译文本"""
        translations = TRANSLATIONS.get(self.current_language, TRANSLATIONS['zh_CN'])
        return translations.get(key, key)
    
    def get_available_languages(self):
        """获取可用语言列表"""
        return {
            'zh_CN': '简体中文',
            'en_US': 'English'
        }


# 创建全局翻译器实例
translator = Translator()


def get_translator():
    """获取全局翻译器"""
    return translator


def tr(key):
    """快捷翻译函数"""
    return translator.tr(key)
