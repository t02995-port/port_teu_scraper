import re
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup


def fetch_polb_stats():
    url = "https://polb.com/business/port-statistics/"

    print("🚀 開始連線長堤港官網 (使用 Cloudscraper 模擬真實瀏覽器)...")

    # 建立 cloudscraper 實例以突破 Cloudflare / WAF 防護
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )

    try:
        response = scraper.get(url, timeout=20)
        print(f"📡 狀態碼 (HTTP Status Code): {response.status_code}")

        if response.status_code != 200:
            print("❌ 連線被阻擋或伺服器無回應。")
            raise SystemExit(1)

        soup = BeautifulSoup(response.text, "html.parser")

        # 尋找包含數據的表格
        tables = soup.find_all("table")
        print(f"🔍 成功抓取頁面，共找到 {len(tables)} 個表格")

        if not tables:
            print("⚠️ 未找到任何表格，可能是頁面結構有所調整。")
            raise SystemExit(1)

        # 尋找目標表格 (預設取第一個或包含 TOTAL 的表格)
        target_table = None
        for t in tables:
            if "TOTAL" in t.text.upper() or "CONTAINER" in t.text.upper():
                target_table = t
                break

        if not target_table:
            target_table = tables[0]

        table_text = target_table.text
        rows = target_table.find_all("tr")

        # 解析統計月份與年份 (英文月份 + 4位數年份)
        match_date = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
            table_text,
            re.IGNORECASE,
        )

        if match_date:
            month_name = match_date.group(1)
            ad_year = int(match_date.group(2))

            # 西元年轉民國年 (西元年 - 1911)
            roc_year = ad_year - 1911
            month_num = datetime.strptime(month_name, "%B").month

            total_teu = "尚無數據"
            ytd_teu = "尚無數據"

            for row in rows:
                text = row.get_text().strip()
                # 擷取當月總櫃量
                if (
                    "TOTAL" in text.upper()
                    and "YTD" not in text.upper()
                    and "YEAR" not in text.upper()
                ):
                    nums = re.findall(r"[\d,]+", text)
                    if nums:
                        total_teu = nums[-1]
                # 擷取年度累計
                elif (
                    "YEAR TO DATE" in text.upper()
                    or "CALENDAR YEAR" in text.upper()
                    or "YTD" in text.upper()
                ):
                    nums = re.findall(r"[\d,]+", text)
                    if nums:
                        ytd_teu = nums[-1]

            print("\n" + "=" * 40)
            print("【長堤港 (POLB) 最新貨櫃數據報告】")
            print(f"- 統計月份：{roc_year}年 {month_num}月")
            print(f"- 當月總櫃量 (TOTAL T.E.U.)：{total_teu} TEU")
            print(f"- 當年累計總櫃量 (YTD Total)：{ytd_teu} TEU")
            print("=" * 40 + "\n")

        else:
            print("⚠️ 無法從表格標題辨識月份資訊。")
            raise SystemExit(1)

    except Exception as e:
        print(f"❌ 執行過程發生例外錯誤: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    fetch_polb_stats()
