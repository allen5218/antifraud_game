import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { Body_login_login_access_token as AccessToken } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import { LineAuthButton } from "@/components/Common/LineAuthButton"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"

const formSchema = z.object({
  username: z.email(),
  password: z
    .string()
    .min(1, { message: "Password is required" })
    .min(8, { message: "Password must be at least 8 characters" }),
}) satisfies z.ZodType<AccessToken>

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "登入 - 反詐大師",
      },
    ],
  }),
})

function Login() {
  const { loginMutation, guestMutation } = useAuth()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })

  const onSubmit = (data: FormData) => {
    if (loginMutation.isPending) return
    loginMutation.mutate(data)
  }

  return (
    <AuthLayout>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-6"
        >
          <div className="flex flex-col space-y-1 text-left mb-1">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              探員登入
            </h1>
            <p className="text-xs text-slate-400">
              登入防詐思維訓練總部，或以 LINE 官方帳號一秒通關
            </p>
          </div>

          <LineAuthButton mode="login" />

          <div className="relative flex items-center justify-center my-1">
            <div className="border-t border-slate-800 w-full" />
            <span className="bg-slate-950 px-3 text-[11px] text-slate-500 uppercase tracking-wider relative z-10">
              或以帳號密碼登入
            </span>
          </div>

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-xs font-semibold text-slate-300">
                    電子信箱
                  </FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder="user@example.com"
                      type="email"
                      className="bg-slate-900/80 border-slate-700/80 text-white placeholder:text-slate-500 focus:border-slate-400 focus:ring-slate-400 rounded-xl"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs text-red-400" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center">
                    <FormLabel className="text-xs font-semibold text-slate-300">
                      密碼
                    </FormLabel>
                    <RouterLink
                      to="/recover-password"
                      className="ml-auto text-xs font-medium text-slate-400 underline-offset-4 hover:underline hover:text-white"
                    >
                      忘記密碼?
                    </RouterLink>
                  </div>
                  <FormControl>
                    <PasswordInput
                      data-testid="password-input"
                      placeholder="••••••••"
                      className="bg-slate-900/80 border-slate-700/80 text-white placeholder:text-slate-500 focus:border-slate-400 focus:ring-slate-400 rounded-xl"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs text-red-400" />
                </FormItem>
              )}
            />

            <LoadingButton
              type="submit"
              loading={loginMutation.isPending}
              className="w-full py-2.5 bg-white hover:bg-slate-200 text-slate-950 font-bold rounded-xl shadow-md transition-all cursor-pointer"
            >
              登入
            </LoadingButton>

            <button
              type="button"
              onClick={() => guestMutation.mutate()}
              disabled={guestMutation.isPending}
              className="w-full py-2.5 px-4 bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white font-medium rounded-xl border border-slate-700/80 transition-all flex items-center justify-center gap-2 text-xs cursor-pointer"
            >
              {guestMutation.isPending ? "正在進入…" : "免登入，開始遊戲"}
            </button>
          </div>

          <div className="text-center text-sm text-slate-400">
            還沒有帳號?{" "}
            <RouterLink
              to="/signup"
              className="text-white font-medium underline underline-offset-4 hover:text-slate-300"
            >
              註冊
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
