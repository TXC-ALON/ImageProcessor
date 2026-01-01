from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLineEdit, QPushButton, QFileDialog, QAction)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt


class FolderSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 创建 QLineEdit
        self.folder_path_edit = QLineEdit(self)
        self.folder_path_edit.setPlaceholderText("请选择文件夹路径...")

        import os
        icon_path = r"G:\Dev\PhotoYin\ImageProcesser\resources\icons\Button.png"
        folder_action = QAction(self)
        # 设置一个文件夹图标，您需要提供自己的图标文件路径，例如："folder_icon.png"
        folder_action.setIcon(QIcon(icon_path))
        # 如果暂无图标，也可以用文本提示，但通常建议使用图标
        folder_action.setToolTip("选择文件夹")
        # 将动作连接到槽函数
        folder_action.triggered.connect(self.open_folder_dialog)
        # 将动作添加到 QLineEdit 的右侧（TrailingPosition）
        self.folder_path_edit.addAction(folder_action, QLineEdit.TrailingPosition)

        layout.addWidget(self.folder_path_edit)
        self.setLayout(layout)

    def open_folder_dialog(self):
        """打开文件夹选择对话框，并将选中的路径设置到 QLineEdit 中"""
        # 使用 QFileDialog 选择文件夹
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            "",  # 初始目录，空字符串表示使用默认目录
            QFileDialog.ShowDirsOnly  # 只显示目录
        )

        # 如果用户选择了文件夹（而不是取消），则将其路径设置到输入框
        if folder_path:
            self.folder_path_edit.setText(folder_path)


# 应用启动代码
if __name__ == '__main__':
    app = QApplication([])
    window = FolderSelector()
    window.show()
    app.exec_()