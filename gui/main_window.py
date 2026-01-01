import logging
from pathlib import Path
from typing import List
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QLineEdit,
                             QComboBox, QCheckBox, QHBoxLayout, QWidget, QFileDialog, QMessageBox,
                             QStatusBar, QSplitter, QTableView, QAbstractItemView, QProgressDialog,
                             QApplication, QMenu, QAction, QLabel, QTextEdit, QGroupBox, QDialog)
from PyQt5.QtCore import Qt
from .image_table_model import ImageTableModel,create_control_buttons
from .control_widget import create_image_control_group, create_video_control_group
from .processor_control_dialog_enhanced import ProcessorControlDialogEnhanced as ProcessorControlDialog

from core.image_container import ImageContainer
from core.image_processor import ProcessorChain

from core.init import (WATERMARK_LEFT_LOGO_PROCESSOR, ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR)
from core.init import config

from config.constant import DEBUG
from tqdm import tqdm

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_controls = None
        self.image_controls = None
        self.selected_processors = []  # 存储选中的Processor ID列表
        self.image_containers: List[ImageContainer] = []
        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("图片处理程序")
        self.resize(1200, 600)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建左侧面板
        left_panel = self.create_left_panel()

        # 创建右侧面板
        right_panel = self.create_right_panel()

        # 设置主分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1100])

        self.setCentralWidget(splitter)
        self.setStatusBar(QStatusBar())

    def create_left_panel(self):
        """创建左侧控制面板"""
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # Processor配置显示区域
        processor_display_group = self.create_processor_display_group()
        left_layout.addWidget(processor_display_group)

        # 图片控制参数
        image_group, self.image_controls = create_image_control_group(parent=self)

        # 视频控制参数
        video_group, self.video_controls = create_video_control_group()

        left_layout.addWidget(image_group)
        left_layout.addWidget(video_group)
        
        # 添加打印参数按钮
        btn_print_params = QPushButton("打印所有参数")
        btn_print_params.clicked.connect(self.on_print_parameters)
        left_layout.addWidget(btn_print_params)

        # 新增：打印图片路径按钮
        btn_print_paths = QPushButton("打印图片路径")
        btn_print_paths.clicked.connect(self.print_image_paths)
        left_layout.addWidget(btn_print_paths)

        # 新增：执行操作按钮
        btn_process = QPushButton("执行操作")
        btn_process.clicked.connect(self.process_chain)
        left_layout.addWidget(btn_process)

        # 添加弹性空间，使按钮保持在底部
        left_layout.addStretch()

        left_panel.setLayout(left_layout)
        return left_panel
    
    def create_processor_display_group(self):
        """创建Processor配置显示区域"""
        group = QGroupBox("Processor配置")
        layout = QVBoxLayout()
        
        # 配置显示文本框
        self.processor_display = QTextEdit()
        self.processor_display.setReadOnly(True)
        self.processor_display.setMaximumHeight(100)
        self.processor_display.setPlaceholderText("未配置Processor")
        
        # 按钮布局
        button_layout = QHBoxLayout()
        btn_configure = QPushButton("配置Processor")
        btn_clear = QPushButton("清空配置")
        
        button_layout.addWidget(btn_configure)
        button_layout.addWidget(btn_clear)
        button_layout.addStretch()
        
        # 连接按钮信号
        btn_configure.clicked.connect(self.open_processor_dialog)
        btn_clear.clicked.connect(self.clear_processor_config)
        
        layout.addWidget(self.processor_display)
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def open_processor_dialog(self):
        """打开Processor配置对话框"""
        dialog = ProcessorControlDialog(self, self.selected_processors)
        if dialog.exec_() == QDialog.Accepted:
            # 更新选中的Processor
            self.selected_processors = dialog.get_selected_processors()
            # 更新显示
            self.update_processor_display()
            print("Processor配置已更新")
    
    def clear_processor_config(self):
        """清空Processor配置"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空Processor配置吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.selected_processors = []
            self.update_processor_display()
            print("Processor配置已清空")
    
    def update_processor_display(self):
        """更新Processor配置显示"""
        if not self.selected_processors:
            self.processor_display.setText("未配置Processor")
            return
        
        # 创建简单的显示文本
        display_text = "当前Processor配置:\n"
        
        # 直接从LAYOUT_ITEMS和其他已知Processor中查找显示名称
        from core.init import LAYOUT_ITEMS
        
        # 创建名称映射
        name_map = {}
        for layout_item in LAYOUT_ITEMS:
            name_map[layout_item.value] = layout_item.name
        
        # 添加其他Processor的映射
        additional_mappings = {
            'rounded_corner_blur_shadow': '圆角,背景虚化,主图阴影 效果',
            'rounded_corner_blur': '圆角加背景虚化效果',
            'rounded_corner': '圆角效果',
            'shadow': '阴影',
            'margin': '边距',
            'simple': '默认(简洁)',
            'square': '1:1填充',
            'padding_to_original_ratio': '填充到原始比例',
            'pure_white_margin': '白色边框',
        }
        name_map.update(additional_mappings)
        
        for i, processor_id in enumerate(self.selected_processors):
            display_name = name_map.get(processor_id, processor_id)
            display_text += f"{i + 1}. {display_name}\n"
        
        self.processor_display.setText(display_text)

    def create_right_panel(self):
        """创建右侧显示面板"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # 创建表格视图
        self.table_view = self.create_table_view()

        # 创建控制按钮
        btn_open_file, btn_open_folder, btn_clear = create_control_buttons()

        # 连接按钮信号
        btn_open_file.clicked.connect(self.on_open_images)
        btn_open_folder.clicked.connect(self.on_open_folder)
        btn_clear.clicked.connect(self.on_clear_table)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_open_file)
        button_layout.addWidget(btn_open_folder)
        button_layout.addWidget(btn_clear)
        button_layout.addStretch()

        right_layout.addWidget(self.table_view)
        right_layout.addLayout(button_layout)
        right_panel.setLayout(right_layout)

        return right_panel

    def create_table_view(self):
        """创建并设置表格视图"""
        table_view = QTableView()
        self.model = ImageTableModel(self.image_containers)
        table_view.setModel(self.model)

        # 拖放设置
        table_view.setDragDropMode(QAbstractItemView.InternalMove)
        table_view.setDragEnabled(True)
        table_view.setAcceptDrops(True)
        table_view.setDropIndicatorShown(True)
        table_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 连接顺序改变信号
        self.model.order_changed.connect(self.on_order_changed)

        # 启用右键菜单
        table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        table_view.customContextMenuRequested.connect(self.show_table_context_menu)

        return table_view

    def on_open_images(self):
        """打开图片文件（追加模式）"""
        # 获取上次打开的文件夹路径
        last_dir = config.get_last_opened_dir()
        
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", last_dir, "图像文件 (*.jpg *.jpeg *.png *.tiff *.bmp *.gif *.webp)"
        )
        
        if paths:
            # 更新上次打开的文件夹路径（使用第一个文件的父目录）
            first_file_path = Path(paths[0])
            config.set_last_opened_dir(str(first_file_path.parent))
            
        self.load_images_from_paths(paths, append=True)

    def on_open_folder(self):
        """打开文件夹导入图片（追加模式）"""
        # 获取上次打开的文件夹路径
        last_dir = config.get_last_opened_dir()
        
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹", last_dir)
        if not folder:
            return

        # 更新上次打开的文件夹路径
        config.set_last_opened_dir(folder)

        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.webp'}
        paths = []
        folder_path = Path(folder)

        for file in folder_path.iterdir():
            if file.is_file() and file.suffix.lower() in image_extensions:
                paths.append(str(file))

        if not paths:
            QMessageBox.information(self, "提示", "该文件夹中没有找到支持的图片文件。")
            return

        self.load_images_from_paths(paths, append=True)

    def on_clear_table(self):
        """清空表格和数据"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有图片吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.image_containers = []
            self.model = ImageTableModel(self.image_containers)
            self.model.order_changed.connect(self.on_order_changed)
            self.table_view.setModel(self.model)
            self.statusBar().showMessage("表格已清空", 1500)

    def on_order_changed(self):
        """处理顺序改变事件"""
        print("当前图片顺序（拖拽后）:")
        self.print_current_order()
        self.table_view.clearSelection()

    def print_current_order(self):
        """打印当前图片顺序"""
        if not self.image_containers:
            print("  (空)")
            return
        for i, img in enumerate(self.image_containers):
            print(f"  {i + 1}. {img.path.name}")
        print("-" * 40)

    def load_images_from_paths(self, paths, append=False):
        """从路径列表加载图片，支持追加模式"""
        if not paths:
            return

        # 创建进度对话框
        progress = QProgressDialog("正在加载图片...", "取消", 0, len(paths), self)
        progress.setWindowTitle("加载进度")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)  # 立即显示进度条
        
        new_images = []
        existing_paths = {container.path for container in self.image_containers} if append else set()

        for i, p in enumerate(paths, 1):
            # 更新进度条，显示当前文件名和进度
            progress.setLabelText(f"正在加载 ({i}/{len(paths)}): {Path(p).name}")
            progress.setValue(i)
            
            # 处理取消操作
            if progress.wasCanceled():
                QMessageBox.information(self, "提示", "加载已取消")
                return

            try:
                container_path = Path(p)
                # 如果是追加模式且图片已存在，则跳过
                if append and container_path in existing_paths:
                    continue

                container = ImageContainer(container_path)
                new_images.append(container)
                if append:
                    existing_paths.add(container_path)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法加载 {p}: {str(e)}")
                
            # 处理事件，确保UI响应
            QApplication.processEvents()

        # 关闭进度对话框
        progress.close()

        if not new_images:
            if append:
                QMessageBox.information(self, "提示", "没有新图片可添加（可能所有选择的图片都已存在）。")
            return

        # 根据模式更新图片列表
        if append:
            self.image_containers.extend(new_images)
            message = f"已追加 {len(new_images)} 张新图片"
        else:
            self.image_containers = new_images
            message = f"已加载 {len(new_images)} 张图片"

        # 更新模型
        self.model = ImageTableModel(self.image_containers)
        self.model.order_changed.connect(self.on_order_changed)
        self.table_view.setModel(self.model)

        print(f"当前图片顺序（{'追加后' if append else '加载后'}）:")
        self.print_current_order()
        self.statusBar().showMessage(message, 2000)

    def on_print_parameters(self):
        print(config.get_self_path())
        config.save()


        """打印所有控制参数"""
        print("=" * 50)
        print("当前所有控制参数值:")
        print("=" * 50)

        # 打印图片控制参数
        print("\n📷 图片控制参数:")
        print(f"  前缀: {self.image_controls['prefix'].text()}")
        print(f"  后缀: {self.image_controls['suffix'].text()}")
        print(f"  格式: {self.image_controls['format'].currentText()}")
        print(f"  质量: {self.image_controls['quality'].currentText()}")
        print(f"  调整大小: {'是' if self.image_controls['resize_check'].isChecked() else '否'}")


        if self.image_controls['resize_check'].isChecked():
            print(f"  宽度: {self.image_controls['resize_width'].text()}")
            print(f"  高度: {self.image_controls['resize_height'].text()}")

        print(f"  输出路径: {self.image_controls['output_path'].text()}")

        # 打印视频控制参数（需要先创建对应的控件）
        if hasattr(self, 'video_controls'):
            print("\n🎥 视频控制参数:")
            # 根据你的视频控件结构添加相应的打印代码
            for key, control in self.video_controls.items():
                if isinstance(control, QLineEdit):
                    print(f"  {key}: {control.text()}")
                elif isinstance(control, QComboBox):
                    print(f"  {key}: {control.currentText()}")
                elif isinstance(control, QCheckBox):
                    print(f"  {key}: {'是' if control.isChecked() else '否'}")

        # 同时在状态栏显示提示
        self.statusBar().showMessage("参数已打印到控制台", 2000)

    def print_image_paths(self):
        """打印当前表格中所有图片的路径，以列表形式输出"""
        if not self.image_containers:
            print("当前表格中没有图片")
            self.statusBar().showMessage("表格为空，没有图片路径可打印", 2000)
            return

        print("=" * 60)
        print("当前表格中的所有图片路径:")
        print("=" * 60)

        # 以列表形式输出所有图片路径
        path_list = []
        for i, container in enumerate(self.image_containers):
            path_str = str(container.path)
            path_list.append(path_str)
            print(f"[{i}] {path_str}")

        # 输出Python列表格式
        print("\nPython列表格式:")
        print("[")
        for path in path_list:
            print(f'    "{path}",')
        print("]")

        # 输出可以直接复制的单行列表格式
        print("\n单行列表格式 (可直接复制):")
        list_str = "[" + ", ".join(f'"{path}"' for path in path_list) + "]"
        print(list_str)

        # 显示统计信息
        print(f"\n总计: {len(path_list)} 个图片文件")
        self.statusBar().showMessage(f"已打印 {len(path_list)} 个图片路径到控制台", 3000)

    def show_table_context_menu(self, position):
        """显示表格右键菜单"""
        menu = QMenu()
        delete_action = QAction("删除选中项", self)
        delete_action.triggered.connect(self.delete_selected_images)
        menu.addAction(delete_action)
        
        # 只在有选中项时启用删除操作
        selected_indexes = self.table_view.selectionModel().selectedRows()
        delete_action.setEnabled(len(selected_indexes) > 0)
        
        menu.exec_(self.table_view.viewport().mapToGlobal(position))

    def delete_selected_images(self):
        """删除选中的图片"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return
            
        # 获取选中的行号（从大到小排序，以便从后往前删除）
        rows_to_delete = sorted([index.row() for index in selected_indexes], reverse=True)
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(rows_to_delete)} 张图片吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 从数据中删除
            for row in rows_to_delete:
                if 0 <= row < len(self.image_containers):
                    self.image_containers.pop(row)
            
            # 更新模型
            self.model = ImageTableModel(self.image_containers)
            self.model.order_changed.connect(self.on_order_changed)
            self.table_view.setModel(self.model)
            
            # 更新状态栏
            self.statusBar().showMessage(f"已删除 {len(rows_to_delete)} 张图片", 2000)
            print(f"已删除 {len(rows_to_delete)} 张图片")
            self.print_current_order()



    def get_image_paths(self) -> List[Path]:
        """返回存在的图片文件Path对象列表"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.webp'}

        return [container.path for container in self.image_containers
                if container.path.exists() and  # 检查文件是否存在
                container.path.is_file() and
                container.path.suffix.lower() in image_extensions]
    def process_chain(self):
        """执行流程链操作"""
        file_list = self.get_image_paths()
        if len(file_list) == 0:
            print("当前没有需要处理的图片")
            QMessageBox.information(self, "提示", "当前没有需要处理的图片")
            return
        else:
            print('当前共有 {} 张图片待处理'.format(len(file_list)))
        
        # 使用用户选择的Processor链
        if self.selected_processors:
            # 创建临时对话框来获取Processor链
            temp_dialog = ProcessorControlDialog(self, self.selected_processors)
            processor_chain = temp_dialog.get_processor_chain()
        else:
            # 如果没有选择Processor，使用默认的
            processor_chain = ProcessorChain()
            processor_chain.add(ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR)
            processor_chain.add(WATERMARK_LEFT_LOGO_PROCESSOR)
            QMessageBox.information(self, "提示", "使用默认Processor配置")

        # 创建进度对话框
        progress = QProgressDialog("正在处理图片...", "取消", 0, len(file_list), self)
        progress.setWindowTitle("处理进度")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)  # 立即显示进度条
        
        processed_count = 0
        error_count = 0
        
        for i, source_path in enumerate(file_list, 1):
            # 更新进度条
            progress.setLabelText(f"正在处理 ({i}/{len(file_list)}): {source_path.name}")
            progress.setValue(i)
            
            # 处理取消操作
            if progress.wasCanceled():
                QMessageBox.information(self, "提示", "处理已取消")
                return
            
            try:
                container = ImageContainer(source_path)
                container.is_use_equivalent_focal_length(config.use_equivalent_focal_length())
                processor_chain.process(container)
                
                # 正确构建目标路径
                target_path = Path(config.get_output_dir()).joinpath(source_path.name)
                container.save(target_path, quality=config.get_quality())
                container.close()
                processed_count += 1
                
            except Exception as e:
                logging.exception(f'Error: {str(e)}')
                error_count += 1
                if DEBUG:
                    raise e
                else:
                    print(f'\nError: 文件：{source_path} 处理失败，请检查日志')
            
            # 处理事件，确保UI响应
            QApplication.processEvents()
        
        # 关闭进度对话框
        progress.close()
        
        # 显示处理结果
        message = f"处理完成！\n成功处理: {processed_count} 张图片"
        if error_count > 0:
            message += f"\n处理失败: {error_count} 张图片（请查看控制台日志）"
        message += f"\n输出目录: {config.get_output_dir()}"
        
        QMessageBox.information(self, "处理完成", message)
        print(f"处理完成，文件已输出至 {config.get_output_dir()} 文件夹中")

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 打开文件动作
        open_file_action = QAction("打开文件", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self.on_open_images)
        file_menu.addAction(open_file_action)
        
        # 打开文件夹动作
        open_folder_action = QAction("打开文件夹", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self.on_open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        # 表格列设置动作
        table_columns_action = QAction("表格列设置", self)
        table_columns_action.triggered.connect(self.open_table_columns_dialog)
        settings_menu.addAction(table_columns_action)
        
        # 水印配置动作
        watermark_config_action = QAction("水印配置", self)
        watermark_config_action.triggered.connect(self.open_watermark_config_dialog)
        settings_menu.addAction(watermark_config_action)
        
        # 处理器配置动作
        processor_config_action = QAction("处理器配置", self)
        processor_config_action.triggered.connect(self.open_processor_dialog)
        settings_menu.addAction(processor_config_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        # 关于动作
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def open_table_columns_dialog(self):
        """打开表格列设置对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("表格列设置")
        dialog.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # 说明标签
        label = QLabel("选择要在表格中显示的列（勾选表示显示）：")
        layout.addWidget(label)
        
        # 列选择列表
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.NoSelection)
        
        # 获取所有可用的列
        all_headers = [
            "文件名", "后缀名", "相机品牌", "相机型号", "镜头型号",
            "焦距", "光圈", "ISO", "曝光时间", "分辨率", "拍摄时间", "GPS信息"
        ]
        
        # 获取当前可见的列
        visible_columns = config.get_table_visible_columns()
        
        # 添加所有列到列表，并设置勾选状态
        for header in all_headers:
            item = QListWidgetItem(header)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if header in visible_columns else Qt.Unchecked)
            list_widget.addItem(item)
        
        layout.addWidget(list_widget)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 全选按钮
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(lambda: self.set_all_items_checkstate(list_widget, Qt.Checked))
        button_layout.addWidget(select_all_btn)
        
        # 全不选按钮
        select_none_btn = QPushButton("全不选")
        select_none_btn.clicked.connect(lambda: self.set_all_items_checkstate(list_widget, Qt.Unchecked))
        button_layout.addWidget(select_none_btn)
        
        button_layout.addStretch()
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # 获取选中的列
            selected_columns = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    selected_columns.append(item.text())
            
            # 保存设置
            config.set_table_visible_columns(selected_columns)
            
            # 更新表格模型
            if hasattr(self, 'model'):
                self.model.update_visible_headers()
                self.model.layoutChanged.emit()
            
            self.statusBar().showMessage("表格列设置已更新", 2000)

    def set_all_items_checkstate(self, list_widget, state):
        """设置列表中所有项目的勾选状态"""
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item.setCheckState(state)

    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于图片处理程序", 
                         "图片处理程序 v1.0\n\n"
                         "一个用于批量处理图片的应用程序，支持多种图片处理功能。\n\n"
                         "作者: ImageProcessor Team")

    def open_watermark_config_dialog(self):
        """打开水印配置对话框"""
        from .watermark_config_dialog import WatermarkConfigDialog
        dialog = WatermarkConfigDialog(self, config)
        if dialog.exec_() == QDialog.Accepted:
            self.statusBar().showMessage("水印配置已更新", 2000)
            print("水印配置已更新")
