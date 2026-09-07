import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { SwipeFeedback } from "./SwipeFeedback"

afterEach(cleanup)

describe("<SwipeFeedback />", () => {
  it("shows backend-provided weakness labels and suggestions without raw tags", () => {
    render(
      <SwipeFeedback
        correct={false}
        explanation="這是常見的冒用權威話術。"
        weaknessDetails={[
          {
            tag: "authority",
            label: "權威服從",
            suggestion: "主動查證對方身份",
          },
        ]}
      />,
    )

    expect(screen.getByText("權威服從")).toBeTruthy()
    expect(screen.getByText("主動查證對方身份")).toBeTruthy()
    expect(screen.queryByText("authority")).toBeNull()
  })
})
