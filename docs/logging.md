# 日志系统使用说明

## 概述

本项目集成了完整的日志系统，支持控制台输出和文件记录，提供了多种日志级别和功能丰富的配置选项。

## 功能特性

- ✅ 支持控制台和文件双输出
- ✅ 自动日志文件轮转（避免文件过大）
- ✅ 分离的错误日志和访问日志
- ✅ 可配置的日志级别
- ✅ 详细的日志格式（包含文件路径、行号、函数名）
- ✅ 函数调用装饰器
- ✅ 异步函数支持
- ✅ 环境变量配置

## 配置说明

### 环境变量

在 `.env` 文件中可以配置以下变量：

```bash
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 日志文件目录
LOG_DIR=logs
```

### 日志文件结构

```
logs/
├── finance_system.log         # 主应用日志
├── finance_system_error.log   # 错误日志
├── finance_system_access.log  # 访问日志
└── finance_system.log.1       # 轮转的备份文件
```

## 基本使用

### 1. 获取Logger实例

```python
from app.utils.logger import get_logger

# 自动使用当前模块名作为logger名称
logger = get_logger()

# 或者指定logger名称
logger = get_logger("my_module")
```

### 2. 记录日志

```python
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 记录异常信息（包含堆栈跟踪）
try:
    1 / 0
except Exception as e:
    logger.error(f"计算错误: {str(e)}", exc_info=True)
```

### 3. 使用装饰器

```python
from app.utils.logger import log_function_call, log_async_function_call

# 普通函数装饰器
@log_function_call
def my_function(param1, param2):
    return param1 + param2

# 异步函数装饰器
@log_async_function_call
async def my_async_function(data):
    return await process_data(data)
```

### 4. 在类中使用

```python
from app.utils.logger import get_logger

class MyService:
    def __init__(self):
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("服务初始化")
    
    def process(self, data):
        self.logger.info(f"处理数据: {data}")
        # 处理逻辑...
```

## 高级配置

### 手动初始化日志系统

```python
from app.utils.logger import init_logger

# 自定义配置
init_logger(
    log_level="DEBUG",
    log_dir="custom_logs",
    app_name="my_app",
    enable_console=True,
    enable_file=True,
    max_bytes=20 * 1024 * 1024,  # 20MB
    backup_count=10
)
```

### 配置参数说明

- `log_level`: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_dir`: 日志文件目录
- `app_name`: 应用名称，用于日志文件名
- `enable_console`: 是否启用控制台输出
- `enable_file`: 是否启用文件输出
- `max_bytes`: 单个日志文件最大字节数
- `backup_count`: 备份文件数量

## 日志格式

### 控制台输出格式
```
2025-06-03 01:07:45 - INFO - 应用初始化完成
```

### 文件输出格式
```
2025-06-03 01:07:45 - app.main - INFO - /path/to/file.py:66 - startup_event - 应用初始化完成
```

## 最佳实践

### 1. 日志级别使用建议

- **DEBUG**: 详细的调试信息，仅在开发时使用
- **INFO**: 一般信息，程序正常运行的关键节点
- **WARNING**: 警告信息，可能的问题但不影响运行
- **ERROR**: 错误信息，需要注意但程序可以继续
- **CRITICAL**: 严重错误，程序可能无法继续运行

### 2. 日志内容建议

```python
# ✅ 好的日志记录
logger.info(f"用户登录成功: user_id={user_id}, ip={client_ip}")
logger.error(f"数据库连接失败: {str(e)}", exc_info=True)

# ❌ 避免的日志记录
logger.info("something happened")  # 信息不够具体
logger.error(str(e))  # 缺少上下文信息
```

### 3. 性能考虑

```python
# ✅ 使用懒求值
logger.debug("复杂计算结果: %s", expensive_calculation())

# ❌ 避免在不需要时进行计算
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"复杂计算结果: {expensive_calculation()}")
```

### 4. 敏感信息处理

```python
# ✅ 脱敏处理
logger.info(f"用户注册: email={email[:3]}***@{email.split('@')[1]}")

# ❌ 避免记录敏感信息
logger.info(f"用户密码: {password}")  # 绝对不要这样做
```

## 故障排查

### 常见问题

1. **日志文件没有创建**
   - 检查日志目录权限
   - 确认 `enable_file=True`
   - 查看控制台是否有错误信息

2. **日志级别设置无效**
   - 确认环境变量 `LOG_LEVEL` 设置正确
   - 检查是否在正确的地方调用了 `init_logger()`

3. **日志文件过大**
   - 调整 `max_bytes` 参数
   - 增加 `backup_count` 值
   - 考虑调高日志级别以减少日志量

### 日志查看命令

```bash
# 查看最新日志
tail -f logs/finance_system.log

# 查看错误日志
tail -f logs/finance_system_error.log

# 搜索特定内容
grep "ERROR" logs/finance_system.log

# 按时间范围查看
grep "2025-06-03 01:" logs/finance_system.log
```

## 示例代码

详细的使用示例请参考 `app/utils/logger_example.py` 文件。 