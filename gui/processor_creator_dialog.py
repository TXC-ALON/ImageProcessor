"""
Processor创建对话框
用于创建和配置四大类Processor
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QLineEdit, QColorDialog, QCheckBox,
    QDoubleSpinBox, QMessageBox, QWidget, QTabWidget, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from core.processor_types import (
    ProcessorCategory, TransformType, BorderParams, BlurParams,
    TransformParams, WatermarkParams, ProcessorConfig,
    generate_processor_id, get_default_processor_name
)
from config.image_config import Config
import json
from datetime import datetime


class ProcessorCreatorDialog(QDialog):
    """Processor创建对话框"""
    
    # 信号：当Processor创建完成时发出
    processor_created = pyqtSignal(ProcessorConfig)
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_category = ProcessorCategory.BORDER
        self.setup_ui()
        self.setWindowTitle("创建Processor")
        self.resize(600, 500)
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("创建新的Processor")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Processor名称
        name_layout = QHBoxLayout()
        name_label = QLabel("Processor名称:")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("不填写则使用默认名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 类别选择
        category_layout = QHBoxLayout()
        category_label = QLabel("选择类别:")
        self.category_combo = QComboBox()
        self.category_combo.addItem("边框", ProcessorCategory.BORDER)
        self.category_combo.addItem("模糊", ProcessorCategory.BLUR)
        self.category_combo.addItem("图像变形", ProcessorCategory.TRANSFORM)
        self.category_combo.addItem("水印", ProcessorCategory.WATERMARK)
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)
        
        # 参数配置区域
        self.params_widget = QWidget()
        self.params_layout = QVBoxLayout(self.params_widget)
        layout.addWidget(self.params_widget)
        
        # 初始化参数配置
        self.init_border_params()
        
        # 按钮
        button_layout = QHBoxLayout()
        self.btn_create = QPushButton("创建")
        self.btn_cancel = QPushButton("取消")
        self.btn_preview_json = QPushButton("预览JSON")
        
        button_layout.addWidget(self.btn_create)
        button_layout.addWidget(self.btn_preview_json)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.btn_create.clicked.connect(self.create_processor)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_preview_json.clicked.connect(self.preview_json)
        
    def on_category_changed(self, index):
        """当类别改变时更新参数配置"""
        category = self.category_combo.currentData()
        self.current_category = category
        
        # 清空参数区域
        self.clear_params_layout()
        
        # 根据类别显示对应的参数配置
        if category == ProcessorCategory.BORDER:
            self.init_border_params()
        elif category == ProcessorCategory.BLUR:
            self.init_blur_params()
        elif category == ProcessorCategory.TRANSFORM:
            self.init_transform_params()
        elif category == ProcessorCategory.WATERMARK:
            self.init_watermark_params()
    
    def clear_params_layout(self):
        """清空参数布局"""
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def init_border_params(self):
        """初始化边框参数"""
        group = QGroupBox("边框参数")
        form = QFormLayout()
        
        # 边框大小
        self.border_size_spin = QSpinBox()
        self.border_size_spin.setRange(1, 100)
        self.border_size_spin.setValue(10)
        self.border_size_spin.setSuffix(" 像素")
        form.addRow("边框大小:", self.border_size_spin)
        
        # 边框颜色
        color_layout = QHBoxLayout()
        self.border_color_edit = QLineEdit("#ffffff")
        self.border_color_btn = QPushButton("选择颜色")
        color_layout.addWidget(self.border_color_edit)
        color_layout.addWidget(self.border_color_btn)
        form.addRow("边框颜色:", color_layout)
        
        # 边框边
        self.border_sides_combo = QComboBox()
        self.border_sides_combo.addItems(["全部 (tlrb)", "上边 (t)", "下边 (b)", "左边 (l)", "右边 (r)", 
                                         "上下 (tb)", "左右 (lr)", "上左右 (tlr)", "下左右 (blr)"])
        self.border_sides_combo.setCurrentText("全部 (tlrb)")
        form.addRow("边框边:", self.border_sides_combo)
        
        group.setLayout(form)
        self.params_layout.addWidget(group)
        
        # 连接颜色选择按钮
        self.border_color_btn.clicked.connect(self.choose_border_color)
    
    def init_blur_params(self):
        """初始化模糊参数"""
        group = QGroupBox("模糊参数")
        form = QFormLayout()
        
        # 模糊半径
        self.blur_radius_spin = QSpinBox()
        self.blur_radius_spin.setRange(1, 100)
        self.blur_radius_spin.setValue(35)
        form.addRow("模糊半径:", self.blur_radius_spin)
        
        # 背景填充百分比
        self.padding_percent_spin = QDoubleSpinBox()
        self.padding_percent_spin.setRange(0.01, 1.0)
        self.padding_percent_spin.setValue(0.15)
        self.padding_percent_spin.setSingleStep(0.01)
        self.padding_percent_spin.setDecimals(2)
        form.addRow("背景填充百分比:", self.padding_percent_spin)
        
        # 混合透明度
        self.blend_alpha_spin = QDoubleSpinBox()
        self.blend_alpha_spin.setRange(0.0, 1.0)
        self.blend_alpha_spin.setValue(0.1)
        self.blend_alpha_spin.setSingleStep(0.01)
        self.blend_alpha_spin.setDecimals(2)
        form.addRow("混合透明度:", self.blend_alpha_spin)
        
        group.setLayout(form)
        self.params_layout.addWidget(group)
    
    def init_transform_params(self):
        """初始化图像变形参数"""
        group = QGroupBox("图像变形参数")
        form = QFormLayout()
        
        # 变形类型
        self.transform_type_combo = QComboBox()
        self.transform_type_combo.addItem("1:1填充", TransformType.SQUARE)
        self.transform_type_combo.addItem("按比例处理", TransformType.RATIO)
        self.transform_type_combo.addItem("圆角", TransformType.ROUNDED)
        self.transform_type_combo.currentIndexChanged.connect(self.on_transform_type_changed)
        form.addRow("变形类型:", self.transform_type_combo)
        
        # 目标比例（仅用于RATIO类型）
        self.target_ratio_widget = QWidget()
        target_ratio_layout = QHBoxLayout(self.target_ratio_widget)
        self.target_ratio_spin = QDoubleSpinBox()
        self.target_ratio_spin.setRange(0.1, 10.0)
        self.target_ratio_spin.setValue(1.0)
        self.target_ratio_spin.setSingleStep(0.1)
        self.target_ratio_spin.setDecimals(2)
        target_ratio_layout.addWidget(self.target_ratio_spin)
        target_ratio_layout.addWidget(QLabel("(宽:高)"))
        form.addRow("目标比例:", self.target_ratio_widget)
        self.target_ratio_widget.setVisible(False)
        
        # 圆角半径（仅用于ROUNDED类型）
        self.radius_widget = QWidget()
        radius_layout = QHBoxLayout(self.radius_widget)
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(1, 500)
        self.radius_spin.setValue(50)
        self.radius_spin.setSuffix(" 像素")
        radius_layout.addWidget(self.radius_spin)
        radius_layout.addWidget(QLabel("(0表示自动计算)"))
        form.addRow("圆角半径:", self.radius_widget)
        self.radius_widget.setVisible(False)
        
        group.setLayout(form)
        self.params_layout.addWidget(group)
    
    def init_watermark_params(self):
        """初始化水印参数"""
        # 使用TabWidget组织水印参数
        tabs = QTabWidget()
        
        # 基本设置Tab
        basic_tab = QWidget()
        basic_form = QFormLayout(basic_tab)
        
        # Logo位置
        self.logo_position_combo = QComboBox()
        self.logo_position_combo.addItems(["左侧", "右侧"])
        basic_form.addRow("Logo位置:", self.logo_position_combo)
        
        # 是否启用Logo
        self.logo_enable_check = QCheckBox("启用Logo")
        self.logo_enable_check.setChecked(True)
        basic_form.addRow("", self.logo_enable_check)
        
        # 背景颜色
        bg_color_layout = QHBoxLayout()
        self.bg_color_edit = QLineEdit("#ffffff")
        self.bg_color_btn = QPushButton("选择颜色")
        bg_color_layout.addWidget(self.bg_color_edit)
        bg_color_layout.addWidget(self.bg_color_btn)
        basic_form.addRow("背景颜色:", bg_color_layout)
        
        tabs.addTab(basic_tab, "基本设置")
        
        # 字体颜色Tab
        font_tab = QWidget()
        font_form = QFormLayout(font_tab)
        
        # 左上角
        lt_layout = QHBoxLayout()
        self.font_color_lt_edit = QLineEdit("#212121")
        self.font_color_lt_btn = QPushButton("选择")
        self.bold_font_lt_check = QCheckBox("加粗")
        self.bold_font_lt_check.setChecked(True)
        lt_layout.addWidget(self.font_color_lt_edit)
        lt_layout.addWidget(self.font_color_lt_btn)
        lt_layout.addWidget(self.bold_font_lt_check)
        font_form.addRow("左上角颜色:", lt_layout)
        
        # 左下角
        lb_layout = QHBoxLayout()
        self.font_color_lb_edit = QLineEdit("#424242")
        self.font_color_lb_btn = QPushButton("选择")
        self.bold_font_lb_check = QCheckBox("加粗")
        lb_layout.addWidget(self.font_color_lb_edit)
        lb_layout.addWidget(self.font_color_lb_btn)
        lb_layout.addWidget(self.bold_font_lb_check)
        font_form.addRow("左下角颜色:", lb_layout)
        
        # 右上角
        rt_layout = QHBoxLayout()
        self.font_color_rt_edit = QLineEdit("#212121")
        self.font_color_rt_btn = QPushButton("选择")
        self.bold_font_rt_check = QCheckBox("加粗")
        self.bold_font_rt_check.setChecked(True)
        rt_layout.addWidget(self.font_color_rt_edit)
        rt_layout.addWidget(self.font_color_rt_btn)
        rt_layout.addWidget(self.bold_font_rt_check)
        font_form.addRow("右上角颜色:", rt_layout)
        
        # 右下角
        rb_layout = QHBoxLayout()
        self.font_color_rb_edit = QLineEdit("#424242")
        self.font_color_rb_btn = QPushButton("选择")
        self.bold_font_rb_check = QCheckBox("加粗")
        rb_layout.addWidget(self.font_color_rb_edit)
        rb_layout.addWidget(self.font_color_rb_btn)
        rb_layout.addWidget(self.bold_font_rb_check)
        font_form.addRow("右下角颜色:", rb_layout)
        
        tabs.addTab(font_tab, "字体颜色")
        
        self.params_layout.addWidget(tabs)
        
        # 连接颜色选择按钮
        self.bg_color_btn.clicked.connect(lambda: self.choose_color(self.bg_color_edit))
        self.font_color_lt_btn.clicked.connect(lambda: self.choose_color(self.font_color_lt_edit))
        self.font_color_lb_btn.clicked.connect(lambda: self.choose_color(self.font_color_lb_edit))
        self.font_color_rt_btn.clicked.connect(lambda: self.choose_color(self.font_color_rt_edit))
        self.font_color_rb_btn.clicked.connect(lambda: self.choose_color(self.font_color_rb_edit))
    
    def on_transform_type_changed(self, index):
        """当变形类型改变时更新参数显示"""
        transform_type = self.transform_type_combo.currentData()
        
        # 显示/隐藏相关参数
        if transform_type == TransformType.RATIO:
            self.target_ratio_widget.setVisible(True)
            self.radius_widget.setVisible(False)
        elif transform_type == TransformType.ROUNDED:
            self.target_ratio_widget.setVisible(False)
            self.radius_widget.setVisible(True)
        else:  # SQUARE
            self.target_ratio_widget.setVisible(False)
            self.radius_widget.setVisible(False)
    
    def choose_border_color(self):
        """选择边框颜色"""
        color = QColorDialog.getColor(QColor(self.border_color_edit.text()))
        if color.isValid():
            self.border_color_edit.setText(color.name())
    
    def choose_color(self, line_edit):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(line_edit.text()))
        if color.isValid():
            line_edit.setText(color.name())
    
    def get_border_params(self) -> BorderParams:
        """获取边框参数"""
        # 解析边框边
        sides_text = self.border_sides_combo.currentText()
        sides_map = {
            "全部 (tlrb)": "tlrb",
            "上边 (t)": "t",
            "下边 (b)": "b",
            "左边 (l)": "l",
            "右边 (r)": "r",
            "上下 (tb)": "tb",
            "左右 (lr)": "lr",
            "上左右 (tlr)": "tlr",
            "下左右 (blr)": "blr"
        }
        sides = sides_map.get(sides_text, "tlrb")
        
        return BorderParams(
            border_size=self.border_size_spin.value(),
            border_color=self.border_color_edit.text(),
            sides=sides
        )
    
    def get_blur_params(self) -> BlurParams:
        """获取模糊参数"""
        return BlurParams(
            blur_radius=self.blur_radius_spin.value(),
            padding_percent=self.padding_percent_spin.value(),
            blend_alpha=self.blend_alpha_spin.value()
        )
    
    def get_transform_params(self) -> TransformParams:
        """获取图像变形参数"""
        transform_type = self.transform_type_combo.currentData()
        
        if transform_type == TransformType.RATIO:
            target_ratio = self.target_ratio_spin.value()
            radius = None
        elif transform_type == TransformType.ROUNDED:
            target_ratio = None
            radius = self.radius_spin.value() if self.radius_spin.value() > 0 else None
        else:  # SQUARE
            target_ratio = None
            radius = None
        
        return TransformParams(
            transform_type=transform_type,
            target_ratio=target_ratio,
            radius=radius
        )
    
    def get_watermark_params(self) -> WatermarkParams:
        """获取水印参数"""
        return WatermarkParams(
            logo_position="left" if self.logo_position_combo.currentText() == "左侧" else "right",
            logo_enable=self.logo_enable_check.isChecked(),
            bg_color=self.bg_color_edit.text(),
            font_color_lt=self.font_color_lt_edit.text(),
            bold_font_lt=self.bold_font_lt_check.isChecked(),
            font_color_lb=self.font_color_lb_edit.text(),
            bold_font_lb=self.bold_font_lb_check.isChecked(),
            font_color_rt=self.font_color_rt_edit.text(),
            bold_font_rt=self.bold_font_rt_check.isChecked(),
            font_color_rb=self.font_color_rb_edit.text(),
            bold_font_rb=self.bold_font_rb_check.isChecked()
        )
    
    def create_processor(self):
        """创建Processor"""
        try:
            # 获取类别
            category = self.current_category
            
            # 获取参数
            if category == ProcessorCategory.BORDER:
                params = self.get_border_params()
            elif category == ProcessorCategory.BLUR:
                params = self.get_blur_params()
            elif category == ProcessorCategory.TRANSFORM:
                params = self.get_transform_params()
            elif category == ProcessorCategory.WATERMARK:
                params = self.get_watermark_params()
            else:
                raise ValueError(f"未知的Processor类别: {category}")
            
            # 生成ID和名称
            processor_id = generate_processor_id(category)
            processor_name = self.name_edit.text().strip()
            
            if not processor_name:
                processor_name = get_default_processor_name(category)
            
            # 创建Processor配置
            processor_config = ProcessorConfig(
                id=processor_id,
                name=processor_name,
                category=category,
                params=params
            )
            
            # 发出信号
            self.processor_created.emit(processor_config)
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"Processor '{processor_name}' 创建成功！")
            
            # 关闭对话框
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建Processor失败: {str(e)}")
    
    def preview_json(self):
        """预览JSON配置"""
        try:
            # 获取类别
            category = self.current_category
            
            # 获取参数
            if category == ProcessorCategory.BORDER:
                params = self.get_border_params()
            elif category == ProcessorCategory.BLUR:
                params = self.get_blur_params()
            elif category == ProcessorCategory.TRANSFORM:
                params = self.get_transform_params()
            elif category == ProcessorCategory.WATERMARK:
                params = self.get_watermark_params()
            else:
                raise ValueError(f"未知的Processor类别: {category}")
            
            # 生成ID和名称
            processor_id = generate_processor_id(category)
            processor_name = self.name_edit.text().strip()
            
            if not processor_name:
                processor_name = get_default_processor_name(category)
            
            # 创建Processor配置
            processor_config = ProcessorConfig(
                id=processor_id,
                name=processor_name,
                category=category,
                params=params
            )
            
            # 显示JSON
            json_str = processor_config.to_json()
            
            dialog = QDialog(self)
            dialog.setWindowTitle("JSON预览")
            dialog.resize(500, 400)
            
            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setPlainText(json_str)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 10))
            
            btn_close = QPushButton("关闭")
            btn_close.clicked.connect(dialog.accept)
            
            layout.addWidget(text_edit)
            layout.addWidget(btn_close)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成JSON预览失败: {str(e)}")
