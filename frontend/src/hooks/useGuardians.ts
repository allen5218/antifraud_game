import { useQuery } from "@tanstack/react-query"
import { OpenAPI } from "@/client/core/OpenAPI"
import { request as __request } from "@/client/core/request"

export interface GuardianNpcData {
  id: string
  name: string
  title: string
  avatar: string
  background: string
  trust_score: number
  level: number
  cases_protected: number
  unlocked_letters: string[]
}

export interface GuardiansOverviewData {
  total_protected_cases: number
  guardians: GuardianNpcData[]
}

const MOCK_GUARDIANS_OVERVIEW: GuardiansOverviewData = {
  total_protected_cases: 4,
  guardians: [
    {
      id: "grandma_chen",
      name: "陳林秀琴 阿嬤 (72歲)",
      title: "鄰里互助會榮譽長輩",
      avatar: "/assets/images/guardians/grandma_chen.jpg",
      background:
        "獨居眷村，每月倚賴微薄津貼生活。曾在假檢警詐騙中險遭提領全部積蓄，目前在社區擔任志工。",
      trust_score: 75,
      level: 2,
      cases_protected: 2,
      unlocked_letters: [
        "謝謝搜查官大人上次及時提醒我... 那通電話差點把我和老伴幾十年的積蓄全騙光。這是我自己醃漬的梅子，請務必收下！",
      ],
    },
    {
      id: "student_zhiming",
      name: "林志明 (20歲)",
      title: "大二工讀生",
      avatar: "/assets/images/guardians/student_zhiming.jpg",
      background:
        "半工半讀繳學費與生活費，對科技熟悉但對求職兼職與租屋陷阱缺乏警覺心。",
      trust_score: 45,
      level: 1,
      cases_protected: 1,
      unlocked_letters: [
        "搜查官，真的太感謝你了！差點就把存摺跟提款卡寄給那個假博弈客服，要不是你識破，我現在可能成了詐騙人頭帳戶...",
      ],
    },
    {
      id: "single_mother_yating",
      name: "張雅婷 (36歲)",
      title: "單親媽媽與個人工作室接案者",
      avatar: "/assets/images/guardians/single_mother_yating.jpg",
      background:
        "獨自撫養幼兒園女兒，日常開銷緊湊，對快速回本理財與網購代工投資抱有極大期待。",
      trust_score: 30,
      level: 1,
      cases_protected: 1,
      unlocked_letters: [],
    },
  ],
}

export function useGuardiansOverview() {
  return useQuery<GuardiansOverviewData>({
    queryKey: ["guardiansOverview"],
    queryFn: async () => {
      try {
        return await __request(OpenAPI, {
          method: "GET",
          url: "/api/v1/guardians/overview",
        })
      } catch {
        return MOCK_GUARDIANS_OVERVIEW
      }
    },
    staleTime: 10_000,
  })
}
