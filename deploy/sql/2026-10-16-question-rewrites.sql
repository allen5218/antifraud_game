-- 題庫改寫(2026-10-16):練習案例與查證題依題目檢查清單的拍板改寫。
-- 由同名的 .py 產生(說明見 .py 開頭)。逐列逐欄寫死新舊值,只有內容與舊種子一字不差才更新,可重複執行。
BEGIN;
UPDATE public.game_cases SET narrative = $rw$我應徵一份寫著高佣金的代銷工作，對方約我到辦公室面談。報到那天，一位自稱區域主管的人跟我說，這份工作沒有底薪，收入靠分紅，只要自己先投一筆錢進去跑單，佣金和分紅都能領，一個月賺個十萬不是問題。他還拿出一張表，算給我看一個月能賺多少。他說新人第一筆先放三萬就好，熟悉之後再慢慢加。我坐在會議室裡，他把手機轉過來，讓我看轉帳的頁面。$rw$
  WHERE case_key = $rw$investment-scam-002-v2$rw$ AND narrative = $rw$我應徵一份寫著高佣金的代銷職缺，對方約我到辦公室面談。接待的人很客氣，帶我參觀了整層樓，還特地介紹一位自稱區域主管的人給我認識，說公司制度完整、新人都有專人帶。報到流程走得很順，填完表格後，那位主管說這份工作不領底薪，收入靠分紅，只要自己也投入一筆資金進去跑單，就能同時領佣金和分紅。他隨手算了一個月可能的數字給我看，比我原本預期的多出好幾倍。他說第一筆先放三萬就好，熟悉流程之後再加碼，現在辦好下週就能開始跑。我坐在會議室裡，他把手機轉過來讓我看轉帳頁面。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "主管說一個月賺十萬不是問題"}, {"tag": "authority", "text": "自稱區域主管的人出面說明分紅制度"}]$rw$::jsonb
  WHERE case_key = $rw$investment-scam-002-v2$rw$ AND red_flags = $rw$[{"tag": "greed", "text": "以高佣金、參與分紅的代銷職缺，誘導求職者投入資金追求快速收入"}, {"tag": "authority", "text": "刻意介紹主管級人物、營造公司制度完善的假象取信於人"}, {"tag": "trust_building", "text": "先用簡單的報到流程與專人接待讓你安心，再逐步引導匯款"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在網路上索取了一份免費的投資資料，留了聯絡方式，後來被拉進一個討論群組。群裡有人教我在一個平台開戶，說可以用比市價低的價格搶新股。兩個月下來帳面一直在漲，我陸續投了二十幾萬。上週我申請出金，今天客服傳訊息說，依照稅務規定，我的獲利超過門檻，要先另外匯一筆稅金，系統才會撥款。我問能不能直接從獲利裡扣，他說系統不支援。我看著他給的帳號和金額。$rw$
  WHERE case_key = $rw$investment-scam-003-v2$rw$ AND narrative = $rw$我在網路上索取了一份免費的投資秘笈，留了聯絡方式，沒多久就被拉進一個操盤群組。群組裡有人教我在一個平台上開戶，說可以優先低價申購新股，還會提前佈局。前兩個月帳面確實一直在漲，我陸續投了二十幾萬。上週我按流程申請出金，系統顯示待審核。今天客服傳訊息來，說我的獲利金額達到申報門檻，依主管機關規定要先繳一筆稅金才能撥款，繳完當天就會入帳。我問能不能從我的獲利裡直接扣，他說系統不支援，必須另外匯入。我翻了翻紀錄，這已經是第三次了，前兩次的名目分別是自證金和擔保金。我盯著那個金額，想著要不要再匯一次。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "群裡說能用比市價低的價格搶新股"}, {"tag": "authority", "text": "客服說依稅務規定要先另匯稅金才撥款"}]$rw$::jsonb
  WHERE case_key = $rw$investment-scam-003-v2$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "自稱金管會與國稅局發函，要你先繳稅才審核撥款"}, {"tag": "greed", "text": "以優先低價申購新股、內線佈局等超額獲利話術吸引投入"}, {"tag": "time_pressure", "text": "出金前不斷追加稅金、自證金、擔保金，用層層費用拖住資金"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$investment-scam-003-v2$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$我想幫角色買一件稀有裝備，在遊戲頻道問了一句，有個人主動私訊我。他對版本改動和掉寶機率都很熟，我問什麼他都答得出來，聊了幾天像認識很久的朋友。他說手上剛好有一件，可以便宜賣我，比交易市集少好幾百，不過要加通訊軟體私下轉帳，因為市集要抽成。我加了他，他傳來一組帳號，說錢轉過去他就馬上上線交貨。我停在轉帳的頁面。$rw$
  WHERE case_key = $rw$shopping-scam-001-v2$rw$ AND narrative = $rw$我想幫角色買一件稀有裝備，在遊戲頻道問了一句，有個人主動私訊我。他對版本改動、掉落機率、練功路線都很熟，我問什麼他都答得出來，聊了幾天像認識很久的朋友。他說手上剛好有一件，願意便宜讓給我，但要我加通訊軟體談，說走遊戲內建的交易市集要抽成、還要等審核，私下轉帳比較快也比較便宜。我照做加了他，他傳來一組帳號要我先轉。轉完之後他說銀行那邊還在查帳，要我等一下，晚點就上線交貨。到現在過了兩個小時，他還沒上線，訊息也還沒回。我盯著那個對話框，想著要不要再催一次。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "trust_building", "text": "連聊幾天攻略，像認識很久的朋友"}, {"tag": "greed", "text": "說私下交易比交易市集少好幾百"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-001-v2$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "對方精通遊戲攻略、有問必答，刻意營造可信賴的老玩家形象"}, {"tag": "authority", "text": "要你離開遊戲內建交易市集，改用私人通訊軟體私下交易"}, {"tag": "time_pressure", "text": "收款後以還在查帳、銀行未確認等理由拖延，最後直接失聯"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$shopping-scam-001-v2$rw$ AND difficulty = 1;
UPDATE public.game_cases SET narrative = $rw$我在拍賣平台賣掉一件東西，買家很快就說已經付款了，還把轉帳畫面截圖給我看，可是我的賣家後台一直沒顯示入帳。買家叫我聯絡平台的金流客服。沒多久就有人加我好友，自稱平台的金流專員，說我是新賣家，還沒完成金流認證，款項被系統暫時扣住。他說要到網路銀行輸入一組代碼做認證，今晚前沒做完，買家的訂單就會取消。我打開網銀，他把那組代碼傳過來了。$rw$
  WHERE case_key = $rw$atm-scam-004-v2$rw$ AND narrative = $rw$我在拍賣平台賣掉一件東西，買家很快就說已經付款了，還把轉帳畫面截圖給我看。但我的賣家後台一直沒有顯示入帳。買家說他也很急著要收到貨，建議我聯繫平台的金流客服處理。過沒多久就有人加我，自稱是平台的金流專員，說我是新賣家、還沒完成金流認證，所以款項被系統暫時保留住，要我配合做一次認證才會放行。他說認證的方式是到提款機或網路銀行輸入一組代碼，輸入完成款項就會自動撥入。他語氣很專業，還說了幾個我後台看得到的訂單編號。我打開網銀，他把那組代碼傳過來了。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "自稱平台金流專員，說新賣家要先認證"}, {"tag": "time_pressure", "text": "說今晚前沒認證完，訂單就會取消"}]$rw$::jsonb
  WHERE case_key = $rw$atm-scam-004-v2$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "假冒平台金流客服，以新賣家未完成金流認證的說法取信"}, {"tag": "trust_building", "text": "先由假買家製造已付款卻卡住的情境，再引出客服接手處理"}, {"tag": "authority", "text": "指示你到 ATM 或網銀輸入代碼完成認證，實為誘導匯出款項"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$atm-scam-004-v2$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$在網路上認識三個月的對象自稱是駐外的軍醫，每天早晚都傳訊息來，前陣子就說想跟我結婚，要辦移民手續回國定居。今天他傳來一份文件的照片，說移民要做財力審核，需要先把一筆保證金存進指定帳戶，證明我們有能力一起生活，審核過了就會退還。我說想先視訊講一下，他說部隊裡不能視訊，訊號也不好。我看著他傳來的那組帳號。$rw$
  WHERE case_key = $rw$romance-scam-001-v2$rw$ AND narrative = $rw$在網路上認識三個月的對象自稱是駐外的軍醫，每天早晚都傳訊息來，前陣子就說要跟我結婚、想辦移民手續回國定居。他說已經幫我寄了一份禮物，裡面有戒指和他這幾年攢的一些東西，要我留地址等收件。今天他傳來一份文件的照片，說是移民程序要跑的財力審核，需要一筆保證金存進指定帳戶證明我們有能力共同生活，審核過了就會退還。他又說物流那邊通知包裹到了，要先付運費和清關費才能派送。兩筆加起來不是小數目。我提議視訊講一下，他說部隊裡不能用視訊，訊號也不好。我看著那兩組帳號。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "trust_building", "text": "每天早晚問候，很快就說想跟我結婚"}, {"tag": "authority", "text": "傳來移民財力審核文件，要我存保證金到指定帳戶"}]$rw$::jsonb
  WHERE case_key = $rw$romance-scam-001-v2$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "以每日噓寒問暖與快速示愛建立感情依賴，鋪陳後續要求"}, {"tag": "authority", "text": "聲稱移民署要審核財力證明，要你先把保證金存進指定帳戶"}, {"tag": "greed", "text": "以寄送貴重禮物為誘餌，再要你先付運費與清關費用"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$交友軟體上認識的對象看起來很體面，聊了三個月，每天噓寒問暖，也常分享他的生活。這陣子他開始聊到理財，說他跟著幾個大戶做虛擬貨幣，已經不太需要為錢煩惱，願意帶我一起做。我照他說的放了五萬，兩週帳面漲了快三成。昨天我想先領一點出來，他說要先補繳一筆手續費才能領，從帳面扣不行。我看著那筆手續費的金額發呆。$rw$
  WHERE case_key = $rw$romance-scam-004-v2$rw$ AND narrative = $rw$交友軟體上認識的對象是個看起來很體面的人，聊了三個月，每天噓寒問暖，也常分享他的生活。這陣子他開始聊到理財，說他在虛擬貨幣上做了幾年，跟著幾個大戶的節奏進出場，已經不太需要為錢煩惱。他說自己在那個平台有內部管道，知道什麼時候會拉盤，願意帶我一起做，先小額試試就好。我照他說的入了五萬，帳面兩週漲了快三成，看起來很順。昨天我說想先出一點來用，他說境外資金要做一次查核，得先繳一筆手續費，款項才能匯回國內，還說這是平台規定，大家都一樣。我問能不能從帳面扣，他說不行。我看著那個查核費用的金額。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "trust_building", "text": "每天噓寒問暖，聊三個月後才提理財"}, {"tag": "greed", "text": "說跟著大戶做虛擬貨幣，帶我一起賺"}]$rw$::jsonb
  WHERE case_key = $rw$romance-scam-004-v2$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "以噓寒問暖與成功人士形象建立好感，把感情當成投資入口"}, {"tag": "greed", "text": "以虛擬貨幣財富自由、跟著大戶進出場等高報酬邀你共同投資"}, {"tag": "authority", "text": "自稱掌握平台內部消息，並假借境外資金查核名義要求繳費"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$傍晚接到一通電話，對方說是某購物平台的客服，報得出我的姓名和上個月買的東西。他說系統出錯，把我的會員設成每個月扣款的方案，要透過銀行解除，等一下會有銀行專員打給我。專員打來後說，解除要在提款機上操作，他會在電話裡教我輸入一組解除代碼。他說今天沒弄好，明天就會扣第一筆。我已經走到提款機前面，電話還沒掛。$rw$
  WHERE case_key = $rw$atm-scam-001-v2$rw$ AND narrative = $rw$傍晚接到一通電話，對方說是某購物平台的客服，開口就報出我的姓名、還有我上個月買的東西和金額，完全相符。他說系統作業疏失，把我的會員等級誤設成需要每月扣款的方案，如果不處理，接下來每個月都會從我的帳戶扣一筆錢。他說這個要透過銀行端解除，已經幫我聯絡好了，等一下會有專員回撥。專員接手後說解除設定要在提款機上操作，他會在電話裡引導我輸入一組解除代碼，弄好之後扣款就會取消。他一再強調今天沒處理完，明天就會扣第一筆。我人已經走到提款機前面，電話一直沒掛。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：刑事警察局宣導『高風險業者提醒：誤設會員等級、解除分期付款詐騙（ATM）』$rw$
  WHERE case_key = $rw$atm-scam-001-v2$rw$ AND provenance = $rw$改編自：刑事警察局宣導『高風險業者提醒：誤設會員等級、解除分期付款詐騙（ATM)』$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "購物客服和銀行專員輪流打電話來"}, {"tag": "time_pressure", "text": "說今天沒弄好，明天就會扣第一筆"}]$rw$::jsonb
  WHERE case_key = $rw$atm-scam-001-v2$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "冒充業者與銀行客服，還準確報出姓名與消費資料取信於人"}, {"tag": "time_pressure", "text": "謊稱今天不解除就會每月被扣款，要你立刻處理"}, {"tag": "authority", "text": "以電話指揮到 ATM 操作解除分期，實際是誘導你匯出款項"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我拿著號碼牌坐在銀行大廳，要臨櫃匯一筆三萬多元的款項。這筆錢是一位自稱購物平台客服的人叫我匯的，他說我的付款被系統重複設定，每個月都會扣一次，要匯這筆到指定帳戶才能取消。他還交代我，行員如果問用途，就說是匯給親戚週轉，不要提到這通電話，不然銀行照一般程序處理會拖好幾天，這段時間還是會一直被扣款。電話還沒掛，快輪到我了。$rw$
  WHERE case_key = $rw$atm-scam-003-v2$rw$ AND narrative = $rw$有人打電話來說是購物平台的客服，說我的付款設定被系統重複套用，變成每個月都會扣一次款，要幫我取消。他講得很專業，還說了訂單編號和金額。他說取消要走銀行的系統，金額比較大，得臨櫃辦理，但因為是系統端的作業，行員不一定知道流程。接著他交代我，櫃檯如果問起匯款用途，就說是要匯給親戚週轉，不要提到這通電話，不然行員會照一般程序處理、拖上好幾天，那期間還是會被扣款。他說他會一直在線上陪我，有問題隨時問他。我拿著號碼牌坐在銀行大廳，電話還接著。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：刑事警察局宣導『解除分期付款詐騙：重複扣款話術與規避行員關懷（ATM）』$rw$
  WHERE case_key = $rw$atm-scam-003-v2$rw$ AND provenance = $rw$改編自：刑事警察局宣導『解除分期付款詐騙：重複扣款話術與規避行員關懷（ATM)』$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "自稱平台客服，教我對行員說是匯給親戚"}, {"tag": "time_pressure", "text": "說照一般程序會拖好幾天，這段時間會一直被扣款"}]$rw$::jsonb
  WHERE case_key = $rw$atm-scam-003-v2$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "冒充購物平台客服，以系統重複扣款設定的專業說法取信"}, {"tag": "time_pressure", "text": "謊稱不處理每月都會被多扣款，催促你立刻到 ATM 操作"}, {"tag": "authority", "text": "教你在臨櫃時對行員謊稱匯款用途，規避銀行的關懷提問"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$朋友把我拉進一個投資群組，群主每天都會貼盤前分析。今天群主說有一檔私募基金只收到這週五，跟上的人每個月至少有一成的獲利。過沒多久，助理私訊我，給了一個個人帳戶，說錢先匯過去，她再幫我登記名額。我問能不能從自己的證券戶買，她說這是內部名額，外面買不到，週五一過就沒了。我看著她傳來的帳號，想說要不要先匯個五萬試試看。$rw$
  WHERE case_key = $rw$investment-scam-001-v2$rw$ AND narrative = $rw$朋友把我拉進一個投資群組，裡面有位自稱投顧的老師每天發布盤前分析，還會不定時說有內線消息。群組有兩百多人，每天都有人貼出自己的對帳單和獲利截圖，底下一片道謝。老師說跟著他帶單的獲利率比自己摸索高太多，叫大家別浪費時間。我試著跟了兩次，帳面確實是紅的，就慢慢加碼到三十萬。這週我想提領一部分出來，平台顯示需要先繳一筆保證金才能解鎖提領額度，金額是提領金的兩成。我在群組裡問，馬上有幾個人說他們也繳過、繳完隔天就到帳了。老師私訊我說今天之內辦好就不影響下一輪佈局。我打開轉帳頁面。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "群主說跟上的人每個月至少賺一成"}, {"tag": "time_pressure", "text": "助理說內部名額週五一過就沒了"}]$rw$::jsonb
  WHERE case_key = $rw$investment-scam-001-v2$rw$ AND red_flags = $rw$[{"tag": "social_proof", "text": "群組裡許多陌生人同步曬出獲利截圖，營造大家都在賺錢的熱絡假象"}, {"tag": "authority", "text": "自稱投顧老師，發布內線消息並以專家身分帶單"}, {"tag": "greed", "text": "強調跟單獲利率遠高於自己操作，用高報酬誘使不斷加碼"}, {"tag": "time_pressure", "text": "提領前不斷以繳保證金為由拖延，逼你一次次補錢才能出金"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$交友軟體上認識一位在國外工作的對象，聊了兩個多月，他每天都會傳訊息問我吃飯沒、睡得好不好。最近他常提到自己在做虛擬礦機租賃，說機器放著就有穩定收入，他半年就回本了。他傳來一個平台的畫面，上面的收益每天都在跳，說想帶我一起賺，先放個五萬試試看，不夠的他可以先幫我墊。他把平台的註冊連結傳給我，問我要不要一起開戶。$rw$
  WHERE case_key = $rw$investment-scam-004-v2$rw$ AND narrative = $rw$交友軟體上認識一位在國外工作的對象，聊了兩個多月，每天固定傳訊息關心我的作息，週末會視訊一下下就說訊號不好掛掉。最近他常提到他在做虛擬礦機的租賃，說機器放著就有穩定產出，他自己已經回本，還說跟著他認識的大戶進場更穩。他傳來一個平台的畫面，上面的收益數字每天都在跳。他說有個在那家平台做技術的朋友告訴他，下一波會漲，可以先小額試。我投了八萬，兩週後想把本金拿回來，他說境外的資金匯回要先做一次查核並繳費，不然會卡在那邊。我說我沒有多的錢，他說他可以先幫我墊一半。我看著那個數字。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "trust_building", "text": "每天問候作息，聊兩個多月才提投資"}, {"tag": "greed", "text": "說礦機放著就有穩定收入，半年回本"}]$rw$::jsonb
  WHERE case_key = $rw$investment-scam-004-v2$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "用每日噓寒問暖與甜蜜互動先建立感情依賴，再開口談投資"}, {"tag": "greed", "text": "以虛擬礦機穩定獲利、跟著大戶進場等高報酬話術誘你投入"}, {"tag": "authority", "text": "自稱平台技術員掌握內部資訊，並假借境外查核名義要求付款"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$畢業季找房子，我在社團看到一則套房貼文，照片乾淨明亮，租金比附近便宜一些，地點也剛好是我想住的區域。我加了自稱房東代理人的帳號，他回得很仔細，管理費和押金都講得清清楚楚。我說想約時間看房，他說今天就有三組人要來看，如果我有意願，要先付一個月租金當訂金把房間留住，看房之後再約。我問能不能看完再付，他說那就不能保證還在。他傳來一組帳號。我還沒去看過那間房。$rw$
  WHERE case_key = $rw$shopping-scam-003-v2$rw$ AND narrative = $rw$畢業季找房子，我在社團看到一則貼文，照片裡的套房整潔明亮，租金比周邊行情低一些，地點也剛好在我想要的區域。我加了貼文裡自稱房東代理人的帳號，對方回得很詳細，屋況、管理費、押金都講得清清楚楚。我說想約時間看房，他說最近詢問的人很多，今天就有三組要來看，如果我真的有意願，得先付一個月租金當訂金把房源鎖住，不然很可能被別人先租走，看房再約就好。我問可不可以看完房再付，他說那就不能保證還留著。他傳來一組帳號和一張他手寫的保留單照片。我還沒去看過那間房。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "time_pressure", "text": "說今天有三組人要看，要先付訂金留房"}, {"tag": "greed", "text": "租金比附近少一些，地點又剛好"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-003-v2$rw$ AND red_flags = $rw$[{"tag": "time_pressure", "text": "謊稱多組人同時詢問、機會難得，催促你在看房前先付訂金保留"}, {"tag": "trust_building", "text": "以偽造的匯款成功截圖假裝已退款，製造誠信假象拖延時間"}, {"tag": "greed", "text": "用租金合理、條件優渥的夢幻物件降低戒心、吸引急於找房的人"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在拍賣社團看到有人賣一台很難買到的遊戲主機，價格比市面便宜好幾千。我私訊問能不能面交，他一口答應，還說住得不遠，讓我覺得很有誠意。可是約了三次，每次都臨時有事改期。今天他說面交太麻煩了，叫我先匯款，他直接寄出比較快。他一次傳了三組不同銀行的帳號，說哪一家方便就用哪一家。我看著那三組帳號，想說要不要先匯。$rw$
  WHERE case_key = $rw$fake-sale-scam-003-v2$rw$ AND narrative = $rw$我在拍賣社團看到有人賣一款很難買到的商品，價格比市面便宜不少。我私訊問能不能面交，對方一口答應，讓我覺得很有誠意。但他約的地點都在很偏遠的地方，時間也一直喬不攏，前後改了三次都沒約成。今天他說面交實在太麻煩，不如我先匯款他直接寄出比較快，還說怕我不放心，可以先寄再付一半，但講完又改口說平台規定不行。他一次傳了三組不同銀行的帳號給我，說哪一家方便就用哪一家。我問為什麼有這麼多帳號，他說是不同的收款用途。商品的照片他倒是拍得很清楚。我看著那三組帳號。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "trust_building", "text": "先一口答應面交，讓人覺得有誠意"}, {"tag": "greed", "text": "很難買到的主機，比市面少好幾千元"}]$rw$::jsonb
  WHERE case_key = $rw$fake-sale-scam-003-v2$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "先假意願意面交營造誠意，降低戒心後再改口要求匯款"}, {"tag": "greed", "text": "以難買到的商品搭配低於市面的價格吸引買家"}, {"tag": "authority", "text": "提供多個不同帳戶並以金流有問題為由加收超商費用取信拖延"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$網路上認識一個多月的對象，很快就說要跟我在一起，每天噓寒問暖。這幾天他說有一筆工作的款項要從國外匯進來，但他的帳戶太久沒用被限制了，想先借我的帳戶收一下，等錢到了再轉給他，還會分我一部分當謝禮。他傳了一張匯款證明的照片，上面的金額有七位數。他說收外幣要先開通，叫我打開網路銀行，照他說的步驟設定。我把網銀打開了。$rw$
  WHERE case_key = $rw$romance-scam-002-v2$rw$ AND narrative = $rw$網路上認識一個多月的對象，很快就說要跟我在一起，每天噓寒問暖，講話也讓人放鬆戒心。這幾天他說他有一筆工作上的款項要從國外匯進來，金額不小，但他的帳戶因為久未使用被限制了，想先借我的帳戶收一下，等錢到了再轉給他，還說會分我一部分當作謝禮。他說收外幣要先開通，要我照他說的步驟打開網路銀行設定，或者到提款機輸入一組代碼開通收款功能。他傳了一份看起來像是匯款證明的文件照片給我，上面的金額有七位數。我說我想問一下銀行，他說那樣手續會拖很久，錢會被退回去。我把網銀打開了。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "trust_building", "text": "認識一個多月就說要在一起，每天噓寒問暖"}, {"tag": "greed", "text": "說借帳戶收款後會分我一部分當謝禮"}]$rw$::jsonb
  WHERE case_key = $rw$romance-scam-002-v2$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "認識不久就急著確立情侶關係，讓你放下戒心配合帳戶操作"}, {"tag": "authority", "text": "以開通外幣收款、系統設定等說法，誘導你依指示操作網銀或 ATM"}, {"tag": "greed", "text": "謊稱有一大筆錢要匯給你，以此誘使你借出帳戶或代收轉出"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$romance-scam-002-v2$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$我拿著號碼牌坐在銀行大廳，要臨櫃匯一筆三萬多元的款項。這筆是給合作廠商的貨款，契約上寫著收款戶名。輪到我之後，行員問我認不認識收款人、這筆錢是做什麼用的，還拿出一張表格逐項勾選，說金額到了就要問這些。旁邊還有人在等，我覺得自己好像被當成嫌疑犯。行員說如果我不方便回答，可以在表格上簽名確認。我看著那張表格，還在想要不要簽。$rw$
  WHERE case_key = $rw$atm-legit-011$rw$ AND narrative = $rw$我要到銀行臨櫃匯一筆三萬多元的貨款給合作對象。填好單子遞進去，櫃檯行員看了一眼，開始問我一連串問題：請問您認識這位受款人嗎、辦理這筆匯款的目的是什麼。我覺得有點被冒犯，說是工作上的往來，行員仍請我稍等，拿出一張表格逐項勾選，還說如果我不方便回答，需要請我在下面簽名確認與詐騙情形無關。旁邊有其他客人在等，我開始不太自在，覺得自己好像被當成嫌疑犯。行員全程沒有問我的密碼，也沒有碰我的提款卡，只說這是達到一定金額就要跑的程序。我看著那張要我簽名的表格，一時不確定該不該簽。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "行員只問收款人和用途，說金額到了就要問"}, {"tag": null, "text": "收款戶名寫在和廠商簽的契約上"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-011$rw$ AND red_flags = $rw$[{"tag": null, "text": "交易金額達新臺幣三萬元以上的匯款，銀行公會的臨櫃關懷提問參考範本本就要求行員詢問辦理動機與目的"}, {"tag": null, "text": "提問範圍限於是否認識受款人、辦理目的，全程不涉及密碼、卡片或簡訊驗證碼"}, {"tag": null, "text": "客戶拒答或情況異常時請客戶簽名確認與詐騙無關，是範本明定的處理方式，不是刁難"}, {"tag": null, "text": "行員研判客戶顯屬遭詐騙時會撥打 165 或向 110 報案，這是保護存戶的法定關懷機制"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$傍晚接到一通電話，對方說是某購物平台的客服，報得出我的姓名和上個月買的東西。他說是回覆我前兩天在程式裡問的會員方案。我打開購物程式，那張客服單還在，狀態寫著處理中。他說我上個月不小心勾到每月自動續訂的方案，可以在程式的會員頁自己取消，取消後就不會再扣。我點開會員頁，真的有一個每月續訂的方案和取消按鈕。我正在想要不要直接按取消。$rw$
  WHERE case_key = $rw$atm-legit-012$rw$ AND narrative = $rw$我在信用卡帳單上看到一筆沒印象的小額扣款，就照卡片背面印的號碼撥了客服。接通後對方請我核對出生年月日、戶籍地址，還要我說出最近三筆消費的商家與大概金額，問得很細，我一度覺得自己講出去的個資比對方多。我問能不能直接幫我把那筆退掉，他說爭議帳款要走書面申請，會把申請書寄到我的帳單地址，填完寄回或上傳到我自己登入的網銀。整通電話裡他沒有要我提供完整卡號，沒有提到任何簡訊驗證碼，也沒有叫我去操作 ATM。掛掉之前他還說，如果我對這通電話有疑慮，可以自己重打一次卡背號碼確認。我看著手機，想著剛剛講出去的那些資料。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：購物平台站內客服與自行取消訂閱的流程，對照假客服解除分期的手法$rw$
  WHERE case_key = $rw$atm-legit-012$rw$ AND provenance = $rw$改編自：金管會「提醒民眾防範信用卡遭詐騙盜刷」新聞稿與信用卡爭議帳款處理流程$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "客服單是我自己前兩天在程式裡開的"}, {"tag": null, "text": "會員頁看得到同一個方案，可以自己取消"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-012$rw$ AND red_flags = $rw$[{"tag": null, "text": "這通電話由你依卡片背面印製的號碼主動撥出，聯繫通道由你自己掌握而非對方指定"}, {"tag": null, "text": "身分核對只問你已知的個人資料與消費紀錄，不涉及完整卡號、密碼或簡訊驗證碼"}, {"tag": null, "text": "爭議帳款走書面申請並寄至既有帳單地址，不在通話中要求你即時操作任何裝置"}, {"tag": null, "text": "金管會宣導明示：金融機構不會以電話或簡訊要求你操作 ATM、登入網銀或提供驗證碼"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$atm-legit-012$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$下午接到一通電話，對方說是某購物網站的客服，說他們的系統遭到入侵，我的個資可能外洩了。他報得出我的姓名和最近一筆訂單，要我自己到購物程式裡改密碼。我打開購物程式，公告欄真的有同一則資料外洩的說明，請大家更改密碼，信用卡有疑問就撥卡片背面的電話。公告還寫著明天中午前沒改密碼，會先暫停購物帳號。我看著密碼欄位，電話還拿在手上。$rw$
  WHERE case_key = $rw$atm-legit-013$rw$ AND narrative = $rw$我在購物 App 下單後選了超商代碼繳費，隔天 App 推播提醒我付款期限剩兩小時，訂單頁上還有一個一直在跳的倒數計時。我點進去看，畫面顯示的是我當初自己選的繳費方式與一組繳費代碼，金額跟我下單時一樣。頁面下方寫著逾期未付款訂單會自動取消，商品回到庫存。我人在外面一時走不開，心裡有點急。整個過程沒有人打電話給我，App 裡也沒有出現任何要我改用其他方式付款、或到提款機操作的指示，推播點進去就是原本那張訂單。我盯著那個倒數，考慮要不要現在衝去超商。$rw$;
UPDATE public.game_cases SET provenance = $rw$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」$rw$
  WHERE case_key = $rw$atm-legit-013$rw$ AND provenance = $rw$改編自：電商訂單付款期限與超商代碼繳費之正常流程，對照解除分期詐騙的催促手法$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "購物程式的公告有同一則資料外洩說明"}, {"tag": null, "text": "只要我在程式裡改密碼"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-013$rw$ AND red_flags = $rw$[{"tag": null, "text": "倒數與期限出現在 App 訂單頁內，不是靠陌生來電或簡訊催促你"}, {"tag": null, "text": "付款方式仍是你下單時自己選定的，金額與訂單一致，未被要求變更"}, {"tag": null, "text": "逾期的後果只是訂單自動取消、商品回庫存，沒有威脅、罰款或額外費用"}, {"tag": null, "text": "全程沒有人指示你操作提款機或提供任何驗證碼"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在拍賣平台賣掉一件東西，買家很快就說已經付款了，還把轉帳畫面截圖給我看，可是我的賣家後台一直沒顯示入帳。我從程式的客服中心開了一張單，客服回覆說這筆訂單的錢由平台代管，買家按下收到貨之後才會撥給我，所以後台現在顯示的是待撥款。客服要我在單子裡補上出貨日期。我看了一下訂單頁，狀態真的寫著款項代管中。我正在填出貨日期。$rw$
  WHERE case_key = $rw$atm-legit-014$rw$ AND narrative = $rw$我在拍賣平台賣出一件商品，買家反映包裝有壓損，我在 App 裡開了客服工單。回覆我的客服很有耐心，還主動提到我上個月也開過一張關於運費的工單，說這次一併幫我看。他問得很細：出貨日期、包裝方式、有沒有拍照存證，來回聊了不少訊息，講話的方式讓我覺得他對我的帳號好像很熟。整段對話都在 App 的客服頁面裡，每一則訊息上方都掛著同一組工單編號，我退出去重新登入還是看得到同樣的紀錄。他請我把照片直接上傳到工單附件，沒有給我任何其他帳號，也沒有問我的銀行資料。我看著那串對話，想著要不要照他說的先上傳照片。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "客服單是我自己從程式的客服中心開的"}, {"tag": null, "text": "訂單頁寫著款項由平台代管，收貨後撥款"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-014$rw$ AND red_flags = $rw$[{"tag": null, "text": "對話全程在平台 App 的客服工單內，每則訊息都掛同一組工單編號"}, {"tag": null, "text": "登出後重新登入仍看得到同一份紀錄，聯繫通道可獨立驗證"}, {"tag": null, "text": "客服熟悉你的歷史工單，是因為讀得到平台後台紀錄，不是靠事先打聽你的資料"}, {"tag": null, "text": "未要求你加任何站外通訊帳號，也未詢問銀行帳戶或金流資訊"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$atm-legit-014$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$朋友把我拉進一個投資群組，群主每天都會貼盤前分析。今天群裡有人說，某家投信有一檔新基金只募集到這週五。我午休時去往來的銀行問，理專拿了公開說明書給我，上面寫的募集期確實到週五，也列了手續費和可能虧損的風險。他說這檔不保本，要先做風險屬性問卷，買的話從我自己的帳戶扣款。我把說明書帶回家，還在想要不要買。$rw$
  WHERE case_key = $rw$investment-legit-011$rw$ AND narrative = $rw$我到銀行臨櫃談定期定額，理專介紹一檔正在募集的基金，說募集期只到這週五，過了就要等下一檔。他把公開說明書和月報印給我，裡面有近幾年的報酬，也有一整頁在講最大跌幅與各項費用。我問如果賠了怎麼辦，他說這檔沒有保本也沒有保證獲利，虧損要自己承擔。他請我先填風險屬性評估問卷，說結果如果偏保守，有些商品他不能賣我。我說想回家再想想，他說沒問題，截止日就是截止日，他沒辦法幫我保留額度，要買的話我自己上網銀或再跑一趟臨櫃都可以。我拿著那疊紙走出銀行，還在猶豫。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "說明書上的募集期和群裡說的一樣到週五"}, {"tag": null, "text": "說明書列出手續費和可能虧損的風險"}, {"tag": null, "text": "申購從我自己的銀行帳戶扣款"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-011$rw$ AND red_flags = $rw$[{"tag": null, "text": "期限來自基金本身公告的募集期程，逾期即無法申購，業務並未宣稱能為你特別保留額度"}, {"tag": null, "text": "主動提供公開說明書與月報，揭露最大跌幅與各項費用，明確表示不保本、不保證獲利"}, {"tag": null, "text": "依規定先做風險屬性評估，並說明評估結果會限制可銷售給你的商品"}, {"tag": null, "text": "申購透過你自己的網銀或臨櫃完成，沒有要求你匯款到任何個人帳戶"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在網路上索取了一份免費的投資資料，留了聯絡方式，後來被拉進一個討論群組。群裡有人貼了一檔科技基金近三年的報酬，數字很漂亮，說最近很多人在買。我打開自己銀行的基金頁搜到這一檔，月報上也有它某一年跌了快四成的走勢，手續費和經理費都列在旁邊，還印著過去績效不代表未來。要買的話，錢從我在這家銀行的帳戶扣。我把那張下跌的圖存下來，想再看幾天。$rw$
  WHERE case_key = $rw$investment-legit-012$rw$ AND narrative = $rw$朋友介紹我認識一位在銀行做財富管理的理專，見面時他提到有一檔科技類型的基金近三年報酬相當亮眼，數字確實很吸引我。但他接著把另一張圖轉過來給我看，上面是同一檔基金在某一年跌掉將近四成的走勢，他說這種波動是這類商品的常態，要我先想清楚能不能承受。他把手續費、經理費、保管費逐項念了一遍，還說過去績效不代表未來表現，這句話文件上也印著。我問他能不能保證一年至少賺回本金，他直接說不行，任何人這樣講都有問題。他讓我把資料帶回去，說不急。我回到家把那疊文件攤在桌上，盯著那張下跌的走勢圖。$rw$;
UPDATE public.game_cases SET provenance = $rw$依據：金融商品銷售之風險預告與費用揭露義務$rw$
  WHERE case_key = $rw$investment-legit-012$rw$ AND provenance = $rw$改編自：金融商品銷售之風險預告與費用揭露義務，對照保證獲利話術$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "銀行的月報列出這檔某一年跌了快四成"}, {"tag": null, "text": "手續費和經理費都列在基金頁上"}, {"tag": null, "text": "要買只能從我自己的銀行帳戶扣款"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-012$rw$ AND red_flags = $rw$[{"tag": null, "text": "談報酬的同時主動出示最大跌幅走勢，並說明波動是該類商品的常態"}, {"tag": null, "text": "逐項揭露手續費、經理費與保管費，並指出過去績效不代表未來表現"}, {"tag": null, "text": "明確拒絕做出保本或保證獲利的承諾，並指出這類承諾本身就有問題"}, {"tag": null, "text": "不催促決定，讓你把完整書面資料帶回考慮"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我應徵一份寫著高佣金的代銷工作，對方約我到辦公室面談。報到那天，人資拿出勞動契約，上面寫了底薪、佣金怎麼算和每個月幾號發薪。她要我附一張存摺封面的影本，說薪水要轉進這個帳戶。我有點緊張，因為看過新聞說有人用找工作騙走帳戶，就問她為什麼需要我的帳戶，她說只是設定薪轉，存摺和提款卡我自己留著。我拿著那張表格，還在想要不要把影本交出去。$rw$
  WHERE case_key = $rw$investment-legit-013$rw$ AND narrative = $rw$我應徵上一份行政職，到職第一天人資把我帶到辦公室，拿出一疊表格要我填，其中一項要我附上存摺封面影本，說是要設定薪資轉帳。我想到新聞上有人因為工作名義被騙走帳戶，整個人警覺起來，直接問她為什麼需要我的帳戶。她說薪水要匯進去，不然沒辦法發薪，並把勞動契約、勞健保加保申報表一起攤開給我看，上面有公司名稱與地址。我注意到她只要影本，沒有要我交出存摺正本，也沒有提到提款卡或密碼，更沒有要我把任何東西寄到別的地方。整個過程在公司的人資辦公室進行，旁邊還有其他同事走動。我拿著那張表格，一時不知道該不該填。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "勞動契約寫明底薪、佣金算法和發薪日"}, {"tag": null, "text": "只要存摺封面影本，用來設定薪資轉帳"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-013$rw$ AND red_flags = $rw$[{"tag": null, "text": "只索取存摺封面影本供薪資轉帳設定，未要求交付存摺正本、提款卡或密碼"}, {"tag": null, "text": "同時提供勞動契約與勞健保加保申報表，公司資訊可對外查證"}, {"tag": null, "text": "程序在公司辦公室當面進行，不是要你把證件或卡片寄送到指定地址"}, {"tag": null, "text": "人頭帳戶要能拿來用，靠的是實體卡片與密碼，影本本身無法操作帳戶"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$investment-legit-013$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$交友軟體上認識一位在國外工作的對象，聊了兩個多月，他每天都會傳訊息問我吃飯沒、睡得好不好。最近他提到自己每個月固定買一檔市值型的 ETF，已經扣款好幾年了，說他很多同事也在買。我問要怎麼開始，他叫我用自己的券商程式搜這檔的代號，看看成分股和費用，想買再自己設定定期定額。我問他能不能幫我買，他說這要我自己開戶，他也幫不上忙。我打開券商程式的開戶頁面，想了一下。$rw$
  WHERE case_key = $rw$investment-legit-014$rw$ AND narrative = $rw$最近午休時同事一直在聊某檔市值型 ETF，說很多人在買，有人已經扣款好幾年了。聽多了我也有點心動，就多問了幾句。同事給我的不是什麼帶單群組，而是叫我自己去交易所網站查那檔的成交量與成分股，說資料都是公開的，他也把自己在券商 App 裡的下單畫面給我看了一眼，說流程就是這樣，自己開戶自己下單。我問他要不要幫我操作，他說他碰不到我的錢也不想碰，券商戶頭本來就只有我自己登得進去。他沒有提到任何老師、封閉群組或內線消息，也沒有說買了穩賺。我打開券商 App 的開戶頁面，停在那裡想了一下。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：上市 ETF 之公開資訊查詢與自主下單流程，對照交友投資話術$rw$
  WHERE case_key = $rw$investment-legit-014$rw$ AND provenance = $rw$改編自：上市 ETF 之公開資訊查詢與自主下單流程，對照跟單群組話術$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "他叫我用自己的券商程式查這檔的資料"}, {"tag": null, "text": "開戶和下單都由我在自己的券商帳戶操作"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-014$rw$ AND red_flags = $rw$[{"tag": null, "text": "標的是公開掛牌商品，成交量與成分股可在交易所網站自行查證，不需仰賴他人說法"}, {"tag": null, "text": "開戶與下單都在你自己的券商帳戶完成，推薦者無法接觸你的資金"}, {"tag": null, "text": "沒有帶單老師、封閉群組或內線消息，也沒有任何穩賺承諾"}, {"tag": null, "text": "推薦者不因你是否下單而獲得任何報酬"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$在網路上認識三個月的對象自稱是駐外的軍醫，每天早晚都傳訊息來，前陣子就說想跟我結婚。我說想先看看他，他當天晚上就開了視訊，背景是營區的醫務室，還把識別證翻給我看。他說下個月休假回國，把機票的訂位紀錄傳給我，約我他回來那週在我家附近的餐廳吃飯，也想見見我爸媽。我看著那張訂位紀錄，想著要不要答應讓他見家人。$rw$
  WHERE case_key = $rw$romance-legit-011$rw$ AND narrative = $rw$我在交友軟體上認識一位對象，聊了一陣子他說自己是醫師。我看過太多假冒醫師、軍人的新聞，心裡直接打了問號。我半開玩笑地說想看看他上班的樣子，他當天下班就開了視訊，背景確實是醫院走廊，還把識別證翻過來讓我看了一下姓名。過陣子我們約在他工作醫院附近的咖啡廳見面，他準時到，長相跟照片一樣。他提過幾次值班很累、想找人吃飯，但從沒用醫師的身分要我做什麼，也沒提過任何投資、代收包裹或資金週轉。我自己上衛福部的醫事人員查詢頁，用他的姓名查了一下。我盯著查詢結果，想著這樣算不算確認完了。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：正常網路交友的視訊與見面查證方式，對照冒用高社經身分的交友詐騙$rw$
  WHERE case_key = $rw$romance-legit-011$rw$ AND provenance = $rw$改編自：衛福部醫事人員查詢等公開查證管道，對照冒用高社經身分的交友詐騙$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "當天就開視訊，讓我看工作的地方和識別證"}, {"tag": null, "text": "傳來回國機票的訂位紀錄，約好見面"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-011$rw$ AND red_flags = $rw$[{"tag": null, "text": "願意即時視訊，並出示可辨識的工作場景與識別證"}, {"tag": null, "text": "約在真實地點當面見面且準時出現，外貌與照片一致"}, {"tag": null, "text": "執業身分可透過主管機關的醫事人員查詢頁獨立查證，不需仰賴對方單方說法"}, {"tag": null, "text": "從未以職業身分要求你做任何事，也未提及投資、代收包裹或資金往來"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$romance-legit-011$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$網路上認識一個多月的對象，很快就說要跟我在一起，每天噓寒問暖。這幾天他說有一筆工作的款項要從國外匯進來，但他的帳戶太久沒用被限制了。他說銀行要他本人補一份工作合約，他已經從銀行的網站上傳，還把銀行回覆的信給我看，寫著三個工作天內會審完。他說錢到了想約我吃飯慶祝。我看著那封信，想著要不要答應週末跟他見面。$rw$
  WHERE case_key = $rw$romance-legit-012$rw$ AND narrative = $rw$交往快一年，有天吃飯時他說這個月機車修理花掉太多，問我能不能先借他五千，下個月發薪就還。我心裡警鈴大作，因為新聞上被騙的幾乎都是從借錢開始的。我沒有馬上答應，他也沒有再追問，只說不方便就算了，還把話題轉開。過幾天他自己提起這件事，從包包拿出一張寫好的借據，上面有金額、日期跟他的簽名，說這樣我比較好處理。他要我把現金直接交給他本人就行，沒有給我任何帳號，也沒有提到什麼第三方代收或幫朋友轉帳。他人就坐在我對面，證件我看過，家人我也見過。我看著那張借據，還在猶豫要不要借。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：銀行本人帳戶補件流程，對照借用帳戶與代轉款項的交友詐騙$rw$
  WHERE case_key = $rw$romance-legit-012$rw$ AND provenance = $rw$改編自：一般人際間小額借貸之常見樣態，對照借用帳戶與代轉款項的交友詐騙$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "帳戶的問題由他自己向銀行補件"}, {"tag": null, "text": "銀行回信寫明三個工作天內審完"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-012$rw$ AND red_flags = $rw$[{"tag": null, "text": "開口的對象是你認識本人、見過家人的人，不是只在網路上聯繫的身分"}, {"tag": null, "text": "被拒絕時沒有追問或情緒勒索，也沒有製造任何急迫感"}, {"tag": null, "text": "主動提出書面借據載明金額與日期，金額具體且用途明確"}, {"tag": null, "text": "以現金當面交付本人，沒有出現第三方帳戶、代收或代為轉帳的環節"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$romance-legit-012$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$交友軟體上認識的對象看起來很體面，聊了三個月，每天噓寒問暖，也常分享他的生活。這陣子他開始聊到理財，說他在一家有登記的交易所買一點虛擬貨幣，價格起伏很大，他也虧過。我問能不能跟著買，他說想試的話，自己先查那家交易所在不在金管會的名單上，再用自己的帳戶開戶，他不會幫我操作。我打開金管會的網站，正在找那份名單。$rw$
  WHERE case_key = $rw$romance-legit-013$rw$ AND narrative = $rw$認識三個月的對象問我要不要一起去花蓮兩天一夜，他說看中的民宿只剩一間，免費取消期限到這週五，希望我週五前給他答覆。被催的感覺讓我有點不舒服，催促這件事本身就讓我提高戒心。我說我要看班表，他說好，那就等我，如果來不及就換別的日子或不去也沒關係。他把訂房頁面截圖傳給我，上面確實寫著免費取消期限，是訂房平台的規則，不是他自己訂的規矩。他說房費各付各的，他先訂再跟我拆，或者我自己訂一間也可以。整段對話裡沒有出現任何要我先把錢給他的環節。我看著班表，還在算週五前排不排得出來。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：合法虛擬資產業者之登記查詢與本人開戶流程，對照以理財為名的交友詐騙$rw$
  WHERE case_key = $rw$romance-legit-013$rw$ AND provenance = $rw$改編自：訂房平台免費取消期限之一般規則，對照以急迫感推動匯款的交友詐騙$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "交易所查得到登記，開戶要用自己的帳戶"}, {"tag": null, "text": "他說價格起伏很大，自己也虧過"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-013$rw$ AND red_flags = $rw$[{"tag": null, "text": "期限來自訂房平台公告的免費取消規則，可在頁面上自行查證，不是對方自訂"}, {"tag": null, "text": "被拒絕或要求延後時對方接受，並主動提出改期或取消的選項"}, {"tag": null, "text": "費用各自負擔，沒有要求你先把款項交給對方"}, {"tag": null, "text": "催促的內容是行程決定，完全不涉及任何金錢移轉"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$在交友軟體上聊了兩個多月的對象說要寄一份禮物給我，是他在國外買的一只手錶。今天我收到快遞公司的簡訊，說包裹要繳約四千元的進口稅費。我打開手機裡原本就有的那家快遞的程式，輸入運單號碼，查到同一件包裹和一樣的稅額，可以在程式裡刷卡，也可以送到時付給司機。對象說稅費本來就是收件人繳，他下次見面再把錢給我。我正在選要用哪一種方式付。$rw$
  WHERE case_key = $rw$romance-legit-014$rw$ AND narrative = $rw$交往對象工作常出差，這次去日本前問我想要什麼，我隨口說了個牌子的護唇膏。回國那天他直接約我吃飯，把東西當面拿給我，是個小紙袋，裡面除了護唇膏還有一盒點心。他提到在機場排了很久，還給我看了收據。整個過程裡他沒有要我提供地址收包裹，沒有說有什麼東西被海關扣住，也沒有提到任何關稅、手續費或要我先幫他墊錢。他之前送過幾次小東西，都是當面給的實體物品。這次他倒是說行李超重多付了一點錢，但語氣像在抱怨，沒有要我分攤的意思。我拿著那個紙袋，想到最近看到的包裹新聞。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "快遞程式裡查得到同一件包裹和稅額"}, {"tag": null, "text": "稅費在快遞程式裡付，或送到時付給司機"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-014$rw$ AND red_flags = $rw$[{"tag": null, "text": "禮物是當面交付的實體物品，不需要你提供地址或代為收取包裹"}, {"tag": null, "text": "未出現海關扣件、關稅、清關費或代墊款項等任何要求"}, {"tag": null, "text": "提及的額外支出僅為對方自己負擔的行李費用，並未要求你分攤"}, {"tag": null, "text": "金錢自始至終沒有經由你的帳戶流動"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在社群的買賣社團看到有人賣一台遊戲主機，價格比行情低了將近一半，附了幾張機器的照片。我留言問，賣家說他是在購物平台開店的二手商家，這台是拆封過的福利品，請我到賣場下單。賣場頁寫著外盒有壓痕、機身有一道刮痕，都附了照片，保固只剩三個月。結帳走平台的購物車，收到貨七天內可以退。我把刮痕照片放大看了一下，手指停在下單鍵上。$rw$
  WHERE case_key = $rw$shopping-legit-011$rw$ AND narrative = $rw$我在購物平台看到一副想很久的耳機，標價只有市價四成，便宜到我第一個念頭是有問題。點進去商品頁，標題就寫著拆封福利品，描述欄列了三點：外盒有壓痕、機身左側有一道細刮痕、保固從六個月改為三個月，每一點都附了近拍照片。頁面下方有平台的退貨說明，寫著收到商品七日內可辦理退貨。賣家的評價頁點得進去，有好評也有幾則抱怨出貨慢的三星評價。下單流程是平台的購物車與金流，沒有跳出任何要我加通訊軟體或匯款到個人帳戶的指示。我把那三張刮痕照片放大又看了一遍，手指停在下單鍵上。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "賣家請我到購物平台的賣場下單"}, {"tag": null, "text": "瑕疵和保固都寫在賣場頁，附了照片"}, {"tag": null, "text": "結帳走平台購物車，七天內可以退"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-011$rw$ AND red_flags = $rw$[{"tag": null, "text": "低價有具體且可查證的原因：拆封福利品，瑕疵逐項列出並附近拍照片"}, {"tag": null, "text": "保固條件的差異事先揭露，不是收到貨之後才告知"}, {"tag": null, "text": "通訊交易依消費者保護法第十九條享有收受商品後七日內解除契約的權利，平台頁面載明退貨流程"}, {"tag": null, "text": "全程走平台購物車與金流，未被引導至站外或個人帳戶付款"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 1
  WHERE case_key = $rw$shopping-legit-011$rw$ AND difficulty = 2;
UPDATE public.game_cases SET narrative = $rw$我在社群平台看到有人在賣一款一直搶不到的熱門商品，留言之後對方私訊傳來一組連結，說是超商寄貨便的交易頁面。頁面上有商品名稱、價格和運費，付款方式寫的是到超商取貨時再付錢。我填了收件人和取貨門市，頁面寫著送出後會有一組訂單編號，可以查寄送進度。頁面上方還寫著這個價格只到今晚。我看了一下取貨門市，還沒按送出。$rw$
  WHERE case_key = $rw$shopping-legit-012$rw$ AND narrative = $rw$打開購物 App，首頁掛著一個一直在跳的倒數計時，寫著年中慶最後幾小時。我對這種倒數向來反感，總覺得是在逼人下單。我點進活動頁看了看，上面列出活動期間的起訖日期，底下是一整排不同賣家的商品，每一件都點得進賣場，看得到賣家名稱、評價與退換貨說明。我挑的那件商品下單時，付款方式是我原本就綁的信用卡，沒有跳出任何要我改用其他方式的提示，也沒有人私訊我。結帳頁顯示的金額跟商品頁一致，系統給了訂單編號。倒數還在跳，我看著購物車，想著到底是真的想買還是被氣氛推著走。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：超商寄貨便取貨付款流程，對照仿冒寄貨便頁面的手法$rw$
  WHERE case_key = $rw$shopping-legit-012$rw$ AND provenance = $rw$改編自：電商官方檔期活動之一般揭露方式，對照一頁式網站的倒數催促$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "付款方式是到超商取貨時才付"}, {"tag": null, "text": "送出後有訂單編號，可以查寄送進度"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-012$rw$ AND red_flags = $rw$[{"tag": null, "text": "倒數對應公告的活動起訖期間，是全站一致的檔期，不是針對你個人的限時威脅"}, {"tag": null, "text": "活動頁可點進每個賣場查看賣家資訊、評價與退換貨說明"}, {"tag": null, "text": "付款方式維持你原本綁定的管道，未被要求變更為其他方式"}, {"tag": null, "text": "結帳金額與商品頁一致，並產生可查詢的訂單編號"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$畢業季找房子，我在社團看到一則套房貼文，照片乾淨明亮，租金比附近便宜一些，地點也剛好是我想住的區域。我聯絡貼文上的屋主，約了週末看房。屋主本人來開門，我看了格局和採光，也試了水壓。他說如果確定要租，要先付一個月租金當訂金，他就不再帶別人看。我請他給我看權狀和身分證，名字和地址都對得上。他拿出一張訂金單，寫了金額、保留到哪天，還有沒簽約的話訂金怎麼退。我拿著訂金單，還沒決定要不要付。$rw$
  WHERE case_key = $rw$shopping-legit-013$rw$ AND narrative = $rw$我在租屋網看到一間套房，約了時間去看。屋主本人到場開門，我進去看了格局、水壓和窗戶採光，問了管理費怎麼算。談定後他說如果我確定要租，先付一個月租金當訂金保留，他就不再帶人看房。要先付錢這件事讓我立刻繃緊神經。我提出想看房屋權狀跟他的證件，他直接拿出來讓我核對，地址和名字都相符。他拿出一份書面契約，上面寫明訂金金額、保留期限，以及如果最後沒有簽約，訂金要怎麼處理。錢是當場交給他本人，他當場開了一張收據，上面有他的簽名。我拿著那張收據，還在想這樣到底穩不穩。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "已經實際看過房子，屋主本人到場"}, {"tag": null, "text": "權狀和身分證上的名字、地址對得上"}, {"tag": null, "text": "訂金單寫明金額、保留期限和退還方式"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-013$rw$ AND red_flags = $rw$[{"tag": null, "text": "你已當場看過房屋實體並確認屋況，不是只看照片就先付款"}, {"tag": null, "text": "出租人本人到場，權狀與證件可當場核對，姓名與地址相符"}, {"tag": null, "text": "訂金金額、保留期限與未簽約時的處理方式，都載明於書面契約"}, {"tag": null, "text": "款項當面交付本人並取得載有簽名的收據，不是匯入未曾見面者提供的帳戶"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$shopping-legit-013$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$我想幫角色買一件稀有裝備，在遊戲頻道問了一句，有個人主動私訊我。他對版本改動和掉寶機率都很熟，我問什麼他都答得出來。他說手上剛好有一件，要我加通訊軟體，先傳幾張屬性截圖給我看，因為頻道傳圖會糊掉。看完截圖，他說要買的話他會掛到遊戲的交易市集，價格照市集行情，手續費由系統扣。我在市集找到他掛的那件，屬性和截圖一樣，還沒按購買。$rw$
  WHERE case_key = $rw$shopping-legit-014$rw$ AND narrative = $rw$我在平台看上一張二手書桌，私訊問賣家尺寸。他回得很快，還主動拍了捲尺貼在桌面的照片給我。一來一往聊了三天，他問我房間門寬多少、要不要幫我拆桌腳，聊到最後還加了通訊軟體傳照片，因為平台傳圖會壓縮。加好友那一刻我有點警覺，很多糾紛就是從加通訊軟體開始的。但聊天內容全都是尺寸和搬運方式，他反而主動說金流還是走平台，他不收私下轉帳，這樣雙方都比較清楚。下單時我用的是平台的購物車，運費按平台的貨運選項計算，訂單頁看得到出貨進度。我把桌子加進購物車，又看了一次他的評價。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "通訊軟體只拿來傳屬性截圖"}, {"tag": null, "text": "裝備掛在遊戲交易市集，照市集行情"}, {"tag": null, "text": "付款和交貨都走遊戲內建的市集"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-014$rw$ AND red_flags = $rw$[{"tag": null, "text": "加站外通訊軟體僅用於傳送未壓縮照片，交易本身完全沒有離開平台"}, {"tag": null, "text": "賣家主動拒收私下轉帳，堅持金流走平台系統"}, {"tag": null, "text": "下單、運費計算與出貨進度都在平台訂單系統內可查詢"}, {"tag": null, "text": "對話內容集中在商品規格與搬運方式，未涉及帳戶或匯款"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$shopping-legit-014$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$我在社群動態看到一則廣告，說某個名牌包在做出清特賣，價格低得讓我多看了兩眼。點進去是一家有公司名稱和統一編號的網路商店，這款包還可以免費燙印名字縮寫。頁面寫著燙印過的商品不能退，結帳前還跳出一個框，要我勾選已經看過這項說明。客服電話和退換貨規定都寫在頁面上，付款可以刷卡或貨到付款。我停在那個勾選框前面，還在想要不要燙字。$rw$
  WHERE case_key = $rw$fake-sale-legit-011$rw$ AND narrative = $rw$我在網路上訂做一個刻名字的皮革鑰匙圈。商品頁最上方就有一行紅字，寫著本商品為依消費者要求所為之客製化給付，不適用通訊交易七日解除權。看到不能退，我第一個反應是這會不會是想賴帳。我往下滑，頁面把製作流程、可選字體、預計工作天都列出來了，結帳前系統還跳出一個確認框，要我勾選已閱讀不適用七日解除權的說明才能送出訂單。賣場有公司名稱與統一編號，客服管道和退換貨政策也都在頁面上。金流走平台，結帳後拿到訂單編號。我停在那個勾選框前面，手指懸著沒按下去。$rw$;
UPDATE public.game_cases SET provenance = $rw$依據：消費者保護法第 19 條但書與「通訊交易解除權合理例外情事適用準則」第 2 條$rw$
  WHERE case_key = $rw$fake-sale-legit-011$rw$ AND provenance = $rw$改編自：消費者保護法第 19 條但書與「通訊交易解除權合理例外情事適用準則」第 2 條$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "燙印後不能退的說明在結帳前就跳出來"}, {"tag": null, "text": "頁面有公司名稱、統一編號和客服電話"}, {"tag": null, "text": "付款可以刷卡或貨到付款"}]$rw$::jsonb
  WHERE case_key = $rw$fake-sale-legit-011$rw$ AND red_flags = $rw$[{"tag": null, "text": "依消費者要求所為之客製化給付，是通訊交易解除權合理例外情事適用準則明定的例外之一"}, {"tag": null, "text": "例外情事必須由業者事先告知才成立，此處在商品頁與結帳確認框都明確揭露"}, {"tag": null, "text": "賣場登載公司名稱、統一編號、客服管道與退換貨政策，可對外獨立查證"}, {"tag": null, "text": "金流走平台並產生訂單編號，未引導你到站外付款"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 1
  WHERE case_key = $rw$fake-sale-legit-011$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$我在社群平台的賣場掛賣一台相機，有位買家透過聊天系統聯繫，談得很順，還指定要用某個物流平台寄送，說他常用、比較放心。談好價錢後，他在那個物流平台下了單，我收到通知說訂單成立，請我三天內寄出。我打開那個物流平台的程式，訂單頁有他下單的紀錄，貨款寫著由平台代收，等買家取貨後才撥到我綁定的帳戶。頁面要我補的只有寄件人電話。我正在包相機，還沒拿去寄。$rw$
  WHERE case_key = $rw$fake-sale-legit-012$rw$ AND narrative = $rw$我在拍賣平台賣出一台相機，買家收到後說鏡頭有黴。隔天平台客服主動在站內傳訊息給我，說已經受理買家的爭議申請，要我補充出貨前的照片。有人主動聯繫我談金流爭議，我立刻警覺。我退出對話，自己從 App 主選單點進客服中心，那筆爭議案件確實列在裡面，案件編號跟訊息裡的一樣。訊息從頭到尾沒有要我加任何通訊帳號，沒有給我外部連結，也沒有問我的銀行帳號或要我先退款。他只說買賣雙方的說明都收到後，平台會依爭議處理規則判定，款項在判定前先留在平台。我把出貨那天拍的照片翻出來，想著要不要現在就傳。$rw$;
UPDATE public.game_cases SET provenance = $rw$改編自：物流平台代收貨款與款項保留機制，對照假冒客服與假物流的賣家陷阱$rw$
  WHERE case_key = $rw$fake-sale-legit-012$rw$ AND provenance = $rw$改編自：拍賣平台爭議處理與款項保留機制，對照假冒客服與假物流的賣家陷阱$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "訂單和代收貨款都查得到，在物流平台的程式裡"}, {"tag": null, "text": "貨款等買家取貨後才撥到我的帳戶"}, {"tag": null, "text": "要補的只有寄件人電話"}]$rw$::jsonb
  WHERE case_key = $rw$fake-sale-legit-012$rw$ AND red_flags = $rw$[{"tag": null, "text": "同一筆爭議可從 App 主選單的客服中心獨立找到，案件編號一致，聯繫來源可驗證"}, {"tag": null, "text": "客服未提供任何外部連結或站外通訊帳號，全程在站內訊息進行"}, {"tag": null, "text": "未詢問你的銀行帳號，也未要求你在判定前自行退款或轉帳"}, {"tag": null, "text": "款項於爭議判定前由平台保留，依平台既有規則處理"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$fake-sale-legit-012$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$我在拍賣社團看到有人賣一台很難買到的遊戲主機，價格比市面便宜好幾千。賣家說是尾牙抽到的，自己已經有一台，還拍了外盒封膜的照片。我問能不能面交，他說他住南部不方便，可以用超商店到店寄，我到店取貨時再付錢，沒去領就會退回給他。他沒給我任何帳號，只說東西賣掉就會下架。我看著那張封膜照片，想著要不要下單買下來。$rw$
  WHERE case_key = $rw$fake-sale-legit-013$rw$ AND narrative = $rw$我在拍賣上看到一台很難買到的遊戲主機，價格比市面低了幾千塊。賣家在商品描述裡寫著是尾牙抽到的，自己已經有一台所以出售，還拍了外盒封膜的照片。低於行情這件事讓我提高警覺，我直接問他能不能面交。他說他住南部不方便，但可以走超商店到店的代收貨款，我到店取貨時當場付錢，不用先轉帳。我查了那個運送方式，確實是物流業者提供的服務，包裹沒領就退回，款項也不會事先出去。他沒有給我任何個人帳戶，也沒有催我今天一定要決定，只說賣掉就下架。我看著那張封膜照片，想著要不要下單。$rw$;
UPDATE public.game_cases SET provenance = $rw$依據：超商店到店取貨付款服務說明，對照多帳戶分散收款的假賣家$rw$
  WHERE case_key = $rw$fake-sale-legit-013$rw$ AND provenance = $rw$改編自：超商店到店代收貨款服務之交易保護機制，對照多帳戶分散收款的假賣家$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "到超商取貨時才付錢，沒領就退回"}, {"tag": null, "text": "賣家沒給任何帳號，不用先轉帳"}]$rw$::jsonb
  WHERE case_key = $rw$fake-sale-legit-013$rw$ AND red_flags = $rw$[{"tag": null, "text": "採用超商店到店代收貨款，取貨時才付款，款項不會事先匯出"}, {"tag": null, "text": "未提供任何個人帳戶，也未要求先付訂金、保證金或解鎖費"}, {"tag": null, "text": "低價有具體說明並附外盒封膜照片，說法可與商品狀態相互對照"}, {"tag": null, "text": "未製造限時決定的壓力，也未阻止你選擇其他交易方式"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我滑到一個賣珠寶的直播，主播在講解一只玉鐲的成色，留言區一直有人刷加一，看起來搶得很兇。這場直播開在我常用的購物平台裡。主播說要買的點畫面下方的商品卡，我點進去是平台的商品頁，寫了材質、尺寸和一處小瑕疵，也附了鑑定書的照片，退換貨規定在最下面。結帳走平台的購物車，付款是我原本綁的方式。我把鐲子加進購物車，停在結帳頁。$rw$
  WHERE case_key = $rw$fake-sale-legit-014$rw$ AND narrative = $rw$我滑到一個賣二手精品包的直播，主播在講解一個包的成色，留言區不停有人刷加一，看起來搶得很兇。這種一堆人搶的畫面讓我想到暗樁，心裡先扣了分。但我注意到這場直播是開在購物平台自己的直播購物功能裡，不是社群平台上的私人直播。主播說要買的人點畫面下方的商品卡進去下單，我點了一下，跳出來的是平台的正式商品頁，有價格、賣場名稱、評價和退換貨說明，結帳走平台金流。主播中間講了一句，說不接受私訊匯款，要買就從商品卡走。留言區還是一直在刷。我把那個包加進購物車，停在結帳頁。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "直播開在我常用的購物平台裡"}, {"tag": null, "text": "商品卡連到平台商品頁，寫了材質和瑕疵"}, {"tag": null, "text": "結帳走平台的購物車"}]$rw$::jsonb
  WHERE case_key = $rw$fake-sale-legit-014$rw$ AND red_flags = $rw$[{"tag": null, "text": "直播開設在購物平台官方的直播購物功能內，而非站外的私人直播間"}, {"tag": null, "text": "下單經由平台正式商品頁，可查看價格、賣場資訊、評價與退換貨說明"}, {"tag": null, "text": "主播明確拒絕私訊匯款，交易必須經過平台金流"}, {"tag": null, "text": "留言熱度不影響交易通道，結帳流程與一般平台訂單完全相同"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$fake-sale-legit-014$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$我滑到一場賣絕版模型的直播，主播把盒裝商品拿在鏡頭前轉了一圈，留言區接連有人喊編號，也有人貼出之前收到貨的照片。主播說要買的加他的私人帳號下單。我加了之後，他說我選的款式只剩最後兩盒，已經有人在問，要我先把全額匯到親友的帳戶，備註不要寫商品名稱，收到錢就寄。我問能不能用平台結帳，他說這一輪結束就不保留了。我打開了轉帳頁。$rw$
  WHERE case_key = $rw$fake-sale-scam-022$rw$ AND narrative = $rw$我滑到一場販售絕版模型的直播，主播把盒裝商品拿在鏡頭前轉了一圈，留言區接連有人喊編號，也有帳號貼出先前收貨照片。主播說平台會抽取太多費用，得加他的私人通訊帳號才能拿到直播價格。我加好友後，他傳來另一段倉庫影片，說我選的款式只剩最後兩盒，已有買家正在問。他要求先匯全額到親友帳戶，備註不要寫商品名稱，收到款項就安排寄出。我提出使用平台結帳，他說那樣價格要加回去，而且這一輪結束便不再保留。我一邊看留言繼續跳出成交編號，一邊打開轉帳頁。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "social_proof", "text": "留言接連喊編號，還有人貼收貨照片"}, {"tag": "time_pressure", "text": "說只剩最後兩盒，這輪結束不保留"}]$rw$::jsonb
  WHERE case_key = $rw$fake-sale-scam-022$rw$ AND red_flags = $rw$[{"tag": "social_proof", "text": "留言帳號接連喊編號並貼出收貨照片"}, {"tag": "greed", "text": "用避開平台費用換取較低直播價格"}, {"tag": "time_pressure", "text": "聲稱僅剩兩盒且本輪結束不再保留"}, {"tag": "authority", "text": "要求匯至親友帳戶且備註避開商品名稱"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我從社群廣告點進一個賣廚房家電的頁面，價格大概是市面的一半，買了還送一組耗材。我把商品放進購物車後，一個自稱網站客服的人從通訊軟體傳訊息給我，說刷卡系統今天在維護，折扣訂單要改用轉帳才算數。他給的收款人是一個人的名字。我回到網站想找公司資料，只看到客服的帳號，找不到公司名稱。我已經輸入金額，正在核對戶名。$rw$
  WHERE case_key = $rw$shopping-scam-021$rw$ AND narrative = $rw$我從社群廣告點進一個賣廚房家電的頁面，價格約是市面的一半。商品下方排著大量五星評價，不少留言附上開箱照，頁面頂端的庫存數字一直往下跳。我把商品放進購物車後，客服從通訊軟體聯繫，說刷卡系統維護中，今天的折扣訂單改用轉帳才成立。他給的收款人是個人姓名，還說轉完可再送一組耗材。我回到網站想找公司資料，只看到客服帳號和一張模糊的登記證明。客服接著傳來別人完成付款的畫面，提醒庫存只保留十五分鐘。我已輸入金額，正在核對戶名。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "價格約是市面一半，還加送一組耗材"}, {"tag": "authority", "text": "自稱網站客服，說刷卡系統今天維護"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-021$rw$ AND red_flags = $rw$[{"tag": "social_proof", "text": "商品頁堆疊五星留言與重複的開箱照片"}, {"tag": "greed", "text": "標價約為市面一半並加送整組耗材"}, {"tag": "authority", "text": "以刷卡系統維護為由改收私人轉帳"}, {"tag": "time_pressure", "text": "庫存數字跳動並只保留購物車十五分鐘"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在社群看到一間工作室接受生日蛋糕預購，貼文上寫著工作室的名稱，作品照片正是家人喜歡的風格。私訊後，店家很快傳來口味表和設計草圖，又傳了幾張其他客人已經付訂、在等取貨的留言截圖。他說客製蛋糕要先付全額，給的是一個私人帳戶，也沒有訂單可以看。他說下週只剩一個空檔，今晚付款才排得進去。我問工作室在哪裡、怎麼取貨，他說付款後再通知。我停在轉帳頁，草圖還開在另一個視窗。$rw$
  WHERE case_key = $rw$shopping-scam-022$rw$ AND narrative = $rw$我在社群看到一間工作室接受生日蛋糕預購，作品照片風格正是家人喜歡的樣子。私訊後，店家很快傳來口味表與設計草圖，說客製品需要先付全額，而且一旦排入製作就不適用七日退貨。我能理解客製商品有例外，但對方沒有讓我從原本的商店頁結帳，而是提供一個私人帳戶，也不願開立載明尺寸、取貨日與退款條件的訂單。他說下週只剩一個製作空檔，要我今晚付款才排得進去。我詢問是否有工作室地址或取貨方式，他只回覆付款後再通知。我停在轉帳頁，草圖還開在另一個視窗。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "social_proof", "text": "店家傳來其他客人已付訂的留言截圖"}, {"tag": "time_pressure", "text": "說今晚付款才排得進下週的空檔"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-022$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "先提供口味表與客製草圖讓流程看似完整"}, {"tag": "authority", "text": "挪用客製品退貨例外來拒絕提供訂單"}, {"tag": "time_pressure", "text": "聲稱僅剩一個製作空檔要求今晚付款"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我收到影音服務的續費通知，信裡寫著試用期今天結束，午夜後會扣一整年的費用。郵件上的商標和我用的服務很像，按鈕寫著取消訂閱。我點進去，頁面先要我輸入卡片資料確認本人，接著說驗證失敗，要我打給線上專員。專員說扣款已經送出，要攔下來得先去買等額的遊戲點數當取消憑證，之後會連同年費一起退回。他傳來附近超商的位置，叫我不要掛電話。$rw$
  WHERE case_key = $rw$shopping-scam-023$rw$ AND narrative = $rw$我收到影音服務的續費通知，信裡寫著試用期今天結束，午夜後會扣一整年費用。郵件上的商標和我用過的服務很像，按鈕也寫著取消訂閱。我點進去後，頁面先要求輸入卡片資料確認本人，接著跳出驗證失敗，要我聯繫線上專員。專員說系統已送出扣款，若要攔下必須購買等額的數位點數做取消憑證，完成後會連同年費退回。他傳來附近商店的位置，要求保持通話並逐張念出點數序號。我打開原本的服務應用程式，帳戶頁卻沒有看到相同方案，電話那頭還在等我出門。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "郵件和頁面用了很像影音服務的商標"}, {"tag": "time_pressure", "text": "說午夜就會扣一整年的費用"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-023$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "仿照影音服務商標製作取消訂閱頁面"}, {"tag": "time_pressure", "text": "聲稱午夜將扣全年費用要求立刻處理"}, {"tag": "greed", "text": "承諾取消後退回年費與等額點數款"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$shopping-scam-023$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$朋友轉來一則海邊旅宿團購貼文，照片看起來像新開幕，兩晚價格約是訂房平台的一半。留言區有多個帳號揪團，也有人貼出訂房憑證說已搶到連假房型。我私訊後，小編說團購不走訂房平台，要直接匯款給合作窗口，才能保留折扣。他傳來一張住宿券，券面寫著旅宿名稱、入住兩晚和早餐，但旅宿名稱在搜尋結果中只有相似名稱，電話也與貼文不同。小編說連假房剩最後一間，先匯全額就能改日期一次，逾十分鐘會把房間交給候補。我看著朋友傳來的貼文和收款戶名，還沒按下確認。$rw$
  WHERE case_key = $rw$shopping-scam-024$rw$ AND narrative = $rw$朋友轉來一則海邊旅宿團購貼文，照片看起來像新開幕，兩晚價格約是訂房平台的一半。留言區有多個帳號揪團，也有人貼出訂房憑證說已搶到連假房型。我私訊後，小編說團購不走訂房平台，要直接匯款給合作窗口，才能保留折扣。他傳來一張格式完整的住宿券，但旅宿名稱在搜尋結果中只有相似名稱，電話也與貼文不同。小編說連假房剩最後一間，先匯全額就能改日期一次，逾十分鐘會把房間交給候補。我看著朋友傳來的貼文和收款戶名，還沒按下確認。$rw$;
UPDATE public.game_cases SET narrative = $rw$在交友軟體認識兩個月的對象，最近說挑了一只紀念手錶寄給我。今天一個自稱物流承辦人的人傳來包裹照片，收件標籤上有我的姓，說內容物估價比較高，要先付約四萬元的查驗和保管費才能配送。對象說他在外地開會沒辦法處理，請我先墊，晚上就還我。承辦人說倉庫下班前沒收到錢就退件，傳來一個私人帳戶。我盯著包裹照片上模糊的標籤。$rw$
  WHERE case_key = $rw$romance-scam-021$rw$ AND narrative = $rw$在交友軟體認識兩個月的對象每天和我分享工作與晚餐照片，最近說挑了一只紀念手錶寄給我。今天一名自稱物流承辦人的人傳來包裹照片，收件標籤確實寫著我的姓氏，但表示內容物估價較高，要先付約四萬元的查驗與保管費才能配送。交往對象說他正在外地開會，無法處理境內款項，還傳來同事領到類似包裹的照片，要我先墊付，晚上再還。他說倉庫下班前沒收到款項就會退件，之後訊息一封接一封。我問能否由物流到付，承辦人只回傳一個私人收款帳戶。我盯著包裹照片上的模糊標籤。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "自稱物流承辦人，要先收查驗保管費"}, {"tag": "time_pressure", "text": "說倉庫下班前沒收到錢就退件"}]$rw$::jsonb
  WHERE case_key = $rw$romance-scam-021$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "每天分享生活兩個月後才提出代墊請求"}, {"tag": "authority", "text": "物流承辦人以查驗和保管名目要求付款"}, {"tag": "social_proof", "text": "傳來同事領取相似包裹的照片作證"}, {"tag": "time_pressure", "text": "聲稱倉庫下班前未付款就會退件"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我和網路上認識的對象聊了三個月。最近他說想先讓兩人的旅行基金變多一點，介紹我用一個境外投資平台。我先放了約兩萬元，畫面上的數字每天都在漲。今天他說行情難得，他願意幫我出一半，但我得在晚上前再湊約十萬元。他傳來平台客服的收款帳戶，戶名每次都不一樣。我問為什麼戶名一直換，他說平台有好幾個收款窗口。我看著他整理好的入金步驟。$rw$
  WHERE case_key = $rw$romance-scam-022$rw$ AND narrative = $rw$我和網路上認識的對象聊了三個月，他常談未來一起生活，也會記得我的作息。最近他說想先替兩人的旅行基金增值，介紹我使用一個境外投資平台。他帶我存入約兩萬元，畫面每天顯示數字增加，還主動轉回一小筆讓我試提。今天他說行情出現難得機會，願意替我補一半資金，但我必須在晚上前湊出另外約十萬元。他傳來平台客服的收款帳戶，戶名每次都不同。我說想先找持牌業者詢問，他回覆兩個人的規劃不該讓外人干涉，還問我是不是不把未來當一回事。我看著他整理好的入金步驟。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "說行情難得，他願意幫我出一半"}, {"tag": "time_pressure", "text": "要我在晚上前再湊約十萬元"}]$rw$::jsonb
  WHERE case_key = $rw$romance-scam-022$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "長期記錄作息並用共同未來包裝資金要求"}, {"tag": "greed", "text": "用每日上升的數字和代墊一半引誘加碼"}, {"tag": "time_pressure", "text": "要求當晚湊足款項才能搭上行情"}, {"tag": "authority", "text": "平台客服每次提供不同姓名的收款帳戶"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$網路上交往一個多月的對象突然說，家人在外地住院，要先繳約六萬元的手術押金。他傳來一張繳費通知的照片，醫院名字和病人姓名都被裁掉了。他說自己的帳戶暫時不能轉帳，請我先把錢匯給一位醫院的財務人員，下週領薪水就還我。我說想直接打給醫院，他說探視時間快結束了，財務只能幫他保留到今天的手術排程。他傳來一個私人戶名。$rw$
  WHERE case_key = $rw$romance-scam-024$rw$ AND narrative = $rw$網路上交往一個多月的對象突然說家人在外地住院，需要先繳約六萬元手術押金。他傳來病房照片和一張繳費通知，姓名與院所標誌都被裁掉，理由是家人不想讓病情曝光。他說自己的帳戶因跨境工作暫時無法轉帳，希望我先把錢匯給一名自稱醫院財務的人，下週薪資入帳就歸還。我提出直接打給院所或到櫃檯繳費，他說探視時間快結束，財務人員願意特別替他保留手術排程，不能再改付款方式。通話中他反覆說只有我能幫忙，並傳來一個私人戶名。我正在看那張缺少抬頭的通知。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "收款人自稱醫院財務，要我把押金匯給他"}, {"tag": "time_pressure", "text": "說財務只能把手術排程保留到今天"}]$rw$::jsonb
  WHERE case_key = $rw$romance-scam-024$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "交往後以只有你能幫忙綁住付款決定"}, {"tag": "authority", "text": "裁去院所抬頭的繳費通知搭配私人戶名"}, {"tag": "time_pressure", "text": "以手術排程和探視結束要求立即匯款"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$晚上接到一通電話，對方說是購物平台的客服，說我上個月的網購訂單被重複設定成十二期，下個結帳日會再扣一次。他報出商品和大概的金額，接著把電話轉給一位自稱銀行帳務人員的人。那人說我的金融卡沒有開啟接收退款的功能，要我到提款機插卡，輸入一組交易代碼。我說明天去分行辦，他說批次作業今晚就截止，電話不能掛。我已經站在提款機前面。$rw$
  WHERE case_key = $rw$atm-scam-021$rw$ AND narrative = $rw$晚上接到一通來電，對方說我上月的網購訂單被重複設定成十二期，下個結帳日會再次扣款。他報出商品種類和約略金額，接著把電話轉給自稱銀行帳務人員的人。那人說退款程序已啟動，但我的金融卡沒有開啟接收功能，要我到提款機插卡後輸入一組交易代碼。他解釋畫面雖會顯示轉帳，實際只是測試回沖，完成後兩筆款項都會回到帳戶。我提議明天到分行處理，他說批次作業今晚截止，電話不能掛斷。我已站在提款機前，他正在逐步念出帳號和金額。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "購物客服和銀行帳務人員接力打來"}, {"tag": "time_pressure", "text": "說批次作業今晚截止，不能等明天"}]$rw$::jsonb
  WHERE case_key = $rw$atm-scam-021$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "來電者接力扮演購物客服與銀行帳務人員"}, {"tag": "time_pressure", "text": "以批次作業今晚截止阻止隔日臨櫃"}, {"tag": "trust_building", "text": "先報出商品與金額再逐步引導提款機操作"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$手機響起，對方自稱銀行風控人員，說我的信用卡剛出現一筆境外交易，不是本人刷的話要馬上攔截。他說得出我的姓名和卡號末四碼。他說要先做一筆一樣金額的反向驗證，系統才分得出要撤銷哪一筆，要我打開網路銀行，新增他給的受款人，再把收到的驗證碼念給他。我說想改打卡片背面的電話，他說掛斷後案件要重新排隊，錢可能先被領走。我停在輸入驗證碼的畫面。$rw$
  WHERE case_key = $rw$atm-scam-022$rw$ AND narrative = $rw$手機響起時，對方自稱銀行風控人員，說我的信用卡剛出現一筆境外交易，若不是本人消費就要立刻攔截。他能說出我的姓名和卡片末四碼，並傳來一則格式像銀行通知的簡訊。接著他說卡片可能已被綁到別人的行動支付，要先做一筆相同金額的反向驗證，才能讓系統辨認哪筆要撤銷。他要我開啟網路銀行，新增他提供的受款人，並把收到的一次性密碼念給他。我說想改撥卡片背面的電話，他回覆掛斷後案件會重新排隊，款項可能先請領。我停在密碼輸入畫面，通話仍在進行。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "自稱銀行風控人員，說反向驗證才能撤銷交易"}, {"tag": "time_pressure", "text": "說掛斷就要重新排隊，錢可能先被領走"}]$rw$::jsonb
  WHERE case_key = $rw$atm-scam-022$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "自稱銀行風控並掌握姓名與卡片末四碼"}, {"tag": "time_pressure", "text": "聲稱掛斷後款項可能先被請領"}, {"tag": "authority", "text": "要求新增受款人並口述一次性密碼"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我到分行臨櫃要匯一筆比較大的款項。這是自稱購物平台客服的人叫我匯的，他說我的退款金額比較大，要到臨櫃解除錯誤設定，還報得出我的訂單內容。他教我，行員問起就說錢是借給親戚的，不要提退款，也不要提這通電話。行員問我收款人是誰、有沒有人在電話裡指導，電話那頭的專員馬上傳訊息提醒我照先前說的回答，說中午批次前一定要辦好。我正在想該怎麼回答。$rw$
  WHERE case_key = $rw$atm-scam-023$rw$ AND narrative = $rw$自稱購物平台客服的人說我的退款金額較大，必須到銀行臨櫃解除錯誤設定。他報出訂單內容，還傳來一張退款申請表。電話中的專員教我向行員表示款項是借給親戚，不要提到退款或這通電話，否則銀行會把申請退回，平台還可能繼續扣款。他說會保持通話，等我拿到匯款收據後再替我完成原路退回。我到分行抽了號碼牌，行員先詢問受款人關係、資金用途以及是否有人在線上指示。電話那頭傳訊息提醒我照先前說法回答，並表示午間批次前一定要辦好。我正在想該怎麼回答櫃檯。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "自稱平台專員，說退款要走銀行系統"}, {"tag": "time_pressure", "text": "說中午批次前一定要辦好"}]$rw$::jsonb
  WHERE case_key = $rw$atm-scam-023$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "以退款申請表和訂單資料包裝來電身分"}, {"tag": "trust_building", "text": "承諾全程在線陪同直到款項原路退回"}, {"tag": "time_pressure", "text": "要求午間批次前完成臨櫃匯款"}, {"tag": "authority", "text": "教導對行員隱瞞來電與真實匯款用途"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在通訊軟體收到自稱銀行客服的訊息，說我前一筆轉帳因為收款戶名不符被暫停，要重新驗證。他要我登入行動銀行，改輸入他給的帳號和約三萬元的驗證金額，說送出後會自動取消。我發現畫面上的收款戶名跟商家差了一個字，問他能不能去分行確認，他說這是跨行清算的暫存戶，十分鐘內沒完成，我的帳戶會被列為異常。我停在最後確認鍵前面。$rw$
  WHERE case_key = $rw$atm-scam-024$rw$ AND narrative = $rw$我在通訊軟體收到自稱銀行客服的訊息，說前一筆轉帳因受款戶名不符被暫停，需要重新驗證。對方傳來的畫面顯示部分隱碼戶名，看起來和我原本要付款的商家相近。他說新版轉帳系統會用一筆小額測試確認戶名，要我登入行動銀行，改輸入他提供的帳號與約三萬元的驗證金額，送出後會自動取消。我注意到螢幕實際顯示的隱碼戶名和商家仍差一個字，便詢問能否到分行確認。他回覆這是跨行清算中的暫存戶，若十分鐘內未完成，原帳戶會被列入異常。我停在最終確認鍵前。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "自稱銀行客服，說這是跨行清算暫存戶"}, {"tag": "time_pressure", "text": "說十分鐘內沒完成，帳戶會被列為異常"}]$rw$::jsonb
  WHERE case_key = $rw$atm-scam-024$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "自稱銀行客服解釋跨行清算暫存戶"}, {"tag": "time_pressure", "text": "聲稱十分鐘內未完成帳戶會列入異常"}, {"tag": "greed", "text": "宣稱約三萬元測試款送出後會自動取消"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我從社群貼文加入一個新股申購群組，帶領者每天整理產業消息，群裡也常有人貼中籤通知，看起來很多人在抽。今天有人提醒一檔熱門新股，申購到下午兩點截止。我打開自己券商的程式，從首頁進到申購頁，上面有承銷價和抽籤日，扣款帳戶只列我原本的交割戶。說明寫著沒抽中的話，預扣的錢會退回這個帳戶。我對了一下交割戶的餘額，還沒按送出。$rw$
  WHERE case_key = $rw$investment-legit-021$rw$ AND narrative = $rw$我在自己往來證券商的應用程式看到新股申購通知，熱門程度比預期高，討論區也有人貼出抽籤結果。系統顯示申購截止到下午兩點，逾時就不能參加，看起來同樣需要在期限內準備資金。我從應用程式首頁重新進入申購功能，查到公開說明書、承銷價格與抽籤日期，款項只會由原本綁定的本人交割帳戶預扣。證券商客服提醒，抽中後依公告時程扣款，未抽中則退回預扣款，不會另外提供個人帳戶。我核對交割戶餘額與風險揭露，正在決定要不要送出申請。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "從自己券商程式的首頁進到申購頁"}, {"tag": null, "text": "申購頁列出承銷價和抽籤日"}, {"tag": null, "text": "扣款帳戶只有我原本的交割戶"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-021$rw$ AND red_flags = $rw$[{"tag": null, "text": "從原往來證券商應用程式首頁進入申購"}, {"tag": null, "text": "公開說明書與承銷抽籤日期均可查閱"}, {"tag": null, "text": "申購款僅由本人既有交割帳戶預扣"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$朋友轉給我一場介紹自動投資程式的直播，畫面中的分析師展示系統怎麼依行情買賣，留言也一直有人在討論。我想起往來銀行的程式也有自動投資服務，就打開來看。它先要我做風險問卷，再列出三種組合，每一種都寫了管理費和可能的跌幅。這個月底前不收設定費，錢從我在這家銀行的帳戶扣。我還在比較三種組合，直播那頁也還開著。$rw$
  WHERE case_key = $rw$investment-legit-023$rw$ AND narrative = $rw$我在往來銀行的應用程式裡看到自動投資服務，首頁顯示過去績效曲線，旁邊也有不少使用者討論再平衡功能。系統先要求我完成身分查核與風險問卷，接著依承受度列出三種投資組合，每一種都標示管理費、可能最大波動與績效不代表未來結果。服務有本月底前免收設定費的活動，但我可以不參加，也能隨時回到頁面調整或停止扣款。資金只會從我在這家銀行已綁定的帳戶扣入以機構名義開立的專戶，沒有業務員私下收款。我正在比較三種配置。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "自動投資服務在我原本往來銀行的程式裡"}, {"tag": null, "text": "每種組合都寫了管理費和可能的跌幅"}, {"tag": null, "text": "扣款只從我在這家銀行的帳戶"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-023$rw$ AND red_flags = $rw$[{"tag": null, "text": "服務位於既有往來銀行的應用程式內"}, {"tag": null, "text": "各組合揭露費用波動及績效不保證"}, {"tag": null, "text": "資金只從本人綁定帳戶扣入機構專戶"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在拍賣平台看到一雙剛上市的球鞋，價格比轉售行情低一些，賣家的成交評價很多，大多是五顆星。賣家說是抽籤重複中的，商品頁有鞋盒、鞋標和鞋底的實拍。下單走平台的購物車，錢先留在平台，我收到鞋、按下完成訂單後才會撥給賣家；有問題可以在訂單頁申請退貨。價格還是讓我有點猶豫，我正在把鞋標的照片放大來看，還沒下單。$rw$
  WHERE case_key = $rw$fake-sale-legit-024$rw$ AND narrative = $rw$我在拍賣平台看到一雙剛上市的球鞋，價格比部分轉售店低，頁面也累積不少詢問與成交評價。賣家說商品來自抽籤重複中籤，可以透過平台的鑑定服務出貨。我下單後，款項先留在平台，賣家必須把鞋寄到合作鑑定中心，通過外觀與標示檢查才會轉寄給我；若未通過，系統會取消訂單並把款項退回原支付工具。訂單頁列出服務費、檢查範圍及申訴方式，也能看到每個物流節點。價格仍讓我猶豫，我正在閱讀鑑定服務不涵蓋的項目。$rw$;
UPDATE public.game_cases SET provenance = $rw$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」與拍賣平台款項保留、退貨機制$rw$
  WHERE case_key = $rw$fake-sale-legit-024$rw$ AND provenance = $rw$依據：團隊整理的正規流程說明「正規電商交易與退換貨流程」與拍賣平台鑑定、原支付工具退款機制$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "付款走平台購物車，錢先留在平台"}, {"tag": null, "text": "收到後有問題可以在訂單頁申請退貨"}]$rw$::jsonb
  WHERE case_key = $rw$fake-sale-legit-024$rw$ AND red_flags = $rw$[{"tag": null, "text": "款項由平台保管而非匯入賣家帳戶"}, {"tag": null, "text": "商品先送合作中心檢查再轉寄買家"}, {"tag": null, "text": "未通過檢查即取消並退回原支付工具"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我從社群廣告點進一個賣廚房家電的頁面，價格大概是市面的一半。點進去直接跳到我常用的購物平台，帳號也還是登入的狀態。活動頁寫著週年慶折扣到今晚，商品下面有很多評價和買家的開箱照。賣家頁看得到公司名稱和退貨規則。結帳走平台的購物車，付款是我原本綁的信用卡，金額跟商品頁一樣。我正在看保固寫幾年，還沒按下結帳。$rw$
  WHERE case_key = $rw$shopping-legit-021$rw$ AND narrative = $rw$我在大型購物平台看到廚房家電的週年慶活動，價格接近市面的一半，商品頁也有大量評價與開箱照片。折扣只到今晚，庫存數字會隨訂單變動，看起來很容易讓人衝動。我從平台首頁重新搜尋同一商品，活動頁列出起訖時間、參與賣場與折價方式，賣家頁可查到公司資訊及退貨規則。結帳仍使用平台購物車和原本綁定的信用卡，金額與商品頁一致，沒有客服私訊改變付款方式。頁面載明收貨後七日內可依規定申請解除契約。我正在比較其他賣場的保固。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "廣告直接連到我常用的購物平台"}, {"tag": null, "text": "賣家頁有公司名稱和退貨規則"}, {"tag": null, "text": "結帳走平台購物車和原本綁的信用卡"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-021$rw$ AND red_flags = $rw$[{"tag": null, "text": "活動起訖與參與賣場可從平台首頁核對"}, {"tag": null, "text": "結帳維持平台購物車及原綁定信用卡"}, {"tag": null, "text": "商品頁載明七日解除契約與退貨流程"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我收到影音服務的續費通知，信裡寫著試用期今晚結束，之後會按年扣款。期限很近，我有點緊張。我打開手機上原本就裝的程式，訂閱頁寫的方案、價格和扣款日期都跟信上一樣，旁邊有取消訂閱的按鈕，扣款前取消就不會收費。信裡只說可以到帳戶頁管理方案，沒有要我回覆什麼資料。我正在想這個服務還要不要留著，還是現在就取消。$rw$
  WHERE case_key = $rw$shopping-legit-023$rw$ AND narrative = $rw$我收到影音服務的續費通知，內容寫著試用期今晚結束，之後會按年扣款。期限很近，但郵件沒有要求回信提供卡片資料，只提醒我可從帳戶頁管理方案。我沒有點郵件按鈕，直接打開原本安裝的應用程式，在訂閱頁看到相同的方案名稱、價格、扣款日期及取消規則。頁面讓我在扣款前自行取消，取消後立即顯示不再續費，也寄出一封確認信；若已產生爭議款，則要從應用程式的客服工單申請，退款只回原支付工具。我正在決定要保留服務還是按下取消。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "訂閱頁的方案、價格和扣款日跟信上一樣"}, {"tag": null, "text": "扣款前在訂閱頁就能自己取消"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-023$rw$ AND red_flags = $rw$[{"tag": null, "text": "從原有應用程式帳戶頁核對方案與日期"}, {"tag": null, "text": "扣款前可自行取消並即時取得確認紀錄"}, {"tag": null, "text": "爭議申請走站內工單且退回原支付工具"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 2
  WHERE case_key = $rw$shopping-legit-023$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$朋友轉來一則海邊旅宿團購貼文，照片看起來像新開幕，兩晚價格約是訂房平台的一半。留言區有很多人在揪團。我查了這間民宿的登記資料，找到它的官網，官網上真的有這個團購專案，寫著限平日入住、連假要加價，也寫了取消規定。訂房在官網的系統完成，付款後會收到訂房編號。我正在比較可以免費取消和不能退款的兩種房價，還沒送出。$rw$
  WHERE case_key = $rw$shopping-legit-024$rw$ AND narrative = $rw$朋友轉來海邊旅宿的淡季團購，貼文下有不少人詢問，兩晚價格也比連假低許多。我沒有從貼文私訊付款，而是自行搜尋旅宿登記名稱，再從旅宿網站首頁進入住房專案。頁面顯示團購適用的平日區間、連假加價、可預訂房型及取消期限，線上查詢也看得到空房。結帳由網站的訂房系統處理，付款後會產生訂房編號並寄送確認內容，取消時依頁面條件退回原支付工具。客服表示可先保留購物車十分鐘，逾時只是重新查房。我正在比較可免費取消與不可退款的兩種房價。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "民宿登記資料查得到，官網有同一個專案"}, {"tag": null, "text": "專案頁寫明限平日、連假加價和取消規定"}, {"tag": null, "text": "在官網訂房系統付款，會收到訂房編號"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-024$rw$ AND red_flags = $rw$[{"tag": null, "text": "旅宿登記名稱可由獨立查詢管道核對"}, {"tag": null, "text": "專案頁列明適用日期加價與取消期限"}, {"tag": null, "text": "訂房系統產生編號並依條件原路退款"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$在交友軟體認識兩個月的對象，最近說挑了一只紀念手錶寄給我。他說是請店家直接寄，把店家的出貨通知轉給我，上面有店名和宅配單號。今天宅配司機打電話來，說有一件運費到付的包裹，要付約一百五十元。我用單號在宅配公司的網站查，寄件人是那家手錶店，運費也和網站上寫的一樣。我跟司機說晚上在家，正在等他把包裹送來。$rw$
  WHERE case_key = $rw$romance-legit-021$rw$ AND narrative = $rw$交往兩個月的對象說準備了一只紀念手錶，還拍了包裝照片給我。隔天我們照原本約定在公共場所見面，他本人把紙袋交給我，盒內附有店家開立的購買憑證。他提到挑選時跑了好幾家店，價格比預算高一些，但沒有要我分攤，也沒有要求我提供地址、帳戶或代收其他包裹。我問是否需要回禮，他說可以先把尺寸確認好，不合再由他拿憑證回店處理。我拿著尚未拆封的盒子，還在想這份禮物是否太貴重。$rw$;
UPDATE public.game_cases SET provenance = $rw$依據：團隊整理的正規流程說明「正常網路交友互動特徵」與宅配運費到付流程$rw$
  WHERE case_key = $rw$romance-legit-021$rw$ AND provenance = $rw$依據：團隊整理的正規流程說明「正常網路交友互動特徵」$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "出貨通知上有店名和宅配單號"}, {"tag": null, "text": "宅配網站查得到寄件人和一樣的運費"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-021$rw$ AND red_flags = $rw$[{"tag": null, "text": "雙方依約在公共場所見面並當面交付"}, {"tag": null, "text": "禮物附店家憑證且退換由贈送者處理"}, {"tag": null, "text": "未要求提供帳戶地址或代墊任何費用"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$交友軟體上的對象約我週末吃飯，我們已經視訊過幾次。他傳來餐廳的名稱和菜單，說想訂包廂，包廂每人要先付約一千元訂金，太晚取消可能不退。我上網找到這家餐廳的網站，訂位頁只寫了一般座位的規則，包廂的訂金怎麼付、怎麼退都沒寫。網站最下面有餐廳自己的電話和地址。我還沒付任何一筆訂金，正在想要怎麼確認包廂的規定。$rw$
  WHERE case_key = $rw$romance-legit-023$rw$ AND narrative = $rw$交友軟體上的對象約我週末吃飯，我們已經視訊過幾次，他傳來餐廳名稱和菜單。熱門時段需要每人約一千元訂金，逾期取消可能不退，這讓我先停下來核對。我沒有加任何店長帳號，而是自行搜尋餐廳登記電話並致電，店員確認訂位規則後，請我從餐廳網站選擇日期。訂金由訂位系統收取，頁面列出抵用方式、取消期限與退款條件，完成後寄來訂位編號。同行者各自支付自己的份額，也沒有索取我的卡片資料。我停在付款頁，正在確認取消日期。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "餐廳的網站和電話是我自己查到的"}, {"tag": null, "text": "訂金是付給餐廳，對象沒要我把錢給他"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-023$rw$ AND red_flags = $rw$[{"tag": null, "text": "自行查找餐廳登記電話核對訂位規則"}, {"tag": null, "text": "訂位頁載明訂金抵用取消與退款條件"}, {"tag": null, "text": "同行者各付自己份額且不索取卡片資料"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$網路上交往一個多月的對象突然說，家人在外地住院，要先繳約六萬元的手術押金。他問我能不能陪他去醫院一趟。到了住院櫃檯，批價人員當面給了繳款單，上面有醫院名稱、病人姓名和費用項目。他先用自己的卡繳了一部分，窗口開了收據，收據上是病人的名字。剩下的他問我能不能先借他，下週領薪水就還，錢一樣在窗口繳。我看著那張收據，還沒決定要不要借。$rw$
  WHERE case_key = $rw$romance-legit-024$rw$ AND narrative = $rw$交往一段時間的對象告訴我家人要住院，問我能不能陪他去辦理手續。他沒有要求我轉帳，我們直接到院所的住院櫃檯，費用說明與繳款單都由櫃檯人員當面提供，抬頭和病人資料完整。對方使用自己的卡片在院內收費窗口繳費，收據也開在病人名下。我只被請託在他辦文件時幫忙看行李，沒有交出帳戶、卡片或密碼。因為金額不小，他仍在和櫃檯確認哪些項目可由保險申請。我坐在等候區，看著他整理文件。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "批價櫃檯當面給繳款單，有醫院和病人姓名"}, {"tag": null, "text": "錢直接在醫院窗口繳，收據開在病人名下"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-024$rw$ AND red_flags = $rw$[{"tag": null, "text": "費用由院所櫃檯當面說明並出具繳款單"}, {"tag": null, "text": "對方使用自己的卡片向院內窗口付款"}, {"tag": null, "text": "收據載明病人資料且未索取你的金融資料"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$晚上接到一通電話，對方說是購物平台的客服，說我上個月有一筆訂單可能被重複扣款，請我跟發卡銀行確認。他沒有問我任何資料。我掛掉後打了卡片背面的電話，銀行客服查到兩筆一樣金額的授權，其中一筆還沒請款，說如果之後兩筆都請款，可以申請退回原卡。信用卡的結帳日就在明天，我有點急。我拿著筆，正在記下銀行給的案件編號。$rw$
  WHERE case_key = $rw$atm-legit-021$rw$ AND narrative = $rw$我在購物應用程式看到一筆訂單疑似重複扣款，站內客服回覆說其中一筆是尚未完成請款的授權紀錄，若最後確實重複，會退回原信用卡。客服請我提供訂單編號與卡片末四碼，並在站內工單列出預計查核時間。因為信用卡結帳日在明天，處理確實有時效，但客服表示我可以先撥卡片背面的電話向發卡機構確認，整個過程不需要到提款機，也不會要求輸入轉帳資料。銀行客服查到相同授權紀錄，替我建立爭議案件編號。我正在核對兩邊工單的金額。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "自己打卡片背面的電話，銀行查到兩筆授權"}, {"tag": null, "text": "客服沒問任何資料，只請我跟銀行確認"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-021$rw$ AND red_flags = $rw$[{"tag": null, "text": "客服只在站內工單查核訂單與卡片末四碼"}, {"tag": null, "text": "退款回原信用卡且不要求提款機操作"}, {"tag": null, "text": "可自行撥卡背電話建立爭議案件編號"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$手機響起，對方自稱銀行風控人員，說我的信用卡剛出現一筆境外交易，不是本人刷的話要馬上攔截。他要我自己打開銀行的程式確認，不要把任何密碼告訴他。我打開程式，首頁真的有一筆一樣幣別和金額的交易。我選了不是本人，畫面說卡片會先暫停，處理進度會在程式的訊息裡通知，也可以打卡片背面的電話。卡片要暫停讓我有點擔心，電話那頭還在等。我的手指停在確認鍵上。$rw$
  WHERE case_key = $rw$atm-legit-022$rw$ AND narrative = $rw$我收到發卡銀行的交易確認通知，內容顯示一筆境外刷卡，要我在應用程式裡選擇是否為本人交易。通知來得突然，我沒有點簡訊連結，直接打開原本的銀行應用程式，首頁確實出現相同幣別與金額。選擇非本人後，系統暫停卡片並提供銀行公告的客服按鈕。客服核對基本資料後建立爭議案件，說調查結果會留在站內訊息，不需要提供一次性密碼，也不必新增受款人或先做任何轉帳。我仍可掛斷後改撥卡片背面的電話。我正在確認停卡後的補發地址。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "銀行程式裡有同一筆境外交易"}, {"tag": null, "text": "要我自己在程式裡確認，不要報密碼"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-022$rw$ AND red_flags = $rw$[{"tag": null, "text": "從原有銀行應用程式核對幣別與金額"}, {"tag": null, "text": "爭議案件留在站內且不索取一次性密碼"}, {"tag": null, "text": "可掛斷後自行改撥卡片背面銀行電話"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我到分行臨櫃要匯一筆比較大的款項。這是要付給裝修師傅的工程款，契約、請款單和發票都在我包包裡。行員看到金額，問我收款人是誰、錢做什麼用、有沒有人在電話裡指導，問得很仔細，旁邊還有人在排隊，我有點不耐煩。我把契約拿出來，行員對了一下收款戶名，建議我先打契約上的電話跟師傅確認一次。我拿起手機，正在撥契約上的號碼。$rw$
  WHERE case_key = $rw$atm-legit-023$rw$ AND narrative = $rw$我要在銀行臨櫃匯一筆較大的裝修款，行員看到金額後詢問受款人關係、資金用途，以及是否有人透過電話指示。問題連續而具體，讓我一度覺得被盤問。我拿出和承包商簽的書面契約、分期請款單與發票，行員依資料核對受款戶名，並提醒我再次向契約上的聯絡方式確認。沒有人要求我對櫃檯隱瞞用途，承包商也同意等我查核。行員說若仍有疑慮可以先不匯，文件會退還給我，不收取額外解鎖費。我正在電話中和承包商逐項核對請款內容。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "收款戶名和裝修契約上的一樣"}, {"tag": null, "text": "行員建議打契約上的電話跟師傅確認"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-023$rw$ AND red_flags = $rw$[{"tag": null, "text": "行員依臨櫃關懷流程詢問關係與用途"}, {"tag": null, "text": "書面契約請款單與受款戶名可相互核對"}, {"tag": null, "text": "客戶可暫停交易且不需支付額外費用"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我在通訊軟體收到銀行官方帳號的通知，說我前一筆轉帳因為收款戶名不符，已經退回原帳戶。這個帳號是我開戶時自己加的，以前的轉帳通知也都從這裡來。我打開行動銀行，那筆課程費用真的顯示戶名不符、已退回，錢回到我的帳戶。通知只提醒我核對收款戶名後重新轉帳。我拿出課程的繳費通知，正在一個字一個字對戶名的最後一個字。$rw$
  WHERE case_key = $rw$atm-legit-024$rw$ AND narrative = $rw$我要用行動銀行支付課程費用，輸入完整帳號後，系統顯示部分隱碼的受款戶名，與報名頁列出的公司名稱縮寫相符。因金額約三萬元，應用程式要求我再次確認戶名與用途，並用自己裝置上的生物辨識授權。畫面有一分鐘的操作倒數，逾時只會回到上一頁，不會凍結帳戶或產生罰款。我沒有從陌生訊息取得帳號，而是由課程業者的書面繳費通知輸入，也能先暫停並撥打業者登記電話核對。系統不會要求我把一次性密碼告訴他人。我停在確認頁，正在比對戶名最後一個字。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "通知帳號是我開戶時自己加的"}, {"tag": null, "text": "行動銀行顯示同一筆已退回原帳戶"}, {"tag": null, "text": "只提醒我核對戶名後自己重新轉帳"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-024$rw$ AND red_flags = $rw$[{"tag": null, "text": "轉帳系統自動顯示部分隱碼受款戶名"}, {"tag": null, "text": "逾越操作時間只返回上頁不凍結帳戶"}, {"tag": null, "text": "帳號來自書面通知且可另撥登記電話核對"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀社群上的投資貼文：「盤前公開三檔翻倍黑馬，每天整理產業龍頭，完整名單免費索取。」貼文附上一名財經講師的照片和名字，留言區接連有人說已領到標的，也有人貼出上週上漲的畫面。按鈕把我帶到私人通訊帳號，助理說免費名單只給今天加入的人，先轉約三萬元到她提供的個人帳戶，就能升級成由老師即時帶進出的學員；若其中一檔沒有翻倍，款項可以退回。她又傳來十多張學員道謝截圖，問我要不要現在保留席位。$rw$
  WHERE case_key = $rw$investment-scam-031$rw$ AND narrative = $rw$我正在讀社群上的投資貼文：「盤前公開三檔翻倍黑馬，每天整理產業龍頭，完整名單免費索取。」貼文附上一名財經講師的照片，留言區接連有人說已領到標的，也有人貼出上週上漲的畫面。按鈕把我帶到私人通訊帳號，助理說免費名單只給今天加入的人，先轉約三萬元到她提供的個人帳戶，就能升級成由老師即時帶進出的學員；若其中一檔沒有翻倍，款項可以退回。她又傳來十多張學員道謝截圖，問我要不要現在保留席位。$rw$;
UPDATE public.game_cases SET narrative = $rw$我正在讀帶領者傳來的訊息：「交易所已註冊完成，審核約三到五個工作日，通過後第一時間通知你。」前幾天我照他的說明，在一家交易所開了帳戶，這家我查過，在金管會公布的名單上。今天他說交易所已經核准給我約二十萬元的額度，可以跟我自己的錢一起操作，但啟用前要先匯一成到他給的個人帳戶。他說額度只保留到今晚，過了就要重新排隊。我看著他傳來的帳號。$rw$
  WHERE case_key = $rw$investment-scam-032$rw$ AND narrative = $rw$我正在讀帶領者傳來的訊息：「交易所已註冊完成，審核約三到五個工作日，通過後第一時間通知我，就能替你包裝申請資金。」他先前陪我逐頁設定帳號，群組裡也有成員貼出審核通過後拿到資金的畫面。今天他說系統已核准約二十萬元額度，但啟用前要先匯一成到指定個人帳戶，做完便能連同投入款一起操作。他傳來印有交易所圖樣的核准頁，並表示額度只保留到今晚；我若自己聯絡平台，流程會被退回重排。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "說先匯一成就能啟用約二十萬元額度"}, {"tag": "time_pressure", "text": "說額度只保留到今晚，過了要重排"}]$rw$::jsonb
  WHERE case_key = $rw$investment-scam-032$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "先逐頁陪同註冊再提出入金要求"}, {"tag": "social_proof", "text": "群組成員輪流展示核准與入帳畫面"}, {"tag": "authority", "text": "傳來印有交易所圖樣的核准頁"}, {"tag": "time_pressure", "text": "聲稱額度今晚到期且查詢會被重排"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$收藏群的帶領者介紹一批紀念金幣，說市場上很缺，放半年交給合作的拍賣行轉售，價格可以漲到五倍。他傳來金幣的照片，正面是一隻展翅的老鷹。我問能不能先看實物，他說金幣都由他統一保管，賣掉以後本金和差價會一起匯給我，不用我操心。他說這一輪今天收單，先匯約八萬元到助理的帳戶就能排進去。我正在看他傳來的配額表。$rw$
  WHERE case_key = $rw$investment-scam-033$rw$ AND narrative = $rw$收藏群的帶領者介紹一批經專業機構鑑定的紀念金幣，說市場空缺大，放半年後可交由合作拍賣行轉售，預估價格能漲到五倍。群裡幾名收藏者貼出過往成交單，還有人說已經預訂數十枚。顧問傳來鑑定證書照片，卻不讓我自行向證書上的機構核對，只說整批貨由他統一保管與轉售。我若今天先匯約八萬元到助理帳戶，便能跟上這一輪；等拍賣成交後，本金與差價會一併匯回。我正在看他整理的配額表。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "說放半年交給拍賣行轉售能漲到五倍"}, {"tag": "time_pressure", "text": "說這一輪今天收單，要先匯款才排得進去"}]$rw$::jsonb
  WHERE case_key = $rw$investment-scam-033$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "用無法自行核對的鑑定證書佐證"}, {"tag": "social_proof", "text": "群內接連張貼成交單與預訂數量"}, {"tag": "greed", "text": "預告半年後轉售價格可漲至五倍"}, {"tag": "trust_building", "text": "由同一顧問代為保管並承辦轉售"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我賣出嬰兒推車後，買家傳來一封訂單信，裡面列著商品、金額、付款人和收件人，說款項已經進入代管。信下面要我聯絡小助手處理撥款。小助手說我的收款功能還沒啟用，要先匯約一萬元做流水驗證，完成後貨款和驗證款會一起回到我的帳戶。買家一直說他已經被扣款，今天不處理就要向平台求償。我打開原本的平台後台，找不到這筆訂單。$rw$
  WHERE case_key = $rw$fake-sale-scam-034$rw$ AND narrative = $rw$我賣出嬰兒推車後，買家傳來一封格式完整的訂單信，裡面列著商品、金額、付款人和收件人，還說款項已進入代管。信件下方要我聯絡小助手處理撥款，寄件地址卻與買家在平台填的資料不同。小助手表示我的收款功能尚未啟用，要先匯約一萬元做流水驗證，完成後貨款與驗證款會一起回到帳戶。買家不停說自己已被扣款，若今天不處理就會向平台求償；他另傳數張其他賣家成功撥款的對話。我正在核對原平台後台，仍找不到訂單。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "買家傳來仿訂單格式的代管通知信"}, {"tag": "time_pressure", "text": "買家說今天不處理就要向平台求償"}]$rw$::jsonb
  WHERE case_key = $rw$fake-sale-scam-034$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "仿訂單信件列出付款人與收件資料"}, {"tag": "social_proof", "text": "傳送其他賣家成功撥款的對話畫面"}, {"tag": "time_pressure", "text": "以當日求償要求先做流水驗證"}, {"tag": "trust_building", "text": "買家與小助手接續說明相同流程"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀手機簡訊：「您的包裹因關稅未繳而暫扣，請支付約一百六十元。」最近我確實有一件海外商品在路上，簡訊的寄件名稱看起來也像郵局。我點開簡訊裡的連結，頁面寫著包裹只保留到今天，逾時就退回寄件地。付完小額關稅之後，下一頁要我輸入完整卡號、有效期限和簡訊驗證碼。我打開購物平台看，物流狀態還是只寫運送中。$rw$
  WHERE case_key = $rw$shopping-scam-031$rw$ AND narrative = $rw$我正在讀手機簡訊：「您的包裹因關稅未繳而暫扣，請支付約一百六十元。」最近我確實有一件海外商品在途，簡訊裡的寄件名稱也很像郵務業者。我點開已去除真實網址的頁面，畫面顯示包裹只保留到今天，並列出多則收件人剛完成繳費的通知。頁面先收取小額關稅，下一步卻要求輸入完整卡號、有效期限和簡訊驗證碼，客服視窗還說逾時包裹就會退運。我打開購物平台查看，物流狀態仍只寫運送中。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "簡訊的寄件名稱看起來像郵局"}, {"tag": "time_pressure", "text": "頁面說包裹只保留到今天，逾時退回"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-031$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "以近似郵務業者名稱發送扣件簡訊"}, {"tag": "social_proof", "text": "頁面輪播收件人剛完成繳費的通知"}, {"tag": "time_pressure", "text": "聲稱當日未付款包裹就會退運"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀一封嬰兒推車的訂單郵件，上面列著約一萬六千元、免運、收件人和到府配送，看起來像真的訂單，但我不記得自己買過。信上說有問題要馬上聯絡客服小助手。小助手說這筆已經在請款，要取消的話，半小時內要去買等額的遊戲點數，把序號給他，才能開出取消憑證。我打開原本的購物平台查，帳戶裡找不到這筆訂單，電話那頭還在催。$rw$
  WHERE case_key = $rw$shopping-scam-032$rw$ AND narrative = $rw$我正在讀一封嬰兒推車訂單郵件，內容列出約一萬六千元金額、免運、付款人、收貨人與到府配送，看起來像已成立的交易，但我不記得下過這筆訂單。郵件說若有疑問須立即聯絡小助手，頁面同時顯示數名會員剛取消成功。小助手自稱票務管理人員，表示訂單已進入請款，半小時內購買等額數位點數並交出序號，才能產生取消憑證；處理完兩筆金額都會退回。我從原購物平台的帳戶頁查詢，裡面沒有相同訂單。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "郵件照購物平台訂單的格式列出商品與配送"}, {"tag": "time_pressure", "text": "要我半小時內買點數交出序號"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-032$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "仿訂單格式列出完整商品與配送欄位"}, {"tag": "social_proof", "text": "頁面顯示數名會員剛完成取消程序"}, {"tag": "time_pressure", "text": "要求半小時內交出數位點數序號"}, {"tag": "greed", "text": "承諾退回訂單款與等額點數款"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀保健商品的體驗廣告，上面說吃七天就能讓血糖數值變好，什麼體質都適合，加通訊帳號就能拿配方。我好奇加了之後，客服說第一批體驗者今天可以用六折買三個月份，沒效全額退費。我問成分和食品業者登錄字號，他說配方保密，只給了一個個人帳戶要我匯款。我看著那組大約一萬元的方案，正在考慮要不要先買一組試試看。$rw$
  WHERE case_key = $rw$shopping-scam-033$rw$ AND narrative = $rw$我正在讀保健商品廣告：「七天調整數值，歷經多年驗證，所有族群都適用，加入通訊帳號取得配方。」貼文下有多名使用者留言說服用幾天就能少吃藥，也附上前後檢測數字。客服自稱健康顧問，說第一批體驗者今天可用市價六折購入三個月份，若沒有變化便全額退費。他不提供完整成分、食品業者登錄資料或書面退費條件，只要求匯到個人帳戶，再傳既有顧客的感謝訊息給我。我正在考慮是否購買約一萬元的組合。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "說吃七天就能讓血糖數值變好"}, {"tag": "time_pressure", "text": "說六折只限今天的第一批體驗者"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-scam-033$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "自稱健康顧問卻不提供成分與登錄資料"}, {"tag": "social_proof", "text": "留言者輪流貼出服用前後檢測數字"}, {"tag": "greed", "text": "宣稱短期見效並以六折組合招攬"}, {"tag": "trust_building", "text": "以既有顧客感謝訊息回應疑問"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀新認識的網友傳來的訊息。她說她有個住在海外的姐姐很懂收藏，品相好的金幣經過拍賣行轉手，價格能漲到五倍，她自己就是靠這個多一份收入。她說如果我想試，投入約五萬元，她可以請姐姐幫我留兩枚，不過今天就要把錢匯到代辦人的帳戶。我說想見面再談，她說這批貨等不到那時候，要我先決定。我看著她傳來的一長串付款步驟。$rw$
  WHERE case_key = $rw$romance-scam-032$rw$ AND narrative = $rw$我正在讀新認識的網友傳來的訊息。她先安慰我最近工作不順，又介紹一位住在海外、熟悉收藏市場的姐姐，接著說極美品金幣經拍賣行轉手後預計能漲五倍，自己正靠這種方式增加收入。她傳來兩人的合照、鑑定畫面和幾張成交單，並說共同聊天群裡已有朋友跟著買。若我願意投入約五萬元，她可以請姐姐替我保留兩枚，但今天要先把款項匯到代辦人的帳戶。我提出見面後再談，她回覆這批貨不會等到那時。我看著她一連串關心訊息與付款步驟。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "說金幣經拍賣行轉手能漲到五倍"}, {"tag": "time_pressure", "text": "說今天就要匯款，貨等不到見面"}]$rw$::jsonb
  WHERE case_key = $rw$romance-scam-032$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "先傾聽工作困擾再轉入金錢邀約"}, {"tag": "social_proof", "text": "共同群組成員展示購買與成交單"}, {"tag": "greed", "text": "宣稱收藏金幣轉手可漲到五倍"}, {"tag": "time_pressure", "text": "聲稱保留品項只能在當天付款"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$網路交往三個月的對象說她在海外開舞蹈教室，準備來台灣跟我一起生活，也說願意出一筆錢幫我開店。最近她說自己的跨境帳戶不能直接撥款，請我把提款卡寄給一位金融服務人員，再傳訊息告訴他密碼，先測試我的帳戶能不能收約三十萬元。服務人員說卡片今天寄出，才排得進這週的作業。我拿著還沒封口的寄件袋，提款卡就放在裡面。$rw$
  WHERE case_key = $rw$romance-scam-033$rw$ AND narrative = $rw$網路交往三個月的對象說她在海外經營舞蹈教室，準備來台與我生活，也願意提供創業資金。她每天問候，記得我店面計畫的細節，最近則說自己的跨境帳戶暫時不能直接撥款。她請我把提款卡寄給一名智能金融服務人員，再用訊息告知密碼，理由是先測試本地帳戶是否能接收約三十萬元。服務人員傳來監管標章與撥款流程，表示卡片今天寄出才能排進本週作業。對象說這是一起生活的第一步，也問我是否願意讓她分擔夢想。我拿著尚未封口的寄件袋。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "greed", "text": "說測試帳戶後就給我約三十萬元開店"}, {"tag": "time_pressure", "text": "說卡片今天寄出才排得進這週作業"}]$rw$::jsonb
  WHERE case_key = $rw$romance-scam-033$rw$ AND red_flags = $rw$[{"tag": "trust_building", "text": "記住創業細節並用共同生活包裝要求"}, {"tag": "authority", "text": "金融服務人員展示監管標章與流程"}, {"tag": "time_pressure", "text": "要求當天寄卡才能排進本週作業"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 1
  WHERE case_key = $rw$romance-scam-034$rw$ AND difficulty = 3;
UPDATE public.game_cases SET title = $rw$補助款的帳戶問題$rw$
  WHERE case_key = $rw$atm-scam-033$rw$ AND title = $rw$補助款的信用分處理$rw$;
UPDATE public.game_cases SET narrative = $rw$我正在讀一封簡訊：「您的跨境匯款已出境，收款方境內未能聯繫，請確認是否有異；如無，請收款人聯繫中央銀行外匯部專員。」我上週確實匯了一筆海外學費。我加了專員的帳號，他傳來一張外匯查核公文，說這筆錢因為洗錢審查被暫停，兩小時內要再匯約六萬元保證款，證明款項用途，查完就退。他給了我一個私人的收款戶名，叫我不要跟別人說。$rw$
  WHERE case_key = $rw$atm-scam-034$rw$ AND narrative = $rw$我正在讀一封簡訊：「您的跨境匯款已出境，收款方境內未能聯繫，請確認是否有異；如無，請收款人聯繫中央銀行外匯部專員。」我最近確實匯過一筆海外學費，訊息裡還附了提醒匯款謹慎的文字。加入專員帳號後，對方傳來外匯查核公文，說款項因反洗錢審查暫停，兩小時內要再匯約六萬元保證款，才能證明原款用途；結案後兩筆會一同退回。他不讓我改撥銀行網站上的電話，並說查核內容不得對外透露。我看著他提供的私人收款戶名。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": "authority", "text": "自稱中央銀行外匯專員，傳來查核公文"}, {"tag": "time_pressure", "text": "要我兩小時內再匯一筆保證款"}]$rw$::jsonb
  WHERE case_key = $rw$atm-scam-034$rw$ AND red_flags = $rw$[{"tag": "authority", "text": "以中央銀行外匯專員與查核公文聯繫"}, {"tag": "time_pressure", "text": "要求兩小時內另付保證款完成審查"}, {"tag": "greed", "text": "承諾結案後原款與保證款一同退回"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀券商程式推來的盤前通知：「今天整理三檔產業觀察名單，本月前可以免費看完整報告。」底下有不少人留言，說上次那份名單很準。我點進去看，每一檔都寫了看好的理由，也寫了可能下跌的情況和資料日期，最下面註明只供研究參考。想買的話要自己在證券帳戶下單，錢從原本的交割戶扣。我正在比較報告裡的營收數字，還沒決定要不要買。$rw$
  WHERE case_key = $rw$investment-legit-031$rw$ AND narrative = $rw$我正在讀往來證券商應用程式的盤前通知：「今日提供三檔產業觀察名單，內容僅供研究，不代表買賣建議。」文章下方有讀者討論，但每檔都同時列出上漲理由、可能下跌情境與資料日期。通知提到本月前可免費使用研究報告，我也能不申請。若想交易，必須回到自己的證券帳戶，完成風險提示後自行下單，款項只從既有交割戶扣除；研究員不收款，也不承諾價格。我正在比較報告中的產業數據。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "每一檔都列出可能下跌的情況和資料日期"}, {"tag": null, "text": "要買得自己在證券帳戶下單"}, {"tag": null, "text": "款項從原本的交割戶扣"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-031$rw$ AND red_flags = $rw$[{"tag": null, "text": "名單同時列出下跌情境與資料日期"}, {"tag": null, "text": "交易須回本人證券帳戶自行下單"}, {"tag": null, "text": "款項僅由既有交割戶依委託扣除"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$收藏群的帶領者介紹一批紀念金幣，說是一家拍賣公司下個月的專場，這幾年價格漲了不少。群裡有人說已經在看了。我上網查到那家拍賣公司，目錄寫了每一枚的鑑定機構、重量和估價範圍。預展那幾天可以到現場看實物，證書號碼也能自己拿去鑑定機構查。得標的話錢付給拍賣公司，佣金和交貨日期都寫在拍賣條件裡。我拿著目錄，比較兩枚金幣的狀況。$rw$
  WHERE case_key = $rw$investment-legit-033$rw$ AND narrative = $rw$我在持有商業登記的拍賣公司看到一場紀念金幣專場，目錄寫明鑑定機構、重量、品相與估價區間，也提醒收藏品沒有保證增值。預展期間我能到現場查看實物，並用證書序號向鑑定機構核對。若得標，款項依拍賣條件付給公司帳戶，發票、買受人佣金與交付日期都載在書面契約；日後想轉售，仍需重新送拍與估價，拍賣公司不會預先承諾成交價。我正拿著目錄比較兩枚金幣的保存狀況。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "預展可以看實物，證書號碼能自己查"}, {"tag": null, "text": "目錄寫了鑑定機構、重量和估價範圍"}, {"tag": null, "text": "錢付給拍賣公司，佣金寫在拍賣條件裡"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-033$rw$ AND red_flags = $rw$[{"tag": null, "text": "實物可於預展查看並核對證書序號"}, {"tag": null, "text": "拍賣條件載明佣金交付與付款帳戶"}, {"tag": null, "text": "轉售須重新估價且不承諾成交價格"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀收藏群訊息：「這批三十年酒款只有四千瓶，協會專家已分走一千五百瓶，群友也預訂三百瓶，現在統計最後名單。」訊息後面附了一家拍賣公司的專場名稱。我上網查到這家公司，目錄有每瓶酒的來源、照片和保存狀況，佣金也寫在上面。報名要先付保證金，走公司的刷卡頁面，沒得標會退回原來的卡。我正在看保管和取貨的規定，還沒報名。$rw$
  WHERE case_key = $rw$investment-legit-034$rw$ AND narrative = $rw$收藏社團有人分享一場限量酒款拍賣，貼文下不少人討論年份與估價，拍賣場也公告了報名截止時間。我沒有在群組付款，而是從拍賣公司登記資料找到電話與網站，目錄可查每件拍品的來源、照片、保存狀況及佣金。若參加，保證金由公司金流收取並開立憑證，未得標會按條件退回原支付工具；得標也只代表買到藏品，不代表未來一定能以更高價格售出。我正在閱讀保管與取貨方式。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "目錄寫了每瓶酒的來源和保存狀況"}, {"tag": null, "text": "保證金走拍賣公司的刷卡頁面"}, {"tag": null, "text": "沒得標，保證金退回原來的卡"}]$rw$::jsonb
  WHERE case_key = $rw$investment-legit-034$rw$ AND red_flags = $rw$[{"tag": null, "text": "拍品來源狀況與佣金載於公開目錄"}, {"tag": null, "text": "保證金由公司金流收取並開立憑證"}, {"tag": null, "text": "未得標依條件退回原支付工具"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀手機簡訊：「您的包裹因關稅未繳而暫扣，請支付約一百六十元。」最近我確實有一件海外商品在路上。我打開手機上原本就有的實名委任報關程式，裡面真的有同一張運單，寫著申報的品名和稅費約一百六十元，繳費期限到這週五，繳費也在程式裡完成，只付這一筆。購物平台上的物流狀態還寫運送中。我正在核對申報的商品價格對不對。$rw$
  WHERE case_key = $rw$shopping-legit-031$rw$ AND narrative = $rw$我正在讀原購物平台的物流通知：「海外包裹已到海關，應繳稅費約一百六十元，請於報關應用程式確認。」我沒有使用簡訊連結，而是打開既有的實名委任應用程式，裡面確實列出同一運單、申報品名、稅額與承運業者。我可以先核對或提出申訴，繳費則由報關系統串接的金流完成，只需授權該筆金額，不會要求交出卡片驗證碼。通知有繳納期限，逾期會依報關程序處理。我正在比對商品價格與申報內容。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "原本的報關程式裡有同一張運單和稅費"}, {"tag": null, "text": "繳費在報關程式裡完成，只付這一筆"}, {"tag": null, "text": "申報的品名和金額都查得到"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-031$rw$ AND red_flags = $rw$[{"tag": null, "text": "運單品名稅額可在既有報關程式核對"}, {"tag": null, "text": "繳費只授權列明稅額且不交出驗證碼"}, {"tag": null, "text": "對申報內容可提出查詢或申訴"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀保健商品的體驗廣告，貼文寫著本週有組合價，留言有好幾個人在分享口味和吃法。我點進商品頁，上面列了完整成分、食品業者登錄字號和營養標示，也寫著孕婦和正在服藥的人要先問醫師。結帳走網站的金流，會開發票，沒拆封的話收到後幾天內可以退。我正在比較單盒和三盒的價格，打算先問看診的醫生適不適合我再決定。$rw$
  WHERE case_key = $rw$shopping-legit-033$rw$ AND narrative = $rw$我正在讀保健食品業者的體驗廣告，貼文有使用者分享口味與食用方式，也寫著本週組合價。商品頁不宣稱治療疾病，而是列出完整成分、食品業者登錄字號、營養標示及不適用族群。結帳前可下載退貨與客服資訊，付款透過網站金流，發票與訂單都會寄到會員帳戶；收到一般未拆封商品後，仍可依通訊交易規定在期限內申請解除契約。我正在比較單盒與三盒方案，並準備先詢問醫師是否適合。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "商品頁列出成分和食品業者登錄字號"}, {"tag": null, "text": "結帳走網站金流，會開發票"}, {"tag": null, "text": "寫明正在服藥的人要先問醫師"}]$rw$::jsonb
  WHERE case_key = $rw$shopping-legit-033$rw$ AND red_flags = $rw$[{"tag": null, "text": "商品頁列出成分登錄字號與營養標示"}, {"tag": null, "text": "付款經網站金流並產生發票與訂單"}, {"tag": null, "text": "未拆封商品載明解除契約申請方式"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀新認識的網友傳來的訊息。她說週末要去看一場金幣拍賣的預展，這幾年價格漲了不少，問我要不要一起去。她把拍賣公司的名稱給我，我自己上網查到那場預展，時間和地點都對得上，目錄上有每枚金幣的估價和鑑定資料。如果想下標，要先向拍賣公司登記、付保證金，沒得標會退回。我們約在展場門口見面，我正在查怎麼搭車過去。$rw$
  WHERE case_key = $rw$romance-legit-032$rw$ AND narrative = $rw$我正在讀新認識的網友傳來的訊息。她先問候我的工作近況，再分享週末要去看的金幣公開預展，說收藏市場價格有起伏，自己也還在研究。她把拍賣公司網站與目錄名稱告訴我，讓我自行搜尋，不代收款，也不要求跟著購買。預展可現場查看實物與核對證書，拍賣條件列明佣金和付款方式；如果我只想聊天或一起參觀也可以。我們已約在展場入口見面，我正在查詢交通方式與開放時間。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "預展的時間地點自己查得到，目錄有估價"}, {"tag": null, "text": "下標要向拍賣公司登記，沒得標保證金退回"}, {"tag": null, "text": "約在展場門口見面"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-032$rw$ AND red_flags = $rw$[{"tag": null, "text": "拍賣公司與目錄可自行搜尋核對"}, {"tag": null, "text": "預展可看實物並核對證書資料"}, {"tag": null, "text": "網友不代收款也接受只參觀不購買"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$交友軟體認識一個多月的對象說，他的銀行帳戶被暫停使用，問我能不能陪他去處理。我們白天一起去他開戶的那家分行，他帶著證件到櫃檯問，行員說帳戶狀態要由他本人依程序確認，今天缺一份文件，要另外約時間補。我坐在等候區陪他，他正拿著清單，跟行員一項一項確認要補哪些東西。我手上拿著他的外套，等他把事情問完再一起去吃飯。$rw$
  WHERE case_key = $rw$romance-legit-034$rw$ AND narrative = $rw$交友軟體認識一個多月的對象說自己的銀行帳戶暫停使用，問我能否陪他處理。我們約在白天到該銀行分行，他本人帶證件向櫃檯詢問；行員說帳戶狀態只能由本人依程序確認，不需要借用我的帳戶或金融卡。我只在等候區陪同，沒有交出密碼，也不代收或轉付任何款項。若當天文件不足，他會另約時間補件，不把結果和兩人的交往綁在一起。我正在和他確認分行營業時間及見面地點。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "由他本人帶證件到分行處理帳戶"}, {"tag": null, "text": "文件不齊，行員請他另外約時間補件"}]$rw$::jsonb
  WHERE case_key = $rw$romance-legit-034$rw$ AND red_flags = $rw$[{"tag": null, "text": "帳戶問題由本人持證件到分行辦理"}, {"tag": null, "text": "陪同者不交金融卡也不代收轉付款"}, {"tag": null, "text": "文件不足可另期補件且不牽動交往"}]$rw$::jsonb;
UPDATE public.game_cases SET difficulty = 1
  WHERE case_key = $rw$romance-legit-034$rw$ AND difficulty = 3;
UPDATE public.game_cases SET narrative = $rw$我正在讀健保快易通應用程式裡的通知：「您的健保卡即將停止使用，請核對補發案件。」看到停用兩個字我嚇了一跳。我前幾天弄丟健保卡，在這個程式申請了遺失補發。我從主選單點進補換發頁，案件的申請時間和我那天操作的一樣，寄送地址和規費也都列在上面，規費照頁面上的方式繳。我正在核對新卡的寄送地址，還沒按下完成。$rw$
  WHERE case_key = $rw$atm-legit-031$rw$ AND narrative = $rw$我剛在健保快易通應用程式申請遺失補發，現在正在讀站內確認通知：新卡製作後，原卡會停止使用，申請進度可由案件頁查詢。通知中的申請時間與我剛才操作相同，我也能從主選單重新進入補換發頁，不必加入任何通訊帳號。規費由應用程式列出的繳款管道處理，系統不會叫我到提款機轉帳，更不會要求提供銀行密碼。若想撤回或查詢，我可撥健保署公布電話或到服務據點辦理。我正在核對寄送地址。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "補換發頁的申請時間和我那天操作的一樣"}, {"tag": null, "text": "規費照補換發頁上列的方式繳"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-031$rw$ AND red_flags = $rw$[{"tag": null, "text": "通知時間與本人剛送出的補發申請相符"}, {"tag": null, "text": "案件可由既有應用程式主選單查詢"}, {"tag": null, "text": "疑問可撥健保署公布電話或臨櫃辦理"}]$rw$::jsonb;
UPDATE public.game_cases SET title = $rw$補助款的帳戶問題$rw$
  WHERE case_key = $rw$atm-legit-033$rw$ AND title = $rw$補助款的信用分處理$rw$;
UPDATE public.game_cases SET narrative = $rw$我正在讀基金會人員的訊息：「您申請補助時寫錯帳號，撥款沒有成功，請在月底前回到申請頁更正本人帳戶。」我上個月確實在這個基金會的網站申請了一筆獎助學金。我從當初申請的網站登入，案件頁也寫著帳戶核驗沒過，要我上傳本人存摺封面，月底前沒更正，這次就先不撥款。頁面最下面有基金會的公開電話。我正在找存摺封面的照片。$rw$
  WHERE case_key = $rw$atm-legit-033$rw$ AND narrative = $rw$我正在讀普發現金登記網站的結果：「帳戶核驗未成功，請於開放期間重新登記或改用其他公告領取方式。」我從政府公布入口重新進入查詢頁，核對身分資料、本人帳戶與登記結果；頁面沒有信用分，也不會要求先匯一部分現金。若重新登記仍未通過，我可依公告到指定金融機構或提款機領取，銀行也不會因這筆政府批次入帳就要求付解鎖費。各種方式的開放日期都在同一公告頁。我正在比對帳戶戶名與領取期限。$rw$;
UPDATE public.game_cases SET provenance = $rw$依據：民間獎助學金撥款前核對本人帳戶的一般作法$rw$
  WHERE case_key = $rw$atm-legit-033$rw$ AND provenance = $rw$依據：金管會「普發現金安心領」與政府登記入帳領取流程$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "申請網站的案件頁寫著同樣的帳戶問題"}, {"tag": null, "text": "只要上傳本人存摺封面更正"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-033$rw$ AND red_flags = $rw$[{"tag": null, "text": "登記結果可從政府公布入口重新查詢"}, {"tag": null, "text": "核驗未成功可改用公告的領取方式"}, {"tag": null, "text": "領取前不需轉帳或支付解鎖費用"}]$rw$::jsonb;
UPDATE public.game_cases SET narrative = $rw$我正在讀一封簡訊：「您的跨境匯款資料不完整，已暫停處理，請登入行動銀行查看。」我上週確實從這家銀行匯了一筆海外學費給學校。我自己打開銀行的程式，那筆匯款停在補件，原因是學校的英文地址少一欄，案件頁有承辦分行的電話和補件期限，期限內沒補的話，錢會退回原本扣款的帳戶。我拿著學校的繳費通知，正在對學校的英文地址。$rw$
  WHERE case_key = $rw$atm-legit-034$rw$ AND narrative = $rw$我正在讀往來銀行應用程式的跨境匯款通知，內容顯示海外學費匯款因收款資料缺少欄位而暫待處理。我從匯款紀錄進入案件頁，看到相同金額、學校名稱與承辦分行電話。銀行請我在期限內補上學校地址，或由本人帶匯款水單到分行確認；不會要求另付保證款到其他帳戶。若不補件，原款會依規定退回我的扣款帳戶，相關費用也列在頁面。我正拿著校方繳費通知核對英文地址。$rw$;
UPDATE public.game_cases SET red_flags = $rw$[{"tag": null, "text": "銀行程式裡同一筆匯款停在補件"}, {"tag": null, "text": "沒補件的話錢退回原扣款帳戶"}]$rw$::jsonb
  WHERE case_key = $rw$atm-legit-034$rw$ AND red_flags = $rw$[{"tag": null, "text": "金額校名與分行電話可在匯款紀錄核對"}, {"tag": null, "text": "補件可在案件頁或本人到分行完成"}, {"tag": null, "text": "未完成時原款依規定退回扣款帳戶"}]$rw$::jsonb;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "親自到機構的服務據點問"}, {"key": "B", "text": "從原本的程式查這件事"}, {"key": "C", "text": "自己打機構公開的電話問"}]$rw$::jsonb
  WHERE question_key = $rw$verif-atm-legit-031-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "掛斷後自行改撥卡片背面客服"}, {"key": "B", "text": "自行查機構總機再轉承辦窗口"}, {"key": "C", "text": "從原本就在使用的程式查案件"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$B$rw$
  WHERE question_key = $rw$verif-atm-legit-031-1$rw$ AND version = 1 AND correct_key = $rw$C$rw$;
UPDATE public.game_case_questions SET explanation = $rw$你已經在原本的健保程式裡看到同一筆補發案件，寄送地址就列在補換發頁，直接在那裡核對最快。看不懂的地方，也可以自己查健保署的電話問，或到服務據點問，只是要多花時間。$rw$
  WHERE question_key = $rw$verif-atm-legit-031-1$rw$ AND version = 1 AND explanation = $rw$此刻要核對的是寄送地址這個欄位，只有案件頁逐項列得出來。健保署公布電話與服務據點辦得了撤回與查詢進度，但對方不會逐字唸出你填的地址；卡背客服則是金融卡與信用卡的管道，與健保補卡無關。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "從原本的程式查這件事"}, {"key": "B", "text": "到公開的登記名單查對方"}, {"key": "C", "text": "打165問這種說法"}]$rw$::jsonb
  WHERE question_key = $rw$verif-atm-legit-034-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "掛斷後自行改撥卡片背面客服"}, {"key": "B", "text": "從原本就在使用的程式查案件"}, {"key": "C", "text": "自行查機構總機再轉承辦窗口"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$A$rw$
  WHERE question_key = $rw$verif-atm-legit-034-1$rw$ AND version = 1 AND correct_key = $rw$B$rw$;
UPDATE public.game_case_questions SET explanation = $rw$這筆學費是你自己從這家銀行匯的，銀行程式的案件頁已經寫出缺的是學校的英文地址，還有補件期限，直接在程式裡核對、補上最快。需要有人幫忙時，也可以打銀行的客服或到分行問。簡訊只叫你登入自己的銀行看，沒有要你做別的事。$rw$
  WHERE question_key = $rw$verif-atm-legit-034-1$rw$ AND version = 1 AND explanation = $rw$要補的是學校地址這一欄，只有銀行應用程式的案件頁列得出缺什麼、期限到哪天。行員或客服問得到一般處理流程，律師審閱的是私人契約；兩者都不會逐欄告訴你這筆匯款還差什麼。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "從原本的程式查這件事"}, {"key": "B", "text": "親自到機構的服務據點問"}, {"key": "C", "text": "自己打機構公開的電話問"}]$rw$::jsonb
  WHERE question_key = $rw$verif-atm-scam-022-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "從原本就在使用的程式查案件"}, {"key": "B", "text": "掛斷後自行改撥卡片背面客服"}, {"key": "C", "text": "自行查機構總機再轉承辦窗口"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$C$rw$
  WHERE question_key = $rw$verif-atm-scam-022-1$rw$ AND version = 1 AND correct_key = $rw$B$rw$;
UPDATE public.game_case_questions SET explanation = $rw$電話那頭自稱銀行，正要你新增受款人、念驗證碼。先掛掉，自己打卡片背面那支銀行的電話問：有沒有這筆境外交易、剛才那通電話是不是他們打的。銀行程式查得到交易，但查不到剛才是誰打來；跑一趟分行也太慢。$rw$
  WHERE question_key = $rw$verif-atm-scam-022-1$rw$ AND version = 1 AND explanation = $rw$這是一通打進來的電話，對方自稱銀行。來電號碼能偽造，所以要先掛斷，再撥卡片背面印的號碼，那是唯一不會被對方指定的管道。打開銀行 App 雖然也安全，但卡片爭議交易本來就由發卡客服處理；總機轉窗口在這裡只是繞遠路。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "自己打機構公開的電話問"}, {"key": "B", "text": "親自到機構的服務據點問"}, {"key": "C", "text": "從原本的程式查這件事"}]$rw$::jsonb
  WHERE question_key = $rw$verif-atm-scam-023-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "請律師逐條核對書面契約條款"}, {"key": "B", "text": "從官方應用程式功能頁查款項"}, {"key": "C", "text": "向往來機構行員或官方客服確認"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$B$rw$
  WHERE question_key = $rw$verif-atm-scam-023-1$rw$ AND version = 1 AND correct_key = $rw$C$rw$;
UPDATE public.game_case_questions SET explanation = $rw$你人就在分行，眼前的行員正在問有沒有人在電話裡指導你。電話那頭叫你說謊，這件事要直接照實告訴行員，由銀行幫你確認這筆該不該匯。另外打電話或開程式都比當面講慢，對方也還在線上催你。$rw$
  WHERE question_key = $rw$verif-atm-scam-023-1$rw$ AND version = 1 AND explanation = $rw$你人在櫃檯，對方在電話裡要你別說出匯款原因，光是這句話就是警訊。該做的是把完整經過如實告訴眼前的行員（或另外撥往來銀行官方客服），由銀行確認這筆匯款的正當流程。這裡沒有契約要律師看，帳戶功能頁也不會告訴你對方為什麼要你隱瞞。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "銀行的紀錄列出這筆刷卡授權"}, {"key": "B", "text": "對方的訊息或來電列出交易內容"}, {"key": "C", "text": "平台後台列出這筆訂單已付款"}]$rw$::jsonb
  WHERE question_key = $rw$verif-atm-legit-021-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "已向發卡機構核對這筆交易授權紀錄"}, {"key": "B", "text": "僅取得聯絡者提供的交易相關資訊"}, {"key": "C", "text": "已自行核對平台後台的訂單付款狀態"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$你自己打卡片背面的電話，銀行查到了這兩筆授權，這是銀行那邊的紀錄。打來的客服沒有講任何交易內容，只請你跟銀行確認；你這次也沒有去看購物平台的後台。$rw$
  WHERE question_key = $rw$verif-atm-legit-021-1$rw$ AND version = 1 AND explanation = $rw$情境明確寫到銀行客服查得相同授權紀錄並建立爭議案件，因此有發卡機構的查詢依據；授權仍不等於最後請款。聯絡者提及交易資訊只描述收到說法的層次；平台工單是在查重複扣款，並未呈現平台後台的已付款狀態，不能用它替代銀行查核結果。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "對方的訊息或來電列出交易內容"}, {"key": "B", "text": "平台後台列出這筆訂單已付款"}, {"key": "C", "text": "銀行的紀錄列出這筆刷卡授權"}]$rw$::jsonb
  WHERE question_key = $rw$verif-atm-scam-001-v2-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "僅取得聯絡者提供的交易相關資訊"}, {"key": "B", "text": "已自行核對平台後台的訂單付款狀態"}, {"key": "C", "text": "已向發卡機構核對這筆交易授權紀錄"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$對方報得出你的姓名和上個月買的東西，這只代表他手上有你的訂單資料，不代表他是客服。購物平台的後台和銀行的紀錄你都還沒看過，這兩項都還沒有根據。$rw$
  WHERE question_key = $rw$verif-atm-scam-001-v2-1$rw$ AND version = 1 AND explanation = $rw$來電者能說出姓名、商品與金額，直接支持的只是他掌握交易資訊。若自行登入平台看到付款狀態，才能支持平台留有付款紀錄；若獨立聯絡發卡機構查得授權，才能支持銀行已有授權紀錄。情境中這兩種查核都尚未發生，熟知訂單不等於身分已確認。$rw$;
UPDATE public.game_case_questions SET explanation = $rw$票已經轉進你原本的售票帳號，場次和座位在訂單頁上看得到，先在訂單頁核對最直接。有疑問也可以自己查業者的電話問；主管機關不管個別票券的轉讓紀錄。$rw$
  WHERE question_key = $rw$verif-fake-sale-legit-023-1$rw$ AND version = 1 AND explanation = $rw$要確認的是票有沒有真的轉進自己帳號、場次與座位對不對，這些只在售票系統的訂單頁上。打電話問業者得到的是一般規則，主管機關不掌管個別票券的轉讓紀錄。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "到公開的登記名單查對方"}, {"key": "B", "text": "從原本的程式查這件事"}, {"key": "C", "text": "打165問這種說法"}]$rw$::jsonb
  WHERE question_key = $rw$verif-fake-sale-scam-031-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "從原平台官方入口查帳戶狀態"}, {"key": "B", "text": "從主管機關官方名單查資格"}, {"key": "C", "text": "從商業登記查營業主體的資料"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$B$rw$
  WHERE question_key = $rw$verif-fake-sale-scam-031-1$rw$ AND version = 1 AND correct_key = $rw$A$rw$;
UPDATE public.game_case_questions SET explanation = $rw$你已經在原本的平台訂單頁，裡面沒有這筆交易，也沒有什麼實名程序，平台的規定以自己帳戶裡看到的為準。165 能說明這種手法，但查不到你這筆訂單；登記名單查的是公司在不在，查不到這則通知是誰發的。$rw$
  WHERE question_key = $rw$verif-fake-sale-scam-031-1$rw$ AND version = 1 AND explanation = $rw$對方要你離開平台、改到通訊軟體完成實名程序。平台的實名規則與帳戶狀態，只有從原平台官方入口登入才看得到。主管機關名單與商業登記查的都是機構，回答不了「這個平台真的要求我這樣做嗎」。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "對方的訊息或來電列出交易內容"}, {"key": "B", "text": "平台後台列出這筆訂單已付款"}, {"key": "C", "text": "銀行的紀錄列出這筆刷卡授權"}]$rw$::jsonb
  WHERE question_key = $rw$verif-fake-sale-legit-034-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "僅取得聯絡者提供的交易相關資訊"}, {"key": "B", "text": "已自行核對平台後台的訂單付款狀態"}, {"key": "C", "text": "已向發卡機構核對這筆交易授權紀錄"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$你自己打開平台後台，看到同一筆訂單已付款，這有直接根據；錢還在平台代管，還沒撥進你的帳戶。買家的訊息只問能不能今天寄，沒有列交易內容；這次也沒有查銀行的紀錄。$rw$
  WHERE question_key = $rw$verif-fake-sale-legit-034-1$rw$ AND version = 1 AND explanation = $rw$自己打開平台後台已找到同一訂單與已付款狀態，支持的是平台內這筆付款紀錄，還不是貨款已撥入自己的銀行。聯絡者提及交易資訊只描述郵件或對話；發卡機構的授權紀錄則需向銀行查得，本情境沒有這項查詢。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "對方的訊息或來電列出交易內容"}, {"key": "B", "text": "平台後台列出這筆訂單已付款"}, {"key": "C", "text": "銀行的紀錄列出這筆刷卡授權"}]$rw$::jsonb
  WHERE question_key = $rw$verif-fake-sale-scam-021-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "僅取得聯絡者提供的交易相關資訊"}, {"key": "B", "text": "已自行核對平台後台的訂單付款狀態"}, {"key": "C", "text": "已向發卡機構核對這筆交易授權紀錄"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$買家傳來付款成功的截圖，金流人員也說錢被鎖住，這些都是對方說的。你自己看過賣家後台，裡面沒有這筆訂單，「後台已付款」並不成立；也沒有人查過銀行的紀錄。$rw$
  WHERE question_key = $rw$verif-fake-sale-scam-021-1$rw$ AND version = 1 AND explanation = $rw$目前有的是買家提供的付款截圖與金流人員的說法，因此只能確認對方提出了交易相關資訊。平台後台反而沒有訂單，不能支持平台已留有付款狀態；也沒有獨立向發卡機構查到授權。後兩項各需平台紀錄或銀行查詢，截圖本身不能替代。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "自己打機構的官方客服問"}, {"key": "B", "text": "請專業的人看過書面條件"}, {"key": "C", "text": "從原本的程式查這筆款項"}]$rw$::jsonb
  WHERE question_key = $rw$verif-investment-legit-021-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "向往來機構行員或官方客服確認"}, {"key": "B", "text": "請律師逐條核對書面契約條款"}, {"key": "C", "text": "從官方應用程式功能頁查款項"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$截止時間、承銷價和要從哪個帳戶預扣，申購頁上都寫了，你也已經在券商的程式裡，直接在申購頁核對最快。打客服也問得到，只是比較慢；這筆申購沒有需要請人看的書面契約。$rw$
  WHERE question_key = $rw$verif-investment-legit-021-1$rw$ AND version = 1 AND explanation = $rw$要核對的是這次申購何時截止、怎麼預扣，這些都在自己券商帳戶的申購功能裡。客服問得到一般規則但不是你這筆，新股申購也沒有需要律師審閱的私人契約。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "打165問這種說法"}, {"key": "B", "text": "到公開的登記名單查對方"}, {"key": "C", "text": "從原本的程式查這件事"}]$rw$::jsonb
  WHERE question_key = $rw$verif-investment-scam-032-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "從主管機關官方名單查資格"}, {"key": "B", "text": "從原平台官方入口查帳戶狀態"}, {"key": "C", "text": "從商業登記查營業主體的資料"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$C$rw$
  WHERE question_key = $rw$verif-investment-scam-032-1$rw$ AND version = 1 AND correct_key = $rw$B$rw$;
UPDATE public.game_case_questions SET explanation = $rw$這家交易所你查過是真的，帳號也是你自己開的。打開交易所的程式，看帳戶裡有沒有這筆額度最快。登記名單你已經查過了，只能證明交易所是真的，不能證明帶領者說的是真的；165 能說明手法，但查不到你的帳戶。$rw$
  WHERE question_key = $rw$verif-investment-scam-032-1$rw$ AND version = 1 AND explanation = $rw$訊息要你去一個新網站處理資金，但你的帳戶在原本的交易所。直接從原平台官方入口登入，看得到帳戶真正的狀態與有沒有這筆審核。主管機關名單查的是機構資格，商業登記查的是公司；兩者都不會告訴你自己的帳戶現在怎麼了。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "打165問這種說法"}, {"key": "B", "text": "從原本的程式查這件事"}, {"key": "C", "text": "到公開的登記名單查對方"}]$rw$::jsonb
  WHERE question_key = $rw$verif-investment-scam-031-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "從主管機關官方名單查資格"}, {"key": "B", "text": "從商業登記查營業主體的資料"}, {"key": "C", "text": "從原平台官方入口查帳戶狀態"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$C$rw$
  WHERE question_key = $rw$verif-investment-scam-031-1$rw$ AND version = 1 AND correct_key = $rw$A$rw$;
UPDATE public.game_case_questions SET explanation = $rw$這位講師要收錢帶你進出，得有投顧資格。貼文上有他的名字，到投信投顧公會的網站一查，就知道有沒有登記。165 能說明手法，但查不到這個人；你和他也沒有任何原本在用的程式可以查。$rw$
  WHERE question_key = $rw$verif-investment-scam-031-1$rw$ AND version = 1 AND explanation = $rw$收費提供「即時帶進出」就是代客操作，該查的是這個人與機構有沒有投顧資格。商業登記只看得到公司存不存在，原平台入口在這裡用不上，因為根本沒有平台，錢是直接匯到個人帳戶。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "群組訊息列有他人參與的數量"}, {"key": "B", "text": "對方傳來的憑證列有方案內容"}, {"key": "C", "text": "手上文件列有費用與風險說明"}]$rw$::jsonb
  WHERE question_key = $rw$verif-investment-legit-012-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "群組訊息列有他人參與的數量"}, {"key": "B", "text": "對方傳來的憑證列有方案內容"}, {"key": "C", "text": "手上文件列有金額與費用明細"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$銀行的基金頁和月報列出這檔某一年大跌的走勢、手續費和經理費，還印著過去績效不代表未來，這些都有根據。群裡只說很多人在買，沒有列出人數；也沒有人傳憑證給你。這些資料能說明過去的波動和成本，不能保證以後。$rw$
  WHERE question_key = $rw$verif-investment-legit-012-1$rw$ AND version = 1 AND explanation = $rw$理專交付的文件上確實有過去的跌幅與逐項費用，這部分有直接依據。這裡沒有群組，也沒有誰傳憑證給你；文件能支持的就是歷史波動與成本，不能拿來保證未來。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "手上文件列有費用與風險說明"}, {"key": "B", "text": "群組訊息列有他人參與的數量"}, {"key": "C", "text": "對方傳來的憑證列有方案內容"}]$rw$::jsonb
  WHERE question_key = $rw$verif-investment-scam-034-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "手上文件列有金額與費用明細"}, {"key": "B", "text": "群組訊息列有他人參與的數量"}, {"key": "C", "text": "對方傳來的憑證列有方案內容"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$能確認的只有群組裡出現了預訂數字這件事，不代表真的有人付過款。對方沒有提供保管契約或任何憑證，你手上也沒有列著費用與風險說明的文件。$rw$
  WHERE question_key = $rw$verif-investment-scam-034-1$rw$ AND version = 1 AND explanation = $rw$能確認的只有群組裡出現了預訂數字這件事，不代表真的有人付過款。對方沒有提供保管契約或任何憑證，你手上也沒有列著金額與費用的文件。$rw$;
UPDATE public.game_case_questions SET explanation = $rw$包廂的訂金和取消規定網站上沒寫，網站下面就有餐廳自己的電話，打去問最直接。訂位頁目前只看得到一般座位的規則；主管機關不管個別餐廳的訂位規定。$rw$
  WHERE question_key = $rw$verif-romance-legit-023-1$rw$ AND version = 1 AND explanation = $rw$訂金規則與取消期限要向餐廳本身確認，而且電話要自己查。敘事裡她沒有加對方給的店長帳號，而是自行搜尋登記電話，這正是這題的重點。訂位系統頁面呈現的是系統端條件，主管機關也不管個別餐廳的取消政策。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "從原本的程式查這筆款項"}, {"key": "B", "text": "自己打機構的官方客服問"}, {"key": "C", "text": "請專業的人看過書面條件"}]$rw$::jsonb
  WHERE question_key = $rw$verif-romance-legit-033-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "請律師逐條核對書面契約條款"}, {"key": "B", "text": "向往來機構行員或官方客服確認"}, {"key": "C", "text": "從官方應用程式功能頁查款項"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$C$rw$
  WHERE question_key = $rw$verif-romance-legit-033-1$rw$ AND version = 1 AND correct_key = $rw$A$rw$;
UPDATE public.game_case_questions SET explanation = $rw$要確認的是還沒簽的借款契約，利息、還款日和雙方的權利，請律師逐條看過最可靠，她也這樣建議。錢還沒有匯，程式裡查不到東西；銀行客服也不審私人之間的借款契約。$rw$
  WHERE question_key = $rw$verif-romance-legit-033-1$rw$ AND version = 1 AND explanation = $rw$現在要處理的是還沒簽的借款契約，利息、還款日與雙方權利得由律師逐條看過。銀行客服不審閱私人借貸條款，帳戶功能頁在款項還沒進來之前也看不到東西。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "到公開的登記名單查對方"}, {"key": "B", "text": "打165問這種說法"}, {"key": "C", "text": "從原本的程式查這件事"}]$rw$::jsonb
  WHERE question_key = $rw$verif-romance-scam-024-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "掛斷後自行改撥卡片背面客服"}, {"key": "B", "text": "從原本就在使用的程式查案件"}, {"key": "C", "text": "自行查機構總機再轉承辦窗口"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$B$rw$
  WHERE question_key = $rw$verif-romance-scam-024-1$rw$ AND version = 1 AND correct_key = $rw$C$rw$;
UPDATE public.game_case_questions SET explanation = $rw$繳費通知上的醫院名字被裁掉了，你連是哪家醫院都不知道，查不到它的登記，也沒有程式可以查。先打165問這種「把押金匯給醫院財務」的說法，錢先不要匯。知道是哪家醫院以後，才能自己查電話問正式的繳費方式。$rw$
  WHERE question_key = $rw$verif-romance-scam-024-1$rw$ AND version = 1 AND explanation = $rw$款項被說成手術押金，通知卻被裁掉抬頭。要確認這張單子是不是真的，只能自己查到院所總機、再轉收費窗口問正式繳費管道。卡背客服處理的是自己的卡片，醫療院所也沒有你能登入的既有程式。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "請專業的人看過書面條件"}, {"key": "B", "text": "自己打機構的官方客服問"}, {"key": "C", "text": "從原本的程式查這筆款項"}]$rw$::jsonb
  WHERE question_key = $rw$verif-romance-scam-033-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "請律師逐條核對書面契約條款"}, {"key": "B", "text": "向往來機構行員或官方客服確認"}, {"key": "C", "text": "從官方應用程式功能頁查款項"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$收款從來不需要把提款卡寄出去，也不用給密碼。卡片寄出前，自己打給往來銀行的客服問一聲，就能確認銀行沒有這種「測試收款」的程序。錢還沒進來，程式裡查不到東西；這件事也沒有契約可以請人看。$rw$
  WHERE question_key = $rw$verif-romance-scam-033-1$rw$ AND version = 1 AND explanation = $rw$收款不需要交出提款卡或密碼，這件事沒有例外。打給自己往來銀行的官方客服，是為了把這條規則確認清楚，不是去問寄卡流程。這裡沒有書面契約要律師看，帳戶功能頁也不會出現「先寄卡才能收款」這種選項。$rw$;
UPDATE public.game_case_questions SET explanation = $rw$房子你一次都還沒看過，先約到現場看房，當場核對權狀和屋主的身分；對方自稱代理人，還要看屋主寫的授權書。鑑定報告和證書查詢，都不能證明這個帳號真的有權出租這間房。$rw$
  WHERE question_key = $rw$verif-shopping-scam-003-v2-1$rw$ AND version = 1 AND explanation = $rw$房子你一次都還沒看過，聯絡的人又自稱代理人。到現場看屋並當場核對權狀與身分，才同時確認得了房子存在、以及這個人有沒有權利出租。獨立鑑定不處理不動產，謄本上的發證資料也對不上線上這個帳號。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "到公開的登記名單查對方"}, {"key": "B", "text": "從原本的程式查這件事"}, {"key": "C", "text": "打165問這種說法"}]$rw$::jsonb
  WHERE question_key = $rw$verif-shopping-scam-022-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "從主管機關官方名單查資格"}, {"key": "B", "text": "從商業登記查營業主體的資料"}, {"key": "C", "text": "從原平台官方入口查帳戶狀態"}]$rw$::jsonb;
UPDATE public.game_case_questions SET correct_key = $rw$A$rw$
  WHERE question_key = $rw$verif-shopping-scam-022-1$rw$ AND version = 1 AND correct_key = $rw$B$rw$;
UPDATE public.game_case_questions SET explanation = $rw$對方不給地址、只給私人帳戶，你也不是在原本的商店頁跟他買。先用貼文上的工作室名稱查商業登記，看有沒有這家店、登記在哪裡，查到以後再自己找電話或去店裡問。查到店家存在，也不代表跟你私訊的人就是這家店。$rw$
  WHERE question_key = $rw$verif-shopping-scam-022-1$rw$ AND version = 1 AND explanation = $rw$爭點是這個收錢的人到底是誰。商業登記查得到工作室存不存在、登記地址與負責人是誰。這種個人工作室不受金融主管機關名單管轄，對方也刻意不讓你從原本的商店頁結帳，沒有平台紀錄可查。$rw$;
UPDATE public.game_case_questions SET explanation = $rw$現場看過屋主的權狀和身分證，名字和地址都對得上，這有直接根據。屋主拿出的是他自己寫的訂金單，不是機構開的收據；這次也沒有人傳照片給你。$rw$
  WHERE question_key = $rw$verif-shopping-legit-013-1$rw$ AND version = 1 AND explanation = $rw$現場看到屋主的證件與權狀，敘事明說姓名地址相符，這點有直接依據。當場那張收據是屋主本人簽的，不是機構開立的；抵押設定要調謄本才看得到。兩者都不在這次看房已取得的資料裡。$rw$;
UPDATE public.game_case_questions SET options = $rw$[{"key": "A", "text": "手上文件列有費用與風險說明"}, {"key": "B", "text": "對方傳來的憑證列有方案內容"}, {"key": "C", "text": "群組訊息列有他人參與的數量"}]$rw$::jsonb
  WHERE question_key = $rw$verif-shopping-scam-024-1$rw$ AND version = 1 AND options = $rw$[{"key": "A", "text": "手上文件列有金額與費用明細"}, {"key": "B", "text": "對方傳來的憑證列有方案內容"}, {"key": "C", "text": "群組訊息列有他人參與的數量"}]$rw$::jsonb;
UPDATE public.game_case_questions SET explanation = $rw$手上只有小編傳來的住宿券，能確認的是券面寫了旅宿名稱、住兩晚和早餐，不能證明券是真的、房間已經訂好。你手上沒有列出費用和規定的正式文件，留言區的揪團也沒寫出人數。$rw$
  WHERE question_key = $rw$verif-shopping-scam-024-1$rw$ AND version = 1 AND explanation = $rw$手上只有小編傳來的住宿券，能確認的就是券面上寫了什麼方案。那不是載明費用明細的正式文件，留言區的揪團也不是你所在群組的預訂紀錄；券的格式再完整也不等於訂房成立。$rw$;
UPDATE public.game_case_questions SET explanation = $rw$對方是網路上認識的人，不肯視訊，收保證金的單位也查不到是誰。這種時候打165問最快，可以知道這套說法是不是常見的手法。自己的銀行能說明匯款的風險，但查不到這個人是誰；主管機關名單查的是金融機構，對不上一個網友。$rw$
  WHERE question_key = $rw$verif-romance-scam-001-v2-1$rw$ AND version = 1 AND explanation = $rw$對方是網路上認識的人、拒絕視訊，「移民保證金」與「清關費」都沒有任何查得到的單位在收款。這正是 165 的用途：查證這套說法是不是常見的詐騙手法。往來銀行只能告訴你錢匯出去了，主管機關名單查的是金融機構的資格，兩者都對不上一個身分查不出來的人。$rw$;
UPDATE public.game_case_questions SET explanation = $rw$訊息說是你的銀行，銀行是找得到本人的：自己打銀行的官方客服，就能問到有沒有這筆被暫停的轉帳。165 能幫你判斷這種「驗證款」的說法，但查不到你這筆交易，號碼沒被檢舉也不代表安全；主管機關名單查的是機構有沒有立案。$rw$
  WHERE question_key = $rw$verif-atm-scam-024-1$rw$ AND version = 1 AND explanation = $rw$這則訊息宣稱是你的銀行，而你的銀行是找得到本尊的。不要回訊息，自己撥官方客服，就問得到有沒有這筆被暫停的轉帳。165 查得到某個號碼有沒有被檢舉，但查不到你這筆交易的狀態；主管機關名單查的是機構有沒有立案，也不是你這筆轉帳。能直接找到本尊時，找本尊比查手法更快。$rw$;
COMMIT;

-- 檢查:改寫後應有的列數(已發布的案例 120、查證題 34)
SELECT 'game_cases' AS 資料表, count(*) FROM public.game_cases WHERE status = 'published'
UNION ALL
SELECT 'game_case_questions', count(*) FROM public.game_case_questions WHERE status = 'published';
