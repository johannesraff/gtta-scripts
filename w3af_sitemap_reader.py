# -*- coding: utf-8 -*-

from sys import path
path.append('pythonlib')

import gtta
import w3af_utils

class SitemapReaderTask(gtta.Task, w3af_utils.W3AFScriptLauncher):
    """
    GTTA task:
        w3af: sitemapReader
    """
    def main(self):
        """
        Main function
        """
        super(SitemapReaderTask, self).main()

    def _get_commands(self):
        """
        Returns the list of w3af commands
        """
        return [
            "plugins",
            "discovery sitemapReader",
            "back"
        ]

gtta.execute_task(SitemapReaderTask)
