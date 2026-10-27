import type { TeacherApplication } from "@/client"
import { AdminTeachersService, UsersService } from "@/client/sdk.gen"

type TeacherAction = "approve" | "reject" | "suspend" | "restore"
type TeacherStatus = "pending" | "approved" | "rejected" | "suspended"

// 元件經過這一層呼叫 API，測試 spy 這個物件（和 shop/mascotApi 同一種寫法）
export const teacherApi = {
  apply: (body: TeacherApplication) =>
    UsersService.applyTeacherMe({ requestBody: body }),
  list: (status: TeacherStatus) =>
    AdminTeachersService.listTeachers({ status }),
  change: (userId: string, action: TeacherAction) =>
    AdminTeachersService.changeTeacher({ userId, action }),
}
