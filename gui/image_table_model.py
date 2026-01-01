from PyQt5.QtCore import QAbstractTableModel, Qt, QByteArray, QDataStream, QIODevice, pyqtSignal
from PyQt5.QtCore import QMimeData
from typing import List
import os
from core.image_container import ImageContainer
from PyQt5.QtWidgets import (QPushButton, QTableView, QAbstractItemView,
                             QGroupBox, QFormLayout, QLineEdit, QComboBox,
                             QCheckBox, QHBoxLayout, QWidget, QVBoxLayout)

from core.init import config


def format_file_size(size_bytes):
    """格式化文件大小，返回Mb或Kb单位"""
    if size_bytes is None:
        return "N/A"
    
    try:
        size_bytes = float(size_bytes)
        if size_bytes >= 1024 * 1024:  # 大于等于1MB
            size_mb = size_bytes / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        elif size_bytes >= 1024:  # 大于等于1KB
            size_kb = size_bytes / 1024
            return f"{size_kb:.2f} KB"
        else:  # 小于1KB
            return f"{size_bytes:.0f} B"
    except (ValueError, TypeError):
        return "N/A"

class ImageTableModel(QAbstractTableModel):
    order_changed = pyqtSignal()

    def __init__(self, images: List[ImageContainer]):
        super().__init__()
        self.images = images
        self.all_headers = [
            "文件名", "后缀名", "文件大小", "相机品牌", "相机型号", "镜头型号",
            "焦距", "光圈", "ISO", "曝光时间", "分辨率", "拍摄时间", "GPS信息"
        ]
        self.update_visible_headers()
    
    def update_visible_headers(self):
        """更新可见表头"""
        visible_columns = config.get_table_visible_columns()
        self.headers = []
        self.column_mapping = []  # 存储可见列在all_headers中的索引
        
        # 按照visible_columns中的顺序来构建headers
        for header in visible_columns:
            if header in self.all_headers:
                self.headers.append(header)
                # 找到该header在all_headers中的索引
                index = self.all_headers.index(header)
                self.column_mapping.append(index)
        
        # 如果配置为空，显示所有列
        if not self.headers:
            self.headers = self.all_headers.copy()
            self.column_mapping = list(range(len(self.all_headers)))

    def rowCount(self, parent=None):
        return len(self.images)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._get_display_data(index)
        elif role == Qt.ToolTipRole:
            # 显示完整路径作为tooltip
            if 0 <= index.row() < len(self.images):
                img = self.images[index.row()]
                return str(img.path)
        return None

    def _get_display_data(self, index):
        img = self.images[index.row()]
        col = index.column()
        
        # 获取实际的数据列索引
        if col < len(self.column_mapping):
            actual_col = self.column_mapping[col]
        else:
            return None

        # 获取文件大小
        file_size = None
        try:
            if img.path.exists():
                file_size = os.path.getsize(img.path)
        except (OSError, AttributeError):
            file_size = None
        
        mapping = [
            img.path.name,
            img.path.suffix.upper(),
            img.make,
            img.model,
            img.lens_model,
            img.focal_length + "mm",
            "f/" + img.f_number,
            img.iso,
            img.exposure_time,
            f"{img.original_width}×{img.original_height} ({getattr(img, '_param_dict', {}).get('total_pixel', 'N/A')})",
            getattr(img, '_param_dict', {}).get('datetime', 'N/A'),
            getattr(img, '_param_dict', {}).get('geo_info', 'N/A'),
            format_file_size(file_size)  # 文件大小列
        ]
        return mapping[actual_col] if actual_col < len(mapping) else None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return default_flags | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes):
        mime_data = QMimeData()
        encoded = QByteArray()
        stream = QDataStream(encoded, QIODevice.WriteOnly)

        rows = sorted(set(index.row() for index in indexes))
        for row in rows:
            stream.writeInt32(row)
            stream.writeInt32(0)
            stream.writeInt32(0)

        mime_data.setData('application/x-qabstractitemmodeldatalist', encoded)
        return mime_data

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction or not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            return False
        if action != Qt.MoveAction:
            return False

        begin_row = row if row != -1 else parent.row() if parent.isValid() else len(self.images)
        encoded = data.data('application/x-qabstractitemmodeldatalist')
        stream = QDataStream(encoded, QIODevice.ReadOnly)
        dragged_rows = []

        while not stream.atEnd():
            row_data = stream.readInt32()
            stream.readInt32()
            stream.readInt32()
            dragged_rows.append(row_data)

        dragged_rows = sorted(set(dragged_rows), reverse=True)
        moved_items = []

        for r in dragged_rows:
            if 0 <= r < len(self.images):
                moved_items.append(self.images[r])
        moved_items.reverse()

        for r in dragged_rows:
            if 0 <= r < len(self.images):
                self.images.pop(r)

        insert_pos = begin_row
        for item in moved_items:
            if insert_pos <= len(self.images):
                self.images.insert(insert_pos, item)
                insert_pos += 1

        self.layoutChanged.emit()
        self.order_changed.emit()
        return True

def create_control_buttons():
    """创建控制按钮"""
    btn_open_file = QPushButton("打开图片")
    btn_open_folder = QPushButton("打开文件夹")
    btn_clear = QPushButton("清空表格")

    return btn_open_file, btn_open_folder, btn_clear
