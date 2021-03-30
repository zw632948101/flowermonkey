#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
__author__ = 'Heng Xin'
__date__ = '2018/3/28'
"""

import logging
import os


def logger(name=None, level="DEBUG"):
    # 获取logger实例，如果参数为空则返回root logger
    if name is None:
        name = 'Monkey'
    logger_object = logging.getLogger(name)

    # 指定日志的最低输出级别，默认为WARN级别
    if level == "CRITICAL":
        logger_object.setLevel(logging.CRITICAL)
    elif level == "ERROR":
        logger_object.setLevel(logging.ERROR)
    elif level == "WARNING":
        logger_object.setLevel(logging.WARNING)
    elif level == "INFO":
        logger_object.setLevel(logging.INFO)
    else:
        logger_object.setLevel(logging.DEBUG)

    # 控制台日志
    # console_handler = logging.StreamHandler(sys.stdout)
    console_handler = logging.StreamHandler()

    # 文件日志
    current_path = os.path.dirname(__file__) + '/logFiles/'
    try:
        current_path = current_path.split('common')[0] + '/logFiles/'
    except Exception:
        pass
    if not os.path.exists(current_path):
        os.makedirs(current_path)
    file_handler = logging.FileHandler(filename=current_path + '%s.log' % name, mode='w',
                                       encoding='utf-8')

    # 指定logger输出格式
    formatter = logging.Formatter('%(asctime)s - %(filename)s - line:%(lineno)d - %(name)s - '
                                  '%(levelname)s - %(funcName)s() -  %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 为logger添加的日志处理器
    logger_object.addHandler(console_handler)
    logger_object.addHandler(file_handler)

    return logger_object
