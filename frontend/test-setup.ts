import { GlobalRegistrator } from "@happy-dom/global-registrator"

GlobalRegistrator.register()

const { afterEach } = await import("bun:test")
const { cleanup } = await import("@testing-library/react")

afterEach(() => {
  cleanup()
})

