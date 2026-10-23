import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { TrialService } from "@/client"
import { HOME_SUMMARY_KEY } from "@/hooks/useHomeSummary"

export const TRIAL_SURVEY_KEY = ["trial", "survey"] as const

export const trialSurveyQuery = queryOptions({
  queryKey: TRIAL_SURVEY_KEY,
  queryFn: () => TrialService.readSurvey(),
  retry: false,
})

export function useTrialSurvey() {
  return useQuery(trialSurveyQuery)
}

/** 開始計時。只在問卷頁打開時呼叫，不能放進 loader（預先載入就會開始計時） */
export function useStartTrialSurvey() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => TrialService.startSurvey(),
    onSuccess: (data) => qc.setQueryData(TRIAL_SURVEY_KEY, data),
  })
}

export function useSubmitTrialSurvey() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (answers: Record<string, unknown>) =>
      TrialService.submitSurvey({ requestBody: { answers } }),
    onSuccess: (data) => {
      qc.setQueryData(TRIAL_SURVEY_KEY, data)
      qc.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
    },
  })
}
