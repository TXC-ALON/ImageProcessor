import logging
from pathlib import Path
from typing import List
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QLineEdit,
                             QComboBox, QCheckBox, QHBoxLayout, QWidget, QFileDialog, QMessageBox,
                             QStatusBar, QSplitter, QTableView, QAbstractItemView, QProgressDialog,
                             QApplication, QMenu, QAction)
from PyQt5.QtCore import Qt
from .image_table_model import ImageTableModel,create_control_buttons
from .control_widget import create_image_control_group, create_video_control_group

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
        self.image_containers: List[ImageContainer] = []
        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("图片处理程序")
        self.resize(1200, 600)

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

        # 图片控制参数
        image_group, self.image_controls = create_image_control_group(parent=self)

        # 视频控制参数
        video_group, self.video_controls = create_video_control_group()

        left_layout.addWidget(image_group)
        left_layout.addWidget(video_group)
        left_panel.setLayout(left_layout)
        # 添加打印参数按钮
        btn_print_params = QPushButton("打印所有参数")
        btn_print_params.clicked.connect(self.on_print_parameters)
        left_layout.addWidget(btn_print_params)

        # 新增：打印图片路径按钮
        btn_print_paths = QPushButton("打印图片路径")
        btn_print_paths.clicked.connect(self.print_image_paths)
        left_layout.addWidget(btn_print_paths)

        # 新增：打印图片路径按钮
        btn_process = QPushButton("执行操作")
        btn_process.clicked.connect(self.process_chain)
        left_layout.addWidget(btn_process)

        # 添加弹性空间，使按钮保持在底部
        left_layout.addStretch()

        left_panel.setLayout(left_layout)
        return left_panel

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
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", "图像文件 (*.jpg *.jpeg *.png *.tiff *.bmp *.gif *.webp)"
        )
        self.load_images_from_paths(paths, append=True)

    def on_open_folder(self):
        """打开文件夹导入图片（追加模式）"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if not folder:
            return

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
            return
        else:
            print('当前共有 {} 张图片待处理'.format(len(file_list)))
        processor_chain = ProcessorChain()
        # config.set_layout('background_blur')
        processor_chain.add(ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR)
        processor_chain.add(WATERMARK_LEFT_LOGO_PROCESSOR)

        for source_path in tqdm(file_list):
            container = ImageContainer(source_path)
            container.is_use_equivalent_focal_length(config.use_equivalent_focal_length())
            try:
                processor_chain.process(container)
            except Exception as e:
                logging.exception(f'Error: {str(e)}')
                if DEBUG:
                    raise e
                else:
                    print(f'\nError: 文件：{source_path} 处理失败，请检查日志')
            # 正确构建目标路径
            target_path = Path(config.get_output_dir()).joinpath(source_path.name)
            print(target_path)
            container.save(target_path, quality=config.get_quality())
            container.close()
        print(f"处理完成，文件已输出至 {config.get_output_dir()} 文件夹中")
        #option = input('处理完成，文件已输出至 output 文件夹中，输入【r】返回主菜单，输入【x】退出程序\n')
        # if DEBUG:
        #     sys.exit(0)
        # else:
        #     if option == 'x' or option == 'X':
        #         state = -1
        #         # r 返回上一层
        #     else:
        #         state = 0
