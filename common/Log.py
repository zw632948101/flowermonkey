#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
__author__ = 'Heng Xin'
__date__ = '2018/3/28'
"""


import logging
import os


class Log(object):
    def __init__(self, name, level="DEBUG"):
        self.logger = logging.getLogger(name)
        if level == "CRITICAL":
            self.logger.setLevel(logging.CRITICAL)
        elif level == "ERROR":
            self.logger.setLevel(logging.ERROR)
        elif level == "WARNING":
            self.logger.setLevel(logging.WARNING)
        elif level == "INFO":
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        current_path = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(current_path + "/Logs"):
            os.makedirs(current_path + "/Logs")
        fh = logging.FileHandler(filename=current_path + '/Logs/%s.log' % name, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(filename)s - %(name)s - '
                                      '%(levelname)s - %(funcName)s() -  %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)
