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
    """串口监视器独立窗口组件"""
    
    # 信号
    data_received = Signal(str)
    data_sent = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
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
        
        # 串口选择
        port_layout = QHBoxLayout()
        port_label = QLabel(tr('serial_port_label'))
        self.port_combo = QComboBox()
        self.refresh_ports()
        
        refresh_btn = QPushButton(tr('refresh_btn'))
        refresh_btn.clicked.connect(self.refresh_ports)
        refresh_btn.setFixedWidth(60)
        
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(refresh_btn)
        layout.addLayout(port_layout)
        
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
    
    def refresh_ports(self):
        """刷新可用串口列表"""
        self.port_combo.clear()
        try:
            from serial.tools.list_ports import comports
            ports = comports()
            for port in ports:
                self.port_combo.addItem(f"{port.device} - {port.description}")
        except Exception as e:
            print(f"[SerialMonitor] 获取串口列表失败：{e}")
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """开始监控"""
        port_name = self.port_combo.currentText().split(' - ')[0]
        
        try:
            self.serial_port = serial.Serial(port_name, timeout=0.1)
            self.monitor_timer.start(50)  # 50ms 检查一次
            self.is_monitoring = True
            self.start_btn.setText(tr('stop_monitoring'))
            self.start_btn.setChecked(True)
            self.append_message(f"[Connected] {port_name}", '#00ff00')
            print(f"[SerialMonitor] 已开始监控：{port_name}")
        except Exception as e:
            self.append_message(f"[Error] {str(e)}", '#ff0000')
            self.is_monitoring = False
            self.start_btn.setChecked(False)
    
    def stop_monitoring(self):
        """停止监控"""
        if self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
        
        self.monitor_timer.stop()
        self.is_monitoring = False
        self.start_btn.setText(tr('start_monitoring'))
        self.start_btn.setChecked(False)
        
        if hasattr(self, 'serial_port') and self.serial_port:
            port_name = self.serial_port.port
            self.append_message(f"[Disconnected] {port_name}", '#ffaa00')
    
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
