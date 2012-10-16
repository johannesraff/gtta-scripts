# -*- coding: utf-8 -*-

from sys import path
path.append('pythonlib')

import gtta
import w3af_utils

class DetectTransparentProxyTask(gtta.Task, w3af_utils.W3AFScriptLauncher):
    """
    GTTA task:
        w3af: detectTransparentProxy
    """
    def main(self):
        """
        Main function
        """
        super(DetectTransparentProxyTask, self).main()

    def _get_commands(self):
        """
        Returns the list of w3af commands
        """
        return [
            "plugins",
            "discovery detectTransparentProxy",
            "back"
        ]

gtta.execute_task(DetectTransparentProxyTask)
