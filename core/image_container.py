import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.Image import Transpose
from dateutil import parser

from config.image_config import ElementConfig
from config.constant import *
from config.enums import ExifId
from utils.exif_utils import calculate_pixel_count, extract_attribute ,extract_gps_info,extract_gps_lat_and_long,get_exif

logger = logging.getLogger(__name__)
PATTERN = re.compile(r"(\d+)\.")  # 匹配小数


def get_datetime(exif) -> datetime:
    dt = datetime.now()
    try:
        dt = parser.parse(extract_attribute(exif, ExifId.DATETIME.value,
                                            default_value=str(datetime.now())))
    except ValueError as e:
        logger.info(f'Error: 时间格式错误：{extract_attribute(exif, ExifId.DATETIME.value)}')
    return dt


# 获取焦距与等效焦距
def get_focal_length(exif):
    focal_length = DEFAULT_VALUE
    focal_length_in_35mm_film = DEFAULT_VALUE

    try:
        focal_lengths = PATTERN.findall(extract_attribute(exif, ExifId.FOCAL_LENGTH.value))
        try:
            focal_length = focal_lengths[0] if focal_length else DEFAULT_VALUE
        except IndexError as e:
            logger.info(
                f'ValueError: 不存在焦距：{focal_lengths} : {e}')
        try:
            focal_length_in_35mm_film: str = focal_lengths[1] if focal_length else DEFAULT_VALUE
        except IndexError as e:
            logger.info(f'ValueError: 不存在 35mm 焦距：{focal_lengths} : {e}')
    except Exception as e:
        logger.info(f'KeyError: 焦距转换错误：{extract_attribute(exif, ExifId.FOCAL_LENGTH.value)} : {e}')

    return focal_length, focal_length_in_35mm_film


# 定义图片的类
class ImageContainer(object):
    """
    图像容器类，用于存储和处理图像相关信息。

    该类封装了图像路径、图像对象、EXIF 信息以及一些图像的元数据（如相机型号、镜头信息、拍摄时间等）。

    Attributes:
        path (Path): 图像文件路径。
        name (str): 图像文件名。
        target_path (Path | None): 目标路径，初始为 None。
        img (Image.Image): Pillow 图像对象。
        exif (dict): 图像的 EXIF 信息字典。
        original_width (int): 图像原始宽度。
        original_height (int): 图像原始高度。
        _param_dict (dict): 参数字典。
        model (str): 相机型号。
        make (str): 相机品牌。
        lens_model (str): 镜头型号。
        lens_make (str): 镜头品牌。
        date (datetime): 拍摄时间。
        focal_length (int | None): 焦距。
        focal_length_in_35mm_film (int | None): 35mm 胶片等效焦距。
        f_number (str): 光圈值。
        exposure_time (str): 曝光时间。
        iso (str): ISO 感光度。
    """

    def __init__(self, path: Path):
        self.path: Path = path
        self.name: str = path.name
        self.target_path: Path | None = None
        self.img: Image.Image = Image.open(path)
        self.exif: dict = get_exif(path)  # 图片信息字典
        self.original_width = self.img.width
        self.original_height = self.img.height
        self._param_dict = dict()
        self.model: str = extract_attribute(self.exif, ExifId.CAMERA_MODEL.value)
        self.make: str = extract_attribute(self.exif, ExifId.CAMERA_MAKE.value)
        self.lens_model: str = extract_attribute(self.exif, *ExifId.LENS_MODEL.value)
        self.lens_make: str = extract_attribute(self.exif, ExifId.LENS_MAKE.value)
        self.date: datetime = get_datetime(self.exif)
        self.focal_length, self.focal_length_in_35mm_film = get_focal_length(self.exif)
        self.f_number: str = extract_attribute(self.exif, ExifId.F_NUMBER.value, default_value=DEFAULT_VALUE)
        self.exposure_time: str = extract_attribute(self.exif, ExifId.EXPOSURE_TIME.value, default_value=DEFAULT_VALUE,suffix='s')
        self.iso: str = extract_attribute(self.exif, ExifId.ISO.value, default_value=DEFAULT_VALUE)

        # 是否使用等效焦距
        self.use_equivalent_focal_length: bool = True
        self.orientation = self.exif[ExifId.ORIENTATION.value] if ExifId.ORIENTATION.value in self.exif else 1
        # print(self.orientation)
        if self.orientation == "Rotate 0":
            pass
        elif self.orientation == "Rotate 90 CW":
            self.img = self.img.transpose(Transpose.ROTATE_270)
        elif self.orientation == "Rotate 180":
            self.img = self.img.transpose(Transpose.ROTATE_180)
        elif self.orientation == "Rotate 270 CW":
            self.img = self.img.transpose(Transpose.ROTATE_90)
        else:
            pass

        # 水印设置
        self.custom = '无'
        self.logo = None
        # 水印图片
        self.watermark_img = None
        self._param_dict[MODEL_VALUE] = self.model
        self._param_dict[PARAM_VALUE] = self.get_param_str()
        self._param_dict[MAKE_VALUE] = self.make
        self._param_dict[DATETIME_VALUE] = self._parse_datetime()
        self._param_dict[DATE_VALUE] = self._parse_date()
        self._param_dict[LENS_VALUE] = self.lens_model
        filename_without_ext = os.path.splitext(self.path.name)[0] #文件名(无后缀)
        self._param_dict[FILENAME_VALUE] = filename_without_ext
        self._param_dict[TOTAL_PIXEL_VALUE] = calculate_pixel_count(self.original_width, self.original_height)

        # GPS 信息
        if 'GPSPosition' in self.exif:
            self._param_dict[GEO_INFO_VALUE] = str.join(' ', extract_gps_info(self.exif.get('GPSPosition')))
        elif 'GPSLatitude' in self.exif and 'GPSLongitude' in self.exif:
            self._param_dict[GEO_INFO_VALUE] = str.join(' ', extract_gps_lat_and_long((self.exif.get('GPSLatitude'),
                                                                                       self.exif.get('GPSLongitude'))))
        else:
            self._param_dict[GEO_INFO_VALUE] = '无'

        self._param_dict[CAMERA_MAKE_CAMERA_MODEL_VALUE] = ' '.join(
            [self._param_dict[MAKE_VALUE], self._param_dict[MODEL_VALUE]])
        self._param_dict[LENS_MAKE_LENS_MODEL_VALUE] = ' '.join(
            [self.lens_make, self._param_dict[LENS_VALUE]])
        self._param_dict[CAMERA_MODEL_LENS_MODEL_VALUE] = ' '.join(
            [self._param_dict[MODEL_VALUE], self._param_dict[LENS_VALUE]])
        self._param_dict[DATE_FILENAME_VALUE] = ' '.join(
            [self._param_dict[DATE_VALUE], self._param_dict[FILENAME_VALUE]])
        self._param_dict[DATETIME_FILENAME_VALUE] = ' '.join(
            [self._param_dict[DATETIME_VALUE], self._param_dict[FILENAME_VALUE]])

    def print_info(self):
        """打印ImageContainer的信息"""
        print(f"图像路径: {self.path}")
        print(f"是否使用等效焦距: {self.use_equivalent_focal_length}")
        print(f"模型: {self.model}")
        print(f"制造商: {self.make}")
        print(f"镜头型号: {self.lens_model}")
        print(f"镜头制造商: {self.lens_make}")
        print(f"日期: {self.date}")
        print(f"焦距: {self.focal_length}")
        print(f"等效35mm焦距: {self.focal_length_in_35mm_film}")
        print(f"F数: {self.f_number}")
        print(f"曝光时间: {self.exposure_time}")
        print(f"ISO值: {self.iso}")
        print(f"原始宽度: {self.original_width}")
        print(f"原始高度: {self.original_height}")
        print(f"方向: {self.orientation}")
        print(f"自定义水印: {self.custom}")
        print(f"水印图片: {self.watermark_img}")

    def write_to_json(self, json_path: Path):
        """将ImageContainer的信息写入JSON文件"""
        data = {
            "path": str(self.path),
            "use_equivalent_focal_length": self.use_equivalent_focal_length,
            "model": self.model,
            "make": self.make,
            "lens_model": self.lens_model,
            "lens_make": self.lens_make,
            "date": self.date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(self.date, datetime) else str(self.date),
            "focal_length": self.focal_length,
            "focal_length_in_35mm_film": self.focal_length_in_35mm_film,
            "f_number": self.f_number,
            "exposure_time": self.exposure_time,
            "iso": self.iso,
            "original_width": self.original_width,
            "original_height": self.original_height,
            "orientation": self.orientation,
            "custom": self.custom,
            "watermark_img": str(self.watermark_img) if self.watermark_img else None,
            **self._param_dict  # 合并_param_dict中的数据
        }

        # 移除图像对象，因为它不能被JSON序列化
        if "img" in data:
            del data["img"]

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_param_str(self) -> str:
        """
        组合拍摄参数，输出一个字符串
        :return: 拍摄参数字符串
        """
        focal_length = self.focal_length_in_35mm_film if self.use_equivalent_focal_length else self.focal_length
        return '  '.join([str(focal_length) + 'mm', 'f/' + self.f_number, self.exposure_time,
                          'ISO' + str(self.iso)])

    def get_attribute_str(self, element: ElementConfig) -> str:
        """
        通过 element 获取属性值
        :param element: element 对象有 name 和 value 两个字段，通过 name 和 value 获取属性值
        :return: 属性值字符串
        """
        if element.get_name() in self._param_dict:
            return self._param_dict[element.get_name()]
        if element is None or element.get_name() == '':
            return ''
        if element.get_name() == CUSTOM_VALUE:
            self.custom = element.get_value()
            return self.custom
        elif element.get_name() in self._param_dict:
            return self._param_dict[element.get_name()]
        else:
            return ''

    def _parse_datetime(self) -> str:
        """
        解析日期，转换为指定的格式
        :return: 指定格式的日期字符串，转换失败返回原始的时间字符串
        """
        return datetime.strftime(self.date, '%Y-%m-%d %H:%M')

    def _parse_date(self) -> str:
        """
        解析日期，转换为指定的格式
        :return: 指定格式的日期字符串，转换失败返回原始的时间字符串
        """
        return datetime.strftime(self.date, '%Y-%m-%d')

    def get_original_height(self):
        return self.original_height

    def get_original_width(self):
        return self.original_width

    def get_original_ratio(self):
        return self.original_width / self.original_height

    def get_logo(self):
        return self.logo

    def set_logo(self, logo) -> None:
        self.logo = logo

    def is_use_equivalent_focal_length(self, flag: bool) -> None:
        self.use_equivalent_focal_length = flag

    def get_watermark_img(self) -> Image.Image:
        if self.watermark_img is None:
            self.watermark_img = self.img.copy()
            # 复制原始图片的DPI信息到watermark_img
            if 'dpi' in self.img.info:
                # PIL的copy()方法应该会自动复制info字典，但为了确保安全，我们显式设置
                pass  # copy()应该已经复制了info
        return self.watermark_img

    def update_watermark_img(self, watermark_img) -> None:
        if self.watermark_img == watermark_img:
            return
        original_watermark_img = self.watermark_img
        self.watermark_img = watermark_img
        
        # 如果新图片没有DPI信息，但原始图片有，则复制DPI信息
        if self.watermark_img and 'dpi' in self.img.info and 'dpi' not in self.watermark_img.info:
            # 注意：我们不能直接修改PIL图片的info字典，但可以在保存时传递dpi参数
            # 这里我们确保watermark_img有一个info字典
            pass
        
        if original_watermark_img is not None:
            original_watermark_img.close()
    def update_img(self, img) -> None:
        if self.img == img:
            return
        original_img = self.img
        
        # 保存原始图片的DPI信息
        original_dpi = self.img.info.get('dpi') if self.img else None
        
        self.img = img
        
        # 如果新图片没有DPI信息，但原始图片有，尝试保留
        if self.img and original_dpi and 'dpi' not in self.img.info:
            # 注意：我们不能直接修改PIL图片的info字典
            # 但可以在保存时传递dpi参数，或者创建一个新的图片对象
            pass
        
        if original_img is not None:
            original_img.close()
    def close(self):
        self.img.close()
        if self.watermark_img is not None:
            self.watermark_img.close()

    def save(self, target_path, quality=100):
        if self.watermark_img is None:
            print("{} has no watermark_img".format(self.name))
            # 获取原始图片的DPI信息
            dpi = self.img.info.get('dpi')
            save_kwargs = {
                'quality': quality,
                'encoding': 'utf-8'
            }
            
            # 如果有DPI信息，添加到保存参数中
            if dpi:
                save_kwargs['dpi'] = dpi
            
            # 如果有EXIF信息，也保留
            if 'exif' in self.img.info:
                save_kwargs['exif'] = self.img.info['exif']
            
            self.img.save(target_path, **save_kwargs)
            return

        if self.orientation == "Rotate 0":
            pass
        elif self.orientation == "Rotate 90 CW":
            self.watermark_img = self.watermark_img.transpose(Transpose.ROTATE_90)
        elif self.orientation == "Rotate 180":
            self.watermark_img = self.watermark_img.transpose(Transpose.ROTATE_180)
        elif self.orientation == "Rotate 270 CW":
            self.watermark_img = self.watermark_img.transpose(Transpose.ROTATE_270)
        else:
            pass

        if self.watermark_img.mode != 'RGB':
            self.watermark_img = self.watermark_img.convert('RGB')

        # 准备保存参数
        save_kwargs = {
            'quality': quality,
            'encoding': 'utf-8'
        }
        
        # 获取DPI信息：首先检查是否有保存的DPI，然后检查原始图片
        dpi = None
        if hasattr(self, '_saved_dpi'):
            dpi = self._saved_dpi
        elif 'dpi' in self.img.info:
            dpi = self.img.info.get('dpi')
        
        if dpi:
            save_kwargs['dpi'] = dpi
        
        # 如果有EXIF信息，也保留
        if 'exif' in self.img.info:
            save_kwargs['exif'] = self.img.info['exif']
        
        self.watermark_img.save(target_path, **save_kwargs)

    def get_height(self):
        return self.get_watermark_img().height

    def get_width(self):
        return self.get_watermark_img().width

    def get_model(self):
        return self.model

    def get_make(self):
        return self.make

    def get_ratio(self):
        # print('self.original_width {} self.original_height {}'.format( self.original_width, self.original_height, self.img.width / self.img.height))
        # print( 'self.img.width {} self.img.height {}'.format(self.img.width , self.img.height,self.img.width / self.img.height) )
        return self.img.width / self.img.height

    def get_img(self):
        return self.img
