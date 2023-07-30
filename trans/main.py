# encoding=utf8
import json
from bs4 import BeautifulSoup
from wox import Wox, WoxAPI
import pyperclip, copy, logging, os, webbrowser, requests, time, subprocess, hashlib
import uuid

# 配置信息
LEADING = 'tr'  # 触发前缀
FREETRANS = 'http://fanyi.youdao.com/translate?&doctype=json&type=AUTO&i='  # 有道免费接口
BAIDU = "https://fanyi-api.baidu.com/api/trans/vip/translate"  # 百度收费接口 有免费额度
YOUDAO = "https://openapi.youdao.com/api"  # 有道收费接口 正在完善

# 文档链接
QBAIDU = "https://fanyi-api.baidu.com/doc/21"  # 百度翻译
QZHIYUN = "https://ai.youdao.com/DOCSIRMA/html/trans/api/wbfy/index.html"  # 百度翻译

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
    def request(self, url, method="get", params=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42'
        }
        # If user set the proxy, you should handle it.
        if self.proxy and self.proxy.get("enabled") and self.proxy.get("server"):
            proxies = {
                "http": "http://{}:{}".format(self.proxy.get("server"), self.proxy.get("port")),
                "https": "http://{}:{}".format(self.proxy.get("server"), self.proxy.get("port"))}
            if method == "get":
                return requests.get(url, params=params,headers=headers, proxies=proxies)
            else:
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                return requests.post(url,data=params,headers=headers, proxies=proxies)
        else:
            if method == "get":
                return requests.get(url, params=params,headers=headers)
            else:
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                return requests.post(url, data=params, headers=headers)

    def addparam(self, *text):
        s = " ".join(list(text))
        WoxAPI.change_query(s, True)

    def configbaidu(self, *param):
        self.addparam(LEADING, *param)

    def configyoudao(self, *param):
        self.addparam(LEADING, *param)

    def freetrans(self, *param):
        self.addparam(LEADING, *param)

    def reload(self):
        WoxAPI.reload_plugins()

    def checkfile(self, filetype, showtr=True):
        """
        读取配置文件
        :param showtr:
        :param filetype:
        :return:
        """
        """
        检查配置文件
        """

        if filetype == "yd":
            self.results.append(self.add_item("有道免费翻译", "有道免费翻译", "Images/youdao.png", method=None))
        else:
            config = {}
            try:
                with open("./config.json", "r+") as f:
                    config = json.load(f)
            except FileNotFoundError:
                self.show_err(self.results, "配置文件不存在,正在帮您创建")
                with open("./config.json", "w+") as f:
                    json.dump({"bd_appid": "", "bd_key": "", "yd_appid": "", "yd_key": ""}, f)
            except json.decoder.JSONDecodeError:
                self.show_err(self.results, "配置文件格式错误", method="openviewer")

            if filetype == "bd":
                self.appid = config.get('bd_appid', "")
                self.key = config.get('bd_key', "")
                if self.appid == "" or self.key == "":
                    self.show_err(self.results, "请先配置百度翻译的appid和key", method="openviewer")

            elif filetype == "zy":
                self.appid = config.get('yd_appid', "")
                self.key = config.get('yd_key', "")
                if self.appid == "" or self.key == "":
                    self.show_err(self.results, "请先配置有道智云翻译的appid和key", method="openviewer")

            if showtr:
                self.showtrcontent(filetype)

        """
        显示翻译语言内容
        """

    def showtrcontent(self, filetype):
        """
        如果是百度或者有道智云
        """
        self.results = []
        if filetype == "bd" or filetype == "zy":
            try:
                with open("./lang.json", "r+", encoding="utf-8") as f:
                    lang = json.load(f)
                    lang = lang[filetype]
                    for k, v in lang.items():
                        self.results.append(
                            self.add_item(v + ":" + k, "翻译缩短语", "Images/bd.png", "configbaidu", filetype,
                                          k))
            except FileNotFoundError:
                with open("./lang.json", "w+") as f:
                    json.dump({
                        "bd": {
                            "auto": "自动检测",
                            "zh": "中文",
                            "en": "英语",
                            "yue": "粤语",
                            "wyw": "文言文",
                            "jp": "日语",
                            "kor": "韩语",
                            "fra": "法语",
                            "spa": "西班牙语",
                            "th": "泰语",
                            "ara": "阿拉伯语",
                            "ru": "俄语",
                            "pt": "葡萄牙语",
                            "de": "德语",
                            "it": "意大利语",
                            "el": "希腊语",
                            "nl": "荷兰语",
                            "pl": "波兰语",
                            "bul": "保加利亚语",
                            "est": "爱沙尼亚语",
                            "dan": "丹麦语",
                            "fin": "芬兰语",
                            "cs": "捷克语",
                            "rom": "罗马尼亚语",
                            "slo": "斯洛文尼亚语",
                            "swe": "瑞典语",
                            "hu": "匈牙利语",
                            "cht": "繁体中文",
                            "vie": "越南语"
                        },
                        "zy": {
                            "ar": "阿拉伯语",
                            "德语": "de",
                            "英语": "en",
                            "西班牙语": "es",
                            "法语": "fr",
                            "印地语": "hi",
                            "印度尼西亚语": "id",
                            "意大利语": "it",
                            "日语": "ja",
                            "韩语": "ko",
                            "荷兰语": "nl",
                            "葡萄牙语": "pt",
                            "俄语": "ru",
                            "泰语": "th",
                            "越南语": "vi",
                            "简体中文": "zh-CHS",
                            "繁体中文": "zh-CHT",
                            "南非荷兰语": "af",
                            "阿姆哈拉语": "am",
                            "阿塞拜疆语": "az",
                            "白俄罗斯语": "be",
                            "保加利亚语": "bg",
                            "孟加拉语": "bn",
                            "波斯尼亚语": "bs",
                            "加泰隆语": "ca",
                            "宿务语": "ceb",
                            "科西嘉语": "co",
                            "捷克语": "cs",
                            "威尔士语": "cy",
                            "丹麦语": "da",
                            "希腊语": "el",
                            "世界语": "eo",
                            "爱沙尼亚语": "et",
                            "巴斯克语": "eu",
                            "波斯语": "fa",
                            "芬兰语": "fi",
                            "斐济语": "fj",
                            "弗里西语": "fy",
                            "爱尔兰语": "ga",
                            "苏格兰盖尔语": "gd",
                            "加利西亚语": "gl",
                            "古吉拉特语": "gu",
                            "豪萨语": "ha",
                            "夏威夷语": "haw",
                            "希伯来语": "he",
                            "克罗地亚语": "hr",
                            "海地克里奥尔语": "ht",
                            "匈牙利语": "hu",
                            "亚美尼亚语": "hy",
                            "伊博语": "ig",
                            "冰岛语": "is",
                            "爪哇语": "jw",
                            "格鲁吉亚语": "ka",
                            "哈萨克语": "kk",
                            "高棉语": "km",
                            "卡纳达语": "kn",
                            "库尔德语": "ku",
                            "柯尔克孜语": "ky",
                            "拉丁语": "la",
                            "卢森堡语": "lb",
                            "老挝语": "lo",
                            "立陶宛语": "lt",
                            "拉脱维亚语": "lv",
                            "马尔加什语": "mg",
                            "毛利语": "mi",
                            "马其顿语": "mk",
                            "马拉雅拉姆语": "ml",
                            "蒙古语": "mn",
                            "马拉地语": "mr",
                            "马来语": "ms",
                            "马耳他语": "mt",
                            "白苗语": "mww",
                            "缅甸语": "my",
                            "尼泊尔语": "ne",
                            "挪威语": "no",
                            "齐切瓦语": "ny",
                            "克雷塔罗奥托米语": "otq",
                            "旁遮普语": "pa",
                            "波兰语": "pl",
                            "普什图语": "ps",
                            "罗马尼亚语": "ro",
                            "信德语": "sd",
                            "僧伽罗语": "si",
                            "斯洛伐克语": "sk",
                            "斯洛文尼亚语": "sl",
                            "萨摩亚语": "sm",
                            "修纳语": "sn",
                            "索马里语": "so",
                            "阿尔巴尼亚语": "sq",
                            "塞尔维亚语(西里尔文)": "sr-Cyrl",
                            "塞尔维亚语(拉丁文)": "sr-Latn",
                            "塞索托语": "st",
                            "巽他语": "su",
                            "瑞典语": "sv",
                            "斯瓦希里语": "sw",
                            "泰米尔语": "ta",
                            "泰卢固语": "te",
                            "塔吉克语": "tg",
                            "菲律宾语": "tl",
                            "克林贡语": "tlh",
                            "汤加语": "to",
                            "土耳其语": "tr",
                            "塔希提语": "ty",
                            "乌克兰语": "uk",
                            "乌尔都语": "ur",
                            "乌兹别克语": "uz",
                            "南非科萨语": "xh",
                            "意第绪语": "yi",
                            "约鲁巴语": "yo",
                            "尤卡坦玛雅语": "yua",
                            "粤语": "yue",
                            "南非祖鲁语": "zu"
                        }
                    }
                        , f)
            except json.decoder.JSONDecodeError:
                self.show_err(self.results, "配置文件格式错误", "openviewer", "lang.json")

            """
            展示语言选项
            """

    def showcontent(self, filetype, showtr=True):
        if filetype == "bd" or filetype == "zy" or filetype == "yd":
            self.checkfile(filetype, showtr)
        else:
            self.ydtrans(query=filetype)

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

    # A function named query is necessary, we will automatically invoke this function when user query this plugin
    def query(self, key):
        self.results = []
        self.logger = Logger()
        self.logger.info("-------------info--------------")

        args = key.split()
        length = len(args)

        if length == 0:
            self.results.append(
                self.add_item("有道智云翻译", "需要配置key", 'Images/zhiyun.png', "configyoudao", "zy"))
            self.results.append(
                self.add_item("使用有道翻译免费版本", "暂只支持中英互译", 'Images/youdao.png', "freetrans", "yd"))
            self.results.append(self.add_item("使用百度翻译", "需要配置key", 'Images/bd.png', "configbaidu", "bd"))
            self.results.append(self.add_item("重载插件", "重新加载插件", 'Images/pic.jpg', "reload"))
            return self.results

        if length == 1:
            """
            如果长度为1 要么为翻译内容直接有道免费翻译
            要么长度为2 yd bd zy,为翻译器
            """
            translater = args[0]
            self.showcontent(translater)

        elif length >= 2:
            if args[0] == "yd":
                self.ydtrans(" ".join(args[1:]))
            elif args[0] == "bd":
                self.showcontent("bd", False)
                q = " ".join(args[2:])
                if args[1].find("|") != -1:
                    from_, to = args[1].split("|")
                    if from_ == '':
                        from_ = "auto"
                    if to == '':
                        to = "en"
                    self.bdtrans(q, from_=from_, to=to)
                else:
                    q = " ".join(args[1:])
                    self.bdtrans(q)
            elif args[0] == "zy":
                # self.show_err(self.results, "有道智云翻译正在开发中")
                self.showcontent("zy", False)
                q = " ".join(args[2:])
                if args[1].find("|") != -1:
                    from_, to = args[1].split("|")
                    if from_ == '':
                        from_ = "auto"
                    if to == '':
                        to = "en"
                    self.zytrans(q, from_=from_, to=to)
                else:
                    q = " ".join(args[1:])
                    self.zytrans(q)
                # self.ydtrans(args[1])
            else:
                self.ydtrans(" ".join(args))
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

    # 翻译方法
    def ydtrans(self, query=""):

        """
        有道免费翻译
        """

        res = self.request(FREETRANS + query)
        resp = res.json()
        if res.status_code == 200:
            result = resp["translateResult"][0][0]["tgt"]
            self.results.append(self.add_item(result, "有道翻译", 'Images/youdao.png', "copy2clipboard", result))
        else:
            if res.status_code != 200:
                self.show_err(self.results, "有道翻译接口请求失败,可能是网络问题")
            else:
                errcode = resp.get("errorCode", "")
                if errcode != 0:
                    self.show_err(self.results, "翻译可能存在问题")

    def bdtrans(self, q, to="en", from_="auto"):
        salt = str(int(time.time()))[-5:]
        sign = self.appid + q + str(salt) + self.key
        sign = hashlib.md5(sign.encode()).hexdigest()
        params = {
            "q": q,
            "from": from_,
            "to": to,
            "appid": self.appid,
            "salt": salt,
            "sign": sign
        }
        res = self.request(BAIDU, params=params, method="post")
        self.results = []
        resp = res.json()
        if res.status_code == 200:
            result = resp.get("trans_result", "")
            if result:
                result = result[0]["dst"]
                self.results.append(self.add_item(result, "百度翻译", 'Images/bd.png', "copy2clipboard", result))
            else:
                errmsg = resp.get("error_msg", "")
                errcode = resp.get("error_code", "")
                if errmsg:
                    self.show_err(self.results, errcode + ":" + errmsg, "openUrl", QBAIDU)
        else:
            self.show_err(self.results, "网络出现问题,请重试")

    def zytrans(self, q, to="en", from_="auto"):
        curtime = str(int(time.time()))
        salt = str(uuid.uuid1())
        # 计算sign
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update((self.appid + q + salt + curtime + self.key).encode('utf-8'))
        sign = hash_algorithm.hexdigest()

        params = {
            "q": q,
            "from": from_,
            "to": to,
            "appKey": self.appid,
            "signType": "v3",
            "salt": salt,
            "sign": sign,
            "curtime": curtime,
        }
        res = self.request(YOUDAO, params=params, method="post")
        self.results = []
        resp = res.json()
        if res.status_code == 200:
            errcode = resp.get("errorCode", "")
            if errcode == "0":
                result = resp["translation"][0]
                lang = resp["l"]
                webtrans = resp.get("web", "")
                if webtrans:
                    webtrans = ",".join(webtrans[0]["value"])
                    result = result + "\n" + webtrans
                self.results.append(self.add_item("智云翻译 "+lang,result , 'Images/zhiyun.png', "copy2clipboard", result))
            else:
                errmsg = "出现错误,请查看错误码对应含义"
                self.show_err(self.results, errcode + ":" + errmsg, "openUrl", QZHIYUN)
        else:
            self.show_err(self.results, "网络出现问题,请重试")

    #  对内容的操作
    def copy2clipboard(self, text):
        pyperclip.copy(text)
        WoxAPI.change_query(text, False)

    def openviewer(self, file="config.json"):
        try:
            subprocess.Popen(r'explorer "{}"'.format(os.path.join(os.path.dirname(__file__), file)))
        except:
            self.show_err(self.results,
                          "打开配置文件失败,请检查配置文件{}".format(os.path.join(os.path.dirname(__file__), file)))

    def openUrl(self, url):
        webbrowser.open(url)
        WoxAPI.change_query(url, False)

    # Following statement is necessary


if __name__ == "__main__":
    Main()
