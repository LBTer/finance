import hashlib
import os
import shutil
from pathlib import Path
from typing import BinaryIO, Tuple
from fastapi import UploadFile


class FileHandler:
    """文件处理工具类"""
    
    def __init__(self, upload_dir: str = "files"):
        """初始化文件处理器
        
        Args:
            upload_dir: 文件上传目录
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    def calculate_md5(self, file_obj: BinaryIO) -> str:
        """计算文件MD5值
        
        Args:
            file_obj: 文件对象
            
        Returns:
            MD5字符串
        """
        md5_hash = hashlib.md5()
        # 重置文件指针到开头
        file_obj.seek(0)
        
        # 分块读取文件计算MD5
        for chunk in iter(lambda: file_obj.read(8192), b""):
            md5_hash.update(chunk)
        
        # 重置文件指针到开头
        file_obj.seek(0)
        
        return md5_hash.hexdigest()
    
    def get_file_extension(self, filename: str) -> str:
        """获取文件扩展名
        
        Args:
            filename: 文件名
            
        Returns:
            文件扩展名（包含点号）
        """
        return Path(filename).suffix
    
    def generate_stored_filename(self, original_filename: str, file_md5: str) -> str:
        """生成存储文件名
        
        Args:
            original_filename: 原始文件名
            file_md5: 文件MD5值
            
        Returns:
            存储文件名格式：{md5}.{ext}
        """
        extension = self.get_file_extension(original_filename)
        return f"{file_md5}{extension}"
    
    async def save_upload_file(self, upload_file: UploadFile) -> Tuple[str, str, int]:
        """保存上传的文件
        
        Args:
            upload_file: FastAPI上传文件对象
            
        Returns:
            (file_md5, stored_filename, file_size)
        """
        # 计算文件MD5
        file_md5 = self.calculate_md5(upload_file.file)
        
        # 生成存储文件名
        stored_filename = self.generate_stored_filename(upload_file.filename, file_md5)
        
        # 构建完整的文件路径
        file_path = self.upload_dir / stored_filename
        
        # 如果文件已存在，直接返回（避免重复存储相同文件）
        if file_path.exists():
            file_size = file_path.stat().st_size
            return file_md5, stored_filename, file_size
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        # 获取文件大小
        file_size = file_path.stat().st_size
        
        return file_md5, stored_filename, file_size
    
    def get_file_path(self, stored_filename: str) -> Path:
        """获取文件完整路径
        
        Args:
            stored_filename: 存储文件名
            
        Returns:
            文件完整路径
        """
        return self.upload_dir / stored_filename
    
    def file_exists(self, stored_filename: str) -> bool:
        """检查文件是否存在
        
        Args:
            stored_filename: 存储文件名
            
        Returns:
            文件是否存在
        """
        return self.get_file_path(stored_filename).exists()
    
    def delete_file(self, stored_filename: str) -> bool:
        """删除文件
        
        Args:
            stored_filename: 存储文件名
            
        Returns:
            是否删除成功
        """
        file_path = self.get_file_path(stored_filename)
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False


# 全局文件处理器实例
file_handler = FileHandler() 