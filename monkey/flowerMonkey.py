#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@Time: 2020 2020/4/17 9:50
__author__: wei.zhang

"""
import hashlib
import inspect
import os
import random
import sys
from imp import reload
from time import sleep
from faker import Faker
from common.Common import TimestampTransform as tt
from common.Config import Config
from common.Log import Log
import subprocess
import threading
import platform
from common.adbUtils import ADB

PACKAGE_NAME = Config('config').data['PACKAGE_NAME']
ACTIVITY_NAME = Config('config').data['ACTIVITY_NAME']
log = Log("flowerMonkey")
adb = ADB()


class Monkey(object):
    def __init__(self, event_count, device):
        """
        初始化函数
        :param event_count:
        """
        self.adb = ADB(device)
        fake = Faker(locale="zh_CN")
        log.logger.info("########################################start############################################")
        self.now = tt.get_standardtime_by_offset(formats="_%Y%m%d_%H%M%S")
        self.event_count = event_count
        self.phone = fake.phone_number()
        log.logger.info("Phone number: %s" % self.phone)
        log.logger.info("###########################start to init device#############################################")

        self.device_id = device
        if not self.device_id:
            log.logger.error("no device was found!")
            sys.exit("no device was found!")
        log.logger.info("device id: %s" % self.device_id)
        log.logger.info("package name: %s" % PACKAGE_NAME)
        self.system = platform.system()
        if self.system is "Windows":
            self.find_util = "findstr"
        else:
            self.find_util = "grep"

    def open_app(self):
        self.adb.shell("am start -n %s" % "com.github.uiautomator/.MainActivity")
        sleep(2)
        retry_count = 0
        retry_flag = True
        log.logger.info("start to execute: %s" % ("am force-stop " + PACKAGE_NAME))
        self.adb.shell("am force-stop " + PACKAGE_NAME).stdout.readlines()
        while retry_count < 3 and retry_flag:
            log.logger.info(
                "start to execute: shell am start -n %s/%s" % (PACKAGE_NAME, ACTIVITY_NAME))
            self.adb.shell("am start -n %s/%s" % (PACKAGE_NAME, ACTIVITY_NAME))
            # adb.startActivity("%s/%s" % (PACKAGE_NAME, ACTIVITY_NAME))
            sleep(2)
            if PACKAGE_NAME not in self.adb.getCurrentPackageName():
                log.logger.info("start to launch activity: %s/%s" % (PACKAGE_NAME, ACTIVITY_NAME))
                # 20181008  修复当下拉菜单挡住当前程序的问题
                try:
                    self.adb.shell("am start -n %s/%s" % (PACKAGE_NAME, ACTIVITY_NAME))
                except IndexError:
                    self.screenshot(self.get_current_function_name())
                    self.adb.quitApp(PACKAGE_NAME)
                sleep(2)
                if PACKAGE_NAME in self.adb.getCurrentPackageName():
                    log.logger.info(
                        "launch activity: %s/%s successfully" % (PACKAGE_NAME, ACTIVITY_NAME))
                    retry_flag = False
                else:
                    log.logger.error(
                        "launch activity: %s/%s failed!" % (PACKAGE_NAME, ACTIVITY_NAME))
                    retry_count += 1
            else:
                log.logger.info(
                    "launch activity: %s/%s successfully" % (PACKAGE_NAME, ACTIVITY_NAME))
                retry_flag = False
        if not retry_flag:
            return True
        if retry_count == 3 and retry_flag:
            log.logger.error("failed to launch %s" % PACKAGE_NAME)
            sys.exit("failed to launch %s" % PACKAGE_NAME)

    def checkapp_activity(self):
        """
        检查APP是否停留在同一页面,每检查一次
        :return:
        """
        log.logger.info("Check if the APP stays on the same page.")
        activity_num = 0
        activity_name = ''
        while True:
            log.logger.info("dumpsys window w | %s \/ | %s name=" % (self.adb.find_util, self.adb.find_util))
            app_activity = self.adb.getCurrentActivity()
            if activity_name != app_activity:
                log.logger.info("Check that the APP does not stay on the same page, and reset the record times.")
                activity_name = app_activity
                activity_num = 0
            if activity_name == app_activity:
                activity_num += 1
                log.logger.info("Check that the APP stays on the same page: %s times." % activity_num)
            if activity_num == 5:
                log.logger.info("Record 10 times when the APP stays on the same page, and close the APP.")
                log.logger.info("am force-stop %s" % PACKAGE_NAME)
                self.adb.quitApp(packageName=PACKAGE_NAME)
            sleep(60)

    def monkey_test(self, monkeyLog="flowerlog"):
        """执行monkey测试"""
        file_path = os.path.join(os.path.dirname(__file__), monkeyLog)
        file_path = os.path.join(file_path, "monkeyResult" + self.now + ".txt")
        log.logger.info("file_path: " + file_path)
        log.logger.info("start to execute monkey")
        seed = random.randint(1000, 10000)
        # cmd = "adb -s %s shell monkey -p %s -s  %s  --throttle 1000 --ignore-crashes --ignore-timeouts -v -v -v %s 1>%s 2>%s" % (self.device_id,PACKAGE_NAME, seed, self.event_count, file_path)
        cmd = """adb -s %s shell "monkey -p %s -s  %s --pct-touch 50  --pct-trackball 20 --pct-majornav 10 --pct-appswitch 10 --pct-anyevent 10 --ignore-crashes --ignore-timeouts --ignore-security-exceptions --ignore-native-crashes --monitor-native-crashes -v -v -v --throttle 300 %s 2>/sdcard/error.txt 1>/sdcard/info.txt"
              """ % (self.device_id, PACKAGE_NAME, seed, self.event_count)
        log.logger.info(cmd)
        return cmd

    @staticmethod
    def get_current_function_name():
        """
        获取当前的方法名
        :return: 方法名
        """
        return inspect.stack()[1][3]

    def try_logout(self):
        try:
            return self.logout()
        except TypeError:
            log.logger.info("try for the 1 time to start the server")
            self.device.wakeup()
            self.logout()
        return False

    def screenshot(self, function_name):
        """
        截图
        :param function_name: 当前调用的方法名
        :return: None
        """
        png_name = "%s_%s.png" % (function_name, tt.get_standardtime_by_offset(formats="%Y-%m-%d_%H:%M:%S"))
        self.adb.cmd("shell screencap -p /sdcard/%s" % png_name)
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

    def click_or_enter_text_operation(self, element_text, operation, text_to_set=None):
        """
        封装操作
        :param element_text: 元素的text
        :param operation: click/set_text
        :param text_to_set: 如果操作为set_text, 需要设置要输入的text
        :return:
        """
        log.logger.info("start to %s: %s" % (operation, element_text))
        if self.device(text=element_text).exists:
            log.logger.info("%s is existed" % element_text)
            log.logger.info("%s on %s" % (operation, element_text))
            if operation == "click":
                click_index = 0
                if element_text == '注册 ':
                    log.logger.info("index is changed to 1 since the element text is 注册！")
                    click_index = 1
                self.device(text=element_text)[click_index].click()
            elif operation == "set_text":
                self.device(text=element_text)[0].set_text(text_to_set)
            log.logger.info("end to %s: %s" % (operation, element_text))
        else:
            self.screenshot(self.get_current_function_name())
            sys.exit("没有找到 %s " % element_text)

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

    def copy_crash_files(self, crashfiles="/storage/emulated/0/qiansiji/crash", crashlogfile="qiansijiCrashLog"):
        """将当天的崩溃日志保存到本地"""
        # 获取崩溃文件列表
        crash_list = str(self.adb.cmd(("shell ls %s" % crashfiles)).stdout.read())
        crash_list = crash_list.split("\r\n")
        log.logger.info("-----------------崩溃日志------------------")
        log.logger.info(crash_list)
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
        log.logger.info(file_path)
        now = self.now.split("_")[1]
        nowHour = self.now.split("_")[2]
        now = now[0:4] + "-" + now[4:6] + "-" + now[6:8]
        log.logger.info("现在的日期 %s" % now)
        # 拷贝文件到本地
        log.logger.info("开始拷贝crash_list")
        for i in range(len(crash_list) - 1):
            crashListSplit = crash_list[i].split("-")
            crashHour = crashListSplit[4] + crashListSplit[5] + crashListSplit[6]
            if now in crash_list[i] and crashHour >= nowHour:
                self.adb.cmd(" pull %s" % crashfiles + "/%s " % crash_list[i] + " %s" % file_path)
                log.logger.info(" pull %s" % crashfiles + "/%s " % crash_list[i] + " %s" % file_path)
                # 过滤由于页面没有加载完成而操作的超时问题com.facebook.react.bridge.JSApplicationIllegalArgumentException
                # 过滤java.lang.OutOfMemoryError: pthread_create (1040KB stack) failed: Try again
                file = os.path.join(file_path, crash_list[i])
                sleep(10)
                fp = open(file, "r")
                strr = fp.read()
                fp.close()
                if strr.find(filterStr) != -1 or strr.find(filterStr2) != -1 or strr.find(
                        filterStr3) != -1 or strr.find(filterStr4) != -1:
                    log.logger.info("删除超时的崩溃日志 %s" % file)
                    os.remove(file)
        # 删除重复的崩溃日志
        self.delfile(file_path)
        log.logger.info("结束拷贝")

    def copy_anr_files(self, crashfiles="/data/anr", crashlogfile="floweranrlog", appName="flower"):
        """将当天的ANR(无响应)日志保存到本地"""
        # 获取ANR(无响应)文件列表
        anr_list = str(self.adb.cmd(("shell ls %s" % crashfiles)).stdout.read())
        anr_list = anr_list.split("\r\n")
        log.logger.info("ANR日志列表")
        log.logger.info(anr_list)
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
        log.logger.info(file_path)
        now = self.now.split("_")[1]
        # nowHour = self.now.split("_")[2]
        now = now[4:6] + now[6:8]
        log.logger.info("现在的日期 %s" % now)
        # now = "0913"
        # 拷贝文件到本地
        log.logger.info("开始拷贝anr_list")
        for i in range(len(anr_list) - 1):
            if appName in anr_list[i]:
                log.logger.info(file_path)
                log.logger.info("anr_list[i]")
                log.logger.info(anr_list[i])
                crashListSplit = anr_list[i].split("_")
                # crashHour = crashListSplit[4] + crashListSplit[5] + crashListSplit[6].split(".")[0]
                crash_date_list = anr_list[i].split("_")
                print(len(crash_date_list[3]))
                if len(crash_date_list[3]) == 4:
                    nowDate = "0" + crash_date_list[3][0:1] + crash_date_list[2]
                else:
                    nowDate = crash_date_list[3][0:2] + crash_date_list[2]
                log.logger.info(nowDate)
                log.logger.info(now)
                # if now in nowDate and crashHour>=nowHour:
                if now in nowDate:
                    self.adb.cmd(" pull %s" % crashfiles + "/%s " % anr_list[i] + " %s" % file_path)
                    log.logger.info(" pull %s" % crashfiles + "/%s " % anr_list[i] + " %s" % file_path)
        log.logger.info("结束拷贝")

    def create_bugreport(self):
        """保存报告"""
        # 判断monkey是否停止,每隔半小时判断一次，如果停止则生成报告，否则等待继续判断
        log.logger.info("create bugreport file")
        bug_report_dir = os.path.join(os.path.dirname(__file__), "bugReport")
        if not os.path.isdir(bug_report_dir):
            os.mkdir(bug_report_dir)
        file_path = os.path.join(bug_report_dir, self.now)
        os.mkdir(file_path)
        file_path = os.path.join(file_path, "bugReport" + self.now + ".txt")
        log.logger.info(file_path)
        if not (os.path.exists(file_path)):
            file_bug_report = open(file_path, "w")
            file_bug_report.close()
        self.adb.cmd("shell bugreport > %s" % file_path)
        sleep(30)
        chkbug_report = "java -jar %s %s" % (os.path.join(os.path.dirname(__file__), "chkbugreport.jar"), file_path)
        log.logger.info(chkbug_report)
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
                tmp_file_read.write("---------------------------------split line------------------------------------")
            f.close()
            tmp_file_read.close()

    def reboot_device(self):
        log.logger.info("reboot device")
        self.screenshot(self.get_current_function_name())
        self.adb.cmd("reboot")
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

    def connect_client(self):
        connected_devices = self.do_command('adb devices')
        if ":" in self.device_id:  # 检查是否是无线连接方式
            if self.check_client() == 0:  # 连接的设备中没有连接的设备时，执行连接设备
                print('Not connected via Wi-Fi, ready to connect {}...'.format(self.device_id))
                self.do_command('adb connect {}'.format(self.device_id))
                print('Connected to {}'.format(self.device_id))
            elif self.check_client() == 2:
                print('Wi-Fi connection is abnormal, try to reconnect {}'.format(self.device_id))
                self.do_command('adb disconnect {}'.format(self.device_id))
                sleep(0.5)
                self.do_command('adb connect {}'.format(self.device_id))
                print('Connected to {}'.format(self.device_id))
        elif self.device_id in connected_devices:
            print('Connect to {} via USB'.format(self.device_id))
        else:
            print('{} abnormal connection via USB'.format(self.device_id))


class Execommand(Monkey):
    def __init__(self, event_count, device, monkeyLog="flowerlog"):
        super(Execommand, self).__init__(event_count, device)
        self.process = None
        self.monkeyLog = monkeyLog

    def run(self, timeout):
        def target():
            log.logger.info('Thread started')
            self.process = subprocess.Popen(self.monkey_test(self.monkeyLog), shell=True, stdout=subprocess.PIPE)
            out, err = self.process.communicate()
            log.logger.info('Thread finished')
            return out

        def check_app():
            while True:
                try:
                    self.connect_client()
                    self.open_app()
                except IndexError:
                    self.screenshot(self.get_current_function_name())
                    self.open_app()
                log.logger.info("________Waiting for entry detection:30s___________")
                sleep(60)

        log.logger.info("________execute monkey___________")
        dist = list()
        for i in [target, check_app, self.checkapp_activity]:
            print(i)
            thread = threading.Thread(target=i)
            thread.start()
            dist.append(thread)

        for i in dist:
            i.join(timeout)

# if __name__ == '__main__':
#     Monkey = Execommand(event_count=3000000, device=sys.argv[1])
#     print(Monkey.run(timeout=60 * 60 * 3))
