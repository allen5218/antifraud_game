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
        title="電商客服來電通知帳務問題",
        narrative="傍晚接獲自稱購物平台客服來電，表示因系統作業疏失，將你誤設為批發會員，今晚 12 點將自動扣款 12,000 元。",
        question="面對此情況，最安全有效的下一步查證方式為何？",
        options=[
            {
                "key": "A",
                "text": "自行開啟官方購物 App 檢查訂單狀態與會員設定，或撥打 165 專線查證",
                "is_correct": True,
            },
            {
                "key": "B",
                "text": "請對方在電話中協助轉接銀行專員，並在電話指引下至提款機確認",
                "is_correct": False,
            },
            {
                "key": "C",
                "text": "要求對方提供工作證照片，在確認照片看起來屬實後配合操作",
                "is_correct": False,
            },
        ],
        explanation="提款機（ATM）與網路銀行均無法解除任何分期付款或會員設定。任何疑慮應主動開啟官方 App 或撥打 165 查證。",
        weakness_tag="authority",
    ),
    VerificationQuestionMaterial(
        material_id="verif-investment-001",
        fraud_type="investment",
        title="投資群組內的對帳單截圖",
        narrative="LINE 投資群組中多位成員連續貼出單日獲利數十萬元的對帳單截圖，並感謝老師精準帶單。",
        question="這項「群友曬單」的證據，在防詐查證上能證明什麼？",
        options=[
            {
                "key": "A",
                "text": "證明群內確實有多位真實散戶獲利，具有高度參考價值",
                "is_correct": False,
            },
            {
                "key": "B",
                "text": "截圖極易由修圖軟體或暗樁配合偽造，無法證明該平台或獲利真實性",
                "is_correct": True,
            },
            {
                "key": "C",
                "text": "證明該投資顧問已經取得金管會合法特許執照",
                "is_correct": False,
            },
        ],
        explanation="群組曬單屬於常見的從眾心理（social proof）操縱，暗樁帳號可集體分飾角色。唯有在金管會證期局網站查核立案名單才是真實依據。",
        weakness_tag="social_proof",
    ),
    VerificationQuestionMaterial(
        material_id="verif-fake-sale-001",
        fraud_type="fake-sale",
        title="拍賣平台買家傳來的付款失敗截圖",
        narrative="在拍賣平台掛賣二手相機，買家傳訊表示已下單但畫面跳出「賣家未簽署金流協定，款項凍結」，並附上附有客服 QR Code 的截圖。",
        question="面對這張截圖，最正確的查證步驟為何？",
        options=[
            {
                "key": "A",
                "text": "掃描截圖上的客服 QR Code 加 LINE，依客服指示解除金流凍結",
                "is_correct": False,
            },
            {
                "key": "B",
                "text": "直接登入官方拍賣網站後台查看訂單狀態，不點擊或掃描買家提供的任何外部連結",
                "is_correct": True,
            },
            {
                "key": "C",
                "text": "先將銀行卡號與網銀餘額傳給買家，請買家向其銀行查詢",
                "is_correct": False,
            },
        ],
        explanation="正規拍賣平台所有金流狀態一律在站內官方系統呈現，絕不會要求賣家透過外部通訊軟體或 QR Code 聯繫客服解除凍結。",
        weakness_tag="authority",
    ),
    VerificationQuestionMaterial(
        material_id="verif-romance-001",
        fraud_type="romance",
        title="交往對象寄送的海外包裹稅金證明",
        narrative="網戀對象聲稱寄送貴重禮物與現金包裹，隨後你收到自稱「國際物流海關部門」電子郵件，催繳四萬元進口保證金否則退運。",
        question="這份自稱「海關清關繳費單」的文件，能證明什麼？",
        options=[
            {
                "key": "A",
                "text": "證明海關確實扣留此包裹，必須先行繳納方能通關",
                "is_correct": False,
            },
            {
                "key": "B",
                "text": "公家機關與海關稅費繳納有法定公庫程序，私人文件照片不能證明真實性，且海關絕不使用個人帳戶收款",
                "is_correct": True,
            },
            {
                "key": "C",
                "text": "證明交往對象經濟實力雄厚，值得信任",
                "is_correct": False,
            },
        ],
        explanation="假包裹、假清關稅費是愛情交友詐騙的標準套路。正式海關稅款繳納均有公庫稅單與海關官方查詢管道，絕不要求私人匯款。",
        weakness_tag="trust_building",
    ),
    VerificationQuestionMaterial(
        material_id="verif-shopping-001",
        fraud_type="shopping",
        title="社群賣家熱門商品極低價出清",
        narrative="在臉書二手社團看到原價三萬元的全新筆電僅售 9,000 元，賣家聲稱搬家急售，限兩小時內匯款即可當日寄出。",
        question="面對這項交易要約，哪一項查證行為最能保障自身權益？",
        options=[
            {
                "key": "A",
                "text": "堅持透過具備價金保管與履約保障的官方購物平台交易，或在公開安全處所當面測試交割",
                "is_correct": True,
            },
            {
                "key": "B",
                "text": "先匯一半訂金（4,500 元）測試賣家是否有誠信寄出",
                "is_correct": False,
            },
            {
                "key": "C",
                "text": "請賣家手持身分證拍照，收到照片後立即以網銀全額轉帳",
                "is_correct": False,
            },
        ],
        explanation="超低價搭配急迫限時匯款是典型假網購特徵。身分證照片極可能是遭冒用之受害者證件，脫離平台保護的私人匯款風險極高。",
        weakness_tag="greed",
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
