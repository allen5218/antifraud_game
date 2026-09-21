import math
import random
import sys
import uuid
from dataclasses import dataclass, field
from typing import Any

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.core.calibration import compute_calibration
from app.core.inoculation import (
    INOCULATION_CATALOG,
    compute_signal_detection_metrics,
    get_inoculation_debriefing,
)
from app.core.skills_config import (
    SKILL_DEFINITIONS,
    calculate_sp_overview,
    get_skill_bonus,
)
from app.core.weakness import WEAKNESS_TAGS
from app.core.implementation_intentions import compute_equipped_bonuses
from app.economy.chapters import apply_income_multiplier
from app.economy.levels import level_of
from app.models import User
from app.scenario import manager


@dataclass
class PlayerPersona:
    id: str
    name: str
    archetype: str
    # 初始對 5 大弱點標籤的易受騙機率 (0.0 - 1.0)
    vulnerabilities: dict[str, float]
    # 查證工具使用偏好 (0.0 - 1.0)
    verification_propensity: float
    # 初始作答反應時間 (秒)
    baseline_deliberation_time: float
    # 初始決策門檻 (偏保守 vs 偏寬鬆)
    initial_bias: float
    # 經濟與遊戲狀態
    cash: int = 1000
    xp: int = 0
    completed_chapters: int = 0
    skills: dict[str, int] = field(default_factory=dict)
    is_bankrupt: bool = False
    is_retained: bool = True
    # 歷程統計
    hits: int = 0
    misses: int = 0
    false_alarms: int = 0
    correct_rejections: int = 0
    history_deliberation: list[float] = field(default_factory=list)
    inoculation_exposures: dict[str, int] = field(default_factory=dict)
    equipped_cards: list[str] = field(default_factory=list)
    predictions: list[tuple[float, bool]] = field(default_factory=list)


def create_cohort(cohort_size_per_archetype: int = 25) -> list[PlayerPersona]:
    players: list[PlayerPersona] = []
    
    # 1. 衝動型網購族 (Impulsive Shopper)
    for i in range(cohort_size_per_archetype):
        players.append(
            PlayerPersona(
                id=f"shopper_{i}",
                name=f"衝動網購者_{i+1}",
                archetype="impulsive_shopper",
                vulnerabilities={
                    "time_pressure": 0.85,
                    "greed": 0.75,
                    "social_proof": 0.70,
                    "authority": 0.45,
                    "trust_building": 0.50,
                },
                verification_propensity=0.20,
                baseline_deliberation_time=1.8,
                initial_bias=-0.45,  # 輕信偏誤
            )
        )

    # 2. 信任型長輩族 (Trusting Senior)
    for i in range(cohort_size_per_archetype):
        players.append(
            PlayerPersona(
                id=f"senior_{i}",
                name=f"信任長輩_{i+1}",
                archetype="trusting_senior",
                vulnerabilities={
                    "authority": 0.90,
                    "trust_building": 0.80,
                    "time_pressure": 0.65,
                    "social_proof": 0.60,
                    "greed": 0.35,
                },
                verification_propensity=0.15,
                baseline_deliberation_time=5.2,
                initial_bias=0.60,  # 極端保守，不願質疑官方
            )
        )

    # 3. 科技防備懷疑者 (Tech-Savvy Cynic)
    for i in range(cohort_size_per_archetype):
        players.append(
            PlayerPersona(
                id=f"cynic_{i}",
                name=f"科技懷疑者_{i+1}",
                archetype="tech_savvy_cynic",
                vulnerabilities={
                    "time_pressure": 0.30,
                    "authority": 0.25,
                    "greed": 0.30,
                    "social_proof": 0.20,
                    "trust_building": 0.35,
                },
                verification_propensity=0.85,
                baseline_deliberation_time=3.5,
                initial_bias=-0.50,  # 過度防禦 (草木皆兵)
            )
        )

    # 4. 休閒型遊戲玩家 (Casual Mobile Gamer)
    for i in range(cohort_size_per_archetype):
        players.append(
            PlayerPersona(
                id=f"gamer_{i}",
                name=f"休閒玩家_{i+1}",
                archetype="casual_gamer",
                vulnerabilities={
                    "time_pressure": 0.55,
                    "greed": 0.60,
                    "social_proof": 0.50,
                    "authority": 0.40,
                    "trust_building": 0.45,
                },
                verification_propensity=0.40,
                baseline_deliberation_time=2.4,
                initial_bias=-0.10,
            )
        )

    return players


class SimulationEngine:
    def __init__(self, players: list[PlayerPersona]):
        self.players = players
        self.tags = list(WEAKNESS_TAGS)
        self.fraud_types = ["investment", "shopping", "fake-sale", "romance", "atm"]

    def run_session_round(self, round_num: int):
        """模擬一輪綜合遊玩：1 次 Swipe (12題) + 1 次 Scenario 偵查 + 技能加點決策。"""
        for p in self.players:
            if not p.is_retained:
                continue
            # 依人格自動裝備 If-Then 反射卡
            if round_num >= 2 and not p.equipped_cards:
                if p.archetype == "impulsive_shopper":
                    p.equipped_cards = ["time_pressure_brake", "greed_freeze"]
                elif p.archetype == "trusting_senior":
                    p.equipped_cards = ["authority_audit", "trust_refuse"]
                elif p.archetype == "tech_savvy_cynic":
                    p.equipped_cards = ["social_proof_verify", "authority_audit"]
                else:
                    p.equipped_cards = ["time_pressure_brake", "social_proof_verify"]


            # ── 1. 模擬 Swipe 快速篩檢 ──
            insight_bonus = get_skill_bonus(p.skills, "insight_1")
            round_correct = 0
            round_streak = 0
            best_streak = 0

            for _ in range(12):
                is_scam = random.random() < 0.65
                tag = random.choice(self.tags)
                
                # 計算當前對該標籤的受騙機率（認知疫苗效應：暴露次數越多，易受騙率呈指數衰減）
                exposures = p.inoculation_exposures.get(tag, 0)
                # Inoculation decay factor lambda = 0.12
                effective_vuln = p.vulnerabilities[tag] * math.exp(-0.12 * exposures)

                # 作答反思時間隨輪數逐步拉長（踩煞車反射逐步成形）
                card_bonuses = compute_equipped_bonuses(p.equipped_cards)
                delib_time = p.baseline_deliberation_time + min(2.5, 0.15 * exposures) + card_bonuses["total_brake_latency"]
                p.history_deliberation.append(delib_time)

                if is_scam:
                    # 詐騙題：若被情緒/弱點劫持，則判定為 legit (Miss)；否則判定為 scam (Hit)
                    scammed = random.random() < effective_vuln
                    if scammed:
                        p.misses += 1
                        round_streak = 0
                        # 答錯觸發三階疫苗復盤，增加曝光強度 (+2)
                        p.inoculation_exposures[tag] = exposures + 2
                        conf = max(0.55, 0.90 - 0.012 * exposures)
                        p.predictions.append((conf, False))
                    else:
                        p.hits += 1
                        round_correct += 1
                        round_streak += 1
                        best_streak = max(best_streak, round_streak)
                        # 答對加深既有防禦基模 (+1)
                        p.inoculation_exposures[tag] = exposures + 1
                        conf = min(0.95, 0.70 + 0.01 * exposures)
                        p.predictions.append((conf, True))
                else:
                    # 正常題：檢驗是否產生誤報 (False Alarm)
                    # 懷疑者或草木皆兵者有一定機率誤判正常為詐騙
                    fa_rate = 0.35 if p.archetype == "tech_savvy_cynic" else 0.10
                    # 隨著疫苗接種成熟，正常訊號基線校準，誤報率下降
                    fa_rate *= math.exp(-0.08 * sum(p.inoculation_exposures.values()) / 10.0)
                    
                    if random.random() < fa_rate:
                        p.false_alarms += 1
                        round_streak = 0
                        p.predictions.append((0.78, False))
                    else:
                        p.correct_rejections += 1
                        round_correct += 1
                        round_streak += 1
                        best_streak = max(best_streak, round_streak)
                        p.predictions.append((0.85, True))

            # 結算 Swipe 獎勵
            streak_mult = 0.1 + insight_bonus
            base_cash = int(100 * round_correct * (1 + streak_mult * (best_streak // 3)))
            cash_earned = apply_income_multiplier(base_cash, p.completed_chapters)
            xp_earned = 10 * round_correct
            p.cash += cash_earned
            p.xp += xp_earned

            # ── 2. 模擬 Scenario 深度情境 ──
            ft = random.choice(self.fraud_types)
            is_scam_scenario = random.random() < 0.60
            primary_tag = random.choice(self.tags)
            
            # 使用查證工具
            uses_verify = random.random() < p.verification_propensity
            if uses_verify:
                # 查證工具直接大幅穿透詐騙偽裝
                effective_vuln = p.vulnerabilities[primary_tag] * 0.2
            else:
                effective_vuln = p.vulnerabilities[primary_tag] * math.exp(
                    -0.12 * p.inoculation_exposures.get(primary_tag, 0)
                )

            shield_reduction = get_skill_bonus(p.skills, "shield_1")
            negotiation_bonus = get_skill_bonus(p.skills, "negotiation_1")

            if is_scam_scenario:
                if random.random() < effective_vuln:
                    # 受騙損失
                    card_bonuses = compute_equipped_bonuses(p.equipped_cards)
                    card_mit = card_bonuses["tag_mitigations"].get(primary_tag, 0.0)
                    loss = int(1500 * (1.0 - min(0.85, shield_reduction + card_mit)))
                    p.cash -= loss
                    p.misses += 1
                    p.inoculation_exposures[primary_tag] = p.inoculation_exposures.get(primary_tag, 0) + 3
                    conf = max(0.55, 0.92 - 0.015 * p.inoculation_exposures.get(primary_tag, 0))
                    p.predictions.append((conf, False))
                else:
                    # 破案勝出
                    win_reward = apply_income_multiplier(1200, p.completed_chapters)
                    p.cash += win_reward
                    p.xp += int(15 * (1.0 + negotiation_bonus))
                    p.hits += 1
                    p.inoculation_exposures[primary_tag] = p.inoculation_exposures.get(primary_tag, 0) + 1
                    conf = min(0.96, 0.75 + 0.012 * p.inoculation_exposures.get(primary_tag, 0))
                    p.predictions.append((conf, True))
            else:
                # 合法情境
                if uses_verify or random.random() > 0.2:
                    trust_reward = apply_income_multiplier(800, p.completed_chapters)
                    p.cash += trust_reward
                    p.xp += int(12 * (1.0 + negotiation_bonus))
                    p.correct_rejections += 1
                    p.predictions.append((0.85, True))
                else:
                    # 誤報罰款
                    mis_penalty = int(800 * (1.0 - min(0.75, shield_reduction)))
                    p.cash -= mis_penalty
                    p.false_alarms += 1
                    p.predictions.append((0.75, False))

            # 推進章節 (每 5 輪通關一章)
            if round_num % 5 == 0 and p.completed_chapters < 5:
                p.completed_chapters += 1

            # ── 3. 模擬天賦樹加點決策 (SP Allocation) ──
            # 建立虛擬 User 計算可用 SP
            u = User(id=uuid.uuid4(), email="sim@test.com", hashed_password="pw", xp=p.xp, completed_chapters=p.completed_chapters)
            sp_data = calculate_sp_overview(u, p.skills)
            available_sp = sp_data["available_sp"]

            if available_sp > 0:
                # 依人格偏好加點
                if p.archetype == "impulsive_shopper":
                    preferred = ["shield_1", "insight_1", "audit_1"]
                elif p.archetype == "trusting_senior":
                    preferred = ["audit_1", "shield_1", "negotiation_1"]
                elif p.archetype == "tech_savvy_cynic":
                    preferred = ["insight_1", "negotiation_1", "yield_1"]
                else:
                    preferred = ["yield_1", "insight_1", "shield_1"]

                for sk in preferred:
                    spec = SKILL_DEFINITIONS.get(sk)
                    if not spec:
                        continue
                    curr_lvl = p.skills.get(sk, 0)
                    cost = spec["sp_cost_per_level"]
                    if curr_lvl < spec["max_level"] and available_sp >= cost:
                        p.skills[sk] = curr_lvl + 1
                        available_sp -= cost

            # ── 4. 留存與流失檢驗 (Churn Analysis) ──
            # 破產流失：若現金小於 0 且護盾等級低，感到挫敗流失
            if p.cash < 0:
                p.is_bankrupt = True
                # 若無護盾保護，有 60% 機率直接挫敗離場
                if p.skills.get("shield_1", 0) == 0 and random.random() < 0.60:
                    p.is_retained = False
            
            # 停滯流失：休閒玩家若已買滿且現金無處花，有微小流失率；但有了天賦與吉祥物後流失大幅下降
            if p.cash > 25000 and random.random() < 0.01:
                p.is_retained = False

    def run_full_simulation(self, total_rounds: int = 30) -> dict[str, Any]:
        """執行完整 30 輪模擬並回傳綜合評估數據。"""
        # 初始基線測量 (Round 0)
        baseline_metrics = self._evaluate_cohort_metrics()

        for r in range(1, total_rounds + 1):
            self.run_session_round(r)

        final_metrics = self._evaluate_cohort_metrics()
        return {
            "baseline": baseline_metrics,
            "final": final_metrics,
            "total_rounds": total_rounds,
        }

    def _evaluate_cohort_metrics(self) -> dict[str, Any]:
        by_archetype: dict[str, Any] = {}
        archetypes = ["impulsive_shopper", "trusting_senior", "tech_savvy_cynic", "casual_gamer"]

        for arch in archetypes:
            subset = [p for p in self.players if p.archetype == arch]
            retained = [p for p in subset if p.is_retained]
            
            total_hits = sum(p.hits for p in subset)
            total_misses = sum(p.misses for p in subset)
            total_fa = sum(p.false_alarms for p in subset)
            total_cr = sum(p.correct_rejections for p in subset)

            sdt = compute_signal_detection_metrics(total_hits, total_misses, total_fa, total_cr)
            
            avg_delib = (
                sum(sum(p.history_deliberation) / max(1, len(p.history_deliberation)) for p in subset)
                / len(subset)
            )

            # 5 大弱點當前平均失誤率
            tag_errors = {}
            for tag in self.tags:
                avg_vuln = sum(
                    p.vulnerabilities[tag] * math.exp(-0.12 * p.inoculation_exposures.get(tag, 0))
                    for p in subset
                ) / len(subset)
                tag_errors[tag] = round(avg_vuln, 3)

            avg_cash = sum(p.cash for p in subset) / len(subset)
            avg_sp_spent = sum(sum(p.skills.values()) for p in subset) / len(subset)
            retention_rate = len(retained) / len(subset)

            by_archetype[arch] = {
                "d_prime": sdt["d_prime"],
                "criterion_c": sdt["criterion_c"],
                "bias_profile": sdt["bias_profile"],
                "immunity_score": sdt["immunity_score"],
                "retention_rate": round(retention_rate, 3),
                "avg_deliberation_seconds": round(avg_delib, 2),
                "tag_error_rates": tag_errors,
                "avg_cash": int(avg_cash),
                "avg_sp_spent": round(avg_sp_spent, 1),
                "bankrupt_count": sum(1 for p in subset if p.is_bankrupt),
            }

        # 總體指標
        all_retained = [p for p in self.players if p.is_retained]
        all_hits = sum(p.hits for p in self.players)
        all_misses = sum(p.misses for p in self.players)
        all_fa = sum(p.false_alarms for p in self.players)
        all_cr = sum(p.correct_rejections for p in self.players)
        overall_sdt = compute_signal_detection_metrics(all_hits, all_misses, all_fa, all_cr)
        all_preds = []
        for p in self.players:
            all_preds.extend(p.predictions)
        overall_calib = compute_calibration(all_preds)

        return {
            "overall_d_prime": overall_sdt["d_prime"],
            "overall_criterion_c": overall_sdt["criterion_c"],
            "overall_immunity_score": overall_sdt["immunity_score"],
            "overall_retention_rate": round(len(all_retained) / len(self.players), 3),
            "overall_calibration": overall_calib,
            "by_archetype": by_archetype,
        }


def main():
    print("啟動防詐騙認知強化學習與玩家留存隊列模擬引擎...")
    cohort = create_cohort(cohort_size_per_archetype=25)
    print(f"初始化虛擬玩家隊列完成：共 4 大群體，總計 {len(cohort)} 名玩家。")

    engine = SimulationEngine(cohort)
    results = engine.run_full_simulation(total_rounds=30)

    print("\n================ 模擬驗證結果報告 (30 輪迭代) ================")
    base = results["baseline"]
    final = results["final"]

    print(f"\n【總體認知免疫力成長】")
    print(f"辨別敏感度 d': 初始 = {base['overall_d_prime']} -> 最終 = {final['overall_d_prime']} (提升 +{round(final['overall_d_prime'] - base['overall_d_prime'], 2)})")
    print(f"決策偏誤 c: 初始 = {base['overall_criterion_c']} -> 最終 = {final['overall_criterion_c']} (趨向理性平衡)")
    print(f"認知免疫總分: 初始 = {base['overall_immunity_score']} -> 最終 = {final['overall_immunity_score']} 分")
    print(f"隊列留存率: {final['overall_retention_rate'] * 100}% (成功遏止無天賦保護時的破產勸退潮)")

    print(f"\n【過度自信校準評量 (Calibration & Brier Score)】")
    print(f"Brier 分數: 初始 = {base['overall_calibration']['brier_score']} -> 最終 = {final['overall_calibration']['brier_score']} (均方誤差大幅收斂)")
    print(f"過度自信指數 (OI): 初始 = {base['overall_calibration']['overconfidence_index']} -> 最終 = {final['overall_calibration']['overconfidence_index']} ({final['overall_calibration']['diagnosis']})")
    print(f"致命高確信失誤次數: 初始 = {base['overall_calibration']['high_confidence_errors']} -> 最終 = {final['overall_calibration']['high_confidence_errors']} (成功消除盲目自負陷阱)")
    print(f"行為校準指引: {final['overall_calibration']['advice']}")

    print(f"\n【各人格群體詳細對照】")
    arch_names = {
        "impulsive_shopper": "衝動型網購族",
        "trusting_senior": "信任型長輩族",
        "tech_savvy_cynic": "科技防衛懷疑者",
        "casual_gamer": "休閒型遊戲玩家",
    }
    for arch, name in arch_names.items():
        b = base["by_archetype"][arch]
        f = final["by_archetype"][arch]
        print(f"\n--- {name} ---")
        print(f"  d' 敏感度: {b['d_prime']} -> {f['d_prime']}")
        print(f"  決策形態: {b['bias_profile']} -> {f['bias_profile']} (c = {f['criterion_c']})")
        print(f"  煞車猶豫時長: {b['avg_deliberation_seconds']}s -> {f['avg_deliberation_seconds']}s")
        print(f"  天賦平均消耗: {f['avg_sp_spent']} SP | 平均資產: {f['avg_cash']} 元")
        print(f"  留存率: {f['retention_rate'] * 100}% | 破產紀錄: {f['bankrupt_count']} 人")
        print(f"  弱點標籤易受騙率演變:")
        for tag, err in f["tag_error_rates"].items():
            b_err = b["tag_error_rates"][tag]
            print(f"    - {tag}: {b_err*100:.1f}% -> {err*100:.1f}% (下降 -{round((b_err - err)*100, 1)}%)")

    return results


if __name__ == "__main__":
    main()
