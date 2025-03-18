from typing import List, Any
import pandas as pd
from fastapi import HTTPException
from datetime import datetime
from pathlib import Path

from app.models.sales_record import SalesRecord


class ExcelExporter:
    """Excel导出工具类"""
    
    @staticmethod
    async def export_sales_records(records: List[SalesRecord], output_dir: str = "exports") -> str:
        """
        导出销售记录到Excel文件
        
        Args:
            records: 销售记录列表
            output_dir: 输出目录
            
        Returns:
            str: 生成的Excel文件路径
        """
        try:
            # 确保输出目录存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 准备数据
            data = []
            for record in records:
                data.append({
                    "订单编号": record.order_number,
                    "产品名称": record.product_name,
                    "数量": record.quantity,
                    "单价": record.unit_price,
                    "运费": record.shipping_fee,
                    "退款金额": record.refund_amount,
                    "退税金额": record.tax_refund,
                    "状态": record.status,
                    "创建时间": record.created_at,
                    "更新时间": record.updated_at,
                    "备注": record.remarks
                })
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sales_records_{timestamp}.xlsx"
            filepath = str(Path(output_dir) / filename)
            
            # 导出到Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            return filepath
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"导出Excel文件时发生错误: {str(e)}"
            )