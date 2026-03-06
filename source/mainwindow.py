# --------------------------------------------------------------------------------------
# Project: OpenMicroManipulator
# License: MIT (see LICENSE file for full description)
#          All text in here must be included in any redistribution.
# Author:  M. S. (diffraction limited)
# --------------------------------------------------------------------------------------

import os
import json
import time

# 性能优化：延迟加载大模块
from optimization import OptimizedImports, LazyLoader

# 初始化并行导入（在后台加载 numpy, cv2, PySide6）
OptimizedImports.initialize()

# 立即需要的轻量级导入
from hardware.open_micro_stage_api import OpenMicroStageInterface
from image_processing.image_point_tracker import ImagePointTracker
from optical_alignment import OpticalAlignment
from gui_components.image_viewer_widget import ImageViewerWidget
from gui_components.realtime_controller_widget import RealtimeControllerWidget
from gui_components.language_settings import LanguageSettingsDialog
from gui_components.serial_monitor import LogMonitorWidget
from gcode_runner import GCodeRunner

# 配置管理
from app_config import get_config, save_config

# 多语言支持
from i18n import get_translator, tr

# 日志管理器
import log_manager

# 重型模块使用延迟加载（首次使用时才导入）
cv2 = LazyLoader('cv2')  # OpenCV - 约 200ms
np_lazy = LazyLoader('numpy')  # NumPy - 约 50ms

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QMessageBox, QButtonGroup,
    QDoubleSpinBox, QFileDialog, QMainWindow, QFrame, QSpacerItem, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QFont

class DeviceControlMainWindow(QMainWindow):
    def __init__(self, oms: OpenMicroStageInterface, camera):
        super().__init__()
        # Data and State
        self.oms = oms
        self.camera = camera
        self.gcode_runner = None

        self.last_frame = None
        self.draw_buffer = None
        self.current_pos = [0, 0, 0]
        self.step_sizes = [1.0, 0.1, 0.01, 0.001, 0.0001]
        self.feedrates = [50.0, 5.0, 5.0, 1.0, 0.1]
        self.step_size_idx = 1
        self.waypoints = []
        self.waypoint_idx = 1000000

        # Trackers
        self.image_point_tracker = ImagePointTracker()
        
        # 翻译器
        self.translator = get_translator()
        
        # 加载配置
        self.config = get_config()
        
        # 应用保存的语言设置
        saved_language = self.config.language
        if saved_language:
            self.translator.set_language(saved_language)
        
        # 初始化日志回调
        self._init_log_callback()
        
        # 等待关键模块加载完成（最多等待 5 秒）
        start_time = time.time()
        OptimizedImports.wait_loading(timeout=5.0)
        load_time = time.time() - start_time
        log_manager.info(f"[启动优化] 模块加载完成，耗时：{load_time*1000:.0f}ms")
        
        self.init_ui()

        if self.oms.is_connected():
            self.current_pos = list(self.oms.read_current_position(True))
            self.oms.set_max_acceleration(self.accel_spinbox.value(), 5000)
    
    def _init_log_callback(self):
        """初始化日志回调，将日志发送到日志监视器"""
        def log_callback(timestamp, level, message):
            # 确定日志类型
            log_type_map = {
                'DEBUG': 'debug',
                'INFO': 'info',
                'WARNING': 'warning',
                'ERROR': 'error',
                'CRITICAL': 'error',
                'COMM': 'comm'
            }
            log_type = log_type_map.get(level, 'info')
            
            # 发送到日志监视器
            if hasattr(self, 'log_monitor') and self.log_monitor:
                from datetime import datetime
                try:
                    ts = datetime.strptime(timestamp, '%H:%M:%S.%f')
                except:
                    ts = datetime.now()
                self.log_monitor.add_log_entry(ts, level, message, log_type)
        
        # 注册回调
        log_manager.add_callback(log_callback)

    def init_ui(self):
        # 设置窗口标题（使用翻译）
        self.setWindowTitle(tr('window_title'))
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
            
        # 创建菜单栏
        self.create_menu_bar()
    
        # Central Widget and Main Horizontal Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_h_layout = QHBoxLayout(central_widget)

        # --- LEFT COLUMN: Controls ---
        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        main_layout = QVBoxLayout(left_panel)  # This replaces your old main_layout

        self.video_viewer = ImageViewerWidget()

        font = QFont("Noto Sans", 12)

        # Movement grid layout
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.create_button(tr('axis_y_minus'), lambda: self.move_axis(1, -1), font), 0, 1)
        grid.addWidget(self.create_button(tr('axis_z_plus'), lambda: self.move_axis(2, +1), font), 0, 3)
        grid.addWidget(self.create_button(tr('axis_x_minus'), lambda: self.move_axis(0, -1), font), 1, 0)

        center_label = QLabel("•")
        center_label.setFont(QFont("Arial", 30))
        center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(center_label, 1, 1)

        grid.addWidget(self.create_button(tr('axis_x_plus'), lambda: self.move_axis(0, +1), font), 1, 2)
        grid.addWidget(self.create_button(tr('axis_y_plus'), lambda: self.move_axis(1, +1), font), 2, 1)
        grid.addWidget(self.create_button(tr('axis_z_minus'), lambda: self.move_axis(2, -1), font), 2, 3)

        main_layout.addLayout(grid)

        # Step size section
        main_layout.addSpacing(25)
        main_layout.addWidget(self.create_label(tr('step_size_label')))

        step_layout = QHBoxLayout()
        self.step_button_group = QButtonGroup()
        self.step_button_group.setExclusive(True)
        for i, val in enumerate(self.step_sizes):
            btn = self.create_button(str(val * 1000), lambda checked=False, idx=i: self.set_step_size(idx), font)
            btn.setCheckable(True)
            if i == self.step_size_idx: btn.setChecked(True)
            self.step_button_group.addButton(btn, i)
            step_layout.addWidget(btn)

        main_layout.addLayout(step_layout)

        # acceleration
        accel_layout, self.accel_spinbox = self.create_spinbox(
            label_text=tr('acceleration_label'),
            min_val=0.01,
            max_val=1000.0,
            step=1,
            default=30.00,
            decimals=2,
            callback=lambda: self.oms.set_max_acceleration(self.accel_spinbox.value(), 5000)
        )
        main_layout.addLayout(accel_layout)

        # Waypoint controls
        main_layout.addSpacing(25)
        self.waypoint_info_label = self.create_label(tr('path_control_label'))
        main_layout.addWidget(self.waypoint_info_label)

        wp_layout = QGridLayout()
        wp_layout.addWidget(self.create_button(tr('add_waypoint_btn'), self.add_waypoint, font), 0, 0)
        wp_layout.addWidget(self.create_button(tr('clear_waypoints_btn'), self.clear_waypoints, font), 0, 1)
        wp_layout.addWidget(self.create_button(tr('run_path_btn'), self.run_path, font), 1, 0)
        wp_layout.addWidget(self.create_button(tr('save_path_btn'), self.save_path, font), 1, 1)
        main_layout.addLayout(wp_layout)

        # self.waypoint_info_label = self.create_label("", font_size=10)
        # main_layout.addWidget(self.waypoint_info_label)
        self.update_waypoint_info()

        # GCode controls
        main_layout.addSpacing(25)
        main_layout.addWidget(self.create_label(tr('advanced_label')))

        #        main_layout.addSpacing(10)
        advanced_frame = QWidget()
        advanced_frame.setObjectName("AdvancedFrame")

        layout = QGridLayout(advanced_frame)
        layout.setContentsMargins(QMargins(0, 0, 0, 0))

        # realtime control widget
        self.realtime_control_widget = RealtimeControllerWidget(self.video_viewer.viewport(), self.oms)
        layout.addWidget(self.realtime_control_widget, 0, 0, 1, 2)
        layout.addItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed), 1, 0, 1, 2)
        self.realtime_control_widget.stop_control_signal.connect(self.on_stop_realtime_control)

        self.run_gcode_button = self.create_button(tr('run_gcode_btn'), self.run_gcode_from_file, font)
        self.run_gcode_button.setCheckable(True)
        layout.addWidget(self.run_gcode_button, 2, 0, 1, 2)
        layout.addItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed), 3, 0, 1, 2)

        layout.addWidget(self.create_button(tr('align_3point_btn'), self.run_3point_alignment, font), 4, 0)
        layout.addWidget(self.create_button(tr('set_origin_btn'), lambda: self.set_origin(), font), 4, 1)
        layout.addWidget(self.create_button(tr('set_tracking_point_btn'), self.set_tracking_point, font), 5, 0)
        layout.addWidget(self.create_button(tr('clear_btn'), self.clear_draw_buffer, font), 5, 1)
        layout.addWidget(self.create_button(tr('load_transform_btn'), self.load_transform, font), 6, 0)
        layout.addWidget(self.create_button(tr('save_transform_btn'), self.save_transform, font), 6, 1)
        layout.addWidget(self.create_button(tr('fiber_alignment_btn'), self.run_fiber_alignment, font), 7, 0)
        layout.addWidget(self.create_button(tr('home_btn'), self.home, font), 7, 1)
        main_layout.addWidget(advanced_frame)

        # vertical stretch
        main_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # --- RIGHT COLUMN: Video Display ---
        self.video_viewer.setMinimumWidth(600)
        self.video_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_viewer.setStyleSheet("background-color: black; border: 2px solid #444;")

        # Add components to the horizontal layout
        main_h_layout.addWidget(left_panel)
        main_h_layout.addWidget(self.video_viewer, stretch=1)

        self.set_stylesheet()

    def setup_movement_grid(self):
        font = QFont("Noto Sans", 12)
        grid = QGridLayout()
        grid.addWidget(self.create_button(tr('axis_y_minus'), lambda: self.move_axis(1, -1), font), 0, 1)
        grid.addWidget(self.create_button(tr('axis_z_plus'), lambda: self.move_axis(2, +1), font), 0, 3)
        grid.addWidget(self.create_button(tr('axis_x_minus'), lambda: self.move_axis(0, -1), font), 1, 0)

        center_label = QLabel("•")
        center_label.setFont(QFont("Arial", 30))
        center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(center_label, 1, 1)

        grid.addWidget(self.create_button(tr('axis_x_plus'), lambda: self.move_axis(0, +1), font), 1, 2)
        grid.addWidget(self.create_button(tr('axis_y_plus'), lambda: self.move_axis(1, +1), font), 2, 1)
        grid.addWidget(self.create_button(tr('axis_z_minus'), lambda: self.move_axis(2, -1), font), 2, 3)
        self.control_layout.addLayout(grid)

    def setup_step_size_ui(self):
        self.control_layout.addSpacing(20)
        self.control_layout.addWidget(self.create_label(tr('step_size_label')))
        step_layout = QHBoxLayout()
        self.step_button_group = QButtonGroup(self)
        for i, val in enumerate(self.step_sizes):
            btn = self.create_button(str(val * 1000), lambda checked=False, idx=i: self.set_step_size(idx), QFont())
            btn.setCheckable(True)
            if i == self.step_size_idx: btn.setChecked(True)
            self.step_button_group.addButton(btn, i)
            step_layout.addWidget(btn)
        self.control_layout.addLayout(step_layout)

    @staticmethod
    def create_label(text, alignment=Qt.AlignmentFlag.AlignLeft, font_size=12):
        label = QLabel(text)
        label.setAlignment(alignment)
        label.setFont(QFont("Noto Sans", font_size))
        return label

    @staticmethod
    def create_button(label, slot, font):
        btn = QPushButton(label)
        # btn.setFont(font)
        btn.setMinimumSize(60, 40)
        btn.setMaximumHeight(40)
        btn.clicked.connect(slot)
        #        btn.setStyleSheet()
        return btn

    def set_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b; color: white;
            }

            QPushButton {
                background-color: #2d5291;
                color: white;
                border: 1px solid #202020;
                border-radius: 3px;
                padding: 8px;
            }

            QWidget#AdvancedFrame QPushButton { background-color: #4d5291; }
            QWidget#AdvancedFrame QPushButton:hover { background-color: #5b72d1; }
            QWidget#AdvancedFrame QPushButton:pressed { background-color: #32a877; }
            QWidget#AdvancedFrame QPushButton:checked { background-color: #32a877; }

            QPushButton:hover {
                background-color: #3b72d1;
            }
            QPushButton:checked {
                background-color: #32a877;
            }
            QPushButton:pressed {
                background-color: #32a877;
            }
        """)

    @staticmethod
    def create_spinbox(label_text, min_val, max_val, step, default, decimals, callback):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSingleStep(step)
        spinbox.setValue(default)
        spinbox.setDecimals(decimals)
        spinbox.editingFinished.connect(callback)

        layout.addWidget(label)
        layout.addWidget(spinbox)

        return layout, spinbox

    def run_fiber_alignment(self):
        return
        aligner = OpticalAlignment(self.oms, self.camera)
        pos, _ = aligner.optimize()
        self.camera.start_grabbing(False)
        self.current_pos = pos

    def on_stop_realtime_control(self):
        self.current_pos[:] = self.oms.read_current_position(True)

    def home(self):
        self.oms.home()
        if self.oms.is_connected():
            self.current_pos = list(self.oms.read_current_position(True))

    def move_axis(self, axis, direction):
        flipped = (1, 1, 1)
        d = self.step_sizes[self.step_size_idx]
        self.current_pos[axis] += direction * d * flipped[axis]
        self.current_pos[axis] = max(min(self.current_pos[axis], 10), -10)
        self.oms.move_to(*self.current_pos, self.feedrates[self.step_size_idx])

    def add_waypoint(self):
        if self.realtime_control_widget.is_running():
            self.current_pos[:] = self.realtime_control_widget.get_current_pose()
            # self.current_pos[:] = self.oms.read_current_position(True)

        self.waypoints.append([self.current_pos.copy(), self.feedrates[self.step_size_idx]])
        self.update_waypoint_info()

    def run_path(self):
        self.waypoint_idx = 0

    def save_path(self):
        if len(self.waypoints) <= 0:
            QMessageBox.critical(self, tr('save_error_title'), tr('waypoint_list_empty'))
            return

        path, _ = QFileDialog.getSaveFileName(
            self, tr('save_path_title'), "",
            f"{tr('gcode_files_filter')};;{tr('text_files_filter')};;{tr('all_files_filter')}"
        )

        if not path:
            return  # user cancelled

        try:
            with open(path, "w") as f:
                # Optional header
                f.write("; Generated by Open Micro Manipulator Controller\n")
                f.write("G90 ; absolute positioning\n\n")

                for waypoint in self.waypoints:
                    (x, y, z), feedrate = waypoint

                    f.write(f"G0 X{x:.10f} Y{y:.10f} Z{z:.10f} F{feedrate * 60:.3f}\n")
                    f.write(f"G4 S{0.1:.6f}\n")

                # Optional footer
                f.write("\n; End of file\n")

        except Exception as e:
            QMessageBox.critical(self, tr('save_error_title'), f"{tr('save_gcode_failed')}\n{e}")

    def set_origin(self):
        self.current_pos[:] = self.oms.read_current_position(True)
        t = self.oms.get_workspace_transform()
        t[0, 3] += self.current_pos[0]
        t[1, 3] += self.current_pos[1]
        t[2, 3] += self.current_pos[2]
        self.oms.set_workspace_transform(t)
        self.current_pos = [0, 0, 0]
        self.oms.move_to(0, 0, 0, self.feedrates[self.step_size_idx])

    def clear_waypoints(self):
        self.waypoints.clear()
        self.update_waypoint_info()

    def update_waypoint_info(self):
        waypoints_count = len(self.waypoints)
        label_text = f"{tr('path_control_label')}  [ {waypoints_count} {tr('waypoints_unit')} ]"
        self.waypoint_info_label.setText(label_text)

    def set_step_size(self, index):
        self.step_size_idx = index

    def update_controller(self, frame, vis_image, pixel_per_mm):
        if self.waypoint_idx <= len(self.waypoints) and len(self.waypoints) > 0:
            self.current_pos[:], f = self.waypoints[self.waypoint_idx % len(self.waypoints)]
            self.oms.move_to(*self.current_pos, f)
            self.oms.dwell(0.1, False)
            self.waypoint_idx += 1
        else:
            self.waypoint_idx = 1000000

        px0, py0 = self.image_point_tracker.prev_pos
        px, py = self.image_point_tracker.update(frame)
        cv2.circle(vis_image, (px, py), 4, (0, 0, 255), thickness=-1)

        if self.draw_buffer is None:
            # 使用延迟加载的 numpy
            np = OptimizedImports.get_numpy()
            self.draw_buffer = np.zeros_like(frame)
        else:
            # cv2.circle(self.draw_buffer, (px, py), radius=0, color=(255,255,255), thickness=1)
            cv2.line(self.draw_buffer, (px0, py0), (px, py), color=(255, 255, 255), thickness=1)
            mask = self.draw_buffer[:, :, 0] != 0
            np = OptimizedImports.get_numpy()
            vis_image[mask, :] = np.array((0, 255, 100), dtype=np.uint8)
            # cv2.subtract(vis_image, self.draw_buffer, vis_image)

        self.video_viewer.set_image(vis_image, pixel_per_mm=pixel_per_mm)

        self.last_frame = frame
        return vis_image

    def set_tracking_point(self):
        if self.last_frame is None:
            return

        self.image_point_tracker.set_track_point(self.last_frame,
                                                 self.last_frame.shape[1] // 2,
                                                 self.last_frame.shape[0] // 2)

    def clear_draw_buffer(self):
        if self.draw_buffer is not None:
            self.draw_buffer = None
            self.image_point_tracker.reset()

    def run_gcode_from_file(self, checked):
        if checked:
            path, _ = QFileDialog.getOpenFileName(self, "Open G-code File",
                                                  "", "G-code Files (*.g *.gcode);;Text Files (*.txt);;All Files (*.*)")

            if not path:
                return
            try:
                gcode = open(path, 'r').read()
            except Exception as e:
                QMessageBox.critical(self, tr('error_title'), f"{tr('open_file_failed')}\n{e}")
                return

            self.gcode_runner = GCodeRunner(gcode, self.oms, max_feedrate=0.5)

            def on_finished():
                self.gcode_runner = None
                self.run_gcode_button.blockSignals(True)
                self.run_gcode_button.setChecked(False)
                self.run_gcode_button.blockSignals(False)

            def on_iteration_finished():
                # self.draw_buffer = None
                pass

            # start gcode runner here
            self.gcode_runner.run(on_finished, on_iteration_finished, loop_playback=False)
        elif self.gcode_runner is not None:
            self.gcode_runner.stop()

    def run_3point_alignment(self):
        if len(self.waypoints) != 3:
            QMessageBox.critical(self, tr('error_title'), tr('need_3_waypoints'))
            return

        old_workspace_transform = self.oms.get_workspace_transform()

        p0 = np.array(self.waypoints[0][0])
        p1 = np.array(self.waypoints[1][0])
        p2 = np.array(self.waypoints[2][0])

        # Step 1: Compute Z-axis (normal to the plane)
        v1 = p1 - p0
        v2 = p2 - p0
        z_axis = np.cross(v1, v2)
        if z_axis[2] < 0.0:
            z_axis = -z_axis
        z_axis /= np.linalg.norm(z_axis)

        # Step 2: Project global X-axis onto the plane to get the local X-axis
        global_x = np.array([1.0, 0.0, 0.0])
        x_proj = global_x - np.dot(global_x, z_axis) * z_axis
        x_axis = x_proj / np.linalg.norm(x_proj)

        # Step 3: Compute Y-axis to complete right-handed system
        y_axis = np.cross(z_axis, x_axis)
        y_axis /= np.linalg.norm(y_axis)

        # Step 4: Build 4x4 transform matrix (from local plane frame to base frame)
        T = np.eye(4)
        T[:3, 0] = x_axis
        T[:3, 1] = y_axis
        T[:3, 2] = z_axis
        T[:3, 3] = p0

        # Step 5: set coordinate system
        self.oms.set_workspace_transform(T @ old_workspace_transform)
        QMessageBox.information(self, tr('alignment_complete_title'), tr('alignment_complete_msg'))

        self.oms.move_to(0, 0, 0, self.feedrates[self.step_size_idx])
        self.current_pos = [0, 0, 0]

        # self.save_transform(ask=False)

    def load_transform(self):
        data = json.load(open("transform.json"))
        T = np.array(data)
        self.oms.set_workspace_transform(T)
        self.oms.move_to(0, 0, 0, self.feedrates[self.step_size_idx])
        self.current_pos = [0, 0, 0]

    def save_transform(self, pressed=True, ask=True):
        if ask:
            confirmed = QMessageBox.question(None, tr('save_transform_title'), tr('confirm_save_transform'),
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
            if not confirmed: return

        T = self.oms.get_workspace_transform()
        json.dump(T.tolist(), open("transform.json", "w"))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_A:
            self.move_axis(0, -1)
        elif event.key() == Qt.Key.Key_D:
            self.move_axis(0, +1)
        elif event.key() == Qt.Key.Key_W:
            self.move_axis(1, -1)
        elif event.key() == Qt.Key.Key_S:
            self.move_axis(1, +1)

    # ==================== 多语言支持 ====================
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 工具菜单
        tools_menu = menubar.addMenu(tr('menu_tools'))
        
        # 语言设置动作
        lang_action = tools_menu.addAction(tr('action_language_settings'))
        lang_action.triggered.connect(self.open_language_settings)
        
        # 日志监视器动作
        log_action = tools_menu.addAction(tr('action_log_monitor'))
        log_action.triggered.connect(self.show_log_monitor)
        
        # 关于菜单
        help_menu = menubar.addMenu(tr('menu_help'))
        about_action = help_menu.addAction(tr('action_about'))
        about_action.triggered.connect(self.show_about)
    
    def open_language_settings(self):
        """打开语言设置对话框"""
        dialog = LanguageSettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 语言已更改，刷新界面
            self.update_ui_language()
            # 保存语言设置
            self.config.language = self.translator.current_language
            save_config()
    
    def show_log_monitor(self):
        """显示日志监视器（独立窗口）"""
        if not hasattr(self, 'log_monitor') or self.log_monitor is None:
            # 创建新的日志监视器窗口
            self.log_monitor = LogMonitorWidget()
        
        # 显示并激活窗口
        self.log_monitor.showNormal()  # 以正常窗口模式显示
        self.log_monitor.raise_()      # 置顶
        self.log_monitor.activateWindow()  # 激活窗口
    
    def update_ui_language(self):
        """更新界面语言"""
        # 更新窗口标题
        self.setWindowTitle(tr('window_title'))
        
        # 更新菜单栏
        for menu in self.menuBar().children():
            if hasattr(menu, 'setTitle'):
                if menu.title() == tr('menu_tools') or 'Tools' in menu.title():
                    menu.setTitle(tr('menu_tools'))
                elif menu.title() == tr('menu_help') or 'Help' in menu.title():
                    menu.setTitle(tr('menu_help'))
        
        # 触发整个界面的样式表更新（可选）
        self.setStyleSheet(self.styleSheet())
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            tr('dlg_title_about'),
            f"<h2>OpenMicroManipulator</h2>"
            f"<p>{tr('about_version')} v0.2.0</p>"
            f"<p>{tr('about_description')}</p>"
            f"<p>{tr('about_license')}</p>"
        )
    
    def closeEvent(self, event):
        """关闭窗口时保存配置"""
        # 保存窗口大小和位置
        self.config.update_window_config(
            self.width(),
            self.height(),
            self.x(),
            self.y()
        )
        
        # 保存当前设置
        save_config()
        print("[Config] 配置已自动保存")
        
        # 停止串口监控并关闭窗口
        if hasattr(self, 'serial_monitor') and self.serial_monitor:
            self.serial_monitor.stop_monitoring()
            self.serial_monitor.close()
            self.serial_monitor = None
        
        event.accept()
    
    # ==================== 键盘事件 ====================
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_A:
            self.move_axis(0, -1)
        elif event.key() == Qt.Key.Key_D:
            self.move_axis(0, +1)
        elif event.key() == Qt.Key.Key_W:
            self.move_axis(1, -1)
        elif event.key() == Qt.Key.Key_S:
            self.move_axis(1, +1)
        elif event.key() == Qt.Key.Key_R:
            self.add_waypoint()
        else:
            super().keyPressEvent(event)