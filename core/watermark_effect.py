"""
可配置的水印效果组件
支持配置水印的颜色、位置、字体、字体大小等参数
"""

from PIL import Image, ImageOps
from typing import Optional, Dict, Any
from config.image_config import Config
from core.image_container import ImageContainer
from config.constant import TRANSPARENT, GRAY
from utils.image_utils import (append_image_by_side, concatenate_image, merge_images,
                              padding_image, resize_image_with_width, text_to_image)

from .effects import BaseEffect


class WatermarkEffect(BaseEffect):
    """可配置的水印效果"""
    
    def __init__(self, config: Config = None, 
                 # 水印位置配置
                 logo_position: str = 'left',  # 'left' 或 'right'
                 logo_enable: bool = True,
                 
                 # 颜色配置
                 bg_color: str = '#ffffff',
                 line_color: str = GRAY,
                 
                 # 字体颜色配置
                 font_color_lt: str = '#212121',  # 左上角
                 bold_font_lt: bool = True,
                 font_color_lb: str = '#424242',  # 左下角
                 bold_font_lb: bool = False,
                 font_color_rt: str = '#212121',  # 右上角
                 bold_font_rt: bool = True,
                 font_color_rb: str = '#424242',  # 右下角
                 bold_font_rb: bool = False,
                 
                 # 布局配置
                 normal_height: int = 1000,
                 padding_ratio_factor: float = 0.02):
        super().__init__(config)
        
        # 水印位置配置
        self.logo_position = logo_position
        self.logo_enable = logo_enable
        
        # 颜色配置
        self.bg_color = bg_color
        self.line_color = line_color
        
        # 字体颜色配置
        self.font_color_lt = font_color_lt
        self.bold_font_lt = bold_font_lt
        self.font_color_lb = font_color_lb
        self.bold_font_lb = bold_font_lb
        self.font_color_rt = font_color_rt
        self.bold_font_rt = bold_font_rt
        self.font_color_rb = font_color_rb
        self.bold_font_rb = bold_font_rb
        
        # 布局配置
        self.normal_height = normal_height
        self.padding_ratio_factor = padding_ratio_factor
        
        # 预定义的间隙图像
        self.small_horizontal_gap = Image.new('RGBA', (50, 20), color=TRANSPARENT)
        self.middle_horizontal_gap = Image.new('RGBA', (100, 20), color=TRANSPARENT)
        self.large_horizontal_gap = Image.new('RGBA', (200, 20), color=TRANSPARENT)
        self.small_vertical_gap = Image.new('RGBA', (20, 50), color=TRANSPARENT)
        self.middle_vertical_gap = Image.new('RGBA', (20, 100), color=TRANSPARENT)
        self.large_vertical_gap = Image.new('RGBA', (20, 200), color=TRANSPARENT)
        self.line_gray = Image.new('RGBA', (20, self.normal_height), color=self.line_color)
        self.line_transparent = Image.new('RGBA', (20, self.normal_height), color=TRANSPARENT)
    
    def is_logo_left(self) -> bool:
        """判断Logo是否在左侧"""
        return self.logo_position == 'left'
    
    def apply(self, image: Image.Image, container: Optional[ImageContainer] = None) -> Image.Image:
        """应用水印效果到图片"""
        if container is None:
            raise ValueError("WatermarkEffect需要ImageContainer对象")
        
        config = self.config
        if config is None:
            raise ValueError("WatermarkEffect需要Config对象")
        
        # 设置背景颜色
        config.bg_color = self.bg_color
        
        # 计算水印比例
        ratio = (.04 if container.get_ratio() >= 1 else .09) + 0.02 * config.get_font_padding_level()
        padding_ratio = (.52 if container.get_ratio() >= 1 else .7) - 0.04 * config.get_font_padding_level()
        
        # 创建空白水印图片
        watermark = Image.new('RGBA', 
                             (int(self.normal_height / ratio), self.normal_height), 
                             color=self.bg_color)
        
        with Image.new('RGBA', (10, 100), color=self.bg_color) as empty_padding:
            # 创建左侧文字内容
            left_top = text_to_image(
                container.get_attribute_str(config.get_left_top()),
                config.get_font(),
                config.get_bold_font(),
                is_bold=self.bold_font_lt,
                fill=self.font_color_lt
            )
            left_bottom = text_to_image(
                container.get_attribute_str(config.get_left_bottom()),
                config.get_font(),
                config.get_bold_font(),
                is_bold=self.bold_font_lb,
                fill=self.font_color_lb
            )
            left = concatenate_image([left_top, empty_padding, left_bottom])
            
            # 创建右侧文字内容
            right_top = text_to_image(
                container.get_attribute_str(config.get_right_top()),
                config.get_font(),
                config.get_bold_font(),
                is_bold=self.bold_font_rt,
                fill=self.font_color_rt
            )
            right_bottom = text_to_image(
                container.get_attribute_str(config.get_right_bottom()),
                config.get_font(),
                config.get_bold_font(),
                is_bold=self.bold_font_rb,
                fill=self.font_color_rb
            )
            right = concatenate_image([right_top, empty_padding, right_bottom])
        
        # 将左右两边的文字内容等比例缩放到相同的高度
        max_height = max(left.height, right.height)
        left = padding_image(left, int(max_height * padding_ratio), 'tb')
        right = padding_image(right, int(max_height * padding_ratio), 't')
        right = padding_image(right, left.height - right.height, 'b')
        
        # 加载Logo
        logo = config.load_logo(container.make) if self.logo_enable else None
        
        if self.logo_enable:
            if self.is_logo_left():
                # Logo在左侧
                line = self.line_transparent.copy()
                if logo is not None:
                    logo = padding_image(logo, int(padding_ratio * logo.height))
                append_image_by_side(watermark, [line, logo, left], is_start=logo is None)
                append_image_by_side(watermark, [right], side='right')
            else:
                # Logo在右侧
                if logo is not None:
                    logo = padding_image(logo, int(padding_ratio * logo.height))
                    line = padding_image(self.line_gray, int(padding_ratio * self.line_gray.height * .8))
                else:
                    line = self.line_transparent.copy()
                append_image_by_side(watermark, [left], is_start=True)
                append_image_by_side(watermark, [logo, line, right], side='right')
                line.close()
        else:
            append_image_by_side(watermark, [left], is_start=True)
            append_image_by_side(watermark, [right], side='right')
        
        left.close()
        right.close()
        
        # 缩放水印大小
        watermark = resize_image_with_width(watermark, container.get_width())
        
        # 将水印图片放置在原始图片的下方
        bg = ImageOps.expand(
            image.convert('RGBA'),
            border=(0, 0, 0, watermark.height),
            fill=self.bg_color
        )
        fg = ImageOps.expand(
            watermark,
            border=(0, container.get_height(), 0, 0),
            fill=TRANSPARENT
        )
        result = Image.alpha_composite(bg, fg)
        watermark.close()
        
        # 更新图片对象
        result = ImageOps.exif_transpose(result).convert('RGB')
        return result
    
    @classmethod
    def from_config(cls, config: Config) -> 'WatermarkEffect':
        """从配置创建水印效果"""
        return cls(
            config=config,
            logo_position='left' if config.is_logo_left() else 'right',
            logo_enable=config.has_logo_enabled(),
            bg_color=config.get_background_color(),
            font_color_lt=config.get_left_top().get_color(),
            bold_font_lt=config.get_left_top().is_bold(),
            font_color_lb=config.get_left_bottom().get_color(),
            bold_font_lb=config.get_left_bottom().is_bold(),
            font_color_rt=config.get_right_top().get_color(),
            bold_font_rt=config.get_right_top().is_bold(),
            font_color_rb=config.get_right_bottom().get_color(),
            bold_font_rb=config.get_right_bottom().is_bold()
        )
    
    @classmethod
    def create_dark_theme(cls, config: Config, logo_position: str = 'left') -> 'WatermarkEffect':
        """创建深色主题的水印效果"""
        return cls(
            config=config,
            logo_position=logo_position,
            logo_enable=True,
            bg_color='#212121',
            line_color=GRAY,
            font_color_lt='#D32F2F',
            bold_font_lt=True,
            font_color_lb='#d4d1cc',
            bold_font_lb=False,
            font_color_rt='#D32F2F',
            bold_font_rt=True,
            font_color_rb='#d4d1cc',
            bold_font_rb=False
        )
    
    @classmethod
    def create_light_theme(cls, config: Config, logo_position: str = 'left') -> 'WatermarkEffect':
        """创建浅色主题的水印效果"""
        return cls(
            config=config,
            logo_position=logo_position,
            logo_enable=True,
            bg_color='#ffffff',
            line_color=GRAY,
            font_color_lt='#212121',
            bold_font_lt=True,
            font_color_lb='#424242',
            bold_font_lb=False,
            font_color_rt='#212121',
            bold_font_rt=True,
            font_color_rb='#424242',
            bold_font_rb=False
        )
