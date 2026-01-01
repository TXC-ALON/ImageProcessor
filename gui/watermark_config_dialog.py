"""
水印配置对话框
允许用户配置水印的各种参数：颜色、位置、字体、字体大小等
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QColorDialog, QSpinBox, QTabWidget, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from config.image_config import Config
from core.watermark_effect import WatermarkEffect


class WatermarkConfigDialog(QDialog):
    """水印配置对话框"""
    
    # 信号：当配置改变时发出
    config_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, config: Config = None):
        super().__init__(parent)
        self.config = config
        self.current_config = {}
        self.setup_ui()
        self.load_current_config()
        self.setWindowTitle("水印配置")
        self.resize(600, 700)
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 基本设置标签页
        basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(basic_tab, "基本设置")
        
        # 颜色设置标签页
        color_tab = self.create_color_tab()
        self.tab_widget.addTab(color_tab, "颜色设置")
        
        # 字体设置标签页
        font_tab = self.create_font_tab()
        self.tab_widget.addTab(font_tab, "字体设置")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.btn_apply = QPushButton("应用")
        self.btn_save = QPushButton("保存")
        self.btn_reset = QPushButton("重置")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok = QPushButton("确定")
        
        button_layout.addWidget(self.btn_apply)
        button_layout.addWidget(self.btn_save)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_reset)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_ok)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 连接信号
        self.btn_apply.clicked.connect(self.apply_config)
        self.btn_save.clicked.connect(self.save_config)
        self.btn_reset.clicked.connect(self.reset_config)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)
    
    def create_basic_tab(self) -> QWidget:
        """创建基本设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Logo设置组
        logo_group = QGroupBox("Logo设置")
        logo_layout = QFormLayout()
        
        self.cb_logo_enable = QCheckBox("启用Logo")
        self.cb_logo_enable.setChecked(True)
        logo_layout.addRow("启用Logo:", self.cb_logo_enable)
        
        self.cb_logo_position = QComboBox()
        self.cb_logo_position.addItems(["左侧", "右侧"])
        logo_layout.addRow("Logo位置:", self.cb_logo_position)
        
        logo_group.setLayout(logo_layout)
        layout.addWidget(logo_group)
        
        # 背景设置组
        bg_group = QGroupBox("背景设置")
        bg_layout = QFormLayout()
        
        self.btn_bg_color = QPushButton("选择背景颜色")
        self.btn_bg_color.clicked.connect(self.select_bg_color)
        self.lbl_bg_color = QLabel("#ffffff")
        self.lbl_bg_color.setStyleSheet("background-color: #ffffff; padding: 5px;")
        bg_layout.addRow("背景颜色:", self.btn_bg_color)
        bg_layout.addRow("当前颜色:", self.lbl_bg_color)
        
        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)
        
        # 线条设置组
        line_group = QGroupBox("线条设置")
        line_layout = QFormLayout()
        
        self.btn_line_color = QPushButton("选择线条颜色")
        self.btn_line_color.clicked.connect(self.select_line_color)
        self.lbl_line_color = QLabel("#757575")
        self.lbl_line_color.setStyleSheet("background-color: #757575; padding: 5px;")
        line_layout.addRow("线条颜色:", self.btn_line_color)
        line_layout.addRow("当前颜色:", self.lbl_line_color)
        
        line_group.setLayout(line_layout)
        layout.addWidget(line_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_color_tab(self) -> QWidget:
        """创建颜色设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 左上角文字颜色
        lt_group = QGroupBox("左上角文字")
        lt_layout = QFormLayout()
        
        self.btn_lt_color = QPushButton("选择颜色")
        self.btn_lt_color.clicked.connect(lambda: self.select_text_color('lt'))
        self.lbl_lt_color = QLabel("#212121")
        self.lbl_lt_color.setStyleSheet("background-color: #212121; padding: 5px;")
        self.cb_lt_bold = QCheckBox("粗体")
        self.cb_lt_bold.setChecked(True)
        
        lt_layout.addRow("文字颜色:", self.btn_lt_color)
        lt_layout.addRow("当前颜色:", self.lbl_lt_color)
        lt_layout.addRow("粗体:", self.cb_lt_bold)
        
        lt_group.setLayout(lt_layout)
        layout.addWidget(lt_group)
        
        # 左下角文字颜色
        lb_group = QGroupBox("左下角文字")
        lb_layout = QFormLayout()
        
        self.btn_lb_color = QPushButton("选择颜色")
        self.btn_lb_color.clicked.connect(lambda: self.select_text_color('lb'))
        self.lbl_lb_color = QLabel("#424242")
        self.lbl_lb_color.setStyleSheet("background-color: #424242; padding: 5px;")
        self.cb_lb_bold = QCheckBox("粗体")
        self.cb_lb_bold.setChecked(False)
        
        lb_layout.addRow("文字颜色:", self.btn_lb_color)
        lb_layout.addRow("当前颜色:", self.lbl_lb_color)
        lb_layout.addRow("粗体:", self.cb_lb_bold)
        
        lb_group.setLayout(lb_layout)
        layout.addWidget(lb_group)
        
        # 右上角文字颜色
        rt_group = QGroupBox("右上角文字")
        rt_layout = QFormLayout()
        
        self.btn_rt_color = QPushButton("选择颜色")
        self.btn_rt_color.clicked.connect(lambda: self.select_text_color('rt'))
        self.lbl_rt_color = QLabel("#212121")
        self.lbl_rt_color.setStyleSheet("background-color: #212121; padding: 5px;")
        self.cb_rt_bold = QCheckBox("粗体")
        self.cb_rt_bold.setChecked(True)
        
        rt_layout.addRow("文字颜色:", self.btn_rt_color)
        rt_layout.addRow("当前颜色:", self.lbl_rt_color)
        rt_layout.addRow("粗体:", self.cb_rt_bold)
        
        rt_group.setLayout(rt_layout)
        layout.addWidget(rt_group)
        
        # 右下角文字颜色
        rb_group = QGroupBox("右下角文字")
        rb_layout = QFormLayout()
        
        self.btn_rb_color = QPushButton("选择颜色")
        self.btn_rb_color.clicked.connect(lambda: self.select_text_color('rb'))
        self.lbl_rb_color = QLabel("#424242")
        self.lbl_rb_color.setStyleSheet("background-color: #424242; padding: 5px;")
        self.cb_rb_bold = QCheckBox("粗体")
        self.cb_rb_bold.setChecked(False)
        
        rb_layout.addRow("文字颜色:", self.btn_rb_color)
        rb_layout.addRow("当前颜色:", self.lbl_rb_color)
        rb_layout.addRow("粗体:", self.cb_rb_bold)
        
        rb_group.setLayout(rb_layout)
        layout.addWidget(rb_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_font_tab(self) -> QWidget:
        """创建字体设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 字体大小设置
        size_group = QGroupBox("字体大小")
        size_layout = QFormLayout()
        
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(1, 3)
        self.spin_font_size.setValue(1)
        self.spin_font_size.setToolTip("1: 小, 2: 中, 3: 大")
        size_layout.addRow("字体大小级别:", self.spin_font_size)
        
        self.spin_bold_font_size = QSpinBox()
        self.spin_bold_font_size.setRange(1, 3)
        self.spin_bold_font_size.setValue(1)
        self.spin_bold_font_size.setToolTip("1: 小, 2: 中, 3: 大")
        size_layout.addRow("粗体字体大小级别:", self.spin_bold_font_size)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # 预设主题
        theme_group = QGroupBox("预设主题")
        theme_layout = QVBoxLayout()
        
        self.btn_light_theme = QPushButton("浅色主题")
        self.btn_light_theme.clicked.connect(self.apply_light_theme)
        theme_layout.addWidget(self.btn_light_theme)
        
        self.btn_dark_theme = QPushButton("深色主题")
        self.btn_dark_theme.clicked.connect(self.apply_dark_theme)
        theme_layout.addWidget(self.btn_dark_theme)
        
        self.btn_custom_theme = QPushButton("自定义主题")
        self.btn_custom_theme.clicked.connect(self.apply_custom_theme)
        theme_layout.addWidget(self.btn_custom_theme)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        tab.setLayout(layout)
        return tab
    
    def select_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor(QColor(self.lbl_bg_color.text()))
        if color.isValid():
            color_hex = color.name()
            self.lbl_bg_color.setText(color_hex)
            self.lbl_bg_color.setStyleSheet(f"background-color: {color_hex}; padding: 5px;")
    
    def select_line_color(self):
        """选择线条颜色"""
        color = QColorDialog.getColor(QColor(self.lbl_line_color.text()))
        if color.isValid():
            color_hex = color.name()
            self.lbl_line_color.setText(color_hex)
            self.lbl_line_color.setStyleSheet(f"background-color: {color_hex}; padding: 5px;")
    
    def select_text_color(self, position: str):
        """选择文字颜色"""
        if position == 'lt':
            label = self.lbl_lt_color
        elif position == 'lb':
            label = self.lbl_lb_color
        elif position == 'rt':
            label = self.lbl_rt_color
        elif position == 'rb':
            label = self.lbl_rb_color
        else:
            return
        
        color = QColorDialog.getColor(QColor(label.text()))
        if color.isValid():
            color_hex = color.name()
            label.setText(color_hex)
            label.setStyleSheet(f"background-color: {color_hex}; padding: 5px;")
    
    def apply_light_theme(self):
        """应用浅色主题"""
        self.lbl_bg_color.setText("#ffffff")
        self.lbl_bg_color.setStyleSheet("background-color: #ffffff; padding: 5px;")
        
        self.lbl_line_color.setText("#757575")
        self.lbl_line_color.setStyleSheet("background-color: #757575; padding: 5px;")
        
        self.lbl_lt_color.setText("#212121")
        self.lbl_lt_color.setStyleSheet("background-color: #212121; padding: 5px;")
        self.cb_lt_bold.setChecked(True)
        
        self.lbl_lb_color.setText("#424242")
        self.lbl_lb_color.setStyleSheet("background-color: #424242; padding: 5px;")
        self.cb_lb_bold.setChecked(False)
        
        self.lbl_rt_color.setText("#212121")
        self.lbl_rt_color.setStyleSheet("background-color: #212121; padding: 5px;")
        self.cb_rt_bold.setChecked(True)
        
        self.lbl_rb_color.setText("#424242")
        self.lbl_rb_color.setStyleSheet("background-color: #424242; padding: 5px;")
        self.cb_rb_bold.setChecked(False)
        
        QMessageBox.information(self, "主题应用", "浅色主题已应用")
    
    def apply_dark_theme(self):
        """应用深色主题"""
        self.lbl_bg_color.setText("#212121")
        self.lbl_bg_color.setStyleSheet("background-color: #212121; padding: 5px;")
        
        self.lbl_line_color.setText("#757575")
        self.lbl_line_color.setStyleSheet("background-color: #757575; padding: 5px;")
        
        self.lbl_lt_color.setText("#D32F2F")
        self.lbl_lt_color.setStyleSheet("background-color: #D32F2F; padding: 5px;")
        self.cb_lt_bold.setChecked(True)
        
        self.lbl_lb_color.setText("#d4d1cc")
        self.lbl_lb_color.setStyleSheet("background-color: #d4d1cc; padding: 5px;")
        self.cb_lb_bold.setChecked(False)
        
        self.lbl_rt_color.setText("#D32F2F")
        self.lbl_rt_color.setStyleSheet("background-color: #D32F2F; padding: 5px;")
        self.cb_rt_bold.setChecked(True)
        
        self.lbl_rb_color.setText("#d4d1cc")
        self.lbl_rb_color.setStyleSheet("background-color: #d4d1cc; padding: 5px;")
        self.cb_rb_bold.setChecked(False)
        
        QMessageBox.information(self, "主题应用", "深色主题已应用")
    
    def apply_custom_theme(self):
        """应用自定义主题（当前设置）"""
        self.apply_config()
        QMessageBox.information(self, "主题应用", "自定义主题已应用")
    
    def load_current_config(self):
        """加载当前配置"""
        if self.config is None:
            return
        
        # 从配置加载设置
        self.cb_logo_enable.setChecked(self.config.has_logo_enabled())
        self.cb_logo_position.setCurrentText("左侧" if self.config.is_logo_left() else "右侧")
        
        # 背景颜色
        bg_color = self.config.get_background_color()
        self.lbl_bg_color.setText(bg_color)
        self.lbl_bg_color.setStyleSheet(f"background-color: {bg_color}; padding: 5px;")
        
        # 文字颜色
        lt_config = self.config.get_left_top()
        self.lbl_lt_color.setText(lt_config.get_color())
        self.lbl_lt_color.setStyleSheet(f"background-color: {lt_config.get_color()}; padding: 5px;")
        self.cb_lt_bold.setChecked(lt_config.is_bold())
        
        lb_config = self.config.get_left_bottom()
        self.lbl_lb_color.setText(lb_config.get_color())
        self.lbl_lb_color.setStyleSheet(f"background-color: {lb_config.get_color()}; padding: 5px;")
        self.cb_lb_bold.setChecked(lb_config.is_bold())
        
        rt_config = self.config.get_right_top()
        self.lbl_rt_color.setText(rt_config.get_color())
        self.lbl_rt_color.setStyleSheet(f"background-color: {rt_config.get_color()}; padding: 5px;")
        self.cb_rt_bold.setChecked(rt_config.is_bold())
        
        rb_config = self.config.get_right_bottom()
        self.lbl_rb_color.setText(rb_config.get_color())
        self.lbl_rb_color.setStyleSheet(f"background-color: {rb_config.get_color()}; padding: 5px;")
        self.cb_rb_bold.setChecked(rb_config.is_bold())
        
        # 字体大小
        self.spin_font_size.setValue(self.config.get_data()['base']['font_size'])
        self.spin_bold_font_size.setValue(self.config.get_data()['base']['bold_font_size'])
    
    def get_current_config(self) -> dict:
        """获取当前配置"""
        config = {
            # Logo设置
            'logo_enable': self.cb_logo_enable.isChecked(),
            'logo_position': 'left' if self.cb_logo_position.currentText() == '左侧' else 'right',
            
            # 颜色设置
            'bg_color': self.lbl_bg_color.text(),
            'line_color': self.lbl_line_color.text(),
            
            # 文字颜色
            'font_color_lt': self.lbl_lt_color.text(),
            'bold_font_lt': self.cb_lt_bold.isChecked(),
            'font_color_lb': self.lbl_lb_color.text(),
            'bold_font_lb': self.cb_lb_bold.isChecked(),
            'font_color_rt': self.lbl_rt_color.text(),
            'bold_font_rt': self.cb_rt_bold.isChecked(),
            'font_color_rb': self.lbl_rb_color.text(),
            'bold_font_rb': self.cb_rb_bold.isChecked(),
            
            # 字体大小
            'font_size': self.spin_font_size.value(),
            'bold_font_size': self.spin_bold_font_size.value(),
        }
        return config
    
    def apply_config(self):
        """应用当前配置"""
        config = self.get_current_config()
        self.current_config = config
        
        # 更新配置对象
        if self.config is not None:
            # 更新Logo设置
            if config['logo_enable']:
                self.config.enable_logo()
            else:
                self.config.disable_logo()
            
            if config['logo_position'] == 'left':
                self.config.set_logo_left()
            else:
                self.config.set_logo_right()
            
            # 更新背景颜色
            self.config.set('layout', self.config.get('layout'))
            if 'background_color' not in self.config.get('layout'):
                self.config.get('layout')['background_color'] = config['bg_color']
            else:
                self.config.get('layout')['background_color'] = config['bg_color']
            
            # 更新文字颜色和粗体设置
            layout_elements = self.config.get('layout')['elements']
            
            # 左上角
            layout_elements['left_top']['color'] = config['font_color_lt']
            layout_elements['left_top']['is_bold'] = config['bold_font_lt']
            
            # 左下角
            layout_elements['left_bottom']['color'] = config['font_color_lb']
            layout_elements['left_bottom']['is_bold'] = config['bold_font_lb']
            
            # 右上角
            layout_elements['right_top']['color'] = config['font_color_rt']
            layout_elements['right_top']['is_bold'] = config['bold_font_rt']
            
            # 右下角
            layout_elements['right_bottom']['color'] = config['font_color_rb']
            layout_elements['right_bottom']['is_bold'] = config['bold_font_rb']
            
            # 更新字体大小
            self.config.get('base')['font_size'] = config['font_size']
            self.config.get('base')['bold_font_size'] = config['bold_font_size']
            
            # 保存配置
            self.config.save()
        
        # 发出配置改变信号
        self.config_changed.emit(config)
        QMessageBox.information(self, "配置应用", "水印配置已应用")
    
    def save_config(self):
        """保存配置到文件"""
        self.apply_config()
        QMessageBox.information(self, "配置保存", "配置已保存到文件")
    
    def reset_config(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置为默认配置吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.load_current_config()
            QMessageBox.information(self, "配置重置", "已重置为当前配置文件中的设置")
    
    def accept(self):
        """确定按钮点击事件"""
        self.apply_config()
        super().accept()
    
    def create_watermark_effect(self) -> WatermarkEffect:
        """根据当前配置创建水印效果"""
        config = self.get_current_config()
        
        return WatermarkEffect(
            config=self.config,
            logo_position=config['logo_position'],
            logo_enable=config['logo_enable'],
            bg_color=config['bg_color'],
            line_color=config['line_color'],
            font_color_lt=config['font_color_lt'],
            bold_font_lt=config['bold_font_lt'],
            font_color_lb=config['font_color_lb'],
            bold_font_lb=config['bold_font_lb'],
            font_color_rt=config['font_color_rt'],
            bold_font_rt=config['bold_font_rt'],
            font_color_rb=config['font_color_rb'],
            bold_font_rb=config['bold_font_rb']
        )
