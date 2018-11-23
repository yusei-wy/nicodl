# -*- coding: utf-8 -*-

import argparse
import configparser
import subprocess
import sys

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


class Crawler(object):
    _driver = None

    def run(self, user, password, url):
        if url is None:
            self.error("Error: url is not specified")
        print(f"run target: {url}")

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self._driver = webdriver.Chrome(chrome_options=options)

        # empty check
        if not user or not password:
            config = configparser.ConfigParser()
            config.read("./config.ini")
            password = config["account"]["password"]
            user = config["account"]["user"]

        # login
        if not self.login(user, password):
            self.error("Error: login failure")
        print("logined")

        # m3u8
        video_data = self.get_video_data(url)
        print(f"get video data: {video_data.get('title')}")

        # download
        ret = self.download(video_data.get("url"), video_data.get("title"))
        print("ret", ret)

        self.quit()

    def login(self, user, password):
        url = "https://account.nicovideo.jp/login"
        self._driver.get(url)
        self._driver.find_element_by_id("input__mailtel").send_keys(user)
        self._driver.find_element_by_id("input__password").send_keys(password)
        self._driver.find_element_by_id("login__submit").click()

        return self._driver.title == "niconico(ニコニコ)"

    def get_video_data(self, url):
        self._driver.get(url)
        title = self._driver.find_element_by_css_selector(".VideoTitle").text
        networks = self._driver.execute_script(
            "return window.performance.getEntries();"
        )

        # get m3u8 url
        m3u8_url = ""
        for n in reversed(networks):
            url = n.get("name")
            if url.find("master.m3u8?") > 0:
                m3u8_url = url
                break

        return dict(title=title, url=m3u8_url)

    def download(self, url, title):
        cmd = f"""ffmpeg \
            -protocol_whitelist file,http,https,tcp,tls,crypto \
            -i {url} \
            -movflags faststart \
            -c copy {title}.mp4 \
        """
        return subprocess.call(cmd.split())

    def error(self, msg):
        print(f"{msg}", file=sys.stderr)
        self.quit()
        exit(1)

    def quit(self):
        if self._driver is not None:
            self._driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="nicodl",
        usage="nicodl \
            -u [email or tel] \
            -p [password] \
            --target [target video page url]",
        description="Nico Nico video download software",
        add_help=True,
    )
    parser.add_argument("-u", "--user", help="email or tel number")
    parser.add_argument("-p", "--password", help="password")
    parser.add_argument("target", help="target video page url")
    args = parser.parse_args()
    cw = Crawler()
    cw.run(args.user, args.password, args.target)
