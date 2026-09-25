"""話術標籤的共用文案(前測/滑卡/題組/情境對抗共用,前端直接顯示這裡的字)。

標籤寫成「對方做了什麼」的白話,不用心理學名詞。
舊版是「權威服從」「貪念誘惑」「信任建立」「社會認同」—— 為了湊四個字,
沒有人會這樣講話,玩家看不懂自己到底被哪一招騙。

tag 代碼(time_pressure 等)存在題庫、作答紀錄與 AI 的回覆格式裡,**不要改代碼**,只改這裡的文字。
"""

WEAKNESS_TAGS: set[str] = {
    "time_pressure",
    "authority",
    "greed",
    "social_proof",
    "trust_building",
}

WEAKNESS_LABELS: dict[str, str] = {
    "time_pressure": "催你快點決定",
    "authority": "冒充官方或專家",
    "greed": "用好處引誘你",
    "social_proof": "說大家都在做",
    "trust_building": "先跟你套交情",
}

WEAKNESS_SUGGESTIONS: dict[str, str] = {
    "time_pressure": "對方越催，越要停下來。銀行、政府和正規商家都不會要你幾分鐘內做決定。",
    "authority": "自稱警察、檢察官、銀行人員或專家，都先掛斷，自己查官方電話打回去問。",
    "greed": "保證賺錢、穩賺不賠、價格低得離譜，都是詐騙最常用的餌。",
    "social_proof": "群組裡的人都說賺到了，他們可能是同一夥的，截圖也能造假。",
    "trust_building": "聊得再久、對你再好，只要開口借錢、要你匯款或下載 App，就先停下來查證。",
}
