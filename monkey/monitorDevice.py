#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# @Time : 2020/7/29 15:15 
# @Author : wei.zhang
# @File : monitorDevice.py
# @Software: PyCharm
import os
import re
from apscheduler.schedulers.blocking import BlockingScheduler
from multiprocessing import Process
from common import log
from common import config
from monkey.Execute import Execommand
from monkey.checkapp import CheckApp


class monitorDevice(object):
    def __init__(self):
        super(monitorDevice, self).__init__()
        self.device_dict = {}
        self.devicelist = []
        self.phone = config.get('MOBLIE')

    def get_device_list(self):
        log.info("Gets the device ID that is now connected")
        devicestr = list(os.popen('adb devices').readlines())
        devicestr.pop()
        devicestr.pop(0)
        devicelist = [re.findall(r'^\w*\b', i)[0] for i in devicestr]
        return devicelist

    def assembly_devices(self):
        """
        对比现在获取的设备ID和原有存储的设备ID，去除已经不存在的设备ID，将新加入的设备ID设置为True
        :return:
        """

        def comparison(list1, list2, addtype):
            difference_list = set(list1).difference(set(list2))
            if addtype == 1:
                for i in list(difference_list):
                    self.device_dict[i] = {'deviceID': i, "status": True, "mobile": self.phone[0]}
                    log.info("Discover new access devices：%s ,Add the task dictionary。" % i)
            else:
                for i in list(difference_list):
                    self.phone.append(self.device_dict[i].get("mobile"))
                    self.device_dict.pop(i)
                    log.info(u" The device %s has been removed. Clear the task dictionary" % i)

        deviceslist = self.get_device_list()
        if self.device_dict is None:
            for i in deviceslist:
                self.device_dict[i] = {'deviceID': i, "status": True, "mobile": self.phone[0]}
        devicedl = []
        for device in self.device_dict.keys():
            if self.device_dict[device]['status'] == False:
                devicedl.append(device)

        comparison(deviceslist, devicedl, addtype=1)
        comparison(devicedl, deviceslist, addtype=2)
        self.fetch_execute_devices()

    def fetch_execute_devices(self):
        """
        取出为True的设备ID，用于执行
        :return:
        """
        device_dict = self.device_dict.copy()
        devicelist = []
        for i in device_dict.keys():
            if self.device_dict[i]["status"]:
                devicelist.append(i)
        self.devicelist = devicelist
        log.info(u"Fetch the unexecuted device ID")

    def execute_check(self):
        """
        执行检测APP执行
        :return:
        """
        for device in self.device_dict.keys():
            c = CheckApp(device)
            c.checkapp_activity()
            c.connect_client()

    def checkapp_monkey(self):
        for device in self.device_dict.keys():
            c = CheckApp(device)
            c.checkapp_music()
            if not c.checkapp_monkey():
                """检查是否有monkey运行，如果没有设置运行状态为True"""
                self.device_dict[device]['status'] = True
                c.pull_monkey_log()

    def run(self, device, mobile):
        """
        调用执行monkey方法
        :param device: 设备ID
        :param mobile: 手机号
        :return:
        """
        e = Execommand(event_count=50000, device=device)
        e.run(mobile)

    def multi_device_run(self):
        for i in self.devicelist:
            log.info(u"Execute device ID：%s" % i)
            self.device_dict[i]["status"] = False
            p = Process(target=self.run, args=(i, self.device_dict[i].get("mobile")))
            p.start()

    def custom_scheduler(self):
        scheduler = BlockingScheduler()
        scheduler.add_job(self.assembly_devices, 'interval', seconds=2, id='test_job1')
        scheduler.add_job(self.multi_device_run, 'interval', seconds=3, id='test_job2')
        scheduler.add_job(self.execute_check, 'interval', seconds=40, id='test_job3')
        scheduler.add_job(self.checkapp_monkey, 'interval', seconds=1, id='test_job4')
        scheduler.start()
