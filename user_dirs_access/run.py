# -*- coding: utf-8 -*-

import urllib
from core import Task, execute_task

class AccessUserDirsTask(Task):
    """
    Check access to user directory
    """

    def main(self, usernames=("root",), *args):
        """
        Main function
        """
        target = '%s://%s' % (
            self.proto or 'http',
            self.host or self.ip
        )

        for username in usernames:
            if not username:
                continue

            self._check_stop()

            try:
                res = urllib.urlopen("%s/~%s" % (target, username))

                if res.code == 403:
                    msg = 'User "%s": user directory is accessible'
                else:
                    msg = 'User "%s": user directory is NOT accessible'

                msg = msg % username

            except IOError:
                msg = "Connection error"

            self._write_result(msg)

    def test(self):
        """
        Test function
        """
        self.host = "ftp.debian.org"
        self.main(["alice"])

execute_task(AccessUserDirsTask)
