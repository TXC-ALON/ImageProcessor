"""
Processor类型定义
定义四大类Processor：边框、模糊、图像变形、水印
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json


class ProcessorCategory(Enum):
    """Processor四大类别"""
    BORDER = "border"          # 边框
    BLUR = "blur"             # 模糊
    TRANSFORM = "transform"   # 图像变形
    WATERMARK = "watermark"   # 水印


class TransformType(Enum):
    """图像变形类型"""
    SQUARE = "square"         # 1:1填充
    RATIO = "ratio"           # 按比例处理
    ROUNDED = "rounded"       # 圆角


@dataclass
class BorderParams:
    """边框参数"""
    border_size: int = 10                    # 边框大小（像素）
    border_color: str = "#ffffff"            # 边框颜色
    sides: str = "tlrb"                      # 边框边：t(top), l(left), r(right), b(bottom)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BorderParams':
        """从字典创建"""
        return cls(**data)


@dataclass
class BlurParams:
    """模糊参数"""
    blur_radius: int = 35                    # 模糊半径
    padding_percent: float = 0.15            # 背景填充百分比
    blend_alpha: float = 0.1                 # 混合透明度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlurParams':
        """从字典创建"""
        return cls(**data)


@dataclass
class TransformParams:
    """图像变形参数"""
    transform_type: TransformType = TransformType.SQUARE  # 变形类型
    target_ratio: Optional[float] = None                  # 目标比例（仅用于RATIO类型）
    radius: Optional[int] = None                         # 圆角半径（仅用于ROUNDED类型）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['transform_type'] = self.transform_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransformParams':
        """从字典创建"""
        data = data.copy()
        data['transform_type'] = TransformType(data['transform_type'])
        return cls(**data)


@dataclass
class WatermarkParams:
    """水印参数"""
    logo_position: str = "left"              # Logo位置：left/right
    logo_enable: bool = True                 # 是否启用Logo
    logo_name: str = "auto"                  # Logo名称：auto表示自动使用照片本身的logo，或指定logo文件名
    bg_color: str = "#ffffff"                # 背景颜色
    font_color_lt: str = "#212121"           # 左上角字体颜色
    bold_font_lt: bool = True                # 左上角是否加粗
    font_color_lb: str = "#424242"           # 左下角字体颜色
    bold_font_lb: bool = False               # 左下角是否加粗
    font_color_rt: str = "#212121"           # 右上角字体颜色
    bold_font_rt: bool = True                # 右上角是否加粗
    font_color_rb: str = "#424242"           # 右下角字体颜色
    bold_font_rb: bool = False               # 右下角是否加粗
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatermarkParams':
        """从字典创建"""
        return cls(**data)


@dataclass
class ProcessorConfig:
    """Processor配置"""
    id: str                                  # 唯一ID
    name: str                                # 配置名称
    category: ProcessorCategory              # 处理器类别
    params: Union[BorderParams, BlurParams, TransformParams, WatermarkParams]  # 参数
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())  # 创建时间
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())  # 更新时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['category'] = self.category.value
        data['params'] = self.params.to_dict()
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessorConfig':
        """从字典创建"""
        data = data.copy()
        category = ProcessorCategory(data['category'])
        
        # 根据类别创建对应的参数对象
        params_data = data['params']
        if category == ProcessorCategory.BORDER:
            params = BorderParams.from_dict(params_data)
        elif category == ProcessorCategory.BLUR:
            params = BlurParams.from_dict(params_data)
        elif category == ProcessorCategory.TRANSFORM:
            params = TransformParams.from_dict(params_data)
        elif category == ProcessorCategory.WATERMARK:
            params = WatermarkParams.from_dict(params_data)
        else:
            raise ValueError(f"未知的Processor类别: {category}")
        
        data['category'] = category
        data['params'] = params
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ProcessorConfig':
        """从JSON字符串创建"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class CompositeProcessorConfig:
    """组合Processor配置"""
    id: str                                  # 唯一ID
    name: str                                # 配置名称
    processor_ids: List[str]                 # 包含的Processor ID列表
    processor_configs: List[ProcessorConfig] = field(default_factory=list)  # Processor配置列表
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())  # 创建时间
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())  # 更新时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['processor_configs'] = [pc.to_dict() for pc in self.processor_configs]
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositeProcessorConfig':
        """从字典创建"""
        data = data.copy()
        
        # 转换Processor配置列表
        processor_configs_data = data.get('processor_configs', [])
        processor_configs = [ProcessorConfig.from_dict(pc_data) for pc_data in processor_configs_data]
        
        data['processor_configs'] = processor_configs
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CompositeProcessorConfig':
        """从JSON字符串创建"""
        data = json.loads(json_str)
        return cls.from_dict(data)


def generate_processor_id(category: ProcessorCategory, timestamp: Optional[str] = None) -> str:
    """生成Processor ID"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{category.value}_{timestamp}"


def generate_composite_processor_id(timestamp: Optional[str] = None) -> str:
    """生成组合Processor ID"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"composite_{timestamp}"


def get_default_processor_name(category: ProcessorCategory) -> str:
    """获取默认的Processor名称"""
    category_names = {
        ProcessorCategory.BORDER: "边框",
        ProcessorCategory.BLUR: "模糊",
        ProcessorCategory.TRANSFORM: "图像变形",
        ProcessorCategory.WATERMARK: "水印"
    }
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{category_names[category]}_{timestamp}"
