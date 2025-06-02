目标：根据app/api/v1目录下的文件中的接口，生成前端html页面。在static目录下生成。
API基础路径：/api/v1
页面风格：现代化设计，线条柔和，主色调蓝色，圆角组件，响应式布局支持移动设备
技术栈：纯HTML/CSS/JS，使用Bootstrap 5框架

用户角色层级：
- ADMIN(超级管理员) > SENIOR(高级用户) > NORMAL(普通用户)

具体需求：
1. 登录模块：
   - 输入手机号和密码
   - 错误提示友好
   - 使用JWT认证，token存储在localStorage
   - API: POST /api/v1/auth/login

2. 用户管理模块：
   - 超级管理员可注册新用户(手机号/邮箱/姓名/密码/角色)和重置密码
   - 超级管理员和高级用户可查看所有比自己低级的用户列表
   - 普通用户无此模块
   - API: POST /api/v1/auth/register, POST /api/v1/auth/reset-password

3. 销售记录模块：
   - 所有用户可提交销售记录，包含以下字段：
     * 订单编号(order_number)
     * 产品名称(product_name)
     * 数量(quantity)
     * 单价(unit_price)
     * 运费(shipping_fee)
     * 退款金额(refund_amount)
     * 税务退款(tax_refund)
     * 备注(remarks)
   - 列表页支持按状态筛选(待审核/已审核/已拒绝)和搜索(订单号/产品名)
   - 分页显示，每页10条记录
   - 超级管理员和高级用户可查看所有订单，普通用户只能查看自己的订单
   - 超级管理员和高级用户可审核订单(批准/拒绝)
   - 普通用户只能修改/删除自己的待审核订单
   - 审核完成的订单不可再修改
   - API: 
     * 创建: POST /api/v1/sales
     * 获取列表: GET /api/v1/sales
     * 获取详情: GET /api/v1/sales/{id}
     * 更新: PUT /api/v1/sales/{id}
     * 删除: DELETE /api/v1/sales/{id}

4. 交互设计:
   - 所有操作需有成功/失败提示
   - 删除和审核操作需二次确认
   - 表单提交前进行客户端验证
   - 加载数据时显示加载指示器

5. 页面结构:
   - 顶部导航栏(显示当前用户信息和退出按钮)
   - 左侧菜单(根据用户角色动态显示)
   - 主内容区
   - 底部版权信息

6. 静态资源组织:
   - static/css/: 样式文件
   - static/js/: 脚本文件
   - static/img/: 图片资源
   - static/pages/: HTML页面