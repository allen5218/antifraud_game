/** 經營頁的玩法說明：第一次進來自動打開，之後按「怎麼玩」再看 */
export type GuideStep = { title: string; text: string }

export const GUIDE_STEPS: GuideStep[] = [
  {
    title: "房子會自己收租",
    text: "每種房產都有自己的收租時間，進度條跑滿就收一次租。同一種買越多間，每次收得越多。一開始送你一間雅房，起家的這一間不會被騙走。",
  },
  {
    title: "吉祥物當經理",
    text: "把吉祥物派去當經理，那種房產就會自動收租，沒開遊戲也照收，最多幫你收 24 小時。沒有經理的房產收完一次會停下來，要自己按收租。商店買到新的吉祥物，就能多派一個經理。",
  },
  {
    title: "買到整數翻倍",
    text: "同一種房產買到 25、50、100、200、300、400 間，那一種的租金各再翻一倍。",
  },
  {
    title: "練習讓房子賺更多",
    text: "每練完一輪卡片，除了拿錢，每答對一張，所有房產立刻多收 20 分鐘的租。每種房產對一類詐騙，那一類累積答對 25、50、100、200、400 題，那種房產的租金各翻一倍。錢只能靠答題加速。",
  },
  {
    title: "升級卡",
    text: "每種房產最多可以買 8 張升級卡，每張讓那一種的租金翻一倍。升級卡搬家也不會不見。",
  },
  {
    title: "搬家換信譽",
    text: "賺到的租金夠多，就可以搬家：房產回到一間雅房、錢回到 1,000 元，換到信譽。每點信譽讓所有收入多 2%，練習拿的錢也算。升級卡、經理和練習的翻倍都會留著。",
  },
  {
    title: "兩週競技榜",
    text: "每日訓練（第 5 級開放）的成績會算進兩週一期的競技榜，在排行榜頁看，分成正確率、速度、養成競技三種。兩週內至少練 5 天、50 題才能領獎，依名次發信譽和獎盃。",
  },
]

export const PROGRESSION_GUIDE_KEY = "scamgym.progressionGuideSeen"

/** 這台裝置看過說明沒有；瀏覽器不給讀就當沒看過 */
export function guideSeen(): boolean {
  try {
    return localStorage.getItem(PROGRESSION_GUIDE_KEY) === "1"
  } catch {
    return false
  }
}

export function markGuideSeen(): void {
  try {
    localStorage.setItem(PROGRESSION_GUIDE_KEY, "1")
  } catch {
    // 私密視窗或封鎖網站資料時存不了，下次再自動打開一次也沒關係
  }
}
