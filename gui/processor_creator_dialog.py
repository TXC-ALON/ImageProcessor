"""
Processor创建对话框
用于创建和配置四大类Processor
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QLineEdit, QColorDialog, QCheckBox,
    QDoubleSpinBox, QMessageBox, QWidget, QTabWidget, QTextEdit, QStackedWidget
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
        """初始化边框参数 - 添加说明文本以保持与其他类别相似的高度"""
        group = QGroupBox("边框参数")
        main_layout = QVBoxLayout()
        
        # 说明标签
        info_label = QLabel("边框：为图像添加指定颜色和大小的边框，可以选择添加边框的边。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(info_label)
        
        # 参数表单
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
        
        main_layout.addLayout(form)
        
        # 添加一些间距
        main_layout.addSpacing(20)
        
        # 示例说明
        example_label = QLabel("示例：为800×600的图像添加10像素白色边框，可以选择只添加左右边框或上下边框。")
        example_label.setWordWrap(True)
        example_label.setStyleSheet("color: #888;")
        main_layout.addWidget(example_label)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        group.setLayout(main_layout)
        self.params_layout.addWidget(group)
        
        # 连接颜色选择按钮
        self.border_color_btn.clicked.connect(self.choose_border_color)
        
        # 初始化颜色显示
        self.update_color_display(self.border_color_edit)
    
    def init_blur_params(self):
        """初始化模糊参数 - 添加说明文本以保持与其他类别相似的高度"""
        group = QGroupBox("模糊参数")
        main_layout = QVBoxLayout()
        
        # 说明标签
        info_label = QLabel("模糊：为图像背景添加模糊效果，可以调整模糊强度、背景填充比例和混合透明度。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(info_label)
        
        # 参数表单
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
        
        main_layout.addLayout(form)
        
        # 添加一些间距
        main_layout.addSpacing(20)
        
        # 示例说明
        example_label = QLabel("示例：为图像添加35像素的模糊背景，背景填充15%，与原图以10%的透明度混合。")
        example_label.setWordWrap(True)
        example_label.setStyleSheet("color: #888;")
        main_layout.addWidget(example_label)
        
        # 参数说明
        param_info_label = QLabel("提示：模糊半径越大效果越明显，背景填充百分比控制背景区域大小，混合透明度控制模糊层与原图的融合程度。")
        param_info_label.setWordWrap(True)
        param_info_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(param_info_label)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        group.setLayout(main_layout)
        self.params_layout.addWidget(group)
    
    def init_transform_params(self):
        """初始化图像变形参数 - 使用QStackedWidget为每种类型显示不同的参数界面"""
        group = QGroupBox("图像变形参数")
        main_layout = QVBoxLayout()
        
        # 变形类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("变形类型:")
        self.transform_type_combo = QComboBox()
        self.transform_type_combo.addItem("1:1填充", TransformType.SQUARE)
        self.transform_type_combo.addItem("按比例处理", TransformType.RATIO)
        self.transform_type_combo.addItem("圆角", TransformType.ROUNDED)
        self.transform_type_combo.currentIndexChanged.connect(self.on_transform_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.transform_type_combo)
        type_layout.addStretch()
        main_layout.addLayout(type_layout)
        
        # 创建StackedWidget来切换不同的参数界面
        self.transform_params_stacked = QStackedWidget()
        
        # 1. SQUARE参数界面
        self.square_params_widget = self.create_square_params_widget()
        self.transform_params_stacked.addWidget(self.square_params_widget)
        
        # 2. RATIO参数界面
        self.ratio_params_widget = self.create_ratio_params_widget()
        self.transform_params_stacked.addWidget(self.ratio_params_widget)
        
        # 3. ROUNDED参数界面
        self.rounded_params_widget = self.create_rounded_params_widget()
        self.transform_params_stacked.addWidget(self.rounded_params_widget)
        
        main_layout.addWidget(self.transform_params_stacked)
        group.setLayout(main_layout)
        self.params_layout.addWidget(group)
        
        # 初始显示SQUARE界面
        self.transform_params_stacked.setCurrentIndex(0)
    
    def create_square_params_widget(self):
        """创建1:1填充参数界面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明标签
        info_label = QLabel("1:1填充：将图像调整为正方形，通过添加白色边框保持原始内容比例。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        # 添加一些间距
        layout.addSpacing(20)
        
        # 示例说明
        example_label = QLabel("示例：800×600的图像将变为800×800，上下各添加100像素的白色边框。")
        example_label.setWordWrap(True)
        example_label.setStyleSheet("color: #888;")
        layout.addWidget(example_label)
        
        layout.addStretch()
        return widget
    
    def create_ratio_params_widget(self):
        """创建按比例处理参数界面 - 使用宽度和高度两个参数"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明标签
        info_label = QLabel("按比例处理：将图像调整为指定的分辨率，通过添加白色边框实现目标宽高比。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        # 宽度参数
        width_layout = QHBoxLayout()
        width_label = QLabel("目标宽度:")
        self.target_width_spin = QSpinBox()
        self.target_width_spin.setRange(1, 10000)
        self.target_width_spin.setValue(1980)
        self.target_width_spin.setSuffix(" 像素")
        self.target_width_spin.setSingleStep(10)
        
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.target_width_spin)
        width_layout.addStretch()
        
        layout.addLayout(width_layout)
        
        # 高度参数
        height_layout = QHBoxLayout()
        height_label = QLabel("目标高度:")
        self.target_height_spin = QSpinBox()
        self.target_height_spin.setRange(1, 10000)
        self.target_height_spin.setValue(1080)
        self.target_height_spin.setSuffix(" 像素")
        self.target_height_spin.setSingleStep(10)
        
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.target_height_spin)
        height_layout.addStretch()
        
        layout.addLayout(height_layout)
        
        # 添加一些间距
        layout.addSpacing(10)
        
        # 计算并显示当前比例
        self.ratio_display_label = QLabel("当前比例: 1980:1080 ≈ 1.83")
        self.ratio_display_label.setWordWrap(True)
        self.ratio_display_label.setStyleSheet("color: #007acc; font-weight: bold;")
        layout.addWidget(self.ratio_display_label)
        
        # 连接信号，当宽度或高度改变时更新比例显示
        self.target_width_spin.valueChanged.connect(self.update_ratio_display)
        self.target_height_spin.valueChanged.connect(self.update_ratio_display)
        
        # 添加一些间距
        layout.addSpacing(10)
        
        # 常见分辨率示例
        examples_label = QLabel("常见分辨率：1920×1080 (16:9) · 1280×720 (16:9) · 1080×1080 (1:1) · 1200×800 (3:2)")
        examples_label.setWordWrap(True)
        examples_label.setStyleSheet("color: #888;")
        layout.addWidget(examples_label)
        
        layout.addStretch()
        return widget
    
    def update_ratio_display(self):
        """更新比例显示"""
        if hasattr(self, 'target_width_spin') and hasattr(self, 'target_height_spin'):
            width = self.target_width_spin.value()
            height = self.target_height_spin.value()
            if height > 0:
                ratio = width / height
                # 简化比例显示
                ratio_str = f"{ratio:.2f}"
                # 常见比例的名称
                ratio_name = ""
                if 0.99 < ratio < 1.01:
                    ratio_name = " (1:1)"
                elif 1.32 < ratio < 1.34:
                    ratio_name = " (4:3)"
                elif 1.49 < ratio < 1.51:
                    ratio_name = " (3:2)"
                elif 1.77 < ratio < 1.79:
                    ratio_name = " (16:9)"
                elif 1.24 < ratio < 1.26:
                    ratio_name = " (5:4)"
                
                self.ratio_display_label.setText(f"当前比例: {width}:{height} ≈ {ratio_str}{ratio_name}")
    
    def create_rounded_params_widget(self):
        """创建圆角参数界面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明标签
        info_label = QLabel("圆角：为图像添加圆角效果，可以指定圆角半径或自动计算。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        # 圆角半径参数
        radius_layout = QHBoxLayout()
        radius_label = QLabel("圆角半径:")
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(0, 500)
        self.radius_spin.setValue(50)
        self.radius_spin.setSuffix(" 像素")
        self.radius_spin.setSpecialValueText("自动计算")
        
        radius_layout.addWidget(radius_label)
        radius_layout.addWidget(self.radius_spin)
        radius_layout.addWidget(QLabel("(0表示根据图像尺寸自动计算)"))
        radius_layout.addStretch()
        
        layout.addLayout(radius_layout)
        
        # 添加一些间距
        layout.addSpacing(10)
        
        # 建议说明
        suggestion_label = QLabel("建议：小图像使用10-30像素，中等图像使用30-80像素，大图像使用80-150像素。")
        suggestion_label.setWordWrap(True)
        suggestion_label.setStyleSheet("color: #888;")
        layout.addWidget(suggestion_label)
        
        layout.addStretch()
        return widget
    
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
        
        # 初始化颜色显示
        self.update_all_color_displays()
    
    def on_transform_type_changed(self, index):
        """当变形类型改变时切换到对应的参数界面"""
        transform_type = self.transform_type_combo.currentData()
        
        # 根据变形类型切换到对应的StackedWidget页面
        if transform_type == TransformType.SQUARE:
            self.transform_params_stacked.setCurrentIndex(0)  # SQUARE界面
        elif transform_type == TransformType.RATIO:
            self.transform_params_stacked.setCurrentIndex(1)  # RATIO界面
        elif transform_type == TransformType.ROUNDED:
            self.transform_params_stacked.setCurrentIndex(2)  # ROUNDED界面
    
    def choose_border_color(self):
        """选择边框颜色"""
        color = QColorDialog.getColor(QColor(self.border_color_edit.text()))
        if color.isValid():
            self.border_color_edit.setText(color.name())
            self.update_color_display(self.border_color_edit)
    
    def choose_color(self, line_edit):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(line_edit.text()))
        if color.isValid():
            line_edit.setText(color.name())
            self.update_color_display(line_edit)
    
    def update_color_display(self, line_edit):
        """更新颜色文本框的显示"""
        try:
            color = QColor(line_edit.text())
            if color.isValid():
                # 设置背景色为选择的颜色
                line_edit.setStyleSheet(f"background-color: {color.name()}; color: {'white' if color.lightness() < 128 else 'black'};")
            else:
                # 无效颜色时恢复默认样式
                line_edit.setStyleSheet("")
        except:
            line_edit.setStyleSheet("")
    
    def update_all_color_displays(self):
        """更新所有颜色文本框的显示"""
        # 边框颜色
        if hasattr(self, 'border_color_edit'):
            self.update_color_display(self.border_color_edit)
        
        # 水印背景颜色
        if hasattr(self, 'bg_color_edit'):
            self.update_color_display(self.bg_color_edit)
        
        # 水印字体颜色
        if hasattr(self, 'font_color_lt_edit'):
            self.update_color_display(self.font_color_lt_edit)
        if hasattr(self, 'font_color_lb_edit'):
            self.update_color_display(self.font_color_lb_edit)
        if hasattr(self, 'font_color_rt_edit'):
            self.update_color_display(self.font_color_rt_edit)
        if hasattr(self, 'font_color_rb_edit'):
            self.update_color_display(self.font_color_rb_edit)
    
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
            # 从宽度和高度计算比例
            width = self.target_width_spin.value()
            height = self.target_height_spin.value()
            target_ratio = width / height if height > 0 else 1.0
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
