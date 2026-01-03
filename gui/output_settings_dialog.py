"""
输出设置对话框
包含输出前后缀、格式、质量、强制输出尺寸和宽高比设置
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QComboBox, QCheckBox, QPushButton, QGroupBox, QLabel, QSpinBox,
    QDoubleSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.init import config


class OutputSettingsDialog(QDialog):
    """输出设置对话框"""
    
    # 信号：当设置改变时发出
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.current_settings = current_settings or {}
        self.setup_ui()
        self.load_current_settings()
        self.setWindowTitle("输出设置")
        self.resize(400, 500)
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("输出设置")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 文件名设置分组
        filename_group = QGroupBox("文件名设置")
        filename_layout = QFormLayout()
        
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("例如: Img_")
        filename_layout.addRow("前缀:", self.prefix_edit)
        
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText("留空则使用时间戳")
        filename_layout.addRow("后缀:", self.suffix_edit)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPG", "PNG", "TIFF", "WEBP"])
        filename_layout.addRow("格式:", self.format_combo)
        
        # 质量设置
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        self.quality_spin.setSuffix("%")
        filename_layout.addRow("质量:", self.quality_spin)
        
        filename_group.setLayout(filename_layout)
        layout.addWidget(filename_group)
        
        # 尺寸设置分组
        size_group = QGroupBox("输出尺寸设置")
        size_layout = QFormLayout()
        
        # 强制输出尺寸复选框
        self.force_size_checkbox = QCheckBox("强制输出尺寸")
        self.force_size_checkbox.stateChanged.connect(self.on_force_size_changed)
        size_layout.addRow(self.force_size_checkbox)
        
        # 自动旋转复选框（当方向不匹配时自动旋转）
        self.auto_rotate_checkbox = QCheckBox("自动旋转以匹配方向")
        self.auto_rotate_checkbox.setToolTip("当竖屏图片需要输出为横屏（或反之）时自动旋转图片")
        self.auto_rotate_checkbox.setChecked(True)  # 默认启用
        size_layout.addRow(self.auto_rotate_checkbox)
        
        # 像素尺寸设置
        pixel_layout = QHBoxLayout()
        
        # 宽度设置
        width_layout = QVBoxLayout()
        width_label = QLabel("宽度:")
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(1920)
        self.width_spin.setEnabled(False)
        self.width_spin.setSuffix(" px")
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_spin)
        
        # 高度设置
        height_layout = QVBoxLayout()
        height_label = QLabel("高度:")
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(1080)
        self.height_spin.setEnabled(False)
        self.height_spin.setSuffix(" px")
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_spin)
        
        pixel_layout.addLayout(width_layout)
        pixel_layout.addLayout(height_layout)
        pixel_layout.addStretch()
        
        size_layout.addRow("输出尺寸:", pixel_layout)
        
        # 常用视频分辨率预设
        preset_layout = QHBoxLayout()
        preset_label = QLabel("预设:")
        preset_layout.addWidget(preset_label)
        
        preset_buttons = [
            ("480p", 854, 480),
            ("720p", 1280, 720),
            ("1080p", 1920, 1080),
            ("2K", 2560, 1440),
            ("4K", 3840, 2160),
            ("Instagram", 1080, 1080),
            ("YouTube封面", 2560, 1440)
        ]
        
        for name, w, h in preset_buttons:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, width=w, height=h: self.set_output_size(width, height))
            preset_layout.addWidget(btn)
        
        preset_layout.addStretch()
        size_layout.addRow(preset_layout)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        

        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.btn_apply = QPushButton("应用")
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        
        button_layout.addWidget(self.btn_apply)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.btn_apply.clicked.connect(self.apply_settings)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
    def on_force_size_changed(self, state):
        """当强制输出尺寸复选框状态改变时"""
        enabled = state == Qt.Checked
        self.width_spin.setEnabled(enabled)
        self.height_spin.setEnabled(enabled)
        
    def set_output_size(self, width, height):
        """设置输出尺寸"""
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        
    def load_current_settings(self):
        """加载当前设置"""
        if self.current_settings:
            self.prefix_edit.setText(self.current_settings.get('prefix', ''))
            self.suffix_edit.setText(self.current_settings.get('suffix', ''))
            
            format_text = self.current_settings.get('format', 'JPG')
            index = self.format_combo.findText(format_text.upper())
            if index >= 0:
                self.format_combo.setCurrentIndex(index)
                
            self.quality_spin.setValue(self.current_settings.get('quality', 95))
            
            force_size = self.current_settings.get('force_size', False)
            self.force_size_checkbox.setChecked(force_size)
            self.on_force_size_changed(Qt.Checked if force_size else Qt.Unchecked)
            
            output_width = self.current_settings.get('output_width', 1920)
            output_height = self.current_settings.get('output_height', 1080)
            self.width_spin.setValue(output_width)
            self.height_spin.setValue(output_height)
            
            auto_rotate = self.current_settings.get('auto_rotate', True)
            self.auto_rotate_checkbox.setChecked(auto_rotate)
            

            
    def get_settings(self):
        """获取当前设置"""
        return {
            'prefix': self.prefix_edit.text().strip(),
            'suffix': self.suffix_edit.text().strip(),
            'format': self.format_combo.currentText().upper(),
            'quality': self.quality_spin.value(),
            'force_size': self.force_size_checkbox.isChecked(),
            'auto_rotate': self.auto_rotate_checkbox.isChecked(),
            'output_width': self.width_spin.value(),
            'output_height': self.height_spin.value(),
        }
        
    def apply_settings(self):
        """应用设置"""
        try:
            settings = self.get_settings()
            self.settings_changed.emit(settings)
            # 使用 try-except 来捕获可能的错误
            QMessageBox.information(self, "提示", "输出设置已应用")
        except Exception as e:
            # 如果显示消息框失败，尝试使用更安全的方式
            print(f"应用设置时出错: {e}")
            import traceback
            traceback.print_exc()
        
    def accept(self):
        """确定按钮点击事件"""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
        super().accept()


def create_output_settings_dialog(parent=None, current_settings=None):
    """创建输出设置对话框的便捷函数"""
    dialog = OutputSettingsDialog(parent, current_settings)
    return dialog


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = OutputSettingsDialog()
    if dialog.exec_() == QDialog.Accepted:
        print("设置:", dialog.get_settings())
    sys.exit(app.exec_())
