pip install requests beautifulsoup4
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def fetch_polb_stats():
    url = "https://polb.com/business/port-statistics/"

    # 1. 偽裝成真實瀏覽器的 Headers，避免被長堤港 WAF 防火牆阻擋
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://polb.com/",
    }

    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"❌ 存取失敗，HTTP 狀態碼：{response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        # 2. 定位 Container Trade 區域 (根據 POLB 網頁結構)
        # 尋找包含月份與 TEU 數據的表格或容器
        stats_section = soup.find("div", id="latest-statistics") or soup.find(
            "section", class_=re.compile("statistics", re.I)
        )

        if not stats_section:
            stats_section = soup  # 全頁搜尋備案

        # 範例解析邏輯：尋找最新月份與數字
        # (備註：若官網 HTML 結構有變，可調整下方 Selector)
        tables = stats_section.find_all("table")

        if tables:
            # 抓取第一張表 (最新數據)
            rows = tables[0].find_all("tr")

            # 抓取標題 (如 "July 2026")
            header_text = tables[0].text

            # 解析西元年與月份
            match_date = re.search(
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
                header_text,
                re.I,
            )

            if match_date:
                month_name = match_date.group(1)
                ad_year = int(match_date.group(2))

                # 西元年轉民國年：西元年 - 1911
                roc_year = ad_year - 1911

                # 轉換英文月份為數字月
                month_num = datetime.strptime(month_name, "%B").month

                # 從表格中尋找 TOTAL 與 YTD 數字
                total_teu = "尚無數據"
                ytd_teu = "尚無數據"

                for row in rows:
                    text = row.get_text()
                    if "TOTAL" in text.upper() and "YTD" not in text.upper():
                        nums = re.findall(r"[\d,]+", text)
                        if nums:
                            total_teu = nums[-1]
                    elif "YEAR TO DATE" in text.upper() or "YTD" in text.upper():
                        nums = re.findall(r"[\d,]+", text)
                        if nums:
                            ytd_teu = nums[-1]

                # 3. 嚴格依照要求格式輸出
                print("【長堤港 (POLB) 最新貨櫃數據報告】")
                print(f"- 統計月份：{roc_year}年 {month_num}月")
                print(f"- 當月總櫃量 (TOTAL T.E.U.)：{total_teu} TEU")
                print(f"- 當年累計總櫃量 (YTD Total)：{ytd_teu} TEU")
                return

        print("⚠️ 未能在網頁中找到預期格式的數據表格，請檢查網頁 DOM 結構。")

    except Exception as e:
        print(f"⚠️ 發生例外錯誤：{e}")


if __name__ == "__main__":
    fetch_polb_stats()
