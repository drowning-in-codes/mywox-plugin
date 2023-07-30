# encoding=utf8
import json
from bs4 import BeautifulSoup
from wox import Wox, WoxAPI
import pyperclip, copy, logging, os, webbrowser, requests, time, subprocess, hashlib
import uuid

# 配置信息
BILI_LIVE = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/w_live_users"
LEADING = "bilive"
LIVE_URL="https://live.bilibili.com/"

# 错误信息模板
ERROR_TEMPLATE = {
    "Title": "{}",
    "SubTitle": "{}",
    "IcoPath": "Images/error.png",
    "JsonRPCAction": {
        "method": "{}",
        "parameters": [],
        "dontHideAfterAction": True,
    },
}


# 日志记录
class Logger:
    def __init__(self):
        filename = os.path.join(os.path.dirname(__file__), 'log.txt')
        logging.basicConfig(level=logging.DEBUG, filename=filename, filemode='a',
                            format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        self.logger = logging.getLogger()

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)


# https://github.com/qianlifeng/Wox/blob/master/PythonHome/wox.py
# 继承Wox类
class Main(Wox):
    def request(self, url, params=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42',
            "Cookie": "SESSDATA={}".format(self.sessdata),
        }
        # If user set the proxy, you should handle it.
        if self.proxy and self.proxy.get("enabled") and self.proxy.get("server"):
            proxies = {
                "http": "http://{}:{}".format(self.proxy.get("server"), self.proxy.get("port")),
                "https": "http://{}:{}".format(self.proxy.get("server"), self.proxy.get("port"))}
            return requests.get(url, params=params, headers=headers, proxies=proxies)
        else:
            return requests.get(url, params=params, headers=headers)


    def checkfile(self):
        """
        读取配置文件
        :param showtr:
        :return:
        """
        """
        检查配置文件
        """
        self.logger.info("-------------检查配置文件--------------")
        try:
            with open("./config.json", "r+") as f:
                config = json.load(f)
        except FileNotFoundError:
            self.show_err(self.results, "配置文件不存在,正在帮您创建")
            with open("./config.json", "w+") as f:
                json.dump({"SESSDATA": ""}, f)
            return False
        except json.decoder.JSONDecodeError:
            self.show_err(self.results, "配置文件格式错误", method="openviewer")
            return False
        self.sessdata = config.get("SESSDATA","")
        if not self.sessdata:
            self.show_err(self.results, "配置文件格式错误,缺少SESSDATA字段,请设置您的Cookie", method="openviewer")
            return False
        self.logger.info("配置正确")
        return True
    # 增加展示内容
    def add_item(self, title, subtitle, icopath, method, *parameters):
        item = {
            "Title": title,
            "SubTitle": subtitle,
            "IcoPath": icopath,
            "JsonRPCAction": {
                "method": method,
                "parameters": parameters,
                "dontHideAfterAction": True,
            },
        }
        return item

    def show_err(self, results, errmsg, method="copy2clipboard", *param):
        """
        thanks to https://github.com/mzfr/Wox.Plugin.Timezones/blob/main/time_convertor.py
        展示错误信息与时间
        :param method:
        :param errmsg:
        :param results:
        :param converted_time:
        :return:
        """
        t = time.localtime(time.time())
        template = copy.deepcopy(ERROR_TEMPLATE)
        template["Title"] = template["Title"].format(errmsg)
        template["SubTitle"] = template["SubTitle"].format(time.asctime(t))
        template["JsonRPCAction"]["method"] = template["JsonRPCAction"]["method"].format(method)
        if method == "copy2clipboard":
            template["JsonRPCAction"]["parameters"].append(errmsg)
        else:
            template["JsonRPCAction"]["parameters"].extend(param)
        results.append(template)

    def add_param(self, text):
        s = LEADING+" "+" ".join(list(text))
        WoxAPI.change_query(s, True)

    def searchall(self,*param):
        self.add_param(param)

    def getlive(self,arg =""):
        self.logger.info("-------------getLive--------------")
        validConfig = self.checkfile()
        if not validConfig:
            self.logger.info("配置错误")
            return self.results
        count_res = self.request(BILI_LIVE)
        if count_res.status_code == 200:
            resp = count_res.json()
            count = resp.get("data").get("count")
            res = self.request(BILI_LIVE,params={"size":count})
            if res.status_code == 200:
                resp = res.json()
                data = resp.get("data").get("items")
                for item in data:
                    self.results.append(
                        self.add_item("uid:"+str(item.get("uid"))+" 用户名:"+item.get("uname"), "直播标题:"+item.get("title"), "Images/pic.png", "openUrl", item.get("link")))
                if arg:
                    self.results = [result for result in self.results if arg in result.get("uname")]
                self.results.append(self.add_item("正在直播", "共{}个".format(count), "Images/pic.png","openUrl",LIVE_URL))
            else:
                self.show_err(self.results, "请求失败")
        else:
            self.show_err(self.results, "请求失败")

    #  对内容的操作
    def copy2clipboard(self, text):
        """
        复制到剪贴板
        :param tgext:
        :return:
        """
        pyperclip.copy(text)
        WoxAPI.change_query(text, False)

    def reload(self):
        """
        重载插件
        :return:
        """
        WoxAPI.reload_plugins()

    def openviewer(self, file="config.json"):
        """
        打开目录
        :param file:
        :return:
        """
        try:
            subprocess.Popen(r'explorer "{}"'.format(os.path.join(os.path.dirname(__file__), file)))
        except:
            self.show_err(self.results,
                          "打开配置文件失败,请检查配置文件{}".format(os.path.join(os.path.dirname(__file__), file)))

    def openUrl(self, url):
        """
        打开网页
        :param url:
        :return:
        """
        webbrowser.open(url)
        WoxAPI.change_query(url, False)

    # A function named query is necessary, we will automatically invoke this function when user query this plugin
    def query(self, key):
        self.results = []
        self.logger = Logger()
        self.logger.info("-------------info--------------")
        args = key.split()
        length = len(args)

        if length == 0:
            self.results.append(
                self.add_item("BiliLive", "查看自己关注的正在直播的主播", 'Images/pic.png',"searchall","all"))
            self.results.append(
                self.add_item("Config Cookie", "配置你的Cookie", 'Images/cookie.png', "openviewer"))
            self.results.append(
                self.add_item("reload", "刷新重载插件", 'Images/pic.png', "reload"))
            return self.results
        else:
            if args[0] == "all":
                self.getlive()
            else:
                self.getlive("".join(args))
            return self.results

    def context_menu(self, arg):
        return [{
            "Title": "去我的博客看看",
            "SubTitle": "www.sekyoro.top",
            "JsonRPCAction": {
                "method": "openUrl",
                "parameters": ["www.sekyoro.top"],
            }
        }]


    # Following statement is necessary


if __name__ == "__main__":
    Main()
