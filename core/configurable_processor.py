"""
可配置的Processor
基于配置创建Processor，支持四大类别
"""

from typing import Optional, Dict, Any
from PIL import Image, ImageFilter, ImageOps, ImageDraw
from config.image_config import Config
from core.image_container import ImageContainer
from core.image_processor import ProcessorComponent
from core.effects import (
    BorderEffect, BackgroundBlurEffect, RoundedCornerEffect,
    ShadowEffect, MarginEffect, CompositeEffect
)
from core.watermark_effect import WatermarkEffect
from core.processor_types import (
    ProcessorCategory, TransformType, BorderParams, BlurParams,
    TransformParams, WatermarkParams, ProcessorConfig
)
from utils.image_utils import padding_image, square_image, resize_image_with_width


class ConfigurableProcessor(ProcessorComponent):
    """可配置的Processor，基于配置创建"""
    
    def __init__(self, config: Config, processor_config: ProcessorConfig):
        """
        初始化可配置Processor
        
        Args:
            config: 应用配置
            processor_config: Processor配置
        """
        super().__init__(config)
        self.processor_config = processor_config
        self.LAYOUT_ID = processor_config.id
        self.LAYOUT_NAME = processor_config.name
        
        # 根据类别创建对应的效果
        self.effect = self._create_effect()
    
    def _create_effect(self):
        """根据配置创建效果"""
        category = self.processor_config.category
        params = self.processor_config.params
        
        if category == ProcessorCategory.BORDER:
            return self._create_border_effect(params)
        elif category == ProcessorCategory.BLUR:
            return self._create_blur_effect(params)
        elif category == ProcessorCategory.TRANSFORM:
            return self._create_transform_effect(params)
        elif category == ProcessorCategory.WATERMARK:
            return self._create_watermark_effect(params)
        else:
            raise ValueError(f"未知的Processor类别: {category}")
    
    def _create_border_effect(self, params: BorderParams):
        """创建边框效果"""
        return BorderEffect(
            config=self.config,
            border_size=params.border_size,
            color=params.border_color,
            sides=params.sides
        )
    
    def _create_blur_effect(self, params: BlurParams):
        """创建模糊效果"""
        return BackgroundBlurEffect(
            config=self.config,
            blur_radius=params.blur_radius,
            padding_percent=params.padding_percent,
            blend_alpha=params.blend_alpha
        )
    
    def _create_transform_effect(self, params: TransformParams):
        """创建图像变形效果"""
        transform_type = params.transform_type
        
        if transform_type == TransformType.SQUARE:
            # 1:1填充效果
            return self._create_square_effect()
        elif transform_type == TransformType.RATIO:
            # 按比例处理
            return self._create_ratio_effect(params.target_ratio)
        elif transform_type == TransformType.ROUNDED:
            # 圆角效果
            return self._create_rounded_effect(params.radius)
        else:
            raise ValueError(f"未知的图像变形类型: {transform_type}")
    
    def _create_square_effect(self):
        """创建1:1填充效果"""
        class SquareEffect:
            def __init__(self, config):
                self.config = config
            
            def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
                return square_image(image, auto_close=False)
        
        return SquareEffect(self.config)
    
    def _create_ratio_effect(self, target_ratio: Optional[float]):
        """创建按比例处理效果"""
        class RatioEffect:
            def __init__(self, config, target_ratio):
                self.config = config
                self.target_ratio = target_ratio or 1.0  # 默认1:1
            
            def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
                if container is None:
                    return image
                
                current_ratio = container.get_ratio()
                if abs(current_ratio - self.target_ratio) < 0.01:
                    return image
                
                if current_ratio > self.target_ratio:
                    # 当前宽高比大于目标宽高比，需要增加高度
                    new_height = int(image.width / self.target_ratio)
                    result = ImageOps.expand(image, (0, (new_height - image.height) // 2), fill='white')
                else:
                    # 当前宽高比小于目标宽高比，需要增加宽度
                    new_width = int(image.height * self.target_ratio)
                    result = ImageOps.expand(image, ((new_width - image.width) // 2, 0), fill='white')
                
                return result
        
        return RatioEffect(self.config, target_ratio)
    
    def _create_rounded_effect(self, radius: Optional[int]):
        """创建圆角效果"""
        return RoundedCornerEffect(
            config=self.config,
            radius=radius
        )
    
    def _create_watermark_effect(self, params: WatermarkParams):
        """创建水印效果"""
        return WatermarkEffect(
            config=self.config,
            logo_position=params.logo_position,
            logo_enable=params.logo_enable,
            bg_color=params.bg_color,
            font_color_lt=params.font_color_lt,
            bold_font_lt=params.bold_font_lt,
            font_color_lb=params.font_color_lb,
            bold_font_lb=params.bold_font_lb,
            font_color_rt=params.font_color_rt,
            bold_font_rt=params.bold_font_rt,
            font_color_rb=params.font_color_rb,
            bold_font_rb=params.bold_font_rb
        )
    
    def process(self, container: ImageContainer) -> None:
        """处理图片容器"""
        if self.effect is None:
            return
        
        # 获取当前图片
        current_image = container.get_watermark_img()
        
        # 应用效果
        processed_image = self.effect.apply(current_image, container)
        
        # 更新图片容器
        container.update_watermark_img(processed_image)
    
    @classmethod
    def from_config_dict(cls, config: Config, config_dict: Dict[str, Any]) -> 'ConfigurableProcessor':
        """从配置字典创建Processor"""
        processor_config = ProcessorConfig.from_dict(config_dict)
        return cls(config, processor_config)
    
    @classmethod
    def from_json(cls, config: Config, json_str: str) -> 'ConfigurableProcessor':
        """从JSON字符串创建Processor"""
        processor_config = ProcessorConfig.from_json(json_str)
        return cls(config, processor_config)


class ConfigurableCompositeProcessor(ProcessorComponent):
    """可配置的组合Processor"""
    
    def __init__(self, config: Config, processor_configs: list[ProcessorConfig], 
                 name: Optional[str] = None, processor_id: Optional[str] = None):
        """
        初始化可配置组合Processor
        
        Args:
            config: 应用配置
            processor_configs: Processor配置列表
            name: 组合Processor名称
            processor_id: 组合Processor ID
        """
        super().__init__(config)
        
        # 生成ID和名称
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        self.processor_id = processor_id or f"composite_{timestamp}"
        self.processor_name = name or f"组合Processor_{timestamp}"
        
        self.LAYOUT_ID = self.processor_id
        self.LAYOUT_NAME = self.processor_name
        
        # 创建Processor列表
        self.processors = []
        for processor_config in processor_configs:
            processor = ConfigurableProcessor(config, processor_config)
            self.processors.append(processor)
    
    def process(self, container: ImageContainer) -> None:
        """处理图片容器，按顺序应用所有Processor"""
        for processor in self.processors:
            processor.process(container)
    
    def add_processor(self, processor_config: ProcessorConfig) -> None:
        """添加Processor到组合"""
        processor = ConfigurableProcessor(self.config, processor_config)
        self.processors.append(processor)
    
    def remove_processor(self, index: int) -> None:
        """从组合中移除Processor"""
        if 0 <= index < len(self.processors):
            del self.processors[index]
    
    def clear_processors(self) -> None:
        """清空所有Processor"""
        self.processors.clear()
    
    def get_processor_count(self) -> int:
        """获取Processor数量"""
        return len(self.processors)
    
    def get_processor_descriptions(self) -> list[str]:
        """获取Processor描述列表"""
        descriptions = []
        for i, processor in enumerate(self.processors):
            descriptions.append(f"{i + 1}. {processor.LAYOUT_NAME} ({processor.LAYOUT_ID})")
        return descriptions


# 工具函数：创建默认的Processor配置
def create_default_border_config(name: Optional[str] = None) -> ProcessorConfig:
    """创建默认的边框配置"""
    from core.processor_types import (
        ProcessorCategory, BorderParams, generate_processor_id, get_default_processor_name
    )
    
    category = ProcessorCategory.BORDER
    processor_id = generate_processor_id(category)
    processor_name = name or get_default_processor_name(category)
    
    return ProcessorConfig(
        id=processor_id,
        name=processor_name,
        category=category,
        params=BorderParams()
    )


def create_default_blur_config(name: Optional[str] = None) -> ProcessorConfig:
    """创建默认的模糊配置"""
    from core.processor_types import (
        ProcessorCategory, BlurParams, generate_processor_id, get_default_processor_name
    )
    
    category = ProcessorCategory.BLUR
    processor_id = generate_processor_id(category)
    processor_name = name or get_default_processor_name(category)
    
    return ProcessorConfig(
        id=processor_id,
        name=processor_name,
        category=category,
        params=BlurParams()
    )


def create_default_transform_config(transform_type: TransformType = TransformType.SQUARE, 
                                   name: Optional[str] = None) -> ProcessorConfig:
    """创建默认的图像变形配置"""
    from core.processor_types import (
        ProcessorCategory, TransformParams, generate_processor_id, get_default_processor_name
    )
    
    category = ProcessorCategory.TRANSFORM
    processor_id = generate_processor_id(category)
    
    # 根据变形类型生成名称
    if name is None:
        transform_names = {
            TransformType.SQUARE: "1:1填充",
            TransformType.RATIO: "按比例处理",
            TransformType.ROUNDED: "圆角"
        }
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        processor_name = f"{transform_names[transform_type]}_{timestamp}"
    else:
        processor_name = name
    
    return ProcessorConfig(
        id=processor_id,
        name=processor_name,
        category=category,
        params=TransformParams(transform_type=transform_type)
    )


def create_default_watermark_config(name: Optional[str] = None) -> ProcessorConfig:
    """创建默认的水印配置"""
    from core.processor_types import (
        ProcessorCategory, WatermarkParams, generate_processor_id, get_default_processor_name
    )
    
    category = ProcessorCategory.WATERMARK
    processor_id = generate_processor_id(category)
    processor_name = name or get_default_processor_name(category)
    
    return ProcessorConfig(
        id=processor_id,
        name=processor_name,
        category=category,
        params=WatermarkParams()
    )
