import { useRegisterSW } from "virtual:pwa-register/react"
import { useEffect, useState } from "react"
import { toast } from "sonner"

const UPDATE_INTERVAL = 60 * 60 * 1000
const TOAST_ID = "pwa-update"

export function UpdatePrompt() {
  const [registration, setRegistration] = useState<
    ServiceWorkerRegistration | undefined
  >()
  const {
    needRefresh: [needRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(_swUrl, registered) {
      setRegistration(registered)
    },
  })

  useEffect(() => {
    if (!registration) return

    const interval = window.setInterval(() => {
      if (!navigator.onLine || registration.installing) return
      void registration.update().catch((error) => {
        console.error("檢查新版本失敗", error)
      })
    }, UPDATE_INTERVAL)

    return () => window.clearInterval(interval)
  }, [registration])

  useEffect(() => {
    if (!needRefresh) return

    toast("有新版本", {
      id: TOAST_ID,
      duration: Number.POSITIVE_INFINITY,
      closeButton: false,
      dismissible: false,
      action: {
        label: "重新整理",
        onClick: () => {
          void updateServiceWorker(true)
        },
      },
    })

    return () => {
      toast.dismiss(TOAST_ID)
    }
  }, [needRefresh, updateServiceWorker])

  return null
}
