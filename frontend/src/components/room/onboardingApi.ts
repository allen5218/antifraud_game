import { OnboardingService } from "@/client/sdk.gen"

// 元件經過這一層呼叫 API，測試 spy 這個物件（和 classroomApi、shop/mascotApi 同一種寫法）
export const onboardingApi = {
  tourDone: () => OnboardingService.tourDone(),
  shopVisited: () => OnboardingService.shopVisited(),
  claim: () => OnboardingService.claimReward(),
}
