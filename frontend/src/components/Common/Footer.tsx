export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t py-4 px-6">
      <p className="text-center text-muted-foreground text-sm sm:text-left">
        ScamGym 識詐練習場 - {currentYear}
      </p>
    </footer>
  )
}
