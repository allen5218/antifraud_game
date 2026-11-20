import { describe, expect, test } from "bun:test"
import { fireEvent, render } from "@testing-library/react"
import { CardArt } from "./CardArt"

const layers = (container: HTMLElement, layer: string) =>
  [...container.querySelectorAll(`image[data-layer="${layer}"]`)].map((el) =>
    el.getAttribute("href"),
  )

describe("CardArt", () => {
  test("場景墊底，角色和道具疊上去", () => {
    const { container } = render(
      <CardArt
        scene="street"
        cast={["grandma"]}
        props={["phone"]}
        pose="worried"
      />,
    )
    expect(layers(container, "scene")).toEqual([
      "/assets/cast/scenes/street.svg",
    ])
    expect(layers(container, "cast")).toEqual([
      "/assets/cast/cast/grandma/worried.svg",
    ])
    expect(layers(container, "prop")).toEqual(["/assets/cast/props/phone.svg"])
    // 場景在最底下：第一個 image 就是場景
    expect(container.querySelector("image")?.getAttribute("data-layer")).toBe(
      "scene",
    )
  })

  test("pose 只套主角，也可以用 id:pose 個別指定", () => {
    const { container } = render(
      <CardArt
        scene="living-room"
        cast={["grandma", "fake-cs:talking-phone", "police"]}
        pose="suspicious"
      />,
    )
    expect(layers(container, "cast")).toEqual([
      "/assets/cast/cast/grandma/suspicious.svg",
      "/assets/cast/cast/fake-cs/talking-phone.svg",
      "/assets/cast/cast/police/neutral.svg",
    ])
  })

  test("清單外的 id 不畫，姿勢不認得就用 neutral", () => {
    const { container } = render(
      <CardArt
        scene="moon"
        cast={["alien", "grandpa"]}
        props={["rocket"]}
        pose="flying"
      />,
    )
    expect(layers(container, "scene")).toEqual([])
    expect(layers(container, "cast")).toEqual([
      "/assets/cast/cast/grandpa/neutral.svg",
    ])
    expect(layers(container, "prop")).toEqual([])
    // 還是有底色，不會整塊空掉
    expect(
      container.querySelector("rect[data-layer='backdrop']"),
    ).not.toBeNull()
  })

  test("圖片載入失敗的那一層藏起來，其他照常", () => {
    const { container } = render(
      <CardArt scene="shop" cast={["seller"]} props={["parcel"]} />,
    )
    const scene = container.querySelector('image[data-layer="scene"]')!
    fireEvent.error(scene)
    expect(layers(container, "scene")).toEqual([])
    expect(layers(container, "cast")).toEqual([
      "/assets/cast/cast/seller/neutral.svg",
    ])
    expect(layers(container, "prop")).toEqual(["/assets/cast/props/parcel.svg"])
  })

  test("第二個人鏡像，面向主角", () => {
    const { container } = render(
      <CardArt scene="shop" cast={["seller", "buyer"]} />,
    )
    const [first, second] = container.querySelectorAll(
      'image[data-layer="cast"]',
    )
    expect(first.getAttribute("transform")).toBeNull()
    expect(second.getAttribute("transform")).toContain("scale(-1 1)")
  })

  test("手機螢幕場景會把主角裁進螢幕裡", () => {
    const { container } = render(
      <CardArt scene="phone-screen" cast={["police"]} />,
    )
    const clipped = container.querySelector(
      "g[clip-path] image[data-layer='cast']",
    )
    expect(clipped?.getAttribute("href")).toBe(
      "/assets/cast/cast/police/neutral.svg",
    )
    const id = container
      .querySelector("g[clip-path]")
      ?.getAttribute("clip-path")
      ?.match(/url\(#(.+)\)/)?.[1]
    expect(id).toBeTruthy()
    expect(container.querySelector(`clipPath[id="${id}"]`)).not.toBeNull()
  })

  test("沒給 label 時是裝飾圖，給了就是有名字的圖片", () => {
    const { container, rerender } = render(<CardArt scene="office" />)
    const svg = () => container.querySelector("svg")!
    expect(svg().getAttribute("aria-hidden")).toBe("true")
    rerender(<CardArt scene="office" label="阿嬤在客廳接電話" />)
    expect(svg().getAttribute("role")).toBe("img")
    expect(svg().getAttribute("aria-label")).toBe("阿嬤在客廳接電話")
    expect(svg().getAttribute("aria-hidden")).toBeNull()
  })
})
