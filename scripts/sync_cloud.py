#!/usr/bin/env python3
"""本地 vault ⇄ iCloud 镜像同步。

push：把本地笔记目录镜像到 iCloud（手机 Obsidian 阅读用）
pull：把手机写下的请求取回本地并执行（.research/requests → 本地脚本 → 结果回写）
both：先 pull 再 push

注意：macOS 不允许 launchd 后台任务访问 iCloud 容器，所以这个脚本由
桌面版 Obsidian 插件调用（Obsidian 有 iCloud 权限），或手动在终端运行。
"""
import argparse
import subprocess
import sys
from pathlib import Path

LOCAL = Path.home() / 'Research'
CLOUD = Path.home() / 'Library/Mobile Documents/iCloud~md~obsidian/Documents/research'
CODE_DIRS = ['scripts', '.obsidian/plugins']
# 除这些之外，本地顶层的东西全部镜像到云盘（新增目录自动带上，不用改代码）
EXCLUDE = {'.git', '.research', '.Trash', '.obsidian', '.DS_Store', '.github', '研究路线'}


def rsync(src, dst, extra=None):
    # iCloud 容器不允许改目录时间（launchd 下会报 failed to set times，rsync 退出 23），
    # 用 -O 忽略目录时间：文件照常同步，任务不再被误判为失败。
    args = ['rsync', '-a', '-O', '--inplace', '--exclude', '.DS_Store', '--exclude', '.git']
    if extra:
        args += extra
    args += [str(src), str(dst)]
    # 文件名里有中文时 rsync 的输出可能不是合法 UTF-8，按字节收再宽松解码。
    result = subprocess.run(args, capture_output=True)
    stderr = (result.stderr or b'').decode('utf-8', 'replace')
    if result.returncode == 0:
        return True
    # launchd 后台进程覆盖 iCloud 里已有文件会被系统拒绝（Operation not permitted）。
    # 这不是内容问题；交给 Obsidian 插件那条路径同步，任务本身不算失败。
    if result.returncode == 23 and 'Operation not permitted' in stderr:
        print('iCloud 拒绝后台覆盖已有文件，本次跳过（Obsidian 插件会继续同步）')
        return False
    raise subprocess.CalledProcessError(result.returncode, args, result.stdout, result.stderr)


def push():
    CLOUD.mkdir(parents=True, exist_ok=True)
    for name in CODE_DIRS:
        if (LOCAL / name).exists():
            rsync(str(LOCAL / name) + '/', str(CLOUD / name) + '/')
    # Route notes use merge bases so phone-written goals and feedback survive.
    result = subprocess.run([sys.executable, '-B', str(LOCAL / 'rubrics/src/publish_review.py')], check=False)
    if result.returncode:
        print('路线页面保留冲突或未同步；其余资料继续同步，不覆盖路线页面。')
    count = 0
    for entry in sorted(LOCAL.iterdir()):
        if entry.name in EXCLUDE:
            continue
        if entry.name == 'rubrics':
            rsync(str(entry) + '/', str(CLOUD / entry.name) + '/',
                  ['--exclude', 'episodes/', '--exclude', 'data/', '--exclude', 'proposals/',
                   '--exclude', 'annotations/', '--exclude', 'system/'])
        elif entry.is_dir():
            rsync(str(entry) + '/', str(CLOUD / entry.name) + '/')
        else:
            rsync(str(entry), str(CLOUD / entry.name))
        count += 1
    print(f'已推送本地 → 云盘：{count} 个顶层条目（含新增目录）+ {len(CODE_DIRS)} 个代码目录')


def pull():
    """手机写的请求取回本地执行，结果写回云盘。"""
    cloud_queue = CLOUD / '.research/requests'
    local_queue = LOCAL / '.research/requests'
    if not cloud_queue.exists():
        print('云盘没有待处理请求')
        return
    local_queue.mkdir(parents=True, exist_ok=True)
    rsync(str(cloud_queue) + '/', str(local_queue) + '/')
    for path in sorted(cloud_queue.glob('*.json')):
        path.unlink()
    if not any(local_queue.glob('*.json')):
        print('没有新请求')
        return
    subprocess.run(['/usr/bin/python3', str(LOCAL / 'scripts/requests.py')], cwd=str(LOCAL), check=False)
    # 结果与更新过的笔记同步回云盘
    rsync(str(LOCAL / '.research/responses') + '/', str(CLOUD / '.research/responses') + '/')
    push()
    print('手机请求已执行，结果已同步回云盘')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['push', 'pull', 'both'], nargs='?', default='both')
    args = parser.parse_args()
    if args.action in ('pull', 'both'):
        pull()
    if args.action in ('push', 'both'):
        push()


if __name__ == '__main__':
    main()
