##### 项目解释
> 当前项目依赖python3 第三方依赖库见requirement.txt文件

##### 思路
>1. 使用adb命令执行monkey和检查monkey运行状态
>2. 适用配置文件配置运行参数
>3. 考虑接入多设备同时执行，使用subprocess模块Popen函数开子进程执行monkey
>4. 考虑设备不定时接入，使用定时任务模块定时扫描接入设备加入执行计划
>5. 考虑不间断执行monkey，使用定时任务检查monkey运行状态，将没有运行monkey的设备重新加入执行计划
>6. 在执行中部分设备会打开非执行monkey的APP，使用定时任务定时检查进行关闭
>7. 在执行monkey过程中，有时会停留在一个页面，对执行monkey意义不大，检查ACTIVITY交于上次检查是否相同进行计算；考虑到多设备执行、降低耦合、减少适用全局变量，接入Redis存储计数，当检测到ACTIVITY大于等于配置值就杀掉APP。
>8. 支持设备多个需要执行的APP，但是同一个设备不能同时对多个APP执行monkey；取配置APP和设备安装第三方APP的交集进行随机执行，同时支持配置默认执行APP
>9. 多设备执行后产生的日志文件均放置执行设备中，支持将设备中执行日志复制到本地并且删除设备中的执行日志。这里涉及到monkey是否执行完成，只有在monkey执行完成后才能将日志拷贝。所以需要使用到Redis进行记录执行日志文件名称，并且在导出日志后需要将已导出的文件名称充Redis中删除。
