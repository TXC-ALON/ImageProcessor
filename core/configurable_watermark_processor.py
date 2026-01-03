"""
可配置的水印处理器
使用用户通过水印配置对话框设置的参数来创建水印效果
"""

from config.image_config import Config
from core.image_container import ImageContainer
from core.image_processor import ProcessorComponent
from core.watermark_effect import WatermarkEffect


class ConfigurableWatermarkProcessor(ProcessorComponent):
    """可配置的水印处理器，使用当前配置创建水印"""
    
    LAYOUT_ID = 'configurable_watermark'
    LAYOUT_NAME = '可配置水印'
    
    def __init__(self, config: Config):
        super().__init__(config)
        # 从配置创建水印效果
        self.watermark_effect = WatermarkEffect.from_config(config)
    
    def process(self, container: ImageContainer) -> None:
        """处理图片容器，应用配置的水印效果"""
        # 获取当前图片
        current_image = container.get_watermark_img()
        
        # 应用水印效果
        watermarked_image = self.watermark_effect.apply(current_image, container)
        
        # 更新图片容器
        container.update_watermark_img(watermarked_image)


class CustomThemeWatermarkProcessor(ProcessorComponent):
    """自定义主题水印处理器，使用指定的主题参数"""
    
    LAYOUT_ID = 'custom_theme_watermark'
    LAYOUT_NAME = '自定义主题水印'
    
    def __init__(self, config: Config, 
                 logo_position: str = 'left',
                 logo_name: str = 'auto',
                 bg_color: str = '#ffffff',
                 font_color_lt: str = '#212121',
                 bold_font_lt: bool = True,
                 font_color_lb: str = '#424242',
                 bold_font_lb: bool = False,
                 font_color_rt: str = '#212121',
                 bold_font_rt: bool = True,
                 font_color_rb: str = '#424242',
                 bold_font_rb: bool = False):
        super().__init__(config)
        
        # 创建自定义水印效果
        self.watermark_effect = WatermarkEffect(
            config=config,
            logo_position=logo_position,
            logo_enable=True,
            logo_name=logo_name,
            bg_color=bg_color,
            font_color_lt=font_color_lt,
            bold_font_lt=bold_font_lt,
            font_color_lb=font_color_lb,
            bold_font_lb=bold_font_lb,
            font_color_rt=font_color_rt,
            bold_font_rt=bold_font_rt,
            font_color_rb=font_color_rb,
            bold_font_rb=bold_font_rb
        )
    
    def process(self, container: ImageContainer) -> None:
        """处理图片容器，应用自定义主题水印效果"""
        # 获取当前图片
        current_image = container.get_watermark_img()
        
        # 应用水印效果
        watermarked_image = self.watermark_effect.apply(current_image, container)
        
        # 更新图片容器
        container.update_watermark_img(watermarked_image)


# 预定义的主题处理器
def create_dark_theme_processor(config: Config, logo_position: str = 'left'):
    """创建深色主题水印处理器"""
    return CustomThemeWatermarkProcessor(
        config=config,
        logo_position=logo_position,
        bg_color='#212121',
        font_color_lt='#D32F2F',
        bold_font_lt=True,
        font_color_lb='#d4d1cc',
        bold_font_lb=False,
        font_color_rt='#D32F2F',
        bold_font_rt=True,
        font_color_rb='#d4d1cc',
        bold_font_rb=False
    )


def create_light_theme_processor(config: Config, logo_position: str = 'left'):
    """创建浅色主题水印处理器"""
    return CustomThemeWatermarkProcessor(
        config=config,
        logo_position=logo_position,
        bg_color='#ffffff',
        font_color_lt='#212121',
        bold_font_lt=True,
        font_color_lb='#424242',
        bold_font_lb=False,
        font_color_rt='#212121',
        bold_font_rt=True,
        font_color_rb='#424242',
        bold_font_rb=False
    )


def create_red_theme_processor(config: Config, logo_position: str = 'left'):
    """创建红色主题水印处理器"""
    return CustomThemeWatermarkProcessor(
        config=config,
        logo_position=logo_position,
        bg_color='#ffffff',
        font_color_lt='#D32F2F',
        bold_font_lt=True,
        font_color_lb='#757575',
        bold_font_lb=False,
        font_color_rt='#D32F2F',
        bold_font_rt=True,
        font_color_rb='#757575',
        bold_font_rb=False
    )


def create_blue_theme_processor(config: Config, logo_position: str = 'left'):
    """创建蓝色主题水印处理器"""
    return CustomThemeWatermarkProcessor(
        config=config,
        logo_position=logo_position,
        bg_color='#ffffff',
        font_color_lt='#1976D2',
        bold_font_lt=True,
        font_color_lb='#424242',
        bold_font_lb=False,
        font_color_rt='#1976D2',
        bold_font_rt=True,
        font_color_rb='#424242',
        bold_font_rb=False
    )
