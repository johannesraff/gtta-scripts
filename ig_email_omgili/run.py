# -*- coding: utf-8 -*-
from omgili import OmgiliParser
from emailgrabber import CommonIGEmailTask
from core import execute_task


class IG_Email_Omgili(CommonIGEmailTask):
    """
    Search emails in pages from source
    """
    parser = OmgiliParser

    def test(self):
        """
        Test function
        """
        self.target = "clariant.com"
        self.main()

execute_task(IG_Email_Omgili)
