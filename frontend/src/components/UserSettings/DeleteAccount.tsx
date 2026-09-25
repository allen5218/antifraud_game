import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  return (
    <div className="max-w-md mt-4 rounded-lg border border-destructive/50 p-4">
      <h3 className="font-semibold text-destructive">刪除帳號</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        永久刪除你的帳號與所有遊戲紀錄。
      </p>
      <DeleteConfirmation />
    </div>
  )
}

export default DeleteAccount
