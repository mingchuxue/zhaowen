"""Tag catalogue and keyword rules."""

CATEGORIES = [
    ("china", "国内"),
    ("world", "国际"),
    ("finance", "财经"),
    ("tech", "科技"),
    ("society", "社会"),
    ("sports", "体育"),
    ("ent", "娱乐"),
    ("health", "健康"),
    ("science", "科学"),
    ("military", "军事"),
    ("auto", "汽车"),
    ("edu", "教育"),
    ("culture", "文化"),
]

# Topical categories are matched by keywords; 国内 / 国际 come from the region tags.
CAT_RULES = {
    "finance": [
        r"股市|A股|港股|美股|股价|大盘|指数|沪指|深成指|创业板|科创板|涨停|跌停|基金|债券|国债|利率|降息|加息|降准|央行|货币政策|通胀|CPI|PPI|GDP|经济|财报|营收|净利润|融资|上市|IPO|并购|收购|投资|市值|汇率|人民币|美元|黄金|油价|原油|期货|银行|保险|券商|楼市|房价|房地产|消费|外贸|出口|进口|关税|财政|税收|企业|公司|产业|供应链|半导体产业",
        r"\b(stocks?|shares|markets?|economy|economic|inflation|interest rates?|central bank|federal reserve|earnings|revenue|profit|ipo|merger|acquisition|investors?|bonds?|treasur(y|ies)|tariffs?|trade deal|gdp|recession|oil prices?|wall street|nasdaq|dow|s&p 500|bank(s|ing)?|billion|startup|funding|valuation)\b",
    ],
    "tech": [
        r"科技|技术|人工智能|AI|大模型|芯片|半导体|手机|iPhone|安卓|鸿蒙|华为|苹果|小米|英伟达|算力|互联网|软件|操作系统|App|应用|5G|6G|量子计算|机器人|无人机|自动驾驶|数码|电脑|笔记本|显卡|处理器|网络安全|黑客|数据泄露|云计算|元宇宙|区块链|SpaceX|星舰|卫星互联网",
        r"\b(tech|technology|ai|artificial intelligence|chatbot|openai|nvidia|apple|google|microsoft|meta|amazon|samsung|chips?|semiconductors?|software|app|iphone|android|smartphone|cyber|hackers?|data breach|robots?|drones?|self-driving|autonomous|quantum computing|startup|silicon valley|outage|cloud)\b",
    ],
    "sports": [
        r"体育|足球|篮球|排球|乒乓|羽毛球|网球|田径|游泳|跳水|体操|举重|射击|滑雪|滑冰|速滑|冰球|马拉松|奥运|亚运|全运|世界杯|欧冠|英超|西甲|德甲|意甲|法甲|中超|CBA|NBA|WNBA|F1|赛车|夺冠|冠军|决赛|半决赛|比分|主教练|球员|球队|国足|女足|男篮|女篮|女排|电竞|LPL|S\d+决赛",
        r"\b(sport|sports|football|soccer|basketball|tennis|golf|cricket|rugby|olympics?|world cup|premier league|champions league|la liga|serie a|bundesliga|nba|nfl|mlb|nhl|f1|formula one|grand prix|marathon|athletics|coach|striker|midfielder|quarterback|playoffs?|semi-?finals?|tournament)\b",
    ],
    "ent": [
        r"娱乐|明星|演员|歌手|电影|影片|票房|电视剧|剧集|综艺|演唱会|音乐|专辑|导演|首映|影视|金鸡|金马|金像|奥斯卡|格莱美|戛纳|柏林电影节|威尼斯电影节|动画|动漫|游戏|主机|Switch|PS5|Xbox|手游|网红|直播",
        r"\b(film|movie|box office|actor|actress|singer|album|music|concert|tour|tv series|netflix|disney|hollywood|oscar|grammy|emmy|celebrity|festival|trailer|streaming|video games?|gaming|nintendo|playstation|xbox|gta)\b",
    ],
    "health": [
        r"健康|医疗|医院|医生|患者|疾病|病毒|疫情|流感|新冠|疫苗|癌|肿瘤|糖尿病|高血压|心脏|心血管|抑郁|心理健康|睡眠|营养|饮食|减肥|药物|新药|药品|医保|卫健委|公共卫生|麻疹|艾滋|传染病|感染|手术|临床",
        r"\b(health|medical|medicine|hospital|doctors?|patients?|disease|virus|flu|covid|vaccines?|cancer|diabetes|heart|mental health|obesity|drugs?|fda|outbreak|measles|infection|clinical|nhs|medicaid|medicare|surgery)\b",
    ],
    "science": [
        r"科学|科研|研究人员|研究团队|科学家|论文|期刊|发现|天文|宇宙|星系|黑洞|行星|火星|月球|探月|嫦娥|天宫|神舟|航天|火箭|发射|卫星|空间站|物理|化学|生物|基因|细胞|进化|化石|恐龙|考古|气候|气候变化|全球变暖|碳排放|生态|环境|地质|地震|海洋|极地|量子",
        r"\b(science|scientists?|researchers?|study|studies|journal|astronom(y|ers)|galaxy|black hole|planet|mars|moon|nasa|space|rocket|launch|satellite|starship|physics|chemistry|biology|genes?|dna|cells?|evolution|fossils?|dinosaurs?|archaeolog(y|ists)|climate|emissions|carbon|environment|species|ocean|cop\d+)\b",
    ],
    "military": [
        r"军事|军队|解放军|国防|国防部|部队|军演|演习|演训|导弹|战机|战斗机|轰炸机|航母|舰艇|驱逐舰|潜艇|无人机作战|武器|军备|防务|空袭|袭击|战争|战火|冲突|停火|士兵|将军|北约|五角大楼|兵力|核武|核弹|军工",
        r"\b(military|army|navy|air force|defen[cs]e|pentagon|nato|missiles?|fighter jets?|warships?|aircraft carrier|submarines?|troops|soldiers|airstrikes?|war|weapons?|drills?|ceasefire|nuclear weapons?|artillery|marines)\b",
    ],
    "auto": [
        r"汽车|新车|车型|轿车|SUV|MPV|电动车|新能源车|新能源汽车|纯电|混动|增程|插混|智驾|自动驾驶|车企|车市|销量|特斯拉|比亚迪|蔚来|小鹏|理想汽车|问界|小米汽车|极氪|零跑|吉利|长城汽车|长安汽车|上汽|广汽|大众|丰田|本田|宝马|奔驰|奥迪|保时捷|充电桩|电池|宁德时代|车展|驾照|车主",
        r"\b(cars?|vehicles?|evs?|electric vehicles?|tesla|byd|toyota|honda|volkswagen|vw|bmw|mercedes|audi|porsche|ford|gm|general motors|stellantis|hyundai|kia|nissan|cybercab|robotaxi|suv|sedan|pickup|automaker|carmaker|dealerships?|charging)\b",
    ],
    "edu": [
        r"教育|学校|高校|大学|中学|小学|幼儿园|学生|教师|老师|校园|高考|中考|考研|考试|招生|录取|课程|教材|双减|学位|研究生|博士|留学|教育部|学科|职业教育|就业季|毕业生",
        r"\b(education|schools?|universit(y|ies)|college|students?|teachers?|campus|exams?|admissions?|tuition|curriculum|degree|graduates?|classroom|academic)\b",
    ],
    "society": [
        r"社会|民生|事故|车祸|火灾|爆炸|坍塌|溺亡|遇难|伤亡|死亡|警方|公安|派出所|法院|判决|起诉|一审|二审|检察院|犯罪|嫌疑人|诈骗|拐卖|案件|案发|通报|救援|失联|走失|暴雨|台风|洪水|寒潮|降温|大风|暴雪|天气|气象|地震|养老|社保|医保|就业|房租|外卖|快递|网约车|出行|铁路|地铁|高铁|航班|春运|旅游|景区|文旅|节假日|婚姻|生育|人口",
        r"\b(police|court|judge|trial|sentenced|charged|arrested|murder|killed|dead|died|crash|fire|explosion|collapse|flood|storm|hurricane|typhoon|earthquake|weather|shooting|crime|lawsuit|victims?|rescue|missing|flights?|airport|airlines?|travel|tourism)\b",
    ],
    "culture": [
        r"文化|文学|作家|小说|诗歌|图书|读书|书店|出版|博物馆|展览|文物|非遗|艺术|画展|美术|书法|戏曲|京剧|昆曲|话剧|舞蹈|历史|传统|节日|民俗|建筑|设计|文学奖|茅盾|诺贝尔文学",
        r"\b(culture|cultural|art|artists?|museum|exhibition|paintings?|books?|novel|novelists?|poet(ry)?|literature|literary|theatre|theater|opera|ballet|dance|history|heritage|architecture|design|booker|nobel prize in literature)\b",
    ],
}

# Region tags: (id, label, zh pattern, en pattern)
GEO = [
    ("cn", "中国大陆",
     r"中国|我国|全国|国务院|中共|中央|国家|北京|上海|广州|深圳|天津|重庆|成都|武汉|杭州|南京|西安|长沙|郑州|沈阳|大连|青岛|厦门|苏州|福州|济南|合肥|昆明|贵阳|南宁|海口|三亚|哈尔滨|长春|石家庄|太原|呼和浩特|兰州|西宁|银川|乌鲁木齐|拉萨|新疆|西藏|内蒙古|广西|宁夏|云南|贵州|四川|湖南|湖北|河南|河北|山东|山西|陕西|甘肃|青海|江苏|浙江|安徽|福建|江西|广东|海南|辽宁|吉林|黑龙江|雄安|长三角|粤港澳|习近平|李强|王毅|外交部|商务部|国家统计局|发改委",
     r"\b(china|chinese|beijing|shanghai|shenzhen|guangzhou|xi jinping|xi's|li qiang|wang yi|xinjiang|tibet|wuhan|chengdu|hangzhou|prc|pla|ccp|communist party)\b"),
    ("hmt", "港澳台",
     r"香港|澳门|台湾|台北|高雄|台中|港府|特区政府|立法会|赖清德|国民党|民进党|港股|港交所",
     r"\b(hong kong|macau|macao|taiwan|taipei|kaohsiung|lai ching-te|kuomintang|kmt|dpp)\b"),
    ("us", "美国",
     r"美国|美方|美军|美联储|白宫|华盛顿|纽约|加州|加利福尼亚|得克萨斯|佛罗里达|芝加哥|洛杉矶|旧金山|硅谷|特朗普|拜登|万斯|鲁比奥|贝森特|国会|参议院|众议院|五角大楼|美股|华尔街|FAA|NASA",
     r"\b(united states|america|american|americans|washington|white house|trump|biden|vance|rubio|bessent|congress|senate|pentagon|new york|california|texas|florida|chicago|los angeles|san francisco|silicon valley|federal reserve|faa|fbi|cia|wall street|democrats?|republicans?|gop|medicaid|virginia|ohio|michigan|georgia|arizona)\b"),
    ("europe", "欧洲",
     r"欧洲|欧盟|英国|伦敦|法国|巴黎|德国|柏林|意大利|罗马|西班牙|葡萄牙|荷兰|比利时|瑞士|瑞典|挪威|芬兰|丹麦|波兰|匈牙利|捷克|奥地利|希腊|爱尔兰|苏格兰|马克龙|默茨|斯塔默|冯德莱恩|梵蒂冈|教皇|教宗|北约",
     r"\b(europe|european|eu|brussels|britain|british|uk|england|london|scotland|wales|ireland|irish|france|french|paris|macron|germany|german|berlin|merz|italy|italian|rome|meloni|spain|spanish|madrid|portugal|netherlands|dutch|belgium|switzerland|swiss|sweden|norway|finland|denmark|poland|hungary|orban|czech|austria|greece|vatican|pope|starmer|nato|von der leyen)\b"),
    ("ruua", "俄罗斯与乌克兰",
     r"俄罗斯|俄方|俄军|莫斯科|普京|乌克兰|乌方|乌军|基辅|泽连斯基|俄乌|白俄罗斯|克里米亚|顿巴斯",
     r"\b(russia|russian|moscow|putin|kremlin|ukraine|ukrainian|kyiv|kiev|zelensky|zelenskyy|belarus|crimea|donbas)\b"),
    ("mideast", "中东",
     r"中东|以色列|巴勒斯坦|加沙|约旦河西岸|哈马斯|真主党|黎巴嫩|叙利亚|伊朗|伊拉克|沙特|阿联酋|迪拜|卡塔尔|也门|胡塞|土耳其|埃及|内塔尼亚胡|红海",
     r"\b(middle east|israel|israeli|palestin(e|ian|ians)|gaza|west bank|hamas|hezbollah|lebanon|syria|iran|iranian|tehran|iraq|saudi|uae|dubai|qatar|yemen|houthis?|turkey|turkish|egypt|netanyahu|red sea)\b"),
    ("jpkr", "日韩朝",
     r"日本|东京|大阪|日方|自民党|高市早苗|石破|韩国|首尔|韩方|李在明|朝鲜|平壤|金正恩|半岛",
     r"\b(japan|japanese|tokyo|osaka|takaichi|ishiba|korea|korean|seoul|lee jae-myung|north korea|pyongyang|kim jong un)\b"),
    ("asean", "东南亚",
     r"东南亚|东盟|新加坡|马来西亚|印尼|印度尼西亚|泰国|曼谷|越南|河内|菲律宾|马尼拉|缅甸|柬埔寨|老挝|文莱|南海|黄岩岛",
     r"\b(southeast asia|asean|singapore|malaysia|indonesia|jakarta|thailand|thai|bangkok|vietnam|hanoi|philippines|manila|myanmar|cambodia|laos|brunei|south china sea)\b"),
    ("southasia", "南亚",
     r"印度|新德里|孟买|莫迪|巴基斯坦|孟加拉|斯里兰卡|尼泊尔|阿富汗|塔利班",
     r"\b(india|indian|new delhi|delhi|mumbai|modi|pakistan|bangladesh|sri lanka|nepal|afghanistan|taliban|bengal|bjp)\b"),
    ("africa", "非洲",
     r"非洲|非盟|南非|尼日利亚|肯尼亚|埃塞俄比亚|苏丹|刚果|塞内加尔|摩洛哥|阿尔及利亚|津巴布韦|坦桑尼亚|加纳",
     r"\b(africa|african|south africa|nigeria|kenya|ethiopia|sudan|congo|senegal|morocco|algeria|zimbabwe|tanzania|ghana|sahel)\b"),
    ("latam", "拉美",
     r"拉美|拉丁美洲|巴西|阿根廷|墨西哥|智利|秘鲁|哥伦比亚|委内瑞拉|古巴|卢拉|米莱",
     r"\b(latin america|brazil|brazilian|argentina|mexico|mexican|chile|peru|colombia|venezuela|cuba|lula|milei|bolivia|ecuador)\b"),
    ("oceania", "大洋洲与加拿大",
     r"澳大利亚|澳洲|悉尼|墨尔本|新西兰|加拿大|多伦多|温哥华|卡尼",
     r"\b(australia|australian|sydney|melbourne|new zealand|canada|canadian|toronto|vancouver|ottawa|carney)\b"),
]

TOPICS = [
    ("ai", "人工智能", r"人工智能|AI|大模型|ChatGPT|DeepSeek|智能体|生成式|算法|OpenAI|Gemini|Claude|豆包|通义|文心|Kimi", r"\b(ai|artificial intelligence|chatgpt|openai|chatbots?|llms?|gemini|claude|deepseek|generative|machine learning|anthropic)\b"),
    ("chip", "芯片半导体", r"芯片|半导体|光刻|晶圆|台积电|中芯国际|英伟达|高通|AMD|英特尔|GPU|算力", r"\b(chips?|semiconductors?|tsmc|nvidia|intel|amd|qualcomm|gpus?|asml|wafer|chipmakers?)\b"),
    ("nvidia", "英伟达风波", r"英伟达|黄仁勋", r"\b(nvidia|jensen huang|huang)\b"),
    ("space", "航天探索", r"航天|火箭|发射|卫星|空间站|神舟|天宫|嫦娥|天问|星舰|SpaceX|NASA|探月|火星|载人", r"\b(space|rockets?|launch|satellites?|spacex|starship|nasa|moon|lunar|mars|astronauts?|orbit|iss)\b"),
    ("ev", "新能源", r"新能源|电动车|电动汽车|纯电|电池|锂电|光伏|风电|储能|充电|氢能|碳中和|宁德时代|比亚迪|特斯拉", r"\b(electric vehicles?|evs?|batter(y|ies)|lithium|solar|wind power|renewables?|clean energy|hydrogen|tesla|byd|charging)\b"),
    ("stock", "股市行情", r"股市|A股|港股|美股|大盘|沪指|深成指|创业板|科创板|涨停|跌停|收涨|收跌|ETF|牛市|熊市", r"\b(stocks?|shares|stock market|nasdaq|dow|s&p 500|rally|sell-?off|bull market|bear market|etf)\b"),
    ("macro", "宏观经济", r"宏观|经济增长|GDP|CPI|PPI|通胀|通缩|降息|加息|降准|利率|央行|美联储|货币政策|财政政策|社融|就业数据|非农", r"\b(gdp|inflation|deflation|interest rates?|rate cuts?|rate hikes?|federal reserve|central bank|monetary policy|fiscal|jobs report|unemployment|recession|economy)\b"),
    ("property", "楼市", r"楼市|房价|房地产|商品房|住房|房贷|限购|二手房|新房|房企|保交楼|租房", r"\b(housing|property|real estate|home prices?|mortgages?|developers?|evergrande|country garden)\b"),
    ("trade", "贸易与关税", r"关税|贸易|出口|进口|外贸|贸易战|制裁|出口管制|实体清单|WTO|自贸", r"\b(tariffs?|trade|exports?|imports?|sanctions?|export controls?|entity list|wto|trade war|trade deal)\b"),
    ("diplomacy", "外交", r"外交|会晤|会谈|访问|峰会|APEC|G20|联合国|大使|外长|双边|多边|国事访问|通话", r"\b(diplomac(y|tic)|summit|talks|visit|apec|g20|g7|united nations|ambassador|foreign minister|bilateral|state visit)\b"),
    ("ukraine", "俄乌冲突", r"俄乌|乌克兰|泽连斯基|基辅|顿巴斯|俄军|乌军", r"\b(ukraine|ukrainian|zelensky|zelenskyy|kyiv|donbas)\b"),
    ("gaza", "巴以局势", r"加沙|巴以|哈马斯|以色列|巴勒斯坦|约旦河西岸|内塔尼亚胡", r"\b(gaza|hamas|israel|israeli|palestin(e|ian|ians)|west bank|netanyahu)\b"),
    ("election", "选举政治", r"选举|大选|投票|选民|竞选|候选人|议会选举|总统选举|中期选举|公投|组阁", r"\b(elections?|vote|voters|voting|ballot|campaign|candidates?|polls?|midterms?|referendum|primary)\b"),
    ("climate", "气候环境", r"气候|全球变暖|碳排放|碳中和|减排|环保|污染|生态|COP\d+|极端天气|热浪|冰川", r"\b(climate|global warming|emissions|carbon|net zero|pollution|cop\d+|heatwave|glaciers?|environmental)\b"),
    ("disaster", "灾害事故", r"地震|台风|洪水|暴雨|山火|火灾|爆炸|坍塌|事故|遇难|救援|海啸|泥石流|空难|沉船|停飞", r"\b(earthquakes?|typhoons?|hurricanes?|floods?|wildfires?|fires?|explosions?|collapse|crash(es)?|disasters?|tsunami|landslides?|rescue|ground stop|outage)\b"),
    ("publichealth", "公共卫生", r"疫情|疫苗|流感|新冠|麻疹|传染|病毒|公共卫生|世卫|卫健委|呼吸道", r"\b(outbreak|vaccines?|flu|covid|measles|infectious|virus|public health|pandemic|epidemic)\b"),
    ("football", "足球", r"足球|世界杯|欧冠|英超|西甲|德甲|意甲|法甲|中超|国足|女足|梅西|C罗|球王", r"\b(football|soccer|world cup|premier league|champions league|la liga|serie a|bundesliga|messi|ronaldo|fifa|uefa)\b"),
    ("basketball", "篮球", r"篮球|NBA|CBA|WNBA|男篮|女篮|詹姆斯|库里|约基奇|文班亚马", r"\b(basketball|nba|wnba|lebron|curry|jokic|wembanyama|lakers|celtics|warriors)\b"),
    ("film", "影视", r"电影|影片|票房|电视剧|剧集|综艺|导演|首映|定档|金鸡|奥斯卡|影视|网剧|短剧", r"\b(film|movie|box office|tv series|series|netflix|director|premiere|oscars?|hollywood|trailer)\b"),
    ("games", "游戏", r"游戏|电竞|主机|手游|Switch|PS5|Xbox|Steam|GTA|黑神话|LPL|英雄联盟", r"\b(video games?|gaming|esports|nintendo|switch|playstation|ps5|xbox|steam|gta)\b"),
    ("phone", "手机数码", r"手机|iPhone|安卓|华为|小米|苹果|三星|OPPO|vivo|荣耀|平板|笔记本|耳机|折叠屏|鸿蒙|Pura|Mate", r"\b(iphone|android|smartphones?|phones?|samsung|galaxy|pixel|ipad|laptops?|macbook|headphones|foldable)\b"),
    ("cyber", "网络安全", r"网络安全|黑客|数据泄露|勒索|漏洞|网络攻击|隐私|诈骗", r"\b(cyber|hackers?|hacked|data breach|ransomware|vulnerabilit(y|ies)|cyberattack|privacy|scams?|leak)\b"),
    ("crypto", "加密货币", r"比特币|加密货币|虚拟货币|以太坊|稳定币|区块链|数字货币", r"\b(bitcoin|crypto|cryptocurrenc(y|ies)|ethereum|stablecoins?|blockchain|btc)\b"),
    ("jobs", "就业职场", r"就业|招聘|裁员|求职|失业|职场|薪资|工资|毕业生|岗位|灵活就业", r"\b(jobs|hiring|layoffs?|job cuts|unemployment|workers|wages|salary|workforce|employees)\b"),
    ("gaokao", "考试升学", r"高考|中考|考研|考公|国考|招生|录取|志愿填报|分数线|保研|留学", r"\b(exams?|admissions?|entrance exam|sat|gaokao|university applications?)\b"),
    ("law", "法治", r"法院|判决|起诉|审判|检察|立法|法律|条例|违法|犯罪|刑事|民事|司法", r"\b(court|ruling|judge|trial|lawsuit|sued|legislation|law|illegal|criminal|justice|supreme court)\b"),
    ("transport", "交通出行", r"航班|机场|航空|高铁|铁路|地铁|公路|春运|出行|停飞|空管|航线|C919|大飞机|商飞", r"\b(flights?|airports?|airlines?|aviation|rail|railway|trains?|subway|metro|highway|travel|air traffic|ground stop|faa|boeing|airbus)\b"),
    ("consume", "消费生活", r"消费|零售|电商|双11|双十一|购物|外卖|奶茶|咖啡|餐饮|旅游|酒店|景区|直播带货|潮玩|泡泡玛特", r"\b(consumers?|retail|shopping|e-commerce|black friday|restaurants?|coffee|tourism|hotels?|travel|pop mart|labubu)\b"),
]

# Case-sensitive English tokens that would be ambiguous otherwise.
CASE_SENSITIVE = {
    "geo:us": r"\bU\.S\.(?!\w)|\bUS\b|\bUSA\b",
    "cat:health": r"\bWHO\b",
    "topic:publichealth": r"\bWHO\b",
    "topic:diplomacy": r"\bUN\b",
    "topic:macro": r"\bFed\b",
    "cat:finance": r"\bFed\b",
}
