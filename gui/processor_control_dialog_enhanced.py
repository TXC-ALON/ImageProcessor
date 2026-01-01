"""
增强版Processor控制对话框
支持创建新的Processor和保存组合Processor
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QWidget, QMessageBox, QInputDialog, QLabel, QGroupBox,
    QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.init import LAYOUT_ITEMS, config
from core.image_processor import ProcessorComponent, ProcessorChain
from core.processor_types import (
    ProcessorConfig, CompositeProcessorConfig, generate_composite_processor_id
)
from core.configurable_processor import (
    ConfigurableProcessor, ConfigurableCompositeProcessor,
    create_default_border_config, create_default_blur_config,
    create_default_transform_config, create_default_watermark_config
)
from gui.processor_creator_dialog import ProcessorCreatorDialog
import json
from pathlib import Path
from datetime import datetime


class ProcessorControlDialogEnhanced(QDialog):
    """增强版Processor控制对话框"""
    
    # 信号：当Processor顺序改变时发出
    processor_order_changed = pyqtSignal(list)
    
    def __init__(self, parent=None, current_processors=None):
        super().__init__(parent)
        self.config = config
        self.selected_processors = current_processors or []  # 存储选中的Processor对象
        self.custom_processors = []  # 存储自定义Processor配置
        self.setup_ui()
        self.load_default_processors()
        self.load_custom_processors()
        self.load_current_processors()
        self.setWindowTitle("Processor控制")
        self.resize(1600, 1200)
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 标题和说明
        title_label = QLabel("配置Processor执行顺序")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel("左侧双击或拖拽Processor到右侧，右侧支持拖拽调整顺序")
        desc_label.setStyleSheet("color: #666;")
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # 列表布局
        lists_layout = QHBoxLayout()
        
        # 左侧：可用Processor（分为默认和自定义）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 新建Processor按钮（放在自定义Processor上面）
        self.btn_create_new = QPushButton("+ 新建Processor")
        left_layout.addWidget(self.btn_create_new)
        
        # 自定义Processor
        custom_group = QGroupBox("自定义Processor")
        custom_layout = QVBoxLayout()
        self.custom_list = QListWidget()
        self.custom_list.setSelectionMode(QListWidget.MultiSelection)
        self.custom_list.setDragEnabled(True)  # 启用拖拽
        custom_layout.addWidget(self.custom_list)
        custom_group.setLayout(custom_layout)
        
        # 默认Processor
        default_group = QGroupBox("默认Processor")
        default_layout = QVBoxLayout()
        self.default_list = QListWidget()
        self.default_list.setSelectionMode(QListWidget.MultiSelection)
        self.default_list.setDragEnabled(True)  # 启用拖拽
        default_layout.addWidget(self.default_list)
        default_group.setLayout(default_layout)

        left_layout.addWidget(default_group)
        left_layout.addWidget(custom_group)

        
        # 右侧：已选Processor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 右侧操作按钮（放在selected_list上面）
        right_buttons_layout = QHBoxLayout()
        self.btn_remove = QPushButton("移除")
        self.btn_clear = QPushButton("清空")
        self.btn_save_composite = QPushButton("保存为组合")
        
        right_buttons_layout.addWidget(self.btn_remove)
        right_buttons_layout.addWidget(self.btn_clear)
        right_buttons_layout.addWidget(self.btn_save_composite)
        right_buttons_layout.addStretch()
        
        right_layout.addLayout(right_buttons_layout)
        
        selected_group = QGroupBox("已选Processor（可拖拽调整顺序）")
        selected_layout = QVBoxLayout()
        self.selected_list = QListWidget()
        self.selected_list.setDragDropMode(QListWidget.InternalMove)
        self.selected_list.setSelectionMode(QListWidget.SingleSelection)
        self.selected_list.setAcceptDrops(True)  # 接受拖拽
        self.selected_list.setDropIndicatorShown(True)  # 显示拖拽指示器
        self.selected_list.model().rowsMoved.connect(self.on_selected_order_changed)
        selected_layout.addWidget(self.selected_list)
        selected_group.setLayout(selected_layout)
        
        right_layout.addWidget(selected_group)
        
        lists_layout.addWidget(left_widget, 2)
        lists_layout.addWidget(right_widget, 2)
        
        # 配置管理按钮
        config_layout = QHBoxLayout()
        self.btn_save_config = QPushButton("保存配置")
        self.btn_load_config = QPushButton("加载配置")
        self.btn_export_json = QPushButton("导出JSON")
        self.btn_import_json = QPushButton("导入JSON")
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        
        config_layout.addWidget(self.btn_save_config)
        config_layout.addWidget(self.btn_load_config)
        config_layout.addWidget(self.btn_export_json)
        config_layout.addWidget(self.btn_import_json)
        config_layout.addStretch()
        config_layout.addWidget(self.btn_ok)
        config_layout.addWidget(self.btn_cancel)
        
        # 添加到主布局
        layout.addLayout(lists_layout)
        layout.addLayout(config_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.btn_create_new.clicked.connect(self.create_new_processor)
        self.btn_remove.clicked.connect(self.remove_selected_processor)
        self.btn_clear.clicked.connect(self.clear_selected_processors)
        self.btn_save_composite.clicked.connect(self.save_as_composite)
        self.btn_save_config.clicked.connect(self.save_configuration)
        self.btn_load_config.clicked.connect(self.load_configuration)
        self.btn_export_json.clicked.connect(self.export_json)
        self.btn_import_json.clicked.connect(self.import_json)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        # 连接双击信号
        self.default_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.custom_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
    def load_default_processors(self):
        """加载默认的可用Processor列表"""
        self.default_list.clear()
        
        # 收集所有Processor，避免重复
        all_processors = {}
        
        # 从LAYOUT_ITEMS中获取所有可用的Processor
        for layout_item in LAYOUT_ITEMS:
            layout_id = layout_item.value
            display_name = layout_item.name
            all_processors[layout_id] = display_name
        
        # 添加其他不在LAYOUT_ITEMS中的Processor
        additional_processors = [
            ("圆角,背景虚化,主图阴影 效果", "rounded_corner_blur_shadow"),
            ("圆角加背景虚化效果", "rounded_corner_blur"),
            ("圆角效果", "rounded_corner"),
        ]
        
        # 添加additional_processors，但跳过已经在LAYOUT_ITEMS中的
        for name, layout_id in additional_processors:
            if layout_id not in all_processors:
                all_processors[layout_id] = name
        
        # 现在添加所有唯一的Processor到列表
        for layout_id, display_name in all_processors.items():
            item_text = f"{display_name} ({layout_id})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, layout_id)
            item.setData(Qt.UserRole + 1, "default")  # 标记为默认Processor
            self.default_list.addItem(item)
        
        # 按名称排序，方便查找
        # self.default_list.sortItems()
    
    def load_custom_processors(self):
        """加载自定义Processor"""
        self.custom_list.clear()
        
        # 从文件加载自定义Processor配置
        custom_configs = self.load_custom_configs()
        
        for processor_config in custom_configs:
            item_text = f"{processor_config.name} ({processor_config.id})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, processor_config.id)
            item.setData(Qt.UserRole + 1, "custom")  # 标记为自定义Processor
            item.setData(Qt.UserRole + 2, processor_config)  # 存储配置对象
            self.custom_list.addItem(item)
        
        # 按名称排序
        self.custom_list.sortItems()
    
    def load_custom_configs(self):
        """从文件加载自定义Processor配置"""
        custom_configs = []
        config_dir = Path("config/processors")
        
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            return custom_configs
        
        # 加载所有JSON文件
        for config_file in config_dir.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 检查是否为组合Processor
                if "processor_ids" in config_data:
                    processor_config = CompositeProcessorConfig.from_dict(config_data)
                else:
                    processor_config = ProcessorConfig.from_dict(config_data)
                
                custom_configs.append(processor_config)
            except Exception as e:
                print(f"加载配置文件 {config_file} 失败: {e}")
        
        return custom_configs
    
    def load_current_processors(self):
        """加载当前已选的Processor"""
        self.selected_list.clear()
        
        for processor_id in self.selected_processors:
            # 首先在默认列表中查找
            found = False
            for i in range(self.default_list.count()):
                item = self.default_list.item(i)
                if item.data(Qt.UserRole) == processor_id:
                    item_text = item.text()
                    new_item = QListWidgetItem(item_text)
                    new_item.setData(Qt.UserRole, processor_id)
                    new_item.setData(Qt.UserRole + 1, "default")
                    self.selected_list.addItem(new_item)
                    found = True
                    break
            
            # 如果在默认列表中没找到，在自定义列表中查找
            if not found:
                for i in range(self.custom_list.count()):
                    item = self.custom_list.item(i)
                    if item.data(Qt.UserRole) == processor_id:
                        item_text = item.text()
                        new_item = QListWidgetItem(item_text)
                        new_item.setData(Qt.UserRole, processor_id)
                        new_item.setData(Qt.UserRole + 1, "custom")
                        self.selected_list.addItem(new_item)
                        found = True
                        break
            
            # 如果都没找到，创建一个简单的项目
            if not found:
                item_text = f"Processor ({processor_id})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, processor_id)
                self.selected_list.addItem(item)
        
        self.update_selected_processors()
    
    def on_item_double_clicked(self, item):
        """处理双击事件：将双击的Processor添加到已选列表"""
        source_type = item.data(Qt.UserRole + 1)
        self.add_processor_item(item, source_type)
        self.update_selected_processors()
    
    def add_processor_item(self, source_item, source_type):
        """添加Processor项目到已选列表"""
        processor_id = source_item.data(Qt.UserRole)
        item_text = source_item.text()
        
        # 检查是否已经存在
        existing_items = [self.selected_list.item(i).data(Qt.UserRole) 
                        for i in range(self.selected_list.count())]
        
        if processor_id not in existing_items:
            new_item = QListWidgetItem(item_text)
            new_item.setData(Qt.UserRole, processor_id)
            new_item.setData(Qt.UserRole + 1, source_type)
            self.selected_list.addItem(new_item)
    
    def remove_selected_processor(self):
        """从已选列表中移除选中的Processor"""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            self.selected_list.takeItem(current_row)
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
            processor_id = item.data(Qt.UserRole)
            self.selected_processors.append(processor_id)
        
        # 发出信号通知顺序改变
        self.processor_order_changed.emit(self.selected_processors)
        
        # 打印当前顺序（调试用）
        print("当前Processor顺序:")
        for i, processor_id in enumerate(self.selected_processors):
            print(f"  {i + 1}. {processor_id}")
    
    def create_new_processor(self):
        """创建新的Processor"""
        dialog = ProcessorCreatorDialog(self.config, self)
        dialog.processor_created.connect(self.on_processor_created)
        dialog.exec_()
    
    def on_processor_created(self, processor_config: ProcessorConfig):
        """当新的Processor创建完成时"""
        try:
            # 保存配置到文件
            self.save_processor_config(processor_config)
            
            # 重新加载自定义Processor
            self.load_custom_processors()
            
            # 自动添加到已选列表
            item_text = f"{processor_config.name} ({processor_config.id})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, processor_config.id)
            item.setData(Qt.UserRole + 1, "custom")
            self.selected_list.addItem(item)
            
            self.update_selected_processors()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存Processor失败: {str(e)}")
    
    def save_configuration(self):
        """保存当前Processor配置到文件"""
        if not self.selected_processors:
            QMessageBox.warning(self, "警告", "没有选中的Processor可保存")
            return
        
        # 获取保存文件名
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置", "processor_config.json", "JSON文件 (*.json)"
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
                    # 在默认列表中查找
                    for j in range(self.default_list.count()):
                        item = self.default_list.item(j)
                        if item.data(Qt.UserRole) == processor_id:
                            item_text = item.text()
                            break
                    # 在自定义列表中查找
                    if item_text == f"Processor ({processor_id})":
                        for j in range(self.custom_list.count()):
                            item = self.custom_list.item(j)
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
    
    def export_json(self):
        """导出当前配置为JSON"""
        if not self.selected_processors:
            QMessageBox.warning(self, "警告", "没有选中的Processor可导出")
            return
        
        # 收集Processor配置
        processor_configs = []
        
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            processor_id = item.data(Qt.UserRole)
            source_type = item.data(Qt.UserRole + 1)
            
            # 如果是自定义Processor，获取配置对象
            if source_type == "custom":
                for j in range(self.custom_list.count()):
                    custom_item = self.custom_list.item(j)
                    if custom_item.data(Qt.UserRole) == processor_id:
                        processor_config = custom_item.data(Qt.UserRole + 2)
                        if processor_config:
                            processor_configs.append(processor_config.to_dict())
                        break
        
        # 构建导出数据
        export_data = {
            "export_time": datetime.now().isoformat(),
            "processor_count": len(self.selected_processors),
            "processor_configs": processor_configs,
            "processor_order": self.selected_processors
        }
        
        # 获取保存文件名
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出JSON", "processor_export.json", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", f"配置已导出到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出配置失败: {str(e)}")
    
    def import_json(self):
        """从JSON文件导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 检查是否为有效的导入文件
            if "processor_configs" not in import_data:
                QMessageBox.warning(self, "警告", "这不是有效的Processor导出文件")
                return
            
            # 导入Processor配置
            imported_count = 0
            for config_dict in import_data.get("processor_configs", []):
                try:
                    # 检查是否为组合Processor
                    if "processor_ids" in config_dict:
                        processor_config = CompositeProcessorConfig.from_dict(config_dict)
                    else:
                        processor_config = ProcessorConfig.from_dict(config_dict)
                    
                    # 保存配置
                    self.save_processor_config(processor_config)
                    imported_count += 1
                except Exception as e:
                    print(f"导入Processor配置失败: {e}")
            
            # 重新加载自定义Processor
            self.load_custom_processors()
            
            QMessageBox.information(self, "成功", f"成功导入 {imported_count} 个Processor配置")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入配置失败: {str(e)}")
    
    def get_processor_chain(self):
        """根据当前选择创建ProcessorChain"""
        from core.init import (
            EMPTY_PROCESSOR, SHADOW_PROCESSOR, MARGIN_PROCESSOR, SIMPLE_PROCESSOR,
            WATERMARK_PROCESSOR, WATERMARK_LEFT_LOGO_PROCESSOR, WATERMARK_RIGHT_LOGO_PROCESSOR,
            DARK_WATERMARK_LEFT_LOGO_PROCESSOR, DARK_WATERMARK_RIGHT_LOGO_PROCESSOR,
            SQUARE_PROCESSOR, PADDING_TO_ORIGINAL_RATIO_PROCESSOR,
            BACKGROUND_BLUR_PROCESSOR, BACKGROUND_BLUR_WITH_WHITE_BORDER_PROCESSOR,
            PURE_WHITE_MARGIN_PROCESSOR, ROUNDED_CORNER_PROCESSOR,
            ROUNDED_CORNER_BLUR_PROCESSOR, ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR,
            config
        )
        from core.image_processor import CustomWatermarkProcessor
        from core.configurable_watermark_processor import (
            ConfigurableWatermarkProcessor,
            create_dark_theme_processor,
            create_light_theme_processor,
            create_red_theme_processor,
            create_blue_theme_processor
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
            'custom_watermark': CustomWatermarkProcessor(config),
            'rounded_corner': ROUNDED_CORNER_PROCESSOR,
            'rounded_corner_blur': ROUNDED_CORNER_BLUR_PROCESSOR,
            'rounded_corner_blur_shadow': ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR,
            # 新的可配置水印处理器
            'configurable_watermark': ConfigurableWatermarkProcessor(config),
            'dark_theme_watermark': create_dark_theme_processor(config, 'left'),
            'light_theme_watermark': create_light_theme_processor(config, 'left'),
            'red_theme_watermark': create_red_theme_processor(config, 'left'),
            'blue_theme_watermark': create_blue_theme_processor(config, 'left'),
        }
        
        # 创建ProcessorChain
        processor_chain = ProcessorChain()
        
        for processor_id in self.selected_processors:
            if processor_id in processor_map:
                processor_chain.add(processor_map[processor_id])
            else:
                # 尝试从自定义Processor创建
                processor = self.create_processor_from_id(processor_id)
                if processor:
                    processor_chain.add(processor)
                else:
                    print(f"警告: 未找到Processor: {processor_id}")
        
        return processor_chain
    
    def create_processor_from_id(self, processor_id):
        """根据ID创建Processor"""
        # 在自定义列表中查找
        for i in range(self.custom_list.count()):
            item = self.custom_list.item(i)
            if item.data(Qt.UserRole) == processor_id:
                processor_config = item.data(Qt.UserRole + 2)
                if processor_config:
                    # 检查是否为组合Processor
                    if isinstance(processor_config, CompositeProcessorConfig):
                        # 创建组合Processor
                        return ConfigurableCompositeProcessor(
                            self.config,
                            processor_config.processor_configs,
                            processor_config.name,
                            processor_config.id
                        )
                    else:
                        # 创建单个Processor
                        return ConfigurableProcessor(self.config, processor_config)
        
        return None
    
    def get_processor_summary(self):
        """获取Processor配置摘要"""
        if not self.selected_processors:
            return "未选择任何Processor"
        
        summary = []
        for i, processor_id in enumerate(self.selected_processors):
            # 查找显示名称
            display_name = processor_id
            
            # 在默认列表中查找
            for j in range(self.default_list.count()):
                item = self.default_list.item(j)
                if item.data(Qt.UserRole) == processor_id:
                    display_name = item.text().split(' (')[0]  # 只取名称部分
                    break
            
            # 在自定义列表中查找
            if display_name == processor_id:
                for j in range(self.custom_list.count()):
                    item = self.custom_list.item(j)
                    if item.data(Qt.UserRole) == processor_id:
                        display_name = item.text().split(' (')[0]
                        break
            
            summary.append(f"{i + 1}. {display_name}")
        
        return "\n".join(summary)
    
    def get_selected_processors(self):
        """获取当前选中的Processor列表"""
        return self.selected_processors.copy()
    
    def save_processor_config(self, processor_config: ProcessorConfig):
        """保存Processor配置到文件"""
        config_dir = Path("config/processors")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / f"{processor_config.id}.json"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(processor_config.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"Processor配置已保存到: {config_file}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存Processor配置失败: {str(e)}")
    
    def save_as_composite(self):
        """将当前选择的Processor保存为组合"""
        if self.selected_list.count() == 0:
            QMessageBox.warning(self, "警告", "没有选中的Processor可保存为组合")
            return
        
        # 获取组合名称
        name, ok = QInputDialog.getText(
            self, "保存组合", "请输入组合名称:",
            text=f"组合_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        if not ok or not name:
            return
        
        # 收集Processor配置
        processor_configs = []
        processor_ids = []
        
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            processor_id = item.data(Qt.UserRole)
            source_type = item.data(Qt.UserRole + 1)
            
            processor_ids.append(processor_id)
            
            # 如果是自定义Processor，获取配置对象
            if source_type == "custom":
                # 从自定义列表中查找配置
                for j in range(self.custom_list.count()):
                    custom_item = self.custom_list.item(j)
                    if custom_item.data(Qt.UserRole) == processor_id:
                        processor_config = custom_item.data(Qt.UserRole + 2)
                        if processor_config:
                            processor_configs.append(processor_config)
                        break
        
        # 创建组合配置
        composite_id = generate_composite_processor_id()
        composite_config = CompositeProcessorConfig(
            id=composite_id,
            name=name,
            processor_ids=processor_ids,
            processor_configs=processor_configs
        )
        
        # 保存组合配置
        config_dir = Path("config/processors")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / f"{composite_id}.json"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(composite_config.to_dict(), f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", f"组合Processor '{name}' 已保存")
            
            # 重新加载自定义Processor
            self.load_custom_processors()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存组合Processor失败: {str(e)}")
