import re
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def fetch_polb_stats():
    url = "https://polb.com/business/port-statistics/#latest-statistics"
    print("🚀 啟動無頭瀏覽器 (Playwright) 等待 JavaScript 畫面渲染完畢...")

    with sync_playwright() as p:
        # 啟動虛擬 Chrome 瀏覽器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 模擬真實使用者 Header
        page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            )
        })

        # 開啟網頁並等待所有網路資源載入完成
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)  # 強制等待 3 秒確保表格渲染

        content = page.content()
        browser.close()

    print("🔍 網頁 DOM 渲染完成，開始解析數據...")
    soup = BeautifulSoup(content, "html.parser")
    text_content = soup.get_text()

    # 搜尋月份與年份 (例: July 2026)
    match_date = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
        text_content,
        re.IGNORECASE,
    )

    if match_date:
        month_name = match_date.group(1)
        ad_year = int(match_date.group(2))

        # 西元年轉民國年 (西元年 - 1911)
        roc_year = ad_year - 1911
        month_num = datetime.strptime(month_name, "%B").month

        lines = [
            line.strip()
            for line in text_content.splitlines()
            if line.strip()
        ]

        total_teu = "尚無數據"
        ytd_teu = "尚無數據"

        for i, line in enumerate(lines):
            upper_line = line.upper()

            # 擷取當月總櫃量 (TOTAL)
            if (
                "TOTAL" in upper_line
                and "YTD" not in upper_line
                and "YEAR" not in upper_line
            ):
                nums = re.findall(r"[\d,]{5,10}", line)
                if not nums and i + 1 < len(lines):
                    nums = re.findall(r"[\d,]{5,10}", lines[i + 1])
                if nums:
                    total_teu = nums[0]

            # 擷取年度累計 (YTD / YEAR TO DATE)
            elif (
                "YEAR TO DATE" in upper_line
                or "CALENDAR YEAR" in upper_line
                or "YTD" in upper_line
            ):
                nums = re.findall(r"[\d,]{5,10}", line)
                if not nums and i + 1 < len(lines):
                    nums = re.findall(r"[\d,]{5,10}", lines[i + 1])
                if nums:
                    ytd_teu = nums[0]

        print("\n" + "=" * 40)
        print("【長堤港 (POLB) 最新貨櫃數據報告】")
        print(f"- 統計月份：{roc_year}年 {month_num}月")
        print(f"- 當月總櫃量 (TOTAL T.E.U.)：{total_teu} TEU")
        print(f"- 當年累計總櫃量 (YTD Total)：{ytd_teu} TEU")
        print("=" * 40 + "\n")

    else:
        print("⚠️ 仍無法找到對應的月份數據。")
        raise SystemExit(1)


if __name__ == "__main__":
    fetch_polb_stats()
