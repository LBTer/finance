from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
import enum


class AttachmentType(str, enum.Enum):
    """附件类型枚举"""
    SALES = "sales"          # 销售附件
    LOGISTICS = "logistics"  # 后勤附件


class Attachment(Base):
    """文件附件模型"""
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 外键关联销售记录
    sales_record_id: Mapped[int] = mapped_column(ForeignKey("salesrecord.id"), nullable=False)
    sales_record: Mapped["SalesRecord"] = relationship(
        "SalesRecord", 
        back_populates="attachments"
    )
    
    # 附件类型
    attachment_type: Mapped[str] = mapped_column(
        String(20),
        default=AttachmentType.SALES.value,
        nullable=False
    )
    
    # 文件信息
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)  # 原始文件名
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)   # 存储文件名（MD5.ext格式）
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)             # 文件大小（字节）
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)      # MIME类型
    file_md5: Mapped[str] = mapped_column(String(32), nullable=False)          # 文件MD5值
    
    def __repr__(self) -> str:
        return f"<Attachment at {hex(id(self))}>" 