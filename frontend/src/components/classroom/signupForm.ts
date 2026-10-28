import { z } from "zod"
import type { UserRegister } from "@/client"

/** 註冊表單：勾「我是老師」才要填學校與任教科目（送出後是審核中，管理員核准才算老師） */
export const signupSchema = z
  .object({
    email: z.email({ message: "電子郵件格式不正確" }),
    full_name: z.string().min(1, { message: "請輸入名稱" }),
    password: z
      .string()
      .min(1, { message: "請輸入密碼" })
      .min(8, { message: "密碼至少要 8 個字元" }),
    confirm_password: z.string().min(1, { message: "請再輸入一次密碼" }),
    teacher: z.boolean(),
    school: z.string().max(100),
    subject: z.string().max(100),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "兩次輸入的密碼不一樣",
    path: ["confirm_password"],
  })
  .superRefine((data, ctx) => {
    if (!data.teacher) return
    if (!data.school.trim())
      ctx.addIssue({ code: "custom", message: "請輸入學校", path: ["school"] })
    if (!data.subject.trim())
      ctx.addIssue({
        code: "custom",
        message: "請輸入任教科目",
        path: ["subject"],
      })
  })

export type SignupForm = z.infer<typeof signupSchema>

export function toSignupBody(data: SignupForm): UserRegister {
  const body: UserRegister = {
    email: data.email,
    full_name: data.full_name,
    password: data.password,
  }
  if (data.teacher)
    body.teacher = { school: data.school.trim(), subject: data.subject.trim() }
  return body
}
