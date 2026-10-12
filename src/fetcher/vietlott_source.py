import logging
import httpx
import re
from datetime import datetime, date
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from src.fetcher.base import DataSource
from src.config.settings import LotteryType

logger = logging.getLogger(__name__)

class VietlottOfficialSource(DataSource):
    """
    Scraper cào kết quả Vietlott thực tế từ xskt.com.vn (hỗ trợ 100 kỳ quay liên tục)
    và dự phòng từ atrungroi.com.
    """

    @property
    def name(self) -> str:
        return "vietlott_official"

    def fetch_latest(self, lottery_type: LotteryType, limit: int = 100) -> List[Dict[str, Any]]:
        logger.info(f"Đang fetch {limit} kỳ quay mới nhất cho {lottery_type}...")
        is_power = (lottery_type == LotteryType.POWER_655)
        
        # 1. Thử lấy từ xskt.com.vn (có sẵn trang 100-ngay siêu tốc và ổn định)
        results = self._fetch_from_xskt(lottery_type, is_power, limit)
        if len(results) >= limit:
            logger.info(f"Lấy thành công {len(results)} kỳ từ xskt.com.vn cho {lottery_type}")
            return results[:limit]

        # 2. Nếu thiếu, bổ sung thêm từ atrungroi.com
        logger.info(f"Đang lấy thêm dữ liệu từ atrungroi.com (hiện có {len(results)} kỳ)...")
        atrungroi_results = self._fetch_from_atrungroi(lottery_type, is_power, limit)
        seen_draws = {r["draw_number"] for r in results}
        for r in atrungroi_results:
            if r["draw_number"] not in seen_draws:
                results.append(r)
                seen_draws.add(r["draw_number"])

        results.sort(key=lambda x: x["draw_number"], reverse=True)
        final_list = results[:limit]
        logger.info(f"Hoàn thành fetch: Tổng cộng {len(final_list)} kỳ quay cho {lottery_type}")
        return final_list

    def _fetch_from_xskt(self, lottery_type: LotteryType, is_power: bool, limit: int) -> List[Dict[str, Any]]:
        """Lấy dữ liệu từ xskt.com.vn (trang 100-ngay hoặc 90-ngay)"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        slug = "xspower" if is_power else "xsmega645"
        # Thử 100-ngay trước, nếu limit > 90
        urls = [
            f"https://xskt.com.vn/{slug}/100-ngay",
            f"https://xskt.com.vn/{slug}/90-ngay",
            f"https://xskt.com.vn/{slug}"
        ]

        results = []
        seen_draws = set()
        current_year = date.today().year
        last_month = 12

        try:
            with httpx.Client(headers=headers, timeout=15.0, follow_redirects=True) as client:
                for url in urls:
                    if len(results) >= limit:
                        break
                    try:
                        res = client.get(url)
                        if res.status_code != 200:
                            continue
                        
                        soup = BeautifulSoup(res.text, "html.parser")
                        boxes = soup.find_all("div", class_="box-ketqua")
                        for b in boxes:
                            parsed = self._parse_xskt_box(b, lottery_type, is_power, current_year, last_month)
                            if parsed:
                                draw_no = parsed["draw_number"]
                                if draw_no not in seen_draws:
                                    seen_draws.add(draw_no)
                                    results.append(parsed)
                                    # Cập nhật năm khi lùi tháng
                                    if parsed["draw_date"].month > last_month and last_month <= 2 and parsed["draw_date"].month >= 11:
                                        current_year -= 1
                                    last_month = parsed["draw_date"].month
                                    if len(results) >= limit:
                                        break
                    except Exception as e_url:
                        logger.warning(f"Lỗi khi tải URL {url}: {e_url}")
        except Exception as e:
            logger.error(f"Lỗi client xskt: {e}")

        return results

    def _parse_xskt_box(self, b, lottery_type: LotteryType, is_power: bool, current_year: int, last_month: int) -> Optional[Dict[str, Any]]:
        try:
            # 1. Mã kỳ mở thưởng
            kmt = b.find("td", class_="kmt")
            if not kmt:
                return None
            m_draw = re.search(r"#(\d+)", kmt.get_text())
            if not m_draw:
                return None
            draw_no = int(m_draw.group(1))

            # 2. Ngày mở thưởng
            draw_date = None
            # Ưu tiên lấy từ link ngày: ví dụ /xspower/ngay-3-10-2026
            a_href = b.find("a", href=re.compile(r"ngay-(\d+)-(\d+)-(\d{4})"))
            if a_href:
                m_date = re.search(r"ngay-(\d+)-(\d+)-(\d{4})", a_href["href"])
                if m_date:
                    d, m, y = int(m_date.group(1)), int(m_date.group(2)), int(m_date.group(3))
                    draw_date = date(y, m, d)

            if not draw_date:
                # Tìm trong thẻ a id="MGngay04-10" hoặc id="MPngay03-10"
                a_id = b.find("a", id=re.compile(r"ngay(\d{2})-(\d{2})"))
                if a_id:
                    m_id = re.search(r"ngay(\d{2})-(\d{2})", a_id["id"])
                    if m_id:
                        d, m = int(m_id.group(1)), int(m_id.group(2))
                        y = current_year
                        if m > last_month and last_month <= 2 and m >= 11:
                            y = current_year - 1
                        draw_date = date(y, m, d)

            if not draw_date:
                # Tìm trong h2 text
                h2 = b.find("h2")
                if h2:
                    m_h2 = re.search(r"ng\xe0y\s*(\d{1,2})/(\d{1,2})", h2.get_text())
                    if m_h2:
                        d, m = int(m_h2.group(1)), int(m_h2.group(2))
                        y = current_year
                        if m > last_month and last_month <= 2 and m >= 11:
                            y = current_year - 1
                        draw_date = date(y, m, d)

            if not draw_date:
                return None

            # 3. Quả bóng số
            res_td = b.find("td", class_=re.compile(r"result|mega|power", re.I))
            if not res_td:
                return None
            nums = [int(x) for x in res_td.get_text(strip=True).split() if x.isdigit()]
            max_val = 55 if is_power else 45
            if len(nums) < 6:
                return None
            main_nums = [n for n in nums[:6] if 1 <= n <= max_val]
            if len(set(main_nums)) != 6:
                return None

            # 4. Jackpot 2 (nếu là Power 6/55)
            jp2 = None
            if is_power:
                jp2_row = b.find("tr", class_="jp2")
                if jp2_row:
                    tds = jp2_row.find_all("td")
                    if len(tds) >= 2:
                        val_txt = tds[1].get_text(strip=True)
                        if val_txt.isdigit():
                            val = int(val_txt)
                            if 1 <= val <= 55:
                                jp2 = val

            return {
                "lottery_type": lottery_type,
                "draw_number": draw_no,
                "draw_date": draw_date,
                "numbers": sorted(main_nums),
                "jackpot_2": jp2
            }
        except Exception as e:
            logger.debug(f"Lỗi parse box xskt: {e}")
            return None

    def _fetch_from_atrungroi(self, lottery_type: LotteryType, is_power: bool, limit: int) -> List[Dict[str, Any]]:
        """Dự phòng cào từ atrungroi.com"""
        base_url = (
            "https://atrungroi.com/xo-so-power-6-55-vietlott.html"
            if is_power
            else "https://atrungroi.com/xstc-xo-so-tu-chon-mega-645-vietlott.html"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        results = []
        seen_draws = set()
        try:
            with httpx.Client(headers=headers, timeout=12.0, follow_redirects=True) as client:
                res = client.get(base_url)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    items = soup.find_all("div", class_="kqxs")
                    for it in items:
                        parsed = self._parse_atrungroi_item(it, lottery_type, is_power)
                        if parsed and parsed["draw_number"] not in seen_draws:
                            seen_draws.add(parsed["draw_number"])
                            results.append(parsed)
        except Exception as e:
            logger.warning(f"Lỗi cào atrungroi: {e}")

        return results

    def _parse_atrungroi_item(self, item, lottery_type: LotteryType, is_power: bool) -> Optional[Dict[str, Any]]:
        try:
            text = item.get_text(" ", strip=True)
            d_match = re.search(r"#(\d+)", text)
            date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
            if not d_match or not date_match:
                return None

            draw_num = int(d_match.group(1))
            day, month, year = date_match.groups()
            draw_date = date(int(year), int(month), int(day))

            ball_spans = item.find_all("span", class_=re.compile(r"ball", re.I))
            nums = [int(b.get_text(strip=True)) for b in ball_spans if b.get_text(strip=True).isdigit()]

            max_val = 55 if is_power else 45
            if len(nums) >= 6:
                main_nums = [n for n in nums[:6] if 1 <= n <= max_val]
                if len(set(main_nums)) == 6:
                    jp2 = nums[6] if is_power and len(nums) > 6 and 1 <= nums[6] <= max_val else None
                    return {
                        "lottery_type": lottery_type,
                        "draw_number": draw_num,
                        "draw_date": draw_date,
                        "numbers": sorted(main_nums),
                        "jackpot_2": jp2
                    }
        except Exception as ex:
            logger.debug(f"Lỗi parse atrungroi item: {ex}")
        return None

    def fetch_by_range(self, lottery_type: LotteryType, start_draw: int, end_draw: int) -> List[Dict[str, Any]]:
        return []
