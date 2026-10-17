--
-- PostgreSQL database dump
--

\restrict 8yMf1tWak60QoS1RjDppVlBf6PIfbIJsaUtNuH6hDjC4vtj0gRxMsQ4PfieU9a4

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

\unrestrict 8yMf1tWak60QoS1RjDppVlBf6PIfbIJsaUtNuH6hDjC4vtj0gRxMsQ4PfieU9a4

COPY public.game_case_questions (id, question_key, version, case_id, question_kind, question, options, correct_key, explanation, weakness_tag, difficulty, source_document_ids, provenance, status, review_notes, created_at, published_at) FROM stdin;
1123	verif-atm-legit-031-1	1	427	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "親自到機構的服務據點問"}, {"key": "B", "text": "從原本的程式查這件事"}, {"key": "C", "text": "自己打機構公開的電話問"}]	B	你已經在原本的健保程式裡看到同一筆補發案件，寄送地址就列在補換發頁，直接在那裡核對最快。看不懂的地方，也可以自己查健保署的電話問，或到服務據點問，只是要多花時間。	authority	1	{}	\N	published	\N	2026-09-22 11:58:26.062911+00	2026-09-22 11:58:28.595978+00
1124	verif-atm-legit-034-1	1	430	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從原本的程式查這件事"}, {"key": "B", "text": "到公開的登記名單查對方"}, {"key": "C", "text": "打165問這種說法"}]	A	這筆學費是你自己從這家銀行匯的，銀行程式的案件頁已經寫出缺的是學校的英文地址，還有補件期限，直接在程式裡核對、補上最快。需要有人幫忙時，也可以打銀行的客服或到分行問。簡訊只叫你登入自己的銀行看，沒有要你做別的事。	authority	3	{}	\N	published	\N	2026-09-22 11:58:26.133162+00	2026-09-22 11:58:28.595978+00
1125	verif-atm-scam-022-1	1	368	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從原本的程式查這件事"}, {"key": "B", "text": "親自到機構的服務據點問"}, {"key": "C", "text": "自己打機構公開的電話問"}]	C	電話那頭自稱銀行，正要你新增受款人、念驗證碼。先掛掉，自己打卡片背面那支銀行的電話問：有沒有這筆境外交易、剛才那通電話是不是他們打的。銀行程式查得到交易，但查不到剛才是誰打來；跑一趟分行也太慢。	authority	2	{}	\N	published	\N	2026-09-22 11:58:26.207744+00	2026-09-22 11:58:28.595978+00
1126	verif-atm-scam-023-1	1	369	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "自己打機構公開的電話問"}, {"key": "B", "text": "親自到機構的服務據點問"}, {"key": "C", "text": "從原本的程式查這件事"}]	B	你人就在分行，眼前的行員正在問有沒有人在電話裡指導你。電話那頭叫你說謊，這件事要直接照實告訴行員，由銀行幫你確認這筆該不該匯。另外打電話或開程式都比當面講慢，對方也還在線上催你。	authority	3	{}	\N	published	\N	2026-09-22 11:58:26.279121+00	2026-09-22 11:58:28.595978+00
1127	verif-atm-legit-021-1	1	387	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "銀行的紀錄列出這筆刷卡授權"}, {"key": "B", "text": "對方的訊息或來電列出交易內容"}, {"key": "C", "text": "平台後台列出這筆訂單已付款"}]	A	你自己打卡片背面的電話，銀行查到了這兩筆授權，這是銀行那邊的紀錄。打來的客服沒有講任何交易內容，只請你跟銀行確認；你這次也沒有去看購物平台的後台。	time_pressure	1	{}	\N	published	\N	2026-09-22 11:58:26.35164+00	2026-09-22 11:58:28.595978+00
1128	verif-atm-scam-001-v2-1	1	321	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "對方的訊息或來電列出交易內容"}, {"key": "B", "text": "平台後台列出這筆訂單已付款"}, {"key": "C", "text": "銀行的紀錄列出這筆刷卡授權"}]	A	對方報得出你的姓名和上個月買的東西，這只代表他手上有你的訂單資料，不代表他是客服。購物平台的後台和銀行的紀錄你都還沒看過，這兩項都還沒有根據。	trust_building	2	{}	\N	published	\N	2026-09-22 11:58:26.424762+00	2026-09-22 11:58:28.595978+00
1129	verif-fake-sale-legit-023-1	1	377	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "自行查公開電話向業者確認"}, {"key": "B", "text": "從服務自己的訂單頁核對條件"}, {"key": "C", "text": "從主管機關入口核對申報資料"}]	B	票已經轉進你原本的售票帳號，場次和座位在訂單頁上看得到，先在訂單頁核對最直接。有疑問也可以自己查業者的電話問；主管機關不管個別票券的轉讓紀錄。	social_proof	3	{}	\N	published	\N	2026-09-22 11:58:26.500177+00	2026-09-22 11:58:28.595978+00
1130	verif-fake-sale-legit-032-1	1	416	next_action	要查明情境中物件本身的疑點，哪種方式最合適？	[{"key": "A", "text": "約現場查看實物並當場核對"}, {"key": "B", "text": "送獨立機構鑑定並取得報告"}, {"key": "C", "text": "向發證單位查詢憑證的真偽"}]	A	賣家同意在管理室看貨並讓你插電試機，現場就能核對型號與序號、確認功能。送獨立鑑定對一台幾百元的二手家電並不相稱，這類家電也沒有可查真偽的發證單位；現場一趟就問完了。	greed	1	{}	\N	published	\N	2026-09-22 11:58:26.57238+00	2026-09-22 11:58:28.595978+00
1131	verif-fake-sale-scam-031-1	1	395	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "到公開的登記名單查對方"}, {"key": "B", "text": "從原本的程式查這件事"}, {"key": "C", "text": "打165問這種說法"}]	B	你已經在原本的平台訂單頁，裡面沒有這筆交易，也沒有什麼實名程序，平台的規定以自己帳戶裡看到的為準。165 能說明這種手法，但查不到你這筆訂單；登記名單查的是公司在不在，查不到這則通知是誰發的。	social_proof	1	{}	\N	published	\N	2026-09-22 11:58:26.65725+00	2026-09-22 11:58:28.595978+00
1132	verif-fake-sale-scam-024-1	1	358	next_action	要查明情境中物件本身的疑點，哪種方式最合適？	[{"key": "A", "text": "約現場查看實物並當場核對"}, {"key": "B", "text": "向發證單位查詢憑證的真偽"}, {"key": "C", "text": "送獨立機構鑑定並取得報告"}]	C	問的是這雙鞋的真偽。對方只肯宅配、不願面交，現場查看這條路被堵死；購買證明只拍到一角，拿去問原廠也只是驗那張紙。剩下的只有把實物送進獨立鑑定，而他願不願意讓鞋先送鑑定，本身就是答案。另外要講清楚：低於行情三成、限時五分鐘、又指定匯到「家人的帳戶」，這筆交易本來就不該繼續。	social_proof	2	{}	\N	published	\N	2026-09-22 11:58:26.729121+00	2026-09-22 11:58:28.595978+00
1133	verif-fake-sale-legit-034-1	1	418	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "對方的訊息或來電列出交易內容"}, {"key": "B", "text": "平台後台列出這筆訂單已付款"}, {"key": "C", "text": "銀行的紀錄列出這筆刷卡授權"}]	B	你自己打開平台後台，看到同一筆訂單已付款，這有直接根據；錢還在平台代管，還沒撥進你的帳戶。買家的訊息只問能不能今天寄，沒有列交易內容；這次也沒有查銀行的紀錄。	time_pressure	3	{}	\N	published	\N	2026-09-22 11:58:26.805162+00	2026-09-22 11:58:28.595978+00
1134	verif-fake-sale-scam-021-1	1	355	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "對方的訊息或來電列出交易內容"}, {"key": "B", "text": "平台後台列出這筆訂單已付款"}, {"key": "C", "text": "銀行的紀錄列出這筆刷卡授權"}]	A	買家傳來付款成功的截圖，金流人員也說錢被鎖住，這些都是對方說的。你自己看過賣家後台，裡面沒有這筆訂單，「後台已付款」並不成立；也沒有人查過銀行的紀錄。	social_proof	3	{}	\N	published	\N	2026-09-22 11:58:26.877317+00	2026-09-22 11:58:28.595978+00
1135	verif-investment-legit-033-1	1	413	next_action	要查明情境中物件本身的疑點，哪種方式最合適？	[{"key": "A", "text": "約現場查看實物並當場核對"}, {"key": "B", "text": "送獨立機構鑑定並取得報告"}, {"key": "C", "text": "向發證單位查詢憑證的真偽"}]	C	這枚金幣有證書與序號，向出具證書的鑑定機構查序號，才對得出手上這枚是不是證書上那一枚。預展現場看得到保存狀況但認不出真偽，重新送鑑定則是還沒必要的重複動作。	greed	3	{}	\N	published	\N	2026-09-22 11:58:26.945026+00	2026-09-22 11:58:28.595978+00
1136	verif-investment-legit-021-1	1	371	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "自己打機構的官方客服問"}, {"key": "B", "text": "請專業的人看過書面條件"}, {"key": "C", "text": "從原本的程式查這筆款項"}]	C	截止時間、承銷價和要從哪個帳戶預扣，申購頁上都寫了，你也已經在券商的程式裡，直接在申購頁核對最快。打客服也問得到，只是比較慢；這筆申購沒有需要請人看的書面契約。	time_pressure	2	{}	\N	published	\N	2026-09-22 11:58:27.017356+00	2026-09-22 11:58:28.595978+00
1137	verif-investment-scam-032-1	1	392	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "打165問這種說法"}, {"key": "B", "text": "到公開的登記名單查對方"}, {"key": "C", "text": "從原本的程式查這件事"}]	C	這家交易所你查過是真的，帳號也是你自己開的。打開交易所的程式，看帳戶裡有沒有這筆額度最快。登記名單你已經查過了，只能證明交易所是真的，不能證明帶領者說的是真的；165 能說明手法，但查不到你的帳戶。	trust_building	2	{}	\N	published	\N	2026-09-22 11:58:27.090349+00	2026-09-22 11:58:28.595978+00
1138	verif-investment-scam-031-1	1	391	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "打165問這種說法"}, {"key": "B", "text": "從原本的程式查這件事"}, {"key": "C", "text": "到公開的登記名單查對方"}]	C	這位講師要收錢帶你進出，得有投顧資格。貼文上有他的名字，到投信投顧公會的網站一查，就知道有沒有登記。165 能說明手法，但查不到這個人；你和他也沒有任何原本在用的程式可以查。	greed	1	{}	\N	published	\N	2026-09-22 11:58:27.171072+00	2026-09-22 11:58:28.595978+00
1139	verif-investment-legit-012-1	1	336	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "群組訊息列有他人參與的數量"}, {"key": "B", "text": "對方傳來的憑證列有方案內容"}, {"key": "C", "text": "手上文件列有費用與風險說明"}]	C	銀行的基金頁和月報列出這檔某一年大跌的走勢、手續費和經理費，還印著過去績效不代表未來，這些都有根據。群裡只說很多人在買，沒有列出人數；也沒有人傳憑證給你。這些資料能說明過去的波動和成本，不能保證以後。	greed	2	{}	\N	published	\N	2026-09-22 11:58:27.247306+00	2026-09-22 11:58:28.595978+00
1140	verif-investment-scam-034-1	1	394	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "手上文件列有費用與風險說明"}, {"key": "B", "text": "群組訊息列有他人參與的數量"}, {"key": "C", "text": "對方傳來的憑證列有方案內容"}]	B	能確認的只有群組裡出現了預訂數字這件事，不代表真的有人付過款。對方沒有提供保管契約或任何憑證，你手上也沒有列著費用與風險說明的文件。	social_proof	2	{}	\N	published	\N	2026-09-22 11:58:27.320671+00	2026-09-22 11:58:28.595978+00
1141	verif-romance-legit-023-1	1	385	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從服務自己的訂單頁核對條件"}, {"key": "B", "text": "從主管機關入口核對申報資料"}, {"key": "C", "text": "自行查公開電話向業者確認"}]	C	包廂的訂金和取消規定網站上沒寫，網站下面就有餐廳自己的電話，打去問最直接。訂位頁目前只看得到一般座位的規則；主管機關不管個別餐廳的訂位規定。	time_pressure	3	{}	\N	published	\N	2026-09-22 11:58:27.389401+00	2026-09-22 11:58:28.595978+00
1142	verif-romance-legit-033-1	1	425	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從原本的程式查這筆款項"}, {"key": "B", "text": "自己打機構的官方客服問"}, {"key": "C", "text": "請專業的人看過書面條件"}]	C	要確認的是還沒簽的借款契約，利息、還款日和雙方的權利，請律師逐條看過最可靠，她也這樣建議。錢還沒有匯，程式裡查不到東西；銀行客服也不審私人之間的借款契約。	trust_building	1	{}	\N	published	\N	2026-09-22 11:58:27.466481+00	2026-09-22 11:58:28.595978+00
1143	verif-romance-scam-024-1	1	366	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "到公開的登記名單查對方"}, {"key": "B", "text": "打165問這種說法"}, {"key": "C", "text": "從原本的程式查這件事"}]	B	繳費通知上的醫院名字被裁掉了，你連是哪家醫院都不知道，查不到它的登記，也沒有程式可以查。先打165問這種「把押金匯給醫院財務」的說法，錢先不要匯。知道是哪家醫院以後，才能自己查電話問正式的繳費方式。	time_pressure	2	{}	\N	published	\N	2026-09-22 11:58:27.537529+00	2026-09-22 11:58:28.595978+00
1144	verif-romance-scam-033-1	1	405	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "請專業的人看過書面條件"}, {"key": "B", "text": "自己打機構的官方客服問"}, {"key": "C", "text": "從原本的程式查這筆款項"}]	B	收款從來不需要把提款卡寄出去，也不用給密碼。卡片寄出前，自己打給往來銀行的客服問一聲，就能確認銀行沒有這種「測試收款」的程序。錢還沒進來，程式裡查不到東西；這件事也沒有契約可以請人看。	trust_building	1	{}	\N	published	\N	2026-09-22 11:58:27.618634+00	2026-09-22 11:58:28.595978+00
1145	verif-romance-legit-024-1	1	386	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "機構當場開立的收據載有姓名"}, {"key": "B", "text": "對方傳來的照片可看到我姓氏"}, {"key": "C", "text": "現場出示的證件與文件相符"}]	A	當場看到的是院內窗口開出病人名下的收據，這件事有直接依據。沒有人傳照片給你，對方也沒有出示過任何證件；收據能支持的就是這筆院內收費留下了紀錄。	authority	2	{}	\N	published	\N	2026-09-22 11:58:27.695526+00	2026-09-22 11:58:28.595978+00
1146	verif-romance-scam-021-1	1	363	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "機構當場開立的收據載有姓名"}, {"key": "B", "text": "對方傳來的照片可看到我姓氏"}, {"key": "C", "text": "現場出示的證件與文件相符"}]	B	眼前只有一張包裹照片，能確認的就是標籤上出現自己的姓氏。沒有任何機構開立的收據，對方也從沒出示過證件；物流有沒有收件全是訊息裡的說法。	trust_building	2	{}	\N	published	\N	2026-09-22 11:58:27.769044+00	2026-09-22 11:58:28.595978+00
1147	verif-shopping-legit-031-1	1	419	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "從主管機關入口核對申報資料"}, {"key": "B", "text": "從服務自己的訂單頁核對條件"}, {"key": "C", "text": "自行查公開電話向業者確認"}]	A	包裹的申報品名與稅額算得對不對，是報關主管機關的資料。購物平台的訂單頁只看得到商品多少錢，打電話給業者也問不到這筆運單的申報內容。	time_pressure	1	{}	\N	published	\N	2026-09-22 11:58:27.835992+00	2026-09-22 11:58:28.595978+00
1148	verif-shopping-legit-023-1	1	381	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "自行查公開電話向業者確認"}, {"key": "B", "text": "從主管機關入口核對申報資料"}, {"key": "C", "text": "從服務自己的訂單頁核對條件"}]	C	要決定的是取消會不會立刻生效、下次何時扣款，這寫在服務自己的訂閱頁。打電話問客服繞得更遠，主管機關不處理個別訂閱方案。	time_pressure	3	{}	\N	published	\N	2026-09-22 11:58:27.906302+00	2026-09-22 11:58:28.595978+00
1149	verif-shopping-scam-003-v2-1	1	325	next_action	要查明情境中物件本身的疑點，哪種方式最合適？	[{"key": "A", "text": "送獨立機構鑑定並取得報告"}, {"key": "B", "text": "向發證單位查詢憑證的真偽"}, {"key": "C", "text": "約現場查看實物並當場核對"}]	C	房子你一次都還沒看過，先約到現場看房，當場核對權狀和屋主的身分；對方自稱代理人，還要看屋主寫的授權書。鑑定報告和證書查詢，都不能證明這個帳號真的有權出租這間房。	social_proof	2	{}	\N	published	\N	2026-09-22 11:58:27.979748+00	2026-09-22 11:58:28.595978+00
1150	verif-shopping-scam-022-1	1	360	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "到公開的登記名單查對方"}, {"key": "B", "text": "從原本的程式查這件事"}, {"key": "C", "text": "打165問這種說法"}]	A	對方不給地址、只給私人帳戶，你也不是在原本的商店頁跟他買。先用貼文上的工作室名稱查商業登記，看有沒有這家店、登記在哪裡，查到以後再自己找電話或去店裡問。查到店家存在，也不代表跟你私訊的人就是這家店。	time_pressure	3	{}	\N	published	\N	2026-09-22 11:58:28.057931+00	2026-09-22 11:58:28.595978+00
1151	verif-shopping-legit-013-1	1	345	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "現場出示的證件與文件相符"}, {"key": "B", "text": "機構當場開立的收據載有姓名"}, {"key": "C", "text": "對方傳來的照片可看到我姓氏"}]	A	現場看過屋主的權狀和身分證，名字和地址都對得上，這有直接根據。屋主拿出的是他自己寫的訂金單，不是機構開的收據；這次也沒有人傳照片給你。	trust_building	3	{}	\N	published	\N	2026-09-22 11:58:28.130521+00	2026-09-22 11:58:28.595978+00
1152	verif-shopping-scam-024-1	1	362	evidence_scope	依目前手上的資料，哪一項描述成立？	[{"key": "A", "text": "手上文件列有費用與風險說明"}, {"key": "B", "text": "對方傳來的憑證列有方案內容"}, {"key": "C", "text": "群組訊息列有他人參與的數量"}]	B	手上只有小編傳來的住宿券，能確認的是券面寫了旅宿名稱、住兩晚和早餐，不能證明券是真的、房間已經訂好。你手上沒有列出費用和規定的正式文件，留言區的揪團也沒寫出人數。	social_proof	2	{}	\N	published	\N	2026-09-22 11:58:28.202982+00	2026-09-22 11:58:28.595978+00
1153	verif-atm-scam-033-1	1	409	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "打165查證這則訊息是不是詐騙"}, {"key": "B", "text": "向自己往來銀行的官方客服確認"}, {"key": "C", "text": "從主管機關官方名單查機構資格"}]	A	訊息裡的「基金會」沒有名稱、沒有官方網站，連自稱主管的人也在同一個群組裡，你手上沒有任何可以獨立找到的單位。而「先匯錢提高信用分才能領補助」這套說法，165 查得到它是不是正在流行的手法。你的往來銀行管不到別人的補助案，主管機關名單也查不到一個講不出名字的基金會。	authority	2	{}	\N	published	\N	2026-09-22 11:58:28.281456+00	2026-09-22 11:58:28.595978+00
1154	verif-romance-scam-001-v2-1	1	319	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "打165查證這則訊息是不是詐騙"}, {"key": "B", "text": "向自己往來銀行的官方客服確認"}, {"key": "C", "text": "從主管機關官方名單查機構資格"}]	A	對方是網路上認識的人，不肯視訊，收保證金的單位也查不到是誰。這種時候打165問最快，可以知道這套說法是不是常見的手法。自己的銀行能說明匯款的風險，但查不到這個人是誰；主管機關名單查的是金融機構，對不上一個網友。	trust_building	2	{}	\N	published	\N	2026-09-22 11:58:28.353519+00	2026-09-22 11:58:28.595978+00
1155	verif-atm-scam-024-1	1	370	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "打165查證這則訊息是不是詐騙"}, {"key": "B", "text": "向自己往來銀行的官方客服確認"}, {"key": "C", "text": "從主管機關官方名單查機構資格"}]	B	訊息說是你的銀行，銀行是找得到本人的：自己打銀行的官方客服，就能問到有沒有這筆被暫停的轉帳。165 能幫你判斷這種「驗證款」的說法，但查不到你這筆交易，號碼沒被檢舉也不代表安全；主管機關名單查的是機構有沒有立案。	time_pressure	2	{}	\N	published	\N	2026-09-22 11:58:28.428931+00	2026-09-22 11:58:28.595978+00
1156	verif-investment-scam-022-1	1	352	next_action	依這段情境，哪個管道最適合核對這件事？	[{"key": "A", "text": "打165查證這則訊息是不是詐騙"}, {"key": "B", "text": "向自己往來銀行的官方客服確認"}, {"key": "C", "text": "從主管機關官方名單查機構資格"}]	C	顧問自稱替多家金融機構規劃商品、投影片還放了證照，這些都是查得到真假的。銷售投資商品要有資格，主管機關的公開名單一查便知，比問「這是不是詐騙」更直接。165 適合對方身分查不出來的時候；往來銀行則管不到別人的商品。聊天室裡的對帳畫面與報名訊息，誰都能做一張。	social_proof	3	{}	\N	published	\N	2026-09-22 11:58:28.508196+00	2026-09-22 11:58:28.595978+00
\.

SELECT pg_catalog.setval(
  'public.game_case_questions_id_seq',
  COALESCE((SELECT max(id) FROM public.game_case_questions), 1),
  EXISTS (SELECT 1 FROM public.game_case_questions)
);

--
-- PostgreSQL database dump
--

\restrict 3NhMIJ5WOLv943wnnyt3V9COOIUVk6IFB3t2sOyb5d03hjmDfcYsOAgPHuH6cQS

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

\unrestrict 3NhMIJ5WOLv943wnnyt3V9COOIUVk6IFB3t2sOyb5d03hjmDfcYsOAgPHuH6cQS
