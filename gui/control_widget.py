from PyQt5.QtWidgets import (QPushButton, QTableView, QAbstractItemView,
                             QGroupBox, QFormLayout, QLineEdit, QComboBox,
                             QCheckBox, QHBoxLayout, QWidget, QVBoxLayout,QAction)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from core.init import config

icon = QIcon(':/icons/resources/icons/icon1.png')
def create_image_control_group(parent=None):
    """创建图片控制参数分组"""
    group = QGroupBox("图片控制参数",parent)
    form = QFormLayout()

    le_image_prefix = QLineEdit("Img_")
    le_image_suffix = QLineEdit("")
    le_image_suffix.setPlaceholderText("默认为时间戳")  # 添加placeholder提示
    cb_image_format = QComboBox()
    cb_image_format.addItems(["JPG", "PNG", "TIFF", "WEBP"])
    
    # 图片质量改为数字输入框，范围1-100
    le_image_quality = QLineEdit("100")
    le_image_quality.setPlaceholderText("1-100")
    le_image_quality.setToolTip("图片质量百分比 (1-100)")
    
    # 移除调整大小和分辨率相关控件

    # 新增：输出路径选择
    le_output_path = QLineEdit("")  # 默认值为output
    #le_output_path.setPlaceholderText("输出目录路径")
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

    form.addRow("前缀:", le_image_prefix)
    form.addRow("后缀:", le_image_suffix)
    form.addRow("格式:", cb_image_format)
    form.addRow("质量:", le_image_quality)
    
    # 新增: 输出路径行
    form.addRow( path_layout)
    # 新增: 打开输出文件夹


    group.setLayout(form)

    # 连接打开输出路径的信号
    btn_browse_path.clicked.connect(lambda: open_output_path(le_output_path))



    return group, {
        'prefix': le_image_prefix,
        'suffix': le_image_suffix,
        'format': cb_image_format,
        'quality': le_image_quality,  # 改为QLineEdit
        'browse_button': btn_browse_path,  # 新增浏览按钮引用
        'output_path': le_output_path,  # 新增输出路径控件引用
    }

def create_video_control_group():
    """创建视频控制参数分组"""
    group = QGroupBox("视频控制参数")
    form = QFormLayout()

    cb_video_codec = QComboBox()
    cb_video_codec.addItems(["H.264", "H.265", "VP9", "AV1"])
    le_video_fps = QLineEdit("24")
    le_video_bitrate = QLineEdit("10M")
    chk_video_loop = QCheckBox("循环播放")
    chk_video_loop.setChecked(True)
    chk_video_audio = QCheckBox("包含音频")
    chk_video_audio.setChecked(False)
    le_video_duration = QLineEdit("5.0")
    le_video_duration.setPlaceholderText("每张图停留时间（秒）")

    form.addRow("编码格式:", cb_video_codec)
    form.addRow("帧率 (FPS):", le_video_fps)
    form.addRow("码率:", le_video_bitrate)
    form.addRow("单图时长:", le_video_duration)
    form.addRow(chk_video_loop)
    form.addRow(chk_video_audio)

    group.setLayout(form)
    return group, {
        'codec': cb_video_codec,
        'fps': le_video_fps,
        'bitrate': le_video_bitrate,
        'duration': le_video_duration,
        'loop': chk_video_loop,
        'audio': chk_video_audio
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
