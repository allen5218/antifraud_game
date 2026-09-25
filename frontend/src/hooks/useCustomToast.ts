import { toast } from "sonner"

const useCustomToast = () => {
  const showSuccessToast = (description: string) => {
    toast.success("完成", {
      description,
    })
  }

  const showErrorToast = (description: string) => {
    toast.error("沒有成功", {
      description,
    })
  }

  return { showSuccessToast, showErrorToast }
}

export default useCustomToast
