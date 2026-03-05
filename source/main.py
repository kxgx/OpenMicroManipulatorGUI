# --------------------------------------------------------------------------------------
# Project: OpenMicroManipulator
# License: MIT (see LICENSE file for full description)
#          All text in here must be included in any redistribution.
# Author:  M. S. (diffraction limited)
# --------------------------------------------------------------------------------------

import os
import sys

# Disable scaling
os.environ['QT_SCALE_FACTOR'] = '1'
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
os.environ['GDK_SCALE'] = '1'
os.environ['GDK_DPI_SCALE'] = '1'

# Enable Qt quick start
os.environ['QT_QPA_PLATFORM'] = 'windows:dpiawareness=0'

from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QListWidget, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QFont

import serial
import serial.tools.list_ports

# Lazy imports - only load when needed
def import_cv2():
    import cv2
    return cv2

def import_hardware():
    from hardware.open_micro_stage_api import OpenMicroStageInterface
    from mainwindow import DeviceControlMainWindow
    from hardware.camera_opencv import OpenCVCamera
    from hardware.camera_basler import BaslerCamera
    return OpenMicroStageInterface, DeviceControlMainWindow, OpenCVCamera, BaslerCamera


class DeviceScanner(QThread):
    """Background thread for scanning devices"""
    scan_complete = Signal(list, list)
    
    def run(self):
        cameras = []
        ports = []
        
        # Scan cameras - optimized
        try:
            cv2 = import_cv2()
            # Only check first 3 indices for speed
            for i in range(3):
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        cameras.append(('OpenCV', i))
                    cap.release()
        except Exception as e:
            pass
        
        # Check Basler camera
        try:
            from pypylon import pylon
            tl_factory = pylon.TlFactory.GetInstance()
            devices = tl_factory.EnumerateDevices()
            if devices:
                cameras.append(('Basler', None))
        except Exception:
            pass
        
        # Scan serial ports - cached
        try:
            port_list = serial.tools.list_ports.comports()
            ports = [(port.device, port.description) for port in port_list]
        except Exception:
            pass
        
        self.scan_complete.emit(cameras, ports)


class StartupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Open Micro Manipulator - Setup")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        
        self.selected_camera = None
        self.selected_port = None
        self.scanner_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Loading label
        self.loading_label = QLabel("Scanning for devices...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setFont(QFont("Noto Sans", 10))
        layout.addWidget(self.loading_label)
        
        # Camera selection
        camera_label = QLabel("Select Camera:")
        camera_label.setFont(QFont("Noto Sans", 12))
        layout.addWidget(camera_label)
        
        self.camera_list = QListWidget()
        self.camera_list.setStyleSheet("background-color: #3b3b3b; border: 1px solid #555;")
        layout.addWidget(self.camera_list)
        
        # Serial port selection
        port_label = QLabel("Select Serial Port (OMS):")
        port_label.setFont(QFont("Noto Sans", 12))
        layout.addWidget(port_label)
        
        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet("background-color: #3b3b3b; border: 1px solid #555; padding: 5px;")
        layout.addWidget(self.port_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.start_scan)
        self.refresh_btn.setStyleSheet("background-color: #4d5291; padding: 8px;")
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.accept)
        self.start_btn.setStyleSheet("background-color: #32a877; padding: 8px;")
        button_layout.addWidget(self.start_btn)
        
        layout.addLayout(button_layout)
        
        # Start background scanning
        self.start_scan()
    
    def start_scan(self):
        """Start background device scanning"""
        self.loading_label.setText("Scanning for devices...")
        self.camera_list.clear()
        self.port_combo.clear()
        self.start_btn.setEnabled(False)
        
        # Start scanner thread
        self.scanner_thread = DeviceScanner()
        self.scanner_thread.scan_complete.connect(self.on_scan_complete)
        self.scanner_thread.start()
    
    def on_scan_complete(self, cameras, ports):
        """Handle scan results"""
        self.loading_label.setText("Device Selection:")
        
        # Populate cameras
        for cam_type, idx in cameras:
            if cam_type == 'OpenCV':
                self.camera_list.addItem(f"OpenCV Camera (index {idx})")
            elif cam_type == 'Basler':
                self.camera_list.addItem("Basler Camera")
        
        # Populate ports
        for device, description in ports:
            self.port_combo.addItem(f"{device} - {description}", userData=device)
        
        # Auto-select
        if self.camera_list.count() > 0:
            self.camera_list.setCurrentRow(0)
        
        for i in range(self.port_combo.count()):
            text = self.port_combo.itemText(i).upper()
            if 'COM' in text or 'USB' in text or 'SERIAL' in text:
                self.port_combo.setCurrentIndex(i)
                break
        
        self.start_btn.setEnabled(True)
    
    def accept(self):
        """Handle start button click"""
        # Get selected camera
        current_camera_item = self.camera_list.currentItem()
        if not current_camera_item:
            QMessageBox.warning(self, "Warning", "Please select a camera!")
            return
        
        camera_text = current_camera_item.text()
        if camera_text.startswith("OpenCV"):
            import re
            match = re.search(r'\(index (\d+)\)', camera_text)
            if match:
                self.selected_camera = ('opencv', int(match.group(1)))
        elif camera_text == "Basler Camera":
            self.selected_camera = ('basler', None)
        
        # Get selected port
        port_data = self.port_combo.currentData()
        if port_data:
            self.selected_port = port_data
        else:
            QMessageBox.warning(self, "Warning", "Please select a serial port!")
            return
        
        super().accept()


def main():
    app = QApplication(sys.argv)
    
    # Show splash screen
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(Qt.GlobalColor.darkBlue)
    splash = QSplashScreen(splash_pix)
    splash.showMessage(
        "Open Micro Manipulator\n\nStarting...",
        Qt.AlignmentFlag.AlignCenter,
        Qt.GlobalColor.white
    )
    splash.setFont(QFont("Arial", 16))
    splash.show()
    app.processEvents()
    
    # Show startup dialog
    dialog = StartupDialog()
    splash.finish(dialog)
    dialog.raise_()
    
    if dialog.exec() != QDialog.Accepted:
        return
    
    camera_type, camera_idx = dialog.selected_camera
    port = dialog.selected_port
    
    # Lazy load hardware modules
    OpenMicroStageInterface, DeviceControlMainWindow, OpenCVCamera, BaslerCamera = import_hardware()
    
    # Create interface and connect
    oms = OpenMicroStageInterface(show_communication=False, show_log_messages=True)
    oms.connect(port)
    
    # Setup camera
    if camera_type == 'basler':
        camera = BaslerCamera()
        # camera.set_exposure_time(16000//32)
        # camera.set_gain(6.0)
    else:
        camera = OpenCVCamera(camera_index=camera_idx)
    
    # create the Qt app and GUI
    gui = DeviceControlMainWindow(oms, camera)
    gui.show()
    
    def process_frame(frame):
        #frame = cv2.flip(frame, 1)
        
        # Convert grayscale to BGR if needed
        if len(frame.shape) == 2 or frame.shape[2] == 1:
            vis_img = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        else:
            vis_img = frame.copy()
        
        gui.update_controller(frame, vis_img, pixel_per_mm=2000.0)
        
        app.processEvents()
        a = gui.isVisible()
        return a
    
    if camera.is_connected():
        # Run the camera loop (which also runs qt event loop)
        camera.grab_loop(callback=process_frame)
    else:
        QMessageBox.warning(None, "Warning", f"Failed to connect to camera: {camera_type}")
        # Start the Qt event loop anyway
        app.exec()

if __name__ == "__main__":
    main()