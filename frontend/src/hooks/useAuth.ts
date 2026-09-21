import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  type Body_login_login_access_token as AccessToken,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from "@/client"
import { isDemoMode } from "@/lib/errorNormalizer"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  if (localStorage.getItem("access_token") === "demo_token_123") {
    localStorage.removeItem("access_token")
    localStorage.removeItem("demo_mode")
  }
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: async () => {
      try {
        return await UsersService.readUserMe()
      } catch (err) {
        if (isDemoMode()) {
          return {
            id: "demo_user_id",
            email: "demo@antifraud.game",
            full_name: "反詐玩家 (本機體驗)",
            is_active: true,
            is_superuser: false,
          } as any
        }
        throw err
      }
    },
    enabled: isLoggedIn(),
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      formData: data,
    })
    localStorage.setItem("access_token", response.access_token)
    localStorage.removeItem("demo_mode")
    queryClient.clear()
  }

  const guestMutation = useMutation({
    mutationFn: async () => {
      const response = await LoginService.loginGuest()
      localStorage.removeItem("demo_mode")
      localStorage.setItem("access_token", response.access_token)
      queryClient.clear()
    },
    onSuccess: () => { navigate({ to: "/" }) },
    onError: handleError.bind(showErrorToast),
  })

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("demo_mode")
    queryClient.clear()
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    loginMutation,
    guestMutation,
    logout,
    user,
  }
}

export { isLoggedIn }
export default useAuth
