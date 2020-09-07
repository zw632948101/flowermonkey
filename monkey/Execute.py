#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# @Time : 2020/7/29 14:19 
# @Author : wei.zhang
# @File : Execute.py
# @Software: PyCharm
import subprocess
import threading
from common import config
from monkey.Monkey import Monkey
from common import log
from time import sleep

MOBLIE = config.get('MOBLIE')


class Execommand(Monkey):
    """
    执行monkey入口
    event_count int:执行monkey次数
    device str: 执行设备ID
    monkeyLog str: 运行脚本日志文件
    timeout int: 退出线程时间
    """

    def __init__(self, event_count, device):
        super(Execommand, self).__init__(event_count, device)
        self.process = None

    def run(self, mobile):
        def target():
            log.info('Thread started')
            sleep(2)
            self.process = subprocess.Popen(self.monkey_test(), shell=True, stdout=subprocess.PIPE)
            out, err = self.process.communicate()
            log.info('Thread finished')
            return out

        if not self.ca.checkapp_monkey():
            log.info("________execute monkey___________")
            thread = threading.Thread(target=target)
            thread.start()
            thread.join()
        else:
            log.info("There's an Monkey running")
