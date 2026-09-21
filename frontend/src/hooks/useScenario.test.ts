import { afterEach, beforeEach, describe, expect, it, mock } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, renderHook, waitFor } from "@testing-library/react"
import React from "react"
import { ScenarioService } from "@/client"
import {
  useExecuteAction,
  useJudge,
  useNewScenario,
  usePauseScenario,
  usePurchaseItem,
  useResumeScenario,
  useScenario,
  useSendMessage,
  useVerifyScenario,
} from "./useScenario"

afterEach(cleanup)

describe("useScenario hooks lifecycle", () => {
  let queryClient: QueryClient

  const createWrapper = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(
        QueryClientProvider,
        { client: queryClient },
        children,
      )
  }

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
  })

  it("useScenario fetches and returns scenario detail", async () => {
    const mockDetail = {
      id: "sc-100",
      contact_id: "wei_jie",
      display_name: "薇姐",
      status: "active",
      revision: 1,
      player_turns: 0,
      max_turns: 10,
      history: [],
      available_branch_actions: [
        {
          action_id: "check_personal_records",
          label: "自查紀錄",
          category: "network",
          description: "自查紀錄說明",
          is_available: true,
        },
      ],
    }

    const readMock = mock(async () => mockDetail as any)
    ScenarioService.readScenario = readMock

    const { result } = renderHook(() => useScenario("sc-100"), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(readMock).toHaveBeenCalledWith({ scenarioId: "sc-100" })
    expect(result.current.data?.id).toBe("sc-100")
    expect(result.current.data?.available_branch_actions?.length).toBe(1)
  })

  it("useSendMessage sends message with structured CAS revision and request_id", async () => {
    const sendMock = mock(
      async () =>
        ({
          message: "收到，我們來看看",
          history: [],
          turns_left: 9,
          revision: 2,
        }) as any,
    )
    ScenarioService.sendMessage = sendMock

    const wrapper = createWrapper()
    const invalidateSpy = mock(() => Promise.resolve())
    queryClient.invalidateQueries = invalidateSpy

    const { result } = renderHook(() => useSendMessage("sc-100"), { wrapper })

    result.current.mutate({
      text: "可以先不要匯嗎？",
      expectedRevision: 1,
      requestId: "msg-req-1",
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(sendMock).toHaveBeenCalledWith({
      scenarioId: "sc-100",
      requestBody: {
        text: "可以先不要匯嗎？",
        expected_revision: 1,
        request_id: "msg-req-1",
      },
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["scenario", "sc-100"],
    })
  })

  it("useSendMessage handles revision mismatch 409 error", async () => {
    const conflictErr = new Error("Revision mismatch")
    ;(conflictErr as any).status = 409
    ;(conflictErr as any).body = { detail: { code: "revision_mismatch" } }

    ScenarioService.sendMessage = mock(async () => {
      throw conflictErr
    })

    const wrapper = createWrapper()
    const { result } = renderHook(() => useSendMessage("sc-100"), { wrapper })

    result.current.mutate({
      text: "測試訊息",
      expectedRevision: 0,
      requestId: "msg-req-conflict",
    })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect((result.current.error as any)?.status).toBe(409)
  })

  it("useExecuteAction executes branch action and invalidates scenario and economy", async () => {
    const actionMock = mock(
      async () =>
        ({
          action_id: "high_cash_collateral",
          action_label: "提存大額保證金",
          action_result: "已前往約定處所提存",
          cost_cash: 5000,
          revision: 3,
          conversation_history: [],
        }) as any,
    )
    ScenarioService.performScenarioAction = actionMock

    const wrapper = createWrapper()
    const invalidateSpy = mock(() => Promise.resolve())
    queryClient.invalidateQueries = invalidateSpy

    const { result } = renderHook(() => useExecuteAction("sc-100"), { wrapper })

    result.current.mutate({
      actionId: "high_cash_collateral",
      expectedRevision: 2,
      requestId: "act-req-1",
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(actionMock).toHaveBeenCalledWith({
      scenarioId: "sc-100",
      requestBody: {
        action_id: "high_cash_collateral",
        expected_revision: 2,
        request_id: "act-req-1",
      },
    })
    // Invalidates both scenario and economy cache
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["scenario", "sc-100"],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["economy"] })
  })

  it("useVerifyScenario runs independent verification tool", async () => {
    const verifyMock = mock(
      async () =>
        ({
          tool_id: "check_official_registry",
          tool_name: "主管機關登記名冊",
          title: "官方查核結果",
          content: "【遊戲模擬查證】查無特許營業登記",
          revision: 2,
        }) as any,
    )
    ScenarioService.verifyScenario = verifyMock

    const wrapper = createWrapper()
    const invalidateSpy = mock(() => Promise.resolve())
    queryClient.invalidateQueries = invalidateSpy

    const { result } = renderHook(() => useVerifyScenario("sc-100"), {
      wrapper,
    })

    result.current.mutate({
      toolId: "check_official_registry",
      expectedRevision: 1,
      requestId: "ver-req-1",
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(verifyMock).toHaveBeenCalledWith({
      scenarioId: "sc-100",
      requestBody: {
        tool_id: "check_official_registry",
        expected_revision: 1,
        request_id: "ver-req-1",
      },
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["scenario", "sc-100"],
    })
  })

  it("usePauseScenario and useResumeScenario manage lifecycle and invalidate inbox", async () => {
    const pauseMock = mock(
      async () =>
        ({
          scenario_id: "sc-100",
          status: "paused",
          is_paused: true,
          revision: 2,
        }) as any,
    )
    const resumeMock = mock(
      async () =>
        ({
          scenario_id: "sc-100",
          status: "active",
          is_paused: false,
          revision: 3,
        }) as any,
    )
    ScenarioService.pauseScenario = pauseMock
    ScenarioService.resumeScenario = resumeMock

    const wrapper = createWrapper()
    const invalidateSpy = mock(() => Promise.resolve())
    queryClient.invalidateQueries = invalidateSpy

    // Test Pause
    const { result: pauseHook } = renderHook(() => usePauseScenario("sc-100"), {
      wrapper,
    })
    pauseHook.current.mutate({
      expectedRevision: 1,
      requestId: "pause-req-1",
    })
    await waitFor(() => expect(pauseHook.current.isSuccess).toBe(true))
    expect(pauseMock).toHaveBeenCalledWith({
      scenarioId: "sc-100",
      requestBody: {
        expected_revision: 1,
        request_id: "pause-req-1",
      },
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["scenario", "sc-100"],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["scenario", "inbox"],
    })

    // Test Resume
    const { result: resumeHook } = renderHook(
      () => useResumeScenario("sc-100"),
      { wrapper },
    )
    resumeHook.current.mutate({
      expectedRevision: 2,
      requestId: "resume-req-1",
    })
    await waitFor(() => expect(resumeHook.current.isSuccess).toBe(true))
    expect(resumeMock).toHaveBeenCalledWith({
      scenarioId: "sc-100",
      requestBody: {
        expected_revision: 2,
        request_id: "resume-req-1",
      },
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["scenario", "sc-100"],
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["scenario", "inbox"],
    })
  })

  it("useJudge executes cautious terminal disposition (safe_exit) and invalidates economy/scenario", async () => {
    const judgeMock = mock(
      async () =>
        ({
          scenario_id: "sc-100",
          status: "completed",
          outcome: "safe_exit",
          true_role: "pause_pending",
          persona_name: "老舊公寓房東",
          cash_delta: 0,
          xp_delta: 60,
          flags: [],
          reward_breakdown: {
            base_cash: 0,
            chapter_multiplier: 1.0,
            chapter_level: 1,
            is_chapter_finale: false,
            total_chat_factor: 1.2,
            is_replay: false,
            factors: { service_objective: true },
          },
          triggers_forced_sell: false,
        }) as any,
    )
    ScenarioService.judgeScenario = judgeMock

    const wrapper = createWrapper()
    const invalidateSpy = mock(() => Promise.resolve())
    queryClient.invalidateQueries = invalidateSpy

    const { result } = renderHook(() => useJudge("sc-100"), { wrapper })

    result.current.mutate({
      action: "safe_exit",
      expectedRevision: 3,
      requestId: "judge-req-1",
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(judgeMock).toHaveBeenCalledWith({
      scenarioId: "sc-100",
      requestBody: {
        action: "safe_exit",
        expected_revision: 3,
        request_id: "judge-req-1",
      },
    })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["economy"] })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["scenario"] })
  })

  it("useNewScenario and usePurchaseItem trigger expected mutations and cache invalidations", async () => {
    const createMock = mock(
      async () =>
        ({
          id: "sc-new-1",
          contact_id: "li_li",
          fraud_type: "shopping",
          status: "active",
        }) as any,
    )
    ScenarioService.createScenario = createMock

    const purchaseMock = mock(
      async () =>
        ({
          success: true,
          item_id: "dashcam",
          user_cash: 8000,
        }) as any,
    )
    ScenarioService.purchaseItem = purchaseMock

    const wrapper = createWrapper()
    const invalidateSpy = mock(() => Promise.resolve())
    queryClient.invalidateQueries = invalidateSpy

    // Create scenario
    const { result: newHook } = renderHook(() => useNewScenario(), { wrapper })
    newHook.current.mutate({
      contactId: "li_li",
      fraudType: "shopping",
      requestId: "create-req-1",
    })
    await waitFor(() => expect(newHook.current.isSuccess).toBe(true))
    expect(createMock).toHaveBeenCalledWith({
      requestBody: {
        contact_id: "li_li",
        fraud_type: "shopping",
        story_id: undefined,
        request_id: "create-req-1",
      },
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["scenario", "inbox"],
    })

    // Purchase item
    const { result: purchaseHook } = renderHook(() => usePurchaseItem(), {
      wrapper,
    })
    purchaseHook.current.mutate({
      itemId: "dashcam",
      requestId: "buy-req-1",
    })
    await waitFor(() => expect(purchaseHook.current.isSuccess).toBe(true))
    expect(purchaseMock).toHaveBeenCalledWith({
      requestBody: {
        item_id: "dashcam",
        request_id: "buy-req-1",
      },
    })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["economy"] })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["scenario"] })
  })
})
