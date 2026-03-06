"""
日志监视器组件
用于显示主程序详细日志（包括串口通信信息）
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel, 
                                QPushButton, QHBoxLayout, QCheckBox, QComboBox,
                                QSplitter, QFrame)
from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QFont
import time
from i18n import tr


class LogMonitorWidget(QWidget):
    """日志监视器独立窗口组件 - 显示主程序详细日志"""
    
    # 信号
    log_cleared = Signal()
    
    def __init__(self, parent=None):
        """
        初始化日志监视器
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 设置为独立窗口
        self.setWindowTitle(tr('log_monitor_title'))
        self.setMinimumSize(700, 500)
        self.resize(900, 700)
        
        # 日志存储
        self.log_entries = []
        self.max_log_entries = 1000  # 最多保存 1000 条日志
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_label = QLabel(tr('log_monitor_title'))
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 日志级别过滤
        filter_layout = QHBoxLayout()
        filter_label = QLabel("日志级别过滤:")
        
        self.filter_debug = QCheckBox("调试")
        self.filter_debug.setChecked(True)
        self.filter_debug.stateChanged.connect(self.apply_filter)
        
        self.filter_info = QCheckBox("信息")
        self.filter_info.setChecked(True)
        self.filter_info.stateChanged.connect(self.apply_filter)
        
        self.filter_warning = QCheckBox("警告")
        self.filter_warning.setChecked(True)
        self.filter_warning.stateChanged.connect(self.apply_filter)
        
        self.filter_error = QCheckBox("错误")
        self.filter_error.setChecked(True)
        self.filter_error.stateChanged.connect(self.apply_filter)
        
        self.filter_comm = QCheckBox("通信")
        self.filter_comm.setChecked(True)
        self.filter_comm.stateChanged.connect(self.apply_filter)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_debug)
        filter_layout.addWidget(self.filter_info)
        filter_layout.addWidget(self.filter_warning)
        filter_layout.addWidget(self.filter_error)
        filter_layout.addWidget(self.filter_comm)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 日志显示区
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        self.display.setFont(QFont("Consolas", 9))
        self.display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                font-family: 'Consolas', 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.display)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.auto_scroll_check = QCheckBox(tr('auto_scroll'))
        self.auto_scroll_check.setChecked(True)
        
        self.clear_btn = QPushButton(tr('clear_btn'))
        self.clear_btn.clicked.connect(self.clear_display)
        
        self.export_btn = QPushButton("导出日志")
        self.export_btn.clicked.connect(self.export_logs)
        
        control_layout.addWidget(self.auto_scroll_check)
        control_layout.addStretch()
        control_layout.addWidget(self.export_btn)
        control_layout.addWidget(self.clear_btn)
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
    
    def add_log_entry(self, timestamp, level, message, log_type='info'):
        """
        添加日志条目
        
        Args:
            timestamp: 时间戳
            level: 日志级别字符串
            message: 日志内容
            log_type: 日志类型 ('debug', 'info', 'warning', 'error', 'comm')
        """
        # 存储日志
        entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'type': log_type
        }
        self.log_entries.append(entry)
        
        # 限制日志数量
        if len(self.log_entries) > self.max_log_entries:
            self.log_entries.pop(0)
        
        # 显示日志
        self._display_log_entry(entry)
    
    def _display_log_entry(self, entry):
        """显示单条日志"""
        # 检查过滤
        if not self._should_display(entry['type']):
            return
        
        # 设置颜色
        color_map = {
            'debug': '#888888',      # 灰色
            'info': '#00ff00',       # 绿色
            'warning': '#ffaa00',    # 橙色
            'error': '#ff0000',      # 红色
            'comm': '#00aaff',       # 蓝色
        }
        color = color_map.get(entry['type'], '#d4d4d4')
        
        # 格式化显示
        timestamp_str = entry['timestamp'].strftime('%H:%M:%S.%f')[:-3]  # 毫秒精度
        html_message = f'<span style="color:#666;">[{timestamp_str}]</span> <span style="color:{color};">[{entry["level"]}] {entry["message"]}</span>'
        self.display.append(html_message)
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            scrollbar = self.display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _should_display(self, log_type):
        """检查日志是否应该显示"""
        if log_type == 'debug' and not self.filter_debug.isChecked():
            return False
        if log_type == 'info' and not self.filter_info.isChecked():
            return False
        if log_type == 'warning' and not self.filter_warning.isChecked():
            return False
        if log_type == 'error' and not self.filter_error.isChecked():
            return False
        if log_type == 'comm' and not self.filter_comm.isChecked():
            return False
        return True
    
    def apply_filter(self):
        """应用过滤设置，刷新显示"""
        # 清空显示
        self.display.clear()
        
        # 重新显示所有日志
        for entry in self.log_entries:
            if self._should_display(entry['type']):
                self._display_log_entry(entry)
    
    def clear_display(self):
        """清空显示区"""
        self.log_entries.clear()
        self.display.clear()
        self.append_message("[日志已清空]", '#888888')
    
    def export_logs(self):
        """导出日志到文件"""
        from PySide6.QtWidgets import QFileDialog
        import os
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志文件",
            "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for entry in self.log_entries:
                        timestamp_str = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        f.write(f"[{timestamp_str}] [{entry['level']}] {entry['message']}\n")
                
                self.append_message(f"[日志已导出到：{os.path.basename(file_path)}]", '#00ff00')
            except Exception as e:
                self.append_message(f"[导出失败：{str(e)}]", '#ff0000')
    
    def append_message(self, message, color='#ffffff'):
        """添加消息到显示区"""
        timestamp = time.strftime('%H:%M:%S')
        html_message = f'<span style="color:#888;">[{timestamp}]</span> <span style="color:{color};">{message}</span>'
        self.display.append(html_message)
    
    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        event.accept()
