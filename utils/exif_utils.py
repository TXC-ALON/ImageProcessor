import logging
import platform
import re
import shutil
import subprocess
from pathlib import Path



if platform.system() == 'Windows':
    EXIFTOOL_PATH = Path('./utils/exiftool/exiftool.exe')
    ENCODING = 'gbk'
elif shutil.which('exiftool') is not None:
    EXIFTOOL_PATH = shutil.which('exiftool')
    ENCODING = 'utf-8'
else:
    EXIFTOOL_PATH = Path('./exiftool/exiftool')
    ENCODING = 'utf-8'

logger = logging.getLogger(__name__)


def get_file_list(path):
    """
    获取 jpg 文件列表
    :param path: 路径
    :return: 文件名
    """
    path = Path(path, encoding=ENCODING)
    return [file_path for file_path in path.iterdir()
            if file_path.is_file() and file_path.suffix in ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.PNG']]


def get_exif(path) -> dict:
    """
    获取exif信息
    :param path: 照片路径
    :return: exif信息
    """
    exif_dict = {}
    try:
        output_bytes = subprocess.check_output([EXIFTOOL_PATH, '-d', '%Y-%m-%d %H:%M:%S%3f%z', path])
        output = output_bytes.decode('utf-8', errors='ignore')

        lines = output.splitlines()
        utf8_lines = [line for line in lines]

        for line in utf8_lines:
            # 将每一行按冒号分隔成键值对
            kv_pair = line.split(':')
            if len(kv_pair) < 2:
                continue
            key = kv_pair[0].strip()
            value = ':'.join(kv_pair[1:]).strip()
            # 将键中的空格移除
            key = re.sub(r'\s+', '', key)
            key = re.sub(r'/', '', key)
            # 将键值对添加到字典中
            exif_dict[key] = value
        for key, value in exif_dict.items():
            # 过滤非 ASCII 字符
            value_clean = ''.join(c for c in value if ord(c) < 128)
            # 将处理后的值更新到 exif_dict 中
            exif_dict[key] = value_clean
    except Exception as e:
        logger.error(f'get_exif error: {path} : {e}')

    return exif_dict


def insert_exif(source_path, target_path) -> None:
    """
    复制照片的 exif 信息
    :param source_path: 源照片路径
    :param target_path: 目的照片路径
    """
    try:
        # 将 exif 信息转换为字节串
        subprocess.check_output([EXIFTOOL_PATH, '-tagsfromfile', source_path, '-overwrite_original', target_path])
    except ValueError as e:
        logger.exception(f'ValueError: {source_path}: cannot insert exif {str(e)}')


def calculate_pixel_count(width: int, height: int) -> str:
    # 计算像素总数
    pixel_count = width * height
    # 计算百万像素数
    megapixel_count = pixel_count / 1000000.0
    # 返回结果字符串
    return f"{megapixel_count:.2f} MP"


def extract_attribute(data_dict: dict, *keys, default_value: str = '', prefix='', suffix='') -> str:
    """
    从字典中提取对应键的属性值

    :param data_dict: 包含属性值的字典
    :param keys: 一个或多个键
    :param default_value: 默认值，默认为空字符串
    :return: 对应的属性值或空字符串
    """
    for key in keys:
        if key in data_dict:
            return data_dict[key] + suffix
    return default_value


def extract_gps_lat_and_long(lat: str, long: str):
    # 提取出纬度和经度主要部分
    lat_deg, _, lat_min = re.findall(r"(\d+ deg \d+)", lat)[0].split()
    long_deg, _, long_min = re.findall(r"(\d+ deg \d+)", long)[0].split()

    # 提取出方向（北 / 南 / 东 / 西）
    lat_dir = re.findall(r"([NS])", lat)[0]
    long_dir = re.findall(r"([EW])", long)[0]

    latitude = f"{lat_deg}°{lat_min}'{lat_dir}"
    longitude = f"{long_deg}°{long_min}'{long_dir}"

    return latitude, longitude


def extract_gps_info(gps_info: str):
    lat, long = gps_info.split(", ")
    return extract_gps_lat_and_long(lat, long)
