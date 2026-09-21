"""快速測驗查證行動與證據解讀題庫素材（T1 / AC1）。

納入「下一步查證」與「證據能證明什麼」題型，提升玩家在有限資訊下的查證與決策能力。
作答前不洩漏正解與話術標籤。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VerificationQuestionMaterial:
    material_id: str
    fraud_type: str
    title: str
    narrative: str
    question: str
    options: list[
        dict[str, Any]
    ]  # list of {"key": "A", "text": "...", "is_correct": bool}
    explanation: str
    weakness_tag: str


VERIFICATION_MATERIALS: list[VerificationQuestionMaterial] = [
    VerificationQuestionMaterial(
        material_id="verif-atm-001",
        fraud_type="atm",
        title="客服說今晚會扣款",
        narrative="有人自稱購物平台客服，說你被誤設成會員，今晚會扣 12,000 元。",
        question="你認為怎麼做比較好？",
        options=[
            {
                "key": "A",
                "text": "自己打開官方 App，或打 165 查證",
                "is_correct": True,
            },
            {
                "key": "B",
                "text": "讓對方轉接銀行，再照電話指示操作",
                "is_correct": False,
            },
            {
                "key": "C",
                "text": "看過客服的工作證照片就配合",
                "is_correct": False,
            },
        ],
        explanation="不要跟著來電者操作。自己開官方 App，或打 165 查證最安全。",
        weakness_tag="authority",
    ),
    VerificationQuestionMaterial(
        material_id="verif-investment-001",
        fraud_type="investment",
        title="群組裡大家都在賺錢",
        narrative="投資群組裡，很多人貼出獲利截圖，還一直感謝老師帶單。",
        question="你認為這些截圖代表什麼？",
        options=[
            {
                "key": "A",
                "text": "很多真人都賺錢，應該可信",
                "is_correct": False,
            },
            {
                "key": "B",
                "text": "截圖可以造假，不能證明真的有獲利",
                "is_correct": True,
            },
            {
                "key": "C",
                "text": "代表老師有合法投資執照",
                "is_correct": False,
            },
        ],
        explanation="群組帳號和獲利截圖都可能是假的。是否合法，要到金管會網站查。",
        weakness_tag="social_proof",
    ),
    VerificationQuestionMaterial(
        material_id="verif-fake-sale-001",
        fraud_type="fake-sale",
        title="買家說你的款項被卡住",
        narrative="買家傳來付款失敗截圖，叫你掃 QR Code 聯絡客服。",
        question="你認為怎麼做比較好？",
        options=[
            {
                "key": "A",
                "text": "掃 QR Code，加客服好友處理",
                "is_correct": False,
            },
            {
                "key": "B",
                "text": "自己登入官方平台查看訂單",
                "is_correct": True,
            },
            {
                "key": "C",
                "text": "把卡號和餘額傳給買家查詢",
                "is_correct": False,
            },
        ],
        explanation="訂單和款項只看官方平台。不要掃買家傳來的 QR Code。",
        weakness_tag="authority",
    ),
    VerificationQuestionMaterial(
        material_id="verif-romance-001",
        fraud_type="romance",
        title="網友寄禮物，海關要你付錢",
        narrative="網友說寄了貴重禮物給你。接著有人寄信，催你付四萬元才能領。",
        question="你認為這張繳費單可信嗎？",
        options=[
            {
                "key": "A",
                "text": "可信，先付款才能領包裹",
                "is_correct": False,
            },
            {
                "key": "B",
                "text": "不能只看片面文件，要向海關官方查證",
                "is_correct": True,
            },
            {
                "key": "C",
                "text": "代表網友很有錢，值得相信",
                "is_correct": False,
            },
        ],
        explanation="一張照片不能證明是海關文件。請自己找海關官方管道查證。",
        weakness_tag="trust_building",
    ),
    VerificationQuestionMaterial(
        material_id="verif-shopping-001",
        fraud_type="shopping",
        title="三萬元筆電只賣九千",
        narrative="社群賣家說搬家急售，兩小時內匯款就立刻寄出。",
        question="你認為怎麼買比較安心？",
        options=[
            {
                "key": "A",
                "text": "走有保障的平台，或約安全地點面交測試",
                "is_correct": True,
            },
            {
                "key": "B",
                "text": "先匯一半訂金試試看",
                "is_correct": False,
            },
            {
                "key": "C",
                "text": "看過賣家的身分證照片就全額匯款",
                "is_correct": False,
            },
        ],
        explanation="超低價又催你快匯款，風險很高。留在有保障的平台比較安全。",
        weakness_tag="greed",
    ),
    VerificationQuestionMaterial(
        material_id="verif-overseas-job-001",
        fraud_type="overseas-job",
        title="海外高薪工作要收護照",
        narrative="對方說月薪 12 萬、包機票食宿，還要求你先交護照正本。",
        question="你認為怎麼做比較安全？",
        options=[
            {
                "key": "A",
                "text": "到勞動部查仲介資格，也不交出護照正本",
                "is_correct": True,
            },
            {
                "key": "B",
                "text": "先收一個月薪水，入帳後再交護照",
                "is_correct": False,
            },
            {
                "key": "C",
                "text": "加入對方的員工群，問群友是不是真的",
                "is_correct": False,
            },
        ],
        explanation="先向勞動部查仲介資格。護照正本不要交給陌生人保管。",
        weakness_tag="greed",
    ),
    VerificationQuestionMaterial(
        material_id="verif-ai-deepfake-001",
        fraud_type="ai-deepfake",
        title="好友視訊借三萬元",
        narrative="好友打視訊說出了車禍，催你立刻匯三萬元到陌生帳戶。",
        question="就算看見本人，你認為還要怎麼確認？",
        options=[
            {
                "key": "A",
                "text": "先掛斷，再用平常的電話回撥確認",
                "is_correct": True,
            },
            {
                "key": "B",
                "text": "視訊裡看見本人，可以直接匯款",
                "is_correct": False,
            },
            {
                "key": "C",
                "text": "請他比個手勢，看得到就相信",
                "is_correct": False,
            },
        ],
        explanation="影像和聲音也可能被仿冒。掛斷後用平常的電話回撥確認。",
        weakness_tag="trust_building",
    ),
    VerificationQuestionMaterial(
        material_id="verif-ghost-parcel-001",
        fraud_type="ghost-parcel",
        title="收到沒買過的貨到付款包裹",
        narrative="超商有一件 1,280 元的包裹，但你完全不記得自己買過。",
        question="你認為怎麼做比較好？",
        options=[
            {
                "key": "A",
                "text": "不付款，直接拒領退回",
                "is_correct": True,
            },
            {
                "key": "B",
                "text": "先付款拆開，不是自己的再退",
                "is_correct": False,
            },
            {
                "key": "C",
                "text": "先在櫃檯拆開看看內容物",
                "is_correct": False,
            },
        ],
        explanation="不確定是自己買的，就先不要付款。未訂購的包裹可以直接拒領。",
        weakness_tag="time_pressure",
    ),
]


def list_verification_materials(limit: int = 5) -> list[VerificationQuestionMaterial]:
    """取得查證題素材清單。"""
    return VERIFICATION_MATERIALS[:limit]


def get_verification_material(material_id: str) -> VerificationQuestionMaterial | None:
    """依 ID 取得查證題素材。"""
    for m in VERIFICATION_MATERIALS:
        if m.material_id == material_id:
            return m
    return None
