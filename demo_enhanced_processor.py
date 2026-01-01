"""
增强版Processor功能演示
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui.processor_control_dialog_enhanced import ProcessorControlDialogEnhanced
from gui.processor_creator_dialog import ProcessorCreatorDialog
from core.processor_types import (
    ProcessorCategory, TransformType, BorderParams, BlurParams,
    TransformParams, WatermarkParams, ProcessorConfig
)
from config.image_config import Config

def demo_processor_creation():
    """演示Processor创建功能"""
    app = QApplication(sys.argv)
    config = Config()
    
    print("演示：创建自定义Processor")
    print("=" * 60)
    
    # 创建Processor创建对话框
    creator_dialog = ProcessorCreatorDialog(config)
    
    def on_processor_created(processor_config):
        """当Processor创建完成时的回调"""
        print(f"\n✅ 成功创建Processor:")
        print(f"   名称: {processor_config.name}")
        print(f"   ID: {processor_config.id}")
        print(f"   类别: {processor_config.category}")
        print(f"   参数: {processor_config.params}")
        
        # 显示JSON配置
        json_str = processor_config.to_json()
        print(f"\n📋 JSON配置:")
        print(json_str)
        
        QMessageBox.information(creator_dialog, "成功", 
                               f"Processor '{processor_config.name}' 创建成功！\n\n"
                               f"ID: {processor_config.id}\n"
                               f"类别: {processor_config.category}")
    
    # 连接信号
    creator_dialog.processor_created.connect(on_processor_created)
    
    print("请在弹出的窗口中创建Processor...")
    creator_dialog.exec_()
    
    return app

def demo_processor_control():
    """演示Processor控制功能"""
    app = QApplication(sys.argv)
    
    print("\n演示：Processor控制和管理")
    print("=" * 60)
    
    # 创建Processor控制对话框
    control_dialog = ProcessorControlDialogEnhanced()
    
    print("功能说明:")
    print("1. 左侧显示默认Processor和自定义Processor")
    print("2. 点击'+ 新建Processor'按钮可以创建新的Processor")
    print("3. 选择Processor后点击'添加 →'按钮添加到右侧执行列表")
    print("4. 在右侧列表中拖拽调整Processor执行顺序")
    print("5. 点击'保存为组合'可以将当前选择的Processor保存为组合")
    print("6. 支持JSON导入/导出功能")
    
    control_dialog.show()
    
    return app, control_dialog

def demo_workflow():
    """演示完整工作流程"""
    print("\n演示：完整工作流程")
    print("=" * 60)
    print("1. 创建自定义Processor")
    print("2. 配置Processor执行顺序")
    print("3. 保存为组合Processor")
    print("4. 导出JSON配置")
    print("5. 导入JSON配置")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    config = Config()
    
    # 创建一些示例Processor配置
    print("\n📝 创建示例Processor配置...")
    
    # 边框Processor
    border_config = ProcessorConfig(
        id="demo_border_001",
        name="演示边框",
        category=ProcessorCategory.BORDER,
        params=BorderParams(
            border_size=20,
            border_color="#00ff00",
            sides="tlrb"
        )
    )
    
    # 模糊Processor
    blur_config = ProcessorConfig(
        id="demo_blur_001",
        name="演示模糊",
        category=ProcessorCategory.BLUR,
        params=BlurParams(
            blur_radius=25,
            padding_percent=0.1,
            blend_alpha=0.05
        )
    )
    
    print(f"✅ 创建边框Processor: {border_config.name}")
    print(f"✅ 创建模糊Processor: {blur_config.name}")
    
    # 显示JSON配置
    print(f"\n📋 边框Processor JSON:")
    print(border_config.to_json())
    
    print(f"\n📋 模糊Processor JSON:")
    print(blur_config.to_json())
    
    # 创建控制对话框并添加示例Processor
    control_dialog = ProcessorControlDialogEnhanced()
    
    # 模拟添加Processor到对话框
    print("\n🔧 在控制对话框中添加示例Processor...")
    print("（在实际应用中，可以通过'新建Processor'按钮创建）")
    
    QMessageBox.information(None, "演示完成", 
                           "演示完成！\n\n"
                           "新功能包括：\n"
                           "1. 四大类Processor（边框、模糊、图像变形、水印）\n"
                           "2. 参数化配置系统\n"
                           "3. 自定义Processor创建\n"
                           "4. Processor组合保存\n"
                           "5. JSON导入/导出\n\n"
                           "请运行主程序测试完整功能。")
    
    return app

def main():
    """主演示函数"""
    print("=" * 60)
    print("增强版Processor功能演示")
    print("=" * 60)
    
    print("\n请选择演示模式:")
    print("1. Processor创建演示")
    print("2. Processor控制演示")
    print("3. 完整工作流程演示")
    print("4. 运行主程序")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        demo_processor_creation()
    elif choice == "2":
        app, dialog = demo_processor_control()
        sys.exit(app.exec_())
    elif choice == "3":
        demo_workflow()
    elif choice == "4":
        print("\n运行主程序...")
        print("python main.py")
        import subprocess
        subprocess.run([sys.executable, "main.py"])
    else:
        print("无效选择")

if __name__ == "__main__":
    main()
