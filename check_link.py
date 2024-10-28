# -*- coding: utf-8 -*-
from pathlib import Path
import re
import sys
import subprocess
from collections import Counter

# 配置
root_path = input("请输入要检查的目录：")
while not Path(root_path).exists():
    root_path = input("目录不存在，请重新输入：")
root_path = Path(root_path)

exclude_paths = input("请输入要排除的目录，多个目录用英文逗号分隔：")
exclude_path_flag = True
while exclude_path_flag:
    exclude_paths = exclude_paths.split(",")
    exclude_paths = [Path(x.strip()) for x in exclude_paths]
    for exclude_path in exclude_paths:
        if not exclude_path.exists():
            print("目录不存在：{}".format(exclude_path))
            exclude_path_flag = True
            break
        else:
            exclude_path_flag = False
    if exclude_path_flag:
        exclude_paths = input("目录不存在，请重新输入：")

exclude_re = input("请输入要排除的文件名及路径的正则表达式：")
#exclude_re = r".[Ss]ample.|.EXTRA.|.MANGA.|.NCOP.|.NCED.|.BDMenu.|.PV\d{1,2}.|.Menu\d{1,2}.|.CDs.|.Scans.|\[[Cc][Mm](?:\d{1,2}|)\]|\[IV\]|The Making of Made in Abyss"
# 常见的媒体文件后缀
media_suffix = {'.m2ts', '.mka', '.MP4', '.mp4', '.mkv', '.ts', '.TS'}

print("开始检查硬链接")
# 递归遍历目录
media_list = []
for path in root_path.rglob("*.*"):
    if path.is_file() and path.suffix in media_suffix:
        exclude_flag = False
        for exclude_path in exclude_paths:
            if exclude_path in path.parents:
                exclude_flag = True
                break
        if not exclude_flag:
            media_list.append(path)
media_count = len(media_list)
print("共找到{}个媒体文件，开始查询文件ID".format(media_count))


def find_fileid(_path: Path):
    _path = Path(_path.as_posix().replace("\\", "/"))
    _file_id = subprocess.getoutput("fsutil file queryFileId \"{}\"".format(_path.resolve()))
    _file_id = re.findall(r"0x[0-9a-z]{32}$", _file_id)
    if not _file_id:
        _path = Path("//?/" + _path.as_posix().replace("\\", "/"))
        _file_id = subprocess.getoutput("fsutil file queryFileId \"{}\"".format(_path.resolve()))
        _file_id = re.findall(r"0x[0-9a-z]{32}$", _file_id)
        if not _file_id:
            print("无法查询到文件ID：{}".format(_path))
            return None
        else:
            return _file_id[0]
    else:
        return _file_id[0]


# 逐个检查硬链接
error_list = []
file_id_list = []
file_dict = {}
i = 0
for media in media_list:
    i += 1
    file_id = find_fileid(media)
    if not file_id:
        error_list.append(media)
    else:
        file_id = file_id
        file_id_list.append(file_id)
        if file_dict.get(file_id):
            file_dict[file_id].append(media)
        else:
            file_dict[file_id] = [media]
    print("\r", end="")
    print("{}/{}".format(i, media_count), end="")
    sys.stdout.flush()

if error_list:
    message = "以下文件无法查询到文件ID：\n" + "\n".join([str(x) for x in error_list])
    with open("error.txt", mode='w', encoding='utf-8') as error_flie:
        error_flie.write(message)

if file_id_list:
    nolink_file_id_list = [key for key, val in dict(Counter(file_id_list)).items() if val == 1]
    nolink_file_list = [str(file_dict[x][0]) for x in nolink_file_id_list]
    nolink_file_list_exclude = []
    for file in nolink_file_list.copy():
        if re.findall(exclude_re, file):
            nolink_file_list_exclude.append(file)
            nolink_file_list.remove(file)
    if nolink_file_list_exclude:
        message = "以下文件没有硬链接，但是符合排除条件：\n" + "\n".join(nolink_file_list_exclude)
        with open("nolink_exclude.txt", mode='w', encoding='utf-8') as nolink_exclude_flie:
            nolink_exclude_flie.write(message)
    if nolink_file_list:
        message = "以下文件没有硬链接：\n" + "\n".join(nolink_file_list)
    else:
        message = "所有文件都有硬链接"
    with open("nolink.txt", mode='w', encoding='utf-8') as nolink_flie:
        nolink_flie.write(message)
