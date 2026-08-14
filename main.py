import re
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests


def fetch_polb_stats():
    url = "https://polb.com/business/port-statistics/"
    print("🚀 開始連線長堤港官網 (使用 curl_cffi 擬真 Chrome TLS 指紋)...")

    try:
        # 使用 impersonate="chrome120" 100% 擬真真實 Chrome 的 TLS 指紋，避開 Cloudflare
        response = requests.get(
            url,
            impersonate="chrome120",
            timeout=30,
            headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://polb.com/",
            },
        )

        print(f"📡 狀態碼 (HTTP Status Code): {response.status_code}")

        if response.status_code != 200:
            print(f"❌ 連線失敗，HTTP 狀態碼: {response.status_code}")
            raise SystemExit(1)

        soup = BeautifulSoup(response.text, "html.parser")

        # 檢查是否遭到 Cloudflare Challenge 攔截
        if (
            "Just a moment..." in soup.text
            or "Enable JavaScript" in soup.text
        ):
            print("❌ 頁面被 Cloudflare 驗證頁面攔截。")
            raise SystemExit(1)

        print("🔍 成功取得網頁 DOM，開始解析統計數據...")

        tables = soup.find_all("table")
        print(f"📊 找到 {len(tables)} 個數據表格")

        full_text = soup.text

        # 抓取統計月份與年份 (例: July 2026)
        match_date = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
            full_text,
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

            # 遍歷表格解析當月 TOTAL 與 Calendar YTD TOTAL
            for table in tables:
                t_text = table.text
                rows = table.find_all("tr")

                # 當月數據表 (Container Trade in TEUs)
                if (
                    "Calendar Year to Date" not in t_text
                    and "Fiscal Year" not in t_text
                ):
                    for r in rows:
                        r_text = r.get_text().strip()
                        if (
                            "TOTAL" in r_text.upper()
                            and "YTD" not in r_text.upper()
                        ):
                            nums = re.findall(r"[\d,]{5,10}", r_text)
                            if nums:
                                total_teu = nums[0]

                # 年度累計數據表 (Calendar Year to Date)
                elif "Calendar Year to Date" in t_text:
                    for r in rows:
                        r_text = r.get_text().strip()
                        if "TOTAL" in r_text.upper():
                            nums = re.findall(r"[\d,]{5,10}", r_text)
                            if nums:
                                ytd_teu = nums[0]

            print("\n" + "=" * 40)
            print("【長堤港 (POLB) 最新貨櫃數據報告】")
            print(f"- 統計月份：{roc_year}年 {month_num}月")
            print(f"- 當月總櫃量 (TOTAL T.E.U.)：{total_teu} TEU")
            print(f"- 當年累計總櫃量 (YTD Total)：{ytd_teu} TEU")
            print("=" * 40 + "\n")

        else:
            print("⚠️ 未能在網頁中找到對應的月份標題。")
            raise SystemExit(1)

    except Exception as e:
        print(f"❌ 執行過程發生例外錯誤: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    fetch_polb_stats()
