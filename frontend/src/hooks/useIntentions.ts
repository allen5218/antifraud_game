import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { OpenAPI } from "@/client/core/OpenAPI"
import { request as __request } from "@/client/core/request"
import useCustomToast from "./useCustomToast"

export interface ReflexCardData {
  id: string
  name: string
  weakness_tag: string
  title_label: string
  if_trigger: string
  then_action: string
  psychological_basis: string
  passive_bonus_text: string
  brake_latency_bonus: number
  damage_mitigation_rate: number
  far_transfer_multiplier: number
  is_unlocked: boolean
  is_equipped: boolean
  slot_index?: number | null
}

export interface IntentionsOverviewData {
  equipped_slots: (ReflexCardData | null)[]
  cards: ReflexCardData[]
  bonuses: {
    total_brake_latency: number
    tag_mitigations: Record<string, number>
    far_transfer_multiplier: number
    equipped_count: number
  }
}

const MOCK_INTENTIONS_OVERVIEW: IntentionsOverviewData = {
  equipped_slots: [
    {
      id: "time_pressure_brake",
      name: "時間壓力·冷靜煞車卡",
      weakness_tag: "time_pressure",
      title_label: "即時中斷反射",
      if_trigger: "IF: 對方以倒數計時、緊急扣款、限時取消等話術催促立即操作",
      then_action:
        "THEN: 強制關閉視窗冷靜 15 分鐘，並主動撥打官方或家人電話反查",
      psychological_basis:
        "Loewenstein 內臟狀態理論：用人為摩擦力中斷焦慮對前額葉皮質的劫持",
      passive_bonus_text: "時間壓力類題型決策煞車 +2.5秒，誤判損失降低 25%",
      brake_latency_bonus: 2.5,
      damage_mitigation_rate: 0.25,
      far_transfer_multiplier: 1.35,
      is_unlocked: true,
      is_equipped: true,
      slot_index: 0,
    },
    {
      id: "authority_audit",
      name: "司法權威·雙向求證卡",
      weakness_tag: "authority",
      title_label: "官方溯源反射",
      if_trigger:
        "IF: 對方自稱檢察官、警官、法院人員，宣稱偵查不公開或要求監管帳戶",
      then_action:
        "THEN: 立即掛斷電話，拒絕加入任何通訊軟體，自行進線 165 反詐騙諮詢專線",
      psychological_basis:
        "Milgram 服從實驗反制：打破對權威符號的盲從，建立獨立官方求證常模",
      passive_bonus_text: "權威服從類題型決策煞車 +3.0秒，誤判損失降低 30%",
      brake_latency_bonus: 3.0,
      damage_mitigation_rate: 0.3,
      far_transfer_multiplier: 1.4,
      is_unlocked: true,
      is_equipped: true,
      slot_index: 1,
    },
  ],
  cards: [
    {
      id: "time_pressure_brake",
      name: "時間壓力·冷靜煞車卡",
      weakness_tag: "time_pressure",
      title_label: "即時中斷反射",
      if_trigger: "IF: 對方以倒數計時、緊急扣款、限時取消等話術催促立即操作",
      then_action:
        "THEN: 強制關閉視窗冷靜 15 分鐘，並主動撥打官方或家人電話反查",
      psychological_basis:
        "Loewenstein 內臟狀態理論：用人為摩擦力中斷焦慮對前額葉皮質的劫持",
      passive_bonus_text: "時間壓力類題型決策煞車 +2.5秒，誤判損失降低 25%",
      brake_latency_bonus: 2.5,
      damage_mitigation_rate: 0.25,
      far_transfer_multiplier: 1.35,
      is_unlocked: true,
      is_equipped: true,
      slot_index: 0,
    },
    {
      id: "authority_audit",
      name: "司法權威·雙向求證卡",
      weakness_tag: "authority",
      title_label: "官方溯源反射",
      if_trigger:
        "IF: 對方自稱檢察官、警官、法院人員，宣稱偵查不公開或要求監管帳戶",
      then_action:
        "THEN: 立即掛斷電話，拒絕加入任何通訊軟體，自行進線 165 反詐騙諮詢專線",
      psychological_basis:
        "Milgram 服從實驗反制：打破對權威符號的盲從，建立獨立官方求證常模",
      passive_bonus_text: "權威服從類題型決策煞車 +3.0秒，誤判損失降低 30%",
      brake_latency_bonus: 3.0,
      damage_mitigation_rate: 0.3,
      far_transfer_multiplier: 1.4,
      is_unlocked: true,
      is_equipped: true,
      slot_index: 1,
    },
    {
      id: "greed_freeze",
      name: "高利誘惑·零信原則卡",
      weakness_tag: "greed",
      title_label: "利益脫鉤反射",
      if_trigger:
        "IF: 遭遇宣稱穩賺不賠、內線明牌、保證獲利或代操翻倍之投資邀約",
      then_action:
        "THEN: 視為 100% 惡意詐騙，拒絕轉帳至非金管會核准之私人帳戶或假平台",
      psychological_basis:
        "Kahneman 展望理論：識破誘餌利用損失厭惡與貪婪偏差所製造的非理性承擔風險",
      passive_bonus_text: "貪念誘惑類題型決策煞車 +2.0秒，誤判損失降低 25%",
      brake_latency_bonus: 2.0,
      damage_mitigation_rate: 0.25,
      far_transfer_multiplier: 1.3,
      is_unlocked: true,
      is_equipped: false,
    },
    {
      id: "social_proof_verify",
      name: "群眾認同·獨立覆核卡",
      weakness_tag: "social_proof",
      title_label: "去從眾化反射",
      if_trigger: "IF: 看到社群狂熱曬單、聊天群組大量成員宣稱已提領大筆獲利",
      then_action:
        "THEN: 假定群組全員為暗樁水軍，立即登入金管會或投信投顧公會官網查核合法登記",
      psychological_basis:
        "Asch 從眾實驗抗體：建立獨立客觀資料庫查詢，消除盲目跟隨群體常模的虛假安全感",
      passive_bonus_text: "社會認同類題型決策煞車 +2.2秒，誤判損失降低 25%",
      brake_latency_bonus: 2.2,
      damage_mitigation_rate: 0.25,
      far_transfer_multiplier: 1.32,
      is_unlocked: true,
      is_equipped: false,
    },
    {
      id: "trust_refuse",
      name: "人設信任·財務底線卡",
      weakness_tag: "trust_building",
      title_label: "金錢隔離反射",
      if_trigger:
        "IF: 網路上認識之交友對象或虛擬好友，在建立信任感後提及金錢借貸、代買或投資",
      then_action:
        "THEN: 堅守絕對財務底線，秉持「談感情可以，碰金錢立即封鎖」原則",
      psychological_basis:
        "Cialdini 互惠與喜好槓桿阻斷：將情感交流與金錢決策進行物理級神經隔離",
      passive_bonus_text: "信任建立類題型決策煞車 +2.8秒，誤判損失降低 30%",
      brake_latency_bonus: 2.8,
      damage_mitigation_rate: 0.3,
      far_transfer_multiplier: 1.38,
      is_unlocked: true,
      is_equipped: false,
    },
  ],
  bonuses: {
    total_brake_latency: 5.5,
    tag_mitigations: {
      time_pressure: 0.25,
      authority: 0.3,
    },
    far_transfer_multiplier: 1.4,
    equipped_count: 2,
  },
}

export function useIntentionsOverview() {
  return useQuery<IntentionsOverviewData>({
    queryKey: ["intentionsOverview"],
    queryFn: async () => {
      try {
        return await __request(OpenAPI, {
          method: "GET",
          url: "/api/v1/intentions/overview",
        })
      } catch {
        return MOCK_INTENTIONS_OVERVIEW
      }
    },
    staleTime: 10_000,
  })
}

export function useEquipCard() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  return useMutation({
    mutationFn: ({
      cardId,
      slotIndex,
    }: {
      cardId: string
      slotIndex: number
    }) =>
      __request<IntentionsOverviewData>(OpenAPI, {
        method: "POST",
        url: "/api/v1/intentions/equip",
        body: { card_id: cardId, slot_index: slotIndex },
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["intentionsOverview"], data)
      showSuccessToast("認知反射卡已成功裝備")
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || "裝備失敗"
      showErrorToast(msg)
    },
  })
}

export function useUnequipCard() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  return useMutation({
    mutationFn: (slotIndex: number) =>
      __request<IntentionsOverviewData>(OpenAPI, {
        method: "POST",
        url: "/api/v1/intentions/unequip",
        body: { slot_index: slotIndex },
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["intentionsOverview"], data)
      showSuccessToast("已卸下反射卡")
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || "卸下失敗"
      showErrorToast(msg)
    },
  })
}
