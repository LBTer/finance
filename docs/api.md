# 销售提成管理系统 API 文档

## 基础信息

- 基础URL: `http://localhost:8000`
- API版本: v1
- 认证方式: JWT Bearer Token

## 认证相关接口

### 登录

```
POST /api/v1/auth/login
```

请求体:
```json
{
    "email": "string",
    "password": "string"
}
```

响应:
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

### 注册（仅管理员）

```
POST /api/v1/auth/register
```

请求头:
```
Authorization: Bearer <token>
```

请求体:
```json
{
    "email": "string",
    "password": "string",
    "full_name": "string",
    "role": "string"  // "user", "manager", "admin"
}
```

响应:
```json
{
    "id": "integer",
    "email": "string",
    "full_name": "string",
    "role": "string",
    "is_active": "boolean",
    "created_at": "datetime"
}
```

### 密码重置请求

```
POST /api/v1/auth/password-reset-request
```

请求体:
```json
{
    "email": "string"
}
```

响应:
```json
{
    "message": "如果邮箱存在，重置链接已发送"
}
```

### 密码重置

```
POST /api/v1/auth/password-reset
```

请求体:
```json
{
    "token": "string",
    "new_password": "string"
}
```

响应:
```json
{
    "message": "密码重置成功"
}
```

## 销售记录接口

### 创建销售记录

```
POST /api/v1/sales
```

请求头:
```
Authorization: Bearer <token>
```

请求体:
```json
{
    "order_number": "string",
    "product_name": "string",
    "quantity": "integer",
    "unit_price": "number",
    "shipping_fee": "number",
    "refund_amount": "number",
    "tax_refund": "number",
    "remarks": "string"
}
```

响应:
```json
{
    "id": "integer",
    "order_number": "string",
    "user_id": "integer",
    "product_name": "string",
    "quantity": "integer",
    "unit_price": "number",
    "shipping_fee": "number",
    "refund_amount": "number",
    "tax_refund": "number",
    "status": "string",
    "remarks": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### 获取销售记录列表

```
GET /api/v1/sales
```

请求头:
```
Authorization: Bearer <token>
```

查询参数:
```
page: integer (默认: 1)
size: integer (默认: 10)
start_date: string (可选, 格式: YYYY-MM-DD)
end_date: string (可选, 格式: YYYY-MM-DD)
status: string (可选, "pending"/"approved"/"rejected")
```

响应:
```json
{
    "items": [
        {
            "id": "integer",
            "order_number": "string",
            "user_id": "integer",
            "product_name": "string",
            "quantity": "integer",
            "unit_price": "number",
            "shipping_fee": "number",
            "refund_amount": "number",
            "tax_refund": "number",
            "status": "string",
            "remarks": "string",
            "created_at": "datetime",
            "updated_at": "datetime"
        }
    ],
    "total": "integer",
    "page": "integer",
    "size": "integer",
    "pages": "integer"
}
```

### 获取单个销售记录

```
GET /api/v1/sales/{record_id}
```

请求头:
```
Authorization: Bearer <token>
```

响应:
```json
{
    "id": "integer",
    "order_number": "string",
    "user_id": "integer",
    "product_name": "string",
    "quantity": "integer",
    "unit_price": "number",
    "shipping_fee": "number",
    "refund_amount": "number",
    "tax_refund": "number",
    "status": "string",
    "remarks": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### 更新销售记录

```
PUT /api/v1/sales/{record_id}
```

请求头:
```
Authorization: Bearer <token>
```

请求体:
```json
{
    "product_name": "string",
    "quantity": "integer",
    "unit_price": "number",
    "shipping_fee": "number",
    "refund_amount": "number",
    "tax_refund": "number",
    "remarks": "string"
}
```

响应:
```json
{
    "id": "integer",
    "order_number": "string",
    "user_id": "integer",
    "product_name": "string",
    "quantity": "integer",
    "unit_price": "number",
    "shipping_fee": "number",
    "refund_amount": "number",
    "tax_refund": "number",
    "status": "string",
    "remarks": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### 删除销售记录

```
DELETE /api/v1/sales/{record_id}
```

请求头:
```
Authorization: Bearer <token>
```

响应:
```
状态码: 204 No Content
```

### 审核销售记录（仅管理员和经理）

```
PUT /api/v1/sales/{record_id}/review
```

请求头:
```
Authorization: Bearer <token>
```

请求体:
```json
{
    "status": "string",  // "approved" 或 "rejected"
    "remarks": "string"  // 可选，审核意见
}
```

响应:
```json
{
    "id": "integer",
    "status": "string",
    "remarks": "string",
    "updated_at": "datetime"
}
```

## 数据导出接口

### 导出销售记录

```
GET /api/v1/sales/export
```

请求头:
```
Authorization: Bearer <token>
```

查询参数:
```
start_date: string (可选, 格式: YYYY-MM-DD)
end_date: string (可选, 格式: YYYY-MM-DD)
status: string (可选, "pending"/"approved"/"rejected")
format: string (可选, "xlsx"/"csv", 默认: "xlsx")
```

响应:
```
文件下载（Excel或CSV格式）
```

## 错误响应

所有接口的错误响应格式如下：

```json
{
    "detail": "错误信息描述"
}
```

常见错误状态码：
- 400: 请求参数错误
- 401: 未认证或认证失败
- 403: 权限不足
- 404: 资源不存在
- 422: 请求体验证失败
- 500: 服务器内部错误

## 权限说明

系统包含三种角色：
1. 普通用户（user）
   - 只能查看和管理自己的销售记录
   - 不能审核记录
   - 不能注册新用户

2. 经理（manager）
   - 可以查看所有销售记录
   - 可以审核销售记录
   - 不能注册新用户

3. 管理员（admin）
   - 拥有所有权限
   - 可以注册新用户
   - 可以查看和管理所有记录
   - 可以审核销售记录 