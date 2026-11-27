/**
 * 分頁「經營」（/room）要顯示哪一個畫面：平常是放置經營；
 * 年長者、新手導覽（還沒看過或 `?tour=1`）和「我的家」（`?view=house`）是原本鋪滿畫面的房間。
 * 路由與外框（要不要內距、頁首）共用這一份判斷。
 */
export function showsRoomScene(o: {
  elder: boolean
  tour?: unknown
  view?: unknown
  tourPending?: boolean
}): boolean {
  return (
    o.elder || Boolean(o.tour) || o.view === "house" || o.tourPending === true
  )
}
