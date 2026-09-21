from typing import Any

GUARDIAN_NPCS: dict[str, dict[str, Any]] = {
    "npc_grandma_chen": {
        "id": "npc_grandma_chen",
        "name": "陳阿嬤",
        "title": "72歲 退休國小教師",
        "avatar": "/assets/avatars/grandma_chen.png",
        "target_fraud_types": ["atm", "fake-sale"],
        "weakness_tags": ["authority", "trust_building"],
        "background": "獨居在舊社區公寓，兒子常年在海外工作。一生奉公守法，最敬畏執法人員與官方公文。",
        "letters": {
            1: "謝謝調查員提醒我！剛才差點把存摺交給自稱主任檢察官的年輕人...有你真好！",
            2: "這是我自己醃的脆梅，送給你吃！有你在社區巡守，我們這些老人家安心多了。",
            3: "我把你的防詐秘訣印出來分給鄰居長輩了！你是我們社區的守護天使！",
        },
    },
    "npc_student_zhiming": {
        "id": "npc_student_zhiming",
        "name": "志明",
        "title": "20歲 大二工讀生",
        "avatar": "/assets/avatars/student_zhiming.png",
        "target_fraud_types": ["shopping", "fake-sale"],
        "weakness_tags": ["time_pressure", "greed"],
        "background": "半工半讀繳學雜費，在二手拍賣版交易頻繁，對『高薪兼職』與『低價出清』缺乏戒心。",
        "letters": {
            1: "太神了！差點把這學期的打工生活費全部匯給假賣家，謝謝學長/長官及時拉住我！",
            2: "我按照你教的，要求面交並查證第三方履約保證，那個騙子直接把我封鎖了！超爽快！",
            3: "我加入了學校反詐宣導隊！以後換我來保護學弟妹不被網購騙局坑害！",
        },
    },
    "npc_mother_yating": {
        "id": "npc_mother_yating",
        "name": "雅婷",
        "title": "35歲 單親兼職媽媽",
        "avatar": "/assets/avatars/mother_yating.png",
        "target_fraud_types": ["investment", "romance"],
        "weakness_tags": ["greed", "social_proof", "trust_building"],
        "background": "獨自撫養幼兒園女兒，為了兼顧育兒在網路上尋求彈性收入，常被群組獲利截圖吸引。",
        "letters": {
            1: "看到群組大家都在曬單，我差點把女兒的教育基金投進去...謝謝你讓我看破那個假平台！",
            2: "今天帶女兒去公園玩，心情特別輕鬆。不用再每天焦慮那些奇怪投資老師的指示了。",
            3: "我找到了一份正規的遠端行銷工作！謝謝調查員幫我守住了我們母女倆的家。",
        },
    },
}


def get_guardian_for_fraud_type(fraud_type: str) -> str:
    if fraud_type in ("investment", "romance"):
        return "npc_mother_yating"
    if fraud_type in ("shopping", "fake-sale"):
        return "npc_student_zhiming"
    return "npc_grandma_chen"


def calculate_guardian_level(trust_score: int) -> int:
    if trust_score >= 300:
        return 3
    if trust_score >= 100:
        return 2
    if trust_score >= 30:
        return 1
    return 0
