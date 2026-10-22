import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { TeamService } from "@/client"

export type TeamItemKind = "pretest" | "swipe" | "case" | "question" | "persona"

export const TEAM_BANK_KEY = ["team", "bank"] as const

export const teamBankQuery = queryOptions({
  queryKey: TEAM_BANK_KEY,
  queryFn: () => TeamService.readBank(),
  staleTime: 60_000,
  retry: false,
})

export function useTeamBank() {
  return useQuery(teamBankQuery)
}

function commentsKey(kind: TeamItemKind, key: string) {
  return ["team", "comments", kind, key] as const
}

export function useTeamComments(
  kind: TeamItemKind,
  key: string,
  enabled: boolean,
) {
  return useQuery({
    queryKey: commentsKey(kind, key),
    queryFn: () => TeamService.listComments({ itemKind: kind, itemKey: key }),
    enabled,
    retry: false,
  })
}

/** 留言或刪留言後，那一題的討論和題庫上的留言數都要重讀 */
function useRefreshComments(kind: TeamItemKind, key: string) {
  const qc = useQueryClient()
  return () => {
    qc.invalidateQueries({ queryKey: commentsKey(kind, key) })
    qc.invalidateQueries({ queryKey: TEAM_BANK_KEY })
  }
}

export function useCreateTeamComment(kind: TeamItemKind, key: string) {
  const refresh = useRefreshComments(kind, key)
  return useMutation({
    mutationFn: (body: string) =>
      TeamService.createComment({
        requestBody: { item_kind: kind, item_key: key, body },
      }),
    onSuccess: refresh,
  })
}

export function useDeleteTeamComment(kind: TeamItemKind, key: string) {
  const refresh = useRefreshComments(kind, key)
  return useMutation({
    mutationFn: (commentId: string) => TeamService.deleteComment({ commentId }),
    onSuccess: refresh,
  })
}
