import os, hashlib, time, schedule
from subprocess import PIPE, Popen, CalledProcessError, TimeoutExpired, call
from pathlib import Path


class Mtree(object):
    _name = 'log_files'

    def get_base_line(self):
        Path('/home/PycharmProjects/pythonProject/base_log.txt').touch()
        filesize = os.path.getsize("base_log.txt")
        if filesize == 0:
            try:
                sp_base = Popen(
                    'mtree -p /home/test_exclude/ -k flags,gid,link,mode,nlink,size,time,type,uid,md5 -c -X /home/test_exclude/ignore.txt | tail -n +7', \
                    shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                try:
                    spout, sperr = sp_base.communicate(timeout=20)
                    with open('base_log.txt', 'w') as base_log:
                        for line in spout:
                            base_log.write(line)
                    with open('base_md5.txt', 'w') as base_md5:
                        base_md5.write(hashlib.md5(spout.encode('utf-8')).hexdigest())
                except TimeoutExpired:
                    print("Timeout happened.\n")

            except CalledProcessError as e:
                print(e.output)
        return

    def is_base_changed(self, spec_log):
        is_changed = False
        with open('base_log.txt', 'r+') as b_log:
            same = set(b_log.read()).intersection(spec_log)
            same.discard('\n')
            if len(same)>0:
                for line in spec_log:
                    b_log.write(line)
                is_changed = True
        if is_changed:
            stack_md5 = hashlib.md5(spec_log.encode()).hexdigest()
            with open('base_md5.txt', 'w') as base_md5:
                base_md5.write(stack_md5)

        return is_changed

    def update_log(self):
        Path('/home/PycharmProjects/pythonProject/base_log.txt').touch()
        filesize = os.path.getsize("base_log.txt")
        if filesize == 0:
            self.get_base_line()
        try:
            spec = Popen(
                'mtree -p /home/test_exclude/ -k flags,gid,link,mode,nlink,size,time,type,uid,md5 -c -X /home/test_exclude/ignore.txt | tail -n +7',
                shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)

            sout = spec.stdout.read()

            if self.is_base_changed(sout):
                try:
                    sp_diff = Popen(
                        'mtree -p /home/test_exclude/ -k flags,gid,link,mode,nlink,size,time,type,uid,md5 -X /home/test_exclude/ignore.txt',
                        shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                    try:
                        stout, sterr = sp_diff.communicate(sout)

                        with open('diff_log.txt', 'a+') as diff_log:
                            diff_log.seek(0)
                            if len(diff_log.read()):
                                diff_log.write("\n")
                            for line in stout:
                                diff_log.write(line)

                    except TimeoutExpired:

                        print("Timeout happened.\n")

                except CalledProcessError as e:

                    print(e.output)

        except CalledProcessError as e:

            print(e.output)
        return


class MBR(object):
    _name = 'MBR_log'

    def mbr_base(self, filename: str = 'bootloader', skip: int = 0, count: int = 0) -> None:
        filesize = os.path.getsize(filename)
        if filesize == 0:
            try:
                Popen("dd if=/home/test_exclude/ of=/home/Documents" + filename + " bs=512 skip=" + str(skip) + " count=" + str(
                    count) + " iflag=skip_bytes,count_bytes" \
                      , shell=True, stderr=PIPE)

            except CalledProcessError as e:
                print(e.output)
            return

    def mbr_update(self, \
                   filename: str = 'bootloader_', skip: int = 0, count: int = 0, first_filename='bootloader') -> None:
        try:
            Popen("dd if=/home/test_exclude/ of=/home/Documents" + filename + " bs=512 skip=" + str(skip) + " count=" + str(
                count) + " iflag=skip_bytes,count_bytes" \
                  , shell=True, stderr=PIPE)
            try:
                sp_diffMBR = call("diff " + filename + '\t' + first_filename, shell=True)
                if sp_diffMBR != 0:
                    print("sth has been changed")

                    call("mv " + first_filename + '\t' + filename, shell=True)

            except TimeoutExpired:

                print("Timeout happened.\n")

        except CalledProcessError as e:

            print(e.output)


# Timer scheduler


lp = Mtree()
lp.get_base_line()
schedule.every(20).seconds.do(lp.update_log)
mbr = MBR()
mbr.mbr_base()
schedule.every(20).seconds.do(mbr.mbr_update)

while True:
    schedule.run_pending()
    time.sleep(10)
