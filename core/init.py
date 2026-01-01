from dataclasses import dataclass

from config.image_config import Config

from .image_processor import EmptyProcessor
from .image_processor import ShadowProcessor
from .image_processor import MarginProcessor
from .image_processor import SimpleProcessor
from .image_processor import WatermarkProcessor
from .image_processor import WatermarkLeftLogoProcessor
from .image_processor import WatermarkRightLogoProcessor
from .image_processor import DarkWatermarkLeftLogoProcessor
from .image_processor import DarkWatermarkRightLogoProcessor
from .image_processor import SquareProcessor
from .image_processor import PaddingToOriginalRatioProcessor
from .image_processor import BackgroundBlurProcessor
from .image_processor import BackgroundBlurWithWhiteBorderProcessor
from .image_processor import PureWhiteMarginProcessor
from .image_processor import CustomWatermarkProcessor
from .image_processor import RoundedCornerProcessor
from .image_processor import RoundedCornerBlurProcessor
from .image_processor import RoundedCornerBlurShadowProcessor

# 新的组件架构
from .effects import (
    RoundedCornerEffect,
    ShadowEffect,
    MarginEffect,
    BackgroundBlurEffect,
    BorderEffect,
    CompositeEffect
)
from .watermark_effect import WatermarkEffect
from .composite_processor import (
    CompositeProcessor,
    create_rounded_corner_blur_shadow_processor,
    create_rounded_corner_blur_processor,
    create_rounded_corner_processor,
    create_background_blur_with_border_processor,
    create_watermark_with_effects_processor
)

# 可配置的水印处理器
from .configurable_watermark_processor import (
    ConfigurableWatermarkProcessor,
    CustomThemeWatermarkProcessor,
    create_dark_theme_processor,
    create_light_theme_processor,
    create_red_theme_processor,
    create_blue_theme_processor
)

# 读取配置
config = Config('config.yaml')

EMPTY_PROCESSOR = EmptyProcessor(config)
SHADOW_PROCESSOR = ShadowProcessor(config)
MARGIN_PROCESSOR = MarginProcessor(config)
SIMPLE_PROCESSOR = SimpleProcessor(config)
WATERMARK_PROCESSOR = WatermarkProcessor(config)
WATERMARK_LEFT_LOGO_PROCESSOR = WatermarkLeftLogoProcessor(config)
WATERMARK_RIGHT_LOGO_PROCESSOR = WatermarkRightLogoProcessor(config)
DARK_WATERMARK_LEFT_LOGO_PROCESSOR = DarkWatermarkLeftLogoProcessor(config)
DARK_WATERMARK_RIGHT_LOGO_PROCESSOR = DarkWatermarkRightLogoProcessor(config)
SQUARE_PROCESSOR = SquareProcessor(config)
PADDING_TO_ORIGINAL_RATIO_PROCESSOR = PaddingToOriginalRatioProcessor(config)
BACKGROUND_BLUR_PROCESSOR = BackgroundBlurProcessor(config)
BACKGROUND_BLUR_WITH_WHITE_BORDER_PROCESSOR = BackgroundBlurWithWhiteBorderProcessor(config)
PURE_WHITE_MARGIN_PROCESSOR = PureWhiteMarginProcessor(config)
ROUNDED_CORNER_PROCESSOR = RoundedCornerProcessor(config)
ROUNDED_CORNER_BLUR_PROCESSOR = RoundedCornerBlurProcessor(config)
ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR = RoundedCornerBlurShadowProcessor(config)


SEPARATE_LINE = '+' + '-' * 15 + '+' + '-' * 15 + '+'


from .image_processor import ProcessorComponent

@dataclass
class ElementItem(object):
    name: str
    value: str
@dataclass
class LayoutItem(object):
    name: str
    value: str
    processor: ProcessorComponent
    @staticmethod
    def from_processor(processor: ProcessorComponent):
        return LayoutItem(processor.LAYOUT_NAME, processor.LAYOUT_ID, processor)

LAYOUT_ITEMS = [
    LayoutItem.from_processor(SIMPLE_PROCESSOR),
    LayoutItem.from_processor(SHADOW_PROCESSOR),
    LayoutItem.from_processor(MARGIN_PROCESSOR),

    LayoutItem.from_processor(SQUARE_PROCESSOR),
    LayoutItem.from_processor(PADDING_TO_ORIGINAL_RATIO_PROCESSOR),

    LayoutItem.from_processor(BACKGROUND_BLUR_PROCESSOR),
    LayoutItem.from_processor(BACKGROUND_BLUR_WITH_WHITE_BORDER_PROCESSOR),
    LayoutItem.from_processor(PURE_WHITE_MARGIN_PROCESSOR),


    LayoutItem.from_processor(ROUNDED_CORNER_PROCESSOR),
    LayoutItem.from_processor(ROUNDED_CORNER_BLUR_PROCESSOR),
    LayoutItem.from_processor(ROUNDED_CORNER_BLUR_SHADOW_PROCESSOR),

    # 水印处理器
    LayoutItem.from_processor(WATERMARK_LEFT_LOGO_PROCESSOR),
    LayoutItem.from_processor(WATERMARK_RIGHT_LOGO_PROCESSOR),
    LayoutItem.from_processor(DARK_WATERMARK_LEFT_LOGO_PROCESSOR),
    LayoutItem.from_processor(DARK_WATERMARK_RIGHT_LOGO_PROCESSOR),

]
layout_items_dict = {item.value: item for item in LAYOUT_ITEMS}
