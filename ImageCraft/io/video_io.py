import numpy as np
import cv2
from typing import Optional, List, Tuple
import os


class VideoProcessor:
    """视频处理器"""
    
    def __init__(self):
        self.cap: Optional[cv2.VideoCapture] = None
        self.writer: Optional[cv2.VideoWriter] = None
        self.fps: float = 0
        self.frame_count: int = 0
        self.width: int = 0
        self.height: int = 0
    
    def open(self, video_path: str) -> bool:
        """
        打开视频文件
        
        Args:
            video_path: 视频路径
        
        Returns:
            是否成功打开
        """
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            return False
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return True
    
    def get_frame(self, frame_index: int) -> Optional[np.ndarray]:
        """
        获取指定帧
        
        Args:
            frame_index: 帧索引
        
        Returns:
            帧图像，失败返回 None
        """
        if self.cap is None:
            return None
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            return None
    
    def process_frames(self, process_func, output_path: str, 
                      start_frame: int = 0, end_frame: Optional[int] = None) -> int:
        """
        处理视频帧
        
        Args:
            process_func: 处理函数
            output_path: 输出视频路径
            start_frame: 起始帧
            end_frame: 结束帧
        
        Returns:
            处理的帧数
        """
        if self.cap is None:
            raise ValueError("请先打开视频文件")
        
        if end_frame is None:
            end_frame = self.frame_count
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(output_path, fourcc, self.fps, 
                                     (self.width, self.height))
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        count = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or count + start_frame >= end_frame:
                break
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = process_func(frame_rgb)
            
            if len(processed.shape) == 2:
                processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
            
            processed_bgr = cv2.cvtColor(processed, cv2.COLOR_RGB2BGR)
            self.writer.write(processed_bgr)
            
            count += 1
        
        self.release()
        
        return count
    
    def extract_frames(self, output_dir: str, interval: int = 1) -> int:
        """
        提取视频帧为图像
        
        Args:
            output_dir: 输出目录
            interval: 提取间隔
        
        Returns:
            提取的帧数
        """
        if self.cap is None:
            raise ValueError("请先打开视频文件")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        count = 0
        frame_index = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            if frame_index % interval == 0:
                output_path = os.path.join(output_dir, f"frame_{frame_index:06d}.jpg")
                cv2.imwrite(output_path, frame)
                count += 1
            
            frame_index += 1
        
        return count
    
    def create_video_from_images(self, image_paths: List[str], output_path: str, 
                                fps: float = 30) -> None:
        """
        从图像序列创建视频
        
        Args:
            image_paths: 图像路径列表
            output_path: 输出视频路径
            fps: 帧率
        """
        if len(image_paths) == 0:
            raise ValueError("图像路径列表为空")
        
        first_frame = cv2.imread(image_paths[0])
        height, width = first_frame.shape[:2]
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for path in image_paths:
            frame = cv2.imread(path)
            writer.write(frame)
        
        writer.release()
    
    def release(self) -> None:
        """释放资源"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        if self.writer is not None:
            self.writer.release()
            self.writer = None
    
    def get_info(self) -> dict:
        """
        获取视频信息
        
        Returns:
            视频信息字典
        """
        return {
            'fps': self.fps,
            'frame_count': self.frame_count,
            'width': self.width,
            'height': self.height,
            'duration': self.frame_count / self.fps if self.fps > 0 else 0
        }
