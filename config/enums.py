from enum import Enum

class ExifId(Enum):
    CAMERA_MODEL = 'CameraModelName'
    CAMERA_MAKE = 'Make'
    LENS_MODEL = ['LensModel', 'Lens']
    LENS_MAKE = 'LensMake'
    DATETIME = 'DateTimeOriginal'
    FOCAL_LENGTH = 'FocalLength'
    FOCAL_LENGTH_IN_35MM_FILM = 'FocalLengthIn35mmFormat'
    F_NUMBER = 'FNumber'
    ISO = 'ISO'
    EXPOSURE_TIME = 'ExposureTime'
    SHUTTER_SPEED_VALUE = 'ShutterSpeedValue'
    ORIENTATION = 'Orientation'

# 常量定义
DEFAULT_VALUE = "N/A"
MODEL_VALUE = "model"
MAKE_VALUE = "make"
LENS_VALUE = "lens"
DATETIME_VALUE = "datetime"
DATE_VALUE = "date"
FILENAME_VALUE = "filename"
GEO_INFO_VALUE = "geo_info"
TOTAL_PIXEL_VALUE = "total_pixel"
CUSTOM_VALUE = "custom"
PARAM_VALUE = "param"