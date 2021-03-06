# -*- coding: utf-8 -*-
import re
import whois
import socket
from core import Task


class CommonIGDomainToolsTask(Task):
    """
    Common abstract class for ig_domain tasks
    """
    TEST_TIMEOUT = 2 * 60
    parser = None
    params = None
    results = set()
    whois_path = "http://whois.domaintools.com/"
    domain_re = r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$"
    ip_re = r"\b" \
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\." \
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\." \
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\." \
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"

    def _wrap_target(self, target):
        """
        Wrap target
        """
        return "%s" % target

    def _output_result(self):
        """
        Output result
        """
        self._write_result("\n".join(
            filter(lambda x: re.match(self.domain_re, x), self.results)))

    def _strip_url(self, url):
        """
        Strip url
        """
        return url.replace(self.whois_path, "").split("//")[-1].split("/")[0]

    def _collect_domains_by_target(self, target, is_ip=False):
        """
        Collect domains
        """
        if not is_ip:
            query = "site:domaintools.com %s" % target
        else:
            query = "ip:%s" % target

        for url in self.parser(self._wrap_target(query)).process(*self.params):
            url = self._strip_url(url)

            if url not in self.results:
                self._write_result(url)
                self.results.add(url)

    def _search_by_ip(self):
        """
        Search by ip from self.target
        """
        if re.match(self.ip_re, self.target):
            ip = self.target
        elif re.match(self.domain_re, self.target):
            ip = socket.gethostbyname(self.target)
        else:
            return

        self._collect_domains_by_target(ip, is_ip=True)

    def _search_by_target(self):
        """
        Search by self.target
        """
        self._collect_domains_by_target(self.target)

        if re.match(self.domain_re, self.target):
            self._search_by_domain()

    def _search_by_domain(self):
        """
        Search by self.target if it"s domain
        """
        # get name and emails
        domain = whois.whois(self.target)

        # search by name
        try:
            self._collect_domains_by_target("\"%s\"" % domain.name)
        except Exception as e:
            pass

        # search by emails
        try:
            map(lambda x: self._collect_domains_by_target(x), domain.emails)
        except Exception as e:
            pass

        # search by domain without TLD
        self._collect_domains_by_target(self.target[:self.target.rindex(".")])

    def main(self, *args):
        """
        Main function
        """
        if not self.parser:
            self._write_result("Parser not found.")
            return

        self.params = args

        try:
            if not self.ip:
                self._search_by_target()

            #  if "search by ip" is not needed, just redefine as "pass"
            self._search_by_ip()

        except ValueError as e:
            self._write_result(e.message)
