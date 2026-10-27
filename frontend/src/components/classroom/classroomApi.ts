import type {
  AssignmentCreate,
  AssignmentUpdate,
  ClassMemberUpdate,
  ClassroomUpdate,
  JoinClass,
  TeacherApplication,
} from "@/client"
import {
  AdminTeachersService,
  ClassesService,
  InviteService,
  UsersService,
} from "@/client/sdk.gen"

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

export const classApi = {
  list: () => ClassesService.listClasses(),
  create: (name: string) =>
    ClassesService.createClass({ requestBody: { name } }),
  update: (classId: string, body: ClassroomUpdate) =>
    ClassesService.updateClass({ classId, requestBody: body }),
  members: (classId: string) => ClassesService.listMembers({ classId }),
  updateMember: (classId: string, userId: string, body: ClassMemberUpdate) =>
    ClassesService.updateMember({ classId, userId, requestBody: body }),
  removeMember: (classId: string, userId: string) =>
    ClassesService.removeMember({ classId, userId }),
  member: (classId: string, userId: string) =>
    ClassesService.readMember({ classId, userId }),
  overview: (classId: string) => ClassesService.readOverview({ classId }),
  exportCsv: (classId: string) =>
    ClassesService.exportClass({ classId }) as unknown as Promise<string>,
  createAssignment: (classId: string, body: AssignmentCreate) =>
    ClassesService.createAssignment({ classId, requestBody: body }),
  updateAssignment: (
    classId: string,
    assignmentId: string,
    body: AssignmentUpdate,
  ) =>
    ClassesService.updateAssignment({
      classId,
      assignmentId,
      requestBody: body,
    }),
  deleteAssignment: (classId: string, assignmentId: string) =>
    ClassesService.deleteAssignment({ classId, assignmentId }),
  // 學生端
  mine: () => ClassesService.readMyClasses(),
  join: (body: JoinClass) => ClassesService.joinClass({ requestBody: body }),
  claim: (classId: string, body: ClassMemberUpdate) =>
    ClassesService.claimMembership({ classId, requestBody: body }),
  redeem: (token: string) => InviteService.redeemClassInvite({ token }),
}
