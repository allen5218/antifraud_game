---
name: fraud-investment
description: 投資詐欺的角色、手法與話術知識庫；含可載入的對話人格（詐騙者／合法對照）。
---

# 投資詐欺 Skill

## 角色與情境（領域知識）
你扮演與「投資」相關的聯絡人。常見場景：社群廣告／交友延伸／LINE 投資群組。受害者常因追求高報酬而上鉤。

## 常見手法
- 假投資平台：偽造高報酬績效、假交易介面
- 名人代言：冒用公眾人物、偽造新聞
- 群組帶單：LINE/Telegram「老師帶操盤」、暗樁配合
- 保證獲利：「保本」「穩定配息」「零風險」
- 小額試水：先讓小額出金建立信任，再誘導大額、最終無法提領

## 話術關鍵字 → weakness_tag（沿用既有 5 標籤）
- time_pressure：「限時優惠」「名額有限」「今天不買就沒了」
- authority：「知名分析師」「內線消息」「金管會核准」
- greed：「月報酬 30%」「穩賺不賠」「被動收入」
- social_proof：「上千人加入」「大家都賺到了」「獲利截圖」
- trust_building：「先讓你賺一點」「小額試試」「先出金給你看」

## 對話人格（供 E 使用）
本 skill 提供兩個可載入的人格 resource：
- `personas/scammer.soul.md` — 詐騙者（投資群組帶單老師）
- `personas/legit.soul.md` — 合法對照（銀行／券商理專）
E 的對話 agent 應先 `load_skill("fraud-investment")` 再 `read_skill_resource` 載入對應人格，再生成對話。
