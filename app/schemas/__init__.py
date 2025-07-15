from .user import (
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse,
)
from .sales_record import (
    SalesRecordCreate,
    SalesRecordUpdate,
    SalesRecordInDB,
    SalesRecordResponse,
)
from .attachment import (
    AttachmentCreate,
    AttachmentInDB,
    AttachmentResponse,
)
from .stats import (
    DashboardStats,
    UserStats,
    OrderTypeStats,
    StageStats,
)
from .fees import (
    ShippingFeesCreate,
    ShippingFeesUpdate,
    ShippingFeesInDB,
    ShippingFeesResponse,
)
from .procurement import (
    ProcurementCreate,
    ProcurementUpdate,
    ProcurementInDB,
    ProcurementResponse,
)

# 解决前向引用问题
from .sales_record import rebuild_models
rebuild_models()

__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    # Sales record schemas
    "SalesRecordCreate",
    "SalesRecordUpdate",
    "SalesRecordInDB",
    "SalesRecordResponse",
    # Attachment schemas
    "AttachmentCreate",
    "AttachmentInDB",
    "AttachmentResponse",
    # Stats schemas
    "DashboardStats",
    "UserStats",
    "OrderTypeStats",
    "StageStats",
    # Shipping fees schemas
    "ShippingFeesCreate",
    "ShippingFeesUpdate",
    "ShippingFeesInDB",
    "ShippingFeesResponse",
    # Procurement schemas
    "ProcurementCreate",
    "ProcurementUpdate",
    "ProcurementInDB",
    "ProcurementResponse",
] 