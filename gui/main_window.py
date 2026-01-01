import logging
from pathlib import Path
from typing import List
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QLineEdit,
                             QComboBox, QCheckBox, QHBoxLayout, QWidget, QFileDialog, QMessageBox,
                             QStatusBar, QSplitter, QTableView, QAbstractItemView, QProgressDialog,
                             QApplication, QMenu, QAction,QListWidgetItem,QLabel, QTextEdit, QGroupBox, QDialog, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from .image_table_model import ImageTableModel,create_control_buttons
from .control_widget import create_image_control_group, create_video_control_group
from .processor_control_dialog_enhanced import ProcessorControlDialogEnhanced as ProcessorControlDialog

from core.image_container import ImageContainer
from core.image_processor import ProcessorChain

from core.init import (WATERMARK_LEFT_LOGO_PROCESSOR, ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR)
from core.init import config

from config.constant import DEBUG
from tqdm import tqdm


class DragDropTableView(QTableView):
    """支持拖拽文件的表格视图"""
    
    # 信号：当文件被拖拽到表格时发出
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """处理拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """处理拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = []
            
            for url in urls:
                # 获取本地文件路径
                file_path = url.toLocalFile()
                if file_path:
                    file_paths.append(file_path)
            
            if file_paths:
                # 发出信号，传递文件路径列表
                self.files_dropped.emit(file_paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

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

        right_layout.addLayout(button_layout)
        right_layout.addWidget(self.table_view)
        right_panel.setLayout(right_layout)

        return right_panel

    def create_table_view(self):
        """创建并设置表格视图"""
        # 创建自定义表格视图以支持文件拖拽
        table_view = DragDropTableView()
        self.model = ImageTableModel(self.image_containers)
        table_view.setModel(self.model)

        # 拖放设置
        table_view.setDragDropMode(QAbstractItemView.InternalMove)
        table_view.setDragEnabled(True)
        table_view.setAcceptDrops(True)
        table_view.setDropIndicatorShown(True)
        table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # 启用列拖动调整顺序
        table_view.horizontalHeader().setSectionsMovable(True)
        table_view.horizontalHeader().setDragEnabled(True)
        table_view.horizontalHeader().setDragDropMode(QHeaderView.InternalMove)
        table_view.horizontalHeader().sectionMoved.connect(self.on_column_order_changed)

        # 连接顺序改变信号
        self.model.order_changed.connect(self.on_order_changed)

        # 启用右键菜单
        table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        table_view.customContextMenuRequested.connect(self.show_table_context_menu)
        
        # 连接拖拽完成信号
        table_view.files_dropped.connect(self.on_files_dropped)

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

    def on_files_dropped(self, file_paths):
        """处理拖拽文件事件"""
        if not file_paths:
            return
        
        # 收集所有图片文件路径
        all_image_paths = []
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.webp'}
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if path.is_file():
                # 如果是文件，检查是否是图片
                if path.suffix.lower() in image_extensions:
                    all_image_paths.append(str(path))
            elif path.is_dir():
                # 如果是文件夹，只导入当前层次的图片文件（不递归）
                for item in path.iterdir():
                    if item.is_file() and item.suffix.lower() in image_extensions:
                        all_image_paths.append(str(item))
        
        if not all_image_paths:
            QMessageBox.information(self, "提示", "拖拽的文件或文件夹中没有找到支持的图片文件。")
            return
        
        # 加载图片（追加模式）
        self.load_images_from_paths(all_image_paths, append=True)
        
        # 更新上次打开的文件夹路径（使用第一个文件的父目录）
        if all_image_paths:
            first_file_path = Path(all_image_paths[0])
            config.set_last_opened_dir(str(first_file_path.parent))
    
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

    def on_column_order_changed(self, logicalIndex, oldVisualIndex, newVisualIndex):
        """处理列顺序改变事件"""
        #print(f"列顺序改变: {logicalIndex} 从 {oldVisualIndex} 移动到 {newVisualIndex}")
        # 保存列顺序到配置
        self.save_column_order()
    
    def save_column_order(self):
        """保存当前列顺序到配置"""
        if not hasattr(self, 'table_view') or not self.table_view:
            return
        
        # 获取当前可见的列顺序
        header = self.table_view.horizontalHeader()
        column_count = header.count()
        
        # 获取逻辑索引到可视索引的映射
        logical_to_visual = {}
        for logical in range(column_count):
            visual = header.visualIndex(logical)
            logical_to_visual[logical] = visual
        
        # 按可视顺序获取列名
        visible_columns = []
        for visual in range(column_count):
            for logical, v in logical_to_visual.items():
                if v == visual:
                    # 获取列名
                    column_name = self.model.headers[logical] if logical < len(self.model.headers) else f"列{logical}"
                    visible_columns.append(column_name)
                    break
        
        # 保存到配置
        config.set_table_visible_columns(visible_columns)
        #print(f"列顺序已保存: {visible_columns}")
    
    def on_order_changed(self):
        """处理顺序改变事件"""
        #print("当前图片顺序（拖拽后）:")
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
        print(f"  质量: {self.image_controls['quality'].text()}%")
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

        # 获取UI控件中的参数
        prefix = self.image_controls['prefix'].text().strip()
        suffix = self.image_controls['suffix'].text().strip()
        format_lower = self.image_controls['format'].currentText().lower()
        
        # 获取质量参数，确保在1-100范围内
        try:
            quality = int(self.image_controls['quality'].text().strip())
            quality = max(1, min(100, quality))  # 限制在1-100范围内
        except ValueError:
            quality = 95  # 默认值
            print(f"警告：质量参数无效，使用默认值 {quality}")
        
        # 获取输出目录
        output_dir = self.image_controls['output_path'].text().strip()
        if not output_dir:
            output_dir = config.get_output_dir()
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
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
                
                # 构建目标文件名
                source_stem = source_path.stem  # 原文件名（不含扩展名）
                source_suffix = source_path.suffix  # 原扩展名
                
                # 如果后缀为空，使用时间戳
                if not suffix:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    actual_suffix = f"_{timestamp}"
                else:
                    actual_suffix = suffix
                
                # 构建新文件名：前缀 + 原文件名 + 后缀 + 格式扩展名
                new_filename = f"{prefix}{source_stem}{actual_suffix}.{format_lower}"
                target_path = output_path / new_filename
                
                # 确保文件名唯一
                counter = 1
                while target_path.exists():
                    new_filename = f"{prefix}{source_stem}{actual_suffix}_{counter}.{format_lower}"
                    target_path = output_path / new_filename
                    counter += 1
                
                # 保存图片
                container.save(target_path, quality=quality)
                container.close()
                processed_count += 1
                
                print(f"已保存: {target_path.name} (质量: {quality}%)")
                
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
        message += f"\n输出目录: {output_dir}"
        message += f"\n文件名格式: {prefix}[原文件名]{'[时间戳]' if not suffix else suffix}.{format_lower}"
        message += f"\n图片质量: {quality}%"
        
        QMessageBox.information(self, "处理完成", message)
        print(f"处理完成，文件已输出至 {output_dir} 文件夹中")
        print(f"文件名格式: {prefix}[原文件名]{'[时间戳]' if not suffix else suffix}.{format_lower}")
        print(f"图片质量: {quality}%")

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
        """打开表格列设置对话框（支持拖动调整顺序）"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("表格列设置")
        dialog.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # 说明标签
        label = QLabel("选择要在表格中显示的列（勾选表示显示，拖动调整顺序，文件名必须选中）：")
        layout.addWidget(label)
        
        # 列选择列表（支持拖拽调整顺序）
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SingleSelection)
        list_widget.setDragDropMode(QListWidget.InternalMove)
        list_widget.setDragEnabled(True)
        list_widget.setAcceptDrops(True)
        list_widget.setDropIndicatorShown(True)
        
        # 获取所有可用的列（包括新增的文件大小列）
        all_headers = [
            "文件名", "后缀名", "文件大小", "相机品牌", "相机型号", "镜头型号",
            "焦距", "光圈", "ISO", "曝光时间", "分辨率", "拍摄时间", "GPS信息"
        ]
        
        # 获取当前可见的列（保持当前顺序）
        visible_columns = config.get_table_visible_columns()
        
        # 首先添加当前可见的列（保持当前顺序）
        for header in visible_columns:
            if header in all_headers:
                item = QListWidgetItem(header)
                # 文件名列必须选中且不可取消，显示为灰色的选中效果
                if header == "文件名":
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
                    item.setCheckState(Qt.Checked)
                else:
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled)
                    item.setCheckState(Qt.Checked)
                list_widget.addItem(item)
        
        # 然后添加未选中的列
        for header in all_headers:
            if header not in visible_columns:
                item = QListWidgetItem(header)
                # 文件名列必须选中且不可取消，显示为灰色的选中效果
                if header == "文件名":
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
                    item.setCheckState(Qt.Checked)
                else:
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled)
                    item.setCheckState(Qt.Unchecked)
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
        
        # 重置顺序按钮
        reset_order_btn = QPushButton("重置顺序")
        reset_order_btn.clicked.connect(lambda: self.reset_column_order(list_widget, all_headers))
        button_layout.addWidget(reset_order_btn)
        
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
            # 获取选中的列（按列表中的顺序）
            selected_columns = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    selected_columns.append(item.text())
            
            # 确保文件名在选中列中（即使由于某些原因不在）
            if "文件名" not in selected_columns:
                selected_columns.append("文件名")
                print("警告：文件名列未选中，已自动添加")
            
            # 保存设置（包括顺序）
            config.set_table_visible_columns(selected_columns)
            
            # 更新表格模型
            if hasattr(self, 'model'):
                self.model.update_visible_headers()
                self.model.layoutChanged.emit()
                # 重新应用列顺序到表格
                self.apply_column_order_to_table(selected_columns)
            
            self.statusBar().showMessage("表格列设置已更新", 2000)
            print(f"列设置已更新: {selected_columns}")
    
    def reset_column_order(self, list_widget, all_headers):
        """重置列顺序为默认顺序（并恢复默认配置）"""
        try:
            # 定义默认可见列（所有列都可见）
            default_visible = [
                "文件名", "后缀名", "文件大小", "相机品牌", "相机型号", "镜头型号",
                "焦距", "光圈", "ISO", "曝光时间", "分辨率", "拍摄时间", "GPS信息"
            ]
            
            # 清空列表
            list_widget.clear()
            
            # 按默认顺序重新添加所有列，并设置为默认勾选状态
            for header in all_headers:
                item = QListWidgetItem(header)
                # 文件名列必须选中且不可取消，显示为灰色的选中效果
                if header == "文件名":
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
                    item.setCheckState(Qt.Checked)
                else:
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled)
                    # 所有列默认都勾选
                    item.setCheckState(Qt.Checked)
                list_widget.addItem(item)
            
            # 更新配置为默认状态
            config.set_table_visible_columns(default_visible)
            
            # 更新表格模型
            if hasattr(self, 'model'):
                self.model.update_visible_headers()
                self.model.layoutChanged.emit()
                # 重新应用列顺序到表格
                self.apply_column_order_to_table(default_visible)
            
            print("列顺序已重置为默认顺序，配置已更新为默认状态")
            print(f"默认可见列: {default_visible}")
        except Exception as e:
            print(f"重置列顺序时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def apply_column_order_to_table(self, column_order):
        """将列顺序应用到表格"""
        if not hasattr(self, 'table_view') or not self.table_view:
            return
        
        # 获取当前表格的列顺序
        header = self.table_view.horizontalHeader()
        
        # 创建列名到逻辑索引的映射
        column_name_to_index = {}
        for i in range(len(self.model.headers)):
            column_name_to_index[self.model.headers[i]] = i
        
        # 重新排列列顺序
        for visual_index, column_name in enumerate(column_order):
            if column_name in column_name_to_index:
                logical_index = column_name_to_index[column_name]
                current_visual_index = header.visualIndex(logical_index)
                if current_visual_index != visual_index:
                    header.moveSection(current_visual_index, visual_index)
        
        print(f"已应用列顺序到表格: {column_order}")

    def set_all_items_checkstate(self, list_widget, state):
        """设置列表中所有项目的勾选状态"""
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            # 文件名列必须始终被选中
            if item.text() == "文件名":
                item.setCheckState(Qt.Checked)
            else:
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
