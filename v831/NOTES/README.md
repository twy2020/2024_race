1、V831联网 串口终端连接后，终端指令：wifi_connect_ap_test Sipeed_Guest qwert123
2、V831安装opencv.whl报错no space：
    df -h 查看剩余空间
    要给 /dev/root 分区增加空间，你需要扩展分区和文件系统。你当前的 /dev/root 是一个较小的分区，且似乎是根分区。下面是详细的步骤：

    1. 确认分区信息
    首先，确认 /dev/root 分区的详细信息和剩余可用空间：

    bash
    复制代码
    fdisk -l /dev/mmcblk0
    这将显示所有分区的详细信息。

    2. 备份数据
    在进行任何分区操作之前，确保备份所有重要数据，以防数据丢失。

    3. 删除并重新创建分区
    使用 fdisk 或 parted 工具来调整分区大小。

    使用 fdisk：
    启动 fdisk：

    bash
    复制代码
    fdisk /dev/mmcblk0
    打印分区表：

    bash
    复制代码
    p
    删除分区：

    bash
    复制代码
    d
    Partition number (1,2, default 1): 1
    重新创建分区：

    bash
    复制代码
    n
    Partition type:
    p   primary (1 primary, 0 extended, 3 free)
    e   extended (container for logical partitions)
    Select (default p): p
    Partition number (1-4, default 1): 1
    First sector (2048-1234567, default 2048): 2048
    Last sector, +sectors or +size{K,M,G,T,P} (2048-1234567, default 1234567): 
    保存更改：

    bash
    复制代码
    w
    使用 parted：
    启动 parted：

    bash
    复制代码
    parted /dev/mmcblk0
    打印分区表：

    bash
    复制代码
    print
    调整分区大小：

    bash
    复制代码
    resizepart 1
    根据提示调整分区到所需大小。

    4. 检查和扩展文件系统
    删除和重新创建分区后，需要检查并扩展文件系统。

    检查文件系统：

    bash
    复制代码
    e2fsck -f /dev/mmcblk0p1
    扩展文件系统：

    bash
    复制代码
    resize2fs /dev/mmcblk0p1
    5. 验证结果
    使用 df -h 检查分区是否已经扩展成功：

    bash
    复制代码
    df -h
    这样，你的 /dev/root 分区应该已经扩展并使用了所有可用空间。如果在执行过程中遇到任何问题，请随时告知，我会进一步帮助解决。