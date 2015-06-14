# -*- coding: utf-8 -*-
from dogpile import DogpileParser
from emailgrabber import CommonIGEmailTask
from core import execute_task


class IG_Email_Dogpile(CommonIGEmailTask):
    """
    Search emails in pages from source
    """
    parser = DogpileParser

    def test(self):
        """
        Test function
        """
        self.target = "clariant.com"
        self.main()

execute_task(IG_Email_Dogpile)
