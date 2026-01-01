from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QCheckBox, QWidget, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.init import LAYOUT_ITEMS, config
from core.image_processor import ProcessorComponent, ProcessorChain
import json
from pathlib import Path


class ProcessorControlWidget(QGroupBox):
    """Processor控制组件"""
    
    # 信号：当Processor顺序改变时发出
    processor_order_changed = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__("Processor控制", parent)
        self.selected_processors = []  # 存储选中的Processor对象
        self.setup_ui()
        self.load_default_processors()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 可用Processor列表（多选框）
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        
        # 已选Processor列表（可拖拽）
        self.selected_list = QListWidget()
        self.selected_list.setDragDropMode(QListWidget.InternalMove)
        self.selected_list.setSelectionMode(QListWidget.SingleSelection)
        self.selected_list.model().rowsMoved.connect(self.on_selected_order_changed)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("添加 →")
        self.btn_remove = QPushButton("← 移除")
        self.btn_move_up = QPushButton("上移")
        self.btn_move_down = QPushButton("下移")
        self.btn_clear = QPushButton("清空")
        self.btn_save = QPushButton("保存配置")
        self.btn_load = QPushButton("加载配置")
        
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_remove)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_move_up)
        button_layout.addWidget(self.btn_move_down)
        button_layout.addWidget(self.btn_clear)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_load)
        
        # 列表布局
        lists_layout = QHBoxLayout()
        lists_widget = QWidget()
        lists_widget.setLayout(lists_layout)
        
        # 左侧：可用Processor
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.available_list)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        
        # 右侧：已选Processor
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.selected_list)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        
        lists_layout.addWidget(left_widget)
        lists_layout.addWidget(right_widget)
        
        # 添加到主布局
        layout.addWidget(lists_widget)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.btn_add.clicked.connect(self.add_selected_processors)
        self.btn_remove.clicked.connect(self.remove_selected_processor)
        self.btn_move_up.clicked.connect(self.move_processor_up)
        self.btn_move_down.clicked.connect(self.move_processor_down)
        self.btn_clear.clicked.connect(self.clear_selected_processors)
        self.btn_save.clicked.connect(self.save_configuration)
        self.btn_load.clicked.connect(self.load_configuration)
        
    def load_default_processors(self):
        """加载默认的可用Processor列表"""
        self.available_list.clear()
        
        # 从LAYOUT_ITEMS中获取所有可用的Processor
        for layout_item in LAYOUT_ITEMS:
            item_text = f"{layout_item.name} ({layout_item.value})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, layout_item.value)  # 存储LAYOUT_ID
            self.available_list.addItem(item)

    def add_selected_processors(self):
        """添加选中的Processor到已选列表"""
        selected_items = self.available_list.selectedItems()
        
        for item in selected_items:
            layout_id = item.data(Qt.UserRole)
            item_text = item.text()
            
            # 检查是否已经存在
            existing_items = [self.selected_list.item(i).data(Qt.UserRole) 
                            for i in range(self.selected_list.count())]
            
            if layout_id not in existing_items:
                new_item = QListWidgetItem(item_text)
                new_item.setData(Qt.UserRole, layout_id)
                self.selected_list.addItem(new_item)
                
        self.update_selected_processors()
        
    def remove_selected_processor(self):
        """从已选列表中移除选中的Processor"""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            self.selected_list.takeItem(current_row)
            self.update_selected_processors()
    
    def move_processor_up(self):
        """将选中的Processor上移"""
        current_row = self.selected_list.currentRow()
        if current_row > 0:
            item = self.selected_list.takeItem(current_row)
            self.selected_list.insertItem(current_row - 1, item)
            self.selected_list.setCurrentRow(current_row - 1)
            self.update_selected_processors()
    
    def move_processor_down(self):
        """将选中的Processor下移"""
        current_row = self.selected_list.currentRow()
        if current_row >= 0 and current_row < self.selected_list.count() - 1:
            item = self.selected_list.takeItem(current_row)
            self.selected_list.insertItem(current_row + 1, item)
            self.selected_list.setCurrentRow(current_row + 1)
            self.update_selected_processors()
    
    def clear_selected_processors(self):
        """清空已选Processor列表"""
        self.selected_list.clear()
        self.update_selected_processors()
    
    def on_selected_order_changed(self):
        """当已选列表顺序改变时更新"""
        self.update_selected_processors()
    
    def update_selected_processors(self):
        """更新选中的Processor列表"""
        self.selected_processors = []
        
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            layout_id = item.data(Qt.UserRole)
            self.selected_processors.append(layout_id)
        
        # 发出信号通知顺序改变
        self.processor_order_changed.emit(self.selected_processors)
        
        # 打印当前顺序（调试用）
        print("当前Processor顺序:")
        for i, processor_id in enumerate(self.selected_processors):
            print(f"  {i + 1}. {processor_id}")
    
    def get_processor_chain(self):
        """根据当前选择创建ProcessorChain"""
        from core.init import (
            EMPTY_PROCESSOR, SHADOW_PROCESSOR, MARGIN_PROCESSOR, SIMPLE_PROCESSOR,
            WATERMARK_PROCESSOR, WATERMARK_LEFT_LOGO_PROCESSOR, WATERMARK_RIGHT_LOGO_PROCESSOR,
            DARK_WATERMARK_LEFT_LOGO_PROCESSOR, DARK_WATERMARK_RIGHT_LOGO_PROCESSOR,
            SQUARE_PROCESSOR, PADDING_TO_ORIGINAL_RATIO_PROCESSOR,
            BACKGROUND_BLUR_PROCESSOR, BACKGROUND_BLUR_WITH_WHITE_BORDER_PROCESSOR,
            PURE_WHITE_MARGIN_PROCESSOR, CUSTOM_WATERMARK_PROCESSOR,
            ROUNDED_CORNER_PROCESSOR, ROUNDED_CORNER_BLUR_PROCESSOR,
            ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR
        )

        # 创建映射字典
        processor_map = {
            'empty': EMPTY_PROCESSOR,
            'shadow': SHADOW_PROCESSOR,
            'margin': MARGIN_PROCESSOR,
            'simple': SIMPLE_PROCESSOR,
            'watermark': WATERMARK_PROCESSOR,
            'watermark_left_logo': WATERMARK_LEFT_LOGO_PROCESSOR,
            'watermark_right_logo': WATERMARK_RIGHT_LOGO_PROCESSOR,
            'dark_watermark_left_logo': DARK_WATERMARK_LEFT_LOGO_PROCESSOR,
            'dark_watermark_right_logo': DARK_WATERMARK_RIGHT_LOGO_PROCESSOR,
            'square': SQUARE_PROCESSOR,
            'padding_to_original_ratio': PADDING_TO_ORIGINAL_RATIO_PROCESSOR,
            'background_blur': BACKGROUND_BLUR_PROCESSOR,
            'background_blur_with_white_border': BACKGROUND_BLUR_WITH_WHITE_BORDER_PROCESSOR,
            'pure_white_margin': PURE_WHITE_MARGIN_PROCESSOR,
            'custom_watermark': CUSTOM_WATERMARK_PROCESSOR,
            'rounded_corner': ROUNDED_CORNER_PROCESSOR,
            'rounded_corner_blur': ROUNDED_CORNER_BLUR_PROCESSOR,
            'rounded_corner_blur_shadow': ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR,
        }
        
        # 创建ProcessorChain
        processor_chain = ProcessorChain()
        
        for processor_id in self.selected_processors:
            if processor_id in processor_map:
                processor_chain.add(processor_map[processor_id])
            else:
                print(f"警告: 未找到Processor: {processor_id}")
        
        return processor_chain
    
    def save_configuration(self):
        """保存当前Processor配置到文件"""
        if not self.selected_processors:
            QMessageBox.warning(self, "警告", "没有选中的Processor可保存")
            return
        
        # 获取保存文件名
        file_path, _ = QInputDialog.getText(
            self, "保存配置", "请输入配置文件名:",
            text="processor_config.json"
        )
        
        if not file_path:
            return
        
        # 确保文件扩展名
        if not file_path.endswith('.json'):
            file_path += '.json'
        
        # 构建配置数据
        config_data = {
            "processor_order": self.selected_processors,
            "processor_names": [
                self.selected_list.item(i).text() 
                for i in range(self.selected_list.count())
            ]
        }
        
        try:
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", f"配置已保存到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def load_configuration(self):
        """从文件加载Processor配置"""
        from PyQt5.QtWidgets import QFileDialog
        
        # 选择配置文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            # 读取配置文件
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 清空当前列表
            self.selected_list.clear()
            
            # 加载Processor顺序
            processor_order = config_data.get("processor_order", [])
            processor_names = config_data.get("processor_names", [])
            
            for i, processor_id in enumerate(processor_order):
                if i < len(processor_names):
                    item_text = processor_names[i]
                else:
                    # 尝试从可用列表中获取名称
                    item_text = f"Processor ({processor_id})"
                    for j in range(self.available_list.count()):
                        item = self.available_list.item(j)
                        if item.data(Qt.UserRole) == processor_id:
                            item_text = item.text()
                            break
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, processor_id)
                self.selected_list.addItem(item)
            
            self.update_selected_processors()
            QMessageBox.information(self, "成功", f"配置已从 {file_path} 加载")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置失败: {str(e)}")


def create_processor_control_group(parent=None):
    """创建Processor控制分组"""
    processor_widget = ProcessorControlWidget(parent)
    return processor_widget
