#! /usr/bin/env python
# -*- coding: UTF-8 -*-
# @Time : 2020/8/4 17:59 
# @Author : wei.zhang
# @File : checkapp.py
# @Software: PyCharm
import inspect
import os
import sys
from time import sleep
from common.Common import TimestampTransform as tt
from common import config
from common import log
from common.RedisOperate import Redis
from common.adbUtils import ADB


class CheckApp(object):
    def __init__(self, device):
        self.adb = ADB(device)
        self.device_id = device
        self.device_key = "MONKEY:" + device
        self.package_name = "PACKAGENAME:" + device
        self.rd = Redis()
        self.pname = self.rd.get(self.package_name)

    @staticmethod
    def get_current_function_name():
        """
        获取当前的方法名
        :return: 方法名
        """
        return inspect.stack()[1][3]

    def screenshot(self, function_name):
        """
        截图
        :param function_name: 当前调用的方法名
        :return: None
        """
        png_name = "%s_%s.png" % (function_name, tt.get_standardtime_by_offset(formats="%Y-%m-%d_%H:%M:%S"))
        self.adb.shell("screencap -p /sdcard/%s" % png_name)
        if os.environ.get("WORKSPACE"):
            local_png_name = os.path.join(os.environ.get("WORKSPACE"), png_name)
        else:
            local_png_name = png_name
        # 20181009: 调用uiautomator原生库无法拉去截图文件
        pull_png_cmd = "pull /sdcard/%s %s" % (png_name, local_png_name)
        # 20181015: 等待png文件生成
        sleep(10)
        os.system("adb -s %s %s" % (self.device_id, pull_png_cmd))
        return True

    def open_app(self):
        """
        重启APP
        :return:
        """
        retry_count = 0
        retry_flag = True
        log.info("start to execute: %s" % ("am force-stop " + self.pname))
        self.adb.shell("am force-stop " + self.pname).stdout.readlines()
        while retry_count < 3 and retry_flag:
            log.info(
                "start to execute: shell am start -n %s" % self.pname)
            self.adb.shell("monkey -p %s -v 1" % (self.pname))
            # adb.startActivity("%s/%s" % (PACKAGE_NAME, ACTIVITY_NAME))
            sleep(2)
            if self.pname not in self.adb.getCurrentPackageName():
                log.info("start to launch activity: %s" % self.pname)
                # 20181008  修复当下拉菜单挡住当前程序的问题
                try:
                    self.adb.shell("monkey -p %s -v 1" % (self.pname))
                except IndexError:
                    self.screenshot(self.get_current_function_name())
                    self.adb.quitApp(self.pname)
                sleep(2)
                if self.pname in self.adb.getCurrentPackageName():
                    log.info(
                        "launch activity: %s successfully" % self.pname)
                    retry_flag = False
                else:
                    log.error(
                        "launch activity: %s failed!" % self.pname)
                    retry_count += 1
            else:
                log.info(
                    "launch activity: %s successfully" % self.pname)
                retry_flag = False
        if not retry_flag:
            return True
        if retry_count == 3 and retry_flag:
            log.error("failed to launch %s" % self.pname)
            sys.exit("failed to launch %s" % self.pname)

    def checkapp_activity(self):
        """
        检查APP是否停留在同一页面,每检查一次
        :return:
        """
        log.info("Check if the APP stays on the same page.")
        activity_key = self.device_key + ':activity'
        activity_name = ''
        log.info("dumpsys window w | %s \/ | %s name=" % (self.adb.find_util, self.adb.find_util))
        app_activity = self.adb.getCurrentActivity()
        if activity_name != app_activity:
            log.info("Check that the APP does not stay on the same page, and reset the record times.")
            activity_name = app_activity
            self.rd.set(key=activity_key, value=0)
        if activity_name == app_activity:
            num = int(self.rd.get(activity_key)) + 1
            self.rd.set(activity_key, num)
            log.info("Check that the APP stays on the same page: %s times." % num)
            log.info("Check that the APP stays on the same page: %s" % app_activity)
        if int(self.rd.get(activity_key)) == config.get('ACTIVITY_NUM'):
            log.info("Record 5 times when the APP stays on the same page, and close the APP.")
            log.info("am force-stop %s" % self.pname)
            self.adb.quitApp(packageName=self.pname)
            self.rd.set(activity_key, 0)

    def checkapp_music(self):
        """
        检查APP后台是否有音乐类APP启动，如果有就进行关闭
        :return:
        """
        log.info("Check to see if a music APP has started.")
        musicapp_list = self.adb.getRunBackgroundProcess()
        for musicapp in musicapp_list:
            if musicapp in config.get('BLACKLIST_PACKAGE'):
                log.info("Close the application：%s" % musicapp)
                self.adb.quitApp(musicapp)
        if self.pname in musicapp_list:
            log.info("restart：%s" % self.pname)
            self.open_app()

    def checkapp_monkey(self):
        """
        检查当前设备是否运行有monkey
        当运行monkey进程大于等于2，杀掉多余进程
        :return:
        """
        log.info("Check to see if an Monkey is running")
        monkeylist = self.adb.getRunMonkeyStatus()
        if len(monkeylist) >= 1:
            monkeylist.pop()
            self.adb.shell('kill -9 {}'.format(''.join(monkeylist)))
            return True
        log.info("未检测到monkey执行")
        return False

    def do_command(self, cmd):
        return os.popen(cmd).readlines()

    def pull_monkey_log(self):
        current_path = os.path.dirname(__file__) + 'Logs\\'
        if not os.path.exists(current_path):
            os.makedirs(current_path)
        filelist = self.rd.lrange(self.device_key + 'LOG')
        for filename in filelist:
            filen = filename.decode('utf-8')
            filepath = current_path + filen
            self.adb.pull_file(filen, filepath)
            self.rd.lrem(self.device_key + 'LOG', filen)

    def connect_client(self):
        connected_devices = self.do_command('adb devices')
        devices_list = []
        devices_id = []
        log.info(connected_devices)
        for i in [i.split('\t') for i in connected_devices]:
            if len(i) >= 2:
                devices_list.append(i)
                devices_id.append(i[0])
        for devices, status in devices_list:
            if status.replace('\n', '') == 'unauthorized':
                log.info(
                    "The {} equipment is not authorized, please try again after authorization".format(
                        self.device_id))
            elif status.replace('\n', '') == 'offline':
                log.info("{} Device connection dropped, try to relink ...".format(self.device_id))
                if self.device_id.find(':'):
                    log.info('Not connected via Wi-Fi, ready to connect {}...'.format(self.device_id))
                    self.adb.connect_devices(devices_id=self.device_id)
                else:
                    log.info(
                        '{} abnormal connection via USB,Please check the USB link !'.format(self.device_id))
            elif status.replace('\n', '') == 'device':
                log.info('{} Device connection is normal'.format(self.device_id))
            else:
                log.info('{} abnormal connection via'.format(self.device_id))
            if self.device_id not in devices_id:
                log.info('The {} device is disconnected.'.format(self.device_id))
                if self.device_id.find(':'):
                    log.info('Not connected via Wi-Fi, ready to connect {}...'.format(self.device_id))
                    self.adb.connect_devices(devices_id=self.device_id)
                else:
                    log.info(
                        '{} abnormal connection via USB,Please check the USB link !'.format(self.device_id))
