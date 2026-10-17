import { describe, expect, it } from "bun:test"
import { QueryClient } from "@tanstack/react-query"
import { refreshAfterPropertyChange } from "./useEconomy"

describe("refreshAfterPropertyChange", () => {
  it("also refreshes the room, whose look follows the best property", () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(["economy", "me"], { cash: 0 })
    queryClient.setQueryData(["home-summary"], { room_stage: 0 })

    refreshAfterPropertyChange(queryClient)

    expect(queryClient.getQueryState(["economy", "me"])?.isInvalidated).toBe(
      true,
    )
    expect(queryClient.getQueryState(["home-summary"])?.isInvalidated).toBe(
      true,
    )
  })
})
