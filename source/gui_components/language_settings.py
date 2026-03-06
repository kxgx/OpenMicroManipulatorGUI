"""
语言设置对话框
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QComboBox, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from i18n import get_translator, tr


class LanguageSettingsDialog(QDialog):
    """语言设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translator = get_translator()
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle(tr('dlg_title_settings'))
        self.setModal(True)
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 语言选择
        lang_layout = QHBoxLayout()
        lang_label = QLabel(tr('language_label'))
        self.lang_combo = QComboBox()
        
        # 添加可用语言
        languages = self.translator.get_available_languages()
        for code, name in languages.items():
            self.lang_combo.addItem(name, code)
        
        # 设置当前语言
        current_lang = self.translator.get_current_language()
        index = self.lang_combo.findData(current_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
        
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)
        
        # 说明文字
        info_label = QLabel(tr('language_restart_info'))
        info_label.setWordWrap(True)
        info_label.setStyleSheet('color: gray; font-size: 10px;')
        layout.addWidget(info_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.ok_btn = QPushButton(tr('btn_ok'))
        self.ok_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton(tr('btn_cancel'))
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_selected_language(self):
        """获取选择的语言代码"""
        return self.lang_combo.currentData()
    
    def accept(self):
        """确认按钮处理"""
        selected_lang = self.get_selected_language()
        current_lang = self.translator.get_current_language()
        
        if selected_lang != current_lang:
            # 语言已更改
            reply = QMessageBox.question(
                self,
                tr('dlg_title_warning'),
                tr('msg_language_change'),
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.translator.set_language(selected_lang)
                super().accept()
                # 触发界面更新
                self.parent().update_ui_language()
        else:
            super().accept()
