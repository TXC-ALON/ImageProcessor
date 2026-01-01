"""
组合处理器
使用新的效果组件架构，可以灵活组合各种效果
"""

from typing import List, Optional
from config.image_config import Config
from core.image_container import ImageContainer
from core.effects import BaseEffect, CompositeEffect
from core.watermark_effect import WatermarkEffect


class CompositeProcessor:
    """组合处理器，可以组合多个效果"""
    
    def __init__(self, config: Config = None):
        self.config = config
        self.effects: List[BaseEffect] = []
    
    def add_effect(self, effect: BaseEffect) -> 'CompositeProcessor':
        """添加效果"""
        self.effects.append(effect)
        return self
    
    def add_rounded_corner(self, radius: Optional[int] = None) -> 'CompositeProcessor':
        """添加圆角效果"""
        from core.effects import RoundedCornerEffect
        effect = RoundedCornerEffect(self.config, radius)
        return self.add_effect(effect)
    
    def add_shadow(self, shadow_color: str = '#6B696A', blur_radius: Optional[int] = None) -> 'CompositeProcessor':
        """添加阴影效果"""
        from core.effects import ShadowEffect
        effect = ShadowEffect(self.config, shadow_color, blur_radius)
        return self.add_effect(effect)
    
    def add_margin(self, margin_size: Optional[int] = None, 
                   sides: str = 'tlr', color: str = '#ffffff') -> 'CompositeProcessor':
        """添加边距效果"""
        from core.effects import MarginEffect
        effect = MarginEffect(self.config, margin_size, sides, color)
        return self.add_effect(effect)
    
    def add_background_blur(self, blur_radius: int = 35, 
                           padding_percent: float = 0.15, blend_alpha: float = 0.1) -> 'CompositeProcessor':
        """添加背景虚化效果"""
        from core.effects import BackgroundBlurEffect
        effect = BackgroundBlurEffect(self.config, blur_radius, padding_percent, blend_alpha)
        return self.add_effect(effect)
    
    def add_border(self, border_size: Optional[int] = None, 
                  color: str = '#ffffff', sides: str = 'tlrb') -> 'CompositeProcessor':
        """添加边框效果"""
        from core.effects import BorderEffect
        effect = BorderEffect(self.config, border_size, color, sides)
        return self.add_effect(effect)
    
    def add_watermark(self, watermark_effect: WatermarkEffect) -> 'CompositeProcessor':
        """添加水印效果"""
        return self.add_effect(watermark_effect)
    
    def add_watermark_from_config(self) -> 'CompositeProcessor':
        """从配置添加水印效果"""
        watermark = WatermarkEffect.from_config(self.config)
        return self.add_effect(watermark)
    
    def add_dark_watermark(self, logo_position: str = 'left') -> 'CompositeProcessor':
        """添加深色主题水印效果"""
        watermark = WatermarkEffect.create_dark_theme(self.config, logo_position)
        return self.add_effect(watermark)
    
    def add_light_watermark(self, logo_position: str = 'left') -> 'CompositeProcessor':
        """添加浅色主题水印效果"""
        watermark = WatermarkEffect.create_light_theme(self.config, logo_position)
        return self.add_effect(watermark)
    
    def process(self, container: ImageContainer) -> None:
        """处理图片容器"""
        if not self.effects:
            return
        
        # 获取当前图片
        current_image = container.get_watermark_img()
        
        # 按顺序应用所有效果
        for effect in self.effects:
            current_image = effect.apply(current_image, container)
        
        # 更新图片容器
        container.update_watermark_img(current_image)
    
    def clear_effects(self) -> 'CompositeProcessor':
        """清空所有效果"""
        self.effects.clear()
        return self
    
    def get_effect_count(self) -> int:
        """获取效果数量"""
        return len(self.effects)
    
    def get_effect_descriptions(self) -> List[str]:
        """获取效果描述列表"""
        descriptions = []
        for i, effect in enumerate(self.effects):
            effect_type = effect.__class__.__name__
            descriptions.append(f"{i + 1}. {effect_type}")
        return descriptions


# 预定义的常用组合
def create_rounded_corner_blur_shadow_processor(config: Config) -> CompositeProcessor:
    """创建圆角+背景虚化+阴影效果的处理器"""
    processor = CompositeProcessor(config)
    processor.add_rounded_corner()
    processor.add_background_blur()
    processor.add_shadow()
    return processor


def create_rounded_corner_blur_processor(config: Config) -> CompositeProcessor:
    """创建圆角+背景虚化效果的处理器"""
    processor = CompositeProcessor(config)
    processor.add_rounded_corner()
    processor.add_background_blur()
    return processor


def create_rounded_corner_processor(config: Config) -> CompositeProcessor:
    """创建圆角效果的处理器"""
    processor = CompositeProcessor(config)
    processor.add_rounded_corner()
    return processor


def create_background_blur_with_border_processor(config: Config) -> CompositeProcessor:
    """创建背景虚化+边框效果的处理器"""
    processor = CompositeProcessor(config)
    processor.add_background_blur()
    processor.add_border()
    return processor


def create_watermark_with_effects_processor(config: Config, 
                                           watermark_effect: Optional[WatermarkEffect] = None) -> CompositeProcessor:
    """创建带效果的水印处理器"""
    processor = CompositeProcessor(config)
    
    # 添加一些基础效果
    processor.add_rounded_corner()
    processor.add_background_blur()
    
    # 添加水印
    if watermark_effect is None:
        watermark_effect = WatermarkEffect.from_config(config)
    processor.add_watermark(watermark_effect)
    
    return processor
