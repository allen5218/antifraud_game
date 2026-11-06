# 本機完整 Supabase 參考環境

來源：https://github.com/supabase/supabase

固定來源 commit：4466cc4e456aabd487699e0873b415f7a076478f

本目錄保留該版本的 Docker 設定與初始化檔案。啟動器另外產生私密環境設定、獨立專案名稱及持久資料卷，不使用範例密碼，不附帶正式站或既有玩家資料。上游授權見 LICENSE。

本機遊戲經 Supavisor 的 5432 埠連線 PostgreSQL。這是可重建的完整參考環境，不冒稱正式主機映像與資料的逐位元複製。
