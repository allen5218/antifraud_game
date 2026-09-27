-- 題庫出處修正(2026-09-27):假網拍 4 題的來源機構、27 題團隊整理文件的標示。
-- 由同名的 .py 產生(說明見 .py 開頭)。逐列寫死新舊值,只有內容與舊種子一字不差才更新,可重複執行。
BEGIN;
UPDATE public.game_cases SET provenance = $prov$改編自：165 全民防騙網「民眾通報高風險業者」（假網路拍賣）與 165 打詐儀錶板網路購物手法$prov$
  WHERE case_key = $prov$fake-sale-scam-004-v2$prov$ AND provenance = $prov$改編自：數位發展部高風險業者通報清單（假網路拍賣）與 165 打詐儀錶板網路購物手法$prov$;
UPDATE public.game_cases SET provenance = $prov$改編自：165 全民防騙網「民眾通報高風險業者」（假網路拍賣）與刑事局宣導之假買家假物流手法$prov$
  WHERE case_key = $prov$fake-sale-scam-001-v2$prov$ AND provenance = $prov$改編自：數位發展部高風險業者通報清單（假網路拍賣）與刑事局宣導之假買家假物流手法$prov$;
UPDATE public.game_cases SET provenance = $prov$改編自：165 全民防騙網「民眾通報高風險業者」（假網路拍賣）與 165 打詐儀錶板網路購物手法$prov$
  WHERE case_key = $prov$fake-sale-scam-002-v2$prov$ AND provenance = $prov$改編自：數位發展部高風險業者通報清單（假網路拍賣）與 165 打詐儀錶板網路購物手法$prov$;
UPDATE public.game_cases SET provenance = $prov$改編自：165 全民防騙網「民眾通報高風險業者」（假網路拍賣）與 165 打詐儀錶板網路購物手法$prov$
  WHERE case_key = $prov$fake-sale-scam-003-v2$prov$ AND provenance = $prov$改編自：數位發展部高風險業者通報清單（假網路拍賣）與 165 打詐儀錶板網路購物手法$prov$;
UPDATE public.game_cases SET provenance = $prov$改編自：165 全民防騙網「網路購物遇到詐騙了？」與團隊整理的正規流程說明「正規電商交易與退換貨流程」$prov$
  WHERE case_key = $prov$shopping-scam-022$prov$ AND provenance = $prov$改編自：165 全民防騙網「網路購物遇到詐騙了？」與官方正規流程文件「正規電商交易與退換貨流程」$prov$;
UPDATE public.game_cases SET provenance = $prov$改編自：165 打詐儀錶板「網友想見的不是你 是你荷包的錢」與團隊整理的正規流程說明「正常網路交友互動特徵」$prov$
  WHERE case_key = $prov$romance-scam-023$prov$ AND provenance = $prov$改編自：165 打詐儀錶板「網友想見的不是你 是你荷包的錢」與官方正規流程文件「正常網路交友互動特徵」$prov$;
UPDATE public.game_cases SET provenance = $prov$改編自：Cofacts 真的假的民眾回報訊息原文與團隊整理的「正常網路交友互動特徵」，已移除姓名及院所資訊$prov$
  WHERE case_key = $prov$romance-scam-024$prov$ AND provenance = $prov$改編自：Cofacts 真的假的民眾回報訊息原文與「正常網路交友互動特徵」，已移除姓名及院所資訊$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「合法投資開戶與交易正規流程」與金管會新聞稿「網路投資群組詐騙多，停看聽後再投資」$prov$
  WHERE case_key = $prov$investment-legit-021$prov$ AND provenance = $prov$依據：官方正規流程文件「合法投資開戶與交易正規流程」與金管會新聞稿「網路投資群組詐騙多，停看聽後再投資」$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「合法投資開戶與交易正規流程」與證券商風險及費用揭露義務$prov$
  WHERE case_key = $prov$investment-legit-022$prov$ AND provenance = $prov$依據：官方正規流程文件「合法投資開戶與交易正規流程」與證券商風險及費用揭露義務$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「合法投資開戶與交易正規流程」與金管會金融商品揭露規範$prov$
  WHERE case_key = $prov$investment-legit-023$prov$ AND provenance = $prov$依據：官方正規流程文件「合法投資開戶與交易正規流程」與金管會金融商品揭露規範$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「合法投資開戶與交易正規流程」與證券商債券商品公開說明作業$prov$
  WHERE case_key = $prov$investment-legit-024$prov$ AND provenance = $prov$依據：官方正規流程文件「合法投資開戶與交易正規流程」與證券商債券商品公開說明作業$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」與拍賣平台站內工單、款項代管機制$prov$
  WHERE case_key = $prov$fake-sale-legit-021$prov$ AND provenance = $prov$依據：官方正規流程文件「正規電商交易與退換貨流程」與拍賣平台站內工單、款項代管機制$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」與購物平台站內結帳機制$prov$
  WHERE case_key = $prov$fake-sale-legit-022$prov$ AND provenance = $prov$依據：官方正規流程文件「正規電商交易與退換貨流程」與購物平台站內結帳機制$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」與票券平台轉讓流程$prov$
  WHERE case_key = $prov$fake-sale-legit-023$prov$ AND provenance = $prov$依據：官方正規流程文件「正規電商交易與退換貨流程」與票券平台轉讓流程$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」與拍賣平台鑑定、原支付工具退款機制$prov$
  WHERE case_key = $prov$fake-sale-legit-024$prov$ AND provenance = $prov$依據：官方正規流程文件「正規電商交易與退換貨流程」與拍賣平台鑑定、原支付工具退款機制$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：消費者保護法第19條通訊交易七日解除權與團隊整理的正規流程說明「正規電商交易與退換貨流程」$prov$
  WHERE case_key = $prov$shopping-legit-021$prov$ AND provenance = $prov$依據：消費者保護法第19條通訊交易七日解除權與官方正規流程文件「正規電商交易與退換貨流程」$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」與金管會信用卡安全提醒$prov$
  WHERE case_key = $prov$shopping-legit-023$prov$ AND provenance = $prov$依據：官方正規流程文件「正規電商交易與退換貨流程」與金管會信用卡安全提醒$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」與交通部旅宿業登記查詢、定型化契約$prov$
  WHERE case_key = $prov$shopping-legit-024$prov$ AND provenance = $prov$依據：官方正規流程文件「正規電商交易與退換貨流程」與交通部旅宿業登記查詢、定型化契約$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「正常網路交友互動特徵」$prov$
  WHERE case_key = $prov$romance-legit-021$prov$ AND provenance = $prov$依據：官方正規流程文件「正常網路交友互動特徵」$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的「正常網路交友互動特徵」與「合法投資開戶與交易正規流程」$prov$
  WHERE case_key = $prov$romance-legit-022$prov$ AND provenance = $prov$依據：「正常網路交友互動特徵」與「合法投資開戶與交易正規流程」$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的「正常網路交友互動特徵」與餐飲訂位可核對業者、訂金及退款條件的正規流程$prov$
  WHERE case_key = $prov$romance-legit-023$prov$ AND provenance = $prov$依據：「正常網路交友互動特徵」與餐飲訂位可核對業者、訂金及退款條件的正規流程$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的「正常網路交友互動特徵」與醫療院所直接繳款並取得收據的可核對流程$prov$
  WHERE case_key = $prov$romance-legit-024$prov$ AND provenance = $prov$依據：「正常網路交友互動特徵」與醫療院所直接繳款並取得收據的可核對流程$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的正規流程說明「訂單問題正規客服處理流程」與金管會信用卡安全提醒$prov$
  WHERE case_key = $prov$atm-legit-021$prov$ AND provenance = $prov$依據：官方正規流程文件「訂單問題正規客服處理流程」與金管會信用卡安全提醒$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的「正常網路交友互動特徵」與消保法預購型群眾募資規範$prov$
  WHERE case_key = $prov$romance-legit-031$prov$ AND provenance = $prov$依據：正常網路交友互動特徵與消保法預購型群眾募資規範$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的「正常網路交友互動特徵」與拍賣公司公開預展交易流程$prov$
  WHERE case_key = $prov$romance-legit-032$prov$ AND provenance = $prov$依據：正常網路交友互動特徵與拍賣公司公開預展交易流程$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的「正常網路交友互動特徵」與民法消費借貸書面契約原則$prov$
  WHERE case_key = $prov$romance-legit-033$prov$ AND provenance = $prov$依據：正常網路交友互動特徵與民法消費借貸書面契約原則$prov$;
UPDATE public.game_cases SET provenance = $prov$依據：團隊整理的「正常網路交友互動特徵」與銀行本人帳戶臨櫃處理流程$prov$
  WHERE case_key = $prov$romance-legit-034$prov$ AND provenance = $prov$依據：正常網路交友互動特徵與銀行本人帳戶臨櫃處理流程$prov$;
COMMIT;

-- 檢查:應該都是 0
SELECT count(*) FILTER (WHERE provenance LIKE '%數位發展部高風險業者%') AS moda_label,
       count(*) FILTER (WHERE provenance LIKE '%官方正規流程文件%') AS official_label,
       count(*) FILTER (WHERE provenance LIKE '%正常網路交友互動特徵%'
                        AND provenance NOT LIKE '%團隊整理的%') AS unlabeled_team_doc
  FROM public.game_cases;
