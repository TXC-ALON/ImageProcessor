# 增强版Processor功能

## 概述

本增强版Processor功能为ImageProcesser应用程序添加了强大的Processor配置和管理系统。系统支持四大类Processor（边框、模糊、图像变形、水印），每类Processor都可以参数化配置，并支持自定义创建、组合保存和JSON导入/导出。

## 新功能特性

### 1. 四大类Processor
- **边框Processor**: 支持边框大小、颜色、边（上、下、左、右）配置
- **模糊Processor**: 支持模糊半径、背景填充百分比、混合透明度配置
- **图像变形Processor**: 支持1:1填充、按比例处理、圆角三种变形类型
- **水印Processor**: 支持Logo位置、背景颜色、字体颜色等完整水印配置

### 2. 参数化配置系统
- 所有Processor参数都可以通过GUI界面配置
- 参数自动保存为JSON格式
- 支持参数预览和验证

### 3. 自定义Processor创建
- 通过"新建Processor"按钮创建自定义Processor
- 支持为自定义Processor命名
- 自动生成唯一ID和时间戳

### 4. Processor组合管理
- 可以将多个Processor组合保存为一个复合Processor
- 支持拖拽调整Processor执行顺序
- 组合Processor可以重命名和重复使用

### 5. JSON导入/导出
- 支持将Processor配置导出为JSON文件
- 支持从JSON文件导入Processor配置
- 便于配置共享和备份

## 文件结构

### 核心文件
- `core/processor_types.py` - Processor类型定义和枚举
- `core/configurable_processor.py` - 可配置Processor基类
- `core/composite_processor.py` - 组合Processor实现

### GUI文件
- `gui/processor_creator_dialog.py` - Processor创建对话框
- `gui/processor_control_dialog_enhanced.py` - 增强版Processor控制对话框
- `gui/main_window.py` - 主窗口（已更新使用新对话框）

### 配置文件
- `config/processors/` - 自定义Processor配置存储目录
- `*.json` - Processor配置文件

## 使用方法

### 1. 创建自定义Processor
1. 在主界面点击"配置Processor"按钮
2. 在对话框中点击"+ 新建Processor"按钮
3. 选择Processor类别（边框、模糊、图像变形、水印）
4. 配置相关参数
5. 输入Processor名称（可选，不输入使用默认名称）
6. 点击"创建"按钮

### 2. 配置Processor执行顺序
1. 在左侧列表中选择Processor（默认或自定义）
2. 点击"添加 →"按钮添加到右侧执行列表
3. 在右侧列表中拖拽调整执行顺序
4. 使用"上移"/"下移"按钮微调顺序

### 3. 保存组合Processor
1. 配置好Processor执行顺序后
2. 点击"保存为组合"按钮
3. 输入组合名称
4. 组合Processor将保存到自定义Processor列表中

### 4. 导入/导出配置
1. **导出**: 点击"导出JSON"按钮，选择保存位置
2. **导入**: 点击"导入JSON"按钮，选择配置文件

## API接口

### ProcessorConfig类
```python
class ProcessorConfig:
    id: str                    # 唯一标识符
    name: str                  # 显示名称
    category: ProcessorCategory # 类别（border/blur/transform/watermark）
    params: BaseParams         # 参数对象
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
    
    def to_dict() -> dict      # 转换为字典
    def to_json() -> str       # 转换为JSON字符串
    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessorConfig'  # 从字典创建
```

### 参数类
- `BorderParams`: 边框参数
- `BlurParams`: 模糊参数
- `TransformParams`: 图像变形参数
- `WatermarkParams`: 水印参数

## 测试和演示

### 测试脚本
```bash
# 运行单元测试
python test_enhanced_processor.py

# 运行演示程序
python demo_enhanced_processor.py
```

### 演示模式
演示程序提供三种演示模式：
1. Processor创建演示
2. Processor控制演示
3. 完整工作流程演示

## 技术实现

### 设计模式
- **工厂模式**: Processor创建
- **组合模式**: Processor链和组合Processor
- **观察者模式**: GUI事件处理
- **策略模式**: 不同Processor算法

### 数据持久化
- JSON格式存储
- 自动版本控制
- 错误恢复机制

### 用户界面
- PyQt5实现
- 响应式设计
- 直观的操作流程
- 实时预览功能

## 兼容性

### 向后兼容
- 兼容现有的Processor系统
- 现有配置文件可以继续使用
- 旧版Processor可以导入到新系统

### 向前兼容
- JSON格式设计考虑未来扩展
- 参数结构支持新字段添加
- 类别系统可扩展

## 性能考虑

### 内存管理
- 懒加载Processor配置
- 图片处理时释放内存
- 配置缓存机制

### 处理速度
- 异步GUI操作
- 批量处理优化
- 进度反馈机制

## 故障排除

### 常见问题
1. **Processor创建失败**: 检查参数是否有效
2. **JSON导入失败**: 检查JSON格式是否正确
3. **组合保存失败**: 检查是否有选中的Processor

### 日志记录
- 所有操作都有日志记录
- 错误信息详细记录
- 调试模式支持

## 未来扩展

### 计划功能
1. **模板系统**: 预定义Processor模板
2. **批量编辑**: 批量修改Processor参数
3. **云端同步**: 配置云端备份和同步
4. **AI建议**: 基于图片内容推荐Processor

### 技术改进
1. **性能优化**: 更快的图片处理算法
2. **内存优化**: 减少内存占用
3. **UI改进**: 更直观的用户界面

## 贡献指南

### 开发环境
- Python 3.8+
- PyQt5
- Pillow
- 其他依赖见requirements.txt

### 代码规范
- 遵循PEP 8
- 类型注解
- 文档字符串
- 单元测试

## 许可证

本项目基于MIT许可证开源。

## 联系方式

如有问题或建议，请通过项目issue系统反馈。
