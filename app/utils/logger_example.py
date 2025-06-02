"""
日志使用示例

演示如何在项目中使用日志功能
"""

from app.utils.logger import get_logger, log_function_call, log_async_function_call

# 获取当前模块的logger
logger = get_logger(__name__)


def example_function():
    """
    普通函数示例
    """
    logger.info("开始执行普通函数")
    logger.debug("这是一个调试信息")
    logger.warning("这是一个警告信息")
    
    try:
        # 模拟一些业务逻辑
        result = 1 / 1
        logger.info(f"计算结果: {result}")
        return result
    except Exception as e:
        logger.error(f"计算出错: {str(e)}", exc_info=True)
        raise


@log_function_call
def decorated_function(param1, param2=None):
    """
    使用装饰器的函数示例
    """
    logger.info(f"处理参数: param1={param1}, param2={param2}")
    return f"处理结果: {param1} + {param2}"


async def async_example_function():
    """
    异步函数示例
    """
    logger.info("开始执行异步函数")
    
    # 模拟异步操作
    import asyncio
    await asyncio.sleep(0.1)
    
    logger.info("异步函数执行完成")
    return "异步结果"


@log_async_function_call
async def decorated_async_function(data):
    """
    使用装饰器的异步函数示例
    """
    logger.info(f"处理异步数据: {data}")
    
    import asyncio
    await asyncio.sleep(0.1)
    
    return f"异步处理结果: {data}"


class ExampleService:
    """
    服务类示例
    """
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("初始化ExampleService")
    
    def process_data(self, data):
        """
        处理数据的方法
        """
        self.logger.info(f"开始处理数据: {data}")
        
        try:
            # 模拟数据处理
            if not data:
                raise ValueError("数据不能为空")
            
            processed = data.upper() if isinstance(data, str) else str(data)
            self.logger.info(f"数据处理完成: {processed}")
            return processed
            
        except Exception as e:
            self.logger.error(f"数据处理失败: {str(e)}", exc_info=True)
            raise
    
    @log_function_call
    def decorated_method(self, value):
        """
        使用装饰器的方法
        """
        self.logger.info(f"处理值: {value}")
        return value * 2


if __name__ == "__main__":
    # 在使用前需要先初始化日志系统
    from app.utils.logger import init_logger
    
    # 初始化日志（通常在应用启动时完成）
    init_logger(log_level="DEBUG")
    
    # 使用示例
    print("=== 普通函数示例 ===")
    example_function()
    
    print("\n=== 装饰器函数示例 ===")
    decorated_function("hello", "world")
    
    print("\n=== 服务类示例 ===")
    service = ExampleService()
    service.process_data("test data")
    service.decorated_method(42)
    
    print("\n=== 异步函数示例 ===")
    import asyncio
    
    async def async_demo():
        await async_example_function()
        await decorated_async_function("async data")
    
    asyncio.run(async_demo())
    
    logger.info("所有示例执行完成") 