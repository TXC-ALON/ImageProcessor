"""
测试增强版Processor功能
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.processor_control_dialog_enhanced import ProcessorControlDialogEnhanced
from gui.processor_creator_dialog import ProcessorCreatorDialog
from core.processor_types import (
    ProcessorCategory, TransformType, BorderParams, BlurParams,
    TransformParams, WatermarkParams, ProcessorConfig
)
from config.image_config import Config

def test_processor_creator():
    """测试Processor创建对话框"""
    app = QApplication(sys.argv)
    config = Config()
    
    print("测试Processor创建对话框...")
    dialog = ProcessorCreatorDialog(config)
    dialog.show()
    
    # 测试各种Processor类别
    print("1. 测试边框Processor...")
    dialog.category_combo.setCurrentIndex(0)  # 边框
    dialog.on_category_changed(0)
    
    print("2. 测试模糊Processor...")
    dialog.category_combo.setCurrentIndex(1)  # 模糊
    dialog.on_category_changed(1)
    
    print("3. 测试图像变形Processor...")
    dialog.category_combo.setCurrentIndex(2)  # 图像变形
    dialog.on_category_changed(2)
    
    print("4. 测试水印Processor...")
    dialog.category_combo.setCurrentIndex(3)  # 水印
    dialog.on_category_changed(3)
    
    print("Processor创建对话框测试完成")
    return dialog

def test_processor_control():
    """测试Processor控制对话框"""
    app = QApplication(sys.argv)
    config = Config()
    
    print("测试Processor控制对话框...")
    dialog = ProcessorControlDialogEnhanced()
    dialog.show()
    
    # 测试加载默认Processor
    print("1. 默认Processor数量:", dialog.default_list.count())
    
    # 测试创建自定义Processor
    print("2. 测试创建自定义Processor...")
    
    # 创建一个测试Processor配置
    test_config = ProcessorConfig(
        id="test_border_001",
        name="测试边框",
        category=ProcessorCategory.BORDER,
        params=BorderParams(
            border_size=10,
            border_color="#ff0000",
            sides="tlrb"
        )
    )
    
    # 模拟Processor创建
    dialog.on_processor_created(test_config)
    print("3. 自定义Processor数量:", dialog.custom_list.count())
    
    print("Processor控制对话框测试完成")
    return dialog

def test_json_serialization():
    """测试JSON序列化/反序列化"""
    print("测试JSON序列化/反序列化...")
    
    # 创建测试配置
    border_config = ProcessorConfig(
        id="border_001",
        name="红色边框",
        category=ProcessorCategory.BORDER,
        params=BorderParams(
            border_size=15,
            border_color="#ff0000",
            sides="tlrb"
        )
    )
    
    blur_config = ProcessorConfig(
        id="blur_001",
        name="背景模糊",
        category=ProcessorCategory.BLUR,
        params=BlurParams(
            blur_radius=35,
            padding_percent=0.15,
            blend_alpha=0.1
        )
    )
    
    transform_config = ProcessorConfig(
        id="transform_001",
        name="1:1填充",
        category=ProcessorCategory.TRANSFORM,
        params=TransformParams(
            transform_type=TransformType.SQUARE,
            target_ratio=None,
            radius=None
        )
    )
    
    # 测试序列化
    print("1. 测试序列化...")
    border_json = border_config.to_json()
    print(f"边框配置JSON:\n{border_json}")
    
    blur_json = blur_config.to_json()
    print(f"模糊配置JSON:\n{blur_json}")
    
    # 测试反序列化
    print("\n2. 测试反序列化...")
    border_dict = border_config.to_dict()
    restored_border = ProcessorConfig.from_dict(border_dict)
    print(f"恢复的边框配置: {restored_border.name}")
    
    blur_dict = blur_config.to_dict()
    restored_blur = ProcessorConfig.from_dict(blur_dict)
    print(f"恢复的模糊配置: {restored_blur.name}")
    
    print("JSON序列化/反序列化测试完成")

def main():
    """主测试函数"""
    print("=" * 60)
    print("开始测试增强版Processor功能")
    print("=" * 60)
    
    # 测试JSON序列化
    test_json_serialization()
    
    print("\n" + "=" * 60)
    print("注意：GUI测试需要手动运行")
    print("请运行以下命令测试GUI功能：")
    print("python -c \"import sys; from PyQt5.QtWidgets import QApplication; from gui.processor_control_dialog_enhanced import ProcessorControlDialogEnhanced; app = QApplication(sys.argv); dialog = ProcessorControlDialogEnhanced(); dialog.show(); sys.exit(app.exec_())\"")
    print("=" * 60)
    
    print("\n所有测试完成！")

if __name__ == "__main__":
    main()
