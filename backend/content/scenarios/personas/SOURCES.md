# 人格寫法的參考來源

只參考公開的角色提示詞寫法，人格內容都是自己寫的，沒有照抄任何角色卡。

| 來源 | 參考了什麼 | 用在哪裡 |
|------|------|------|
| [SillyTavern 角色設計說明](https://docs.sillytavern.app/usage/core-concepts/characterdesign) | 每次都會送進模型的固定欄位要寫短，說話的樣子交給示範對話 | frontmatter 每欄一句話，`## 示範句` 放日常台詞 |
| [Ali:Chat 角色寫法](https://docs.google.com/document/d/1qvcvZWhp24p14dsMlmj7vN4cM5RTDSj0gLaZSl1PPO8/mobilebasic) | 個性要靠台詞和動作表現，不要只堆形容詞 | `## 口頭禪`、`## 示範句`，每句都要看得出這個人怎麼講話 |
| [Anthropic：讓 Claude 保持角色](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/keep-claude-in-character) | 在系統提示裡寫清楚角色個性，並先寫好常見情況要怎麼回，長對話才不會走樣 | `when_doubted` 欄位（被懷疑是最常見、也最容易演壞的情況） |

和這些寫法不同的地方：一般角色卡會把背景、目標和個性寫在一起，這裡刻意拆開。人格只有說話方式和個性，對方是誰、想要什麼、怎麼交鋒都寫在劇本裡，這樣同一個人格才能演詐騙也能演正當的角色。
