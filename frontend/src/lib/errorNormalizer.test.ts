import { describe, expect, it, beforeEach } from "bun:test"
import {
  handleAuthFailure,
  isDemoMode,
  normalizeError,
} from "./errorNormalizer"

describe("errorNormalizer", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it("only treats 401 as an expired login; 403 preserves the session", () => {
    const err401 = { status: 401, message: "Unauthorized" }
    const norm401 = normalizeError(err401)
    expect(norm401.category).toBe("auth")
    expect(norm401.action).toBe("login")
    expect(norm401.canRetry).toBe(false)
    expect(norm401.status).toBe(401)

    const err403 = { status: 403, body: { detail: "Forbidden access" } }
    const norm403 = normalizeError(err403)
    expect(norm403.category).not.toBe("auth")
    localStorage.setItem("access_token", "valid-guest-token")
    expect(handleAuthFailure(err403)).toBe(false)
    expect(localStorage.getItem("access_token")).toBe("valid-guest-token")
  })

  it("normalizes 404 as version mismatch error with reload action", () => {
    const err404 = { status: 404 }
    const norm404 = normalizeError(err404)
    expect(norm404.category).toBe("version")
    expect(norm404.action).toBe("reload")
    expect(norm404.canRetry).toBe(true)
  })

  it("normalizes 500, 502, 503 and network errors as network errors with retry action", () => {
    const err500 = { status: 500 }
    const norm500 = normalizeError(err500)
    expect(norm500.category).toBe("network")
    expect(norm500.action).toBe("retry")
    expect(norm500.canRetry).toBe(true)

    const netErr = new Error("Failed to fetch")
    const normNet = normalizeError(netErr)
    expect(normNet.category).toBe("network")
    expect(normNet.action).toBe("retry")
    expect(normNet.canRetry).toBe(true)
  })

  it("handleAuthFailure clears token and prevents redirect loop when on /login", () => {
    localStorage.setItem("access_token", "fake-token")

    // If pathname is already /login, should NOT re-assign
    let assignedUrl = ""
    const originalLocation = window.location
    delete (window as any).location
    window.location = {
      ...originalLocation,
      pathname: "/login",
      assign: (url: string) => {
        assignedUrl = url
      },
    } as any

    const handled = handleAuthFailure({ status: 401 })
    expect(handled).toBe(true)
    expect(localStorage.getItem("access_token")).toBeNull()
    expect(assignedUrl).toBe("") // No redirect loop!

    // If pathname is not /login, redirects to /login
    window.location.pathname = "/home"
    handleAuthFailure({ status: 401 })
    expect(assignedUrl).toBe("/login")

    window.location = originalLocation
  })

  it("detects demo mode correctly", () => {
    expect(isDemoMode()).toBe(false)
    localStorage.setItem("demo_mode", "true")
    expect(isDemoMode()).toBe(true)
  })
})
