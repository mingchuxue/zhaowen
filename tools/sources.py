"""Source catalogue for the news collector."""

GN_ZH = "https://news.google.com/rss/search?hl=zh-CN&gl=CN&ceid=CN:zh-Hans&q="
GN_EN = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q="

# stype: state 官方媒体 / cnmedia 市场化媒体 / vertical 行业垂直 / overseas 境外中文
#        wire 通讯社 / intl 国际媒体 / journal 科研机构 / social 社交平台
# region: cn 境内来源 / intl 境外来源


def rss(id, name, home, feeds, *, lang, region, stype, w=1.0, cap=36, gn=None, trad=False):
    return {
        "id": id, "name": name, "home": home, "kind": "rss", "feeds": feeds,
        "lang": lang, "region": region, "stype": stype, "w": w, "cap": cap,
        "gn": gn or [], "trad": trad,
    }


def gnews(id, name, home, sites, *, lang, region, stype, cats=None, w=1.0, cap=36, gn=None, junk=None):
    base = GN_ZH if lang == "zh" else GN_EN
    feeds = [(base + "site:%s+when:{when}" % s, cats) for s in sites]
    return {
        "id": id, "name": name, "home": home, "kind": "gn", "feeds": feeds,
        "lang": lang, "region": region, "stype": stype, "w": w, "cap": cap,
        "gn": gn or [name], "junk": junk,
    }


def xacct(id, name, handle, *, lang="en", region="intl", cats=None, w=0.8):
    return {
        "id": id, "name": name, "home": "https://x.com/%s" % handle, "kind": "x",
        "handle": handle, "feeds": [(None, cats)], "lang": lang, "region": region,
        "stype": "social", "w": w, "cap": 14, "gn": [],
    }


CHINANEWS = "https://www.chinanews.com.cn/rss/%s.xml"
BBC = "https://feeds.bbci.co.uk/%s/rss.xml"
GUARDIAN = "https://www.theguardian.com/%s/rss"
NYT = "https://rss.nytimes.com/services/xml/rss/nyt/%s.xml"

SOURCES = [
    # ---------- 境内：官方媒体 ----------
    gnews("xinhua", "新华网", "https://www.news.cn", ["news.cn", "xinhuanet.com"],
          lang="zh", region="cn", stype="state", w=1.35, cap=48, gn=["新华网", "新华网客户端", "新华社"]),
    gnews("people", "人民网", "http://www.people.com.cn", ["people.com.cn"],
          lang="zh", region="cn", stype="state", w=1.3, cap=40, gn=["人民网", "共产党新闻网", "人民日报"]),
    gnews("cctv", "央视网", "https://www.cctv.com", ["cctv.com", "cctv.cn"],
          lang="zh", region="cn", stype="state", w=1.3, cap=40, gn=["央视网", "央视新闻", "CCTV"]),
    rss("chinanews", "中国新闻网", "https://www.chinanews.com.cn", [
        (CHINANEWS % "scroll-news", None),
        (CHINANEWS % "importnews", None),
        (CHINANEWS % "china", ["china"]),
        (CHINANEWS % "world", ["world"]),
        (CHINANEWS % "finance", ["finance"]),
        (CHINANEWS % "society", ["society"]),
        (CHINANEWS % "sports", ["sports"]),
        (CHINANEWS % "health", ["health"]),
        (CHINANEWS % "edu", ["edu"]),
    ], lang="zh", region="cn", stype="state", w=1.2, cap=70, gn=["中国新闻网", "中新网"]),
    gnews("cnr", "央广网", "https://www.cnr.cn", ["cnr.cn"],
          lang="zh", region="cn", stype="state", w=1.05, cap=24),
    gnews("gmw", "光明网", "https://www.gmw.cn", ["gmw.cn"],
          lang="zh", region="cn", stype="state", w=1.0, cap=24),
    gnews("chinadaily", "中国日报网", "https://cn.chinadaily.com.cn", ["chinadaily.com.cn"],
          lang="zh", region="cn", stype="state", w=1.1, cap=30, gn=["中国日报网", "中国日报"]),
    gnews("huanqiu", "环球网", "https://www.huanqiu.com", ["huanqiu.com"],
          lang="zh", region="cn", stype="state", w=1.1, cap=36),
    gnews("cyol", "中青在线", "https://www.cyol.com", ["cyol.com"],
          lang="zh", region="cn", stype="state", w=0.95, cap=20, gn=["中青在线", "中国青年报"]),
    gnews("ce", "中国经济网", "http://www.ce.cn", ["ce.cn"],
          lang="zh", region="cn", stype="state", cats=["finance"], w=0.95, cap=24),
    gnews("mil81", "中国军网", "http://www.81.cn", ["81.cn"],
          lang="zh", region="cn", stype="state", cats=["military"], w=1.1, cap=24, gn=["军网", "中国军网"]),
    gnews("stdaily", "科技日报", "https://www.stdaily.com", ["stdaily.com"],
          lang="zh", region="cn", stype="state", cats=["science"], w=1.0, cap=24),
    gnews("jyb", "中国教育新闻网", "http://www.jyb.cn", ["jyb.cn"],
          lang="zh", region="cn", stype="state", cats=["edu"], w=1.0, cap=24),

    # ---------- 境内：市场化媒体 ----------
    gnews("thepaper", "澎湃新闻", "https://www.thepaper.cn", ["thepaper.cn"],
          lang="zh", region="cn", stype="cnmedia", w=1.3, cap=48, gn=["澎湃新闻", "ThePaper", "The Paper"]),
    gnews("caixin", "财新网", "https://www.caixin.com", ["caixin.com"],
          lang="zh", region="cn", stype="cnmedia", cats=["finance"], w=1.3, cap=36, gn=["财新", "财新网"]),
    gnews("yicai", "第一财经", "https://www.yicai.com", ["yicai.com"],
          lang="zh", region="cn", stype="cnmedia", cats=["finance"], w=1.2, cap=36),
    gnews("jiemian", "界面新闻", "https://www.jiemian.com", ["jiemian.com"],
          lang="zh", region="cn", stype="cnmedia", w=1.1, cap=36, gn=["界面新闻", "Jiemian.com", "界面"]),
    gnews("bjnews", "新京报", "https://www.bjnews.com.cn", ["bjnews.com.cn"],
          lang="zh", region="cn", stype="cnmedia", w=1.1, cap=36),
    gnews("guancha", "观察者网", "https://www.guancha.cn", ["guancha.cn"],
          lang="zh", region="cn", stype="cnmedia", w=1.0, cap=30),
    gnews("ifeng", "凤凰网", "https://www.ifeng.com", ["ifeng.com"],
          lang="zh", region="cn", stype="cnmedia", w=1.0, cap=30, junk=r"#.+#"),
    gnews("cls", "财联社", "https://www.cls.cn", ["cls.cn"],
          lang="zh", region="cn", stype="cnmedia", cats=["finance"], w=1.1, cap=36),
    gnews("21jingji", "21世纪经济报道", "https://www.21jingji.com", ["21jingji.com"],
          lang="zh", region="cn", stype="cnmedia", cats=["finance"], w=1.0, cap=24, gn=["21财经", "21世纪经济报道"]),
    gnews("nbd", "每日经济新闻", "https://www.nbd.com.cn", ["nbd.com.cn"],
          lang="zh", region="cn", stype="cnmedia", cats=["finance"], w=1.0, cap=24, gn=["每日经济新闻", "每经网"]),
    gnews("wallstreetcn", "华尔街见闻", "https://wallstreetcn.com", ["wallstreetcn.com"],
          lang="zh", region="cn", stype="cnmedia", cats=["finance"], w=1.0, cap=24),

    # ---------- 境内：行业垂直 ----------
    rss("36kr", "36氪", "https://36kr.com", [("https://www.36kr.com/feed", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=1.1, cap=36, gn=["36氪", "36Kr"]),
    rss("huxiu", "虎嗅", "https://www.huxiu.com", [("https://rss.huxiu.com/", None)],
        lang="zh", region="cn", stype="vertical", w=1.05, cap=30),
    rss("ithome", "IT之家", "https://www.ithome.com", [("https://www.ithome.com/rss/", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=1.0, cap=44),
    rss("mydrivers", "快科技", "https://www.mydrivers.com", [("https://rss.mydrivers.com/rss.aspx?Tid=1", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=0.9, cap=36, gn=["快科技", "驱动之家"]),
    rss("ifanr", "爱范儿", "https://www.ifanr.com", [("https://www.ifanr.com/feed", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=0.95, cap=20),
    rss("sspai", "少数派", "https://sspai.com", [("https://sspai.com/feed", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=0.85, cap=12),
    rss("geekpark", "极客公园", "https://www.geekpark.net", [("https://www.geekpark.net/rss", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=0.95, cap=20),
    rss("leiphone", "雷峰网", "https://www.leiphone.com", [("https://www.leiphone.com/feed", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=0.9, cap=16),
    rss("tmtpost", "钛媒体", "https://www.tmtpost.com", [("https://www.tmtpost.com/rss.xml", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=0.95, cap=20),
    rss("cnbeta", "cnBeta", "https://www.cnbeta.com.tw", [("https://www.cnbeta.com.tw/backend.php", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=0.85, cap=30),
    rss("solidot", "Solidot", "https://www.solidot.org", [("https://www.solidot.org/index.rss", ["tech"])],
        lang="zh", region="cn", stype="vertical", w=0.85, cap=16),
    rss("gcores", "机核", "https://www.gcores.com", [("https://www.gcores.com/rss", ["ent"])],
        lang="zh", region="cn", stype="vertical", w=0.8, cap=12),
    gnews("autohome", "汽车之家", "https://www.autohome.com.cn", ["autohome.com.cn/news"],
          lang="zh", region="cn", stype="vertical", cats=["auto"], w=0.95, cap=24,
          junk=r"车问答|报价|参数配置|论坛|口碑|二手车|经销商|4S店|优惠\d|促销|团购|【图】.*(?:到店|实拍)"),
    gnews("d1ev", "第一电动", "https://www.d1ev.com", ["d1ev.com"],
          lang="zh", region="cn", stype="vertical", cats=["auto"], w=0.9, cap=20, gn=["第一电动网", "第一电动"],
          junk=r"为新能源汽车而生|电动汽车之家"),
    gnews("dongqiudi", "懂球帝", "https://www.dongqiudi.com", ["dongqiudi.com"],
          lang="zh", region="cn", stype="vertical", cats=["sports"], w=0.9, cap=24),
    gnews("hupu", "虎扑", "https://www.hupu.com", ["hupu.com"],
          lang="zh", region="cn", stype="vertical", cats=["sports"], w=0.85, cap=24),
    gnews("dxy", "丁香园", "https://www.dxy.cn", ["dxy.cn"],
          lang="zh", region="cn", stype="vertical", cats=["health"], w=0.95, cap=16),
    gnews("guokr", "果壳", "https://www.guokr.com", ["guokr.com"],
          lang="zh", region="cn", stype="vertical", cats=["science"], w=0.9, cap=12, gn=["果壳", "果壳科技"]),
    gnews("eol", "中国教育在线", "https://www.eol.cn", ["eol.cn"],
          lang="zh", region="cn", stype="vertical", cats=["edu"], w=0.9, cap=20),

    # ---------- 境外中文 ----------
    rss("bbczh", "BBC 中文", "https://www.bbc.com/zhongwen/simp",
        [("https://feeds.bbci.co.uk/zhongwen/simp/rss.xml", None)],
        lang="zh", region="intl", stype="overseas", w=1.15, cap=24, gn=["BBC News 中文", "BBC 中文"]),
    rss("dwzh", "德国之声中文", "https://www.dw.com/zh", [("https://rss.dw.com/rdf/rss-chi-all", None)],
        lang="zh", region="intl", stype="overseas", w=1.0, cap=24, gn=["DW", "德国之声"]),
    rss("ftchinese", "FT中文网", "https://www.ftchinese.com", [("https://www.ftchinese.com/rss/news", ["finance"])],
        lang="zh", region="intl", stype="overseas", w=1.1, cap=20, gn=["FT中文网"]),
    rss("wsjcn", "华尔街日报中文网", "https://cn.wsj.com", [("https://cn.wsj.com/zh-hans/rss", None)],
        lang="zh", region="intl", stype="overseas", w=1.1, cap=24, gn=["华尔街日报"]),
    gnews("zaobao", "联合早报", "https://www.zaobao.com.sg", ["zaobao.com.sg"],
          lang="zh", region="intl", stype="overseas", w=1.15, cap=36),

    # ---------- 国际通讯社 ----------
    gnews("reuters", "路透社", "https://www.reuters.com", ["reuters.com"],
          lang="en", region="intl", stype="wire", w=1.45, cap=48, gn=["Reuters", "路透社"]),
    gnews("ap", "美联社", "https://apnews.com", ["apnews.com"],
          lang="en", region="intl", stype="wire", w=1.4, cap=48, gn=["AP News", "The Associated Press", "美联社"]),
    gnews("afp", "法新社", "https://www.afp.com", ["afp.com"],
          lang="en", region="intl", stype="wire", w=1.2, cap=20, gn=["AFP", "法新社"]),
    gnews("bloomberg", "彭博社", "https://www.bloomberg.com", ["bloomberg.com"],
          lang="en", region="intl", stype="wire", cats=["finance"], w=1.35, cap=40, gn=["Bloomberg", "Bloomberg.com", "彭博社"]),

    # ---------- 国际媒体 ----------
    rss("bbc", "BBC", "https://www.bbc.com/news", [
        (BBC % "news/world", ["world"]),
        (BBC % "news/business", ["finance"]),
        (BBC % "news/technology", ["tech"]),
        (BBC % "news/science_and_environment", ["science"]),
        (BBC % "news/health", ["health"]),
        (BBC % "news/education", ["edu"]),
        (BBC % "news/entertainment_and_arts", ["ent"]),
        (BBC % "sport", ["sports"]),
    ], lang="en", region="intl", stype="intl", w=1.35, cap=60, gn=["BBC", "BBC News"]),
    rss("guardian", "卫报", "https://www.theguardian.com", [
        (GUARDIAN % "world", ["world"]),
        (GUARDIAN % "world/china", None),
        (GUARDIAN % "business", ["finance"]),
        (GUARDIAN % "technology", ["tech"]),
        (GUARDIAN % "science", ["science"]),
        (GUARDIAN % "environment", ["science"]),
        (GUARDIAN % "education", ["edu"]),
        (GUARDIAN % "sport", ["sports"]),
        (GUARDIAN % "film", ["ent"]),
        (GUARDIAN % "culture", ["culture"]),
    ], lang="en", region="intl", stype="intl", w=1.25, cap=60, gn=["The Guardian", "卫报"]),
    rss("nyt", "纽约时报", "https://www.nytimes.com", [
        (NYT % "HomePage", None),
        (NYT % "World", ["world"]),
        (NYT % "AsiaPacific", ["world"]),
        (NYT % "Business", ["finance"]),
        (NYT % "Technology", ["tech"]),
        (NYT % "Science", ["science"]),
        (NYT % "Climate", ["science"]),
        (NYT % "Health", ["health"]),
        (NYT % "Arts", ["culture"]),
    ], lang="en", region="intl", stype="intl", w=1.35, cap=56, gn=["The New York Times", "纽约时报中文网", "纽约时报"]),
    gnews("wsj", "华尔街日报", "https://www.wsj.com", ["wsj.com"],
          lang="en", region="intl", stype="intl", cats=["finance"], w=1.3, cap=36, gn=["The Wall Street Journal", "WSJ"]),
    rss("ft", "金融时报", "https://www.ft.com", [("https://www.ft.com/rss/home", ["finance"])],
        lang="en", region="intl", stype="intl", w=1.3, cap=20, gn=["Financial Times"]),
    rss("wapo", "华盛顿邮报", "https://www.washingtonpost.com", [("https://feeds.washingtonpost.com/rss/world", ["world"])],
        lang="en", region="intl", stype="intl", w=1.2, cap=20, gn=["The Washington Post"]),
    gnews("cnn", "CNN", "https://www.cnn.com", ["cnn.com"],
          lang="en", region="intl", stype="intl", w=1.2, cap=36),
    rss("aljazeera", "半岛电视台", "https://www.aljazeera.com", [("https://www.aljazeera.com/xml/rss/all.xml", None)],
        lang="en", region="intl", stype="intl", w=1.15, cap=30, gn=["Al Jazeera"]),
    rss("npr", "NPR", "https://www.npr.org", [("https://feeds.npr.org/1001/rss.xml", None)],
        lang="en", region="intl", stype="intl", w=1.05, cap=16),
    rss("dw", "德国之声", "https://www.dw.com/en", [("https://rss.dw.com/rdf/rss-en-all", None)],
        lang="en", region="intl", stype="intl", w=1.05, cap=30, gn=["DW", "Deutsche Welle"]),
    rss("france24", "法国24", "https://www.france24.com/en", [("https://www.france24.com/en/rss", None)],
        lang="en", region="intl", stype="intl", w=1.05, cap=24, gn=["FRANCE 24", "France 24"]),
    rss("euronews", "欧洲新闻台", "https://www.euronews.com", [("https://www.euronews.com/rss", None)],
        lang="en", region="intl", stype="intl", w=0.95, cap=24, gn=["Euronews.com", "Euronews"]),
    rss("lemonde", "世界报", "https://www.lemonde.fr/en", [("https://www.lemonde.fr/en/rss/une.xml", None)],
        lang="en", region="intl", stype="intl", w=1.0, cap=14, gn=["Le Monde.fr", "Le Monde"]),
    rss("cnbc", "CNBC", "https://www.cnbc.com", [
        ("https://www.cnbc.com/id/100003114/device/rss/rss.html", ["finance"]),
        ("https://www.cnbc.com/id/10000664/device/rss/rss.html", ["finance"]),
    ], lang="en", region="intl", stype="intl", w=1.1, cap=30),
    gnews("axios", "Axios", "https://www.axios.com", ["axios.com"],
          lang="en", region="intl", stype="intl", w=1.0, cap=24),
    rss("scmp", "南华早报", "https://www.scmp.com", [
        ("https://www.scmp.com/rss/4/feed", None),
        ("https://www.scmp.com/rss/91/feed", None),
        ("https://www.scmp.com/rss/2/feed", None),
        ("https://www.scmp.com/rss/92/feed", None),
    ], lang="en", region="intl", stype="intl", w=1.15, cap=40, gn=["South China Morning Post", "南华早报"]),
    gnews("nikkei", "日经亚洲", "https://asia.nikkei.com", ["asia.nikkei.com"],
          lang="en", region="intl", stype="intl", w=1.1, cap=20, gn=["Nikkei Asia"]),
    rss("cna", "亚洲新闻台", "https://www.channelnewsasia.com", [("https://www.channelnewsasia.com/rssfeeds/8395986", None)],
        lang="en", region="intl", stype="intl", w=1.0, cap=20, gn=["CNA"]),
    rss("straitstimes", "海峡时报", "https://www.straitstimes.com", [("https://www.straitstimes.com/news/asia/rss.xml", None)],
        lang="en", region="intl", stype="intl", w=0.95, cap=20, gn=["The Straits Times"]),
    rss("japantimes", "日本时报", "https://www.japantimes.co.jp", [("https://www.japantimes.co.jp/feed/", None)],
        lang="en", region="intl", stype="intl", w=0.95, cap=20, gn=["The Japan Times"]),
    rss("yonhap", "韩联社", "https://en.yna.co.kr", [("https://en.yna.co.kr/RSS/news.xml", None)],
        lang="en", region="intl", stype="intl", w=1.0, cap=24, gn=["Yonhap News Agency"]),
    rss("toi", "印度时报", "https://timesofindia.indiatimes.com", [("https://timesofindia.indiatimes.com/rssfeedstopstories.cms", None)],
        lang="en", region="intl", stype="intl", w=0.9, cap=20, gn=["The Times of India"]),
    rss("abcau", "澳大利亚广播公司", "https://www.abc.net.au/news", [("https://www.abc.net.au/news/feed/51120/rss.xml", None)],
        lang="en", region="intl", stype="intl", w=0.95, cap=20, gn=["ABC News (Australia)"]),
    rss("cbc", "加拿大广播公司", "https://www.cbc.ca/news", [("https://www.cbc.ca/webfeed/rss/rss-world", ["world"])],
        lang="en", region="intl", stype="intl", w=0.95, cap=16, gn=["CBC News"]),

    # ---------- 国际：科技 ----------
    rss("verge", "The Verge", "https://www.theverge.com", [("https://www.theverge.com/rss/index.xml", ["tech"])],
        lang="en", region="intl", stype="intl", w=1.05, cap=16),
    rss("arstechnica", "Ars Technica", "https://arstechnica.com", [("https://feeds.arstechnica.com/arstechnica/index", ["tech"])],
        lang="en", region="intl", stype="intl", w=1.0, cap=16),
    rss("techcrunch", "TechCrunch", "https://techcrunch.com", [("https://techcrunch.com/feed/", ["tech"])],
        lang="en", region="intl", stype="intl", w=1.0, cap=16),
    rss("wired", "连线", "https://www.wired.com", [("https://www.wired.com/feed/rss", ["tech"])],
        lang="en", region="intl", stype="intl", w=1.0, cap=20, gn=["WIRED"]),
    rss("engadget", "Engadget", "https://www.engadget.com", [("https://www.engadget.com/rss.xml", ["tech"])],
        lang="en", region="intl", stype="intl", w=0.9, cap=16),
    rss("mittr", "麻省理工科技评论", "https://www.technologyreview.com", [("https://www.technologyreview.com/feed/", ["tech"])],
        lang="en", region="intl", stype="intl", w=1.05, cap=10, gn=["MIT Technology Review"]),

    # ---------- 国际：科学 / 健康 / 教育 ----------
    rss("nature", "自然", "https://www.nature.com", [("https://www.nature.com/nature.rss", ["science"])],
        lang="en", region="intl", stype="journal", w=1.15, cap=16, gn=["Nature"]),
    rss("sciencedaily", "每日科学", "https://www.sciencedaily.com", [("https://www.sciencedaily.com/rss/all.xml", ["science"])],
        lang="en", region="intl", stype="journal", w=0.9, cap=20, gn=["ScienceDaily"]),
    rss("sciencenews", "科学新闻", "https://www.sciencenews.org", [("https://www.sciencenews.org/feed", ["science"])],
        lang="en", region="intl", stype="journal", w=0.95, cap=12, gn=["Science News"]),
    rss("quanta", "量子杂志", "https://www.quantamagazine.org", [("https://www.quantamagazine.org/feed/", ["science"])],
        lang="en", region="intl", stype="journal", w=1.0, cap=6, gn=["Quanta Magazine"]),
    rss("phys", "Phys.org", "https://phys.org", [("https://phys.org/rss-feed/", ["science"])],
        lang="en", region="intl", stype="journal", w=0.85, cap=16),
    rss("nasa", "美国航天局", "https://www.nasa.gov", [("https://www.nasa.gov/feed/", ["science"])],
        lang="en", region="intl", stype="journal", w=1.0, cap=10, gn=["NASA"]),
    rss("stat", "STAT", "https://www.statnews.com", [("https://www.statnews.com/feed/", ["health"])],
        lang="en", region="intl", stype="intl", w=0.95, cap=14, gn=["STAT"]),
    rss("insidehighered", "Inside Higher Ed", "https://www.insidehighered.com",
        [("https://www.insidehighered.com/rss.xml", ["edu"])],
        lang="en", region="intl", stype="intl", w=0.85, cap=10),
    gnews("edweek", "教育周刊", "https://www.edweek.org", ["edweek.org"],
          lang="en", region="intl", stype="intl", cats=["edu"], w=0.85, cap=10, gn=["Education Week"]),

    # ---------- 国际：体育 / 娱乐 / 汽车 / 军事 ----------
    gnews("espn", "ESPN", "https://www.espn.com", ["espn.com"],
          lang="en", region="intl", stype="intl", cats=["sports"], w=1.0, cap=24,
          junk=r"\(\w{3} \d{1,2}, \d{4}\)|Box Score|Game Recap|Live Score|Schedule|Standings|Odds"),
    rss("skysports", "天空体育", "https://www.skysports.com", [("https://www.skysports.com/rss/12040", ["sports"])],
        lang="en", region="intl", stype="intl", w=0.95, cap=16, gn=["Sky Sports"]),
    rss("variety", "综艺", "https://variety.com", [("https://variety.com/feed/", ["ent"])],
        lang="en", region="intl", stype="intl", w=1.0, cap=16, gn=["Variety"]),
    rss("thr", "好莱坞报道", "https://www.hollywoodreporter.com", [("https://www.hollywoodreporter.com/feed/", ["ent"])],
        lang="en", region="intl", stype="intl", w=0.95, cap=14, gn=["The Hollywood Reporter"]),
    rss("deadline", "Deadline", "https://deadline.com", [("https://deadline.com/feed/", ["ent"])],
        lang="en", region="intl", stype="intl", w=0.9, cap=14),
    rss("billboard", "公告牌", "https://www.billboard.com", [("https://www.billboard.com/feed/", ["ent"])],
        lang="en", region="intl", stype="intl", w=0.9, cap=10, gn=["Billboard"]),
    rss("ign", "IGN", "https://www.ign.com", [("https://www.ign.com/rss/articles/feed", ["ent"])],
        lang="en", region="intl", stype="intl", w=0.85, cap=12),
    rss("electrek", "Electrek", "https://electrek.co", [("https://electrek.co/feed/", ["auto"])],
        lang="en", region="intl", stype="intl", w=0.9, cap=16),
    rss("insideevs", "InsideEVs", "https://insideevs.com", [("https://insideevs.com/rss/news/all/", ["auto"])],
        lang="en", region="intl", stype="intl", w=0.85, cap=12),
    rss("motor1", "Motor1", "https://www.motor1.com", [("https://www.motor1.com/rss/news/all/", ["auto"])],
        lang="en", region="intl", stype="intl", w=0.85, cap=12),
    rss("defensenews", "防务新闻", "https://www.defensenews.com", [("https://www.defensenews.com/arc/outboundfeeds/rss/", ["military"])],
        lang="en", region="intl", stype="intl", w=1.0, cap=12, gn=["Defense News"]),
    rss("twz", "The War Zone", "https://www.twz.com", [("https://www.twz.com/feed", ["military"])],
        lang="en", region="intl", stype="intl", w=0.95, cap=12),
    gnews("breakingdefense", "Breaking Defense", "https://breakingdefense.com", ["breakingdefense.com"],
          lang="en", region="intl", stype="intl", cats=["military"], w=0.9, cap=10),

    # ---------- 社交平台：官方推特账号 ----------
    xacct("x-ap", "美联社 · 推特", "AP", w=0.95),
    xacct("x-bbcworld", "BBC World · 推特", "BBCWorld", w=0.95),
    xacct("x-bloomberg", "彭博社 · 推特", "business", cats=["finance"], w=0.9),
    xacct("x-cnn", "CNN · 推特", "CNN", w=0.85),
    xacct("x-nytimes", "纽约时报 · 推特", "nytimes", w=0.9),
    xacct("x-cgtn", "CGTN · 推特", "CGTNOfficial", w=0.85),
    xacct("x-globaltimes", "环球时报 · 推特", "globaltimesnews", w=0.85),
    xacct("x-spacex", "SpaceX · 推特", "SpaceX", cats=["science"], w=0.85),
    xacct("x-nasa", "NASA · 推特", "NASA", cats=["science"], w=0.85),
    xacct("x-who", "世界卫生组织 · 推特", "WHO", cats=["health"], w=0.85),
]

# Google News topic headlines: used to mark stories that are on the front page.
TOPIC_FEEDS = [
    ("https://news.google.com/rss/headlines/section/topic/%s?hl=zh-CN&gl=CN&ceid=CN:zh-Hans" % t, c)
    for t, c in (("WORLD", "world"), ("NATION", "china"), ("BUSINESS", "finance"), ("TECHNOLOGY", "tech"),
                 ("ENTERTAINMENT", "ent"), ("SPORTS", "sports"), ("SCIENCE", "science"), ("HEALTH", "health"))
] + [
    ("https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans", None),
    ("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", None),
] + [
    ("https://news.google.com/rss/headlines/section/topic/%s?hl=en-US&gl=US&ceid=US:en" % t, c)
    for t, c in (("WORLD", "world"), ("BUSINESS", "finance"), ("TECHNOLOGY", "tech"), ("SCIENCE", "science"),
                 ("HEALTH", "health"), ("SPORTS", "sports"), ("ENTERTAINMENT", "ent"))
]

STYPES = [
    ("state", "官方媒体"),
    ("cnmedia", "市场化媒体"),
    ("vertical", "行业媒体"),
    ("overseas", "境外中文媒体"),
    ("wire", "国际通讯社"),
    ("intl", "国际媒体"),
    ("journal", "科研与机构"),
    ("social", "社交平台"),
]
