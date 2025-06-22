# 销售记录（SalesRecord）

## 类型1：美金订单

### 基本信息字段
- **id**: 主键，自增整数
- **order_number**: 订单号（唯一标识，最大50字符）
- **order_type**: 订单类型（最大255字符，）
- **customer_source**: 客户来源（最大255字符，必填，类型在代码里定义，目前有阿里、展会、地推、自主开发）
- **user_id**: 经办人ID（关联用户表，创建记录的人）
- **user**: 经办人关系（关联User模型）

### 销售信息字段
- **product_name**: 产品名称（最大255字符，必填，类型在代码里定义，目前是锻造轮/铸造轮）
- **order_currency**: 订单币种类型（最大100字符，必填，类型在代码里定义，美金/人民币）
- **quantity**: 数量（整数，必填）
- **unit_price**: 单价（美元，精度2位小数，必填）
- **total_price**: 总价（美元，精度2位小数，必填）
- **exchange_rate**: 汇率（美元-人民币，精度4位小数，默认7.0，必填）

### 费用信息字段
- **domestic_shipping_fee**: 运费（陆内）- 人民币（精度2位小数，默认0.0）
- **overseas_shipping_fee**: 运费（海运）- 人民币（精度2位小数，默认0.0）
- **logistics_company**: 物流公司（最大100字符，可选）
- **refund_amount**: 退款金额 - 人民币（精度2位小数，默认0.0）
- **tax_refund**: 退税金额 - 人民币（精度2位小数，默认0.0）
- **profit**: 利润 - 人民币（精度2位小数，默认0.0）

### 状态和审核字段
- **status**: 状态（枚举：pending-待审核/approved-已审核/rejected-已拒绝，默认pending）
- **remarks**: 备注（最大1000字符，可选）
- **approved_at**: 审核时间（带时区的日期时间，可选）
- **approved_by_id**: 审核人ID（关联用户表，可选）
- **approved_by**: 审核人关系（关联User模型）

### 计算属性
- **total_amount**: 计算总金额（美元 + 人民币费用，根据汇率转换）

### 关联关系
- **attachments**: 附件列表（关联Attachment模型，级联删除）

### 继承字段（来自Base类）
- **created_at**: 创建时间
- **updated_at**: 更新时间