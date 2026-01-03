import subprocess
import os
from pathlib import Path
from typing import List, Optional, Dict, Union
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PlaybackMode(Enum):
    """图片播放模式"""
    FIXED_DURATION = "fixed_duration"  # 固定每张图片播放时长
    FIT_TO_MUSIC = "fit_to_music"      # 根据音乐时长自动调整


@dataclass
class VideoSettings:
    """视频设置"""
    output_path: str = "output/video.mp4"
    fps: int = 24
    codec: str = "libx264"
    bitrate: str = "10M"
    resolution: str = "1920x1080"
    playback_mode: PlaybackMode = PlaybackMode.FIXED_DURATION
    image_duration: float = 5.0  # 每张图片播放时长（秒）
    transition_duration: float = 1.0  # 过渡效果时长（秒）
    loop_images: bool = False  # 是否循环播放图片
    include_audio: bool = True  # 是否包含音频
    audio_path: Optional[str] = None  # 音频文件路径
    audio_volume: float = 1.0  # 音频音量（0.0-1.0）
    fade_in_duration: float = 1.0  # 淡入时长（秒）
    fade_out_duration: float = 1.0  # 淡出时长（秒）
    image_path: Optional[str] = None  # 图片文件夹路径，留空则使用默认output文件夹


class VideoCreator:
    """视频创建器"""

    def __init__(self, settings: VideoSettings):
        self.settings = settings

    def create_video_from_images(self, image_paths: List[Union[str, Path]]) -> bool:
        """
        从图片列表创建视频

        Args:
            image_paths: 图片路径列表

        Returns:
            bool: 是否成功
        """
        if not image_paths:
            logger.error("没有图片可处理")
            return False

        # 确保输出目录存在
        output_path = Path(self.settings.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 准备图片列表文件（用于ffmpeg concat）
        image_list_file = self._create_image_list_file(image_paths)
        if not image_list_file:
            return False

        try:
            # 构建ffmpeg命令
            cmd = self._build_ffmpeg_command(image_list_file)

            logger.info(f"开始创建视频: {self.settings.output_path}")
            logger.debug(f"FFmpeg命令: {' '.join(cmd)}")

            # 执行ffmpeg命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg执行失败: {result.stderr}")
                return False

            logger.info(f"视频创建成功: {self.settings.output_path}")
            return True

        except Exception as e:
            logger.error(f"创建视频时出错: {e}")
            return False
        finally:
            # 清理临时文件
            if image_list_file and image_list_file.exists():
                try:
                    image_list_file.unlink()
                except:
                    pass

    def _create_image_list_file(self, image_paths: List[Union[str, Path]]) -> Optional[Path]:
        """创建图片列表文件（用于ffmpeg concat）"""
        try:
            # 创建临时文件
            temp_file = Path("temp_image_list.txt")

            with open(temp_file, 'w', encoding='utf-8') as f:
                for image_path in image_paths:
                    img_path = Path(image_path)
                    if not img_path.exists():
                        logger.warning(f"图片不存在: {img_path}")
                        continue

                    # 写入图片路径和持续时间
                    duration = self._calculate_image_duration()
                    f.write(f"file '{img_path.absolute()}'\n")
                    f.write(f"duration {duration}\n")

            return temp_file if temp_file.exists() else None

        except Exception as e:
            logger.error(f"创建图片列表文件时出错: {e}")
            return None

    def _calculate_image_duration(self) -> float:
        """计算每张图片的持续时间"""
        if self.settings.playback_mode == PlaybackMode.FIXED_DURATION:
            return self.settings.image_duration
        elif self.settings.playback_mode == PlaybackMode.FIT_TO_MUSIC:
            # 需要先获取音乐时长
            music_duration = self._get_music_duration()
            if music_duration and len(self._get_image_paths_from_output()) > 0:
                image_count = len(self._get_image_paths_from_output())
                return music_duration / image_count
            else:
                # 回退到固定时长
                return self.settings.image_duration
        return self.settings.image_duration

    def _get_music_duration(self) -> Optional[float]:
        """获取音乐时长（秒）"""
        if not self.settings.audio_path or not Path(self.settings.audio_path).exists():
            return None

        try:
            # 使用ffprobe获取音频时长
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                self.settings.audio_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"获取音乐时长时出错: {e}")

        return None

    def _get_image_paths_from_output(self) -> List[Path]:
        """从指定文件夹获取图片路径"""
        # 如果设置了自定义图片路径，使用自定义路径，否则使用默认output文件夹
        if self.settings.image_path:
            image_dir = Path(self.settings.image_path)
        else:
            image_dir = Path("output")
        
        if not image_dir.exists():
            logger.warning(f"图片文件夹不存在: {image_dir}")
            return []
        
        # 支持的图片格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_paths = []
        
        for ext in image_extensions:
            image_paths.extend(image_dir.glob(f"*{ext}"))
            image_paths.extend(image_dir.glob(f"*{ext.upper()}"))
        
        # 按文件名排序
        image_paths.sort(key=lambda x: x.name)
        
        if not image_paths:
            logger.warning(f"在文件夹 {image_dir} 中没有找到图片")
        
        return image_paths

    def _build_ffmpeg_command(self, image_list_file: Path) -> List[str]:
        """构建ffmpeg命令"""
        cmd = ['ffmpeg', '-y']  # -y 覆盖输出文件
        
        # 输入图片列表
        cmd.extend(['-f', 'concat', '-safe', '0', '-i', str(image_list_file)])
        
        # 解析分辨率
        resolution = self.settings.resolution
        width, height = resolution.split('x')
        
        # 视频编码参数
        cmd.extend([
            '-c:v', self.settings.codec,
            '-b:v', self.settings.bitrate,
            '-r', str(self.settings.fps),
            '-pix_fmt', 'yuv420p',
            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2'
        ])
        
        # 音频处理
        if self.settings.include_audio and self.settings.audio_path:
            # 添加音频输入
            cmd.extend(['-i', self.settings.audio_path])
            
            # 音频编码参数
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '192k',
                '-filter_complex',
                f'[1:a]volume={self.settings.audio_volume}[audio];'
                f'[audio]afade=t=in:st=0:d={self.settings.fade_in_duration},'
                f'afade=t=out:st={self._calculate_video_duration() - self.settings.fade_out_duration}:d={self.settings.fade_out_duration}[final_audio]',
                '-map', '0:v',
                '-map', '[final_audio]'
            ])
        else:
            # 无音频
            cmd.extend(['-an'])
        
        # 输出文件
        cmd.append(self.settings.output_path)
        
        return cmd

    def _calculate_video_duration(self) -> float:
        """计算视频总时长"""
        image_paths = self._get_image_paths_from_output()
        if not image_paths:
            return 0.0

        image_duration = self._calculate_image_duration()
        return len(image_paths) * image_duration

    def create_video_from_output_folder(self) -> bool:
        """从output文件夹创建视频"""
        image_paths = self._get_image_paths_from_output()
        if not image_paths:
            logger.error("output文件夹中没有找到图片")
            return False

        # 如果使用音乐适配模式，需要检查音乐文件
        if self.settings.playback_mode == PlaybackMode.FIT_TO_MUSIC:
            if not self.settings.audio_path or not Path(self.settings.audio_path).exists():
                logger.warning("音乐适配模式需要有效的音乐文件，将使用固定时长模式")
                self.settings.playback_mode = PlaybackMode.FIXED_DURATION

        return self.create_video_from_images(image_paths)


def get_available_music_files() -> List[Path]:
    """获取可用的音乐文件"""
    music_dir = Path("resources/music")
    if not music_dir.exists():
        return []

    # 支持的音频格式
    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}
    music_files = []

    for ext in audio_extensions:
        music_files.extend(music_dir.glob(f"*{ext}"))
        music_files.extend(music_dir.glob(f"*{ext.upper()}"))

    # 按文件名排序
    music_files.sort(key=lambda x: x.name)
    return music_files


def create_video_with_default_settings() -> bool:
    """使用默认设置创建视频"""
    settings = VideoSettings(
        output_path="output/video.mp4",
        fps=24,
        codec="libx264",
        bitrate="10M",
        resolution="1920x1080",
        playback_mode=PlaybackMode.FIXED_DURATION,
        image_duration=5.0,
        transition_duration=1.0,
        loop_images=False,
        include_audio=True,
        audio_path=None,
        audio_volume=1.0,
        fade_in_duration=1.0,
        fade_out_duration=1.0
    )

    # 尝试使用第一个可用的音乐文件
    music_files = get_available_music_files()
    if music_files:
        settings.audio_path = str(music_files[0])

    creator = VideoCreator(settings)
    return creator.create_video_from_output_folder()


if __name__ == "__main__":
    # 测试代码
    import sys

    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 创建测试视频
    success = create_video_with_default_settings()
    if success:
        print("视频创建成功！")
        sys.exit(0)
    else:
        print("视频创建失败！")
        sys.exit(1)
