"""聊天養成商店與物品設定（C5, R3, R7）。

提供 12 件可購買、持久化、可檢視用途之實體與調查道具。
整合現有經濟與資產（定價 300 ~ 2000 遊戲幣）。
嚴格 6 件物品具備實際觸發支線或替代查證行動功能。
全面剔除虛假法規、技術神話（如「不可篡改拍立得」、「惡意軟體備用機沙箱」等），
回歸務實之物證保存、獨立查詢管道與物理紀錄。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ShopItemConfig:
    id: str
    name: str
    price: int
    category: str  # "investigation_tool" | "environment" | "social"
    description: str
    visible_use: str
    triggers_action: bool
    action_description: str | None = None
    max_quantity: int = 1


ITEMS_CATALOG: dict[str, ShopItemConfig] = {
    # ── 6 件實際觸發調查/支線行動道具 ──
    "second_phone": ShopItemConfig(
        id="second_phone",
        name="第二支手機",
        price=800,
        category="investigation_tool",
        description="配備獨立門號的實體備用手機，便於使用獨立查詢之官方代表號撥打核實，避免使用對方提供之轉接線路。",
        visible_use="在情境查證中啟用『獨立外部線路撥打』行動，向公開登記之客服專線查證。",
        triggers_action=True,
        action_description="解鎖專用查證工具：直接外撥官方獨立總機驗證對方陳述。",
    ),
    "document_scanner": ShopItemConfig(
        id="document_scanner",
        name="文件掃描器",
        price=1200,
        category="investigation_tool",
        description="桌上型公文與紙本光學掃描器，清晰數位化留存合約紙本、印記與字樣，利於對比存查。",
        visible_use="將紙本合約清晰存查，方便比對印文格式與條款細節。",
        triggers_action=True,
        action_description="解鎖專用查證工具：掃描留存合約數位影像與條款存查。",
    ),
    "secondhand_polaroid": ShopItemConfig(
        id="secondhand_polaroid",
        name="二手拍立得",
        price=500,
        category="investigation_tool",
        description="二手即時顯影相機，用於現場實體物件與展台留存實體相片存證。",
        visible_use="在現場拍攝實物外觀並留存時間標記相片存證。",
        triggers_action=True,
        action_description="解鎖專用查證工具：拍攝手工人偶微距實體照片證明原創特徵。",
    ),
    "pet_supplies": ShopItemConfig(
        id="pet_supplies",
        name="高級寵物用品組",
        price=400,
        category="social",
        description="包含舒適貓窩、無塵礦砂與高品質凍乾點心，社區動物照護與共養必備用品。",
        visible_use="開啟社區流浪動物共養與友善互動支線，獲得阿燦與鄰里深厚好感牽絆。",
        triggers_action=True,
        action_description="觸發事件分支：為社區街貓提供照護用品，快速建立鄰里信任牽絆。",
    ),
    "collectible_doll": ShopItemConfig(
        id="collectible_doll",
        name="限定收藏玩偶",
        price=700,
        category="social",
        description="地雷系次文化同好圈手工製作玩偶，精緻工藝象徵同好間的真摯共鳴。",
        visible_use="同好交流信物，在梨梨人偶版權爭議事件中給予極大心理支持，穩定其慌亂心態。",
        triggers_action=True,
        action_description="觸發事件分支：出示限定玩偶引起共鳴，降低梨梨防禦心態並獲得關鍵細節。",
    ),
    "dashcam": ShopItemConfig(
        id="dashcam",
        name="雙鏡頭行車紀錄器",
        price=1000,
        category="investigation_tool",
        description="前後廣角夜視行車紀錄器，清晰記錄外訪與載運樣品過程之影音紀錄。",
        visible_use="提供車輛外出佈展或實體交割時之動線與環境佐證，留存交通與會勘紀錄。",
        triggers_action=True,
        action_description="觸發事件分支：以清晰行車紀錄影音佐證現場會勘與物料載運實態。",
    ),

    # ── 6 件環境/社交/展示道具（不觸發獨立調查工具行動） ──
    "workbench": ShopItemConfig(
        id="workbench",
        name="實木工作桌",
        price=1500,
        category="environment",
        description="厚實溫潤的實木多層收納工作桌，提供清晰井然的事證分類與檔案歸納空間。",
        visible_use="提供整齊卷宗整理空間，在經紀合約等複雜文書審閱中提供條款拆解支援。",
        triggers_action=False,
    ),
    "display_cabinet": ShopItemConfig(
        id="display_cabinet",
        name="鋼化展示櫃",
        price=2000,
        category="environment",
        description="配備柔光射燈的鋼化玻璃展示櫃，展示正派合作合約與感謝狀，提升專業形象。",
        visible_use="大幅提升商業人脈初次拜訪時的專業信任度，解鎖豪哥高階投資防詐深度諮詢。",
        triggers_action=False,
    ),
    "guestroom_decor": ShopItemConfig(
        id="guestroom_decor",
        name="溫馨客房佈置",
        price=1800,
        category="environment",
        description="柔和米白色調的沉靜接待空間佈置，營造遠離外界催促騷擾的安靜隱私環境。",
        visible_use="提供委託人沉澱與隱私保護空間，協助房東阿姨等長輩緩解急迫心理壓力。",
        triggers_action=False,
    ),
    "commemorative_plaque": ShopItemConfig(
        id="commemorative_plaque",
        name="防詐紀念桌牌",
        price=300,
        category="social",
        description="警民反詐互助宣導活動之榮譽紀念桌牌，象徵參與反詐宣導的紀念品（裝飾紀念性質，不具法定效力）。",
        visible_use="擺放於辦公空間作為宣導紀念，提升溝通誠意。",
        triggers_action=False,
    ),
    "vintage_tape": ShopItemConfig(
        id="vintage_tape",
        name="復古錄音帶機",
        price=600,
        category="investigation_tool",
        description="傳統語音磁帶錄音機，適合留存商務洽談口頭說明與對話備忘。",
        visible_use="留存商務洽談口頭討論與說明會重點，防範口頭承諾與書面不符。",
        triggers_action=False,
    ),
    "photo_album": ShopItemConfig(
        id="photo_album",
        name="精裝回憶相冊",
        price=450,
        category="social",
        description="皮革精裝家庭與親友回憶相冊，收錄真實生活照片與重要緊急聯絡人電話名錄。",
        visible_use="強化情感防線，在面對冒名親友求助或緊急事故詐騙時快速查對真正親友現況。",
        triggers_action=False,
    ),
}


def get_item(item_id: str) -> ShopItemConfig | None:
    return ITEMS_CATALOG.get(item_id)


def list_all_items() -> list[ShopItemConfig]:
    return list(ITEMS_CATALOG.values())
