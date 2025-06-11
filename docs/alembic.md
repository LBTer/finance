# 数据库迁移出问题的处理方法

这个错误是因为**数据库状态与 Alembic 版本记录不一致**。

**错误原因：**

1. 之前的迁移 `249ef6cf58ad_add_exchange_rate_field.py` 执行失败了
2. 但 Alembic 的版本表可能已经部分更新，导致状态不一致
3. Alembic 检测到数据库不是最新状态，所以拒绝生成新的迁移文件

**解决方法：**

**方法1：回滚到上一个版本（推荐）**
```bash
alembic downgrade bd3a15ef8eb8
```
然后修改现有的迁移文件 `249ef6cf58ad_add_exchange_rate_field.py`，添加 `server_default`：

**方法2：检查当前版本状态**
```bash
alembic current
alembic history --verbose
```
查看实际的数据库版本状态

**方法3：强制标记为当前版本（如果确定数据库结构正确）**
```bash
alembic stamp head
```

**推荐流程：**
1. 先回滚：`alembic downgrade bd3a15ef8eb8`
2. 修改现有迁移文件，添加 `server_default='1.0'`
3. 重新执行：`alembic upgrade head`

这样比生成新的迁移文件更清晰，避免迁移历史混乱。