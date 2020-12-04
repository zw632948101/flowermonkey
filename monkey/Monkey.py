#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Time: 2020 2020/4/17 9:50
__author__: wei.zhang

"""
import hashlib
import os
import random
import sys
from imp import reload
from time import sleep
from common.Common import TimestampTransform as tt
from common import config
from common import log
import platform
from common.adbUtils import ADB
from monkey.checkapp import CheckApp
from common.RedisOperate import Redis

PACKAGE_NAME = config.get('PACKAGE_NAME')
ACTIVITY_NAME = config.get('ACTIVITY_NAME')
DEFAULT_PACKAGE_NAME = config.get('DEFAULT_PACKAGE_NAME')


class Monkey(object):
    def __init__(self, event_count, device):
        """
        初始化函数
        :param event_count:
        """

        super(Monkey, self).__init__()
        self.adb = ADB(device)
        self.ca = CheckApp(device)
        self.r = Redis()
        self.device_key = "MONKEYLOG:" + device
        self.package_name = "PACKAGENAME:" + device
        log.info(
            "########################################start############################################")
        self.now = tt.get_standardtime_by_offset(formats="_%Y%m%d_%H%M%S")
        self.event_count = event_count
        log.info(
            "###########################start to init device##########################################")

        self.device_id = device
        if not self.device_id:
            log.error("no device was found!")
            sys.exit("no device was found!")
        log.info("device id: %s" % self.device_id)
        self.system = platform.system()
        if self.system == "Windows":
            self.find_util = "findstr"
        else:
            self.find_util = "grep"

    def access_perform_monkey_package(self):
        """
        通过对比配置和系统安装包，如果存在多个时：1没有默认指定执行APP将从对比结果中随机取值，2有默认值时直接执行默认值
        :return:
        """
        sys_package_list = self.adb.getThirdAppList()
        intersection_package = list(set(PACKAGE_NAME).intersection(set(sys_package_list)))
        if DEFAULT_PACKAGE_NAME in intersection_package:
            return DEFAULT_PACKAGE_NAME
        return random.choice(intersection_package)

    def login_app(self, mobile):
        """
        登录APP
        :return:
        """
        self.ca.open_app()
        sleep(5)
        currentActivity = "com.dnkj.chaseflower.ui.login.activity.LoginHomeActivity"
        if currentActivity == self.adb.getCurrentActivity():
            self.adb.touchByRatio(ratioWidth=0.5, ratioHigh=0.95)
            loginactivity = "com.dnkj.chaseflower.ui.login.activity.LoginActivity"
            sleep(2)
            if loginactivity == self.adb.getCurrentActivity():
                self.adb.touchByRatio(ratioWidth=0.5, ratioHigh=0.36)
                self.adb.sendText(mobile)
                self.adb.touchByRatio(ratioWidth=0.5, ratioHigh=0.48)
                self.adb.sendText('8888')
                if self.device_id in ('CLB7N18709015438', ''):
                    self.adb.touchByRatio(ratioWidth=0.5, ratioHigh=0.8088)
                elif self.device_id in ('621QACQS55GQQ', ''):
                    self.adb.touchByRatio(ratioWidth=0.5, ratioHigh=0.59)
                else:
                    self.adb.touchByRatio(ratioWidth=0.5, ratioHigh=0.56)
                sleep(2)
            self.adb.touchByRatio(ratioWidth=0.69, ratioHigh=0.92)
            if self.adb.getCurrentActivity() == "com.dnkj.chaseflower.ui.weather.activity.WeatherHomeActivity":
                log.info("login successfully")
        elif self.adb.getCurrentActivity() == "com.dnkj.chaseflower.ui.weather.activity.WeatherHomeActivity":
            log.info("already logged")

    def write_run_packagename_to_txt(self, package_name):
        """
        将要运行的包名写入白名单
        """
        with open('whitelist.txt', 'w+') as f:
            f.write(package_name)
            f.close()
        self.adb.adb("push whitelist.txt /data/local/tmp")

    def monkey_test(self):
        """执行monkey测试"""
        log.info("start to execute monkey")
        package_name = self.access_perform_monkey_package()
        self.r.set(self.package_name, package_name)
        self.write_run_packagename_to_txt(package_name=package_name)
        seed = random.randint(1000, 100000)
        error_txt = self.device_id + '_' + str(
            tt.get_standardtime_by_offset(formats='%m%d%H%M')) + "_error.log"
        info_txt = self.device_id + '_' + str(
            tt.get_standardtime_by_offset(formats='%m%d%H%M')) + "_info.log"
        self.r.lpush(self.device_key, error_txt, info_txt)
        throttle = random.randint(3, 10) * 100
        cmd = """adb -s %s shell "monkey --pkg-whitelist-file /data/local/tmp/whitelist.txt -s %s --pct-touch 50 --pct-trackball 20 --pct-majornav 10 --pct-appswitch 10 --pct-anyevent 10 --ignore-crashes --ignore-timeouts --ignore-security-exceptions --ignore-native-crashes --monitor-native-crashes -vvv --throttle %s %s 2>/sdcard/%s 1>/sdcard/%s"
              """ % (
            self.device_id, seed, throttle, self.event_count, error_txt, info_txt)
        log.debug(cmd)
        return cmd

    def md5sum(self, file):
        """计算文件的md5值"""
        print(file)
        f = open(file, 'rb')
        md5 = hashlib.md5()
        while True:
            fb = f.read(8096)
            if not fb:
                break
            md5.update(fb)
        f.close()
        return (md5.hexdigest())

    def delfile(self, filepath):
        """删除md5值相同的文件，即删除重复的崩溃日志"""
        all_md5 = {}
        print(filepath)
        filedir = os.walk(filepath)
        for i in filedir:
            for filename in i[2]:
                file = os.path.join(filepath, filename)
                if self.md5sum(file) in all_md5.values():
                    os.remove(file)
                else:
                    all_md5[filename] = self.md5sum(file)

    def copy_crash_files(self, crashfiles="/storage/emulated/0/qiansiji/crash",
                         crashlogfile="qiansijiCrashLog"):
        """将当天的崩溃日志保存到本地"""
        # 获取崩溃文件列表
        crash_list = str(self.adb.cmd(("shell ls %s" % crashfiles)).stdout.read())
        crash_list = crash_list.split("\r\n")
        log.info("-----------------崩溃日志------------------")
        log.info(crash_list)
        filterStr = "com.facebook.react.bridge.JSApplicationIllegalArgumentException"
        filterStr2 = "java.lang.OutOfMemoryError: pthread_create (1040KB stack) failed: Try again"
        filterStr3 = "Trying to add unknown view tag"
        filterStr4 = "Package manager has died"

        # 创建本地文件夹：以当天日期命名
        crash_log_dir = os.path.join(os.path.dirname(__file__), crashlogfile)
        if not os.path.isdir(crash_log_dir):
            os.mkdir(crash_log_dir)
        file_path = os.path.join(crash_log_dir, self.now)
        if not os.path.isdir(file_path):
            os.mkdir(file_path)
        log.info(file_path)
        now = self.now.split("_")[1]
        nowHour = self.now.split("_")[2]
        now = now[0:4] + "-" + now[4:6] + "-" + now[6:8]
        log.info("现在的日期 %s" % now)
        # 拷贝文件到本地
        log.info("开始拷贝crash_list")
        for i in range(len(crash_list) - 1):
            crashListSplit = crash_list[i].split("-")
            crashHour = crashListSplit[4] + crashListSplit[5] + crashListSplit[6]
            if now in crash_list[i] and crashHour >= nowHour:
                self.adb.adb(" pull %s" % crashfiles + "/%s " % crash_list[i] + " %s" % file_path)
                log.info(" pull %s" % crashfiles + "/%s " % crash_list[i] + " %s" % file_path)
                # 过滤由于页面没有加载完成而操作的超时问题com.facebook.react.bridge.JSApplicationIllegalArgumentException
                # 过滤java.lang.OutOfMemoryError: pthread_create (1040KB stack) failed: Try again
                file = os.path.join(file_path, crash_list[i])
                sleep(10)
                fp = open(file, "r")
                strr = fp.read()
                fp.close()
                if strr.find(filterStr) != -1 or strr.find(filterStr2) != -1 or strr.find(
                        filterStr3) != -1 or strr.find(filterStr4) != -1:
                    log.info("删除超时的崩溃日志 %s" % file)
                    os.remove(file)
        # 删除重复的崩溃日志
        self.delfile(file_path)
        log.info("结束拷贝")

    def copy_anr_files(self, crashfiles="/data/anr", crashlogfile="floweranrlog", appName="flower"):
        """将当天的ANR(无响应)日志保存到本地"""
        # 获取ANR(无响应)文件列表
        anr_list = str(self.adb.shell(("ls %s" % crashfiles)).stdout.read())
        anr_list = anr_list.split("\r\n")
        log.info("ANR日志列表")
        log.info(anr_list)
        if sys.getdefaultencoding() != "utf-8":
            reload(sys)
            sys.setdefaultencoding("utf-8")
        # 创建本地文件夹：以当天日期命名
        crash_log_dir = os.path.join(os.path.dirname(__file__), crashlogfile)
        if not os.path.isdir(crash_log_dir):
            os.mkdir(crash_log_dir)
        file_path = os.path.join(crash_log_dir, self.now)
        if not os.path.isdir(file_path):
            os.mkdir(file_path)
        log.info(file_path)
        now = self.now.split("_")[1]
        # nowHour = self.now.split("_")[2]
        now = now[4:6] + now[6:8]
        log.info("现在的日期 %s" % now)
        # now = "0913"
        # 拷贝文件到本地
        log.info("开始拷贝anr_list")
        for i in range(len(anr_list) - 1):
            if appName in anr_list[i]:
                log.info(file_path)
                log.info("anr_list[i]")
                log.info(anr_list[i])
                crashListSplit = anr_list[i].split("_")
                # crashHour = crashListSplit[4] + crashListSplit[5] + crashListSplit[6].split(".")[0]
                crash_date_list = anr_list[i].split("_")
                print(len(crash_date_list[3]))
                if len(crash_date_list[3]) == 4:
                    nowDate = "0" + crash_date_list[3][0:1] + crash_date_list[2]
                else:
                    nowDate = crash_date_list[3][0:2] + crash_date_list[2]
                log.info(nowDate)
                log.info(now)
                # if now in nowDate and crashHour>=nowHour:
                if now in nowDate:
                    self.adb.adb(" pull %s" % crashfiles + "/%s " % anr_list[i] + " %s" % file_path)
                    log.info(" pull %s" % crashfiles + "/%s " % anr_list[i] + " %s" % file_path)
        log.info("结束拷贝")

    def create_bugreport(self):
        """保存报告"""
        # 判断monkey是否停止,每隔半小时判断一次，如果停止则生成报告，否则等待继续判断
        log.info("create bugreport file")
        bug_report_dir = os.path.join(os.path.dirname(__file__), "bugReport")
        if not os.path.isdir(bug_report_dir):
            os.mkdir(bug_report_dir)
        file_path = os.path.join(bug_report_dir, self.now)
        os.mkdir(file_path)
        file_path = os.path.join(file_path, "bugReport" + self.now + ".txt")
        log.info(file_path)
        if not (os.path.exists(file_path)):
            file_bug_report = open(file_path, "w")
            file_bug_report.close()
        self.adb.shell("bugreport > %s" % file_path)
        chkbug_report = "java -jar %s %s" % (
            os.path.join(os.path.dirname(__file__), "chkbugreport.jar"), file_path)
        log.info(chkbug_report)
        os.system(chkbug_report)
        print("create bugreport file done")

    def read_monkeylog(self, monkeyLog="flowerlog"):
        # 过滤monkey日志，提取GC(内存泄漏)相关日志
        monkey_file = os.path.join(os.path.dirname(__file__), monkeyLog)
        monkey_file = os.path.join(monkey_file, "monkeyResult" + self.now + ".txt")
        tmp_file = os.path.join(os.path.dirname(__file__), monkeyLog)
        tmp_file = os.path.join(tmp_file, "monkeyResult" + self.now + "_errors.txt")
        gclist = ["GC_CONCURRENT", "GC_FOR_ALLOC", "GC_EXPLICIT", "GC_BEFORE_OOM"]
        tmp_file_read = open(tmp_file, "w")
        with open(monkey_file) as f:
            lines = f.readlines()
            n = 0
            num = []
            for line in lines:
                for gc in gclist:
                    if line.find(gc) != -1:
                        num.append(n)
                n = n + 1
            for i in num:
                for x in range(i - 10, i + 30):
                    tmp_file_read.write(lines[x])
                tmp_file_read.write(
                    "---------------------------------split line------------------------------------")
            f.close()
            tmp_file_read.close()

    def reboot_device(self):
        log.info("reboot device")
        self.screenshot(self.get_current_function_name())
        self.adb.adb("reboot")
        sleep(60)

    def do_command(self, cmd):
        return os.popen(cmd).readlines()

    def check_client(self):
        connected_devices = self.do_command('adb devices')
        device_num = len(connected_devices)
        if device_num == 0:
            return 0  # 设备不在线
        else:
            for client in connected_devices:
                if self.device_id in client:
                    if 'offline' not in client:
                        return 1  # 设备连接且在线
                    else:
                        return 2  # 设备连接且不在线
                elif connected_devices.index(client) == device_num - 1:
                    return 0

# if __name__ == '__main__':
#     m = Monkey(5, '7c04826')
#     print(m.access_perform_monkey_package())
