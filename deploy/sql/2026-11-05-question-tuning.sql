-- 依試測數據調題（2026-11-05）：檢測話術題兩題，各保留兩種話術。
-- romance-exam-scam-12：10 人全都選了「先跟你套交情」，只有 6 人選「冒充官方」→ 把網友的交情寫清楚、拿掉「銀行協作人員」，正解改成「先跟你套交情」「催你快點決定」。
-- investment-exam-scam-03：常有人多選「用好處引誘你」→ 拿掉「帳面已經翻倍」，正解不變（「說大家都在做」「催你快點決定」）。
-- 新環境由 2026-10-16-exam-cases.sql 直接灌新內容（已同步）。逐欄寫死新舊值，只有內容與舊值一字不差才更新，可重複執行。
BEGIN;
UPDATE public.game_cases SET narrative = $rw$我在語言交流社群認識他，我們每天聊天快兩個月，他常說來台灣第一個就要見我。他說自己在台灣的帳戶被凍結了，裡面是他來台灣的生活費，只要我把金融卡和密碼寄給他的朋友，借我的帳戶就能解鎖，之後就把卡還我。他說解鎖申請明天下午就到期，要我今天就寄出。我看著手上那張金融卡，寄件袋放在桌上，收件地址已經寫好了。$rw$
  WHERE case_key = $rw$romance-exam-scam-12$rw$ AND narrative = $rw$語言交流社群認識的他說，自己在台灣的帳戶被凍結了，帳戶裡有他要來台灣的生活費。一名自稱銀行協作人員的人加入對話，說只要我把金融卡和密碼寄給他，用我的帳戶協助解鎖，之後就會把卡還我。協作人員說解鎖申請隔天下午就到期，要我今天就寄出。我低頭看著手上那張金融卡，寄件袋就放在旁邊的桌上，收件地址已經寫好了。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "trust_building", "text": "每天聊快兩個月，常說來台灣第一個就要見我"}, {"tag": "time_pressure", "text": "說解鎖申請明天下午就到期，要你今天就寄"}]$rw$::jsonb
  WHERE case_key = $rw$romance-exam-scam-12$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "自稱銀行協作人員加入對話"}, {"tag": "time_pressure", "text": "說解鎖申請隔天下午就到期"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我看完一場理財直播，加入主持人開的討論群，群裡每天都有人貼對帳單和獲利截圖，底下一片道謝。我跟著群裡的建議做外匯，前後投了約十二萬元。今天想把這筆錢領出來，平台說要先繳提領金額兩成的保證金才能解鎖。主持人私訊我，說今天之內辦好，才不會影響下一輪布局。我停在提領的頁面，看著那筆保證金的金額，還沒決定。$rw$
  WHERE case_key = $rw$investment-exam-scam-03$rw$ AND narrative = $rw$我看完一場理財直播，加入主持人開的討論群，群裡每天都有人貼對帳單和獲利截圖，底下一片道謝。我跟著群裡的建議做外匯，前後投了約十二萬元，帳面已經翻倍。今天想提領，平台說要先繳提領金額兩成的保證金才能解鎖。主持人私訊我，說今天之內辦好，才不會影響下一輪布局。我停在提領頁，看著那筆保證金的金額，還沒決定。$rw$;
COMMIT;

-- 檢查：兩題都是新內容（應各 1 列）、這兩題不再有「銀行協作人員」與「帳面已經翻倍」（應為 0；別的題目本來就可能有這些字）
SELECT case_key, red_flags FROM public.game_cases WHERE case_key IN ('romance-exam-scam-12', 'investment-exam-scam-03') ORDER BY case_key;
SELECT count(*) AS 舊內容還在 FROM public.game_cases WHERE case_key IN ('romance-exam-scam-12', 'investment-exam-scam-03')
  AND (narrative LIKE '%自稱銀行協作人員%' OR narrative LIKE '%帳面已經翻倍%');
SELECT pool, count(*) FROM public.game_cases WHERE status = 'published' GROUP BY pool ORDER BY pool;
