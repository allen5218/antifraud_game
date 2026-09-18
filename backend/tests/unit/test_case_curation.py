"""測試素材投影與策展覆蓋（T1 / AC1）。"""

from app.core.case_curation import (
    SAFE_CURATED_PROJECTIONS,
    SPOILER_KEYWORDS,
    is_safe_narrative,
    project_case_safely,
)
from app.core.cases import GameCaseRow
from app.models import FraudType


def test_all_five_fraud_types_covered() -> None:
    """確保五種既有詐騙類型皆有策展投影覆蓋。"""
    covered_types = {proj.fraud_type for proj in SAFE_CURATED_PROJECTIONS.values()}
    for ft in FraudType:
        assert ft.value in covered_types, f"缺少 {ft.value} 策展投影"


def test_each_fraud_type_has_scam_and_legit_cases() -> None:
    """每種詐騙類型均包含詐騙與合法對照案例。"""
    for ft in FraudType:
        scam_cases = [
            proj
            for proj in SAFE_CURATED_PROJECTIONS.values()
            if proj.fraud_type == ft.value and proj.is_scam
        ]
        legit_cases = [
            proj
            for proj in SAFE_CURATED_PROJECTIONS.values()
            if proj.fraud_type == ft.value and not proj.is_scam
        ]
        assert len(scam_cases) >= 4, f"{ft.value} 詐騙案例不足"
        assert len(legit_cases) >= 4, f"{ft.value} 合法案例不足"


def test_curated_projections_have_no_spoilers() -> None:
    """所有已審核的策展投影內文均不可包含洩題/定性結局詞彙。"""
    for case_id, proj in SAFE_CURATED_PROJECTIONS.items():
        assert is_safe_narrative(proj.narrative, proj.title), (
            f"案例 {case_id} ({proj.title}) 包含洩題詞彙"
        )
        for kw in SPOILER_KEYWORDS:
            assert kw not in proj.narrative, f"案例 {case_id} 包含關鍵詞 {kw}"
            assert kw not in proj.title, f"案例 {case_id} 標題包含關鍵詞 {kw}"


def test_project_case_safely_rejects_uncurated_spoiler_case() -> None:
    """未經策展且含有警政結局/洩題詞彙的歷史案例，必須被安全攔截。"""
    spoiled_case = GameCaseRow(
        id=99999,
        fraud_type="investment",
        is_scam=True,
        title="警方破獲某投資群組案",
        narrative="被害人匯款後發覺上當，立即到警局報案，警方循線逮捕詐騙集團。",
        red_flags=[],
        difficulty=2,
        provenance="165 歷史舊檔",
    )
    proj, is_safe = project_case_safely(spoiled_case)
    assert not is_safe
    assert proj is None


def test_project_case_safely_accepts_clean_case() -> None:
    """若歷史案例經檢驗無洩題詞彙，可動態產生投影。"""
    clean_case = GameCaseRow(
        id=88888,
        fraud_type="atm",
        is_scam=True,
        title="某購物網站的來電通知",
        narrative="對方在電話中表示我的訂單有異常，要我至鄰近機台確認設定。我站在機台前猶豫不決。",
        red_flags=[],
        difficulty=1,
        provenance="測試案例",
    )
    proj, is_safe = project_case_safely(clean_case)
    assert is_safe
    assert proj is not None
    assert proj.title == clean_case.title
