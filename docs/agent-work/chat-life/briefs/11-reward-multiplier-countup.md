# 11：透明倍率跳表與克制的小鋼珠式結算

## 使用者感受目標

玩家要明顯感受到金錢數字「倍率再倍率」的成長刺激，但不要變成爆閃、轉盤、隨機 jackpot 或過量聲光。刺激來源必須是玩家剛才真正完成的查證、委託與天梯成長，而非虛構動畫。

## 真實計算

沿用現有 server authoritative reward breakdown，不改經濟規則：

`final_cash = round(base_cash × chapter_multiplier × chat_factor)`

- `chapter_multiplier` 是永久天梯／章節倍率，維持既有 cap。
- `chat_factor` 是本案實際獲得的加成總和與 cap；顯示每一個已取得原因。
- 章末特殊 `2.5x` 仍依既有規則「取代 ordinary chat factor」，不得再疊 1.5。
- replay、pause、盲猜、資產收益不得被動畫誤顯示成有倍率。
- 資產收益另列 `資產回流 +N`，不混入案件倍率。

若 response 沒有完整 server breakdown，就只顯示最後實際入帳，不由前端猜 base 或倍率。

## 四拍跳表

終局結果分四個短步驟，總長約 1.8–2.8 秒，並提供 reduced-motion 立即顯示：

1. `基礎報酬`：數字由 0 快速跳到 base。
2. `天梯倍率`：一顆小型光點／金屬珠沿短軌道撞過 `×1.xx` 門，數字跳到 chapter subtotal。
3. `本案倍率`：實際 earned bonus 依序進場，例如 `新證據 +10%`、`完成委託 +20%`，合併顯示 `×1.30` 後跳到 final。
4. `實際入帳`：最終金額停住，輕微 scale 1.03 與單次亮邊；同時列 XP、關係或解鎖，但不再各自爆閃。

畫面永久保留算式，例如：

`$800 × 1.32（天梯）× 1.30（本案）= $1,373`

四捨五入要與 server 完全一致。若 subtotal 只是展示值，使用與 server 相同的 rounding order，或後端直接回傳 subtotal，避免畫面算式和入帳差 1 元。

## 視覺限制

- 深色介面中使用金屬珠、短軌道、局部琥珀／翠綠亮邊。
- 不使用老虎機捲軸、彩券詞彙、jackpot、連續閃白、螢幕震動、全螢幕粒子或強制音效。
- 金額可用等寬數字與 odometer/count-up；只動畫變動的位數。
- 每個倍率門只觸發一次，重新開結果頁直接顯示完成態，不重播到可農刺激。
- `prefers-reduced-motion` 下完全跳過珠子移動與逐位滾動，直接呈現算式與最後值。
- 動畫期間資訊可讀，不能鎖住返回／關閉超過必要時間。

## 天梯連結

- 升階時結算卡在最後增加 `天梯提升`，下一階與新人物解鎖在金額停住後出現。
- 下一階永久倍率只從後續事件開始生效；當次通關使用 server 已計算的舊／新倍率規則，不由前端提早套用。
- 首頁天梯可顯示下一階的永久倍率增幅，讓玩家理解長期價值，但不顯示假預估收入。

## 驗收

1. 以固定 reward breakdown 驗證每一拍顯示值與算式，final 等於 server `final_cash`。
2. ordinary factor、finale 2.5 replacement、replay 0、no-breakdown 四種狀態皆有 component tests。
3. bonus 未 earned 不顯示，資產收益不乘 chat factor。
4. reduced motion 測試確認沒有延遲動畫且內容完整。
5. reload terminal result 不重複入帳，也不依動畫狀態呼叫結算 API。
6. 手機寬度無溢出；動畫完成前後按鈕可操作。

本 brief 等天梯主線 10b 驗收後再派工，避免同時修改首頁／ResultSheet。
