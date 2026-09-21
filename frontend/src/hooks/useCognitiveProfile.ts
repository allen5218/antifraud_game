import { useQuery } from "@tanstack/react-query"
import { OpenAPI } from "@/client/core/OpenAPI"
import { request as __request } from "@/client/core/request"

export interface CognitiveProfileData {
  d_prime: number
  criterion_c: number
  bias_profile: "balanced" | "credulous" | "paranoid"
  immunity_score: number
  total_cases_analyzed: number
  radar_scores: {
    authority: number
    greed: number
    social_proof: number
    time_pressure: number
    trust_building: number
  }
}

export function useCognitiveProfile() {
  return useQuery<CognitiveProfileData>({
    queryKey: ["cognitiveProfile"],
    queryFn: () =>
      __request(OpenAPI, {
        method: "GET",
        url: "/api/v1/users/me/cognitive-profile",
      }),
  })
}
