"""
日志初始化工具
"""
import logging
import logging.config
import os
from pathlib import Path
from datetime import datetime
import sys


def init_logger(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "finance_app",
    enable_console: bool = True,
    enable_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    初始化日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录
        app_name: 应用名称，用于日志文件名
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        max_bytes: 单个日志文件最大字节数
        backup_count: 备份文件数量
    """
    
    # 创建日志目录
    if enable_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置字典
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {},
        'loggers': {
            '': {  # root logger
                'level': log_level,
                'handlers': []
            },
            'uvicorn': {
                'level': log_level,
                'handlers': [],
                'propagate': False
            },
            'uvicorn.access': {
                'level': log_level,
                'handlers': [],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',  # 避免SQL查询日志过多
                'handlers': [],
                'propagate': False
            }
        }
    }
    
    handler_names = []
    
    # 控制台处理器
    if enable_console:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        }
        handler_names.append('console')
    
    # 文件处理器
    if enable_file:
        # 应用日志文件
        app_log_file = os.path.join(log_dir, f'{app_name}.log')
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'detailed',
            'filename': app_log_file,
            'maxBytes': max_bytes,
            'backupCount': backup_count,
            'encoding': 'utf-8'
        }
        handler_names.append('file')
        
        # 错误日志文件
        error_log_file = os.path.join(log_dir, f'{app_name}_error.log')
        config['handlers']['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': error_log_file,
            'maxBytes': max_bytes,
            'backupCount': backup_count,
            'encoding': 'utf-8'
        }
        handler_names.append('error_file')
        
        # 访问日志文件（用于uvicorn）
        access_log_file = os.path.join(log_dir, f'{app_name}_access.log')
        config['handlers']['access_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'filename': access_log_file,
            'maxBytes': max_bytes,
            'backupCount': backup_count,
            'encoding': 'utf-8'
        }
    
    # 为所有logger添加处理器
    for logger_name in config['loggers']:
        if logger_name == 'uvicorn.access' and enable_file:
            config['loggers'][logger_name]['handlers'] = ['access_file']
            if enable_console:
                config['loggers'][logger_name]['handlers'].append('console')
        else:
            config['loggers'][logger_name]['handlers'] = handler_names
    
    # 应用配置
    logging.config.dictConfig(config)
    
    # 获取根logger并记录初始化信息
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info(f"日志系统初始化完成 - {app_name}")
    logger.info(f"日志级别: {log_level}")
    logger.info(f"控制台输出: {'启用' if enable_console else '禁用'}")
    logger.info(f"文件输出: {'启用' if enable_file else '禁用'}")
    if enable_file:
        logger.info(f"日志目录: {os.path.abspath(log_dir)}")
    logger.info("=" * 50)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取logger实例
    
    Args:
        name: logger名称，如果为None则使用调用模块的名称
    
    Returns:
        Logger实例
    """
    if name is None:
        # 获取调用者的模块名
        frame = sys._getframe(1)
        name = frame.f_globals.get('__name__', 'unknown')
    
    return logging.getLogger(name)


def log_function_call(func):
    """
    装饰器：记录函数调用日志
    
    Args:
        func: 被装饰的函数
    
    Returns:
        装饰后的函数
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"调用函数: {func.__name__}, 参数: args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {str(e)}", exc_info=True)
            raise
    
    return wrapper


def log_async_function_call(func):
    """
    装饰器：记录异步函数调用日志
    
    Args:
        func: 被装饰的异步函数
    
    Returns:
        装饰后的异步函数
    """
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"调用异步函数: {func.__name__}, 参数: args={args}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"异步函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"异步函数 {func.__name__} 执行失败: {str(e)}", exc_info=True)
            raise
    
    return wrapper 