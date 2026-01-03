#!/usr/bin/env python3
"""视频设置对话框"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QCheckBox,
                             QPushButton, QGroupBox, QSpinBox, QDoubleSpinBox,
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt

from core.video_creator import VideoSettings, PlaybackMode, get_available_music_files


class VideoSettingsDialog(QDialog):
    """视频设置对话框"""
    
    def __init__(self, parent=None, initial_settings=None):
        super().__init__(parent)
        self.setWindowTitle("视频设置")
        self.resize(500, 600)
        
        # 初始化设置
        if initial_settings is None:
            self.settings = VideoSettings()
        else:
            self.settings = initial_settings
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout()
        
        # 图片路径设置组
        image_path_group = QGroupBox("图片路径设置")
        image_path_layout = QFormLayout()
        
        # 图片路径选择
        self.le_image_path = QLineEdit()
        self.le_image_path.setPlaceholderText("留空则使用默认output文件夹")
        self.btn_browse_image_path = QPushButton("浏览")
        
        image_path_row_layout = QHBoxLayout()
        image_path_row_layout.addWidget(self.le_image_path)
        image_path_row_layout.addWidget(self.btn_browse_image_path)
        
        image_path_layout.addRow("图片路径:", image_path_row_layout)
        
        image_path_group.setLayout(image_path_layout)
        layout.addWidget(image_path_group)
        
        # 播放模式组
        playback_group = QGroupBox("播放模式")
        playback_layout = QFormLayout()
        
        self.cb_playback_mode = QComboBox()
        self.cb_playback_mode.addItems(["固定时长", "适配音乐时长"])
        playback_layout.addRow("播放模式:", self.cb_playback_mode)
        
        self.sb_image_duration = QDoubleSpinBox()
        self.sb_image_duration.setRange(0.1, 60.0)
        self.sb_image_duration.setSingleStep(0.5)
        self.sb_image_duration.setSuffix(" s")
        self.sb_image_duration.setDecimals(1)
        playback_layout.addRow("单图时长:", self.sb_image_duration)
        
        self.sb_transition_duration = QDoubleSpinBox()
        self.sb_transition_duration.setRange(0.0, 5.0)
        self.sb_transition_duration.setSingleStep(0.1)
        self.sb_transition_duration.setSuffix(" s")
        self.sb_transition_duration.setDecimals(1)
        playback_layout.addRow("过渡时长:", self.sb_transition_duration)
        
        self.cb_loop_images = QCheckBox("循环播放图片")
        playback_layout.addRow(self.cb_loop_images)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        # 视频编码组
        video_group = QGroupBox("视频编码设置")
        video_layout = QFormLayout()
        
        self.cb_codec = QComboBox()
        self.cb_codec.addItems(["libx264", "libx265", "libvpx-vp9", "libaom-av1"])
        video_layout.addRow("编码格式:", self.cb_codec)
        
        self.cb_resolution = QComboBox()
        self.cb_resolution.addItems(["1920x1080", "1280x720", "3840x2160", "2560x1440"])
        video_layout.addRow("分辨率:", self.cb_resolution)
        
        self.sb_fps = QSpinBox()
        self.sb_fps.setRange(1, 60)
        self.sb_fps.setSuffix(" fps")
        video_layout.addRow("帧率:", self.sb_fps)
        
        self.le_bitrate = QLineEdit()
        self.le_bitrate.setPlaceholderText("例如: 10M, 5M, 2M")
        video_layout.addRow("码率:", self.le_bitrate)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # 音频设置组
        audio_group = QGroupBox("音频设置")
        audio_layout = QFormLayout()
        
        self.cb_include_audio = QCheckBox("包含音频")
        self.cb_include_audio.setChecked(True)
        audio_layout.addRow(self.cb_include_audio)
        
        self.cb_music = QComboBox()
        self.cb_music.addItem("无音乐", None)
        
        # 获取可用的音乐文件
        music_files = get_available_music_files()
        for music_file in music_files:
            self.cb_music.addItem(music_file.name, str(music_file))
        
        audio_layout.addRow("音乐选择:", self.cb_music)
        
        self.sb_audio_volume = QDoubleSpinBox()
        self.sb_audio_volume.setRange(0.0, 2.0)
        self.sb_audio_volume.setSingleStep(0.1)
        self.sb_audio_volume.setDecimals(1)
        self.sb_audio_volume.setSuffix("")
        audio_layout.addRow("音频音量:", self.sb_audio_volume)
        
        self.sb_fade_in = QDoubleSpinBox()
        self.sb_fade_in.setRange(0.0, 5.0)
        self.sb_fade_in.setSingleStep(0.1)
        self.sb_fade_in.setSuffix(" s")
        self.sb_fade_in.setDecimals(1)
        audio_layout.addRow("淡入时长:", self.sb_fade_in)
        
        self.sb_fade_out = QDoubleSpinBox()
        self.sb_fade_out.setRange(0.0, 5.0)
        self.sb_fade_out.setSingleStep(0.1)
        self.sb_fade_out.setSuffix(" s")
        self.sb_fade_out.setDecimals(1)
        audio_layout.addRow("淡出时长:", self.sb_fade_out)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.btn_ok = QPushButton("确定")
        self.btn_ok.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_default = QPushButton("恢复默认")
        self.btn_default.clicked.connect(self.restore_defaults)
        
        button_layout.addWidget(self.btn_default)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.cb_include_audio.toggled.connect(self.on_audio_toggled)
        self.on_audio_toggled(self.cb_include_audio.isChecked())
        
        # 连接浏览按钮
        self.btn_browse_image_path.clicked.connect(self.browse_image_path)
    
    def browse_image_path(self):
        """浏览图片文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择图片文件夹",
            self.le_image_path.text() or str(Path.cwd())
        )
        if folder:
            self.le_image_path.setText(folder)
    
    def on_audio_toggled(self, enabled):
        """音频复选框状态改变"""
        self.cb_music.setEnabled(enabled)
        self.sb_audio_volume.setEnabled(enabled)
        self.sb_fade_in.setEnabled(enabled)
        self.sb_fade_out.setEnabled(enabled)
    
    def load_settings(self):
        """加载设置到UI"""
        # 图片路径
        if self.settings.image_path:
            self.le_image_path.setText(self.settings.image_path)
        
        # 播放模式
        if self.settings.playback_mode == PlaybackMode.FIXED_DURATION:
            self.cb_playback_mode.setCurrentText("固定时长")
        else:
            self.cb_playback_mode.setCurrentText("适配音乐时长")
        
        self.sb_image_duration.setValue(self.settings.image_duration)
        self.sb_transition_duration.setValue(self.settings.transition_duration)
        self.cb_loop_images.setChecked(self.settings.loop_images)
        
        # 视频编码
        self.cb_codec.setCurrentText(self.settings.codec)
        self.cb_resolution.setCurrentText(self.settings.resolution)
        self.sb_fps.setValue(self.settings.fps)
        self.le_bitrate.setText(self.settings.bitrate)
        
        # 音频设置
        self.cb_include_audio.setChecked(self.settings.include_audio)
        self.sb_audio_volume.setValue(self.settings.audio_volume)
        self.sb_fade_in.setValue(self.settings.fade_in_duration)
        self.sb_fade_out.setValue(self.settings.fade_out_duration)
        
        # 音乐选择
        if self.settings.audio_path:
            for i in range(self.cb_music.count()):
                if self.cb_music.itemData(i) == self.settings.audio_path:
                    self.cb_music.setCurrentIndex(i)
                    break
    
    def get_settings(self):
        """从UI获取设置"""
        # 播放模式
        playback_mode_text = self.cb_playback_mode.currentText()
        playback_mode = PlaybackMode.FIT_TO_MUSIC if playback_mode_text == "适配音乐时长" else PlaybackMode.FIXED_DURATION
        
        # 获取音乐路径
        music_data = self.cb_music.currentData()
        audio_path = music_data if music_data else None
        
        # 获取图片路径（如果为空字符串，则设置为None）
        image_path = self.le_image_path.text().strip()
        if not image_path:
            image_path = None
        
        # 创建设置对象
        settings = VideoSettings(
            output_path=self.settings.output_path,  # 保留原始输出路径
            fps=self.sb_fps.value(),
            codec=self.cb_codec.currentText(),
            bitrate=self.le_bitrate.text(),
            resolution=self.cb_resolution.currentText(),
            playback_mode=playback_mode,
            image_duration=self.sb_image_duration.value(),
            transition_duration=self.sb_transition_duration.value(),
            loop_images=self.cb_loop_images.isChecked(),
            include_audio=self.cb_include_audio.isChecked(),
            audio_path=audio_path,
            audio_volume=self.sb_audio_volume.value(),
            fade_in_duration=self.sb_fade_in.value(),
            fade_out_duration=self.sb_fade_out.value(),
            image_path=image_path
        )
        
        return settings
    
    def restore_defaults(self):
        """恢复默认设置"""
        default_settings = VideoSettings()
        self.settings = default_settings
        self.load_settings()
        QMessageBox.information(self, "提示", "已恢复默认设置")


if __name__ == "__main__":
    # 测试对话框
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = VideoSettingsDialog()
    if dialog.exec_() == QDialog.Accepted:
        settings = dialog.get_settings()
        print("视频设置:")
        print(f"  播放模式: {settings.playback_mode}")
        print(f"  单图时长: {settings.image_duration}s")
        print(f"  过渡时长: {settings.transition_duration}s")
        print(f"  编码格式: {settings.codec}")
        print(f"  分辨率: {settings.resolution}")
        print(f"  帧率: {settings.fps}fps")
        print(f"  码率: {settings.bitrate}")
        print(f"  包含音频: {settings.include_audio}")
        print(f"  音乐路径: {settings.audio_path}")
        print(f"  音频音量: {settings.audio_volume}")
        print(f"  淡入时长: {settings.fade_in_duration}s")
        print(f"  淡出时长: {settings.fade_out_duration}s")
    sys.exit(0)
