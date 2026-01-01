"""
基础效果组件
将常用的图片处理效果抽取为独立的组件，便于组合使用
"""

from PIL import Image, ImageFilter, ImageOps, ImageDraw
from typing import Optional, Tuple
from config.image_config import Config
from core.image_container import ImageContainer
from config.constant import TRANSPARENT
from utils.image_utils import padding_image


class BaseEffect:
    """基础效果类"""
    
    def __init__(self, config: Config = None):
        self.config = config
    
    def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        """应用效果到图片"""
        raise NotImplementedError
    
    def __call__(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        return self.apply(image, container)


class RoundedCornerEffect(BaseEffect):
    """圆角效果"""
    
    def __init__(self, config: Config = None, radius: Optional[int] = None):
        super().__init__(config)
        self.radius = radius
    
    def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        if self.radius is None:
            # 默认圆角半径设为图片较短边的1/10
            self.radius = min(image.width, image.height) // 10
        
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, image.width, image.height), radius=self.radius, fill=255)
        rounded_image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
        rounded_image.putalpha(mask)
        return rounded_image


class ShadowEffect(BaseEffect):
    """阴影效果"""
    
    def __init__(self, config: Config = None, shadow_color: str = '#6B696A', 
                 blur_radius: Optional[int] = None):
        super().__init__(config)
        self.shadow_color = shadow_color
        self.blur_radius = blur_radius
    
    def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        max_pixel = max(image.width, image.height)
        
        if self.blur_radius is None:
            self.blur_radius = int(max_pixel / 512)
        
        # 创建阴影效果
        shadow = Image.new('RGB', image.size, color=self.shadow_color)
        shadow = ImageOps.expand(shadow, 
                                 border=(self.blur_radius * 2, self.blur_radius * 2, 
                                         self.blur_radius * 2, self.blur_radius * 2), 
                                 fill=(255, 255, 255))
        # 模糊阴影
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
        
        # 将原始图像放置在阴影图像上方
        shadow.paste(image, (self.blur_radius, self.blur_radius))
        return shadow


class MarginEffect(BaseEffect):
    """边距效果"""
    
    def __init__(self, config: Config = None, margin_size: Optional[int] = None, 
                 sides: str = 'tlr', color: str = '#ffffff'):
        super().__init__(config)
        self.margin_size = margin_size
        self.sides = sides
        self.color = color
    
    def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        if self.margin_size is None and self.config is not None and container is not None:
            # 从配置获取边距大小
            self.margin_size = int(
                self.config.get_white_margin_width() * 
                min(container.get_width(), container.get_height()) / 100
            )
        elif self.margin_size is None:
            # 默认边距
            self.margin_size = int(min(image.width, image.height) * 0.03)
        
        return padding_image(image, self.margin_size, self.sides, color=self.color)


class BackgroundBlurEffect(BaseEffect):
    """背景虚化效果"""
    
    def __init__(self, config: Config = None, blur_radius: int = 35, 
                 padding_percent: float = 0.15, blend_alpha: float = 0.1):
        super().__init__(config)
        self.blur_radius = blur_radius
        self.padding_percent = padding_percent
        self.blend_alpha = blend_alpha
    
    def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        background = image.copy()
        background = background.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
        
        # 添加白色混合
        fg = Image.new('RGB', background.size, color=(255, 255, 255))
        background = Image.blend(background, fg, self.blend_alpha)
        
        # 调整大小并粘贴原图
        background = background.resize(
            (int(image.width * (1 + self.padding_percent)),
             int(image.height * (1 + self.padding_percent)))
        )
        
        offset_x = int(image.width * self.padding_percent / 2)
        offset_y = int(image.height * self.padding_percent / 2)
        background.paste(image, (offset_x, offset_y))
        
        return background


class BorderEffect(BaseEffect):
    """边框效果"""
    
    def __init__(self, config: Config = None, border_size: Optional[int] = None, 
                 color: str = '#ffffff', sides: str = 'tlrb'):
        super().__init__(config)
        self.border_size = border_size
        self.color = color
        self.sides = sides
    
    def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        if self.border_size is None and self.config is not None and container is not None:
            # 从配置获取边框大小
            self.border_size = int(
                self.config.get_white_margin_width() * 
                min(container.get_width(), container.get_height()) / 100
            )
        elif self.border_size is None:
            # 默认边框大小
            self.border_size = int(min(image.width, image.height) * 0.03)
        
        return padding_image(image, self.border_size, self.sides, color=self.color)


class CompositeEffect(BaseEffect):
    """组合效果，可以按顺序应用多个效果"""
    
    def __init__(self, config: Config = None):
        super().__init__(config)
        self.effects = []
    
    def add(self, effect: BaseEffect):
        """添加效果"""
        self.effects.append(effect)
        return self
    
    def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        result = image
        for effect in self.effects:
            result = effect.apply(result, container)
        return result
