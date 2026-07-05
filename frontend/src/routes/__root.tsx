import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { createRootRoute, HeadContent, Outlet } from "@tanstack/react-router"
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools"
import ErrorComponent from "@/components/Common/ErrorComponent"
import NotFound from "@/components/Common/NotFound"

export const Route = createRootRoute({
  component: () => {
    const showDevtools = import.meta.env.DEV && !navigator.webdriver

    return (
      <>
        <HeadContent />
        <Outlet />
        {showDevtools && (
          <>
            <TanStackRouterDevtools position="bottom-right" />
            <ReactQueryDevtools initialIsOpen={false} />
          </>
        )}
      </>
    )
  },
  notFoundComponent: () => <NotFound />,
  errorComponent: () => <ErrorComponent />,
})
