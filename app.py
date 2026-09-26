from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
import asyncio, json, random, time

app=FastAPI(title='鹹魚翻身測試版')
clients={}
state={'phase':'lobby','question_no':0,'question':None,'deadline':0,'players':{},'spectators':{},'answers':{},'winner':None,'config':{'seconds':20,'min_players':2,'max_players':100,'choices':4}}
BOT_CATALOG=[
 ('阿發哥','男・中年',.84),('美鳳姨','女・熟齡',.66),('小晴','女・青年',.72),('老王','男・熟齡',.48),
 ('Amy','女・青年',.80),('小傑','男・青年',.62),('大雄','男・中年',.54),('玲玲姐','女・中年',.70),
 ('阿凱','男・青年',.76),('秀琴阿姨','女・熟齡',.58),('志明','男・中年',.68),('小美','女・青年',.74),
 ('建國伯','男・長者',.52),('安安','女・青年',.64),('冠宇','男・青年',.78),('淑芬姐','女・中年',.60)]
state['single_mode']=False
state['bots']={}

QUESTIONS=[{'cat': '台灣知識', 'q': '台灣最高的山是哪一座？', 'opts': ['玉山', '雪山', '阿里山', '陽明山'], 'a': 0},
 {'cat': '台灣知識', 'q': '到台南旅遊，最常聽到哪一種小吃名稱？', 'opts': ['牛肉湯', '可麗餅', '熱狗堡', '披薩'], 'a': 0},
 {'cat': '台灣知識', 'q': '台灣便利商店密度很高，下列哪件事通常也能在便利商店完成？', 'opts': ['繳部分帳單', '考汽車駕照', '辦結婚登記', '做牙齒矯正'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「台北101」，應該往哪個地區找？', 'opts': ['台北', '新北', '台中', '台南'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「日月潭」，應該往哪個地區找？', 'opts': ['南投', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「阿里山」，應該往哪個地區找？', 'opts': ['嘉義', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「六合夜市」，應該往哪個地區找？', 'opts': ['高雄', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「安平古堡」，應該往哪個地區找？', 'opts': ['台南', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「太魯閣」，應該往哪個地區找？', 'opts': ['花蓮', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「故宮博物院」，應該往哪個地區找？', 'opts': ['台北', '新北', '台中', '台南'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「鹿港老街」，應該往哪個地區找？', 'opts': ['彰化', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「淡水老街」，應該往哪個地區找？', 'opts': ['新北', '台北', '台中', '台南'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「逢甲夜市」，應該往哪個地區找？', 'opts': ['台中', '台北', '新北', '台南'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「墾丁」，應該往哪個地區找？', 'opts': ['屏東', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「礁溪溫泉」，應該往哪個地區找？', 'opts': ['宜蘭', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「澎湖跨海大橋」，應該往哪個地區找？', 'opts': ['澎湖', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「北投溫泉」，應該往哪個地區找？', 'opts': ['台北', '新北', '台中', '台南'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「九份」，應該往哪個地區找？', 'opts': ['新北', '台北', '台中', '台南'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「赤崁樓」，應該往哪個地區找？', 'opts': ['台南', '台北', '新北', '台中'], 'a': 0},
 {'cat': '台灣知識', 'q': '想去「駁二藝術特區」，應該往哪個地區找？', 'opts': ['高雄', '台北', '新北', '台中'], 'a': 0},
 {'cat': '世界知識', 'q': '法國的首都是哪一座城市？', 'opts': ['巴黎', '里昂', '馬賽', '尼斯'], 'a': 0},
 {'cat': '世界知識', 'q': '如果朋友說他去看自由女神像，他最可能去了哪個城市？', 'opts': ['紐約', '曼谷', '雪梨', '首爾'], 'a': 0},
 {'cat': '世界知識', 'q': '哪個國家的國土外形常被形容像一隻長靴？', 'opts': ['義大利', '日本', '巴西', '冰島'], 'a': 0},
 {'cat': '世界知識', 'q': '日本的首都是哪裡？', 'opts': ['東京', '首爾', '曼谷', '巴黎'], 'a': 0},
 {'cat': '世界知識', 'q': '韓國的首都是哪裡？', 'opts': ['首爾', '東京', '曼谷', '巴黎'], 'a': 0},
 {'cat': '世界知識', 'q': '泰國的首都是哪裡？', 'opts': ['曼谷', '東京', '首爾', '巴黎'], 'a': 0},
 {'cat': '世界知識', 'q': '法國的首都是哪裡？', 'opts': ['巴黎', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '英國的首都是哪裡？', 'opts': ['倫敦', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '義大利的首都是哪裡？', 'opts': ['羅馬', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '西班牙的首都是哪裡？', 'opts': ['馬德里', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '德國的首都是哪裡？', 'opts': ['柏林', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '澳洲的首都是哪裡？', 'opts': ['坎培拉', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '加拿大的首都是哪裡？', 'opts': ['渥太華', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '美國的首都是哪裡？', 'opts': ['華盛頓特區', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '埃及的首都是哪裡？', 'opts': ['開羅', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '印度的首都是哪裡？', 'opts': ['新德里', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '越南的首都是哪裡？', 'opts': ['河內', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '菲律賓的首都是哪裡？', 'opts': ['馬尼拉', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '印尼的首都是哪裡？', 'opts': ['雅加達', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '世界知識', 'q': '紐西蘭的首都是哪裡？', 'opts': ['威靈頓', '東京', '首爾', '曼谷'], 'a': 0},
 {'cat': '生活常識', 'q': '一般情況下，水在攝氏幾度沸騰？', 'opts': ['50度', '80度', '100度', '120度'], 'a': 2},
 {'cat': '生活常識', 'q': '手機掉進水裡後，第一時間最不建議做什麼？', 'opts': ['立刻插電充電', '先關機', '擦乾外部水分', '取下保護殼'], 'a': 0},
 {'cat': '生活常識', 'q': '夏天車子停在大太陽下，哪個地方通常最燙？', 'opts': ['車內密閉空間', '冰箱裡', '地下室', '冷氣出風口'], 'a': 0},
 {'cat': '生活常識', 'q': '手機只剩1%電量，最直接該做什麼？', 'opts': ['充電', '泡水', '冷凍', '敲打'], 'a': 0},
 {'cat': '生活常識', 'q': '過馬路看到紅燈通常應該？', 'opts': ['停下等待', '加速衝過', '閉眼走', '倒退走'], 'a': 0},
 {'cat': '生活常識', 'q': '食物明顯腐敗時較安全做法？', 'opts': ['不要吃', '加糖吃', '只吃一半', '曬一下再吃'], 'a': 0},
 {'cat': '生活常識', 'q': '陌生連結要求輸入銀行密碼？', 'opts': ['不要亂點', '立刻輸入', '公開密碼', '轉傳所有人'], 'a': 0},
 {'cat': '生活常識', 'q': '雨天騎車最需注意？', 'opts': ['路面濕滑', '太陽太大', '沙漠缺水', '雪崩'], 'a': 0},
 {'cat': '生活常識', 'q': '夏天戶外活動應注意？', 'opts': ['補水防曬', '穿羽絨衣', '完全不喝水', '待密閉車內'], 'a': 0},
 {'cat': '生活常識', 'q': '重要檔案較好的習慣？', 'opts': ['定期備份', '只存一份', '每天刪除', '從不命名'], 'a': 0},
 {'cat': '生活常識', 'q': '搭車繫安全帶主要為了？', 'opts': ['降低事故傷害', '讓車更快', '省油一半', '音樂更大'], 'a': 0},
 {'cat': '生活常識', 'q': '插座冒煙最不適合？', 'opts': ['徒手碰觸', '切斷電源', '保持距離', '尋求協助'], 'a': 0},
 {'cat': '生活常識', 'q': '聞到濃厚瓦斯味應避免？', 'opts': ['點火', '開窗', '關瓦斯', '離開'], 'a': 0},
 {'cat': '生活常識', 'q': '切菜最重要？', 'opts': ['注意手指安全', '閉眼切', '邊跑邊切', '把刀往上拋'], 'a': 0},
 {'cat': '生活常識', 'q': '睡前大量喝咖啡最可能影響？', 'opts': ['睡眠', '鞋號', '血型', '身高'], 'a': 0},
 {'cat': '生活常識', 'q': '冰箱冷藏主要為了？', 'opts': ['減慢食物變質', '讓食物變甜', '變大', '變輕'], 'a': 0},
 {'cat': '生活常識', 'q': '油鍋起火最不應倒入？', 'opts': ['水', '鍋蓋', '滅火毯', '合適滅火器'], 'a': 0},
 {'cat': '生活常識', 'q': '火災時一般較建議走？', 'opts': ['安全梯', '電梯', '貨梯', '輸送帶'], 'a': 0},
 {'cat': '生活常識', 'q': '有效日期主要提醒？', 'opts': ['保存食用期限', '店員生日', '商品顏色', '字體大小'], 'a': 0},
 {'cat': '生活常識', 'q': '公共場所播放音樂較好的做法？', 'opts': ['戴耳機控制音量', '開最大聲', '逼別人聽', '堵出口'], 'a': 0},
 {'cat': '自然科學', 'q': '植物行光合作用主要吸收哪一種氣體？', 'opts': ['氧氣', '二氧化碳', '氮氣', '氫氣'], 'a': 1},
 {'cat': '自然科學', 'q': '我們呼吸時，身體最需要空氣中的哪種氣體？', 'opts': ['氧氣', '二氧化碳', '氦氣', '甲烷'], 'a': 0},
 {'cat': '自然科學', 'q': '月亮本身會不會像太陽一樣發出可見光？', 'opts': ['不會，主要反射陽光', '會，自己像燈泡', '只有下雨才會', '只有滿月會'], 'a': 0},
 {'cat': '自然科學', 'q': '地球繞哪顆星運行？', 'opts': ['太陽', '月亮', '火星', '北極星'], 'a': 0},
 {'cat': '自然科學', 'q': '人主要用哪個器官呼吸？', 'opts': ['肺', '胃', '腎臟', '骨頭'], 'a': 0},
 {'cat': '自然科學', 'q': '冰塊融化後變？', 'opts': ['水', '石頭', '木頭', '沙子'], 'a': 0},
 {'cat': '自然科學', 'q': '閃電後常聽到？', 'opts': ['雷聲', '鳥叫', '汽笛', '鐘聲'], 'a': 0},
 {'cat': '自然科學', 'q': '磁鐵容易吸住？', 'opts': ['鐵釘', '木筷', '塑膠杯', '紙巾'], 'a': 0},
 {'cat': '自然科學', 'q': '太陽從哪邊升起？', 'opts': ['東方', '西方', '北方', '南方'], 'a': 0},
 {'cat': '自然科學', 'q': '彩虹通常需要陽光和？', 'opts': ['水滴', '沙子', '木頭', '鐵片'], 'a': 0},
 {'cat': '自然科學', 'q': '流汗作用之一？', 'opts': ['幫助散熱', '改髮色', '增加身高', '讓骨頭變硬'], 'a': 0},
 {'cat': '自然科學', 'q': '地球表面大部分是？', 'opts': ['水', '沙漠', '城市', '冰塊'], 'a': 0},
 {'cat': '自然科學', 'q': '月球是地球的？', 'opts': ['天然衛星', '恆星', '太陽', '彗星'], 'a': 0},
 {'cat': '自然科學', 'q': '植物根主要吸收？', 'opts': ['水分和礦物質', '陽光', '聲音', '塑膠'], 'a': 0},
 {'cat': '自然科學', 'q': '心臟主要工作？', 'opts': ['幫浦血液', '消化食物', '製造聲音', '儲存空氣'], 'a': 0},
 {'cat': '自然科學', 'q': '我們住在哪顆行星？', 'opts': ['地球', '木星', '金星', '水星'], 'a': 0},
 {'cat': '自然科學', 'q': '熱空氣通常會？', 'opts': ['上升', '變石頭', '完全不動', '變成冰'], 'a': 0},
 {'cat': '自然科學', 'q': '葉片常呈綠色與？', 'opts': ['葉綠素', '血紅素', '黑色素', '藍色素'], 'a': 0},
 {'cat': '自然科學', 'q': '水蒸氣是水的？', 'opts': ['氣態', '固態', '金屬態', '木質態'], 'a': 0},
 {'cat': '自然科學', 'q': '聲音在真空中能正常傳播嗎？', 'opts': ['不能', '可以更快', '只有晚上', '只有下雨'], 'a': 0},
 {'cat': '歷史文化', 'q': '古埃及文明最著名的大型陵墓建築是？', 'opts': ['金字塔', '萬里長城', '競技場', '神社'], 'a': 0},
 {'cat': '歷史文化', 'q': '「萬里長城」最容易讓人聯想到哪個國家？', 'opts': ['中國', '埃及', '法國', '澳洲'], 'a': 0},
 {'cat': '歷史文化', 'q': '農曆春節最常見的紅色小紙袋，通常叫什麼？', 'opts': ['紅包', '護照', '發票', '菜單'], 'a': 0},
 {'cat': '歷史文化', 'q': '端午節常紀念？', 'opts': ['屈原', '孔子', '李白', '鄭成功'], 'a': 0},
 {'cat': '歷史文化', 'q': '古代遠距傳消息常靠？', 'opts': ['信件', '視訊', '社群軟體', '電子郵件'], 'a': 0},
 {'cat': '歷史文化', 'q': '文藝復興常與哪地區相關？', 'opts': ['歐洲', '南極洲', '月球', '太平洋'], 'a': 0},
 {'cat': '歷史文化', 'q': '古羅馬競技場位於今天？', 'opts': ['義大利', '日本', '加拿大', '印度'], 'a': 0},
 {'cat': '歷史文化', 'q': '故宮博物院收藏大量？', 'opts': ['歷史文物', '汽車零件', '活體鯨魚', '火箭'], 'a': 0},
 {'cat': '歷史文化', 'q': '古代皇帝正式命令常稱？', 'opts': ['聖旨', '菜單', '收據', '車票'], 'a': 0},
 {'cat': '歷史文化', 'q': '絲路主要促進？', 'opts': ['東西方交流', '海底採礦', '太空旅行', '網購'], 'a': 0},
 {'cat': '歷史文化', 'q': '元宵節常見？', 'opts': ['賞花燈', '吃粽子', '划龍舟', '烤火雞'], 'a': 0},
 {'cat': '歷史文化', 'q': '指南針主要幫助？', 'opts': ['辨別方向', '煮飯', '量體溫', '聽音樂'], 'a': 0},
 {'cat': '歷史文化', 'q': '萬里長城重要用途之一？', 'opts': ['防禦', '游泳', '種稻', '停飛機'], 'a': 0},
 {'cat': '歷史文化', 'q': '古代奧運起源？', 'opts': ['希臘', '巴西', '日本', '澳洲'], 'a': 0},
 {'cat': '歷史文化', 'q': '傳統書法主要工具？', 'opts': ['毛筆', '螺絲起子', '湯匙', '吸管'], 'a': 0},
 {'cat': '歷史文化', 'q': '歷史博物館主要了解？', 'opts': ['過去的人事物', '明天天氣', '即時股價', '手機電量'], 'a': 0},
 {'cat': '歷史文化', 'q': '紙張普及前曾寫在？', 'opts': ['竹簡', '手機螢幕', '塑膠袋', '鋁罐'], 'a': 0},
 {'cat': '歷史文化', 'q': '農曆十五月亮通常較？', 'opts': ['圓', '方形', '三角形', '完全消失'], 'a': 0},
 {'cat': '歷史文化', 'q': '鄭成功在台灣史常與？', 'opts': ['明鄭時期', '恐龍時代', '未來時代', '冰河時代'], 'a': 0},
 {'cat': '歷史文化', 'q': '古代毛筆寫字常搭配？', 'opts': ['墨', '汽油', '牙膏', '洗髮精'], 'a': 0},
 {'cat': '財經知識', 'q': '把錢存在銀行通常可能獲得什麼？', 'opts': ['利息', '罰金', '租金', '關稅'], 'a': 0},
 {'cat': '財經知識', 'q': '看到商品標示「第二件半價」，買兩件時哪一件通常打五折？', 'opts': ['第二件', '第一件', '兩件都免費', '兩件都原價'], 'a': 0},
 {'cat': '財經知識', 'q': '刷卡消費後，如果沒有按時繳清帳單，最可能產生什麼？', 'opts': ['利息或費用', '免費贈品', '薪水', '退稅'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價100元，現折10元，應付多少？', 'opts': ['90元', '110元', '10元', '100元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價200元，現折20元，應付多少？', 'opts': ['180元', '220元', '20元', '200元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價300元，現折50元，應付多少？', 'opts': ['250元', '350元', '50元', '300元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價500元，現折100元，應付多少？', 'opts': ['400元', '600元', '100元', '500元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價80元，現折10元，應付多少？', 'opts': ['70元', '90元', '10元', '80元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價120元，現折20元，應付多少？', 'opts': ['100元', '140元', '20元', '120元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價250元，現折50元，應付多少？', 'opts': ['200元', '300元', '50元', '250元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價1000元，現折200元，應付多少？', 'opts': ['800元', '1200元', '200元', '1000元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價60元，現折5元，應付多少？', 'opts': ['55元', '65元', '5元', '60元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價150元，現折30元，應付多少？', 'opts': ['120元', '180元', '30元', '150元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價400元，現折80元，應付多少？', 'opts': ['320元', '480元', '80元', '400元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價90元，現折10元，應付多少？', 'opts': ['80元', '100元', '10元', '90元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價600元，現折100元，應付多少？', 'opts': ['500元', '700元', '100元', '600元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價700元，現折150元，應付多少？', 'opts': ['550元', '850元', '150元', '700元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價50元，現折5元，應付多少？', 'opts': ['45元', '55元', '5元', '50元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價350元，現折70元，應付多少？', 'opts': ['280元', '420元', '70元', '350元'], 'a': 0},
 {'cat': '財經知識', 'q': '商品原價900元，現折100元，應付多少？', 'opts': ['800元', '1000元', '100元', '900元'], 'a': 0},
 {'cat': '影視娛樂', 'q': '電影通常由誰負責統籌演員表演與鏡頭敘事？', 'opts': ['導演', '觀眾', '售票員', '司機'], 'a': 0},
 {'cat': '影視娛樂', 'q': '演員忘詞時，最可能影響的是哪一件事？', 'opts': ['台詞演出', '電影院椅子', '售票機', '停車場'], 'a': 0},
 {'cat': '影視娛樂', 'q': '一部電影正式上映前常用來吸引觀眾的短影片叫什麼？', 'opts': ['預告片', '收據', '說明書', '畢業照'], 'a': 0},
 {'cat': '影視娛樂', 'q': '電影上映前吸引觀眾的短片叫？', 'opts': ['預告片', '收據', '說明書', '畢業照'], 'a': 0},
 {'cat': '影視娛樂', 'q': '演員忘詞最直接影響？', 'opts': ['台詞演出', '座椅', '售票機', '停車場'], 'a': 0},
 {'cat': '影視娛樂', 'q': '卡拉OK主要讓人？', 'opts': ['唱歌', '游泳', '煮飯', '修車'], 'a': 0},
 {'cat': '影視娛樂', 'q': '主持人主要工作之一？', 'opts': ['帶動節目流程', '修水管', '開公車', '蓋房子'], 'a': 0},
 {'cat': '影視娛樂', 'q': '字幕主要幫助？', 'opts': ['閱讀對白或翻譯', '量體溫', '付款', '導航'], 'a': 0},
 {'cat': '影視娛樂', 'q': '演唱會主要表演？', 'opts': ['音樂演出', '考駕照', '洗車', '煮飯'], 'a': 0},
 {'cat': '影視娛樂', 'q': '喜劇常希望觀眾？', 'opts': ['發笑', '考試', '修手機', '學游泳'], 'a': 0},
 {'cat': '影視娛樂', 'q': '恐怖片常用什麼營造緊張？', 'opts': ['音效與畫面', '菜單價格', '停車格', '收據'], 'a': 0},
 {'cat': '影視娛樂', 'q': '配音員主要做？', 'opts': ['為角色提供聲音', '賣爆米花', '修攝影機', '掃地'], 'a': 0},
 {'cat': '影視娛樂', 'q': '導演喊「卡」通常代表？', 'opts': ['暫停拍攝', '開始吃飯', '開門', '買票'], 'a': 0},
 {'cat': '影視娛樂', 'q': '電影海報主要用途？', 'opts': ['宣傳作品', '繳稅', '量血壓', '導航'], 'a': 0},
 {'cat': '影視娛樂', 'q': '電視遙控器主要用來？', 'opts': ['控制電視', '煮飯', '洗衣', '充輪胎'], 'a': 0},
 {'cat': '影視娛樂', 'q': '直播節目特色之一？', 'opts': ['即時播出', '一定黑白', '沒有聲音', '只能紙本'], 'a': 0},
 {'cat': '影視娛樂', 'q': '電影統籌演出與鏡頭敘事？', 'opts': ['導演', '觀眾', '售票員', '司機'], 'a': 0},
 {'cat': '影視娛樂', 'q': '動畫角色動起來主要靠？', 'opts': ['連續畫面', '一張收據', '一個電話', '一張車票'], 'a': 0},
 {'cat': '影視娛樂', 'q': '歌手上台前常會做？', 'opts': ['彩排', '考駕照', '修水管', '種稻'], 'a': 0},
 {'cat': '影視娛樂', 'q': '麥克風主要用來？', 'opts': ['收錄或放大聲音', '量體重', '煮飯', '導航'], 'a': 0},
 {'cat': '動物植物', 'q': '下列哪一種是哺乳動物？', 'opts': ['海豚', '鯊魚', '章魚', '企鵝'], 'a': 0},
 {'cat': '動物植物', 'q': '狗狗高興時最常見的肢體動作之一是什麼？', 'opts': ['搖尾巴', '長出翅膀', '變成綠色', '開始下蛋'], 'a': 0},
 {'cat': '動物植物', 'q': '仙人掌能適應乾燥環境，常見特徵是什麼？', 'opts': ['能儲存水分', '每天要泡水', '沒有細胞', '只能活一天'], 'a': 0},
 {'cat': '動物植物', 'q': '貓通常有幾隻腳？', 'opts': ['4隻', '2隻', '6隻', '8隻'], 'a': 0},
 {'cat': '動物植物', 'q': '企鵝很擅長？', 'opts': ['游泳', '飛很高', '爬樹', '挖地鐵'], 'a': 0},
 {'cat': '動物植物', 'q': '長頸鹿特徵？', 'opts': ['脖子很長', '沒有腳', '有魚鰭', '會發光'], 'a': 0},
 {'cat': '動物植物', 'q': '蜜蜂常採集？', 'opts': ['花蜜', '汽油', '沙子', '鹽巴'], 'a': 0},
 {'cat': '動物植物', 'q': '魚主要用？', 'opts': ['鰓呼吸', '翅膀', '樹根', '耳朵'], 'a': 0},
 {'cat': '動物植物', 'q': '鳥身上通常有？', 'opts': ['羽毛', '魚鱗', '樹皮', '玻璃'], 'a': 0},
 {'cat': '動物植物', 'q': '熊貓常吃？', 'opts': ['竹子', '披薩', '冰塊', '辣椒醬'], 'a': 0},
 {'cat': '動物植物', 'q': '蝴蝶幼蟲常叫？', 'opts': ['毛毛蟲', '小魚', '蝌蚪', '蚯蚓'], 'a': 0},
 {'cat': '動物植物', 'q': '樹木年輪可估計？', 'opts': ['年齡', '血型', '速度', '音量'], 'a': 0},
 {'cat': '動物植物', 'q': '海豚屬於？', 'opts': ['哺乳動物', '魚類', '昆蟲', '植物'], 'a': 0},
 {'cat': '動物植物', 'q': '青蛙小時候叫？', 'opts': ['蝌蚪', '毛毛蟲', '小雞', '幼苗'], 'a': 0},
 {'cat': '動物植物', 'q': '雞蛋通常由？', 'opts': ['母雞', '公雞', '魚', '蝴蝶'], 'a': 0},
 {'cat': '動物植物', 'q': '章魚有幾隻腕足？', 'opts': ['8隻', '2隻', '4隻', '12隻'], 'a': 0},
 {'cat': '動物植物', 'q': '駱駝常適應？', 'opts': ['乾燥沙漠', '深海', '南極冰原', '高空'], 'a': 0},
 {'cat': '動物植物', 'q': '松鼠常讓人聯想到收藏？', 'opts': ['堅果', '汽油', '螺絲', '冰塊'], 'a': 0},
 {'cat': '動物植物', 'q': '向日葵名稱常聯想到？', 'opts': ['太陽', '月亮', '海底', '雪地'], 'a': 0},
 {'cat': '動物植物', 'q': '狗的嗅覺通常比人？', 'opts': ['靈敏', '完全沒有', '一樣差', '只能聞甜味'], 'a': 0},
 {'cat': '邏輯推理', 'q': '2、4、8、16，下一個數字是？', 'opts': ['18', '24', '32', '64'], 'a': 2},
 {'cat': '邏輯推理', 'q': '桌上有5顆蘋果，拿走2顆，桌上還剩幾顆？', 'opts': ['3顆', '2顆', '5顆', '7顆'], 'a': 0},
 {'cat': '邏輯推理', 'q': '如果今天是星期一，三天後是星期幾？', 'opts': ['星期四', '星期二', '星期三', '星期日'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有2顆糖，又拿到2顆，現在共有幾顆？', 'opts': ['4', '5', '3', '4'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有3顆糖，又拿到3顆，現在共有幾顆？', 'opts': ['6', '7', '5', '9'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有5顆糖，又拿到5顆，現在共有幾顆？', 'opts': ['10', '11', '9', '25'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有10顆糖，又拿到5顆，現在共有幾顆？', 'opts': ['15', '16', '14', '50'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有4顆糖，又拿到4顆，現在共有幾顆？', 'opts': ['8', '9', '7', '16'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有6顆糖，又拿到2顆，現在共有幾顆？', 'opts': ['8', '9', '7', '12'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有7顆糖，又拿到3顆，現在共有幾顆？', 'opts': ['10', '11', '9', '21'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有8顆糖，又拿到4顆，現在共有幾顆？', 'opts': ['12', '13', '11', '32'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有9顆糖，又拿到1顆，現在共有幾顆？', 'opts': ['10', '11', '9', '9'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有12顆糖，又拿到3顆，現在共有幾顆？', 'opts': ['15', '16', '14', '36'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有15顆糖，又拿到5顆，現在共有幾顆？', 'opts': ['20', '21', '19', '75'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有20顆糖，又拿到10顆，現在共有幾顆？', 'opts': ['30', '31', '29', '200'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有11顆糖，又拿到2顆，現在共有幾顆？', 'opts': ['13', '14', '12', '22'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有13顆糖，又拿到4顆，現在共有幾顆？', 'opts': ['17', '18', '16', '52'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有16顆糖，又拿到8顆，現在共有幾顆？', 'opts': ['24', '25', '23', '128'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有25顆糖，又拿到5顆，現在共有幾顆？', 'opts': ['30', '31', '29', '125'], 'a': 0},
 {'cat': '邏輯推理', 'q': '小明有30顆糖，又拿到10顆，現在共有幾顆？', 'opts': ['40', '41', '39', '300'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西明明是你的，別人卻比你更常叫它？', 'opts': ['名字', '手機', '鞋子', '錢包'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼布永遠剪不斷？', 'opts': ['瀑布', '棉布', '麻布', '抹布'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西越洗越髒？', 'opts': ['水', '衣服', '毛巾', '盤子'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西明明是你的，別人卻更常叫？', 'opts': ['名字', '手機', '鞋子', '錢包'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '哪種門永遠關不上？', 'opts': ['球門', '鐵門', '木門', '車門'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西很多牙齒卻不咬人？', 'opts': ['梳子', '老虎', '鯊魚', '狗'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西有腳卻不會走？', 'opts': ['桌子', '小狗', '人', '螞蟻'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西有頭有尾卻沒身體？', 'opts': ['硬幣', '小貓', '魚', '蛇'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '哪種魚不能在水裡游？', 'opts': ['木魚', '鯉魚', '鯊魚', '金魚'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西打破了大家反而高興？', 'opts': ['紀錄', '玻璃杯', '手機', '窗戶'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西不用嘴也能回答你？', 'opts': ['回音', '椅子', '襪子', '雨傘'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西有眼睛卻看不見？', 'opts': ['針', '貓', '老鷹', '人'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西有耳朵卻聽不見？', 'opts': ['茶壺', '兔子', '狗', '人'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西越吹越大？', 'opts': ['氣球', '石頭', '鉛筆', '硬幣'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西越擦越小？', 'opts': ['橡皮擦', '桌子', '電視', '冰箱'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西越冷越愛跑出來？', 'opts': ['鼻水', '汗水', '熱水', '汽水'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '哪種蛋不能吃？', 'opts': ['笨蛋', '雞蛋', '鴨蛋', '茶葉蛋'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '什麼東西沒有生命卻會「跑」？', 'opts': ['時鐘', '石頭', '枕頭', '杯子'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '腦筋急轉彎趣味暖身題19：1加1等於多少？', 'opts': ['2', '1', '3', '4'], 'a': 0},
 {'cat': '腦筋急轉彎', 'q': '腦筋急轉彎趣味暖身題20：1加1等於多少？', 'opts': ['2', '1', '3', '4'], 'a': 0}]
used=[]

async def broadcast(msg, role=None):
    dead=[]
    for ws,meta in list(clients.items()):
        if role and meta['role']!=role: continue
        try: await ws.send_text(json.dumps(msg,ensure_ascii=False))
        except: dead.append(ws)
    for ws in dead: clients.pop(ws,None)

def public_state():
    return {'type':'state','phase':state['phase'],'question_no':state['question_no'],'question':state['question'],'deadline':state['deadline'],'player_count':len(state['players']),'spectator_count':len(state['spectators']),'winner':state['winner'],'config':state['config']}

@app.get('/')
async def home(): return HTMLResponse(HTML)
@app.get('/manifest.webmanifest')
async def manifest():
    return Response(json.dumps({"name":"鹹魚翻身・益智猜謎大挑戰","short_name":"鹹魚翻身","start_url":"/","display":"standalone","background_color":"#08152d","theme_color":"#6b3cff","icons":[{"src":"/icon.svg","sizes":"any","type":"image/svg+xml","purpose":"any maskable"}]},ensure_ascii=False),media_type='application/manifest+json')

@app.get('/sw.js')
async def sw():
    return Response("self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(clients.claim()));self.addEventListener('fetch',e=>{});",media_type='application/javascript')

@app.get('/icon.svg')
async def icon():
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="110" fill="#6b3cff"/><text x="256" y="305" text-anchor="middle" font-size="260">🐟</text><text x="256" y="455" text-anchor="middle" font-size="64" font-weight="900" fill="white">翻身</text></svg>'
    return Response(svg,media_type='image/svg+xml')


@app.websocket('/ws')
async def ws_endpoint(ws:WebSocket):
    await ws.accept(); meta={'name':'訪客','role':'spectator'}; clients[ws]=meta
    await ws.send_text(json.dumps(public_state(),ensure_ascii=False))
    try:
        while True:
            d=json.loads(await ws.receive_text()); typ=d.get('type')
            if typ=='join':
                name=(d.get('name') or '匿名')[:16]; role=d.get('role','spectator')
                if state['phase']!='lobby' and role=='player': role='spectator'
                if role=='player' and len(state['players'])>=state['config']['max_players']: role='spectator'
                meta.update(name=name,role=role); pid=str(id(ws)); meta['pid']=pid
                (state['players'] if role=='player' else state['spectators'])[pid]={'name':name,'alive':role=='player','correct':0,'answered':0}
                await broadcast(public_state())
                await ws.send_text(json.dumps({'type':'joined','role':role,'pid':pid},ensure_ascii=False))
            elif typ=='single_start' and meta.get('pid'):
                pid=meta['pid']
                if state['phase']!='lobby':
                    await ws.send_text(json.dumps({'type':'error','text':'目前已有比賽進行中'},ensure_ascii=False)); continue
                total=max(4,min(16,int(d.get('total',8))))
                if total not in (4,8,12,16): total=8
                human=state['players'].get(pid) or state['spectators'].get(pid) or {'name':meta.get('name','玩家'),'alive':True,'correct':0,'answered':0}
                state['players']={pid:{**human,'alive':True}}; state['spectators']={}; state['bots']={}; state['single_mode']=True
                meta['role']='player'
                for i,(name,look,skill) in enumerate(random.sample(BOT_CATALOG,total-1),1):
                    bid=f'bot-{i}-{random.randint(1000,9999)}'
                    state['players'][bid]={'name':name,'alive':True,'correct':0,'answered':0,'bot':True,'look':look,'skill':max(.35,min(.92,skill+random.uniform(-.07,.07)))}
                    state['bots'][bid]=True
                state['config']['min_players']=2; state['config']['max_players']=16
                await ws.send_text(json.dumps({'type':'joined','role':'player','pid':pid},ensure_ascii=False))
                await broadcast(public_state())
                asyncio.create_task(run_game(state['config']['seconds']))
            elif typ=='answer' and meta.get('pid'):
                pid=meta['pid']; idx=int(d.get('idx',-1))
                if state['phase']=='question' and time.time()<state['deadline']:
                    state['answers'][pid]=idx
                    rec=state['players'].get(pid) or state['spectators'].get(pid)
                    if rec: rec['answered']+=1
            elif typ=='admin_config' and d.get('admin')=='fishboss' and state['phase']=='lobby':
                state['config']['seconds']=max(5,min(120,int(d.get('seconds',20))))
                state['config']['min_players']=max(1,min(100,int(d.get('min_players',2))))
                state['config']['max_players']=max(state['config']['min_players'],min(100,int(d.get('max_players',100))))
                state['config']['choices']=3 if int(d.get('choices',4))==3 else 4
                await broadcast(public_state())
            elif typ=='start' and d.get('admin')=='fishboss':
                state['config']['seconds']=max(5,min(120,int(d.get('seconds',20)))); asyncio.create_task(run_game(state['config']['seconds']))
            elif typ=='giveup' and meta.get('pid') in state['players']:
                pid=meta['pid']; rec=state['players'].pop(pid); rec['alive']=False; state['spectators'][pid]=rec; meta['role']='spectator'; await ws.send_text(json.dumps({'type':'role_changed','role':'spectator','reason':'giveup'},ensure_ascii=False)); await broadcast(public_state())
    except WebSocketDisconnect:
        clients.pop(ws,None)

async def run_game(seconds=20):
    if state['phase']!='lobby': return
    if len(state['players']) < state['config']['min_players']:
        await broadcast({'type':'cancelled','text':'未達最低參加人數，本場取消'})
        return
    state['phase']='question'; state['winner']=None
    while len(state['players'])>1:
        available=[i for i in range(len(QUESTIONS)) if i not in used]
        if not available: used.clear(); available=list(range(len(QUESTIONS)))
        qi=random.choice(available); used.append(qi); q=QUESTIONS[qi]
        correct_text=q['opts'][q['a']]; wrong=[x for i,x in enumerate(q['opts']) if i!=q['a']]
        shown=[correct_text]+random.sample(wrong,state['config']['choices']-1); random.shuffle(shown); correct_idx=shown.index(correct_text)
        state['question_no']+=1; state['answers']={}; state['deadline']=time.time()+seconds
        state['question']={'cat':q['cat'],'q':q['q'],'opts':shown}
        await broadcast(public_state())
        # Computer contestants answer with local probability logic; no AI/API cost.
        if state.get('single_mode'):
            difficulty=random.uniform(-.06,.06)
            for bid,rec in list(state['players'].items()):
                if not rec.get('bot'): continue
                chance=max(.25,min(.95,rec.get('skill',.6)-difficulty))
                if random.random()<chance: state['answers'][bid]=correct_idx
                else: state['answers'][bid]=random.choice([i for i in range(len(shown)) if i!=correct_idx])
                rec['answered']+=1
        await asyncio.sleep(seconds)
        # score spectators
        for pid,rec in list(state['spectators'].items()):
            if pid in state['answers'] and state['answers'][pid]==correct_idx: rec['correct']+=1
        # eliminate wrong/no-answer players
        eliminated=[]
        for pid,rec in list(state['players'].items()):
            ans=state['answers'].get(pid,None); rec['answered']+=0
            if ans==correct_idx: rec['correct']+=1
            else: eliminated.append(pid)
        # if everyone would be eliminated, nobody is eliminated; continue to avoid zero-winner tie
        if len(eliminated)==len(state['players']) and len(state['players'])>1:
            await broadcast({'type':'round','result':'all_wrong','correct':correct_idx})
        else:
            for pid in eliminated:
                rec=state['players'].pop(pid); rec['alive']=False; state['spectators'][pid]=rec
                for w,m in clients.items():
                    if m.get('pid')==pid:
                        m['role']='spectator'
                        try: await w.send_text(json.dumps({'type':'role_changed','role':'spectator','reason':'eliminated'},ensure_ascii=False))
                        except: pass
            await broadcast({'type':'round','result':'resolved','correct':correct_idx,'eliminated':eliminated})
        await asyncio.sleep(2)
    if len(state['players'])==1:
        pid,rec=next(iter(state['players'].items())); state['winner']=rec['name']
    else: state['winner']='本場無冠軍'
    state['phase']='finished'; state['question']=None; state['deadline']=0
    await broadcast(public_state())

HTML=r'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#6b3cff"><link rel="manifest" href="/manifest.webmanifest"><link rel="icon" href="/icon.svg"><title>鹹魚翻身 測試版</title><style>
body{font-family:system-ui;background:linear-gradient(160deg,#08152d,#1a0d35);color:#fff;margin:0;min-height:100vh}.wrap{max-width:520px;margin:auto;padding:18px}.card{background:#ffffff12;border:1px solid #ffffff28;border-radius:22px;padding:18px;margin:12px 0;backdrop-filter:blur(8px)}h1{color:#ffd45b;text-align:center;margin:8px 0}button,input{font-size:18px;border-radius:14px;padding:14px;border:0}input{width:calc(100% - 28px);margin:8px 0}.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.btn{background:#2d6cdf;color:#fff;font-weight:700}.watch{background:#7042c1}.opt{width:100%;margin:6px 0;text-align:left;background:#17345f;color:#fff}.danger{background:#a33}.big{font-size:46px;font-weight:900;text-align:center;color:#ffd45b}.muted{opacity:.75}.good{background:#175c39}.bad{background:#7c2634}.hide{display:none}.stats{display:flex;justify-content:space-between;font-weight:700}.tag{display:inline-block;background:#ffffff1c;padding:5px 9px;border-radius:99px}.winner{text-align:center;font-size:28px}.fish{font-size:64px;text-align:center}
/* 3D EXPERIENCE V2 */
body{background:radial-gradient(circle at 50% -10%,#5430a8 0,#10234d 28%,#061126 60%,#020713 100%);overflow-x:hidden}.wrap{position:relative}.card{background:linear-gradient(145deg,#17284ce8,#0b1734ed);border-color:#9ccaff55;box-shadow:0 18px 42px #0008,inset 0 1px #ffffff35,inset 0 -2px #0008}.fish{filter:drop-shadow(0 10px 10px #0009) drop-shadow(0 0 18px #ffd75a88);animation:float3d 3s ease-in-out infinite}h1{font-size:40px;background:linear-gradient(#fff6ba,#ffcf48 45%,#c77912 80%,#fff1a2);-webkit-background-clip:text;color:transparent;text-shadow:0 5px 18px #0009}.opt{background:linear-gradient(145deg,#173f72,#0b254a);border:1px solid #72bfff55;box-shadow:inset 0 1px #ffffff44,0 8px 18px #0005;transition:.18s}.opt:active{transform:scale(.975)}.opt.chosen{outline:3px solid #ffd45b;box-shadow:0 0 26px #ffd45b88}.big{background:radial-gradient(circle,#1ca8ff,#063267 67%);width:72px;height:72px;line-height:72px;border-radius:50%;margin:8px auto;border:4px solid #7ce7ff;box-shadow:0 0 24px #18b9ff}.stagefx{position:fixed;inset:0;pointer-events:none;z-index:-1;overflow:hidden}.stagefx:after{content:"";position:absolute;left:-25%;right:-25%;bottom:-20%;height:60%;background:repeating-linear-gradient(90deg,#5ec9ff16 0 2px,transparent 2px 64px),repeating-linear-gradient(0deg,#5ec9ff12 0 2px,transparent 2px 48px);transform:perspective(420px) rotateX(62deg);transform-origin:bottom}.overlay{position:fixed;inset:0;z-index:50;display:none;align-items:center;justify-content:center;text-align:center;background:radial-gradient(circle,#35216de8,#020713f7);padding:22px}.overlay.show{display:flex;animation:fade3d .25s}.ovmain{font-size:46px;font-weight:1000;color:#ffd65a;text-shadow:0 6px 20px #000;animation:pop3d .55s}.ovsmall{font-size:20px;font-weight:800}.flash{position:fixed;inset:0;pointer-events:none;z-index:45;opacity:0}.flash.correct{animation:goldFlash .8s}.flash.wrong{animation:redFlash .65s}.confetti{position:fixed;inset:0;z-index:60;pointer-events:none;overflow:hidden}.confetti i{position:absolute;top:-15px;width:8px;height:16px;animation:fall3d 1.6s linear forwards}.shake{animation:shake3d .5s}.questionIn{animation:qIn .55s cubic-bezier(.2,.8,.2,1)}@keyframes float3d{50%{transform:translateY(-7px) rotate(2deg)}}@keyframes fade3d{from{opacity:0}}@keyframes pop3d{0%{transform:scale(.55);opacity:0}70%{transform:scale(1.1)}100%{transform:scale(1)}}@keyframes goldFlash{20%{opacity:1;background:#ffd84f99}100%{opacity:0}}@keyframes redFlash{25%{opacity:1;background:#ff294c88}100%{opacity:0}}@keyframes fall3d{to{transform:translateY(110vh) rotate(720deg)}}@keyframes shake3d{20%,60%{transform:translateX(-8px)}40%,80%{transform:translateX(8px)}}@keyframes qIn{from{opacity:0;transform:translateY(22px) scale(.96)}to{opacity:1;transform:none}}@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;transition:none!important}}
</style>
<style id="touch-hotfix">
/* Mobile interaction hotfix: decorative layers must never intercept taps */
.fx,.particles,.confetti,.spotlight,.stage-lights,.stage-floor,
.stage::before,.stage::after,.card::before,.card::after,
body::before,body::after { pointer-events:none !important; }

/* Actual controls always sit above decorative layers */
button,.btn,[role="button"],input,select,a {
  pointer-events:auto !important;
  position:relative;
  z-index:50;
  touch-action:manipulation;
}
</style>

</head><body><div class="stagefx"></div><div id="flash" class="flash"></div><div id="confetti" class="confetti"></div><div id="overlay" class="overlay"><div><div id="ovmain" class="ovmain">晉級！</div><div id="ovsmall" class="ovsmall">下一題準備中</div></div></div><div class="wrap"><div class="fish">🐟👑</div><h1>鹹魚翻身</h1><div style="text-align:center">益智猜謎大挑戰・多人連線測試版</div>
<div id="join" class="card"><input id="name" placeholder="輸入暱稱"><h3>👤 單人挑戰</h3><div class="row"><button class="btn single" data-total="4">4人場</button><button class="btn single" data-total="8">8人場</button><button class="btn single" data-total="12">12人場</button><button class="btn single" data-total="16">16人場</button></div><h3>👥 多人連線</h3><div class="row"><button class="btn" data-role="player">我要參賽</button><button class="btn watch" data-role="spectator">我要當觀眾</button></div><button id="install" class="good" style="width:100%;color:white;font-weight:800;margin-top:12px">📲 一鍵加入手機桌面</button><button id="sound" class="watch" style="width:100%;color:white;font-weight:800;margin-top:8px">🔊 現場音效：開</button></div>
<div class="card"><div class="stats"><span>參賽者 <b id="pc">0</b></span><span>觀眾 <b id="sc">0</b></span></div><p id="role" class="muted">尚未進場</p></div>
<div id="game" class="card hide"><span id="cat" class="tag"></span><div id="timer" class="big">--</div><h2 id="q"></h2><div id="opts"></div><button id="giveup" class="danger" style="width:100%;margin-top:12px">🏳️ 放棄比賽・轉觀眾</button></div>
<div id="msg" class="card">等待加入...</div>
<div id="admin" class="card"><b>測試中央台</b><p class="muted">本頁先保留簡化中央台，正式部署會拆成管理入口。</p><div class="row"><input id="secs" type="number" value="20" min="5" max="120" placeholder="每題秒數"><input id="minp" type="number" value="2" min="1" max="100" placeholder="最低人數"></div><div class="row"><input id="maxp" type="number" value="100" min="1" max="100" placeholder="最高人數"><select id="choices" style="font-size:18px;border-radius:14px;padding:14px"><option value="4">四選一</option><option value="3">三選一</option></select></div><div class="row"><button id="savecfg" class="watch" style="color:white;font-weight:700">儲存場次設定</button><button id="start" class="btn">開始測試</button></div></div>
</div><script>
const ws=new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');let role='',deadline=0,phase='lobby',answered=false,pendingSingle=0,soundOn=true,deferredPrompt=null;
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e});
if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(()=>{});
function speak(t){if(!soundOn||!('speechSynthesis'in window))return; speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(t);u.lang='zh-TW';u.rate=.96;u.pitch=1.05;speechSynthesis.speak(u)}
function cheer(big=false){if(!soundOn)return;let A=window.AudioContext||window.webkitAudioContext;if(!A)return;let c=new A(),o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=big?880:660;g.gain.setValueAtTime(.001,c.currentTime);g.gain.exponentialRampToValueAtTime(.18,c.currentTime+.03);g.gain.exponentialRampToValueAtTime(.001,c.currentTime+.5);o.start();o.stop(c.currentTime+.52)}

const $=id=>document.getElementById(id);function confetti(n=34){let c=$('confetti');c.innerHTML='';let cs=['#ffd34f','#62d8ff','#ff5ba7','#9b6cff','#6cff9a'];for(let i=0;i<n;i++){let x=document.createElement('i');x.style.left=Math.random()*100+'vw';x.style.background=cs[i%cs.length];x.style.animationDelay=Math.random()*.35+'s';c.appendChild(x)}setTimeout(()=>c.innerHTML='',2200)}function flash(k){let f=$('flash');f.className='flash '+k;setTimeout(()=>f.className='flash',900)}function intermission(a,b,ms=1700){$('ovmain').textContent=a;$('ovsmall').textContent=b;$('overlay').classList.add('show');setTimeout(()=>$('overlay').classList.remove('show'),ms)}function correctFX(){flash('correct');confetti();cheer(false)}function wrongFX(){flash('wrong');$('game').classList.add('shake');setTimeout(()=>$('game').classList.remove('shake'),600)}function send(o){ws.send(JSON.stringify(o))}document.querySelectorAll('[data-role]').forEach(b=>b.onclick=()=>{let n=$('name').value.trim();if(!n)return alert('請輸入暱稱');send({type:'join',name:n,role:b.dataset.role});$('join').classList.add('hide')});document.querySelectorAll('.single').forEach(b=>b.onclick=()=>{let n=$('name').value.trim();if(!n)return alert('請輸入暱稱');pendingSingle=+b.dataset.total;send({type:'join',name:n,role:'player'});$('join').classList.add('hide')});
$('sound').onclick=()=>{soundOn=!soundOn;$('sound').textContent=soundOn?'🔊 現場音效：開':'🔇 現場音效：關'};
$('install').onclick=async()=>{if(deferredPrompt){deferredPrompt.prompt();await deferredPrompt.userChoice;deferredPrompt=null}else alert('若沒有跳出安裝視窗，請用瀏覽器選單的「加到主畫面／加入主畫面」。')};
$('savecfg').onclick=()=>send({type:'admin_config',admin:'fishboss',seconds:+$('secs').value||20,min_players:+$('minp').value||1,max_players:+$('maxp').value||100,choices:+$('choices').value||4});$('start').onclick=()=>{ $('savecfg').click(); setTimeout(()=>send({type:'start',admin:'fishboss',seconds:+$('secs').value||20}),100)};$('giveup').onclick=()=>{if(confirm('確定放棄本場比賽並轉為觀眾？'))send({type:'giveup'})};
ws.onmessage=e=>{let d=JSON.parse(e.data);if(d.type==='joined'){role=d.role;$('role').textContent=role==='player'?'身分：正式參賽者':'身分：觀眾';if(pendingSingle){let t=pendingSingle;pendingSingle=0;send({type:'single_start',total:t});speak('歡迎來到鹹魚翻身益智猜謎大挑戰，單人挑戰正式開始');}}
if(d.type==='state'){phase=d.phase;deadline=d.deadline;$('pc').textContent=d.player_count;$('sc').textContent=d.spectator_count;if(d.phase==='question'){answered=false;$('game').classList.remove('hide');$('game').classList.remove('questionIn');void $('game').offsetWidth;$('game').classList.add('questionIn');$('cat').textContent=d.question.cat;$('q').textContent=d.question.q;$('opts').innerHTML='';d.question.opts.forEach((x,i)=>{let b=document.createElement('button');b.className='opt';b.textContent='ABCD'[i]+'　'+x;b.onclick=()=>{if(answered)return;answered=true;send({type:'answer',idx:i});b.classList.add('chosen');$('msg').textContent=role==='player'?'答案已送出，等待中央判定':'觀眾答案已記錄，不影響正式比賽';};$('opts').appendChild(b)});$('giveup').style.display=role==='player'?'block':'none';$('msg').textContent='作答中…';}else if(d.phase==='finished'){cheer(true);confetti(70);intermission('🏆 冠軍誕生！','鹹魚翻身成功',2600);speak('恭喜，本場總冠軍誕生');$('game').classList.add('hide');$('msg').innerHTML='<div class="winner">🎊🏆🎊<br><b>本場總冠軍</b><br><span style="color:#ffd45b;font-size:36px">'+d.winner+'</span><br>鹹魚翻身成功！</div>';} }
if(d.type==='role_changed'){if(d.reason==='eliminated'){speak('哎呀，這一題可惜了，先到觀眾席繼續幫大家加油');}role=d.role;$('role').textContent='身分：觀眾';$('giveup').style.display='none';if(d.reason==='eliminated')wrongFX();$('msg').innerHTML='😂 <b>答錯或逾時！</b><br>你已掉到觀眾席，繼續陪大家玩！';else $('msg').innerHTML='👋 已放棄正式比賽，現在進入觀眾席。';}
if(d.type==='cancelled'){$('msg').textContent='⚠️ '+d.text;}
if(d.type==='round'){if(d.result==='resolved'){correctFX();intermission('晉級！','下一題準備中');speak('答題結算完成，晉級的選手繼續挑戰');}if(d.result==='all_wrong')$('msg').textContent='😱 全員答錯！本題無人淘汰，繼續下一題！';else $('msg').innerHTML='🎉 <b>答題結算完成！</b><br>晉級者準備下一題，淘汰者已轉入觀眾席。';}}
setInterval(()=>{if(phase==='question'){let s=Math.max(0,Math.ceil(deadline-Date.now()/1000));$('timer').textContent=s;}},200);
</script></body></html>'''
