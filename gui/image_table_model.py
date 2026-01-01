from PyQt5.QtCore import QAbstractTableModel, Qt, QByteArray, QDataStream, QIODevice, pyqtSignal
from PyQt5.QtCore import QMimeData
from typing import List
from core.image_container import ImageContainer
from PyQt5.QtWidgets import (QPushButton, QTableView, QAbstractItemView,
                             QGroupBox, QFormLayout, QLineEdit, QComboBox,
                             QCheckBox, QHBoxLayout, QWidget, QVBoxLayout)

class ImageTableModel(QAbstractTableModel):
    order_changed = pyqtSignal()

    def __init__(self, images: List[ImageContainer]):
        super().__init__()
        self.images = images
        self.headers = [
            "文件名", "后缀名", "相机品牌", "相机型号", "镜头型号",
            "焦距", "光圈", "ISO", "曝光时间", "分辨率", "拍摄时间", "GPS信息"
        ]

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
            getattr(img, '_param_dict', {}).get('geo_info', 'N/A')
        ]
        return mapping[col] if col < len(mapping) else None

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
