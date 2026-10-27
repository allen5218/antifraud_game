import { expect, test } from "bun:test"
import { signupSchema, toSignupBody } from "./signupForm"

const base = {
  email: "a@example.com",
  full_name: "王老師",
  password: "password1",
  confirm_password: "password1",
  teacher: false,
  school: "",
  subject: "",
}

test("沒勾老師不用填學校科目，送出也不帶 teacher", () => {
  const parsed = signupSchema.safeParse(base)
  expect(parsed.success).toBe(true)
  expect(toSignupBody(base)).toEqual({
    email: "a@example.com",
    full_name: "王老師",
    password: "password1",
  })
})

test("勾了老師，學校與任教科目必填", () => {
  const parsed = signupSchema.safeParse({ ...base, teacher: true, school: " " })
  expect(parsed.success).toBe(false)
  const paths = parsed.error?.issues.map((i) => i.path.join(".")) ?? []
  expect(paths).toContain("school")
  expect(paths).toContain("subject")
})

test("勾了老師，送出帶 teacher 並去掉頭尾空白", () => {
  const data = {
    ...base,
    teacher: true,
    school: " 範例國中 ",
    subject: "公民 ",
  }
  expect(signupSchema.safeParse(data).success).toBe(true)
  expect(toSignupBody(data)).toEqual({
    email: "a@example.com",
    full_name: "王老師",
    password: "password1",
    teacher: { school: "範例國中", subject: "公民" },
  })
})
