from PyQt5.QtWidgets import (QPushButton, QTableView, QAbstractItemView,
                             QGroupBox, QFormLayout, QLineEdit, QComboBox,
                             QCheckBox, QHBoxLayout, QWidget, QVBoxLayout, QAction, QLabel, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QIntValidator, QDoubleValidator
from core.init import config
from gui.output_settings_dialog import OutputSettingsDialog

icon = QIcon(':/icons/resources/icons/icon1.png')
def create_image_control_group(parent=None):
    """创建图片控制参数分组"""
    group = QGroupBox("图片控制参数", parent)
    form = QFormLayout()

    # 输出设置状态标签
    output_status_label = QLabel("默认")
    output_status_label.setStyleSheet("color: #666; font-size: 18px;")
    
    # 输出设置布局
    output_layout = QHBoxLayout()
    # output_layout.addWidget(btn_output_settings)
    output_layout.addWidget(output_status_label)
    output_layout.addStretch()

    btn_output_settings = QPushButton("输出控制")
    btn_output_settings.setToolTip("点击配置输出设置")
    form.addRow("当前输出设置:", output_layout)
    form.addRow(btn_output_settings)

    # 从配置中加载输出设置
    output_settings = config.get_output_settings()
    
    # 初始化状态标签显示
    def init_status_label():
        force_size = output_settings.get('force_size', False)
        if force_size:
            output_width = output_settings.get('output_width', 1920)
            output_height = output_settings.get('output_height', 1080)
            status_text = f"尺寸 {output_width}x{output_height}"
        else:
            status_text = "默认尺寸"
        
        format_text = output_settings.get('format', 'JPG')
        quality = output_settings.get('quality', 95)
        status_text += f", {format_text}, {quality}%"
        
        output_status_label.setText(f" {status_text}")
        output_status_label.setToolTip(f"前缀: {output_settings.get('prefix', '')}, 后缀: {output_settings.get('suffix', '')}")
    
    # 调用初始化函数
    init_status_label()
    
    # 输出路径选择（保留，因为用户可能想快速修改）
    le_output_path = QLineEdit("")
    btn_browse_path = QPushButton("输出目录:")
    le_output_path.setText(config.get_output_dir())
    
    # 设置初始tooltip
    le_output_path.setToolTip(config.get_output_dir())
    
    # 连接textChanged信号，当用户手动编辑路径时更新tooltip
    le_output_path.textChanged.connect(lambda text: le_output_path.setToolTip(text))

    # 在创建QAction之前添加路径检查
    icon_path = r"G:\Dev\PhotoYin\ImageProcesser\resources\icons\FilePicker.png"

    # 创建QAction
    folder_action = QAction(parent)
    folder_action.setToolTip("选择文件夹")
    folder_action.setIcon(QIcon(icon_path))
    # 将动作连接到槽函数
    folder_action.triggered.connect(lambda: browse_output_path(le_output_path))

    # 将动作添加到 QLineEdit 的右侧（TrailingPosition）
    le_output_path.addAction(folder_action, QLineEdit.TrailingPosition)
    le_output_path.setStyleSheet("QLineEdit { padding-right: 20px; }")

    # 创建路径选择布局
    path_layout = QHBoxLayout()
    path_layout.addWidget(btn_browse_path)
    path_layout.addWidget(le_output_path)
    
    # 新增: 输出路径行
    form.addRow(path_layout)
    
    # 连接打开输出路径的信号
    btn_browse_path.clicked.connect(lambda: open_output_path(le_output_path))

    group.setLayout(form)
    
    # 输出控制按钮点击事件
    def open_output_settings_dialog():
        """打开输出设置对话框"""
        dialog = OutputSettingsDialog(parent, output_settings)
        # 使用局部变量引用update_output_settings，避免lambda捕获问题
        def on_settings_changed(settings):
            update_output_settings(settings)
        dialog.settings_changed.connect(on_settings_changed)
        if dialog.exec_() == QDialog.Accepted:
            update_output_settings(dialog.get_settings())
    
    def update_output_settings(settings):
        """更新输出设置"""
        output_settings.update(settings)
        # 保存到配置
        config.set_output_settings(output_settings)
        
        # 更新输出路径显示
        le_output_path.setText(settings.get('output_path', config.get_output_dir()))
        
        # 更新状态标签
        force_size = settings.get('force_size', False)
        if force_size:
            output_width = settings.get('output_width', 1920)
            output_height = settings.get('output_height', 1080)
            status_text = f"强制尺寸 {output_width}x{output_height}"
        else:
            status_text = "默认尺寸"
        
        format_text = settings.get('format', 'JPG')
        quality = settings.get('quality', 95)
        status_text += f", {format_text}, {quality}%"
        
        output_status_label.setText(f"{status_text}")
        output_status_label.setToolTip(f"前缀: {settings.get('prefix', '')}, 后缀: {settings.get('suffix', '')}")
    
    btn_output_settings.clicked.connect(open_output_settings_dialog)

    return group, {
        'output_settings': output_settings,  # 输出设置字典
        'output_path': le_output_path,  # 输出路径控件引用
        'browse_button': btn_browse_path,  # 浏览按钮引用
        'output_status_label': output_status_label,  # 状态标签
    }

def create_video_control_group(parent=None):
    """创建视频控制参数分组（简化版）"""
    group = QGroupBox("视频合成")
    form = QFormLayout()
    
    # 视频设置按钮
    btn_video_settings = QPushButton("视频设置")
    btn_video_settings.setToolTip("点击配置视频参数")
    form.addRow("视频参数:", btn_video_settings)
    
    # 输出路径
    le_output_path = QLineEdit("output/video.mp4")
    btn_browse_output = QPushButton("浏览")
    
    # 布局
    output_layout = QHBoxLayout()
    output_layout.addWidget(le_output_path)
    output_layout.addWidget(btn_browse_output)
    
    form.addRow("输出路径:", output_layout)
    
    # 创建视频按钮
    btn_create_video = QPushButton("创建视频")
    btn_create_video.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
    form.addRow(btn_create_video)

    group.setLayout(form)
    
    # 连接浏览按钮
    def browse_output():
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "选择视频输出路径",
            le_output_path.text(),
            "视频文件 (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            le_output_path.setText(file_path)
    
    btn_browse_output.clicked.connect(browse_output)
    
    return group, {
        'settings_button': btn_video_settings,
        'output_path': le_output_path,
        'create_button': btn_create_video
    }


def browse_output_path(path_line_edit):
    """打开目录选择对话框"""
    from PyQt5.QtWidgets import QFileDialog
    from pathlib import Path

    current_path = path_line_edit.text().strip()
    if not current_path:
        current_path = str(Path.cwd() / "output")

    # 打开目录选择对话框
    folder = QFileDialog.getExistingDirectory(
        None,
        "选择输出目录",
        current_path,
        QFileDialog.ShowDirsOnly
    )

    if folder:
        path_line_edit.setText(folder)
        config.set_output_dir(folder)
        # 更新tooltip
        path_line_edit.setToolTip(folder)


import os
import platform
import subprocess
def open_folder(path=None):
    """
    用系统文件资源管理器打开文件夹
    :param path: 文件夹路径，如果为None则打开当前目录
    """
    if path is None:
        path = os.getcwd()

    # 确保路径存在
    if not os.path.exists(path):
        print(f"❌ 路径不存在: {path}")
        return False

    try:
        system_name = platform.system()

        if system_name == "Windows":
            # Windows系统
            if hasattr(os, 'startfile'):
                os.startfile(path)
            else:
                subprocess.Popen(f'explorer "{os.path.normpath(path)}"')
            print(f"📁 在文件资源管理器中打开: {path}")

        elif system_name == "Darwin":
            # macOS系统
            subprocess.Popen(["open", path])
            print(f"📁 在Finder中打开: {path}")

        elif system_name == "Linux":
            # Linux系统
            subprocess.Popen(["xdg-open", path])
            print(f"📁 在文件管理器中打开: {path}")

        else:
            print("❌ 不支持的操作系统")
            return False

        return True

    except Exception as e:
        print(f"❌ 打开文件夹时出错: {e}")
        return False

def open_output_path(path_line_edit):
    """打开目录选择对话框"""

    folder_path = path_line_edit.text()
    success = open_folder(folder_path)

    if success:
        print("✅ 文件夹已打开！")
    else:
        print("❌ 打开文件夹失败! ")
