"""
实时串口监视器组件
用于显示串口通信数据
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel, 
                                QPushButton, QHBoxLayout, QCheckBox, QComboBox)
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
import serial
import time
from i18n import tr


class SerialMonitorWidget(QWidget):
    """串口监视器独立窗口组件 - 监控主程序已连接的串口"""
    
    # 信号
    data_received = Signal(str)
    data_sent = Signal(str)
    
    def __init__(self, serial_port=None, parent=None):
        """
        初始化串口监视器
        
        Args:
            serial_port: 已经打开的串口对象（从主程序传入）
            parent: 父窗口
        """
        super().__init__(parent)
        self.serial_port = serial_port  # 使用传入的串口对象
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_serial_data)
        self.is_monitoring = False
        
        # 设置为独立窗口
        self.setWindowTitle(tr('serial_monitor_title'))
        self.setMinimumSize(600, 400)
        self.resize(800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_label = QLabel(tr('serial_monitor_title'))
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 串口信息显示（只读）
        info_layout = QHBoxLayout()
        info_label = QLabel(tr('monitoring_port'))
        self.port_info_label = QLabel(tr('not_connected'))
        self.port_info_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
        
        info_layout.addWidget(info_label)
        info_layout.addWidget(self.port_info_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 数据显示区
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        self.display.setFont(QFont("Consolas", 9))
        self.display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
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
        
        self.start_btn = QPushButton(tr('start_monitoring'))
        self.start_btn.clicked.connect(self.toggle_monitoring)
        self.start_btn.setCheckable(True)
        
        control_layout.addWidget(self.auto_scroll_check)
        control_layout.addStretch()
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.start_btn)
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
    
    def set_serial_port(self, serial_port):
        """
        设置要监控的串口对象
        
        Args:
            serial_port: 已打开的串口对象
        """
        self.serial_port = serial_port
        if serial_port and serial_port.is_open:
            port_name = serial_port.port
            baudrate = serial_port.baudrate
            self.port_info_label.setText(f"{port_name} @ {baudrate}")
            self.port_info_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            print(f"[SerialMonitor] 开始监控串口：{port_name} @ {baudrate}")
        else:
            self.port_info_label.setText(tr('not_connected'))
            self.port_info_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """开始监控"""
        if not self.serial_port or not self.serial_port.is_open:
            self.append_message(f"[Error] {tr('not_connected')}", '#ff0000')
            return
        
        try:
            self.monitor_timer.start(50)  # 50ms 检查一次
            self.is_monitoring = True
            self.start_btn.setText(tr('stop_monitoring'))
            self.start_btn.setChecked(True)
            port_name = self.serial_port.port
            self.append_message(f"[Monitoring] {port_name}", '#00ff00')
            print(f"[SerialMonitor] 已开始监控：{port_name}")
        except Exception as e:
            self.append_message(f"[Error] {str(e)}", '#ff0000')
            self.is_monitoring = False
            self.start_btn.setChecked(False)
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitor_timer.stop()
        self.is_monitoring = False
        self.start_btn.setText(tr('start_monitoring'))
        self.start_btn.setChecked(False)
        
        # 注意：不关闭串口，因为这是主程序正在使用的串口
        if hasattr(self, 'serial_port') and self.serial_port:
            port_name = self.serial_port.port
            self.append_message(f"[Stopped monitoring] {port_name}", '#ffaa00')
    
    def check_serial_data(self):
        """检查串口数据"""
        if self.serial_port and self.serial_port.is_open:
            try:
                while self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    if data:
                        self.append_message(f"RX: {data.strip()}", '#00ff00')
                        self.data_received.emit(data)
            except Exception as e:
                self.append_message(f"[Read Error] {str(e)}", '#ff0000')
    
    def send_data(self, data):
        """发送数据到串口"""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(data.encode('utf-8'))
                self.append_message(f"TX: {data.strip()}", '#00aaff')
                self.data_sent.emit(data)
                return True
            except Exception as e:
                self.append_message(f"[Write Error] {str(e)}", '#ff0000')
        return False
    
    def append_message(self, message, color='#ffffff'):
        """添加消息到显示区"""
        timestamp = time.strftime('%H:%M:%S')
        html_message = f'<span style="color:#888;">[{timestamp}]</span> <span style="color:{color};">{message}</span>'
        self.display.append(html_message)
        
        if self.auto_scroll_check.isChecked():
            scrollbar = self.display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clear_display(self):
        """清空显示区"""
        self.display.clear()
        self.append_message("[Display cleared]", '#888888')
    
    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        self.stop_monitoring()
        event.accept()
