import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { OpenAPI } from "@/client/core/OpenAPI"
import { request as __request } from "@/client/core/request"
import useCustomToast from "./useCustomToast"

export interface SkillNodeData {
  id: string
  name: string
  category: "洞察" | "查核" | "護盾" | "槓桿" | "話術"
  level: number
  max_level: number
  sp_cost: number
  description: string
  bonus_text: string
  icon_type: "eye" | "search" | "shield" | "trending" | "git-fork"
}

export interface SkillOverviewData {
  available_sp: number
  total_sp: number
  spent_sp: number
  skills: SkillNodeData[]
}

const MOCK_SKILLS_OVERVIEW: SkillOverviewData = {
  available_sp: 2,
  total_sp: 4,
  spent_sp: 2,
  skills: [
    {
      id: "insight_1",
      name: "敏銳洞察",
      category: "洞察",
      level: 1,
      max_level: 3,
      sp_cost: 1,
      description:
        "在快問快答與題組訓練中，提高作答連勝帶來的現金與經驗值獎勵倍率。",
      bonus_text: "作答連勝獎勵 +10%",
      icon_type: "eye",
    },
    {
      id: "audit_1",
      name: "情境查核",
      category: "查核",
      level: 1,
      max_level: 3,
      sp_cost: 1,
      description: "在情境查證中，提高解鎖關鍵證據時獲得的破案分紅。",
      bonus_text: "查證解鎖現金 +10%",
      icon_type: "search",
    },
    {
      id: "shield_1",
      name: "防禦護盾",
      category: "護盾",
      level: 0,
      max_level: 3,
      sp_cost: 1,
      description: "在情境破案判斷失誤或遭詐騙時，減免資產損失。",
      bonus_text: "誤判虧損減免 25%",
      icon_type: "shield",
    },
    {
      id: "yield_1",
      name: "槓桿增益",
      category: "槓桿",
      level: 0,
      max_level: 3,
      sp_cost: 1,
      description: "提升名下所有房產的每日被動收益比例。",
      bonus_text: "房產每日收益 +15%",
      icon_type: "trending",
    },
    {
      id: "negotiation_1",
      name: "說服話術",
      category: "話術",
      level: 0,
      max_level: 3,
      sp_cost: 1,
      description: "情境對話順利完成或安全撤退時，獲得額外經驗值。",
      bonus_text: "破案經驗值 +30%",
      icon_type: "git-fork",
    },
  ],
}

export function useSkillsOverview() {
  return useQuery<SkillOverviewData>({
    queryKey: ["skillsOverview"],
    queryFn: async () => {
      try {
        return await __request(OpenAPI, {
          method: "GET",
          url: "/api/v1/skills/overview",
        })
      } catch {
        return MOCK_SKILLS_OVERVIEW
      }
    },
    staleTime: 10_000,
  })
}

export function useUpgradeSkill() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  return useMutation({
    mutationFn: (skillId: string) =>
      __request<SkillOverviewData>(OpenAPI, {
        method: "POST",
        url: "/api/v1/skills/upgrade",
        body: { skill_id: skillId },
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["skillsOverview"], data)
      queryClient.invalidateQueries({ queryKey: ["economyMe"] })
      showSuccessToast("天賦技能升級成功")
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || "升級失敗，點數不足或已達上限"
      showErrorToast(msg)
    },
  })
}

export function useResetSkills() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  return useMutation({
    mutationFn: () =>
      __request<SkillOverviewData>(OpenAPI, {
        method: "POST",
        url: "/api/v1/skills/reset",
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["skillsOverview"], data)
      queryClient.invalidateQueries({ queryKey: ["economyMe"] })
      showSuccessToast("技能點數已重置，退回所有天賦點數")
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || "重置失敗，現金不足 500 元"
      showErrorToast(msg)
    },
  })
}
