--
-- PostgreSQL database dump
--

\restrict Ov4cEq55AnEbf3xlWDwKjv6J4Pw2zBfSaNOub7tgS7oc8h8j4F9RRmho7TLqONN

-- Dumped from database version 17.10 (Debian 17.10-1.pgdg12+1)
-- Dumped by pg_dump version 17.10 (Debian 17.10-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: game_case_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_case_questions (
    id bigint NOT NULL,
    question_key text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    case_id bigint NOT NULL,
    question_kind text NOT NULL,
    question text NOT NULL,
    options jsonb NOT NULL,
    correct_key text NOT NULL,
    explanation text NOT NULL,
    weakness_tag text,
    difficulty integer DEFAULT 2 NOT NULL,
    source_document_ids bigint[] DEFAULT '{}'::bigint[] NOT NULL,
    provenance text,
    status text DEFAULT 'draft'::text NOT NULL,
    review_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    published_at timestamp with time zone
);


--
-- Name: game_case_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.game_case_questions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: game_case_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.game_case_questions_id_seq OWNED BY public.game_case_questions.id;


--
-- Name: game_case_questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_case_questions ALTER COLUMN id SET DEFAULT nextval('public.game_case_questions_id_seq'::regclass);


--
-- PostgreSQL database dump complete
--

\unrestrict Ov4cEq55AnEbf3xlWDwKjv6J4Pw2zBfSaNOub7tgS7oc8h8j4F9RRmho7TLqONN

COPY public.game_case_questions (id, question_key, version, case_id, question_kind, question, options, correct_key, explanation, weakness_tag, difficulty, source_document_ids, provenance, status, review_notes, created_at, published_at) FROM stdin;
1059	verif-atm-legit-031-1	1	427	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "掛斷後自行改撥卡片背面客服"}, {"key": "B", "text": "自行查機構總機再轉承辦窗口"}, {"key": "C", "text": "從原本就在使用的程式查案件"}]	C	此刻要核對的是寄送地址這個欄位,只有案件頁逐項列得出來。健保署公布電話與服務據點辦得了撤回與查詢進度,但對方不會逐字唸出你填的地址;卡背客服則是金融卡與信用卡的管道,與健保補卡無關。	authority	1	{}	\N	published	\N	2026-09-22 11:30:17.090495+00	2026-09-22 11:30:19.306883+00
1060	verif-atm-legit-034-1	1	430	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "掛斷後自行改撥卡片背面客服"}, {"key": "B", "text": "從原本就在使用的程式查案件"}, {"key": "C", "text": "自行查機構總機再轉承辦窗口"}]	B	要補的是學校地址這一欄,只有銀行應用程式的案件頁列得出缺什麼、期限到哪天。行員或客服問得到一般處理流程,律師審閱的是私人契約;兩者都不會逐欄告訴你這筆匯款還差什麼。	authority	3	{}	\N	published	\N	2026-09-22 11:30:17.160062+00	2026-09-22 11:30:19.306883+00
1061	verif-atm-scam-022-1	1	368	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從原本就在使用的程式查案件"}, {"key": "B", "text": "掛斷後自行改撥卡片背面客服"}, {"key": "C", "text": "自行查機構總機再轉承辦窗口"}]	B	這是一通打進來的電話，對方自稱銀行。來電號碼能偽造，所以要先掛斷，再撥卡片背面印的號碼——那是唯一不會被對方指定的管道。開程式雖然也安全，但卡片爭議交易本來就由發卡客服處理；總機轉窗口在這裡只是繞遠路。	authority	2	{}	\N	published	\N	2026-09-22 11:30:17.230224+00	2026-09-22 11:30:19.306883+00
1062	verif-atm-scam-023-1	1	369	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "請律師逐條核對書面契約條款"}, {"key": "B", "text": "從官方應用程式功能頁查款項"}, {"key": "C", "text": "向往來機構行員或官方客服確認"}]	C	你人在櫃檯,對方在電話裡要你別說出匯款原因——那句話本身就是警訊。該做的是把完整經過如實告訴眼前的行員(或另外撥往來銀行官方客服),由銀行確認這筆匯款的正當流程。這裡沒有契約要律師看,帳戶功能頁也不會告訴你對方為什麼要你隱瞞。	authority	3	{}	\N	published	\N	2026-09-22 11:30:17.302412+00	2026-09-22 11:30:19.306883+00
1063	verif-atm-legit-021-1	1	387	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "已向發卡機構核對這筆交易授權紀錄"}, {"key": "B", "text": "僅取得聯絡者提供的交易相關資訊"}, {"key": "C", "text": "已自行核對平台後台的訂單付款狀態"}]	A	情境明確寫到銀行客服查得相同授權紀錄並建立爭議案件，因此有發卡機構的查詢依據；授權仍不等於最後請款。聯絡者提及交易資訊只描述收到說法的層次；平台工單是在查重複扣款，並未呈現平台後台的已付款狀態，不能用它替代銀行查核結果。	time_pressure	1	{}	\N	published	\N	2026-09-22 11:30:17.387879+00	2026-09-22 11:30:19.306883+00
1064	verif-atm-scam-001-v2-1	1	321	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "僅取得聯絡者提供的交易相關資訊"}, {"key": "B", "text": "已自行核對平台後台的訂單付款狀態"}, {"key": "C", "text": "已向發卡機構核對這筆交易授權紀錄"}]	A	來電者能說出姓名、商品與金額，直接支持的只是他掌握交易資訊。若自行登入平台看到付款狀態，才能支持平台留有付款紀錄；若獨立聯絡發卡機構查得授權，才能支持銀行已有授權紀錄。情境中這兩種查核都尚未發生，熟知訂單不等於身分已確認。	trust_building	2	{}	\N	published	\N	2026-09-22 11:30:17.454022+00	2026-09-22 11:30:19.306883+00
1065	verif-fake-sale-legit-023-1	1	377	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "自行查公開電話向業者確認"}, {"key": "B", "text": "從服務自己的訂單頁核對條件"}, {"key": "C", "text": "從主管機關入口核對申報資料"}]	B	要確認的是票有沒有真的轉進自己帳號、場次與座位對不對，這些只在售票系統的訂單頁上。打電話問業者得到的是一般規則，主管機關不掌管個別票券的轉讓紀錄。	social_proof	3	{}	\N	published	\N	2026-09-22 11:30:17.523947+00	2026-09-22 11:30:19.306883+00
1066	verif-fake-sale-legit-032-1	1	416	next_action	要查明情境中物件本身的疑點，哪種方式最合適？	[{"key": "A", "text": "約現場查看實物並當場核對"}, {"key": "B", "text": "送獨立機構鑑定並取得報告"}, {"key": "C", "text": "向發證單位查詢憑證的真偽"}]	A	賣家同意在管理室看貨並讓你插電試機，現場就能核對型號與序號、確認功能。送獨立鑑定對一台幾百元的二手家電並不相稱，這類家電也沒有可查真偽的發證單位；現場一趟就問完了。	greed	1	{}	\N	published	\N	2026-09-22 11:30:17.612323+00	2026-09-22 11:30:19.306883+00
1067	verif-fake-sale-scam-031-1	1	395	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從原平台官方入口查帳戶狀態"}, {"key": "B", "text": "從主管機關官方名單查資格"}, {"key": "C", "text": "從商業登記查營業主體的資料"}]	A	對方要你離開平台、改到通訊軟體完成實名程序。平台的實名規則與帳戶狀態，只有從原平台官方入口登入才看得到。主管機關名單與商業登記查的都是機構，回答不了「這個平台真的要求我這樣做嗎」。	social_proof	1	{}	\N	published	\N	2026-09-22 11:30:17.679852+00	2026-09-22 11:30:19.306883+00
1068	verif-fake-sale-scam-024-1	1	358	next_action	要查明情境中物件本身的疑點，哪種方式最合適？	[{"key": "A", "text": "約現場查看實物並當場核對"}, {"key": "B", "text": "向發證單位查詢憑證的真偽"}, {"key": "C", "text": "送獨立機構鑑定並取得報告"}]	C	問的是這雙鞋的真偽。對方只肯宅配、不願面交,現場查看這條路被堵死;購買證明只拍到一角,拿去問原廠也只是驗那張紙。剩下的只有把實物送進獨立鑑定——而他願不願意讓鞋先進鑑定,本身就是答案。另外要講清楚:低於行情三成、限時五分鐘、又指定匯到「家人的帳戶」,這筆交易本來就不該繼續。	social_proof	2	{}	\N	published	\N	2026-09-22 11:30:17.749671+00	2026-09-22 11:30:19.306883+00
1069	verif-fake-sale-legit-034-1	1	418	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "僅取得聯絡者提供的交易相關資訊"}, {"key": "B", "text": "已自行核對平台後台的訂單付款狀態"}, {"key": "C", "text": "已向發卡機構核對這筆交易授權紀錄"}]	B	自己打開平台後台已找到同一訂單與已付款狀態，支持的是平台內這筆付款紀錄，還不是貨款已撥入自己的銀行。聯絡者提及交易資訊只描述郵件或對話；發卡機構的授權紀錄則需向銀行查得，本情境沒有這項查詢。	time_pressure	3	{}	\N	published	\N	2026-09-22 11:30:17.814895+00	2026-09-22 11:30:19.306883+00
1070	verif-fake-sale-scam-021-1	1	355	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "僅取得聯絡者提供的交易相關資訊"}, {"key": "B", "text": "已自行核對平台後台的訂單付款狀態"}, {"key": "C", "text": "已向發卡機構核對這筆交易授權紀錄"}]	A	目前有的是買家提供的付款截圖與金流人員的說法，因此只能確認對方提出了交易相關資訊。平台後台反而沒有訂單，不能支持平台已留有付款狀態；也沒有獨立向發卡機構查到授權。後兩項各需平台紀錄或銀行查詢，截圖本身不能替代。	social_proof	3	{}	\N	published	\N	2026-09-22 11:30:17.895872+00	2026-09-22 11:30:19.306883+00
1071	verif-investment-legit-033-1	1	413	next_action	要查明情境中物件本身的疑點，哪種方式最合適？	[{"key": "A", "text": "約現場查看實物並當場核對"}, {"key": "B", "text": "送獨立機構鑑定並取得報告"}, {"key": "C", "text": "向發證單位查詢憑證的真偽"}]	C	這枚金幣有證書與序號，向出具證書的鑑定機構查序號，才對得出手上這枚是不是證書上那一枚。預展現場看得到保存狀況但認不出真偽，重新送鑑定則是還沒必要的重複動作。	greed	3	{}	\N	published	\N	2026-09-22 11:30:17.966667+00	2026-09-22 11:30:19.306883+00
1072	verif-investment-legit-021-1	1	371	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "向往來機構行員或官方客服確認"}, {"key": "B", "text": "請律師逐條核對書面契約條款"}, {"key": "C", "text": "從官方應用程式功能頁查款項"}]	C	要核對的是這次申購何時截止、怎麼預扣，這些都在自己券商帳戶的申購功能裡。客服問得到一般規則但不是你這筆，新股申購也沒有需要律師審閱的私人契約。	time_pressure	2	{}	\N	published	\N	2026-09-22 11:30:18.034573+00	2026-09-22 11:30:19.306883+00
1073	verif-investment-scam-032-1	1	392	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從主管機關官方名單查資格"}, {"key": "B", "text": "從原平台官方入口查帳戶狀態"}, {"key": "C", "text": "從商業登記查營業主體的資料"}]	B	訊息要你去一個新網站處理資金，但你的帳戶在原本的交易所。直接從原平台官方入口登入，看得到帳戶真正的狀態與有沒有這筆審核。主管機關名單查的是機構資格，商業登記查的是公司；兩者都不會告訴你自己的帳戶現在怎麼了。	trust_building	2	{}	\N	published	\N	2026-09-22 11:30:18.11478+00	2026-09-22 11:30:19.306883+00
1074	verif-investment-scam-031-1	1	391	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從主管機關官方名單查資格"}, {"key": "B", "text": "從商業登記查營業主體的資料"}, {"key": "C", "text": "從原平台官方入口查帳戶狀態"}]	A	收費提供「即時帶進出」就是代客操作，該查的是這個人與機構有沒有投顧資格。商業登記只看得到公司存不存在，原平台入口在這裡根本沒有平台——錢是匯到個人帳戶。	greed	1	{}	\N	published	\N	2026-09-22 11:30:18.188536+00	2026-09-22 11:30:19.306883+00
1075	verif-investment-legit-012-1	1	336	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "群組訊息列有他人參與的數量"}, {"key": "B", "text": "對方傳來的憑證列有方案內容"}, {"key": "C", "text": "手上文件列有金額與費用明細"}]	C	理專交付的文件上確實有過去的跌幅與逐項費用，這部分有直接依據。這裡沒有群組，也沒有誰傳憑證給你；文件能支持的就是歷史波動與成本，不能拿來保證未來。	greed	2	{}	\N	published	\N	2026-09-22 11:30:18.257015+00	2026-09-22 11:30:19.306883+00
1076	verif-investment-scam-034-1	1	394	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "手上文件列有金額與費用明細"}, {"key": "B", "text": "群組訊息列有他人參與的數量"}, {"key": "C", "text": "對方傳來的憑證列有方案內容"}]	B	能確認的只有群組裡出現了預訂數字這件事，不代表真的有人付過款。對方沒有提供保管契約或任何憑證，你手上也沒有列著金額與費用的文件。	social_proof	2	{}	\N	published	\N	2026-09-22 11:30:18.332514+00	2026-09-22 11:30:19.306883+00
1077	verif-romance-legit-023-1	1	385	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從服務自己的訂單頁核對條件"}, {"key": "B", "text": "從主管機關入口核對申報資料"}, {"key": "C", "text": "自行查公開電話向業者確認"}]	C	訂金規則與取消期限要向餐廳本身確認,而且電話要自己查——敘事裡她沒有加對方給的店長帳號,而是自行搜尋登記電話,那正是這題的重點。訂位系統頁面呈現的是系統端條件,主管機關也不管個別餐廳的取消政策。	time_pressure	3	{}	\N	published	\N	2026-09-22 11:30:18.410099+00	2026-09-22 11:30:19.306883+00
1078	verif-romance-legit-033-1	1	425	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "請律師逐條核對書面契約條款"}, {"key": "B", "text": "向往來機構行員或官方客服確認"}, {"key": "C", "text": "從官方應用程式功能頁查款項"}]	A	現在要處理的是還沒簽的借款契約，利息、還款日與雙方權利得由律師逐條看過。銀行客服不審閱私人借貸條款，帳戶功能頁在款項還沒進來之前也看不到東西。	trust_building	1	{}	\N	published	\N	2026-09-22 11:30:18.48815+00	2026-09-22 11:30:19.306883+00
1079	verif-romance-scam-024-1	1	366	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "掛斷後自行改撥卡片背面客服"}, {"key": "B", "text": "從原本就在使用的程式查案件"}, {"key": "C", "text": "自行查機構總機再轉承辦窗口"}]	C	款項被說成手術押金，通知卻被裁掉抬頭。要確認這張單子是不是真的，只能自己查到院所總機、再轉收費窗口問正式繳費管道。卡背客服處理的是自己的卡片，醫療院所也沒有你能登入的既有程式。	time_pressure	2	{}	\N	published	\N	2026-09-22 11:30:18.557426+00	2026-09-22 11:30:19.306883+00
1080	verif-romance-scam-033-1	1	405	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "請律師逐條核對書面契約條款"}, {"key": "B", "text": "向往來機構行員或官方客服確認"}, {"key": "C", "text": "從官方應用程式功能頁查款項"}]	B	收款不需要交出提款卡或密碼，這件事沒有例外。打給自己往來銀行的官方客服，是為了把這條規則確認清楚，不是去問寄卡流程。這裡沒有書面契約要律師看，帳戶功能頁也不會出現「先寄卡才能收款」這種選項。	trust_building	1	{}	\N	published	\N	2026-09-22 11:30:18.630166+00	2026-09-22 11:30:19.306883+00
1081	verif-romance-legit-024-1	1	386	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "機構當場開立的收據載有姓名"}, {"key": "B", "text": "對方傳來的照片可看到我姓氏"}, {"key": "C", "text": "現場出示的證件與文件相符"}]	A	當場看到的是院內窗口開出病人名下的收據，這件事有直接依據。沒有人傳照片給你，對方也沒有出示過任何證件；收據能支持的就是這筆院內收費留下了紀錄。	authority	2	{}	\N	published	\N	2026-09-22 11:30:18.694506+00	2026-09-22 11:30:19.306883+00
1082	verif-romance-scam-021-1	1	363	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "機構當場開立的收據載有姓名"}, {"key": "B", "text": "對方傳來的照片可看到我姓氏"}, {"key": "C", "text": "現場出示的證件與文件相符"}]	B	眼前只有一張包裹照片，能確認的就是標籤上出現自己的姓氏。沒有任何機構開立的收據，對方也從沒出示過證件；物流有沒有收件全是訊息裡的說法。	trust_building	2	{}	\N	published	\N	2026-09-22 11:30:18.765159+00	2026-09-22 11:30:19.306883+00
1083	verif-shopping-legit-031-1	1	419	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從主管機關入口核對申報資料"}, {"key": "B", "text": "從服務自己的訂單頁核對條件"}, {"key": "C", "text": "自行查公開電話向業者確認"}]	A	包裹的申報品名與稅額算得對不對，是報關主管機關的資料。購物平台的訂單頁只看得到商品多少錢，打電話給業者也問不到這筆運單的申報內容。	time_pressure	1	{}	\N	published	\N	2026-09-22 11:30:18.839688+00	2026-09-22 11:30:19.306883+00
1084	verif-shopping-legit-023-1	1	381	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "自行查公開電話向業者確認"}, {"key": "B", "text": "從主管機關入口核對申報資料"}, {"key": "C", "text": "從服務自己的訂單頁核對條件"}]	C	要決定的是取消會不會立刻生效、下次何時扣款，這寫在服務自己的訂閱頁。打電話問客服繞得更遠，主管機關不處理個別訂閱方案。	time_pressure	3	{}	\N	published	\N	2026-09-22 11:30:18.918007+00	2026-09-22 11:30:19.306883+00
1085	verif-shopping-scam-003-v2-1	1	325	next_action	要查明情境中物件本身的疑點，哪種方式最合適？	[{"key": "A", "text": "送獨立機構鑑定並取得報告"}, {"key": "B", "text": "向發證單位查詢憑證的真偽"}, {"key": "C", "text": "約現場查看實物並當場核對"}]	C	房子你一次都還沒看過，聯絡的人又自稱代理人。到現場看屋並當場核對權狀與身分，才同時確認得了房子存在、以及這個人有沒有權利出租。獨立鑑定不處理不動產，謄本上的發證資料也對不上線上這個帳號。	social_proof	2	{}	\N	published	\N	2026-09-22 11:30:18.987807+00	2026-09-22 11:30:19.306883+00
1086	verif-shopping-scam-022-1	1	360	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從主管機關官方名單查資格"}, {"key": "B", "text": "從商業登記查營業主體的資料"}, {"key": "C", "text": "從原平台官方入口查帳戶狀態"}]	B	爭點是這個收錢的人到底是誰。商業登記查得到工作室存不存在、登記地址與負責人是誰。這種個人工作室不受金融主管機關名單管轄，對方也刻意不讓你從原本的商店頁結帳，沒有平台紀錄可查。	time_pressure	3	{}	\N	published	\N	2026-09-22 11:30:19.06728+00	2026-09-22 11:30:19.306883+00
1087	verif-shopping-legit-013-1	1	345	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "現場出示的證件與文件相符"}, {"key": "B", "text": "機構當場開立的收據載有姓名"}, {"key": "C", "text": "對方傳來的照片可看到我姓氏"}]	A	現場看到屋主的證件與權狀,敘事明說姓名地址相符,這點有直接依據。當場那張收據是屋主本人簽的,不是機構開立的;抵押設定要調謄本才看得到。兩者都不在這次看房已取得的資料裡。	trust_building	3	{}	\N	published	\N	2026-09-22 11:30:19.142747+00	2026-09-22 11:30:19.306883+00
1088	verif-shopping-scam-024-1	1	362	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "手上文件列有金額與費用明細"}, {"key": "B", "text": "對方傳來的憑證列有方案內容"}, {"key": "C", "text": "群組訊息列有他人參與的數量"}]	B	手上只有小編傳來的住宿券，能確認的就是券面上寫了什麼方案。那不是載明費用明細的正式文件，留言區的揪團也不是你所在群組的預訂紀錄；券的格式再完整也不等於訂房成立。	social_proof	2	{}	\N	published	\N	2026-09-22 11:30:19.218828+00	2026-09-22 11:30:19.306883+00
\.

SELECT pg_catalog.setval(
  'public.game_case_questions_id_seq',
  COALESCE((SELECT max(id) FROM public.game_case_questions), 1),
  EXISTS (SELECT 1 FROM public.game_case_questions)
);

--
-- PostgreSQL database dump
--

\restrict kMpbnQyMysJFuCN0MsMcIYagNt0xbeCa3v6wKaWjjAiBgSatpdX0ssWhVbbgOYj

-- Dumped from database version 17.10 (Debian 17.10-1.pgdg12+1)
-- Dumped by pg_dump version 17.10 (Debian 17.10-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

--
-- Name: game_case_questions game_case_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_case_questions
    ADD CONSTRAINT game_case_questions_pkey PRIMARY KEY (id);


--
-- Name: game_case_questions game_case_questions_question_key_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_case_questions
    ADD CONSTRAINT game_case_questions_question_key_version_key UNIQUE (question_key, version);


--
-- Name: game_case_questions_published_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX game_case_questions_published_idx ON public.game_case_questions USING btree (case_id) WHERE (status = 'published'::text);


--
-- Name: game_case_questions game_case_questions_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_case_questions
    ADD CONSTRAINT game_case_questions_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.game_cases(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict kMpbnQyMysJFuCN0MsMcIYagNt0xbeCa3v6wKaWjjAiBgSatpdX0ssWhVbbgOYj
