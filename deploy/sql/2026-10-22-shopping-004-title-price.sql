-- 購物詐騙一組對照題(2026-10-22):shopping-scam-004-v2 與它的對照正常題 shopping-legit-011。
-- 標題「購物平台上的那件折價商品」對不上詐騙題(全程在社群社團、沒進購物平台)→「社團裡那台便宜的遊戲主機」;
-- 價差「比行情低了將近一半」太離譜 →「比行情便宜快三成」,詐騙題第一條可疑之處跟著改。
-- 檢測專用的 shopping-exam-scam-04／shopping-exam-legit-04(搬家出清的平板電腦)同樣的價差一起改。
-- 原稿 data_pipeline/data/manual/*.jsonl 與種子已一起改好。這份由 2026-10-16-question-rewrites.py 產生:
--   python3 deploy/sql/2026-10-16-question-rewrites.py <改前的 deploy/seed/game_cases.sql> deploy/seed/game_cases.sql
-- 逐列逐欄寫死新舊值,只有內容與舊種子一字不差才更新,可重複執行。
BEGIN;
UPDATE public.game_cases SET title = $rw$社團裡那台便宜的遊戲主機$rw$
  WHERE case_key = $rw$shopping-scam-004-v2$rw$ AND title = $rw$購物平台上的那件折價商品$rw$;
UPDATE public.game_cases SET narrative = $rw$我在社群的買賣社團看到有人賣一台遊戲主機，價格比行情便宜快三成，貼文寫著急需用錢才割愛，附了幾張機器的照片。我留言詢問，賣家很快私訊我，說社團最近查得嚴，怕交易被檢舉下架，叫我加他的通訊軟體到外面談比較安全。加了之後他說已經有好幾個人在問，誰先付款就先保留，要我趕快決定。我問能不能面交或走平台的購物車，他說他人在外縣市、又怕平台抽成，直接轉帳最快，轉完他今天就寄出。他傳來一組帳號，說再等下去就要賣給別人了。我把轉帳頁面打開了。$rw$
  WHERE case_key = $rw$shopping-scam-004-v2$rw$ AND narrative = $rw$我在社群的買賣社團看到有人賣一台遊戲主機，價格比行情低了將近一半，貼文寫著急需用錢才割愛，附了幾張機器的照片。我留言詢問，賣家很快私訊我，說社團最近查得嚴，怕交易被檢舉下架，叫我加他的通訊軟體到外面談比較安全。加了之後他說已經有好幾個人在問，誰先付款就先保留，要我趕快決定。我問能不能面交或走平台的購物車，他說他人在外縣市、又怕平台抽成，直接轉帳最快，轉完他今天就寄出。他傳來一組帳號，說再等下去就要賣給別人了。我把轉帳頁面打開了。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "價格比行情便宜不少，又說急需用錢才割愛"}, {"tag": "authority", "text": "藉口怕被檢舉下架，要你離開平台到站外私下交易"}, {"tag": "time_pressure", "text": "謊稱很多人搶購、催促你先付款保留，不給你查證的時間"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-004-v2$rw$ AND red_flags = $rw$[{"tag": "greed", "text": "以明顯低於行情的超低價、急賣話術吸引買家上鉤"}, {"tag": "authority", "text": "藉口怕被檢舉下架，要你離開平台到站外私下交易"}, {"tag": "time_pressure", "text": "謊稱很多人搶購、催促你先付款保留，不給你查證的時間"}]$rw$::jsonb;
UPDATE public.game_cases SET title = $rw$社團裡那台便宜的遊戲主機$rw$
  WHERE case_key = $rw$shopping-legit-011$rw$ AND title = $rw$購物平台上的那件折價商品$rw$;
UPDATE public.game_cases SET narrative = $rw$我在社群的買賣社團看到有人賣一台遊戲主機，價格比行情便宜快三成，附了幾張機器的照片。我留言問，賣家說他是在購物平台開店的二手商家，這台是拆封過的福利品，請我到賣場下單。賣場頁寫著外盒有壓痕、機身有一道刮痕，都附了照片，保固只剩三個月。結帳走平台的購物車，收到貨七天內可以退。我把刮痕照片放大看了一下，手指停在下單鍵上。$rw$
  WHERE case_key = $rw$shopping-legit-011$rw$ AND narrative = $rw$我在社群的買賣社團看到有人賣一台遊戲主機，價格比行情低了將近一半，附了幾張機器的照片。我留言問，賣家說他是在購物平台開店的二手商家，這台是拆封過的福利品，請我到賣場下單。賣場頁寫著外盒有壓痕、機身有一道刮痕，都附了照片，保固只剩三個月。結帳走平台的購物車，收到貨七天內可以退。我把刮痕照片放大看了一下，手指停在下單鍵上。$rw$;
-- 檢測專用題的同一個問題:shopping-exam-scam-04 與對照正常題 shopping-exam-legit-04(新環境由 2026-10-16-exam-cases.sql 直接灌新內容)
UPDATE public.game_cases SET narrative = $rw$我在社群買賣社團看到一台平板電腦，賣家說搬家整理要出清，價格比行情便宜了快三成。我私訊問能不能面交，他說住在台南，我在台北，沒辦法約。我問能不能走平台的購物車，他說社團最近查得很嚴，怕交易被檢舉下架，要我直接轉帳，付款當天就寄出。他說還有好幾個人在問，再等下去就要賣給別人了。他還傳了開機畫面的照片給我。我正在看他給的帳號。$rw$
  WHERE case_key = $rw$shopping-exam-scam-04$rw$ AND narrative = $rw$我在社群買賣社團看到一台平板電腦，賣家說搬家整理要出清，價格比行情低了將近一半。我私訊問能不能面交，他說住在台南，我在台北，沒辦法約。我問能不能走平台的購物車，他說社團最近查得很嚴，怕交易被檢舉下架，要我直接轉帳，付款當天就寄出。他說還有好幾個人在問，再等下去就要賣給別人了。他還傳了開機畫面的照片給我。我正在看他給的帳號。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "價格比行情便宜快三成"}, {"tag": "time_pressure", "text": "說再等下去就要賣給別人"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-exam-scam-04$rw$ AND red_flags = $rw$[{"tag": "greed", "text": "價格比行情低將近一半"}, {"tag": "time_pressure", "text": "說再等下去就要賣給別人"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在社群買賣社團看到一台平板電腦，賣家說搬家整理要出清，價格比行情便宜了快三成。我私訊問為什麼這麼便宜，他說螢幕有一道刮痕，電池健康度只剩七成，還拍了照片給我看。他住在台南，我在台北，他說可以在二手平台開一個賣場給我下單，用平台的付款保障，我收到確認沒問題，平台才撥款給他。我正在平台上看他開的賣場。$rw$
  WHERE case_key = $rw$shopping-exam-legit-04$rw$ AND narrative = $rw$我在社群買賣社團看到一台平板電腦，賣家說搬家整理要出清，價格比行情低了將近一半。我私訊問為什麼這麼便宜，他說螢幕有一道刮痕，電池健康度只剩七成，還拍了照片給我看。他住在台南，我在台北，他說可以在二手平台開一個賣場給我下單，用平台的付款保障，我收到確認沒問題，平台才撥款給他。我正在平台上看他開的賣場。$rw$;
COMMIT;

-- 檢查:兩題都已換成新標題(應為 2 列)、不再有「將近一半」(應為 0),已發布的案例練習 120、檢測 110
SELECT case_key, title FROM public.game_cases WHERE case_key IN ('shopping-scam-004-v2', 'shopping-legit-011') ORDER BY case_key;
SELECT count(*) AS 還有將近一半 FROM public.game_cases WHERE narrative LIKE '%將近一半%';
SELECT pool, count(*) FROM public.game_cases WHERE status = 'published' GROUP BY pool ORDER BY pool;
