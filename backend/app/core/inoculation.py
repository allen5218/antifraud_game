import math
from typing import Any
from pydantic import BaseModel

from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_TAGS


class InoculationDebriefing(BaseModel):
    scammer_playbook: list[str]
    manipulation_tactic_analysis: str
    targeted_heuristics: list[str]
    vulnerability_explanation: str
    if_trigger: str
    then_action: str
    verification_challenge: str


INOCULATION_CATALOG: dict[str, dict[str, Any]] = {
    "time_pressure": {
        "playbook": [
            "製造突發急迫情境（帳戶凍結/名額被搶走）",
            "設置短時間倒數窗口阻斷理性思考",
            "逼迫受害者跳過第三方常規驗證",
        ],
        "manipulation_tactic": "透過人為時間視窗截斷，阻斷系統二進行假設性思維的工作記憶預算。",
        "heuristics": ["稀缺性捷思 (Scarcity Heuristic)", "損失厭惡 (Loss Aversion)"],
        "vulnerability_explanation": "大腦在面對『即將失去』的時間倒數時，杏仁核迅速激活，本能尋求最快解除焦慮的出口。",
        "if_trigger": "當對方以『限時催促、否則權益失效/帳戶凍結』為由要求立即動作時",
        "then_action": "我會無條件強制冷靜 15 分鐘，放開手機並透過獨立第三方管道查證",
        "challenge": "如果是正規行政或合約程序，為何不能等待 24 小時書面核對？",
    },
    "authority": {
        "playbook": [
            "冒用檢警、監理站或金融主管機關專業人設",
            "出示偽造公文或專業執照施加法律威懾",
            "以『偵查不公開』或『內部規定』阻絕受害者向家人求助",
        ],
        "manipulation_tactic": "單向不對稱權力壓迫，觸發社會化服從定勢，誘使個體將決策責任外包。",
        "heuristics": ["權威偏差 (Authority Bias)", "服從定勢 (Compliance Script)"],
        "vulnerability_explanation": "人類對執法與體制象徵具有先天的服從慣性，面對官方威懾時易產生過度恐懼。",
        "if_trigger": "當對方自稱檢警官員、銀行法務，要求私下通話或監管資金時",
        "then_action": "我會立即掛斷通話，主動撥打 165 反詐專線或向該機關總機獨立查證",
        "challenge": "檢警與金融監理機關絕無任何『個人帳戶資金監管』程序！",
    },
    "greed": {
        "playbook": [
            "拋出超常年化報酬率與『保本保息』誘餌",
            "先給予小額出金獲利體驗，降低戒心並誘使大額加碼",
            "出金時設置手續費、稅金等『連環解鎖障礙』",
        ],
        "manipulation_tactic": "非對稱風險回報背離，利用超常刺激劫持腹側紋狀體多巴胺獎勵預期。",
        "heuristics": ["非理性繁榮 (Irrational Exuberance)", "沉沒成本效應 (Sunk Cost Fallacy)"],
        "vulnerability_explanation": "高回報誘惑使大腦前額葉對風險機率的批判性評估短路，沉沒成本迫使人越陷越深。",
        "if_trigger": "當任何投資項目宣稱『保證獲利』或遠高於市場無風險利率時",
        "then_action": "我會將其直接歸類為高危龐氏騙局，絕不在非受管轄平台存入資產",
        "challenge": "若真有穩賺不賠的高報酬，對方為何不自行融資獨賺，而要分享給陌生人？",
    },
    "social_proof": {
        "playbook": [
            "建立數十人暗樁群組，每日洗版獲利截圖與感謝證言",
            "營造『全場搶購/眾人上車』的群體狂熱氛圍",
            "孤立並壓制任何提出合理質疑的聲音",
        ],
        "manipulation_tactic": "人工製造一致性同溫層，利用錯失焦慮（FOMO）強加群體從眾壓力。",
        "heuristics": ["從眾效應 (Bandwagon Effect)", "錯失焦慮 (FOMO Cascade)"],
        "vulnerability_explanation": "人類進化形成依靠群體信號做判斷的直覺，在封閉環境中容易將人造共識誤認為真相。",
        "if_trigger": "當遇到封閉群組眾人一致鼓吹某項獲利機會且缺乏第三方審查時",
        "then_action": "我會提醒自己截圖與人設皆可批量偽造，跳出群組保持獨立審查",
        "challenge": "在封閉的私人聊天室中，眼見不一定為憑，暗樁製造的共識毫無客觀可信度。",
    },
    "trust_building": {
        "playbook": [
            "長週期情感鋪陳與無微不至的關懷（人設共振）",
            "過度利他與贈送小禮，建立互惠心理債務",
            "關係牢固後突發急難危機或共享賺錢機密，要求金流移轉",
        ],
        "manipulation_tactic": "漸進式人設共振與登門檻技術，利用互惠原則模糊交易與私交邊界。",
        "heuristics": ["互惠原則 (Reciprocity Norm)", "光環效應 (Halo Effect)"],
        "vulnerability_explanation": "情感連結使個體對對方的道德品行產生過度推定，防備警覺心隨信任感上升而解除。",
        "if_trigger": "當網路結識的熱心好友或交往對象突然涉及金錢借貸或投資操作時",
        "then_action": "我會嚴格遵守『談錢即踩煞車』原則，要求實體見面或官方合規驗證",
        "challenge": "人設與談吐再真誠，只要牽涉無法追溯的非正規金流，風險即為百分之百。",
    },
}


def _norm_inv(p: float) -> float:
    """標準常態分佈反累積函數近似算法 (Winitzki 近似)。"""
    p = max(0.001, min(0.999, p))
    # 使用經典 Abramowitz & Stegun 有理近似
    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308

    if p < 0.5:
        t = math.sqrt(-2.0 * math.log(p))
        num = c0 + c1 * t + c2 * (t**2)
        den = 1.0 + d1 * t + d2 * (t**2) + d3 * (t**3)
        return -(t - num / den)
    else:
        t = math.sqrt(-2.0 * math.log(1.0 - p))
        num = c0 + c1 * t + c2 * (t**2)
        den = 1.0 + d1 * t + d2 * (t**2) + d3 * (t**3)
        return t - num / den


def compute_signal_detection_metrics(
    hits: int,
    misses: int,
    false_alarms: int,
    correct_rejections: int,
) -> dict[str, Any]:
    """計算信號偵測理論 (SDT) 之辨別敏感度 d' 與決策偏誤 c。
    
    使用 Hautus (1995) 對數線性平滑 (Log-linear smoothing: +0.5 / +1)
    以避免極端值 (0 或 1) 造成常態分佈無窮大。
    """
    total_signal = hits + misses
    total_noise = false_alarms + correct_rejections

    # Hautus log-linear correction
    hit_rate = (hits + 0.5) / (total_signal + 1.0) if total_signal > 0 else 0.5
    fa_rate = (false_alarms + 0.5) / (total_noise + 1.0) if total_noise > 0 else 0.5

    z_hit = _norm_inv(hit_rate)
    z_fa = _norm_inv(fa_rate)

    # d' = Z(H) - Z(FA)
    d_prime = round(float(z_hit - z_fa), 2)

    # c = -0.5 * (Z(H) + Z(FA))
    # c < -0.35: 寬鬆判定/草木皆兵 (Paranoid); c > 0.35: 保守判定/輕信冒險 (Credulous); c ~ 0: 理性平衡 (Balanced)
    criterion_c = round(float(-0.5 * (z_hit + z_fa)), 2)

    if criterion_c < -0.35:
        bias_profile = "paranoid"   # 草木皆兵型：決策門檻過低，將正常交易頻繁誤判為詐騙
    elif criterion_c > 0.35:
        bias_profile = "credulous"  # 輕信冒險型：決策門檻過高，鮮少舉報，極易受騙漏報
    else:
        bias_profile = "balanced"   # 理性免疫型：精準識別且維持健康信任

    # 綜合認知免疫力評分 (0-100)
    # d' 典型範圍 0.0 到 3.5；1.5 以上為良好，2.5 以上為卓越
    immunity_score = min(100, max(0, int(30 * max(0.0, d_prime) - 15 * abs(criterion_c) + 20)))

    return {
        "d_prime": d_prime,
        "criterion_c": criterion_c,
        "bias_profile": bias_profile,
        "immunity_score": immunity_score,
        "hit_rate": round(hit_rate, 2),
        "false_alarm_rate": round(fa_rate, 2),
    }


def get_inoculation_debriefing(tag: str | None) -> InoculationDebriefing:
    """根據弱點標籤產生三階解構式復盤內容。"""
    key = tag if tag in INOCULATION_CATALOG else "time_pressure"
    data = INOCULATION_CATALOG[key]
    return InoculationDebriefing(
        scammer_playbook=data["playbook"],
        manipulation_tactic_analysis=data["manipulation_tactic"],
        targeted_heuristics=data["heuristics"],
        vulnerability_explanation=data["vulnerability_explanation"],
        if_trigger=data["if_trigger"],
        then_action=data["then_action"],
        verification_challenge=data["challenge"],
    )
