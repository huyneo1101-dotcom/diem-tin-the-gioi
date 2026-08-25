#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG NGÀY ĐĂNG THẬT — mở chính bài ra đo ngày, không tin `date` do agent khai.

VÌ SAO CÓ FILE NÀY (đo 25/08/2026, 334 tin đã nạp trong index.html):
`add_news.py::check_date_window` chỉ so trường `date` trong JSON của lô với ngày batch và
với hôm nay. Cả hai vế đều là **con số do chính agent viết ra**, nên agent ghi `date` bằng
ngày quét là lô đi qua cổng, dù bài đăng từ bao giờ. Đo bằng cách mở lại 334 bài đã nạp và
đọc metadata ngày:
  - lô 15-24/08: 153 bài đọc được ngày, **03 bài** đăng ngoài khung (lệch 19 · 12 · 07 ngày);
  - lô 10-31/07: 164 bài đọc được ngày, **06 bài** ngoài khung, nặng nhất là bài South China
    Morning Post đăng **21/12/2024** mang `date` 29/07/2026, lệch 585 ngày.
Không phải bệnh của một phiên hay của một model: hai lô cách nhau một tháng cho cùng một tỷ
lệ (2,0% và 3,7%). Cổng cũ đứng đó mà không đo được gì vì nó không bao giờ mở bài ra.

CÁCH ĐO — CHỈ metadata có cấu trúc, TUYỆT ĐỐI không quét ngày trong văn bản tự do. Bài quân
sự nào cũng dày đặc ngày lịch sử, bắt ngày trôi nổi là gán bài 2026 thành 1944 (bẫy đã vấp
thật ở QuetThinkTank 29/07/2026, loại nhầm 46 bài). Bảng mẫu bên dưới bê nguyên từ
`/Users/Huy/Claude/QuetThinkTank/kiem_ngay_that.py::doc_ngay` — chép thay vì import vì máy
chạy của GitHub Actions KHÔNG có thư mục đó, mà cổng phải sống ở CI trước tiên.

HAI CẢNH KHÔNG ĐỌC ĐƯỢC NGÀY, XỬ KHÁC NHAU (siết 25/08/2026 theo chỉ thị Huy *"trang không
ghi ngày thì bỏ đi"*):
  - **Trang mở được nhưng không in ngày** → CHẶN. Không in ngày thì không có cách nào biết
    bài cũ hay mới, mà tin cũ lọt vào bản tin là hỏng đúng thứ người đọc nhìn thấy. Đo trước
    khi siết: 20/181 bài lô 15-24/08 và 32/200 bài lô 10-31/07 (11% và 16%).
  - **Trang không mở được** (bị chặn, mạng hỏng, bản tải về không có nổi thẻ `<title>`) →
    GIỮ, kèm dòng `⚠ NGÀY THẬT`. Chặn ở đây là để mạng của máy chạy quyết định bản tin có
    tin hay không, và nguồn nào trả 403 thì mất trắng. Đo 25/08: 8/181 bài (4,4%).
Ranh giới giữa hai cảnh đo bằng thẻ `<title>`: CNN và CNBC tải về 300 KB mà không có title
(trang dựng bằng JavaScript hoặc bị chặn), trong khi DVIDS/PACOM/war.gov có title đúng tên
bài — nhóm sau mới thật sự là "trang không in ngày".
"""
import datetime
import pathlib
import re
import sys
from concurrent.futures import ThreadPoolExecutor

THANG = {m: i + 1 for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June',
     'July', 'August', 'September', 'October', 'November', 'December'])}

SO_LUONG = 8      # số bài mở song song; lô một phiên thường 10-25 bài


def doc_ngay(h):
    """(ngày ISO | None, cách lấy được) từ HTML — CHỈ đọc metadata có cấu trúc."""
    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', h)
    if m:
        return m.group(1), 'datePublished'
    m = re.search(r'<meta[^>]+article:published_time[^>]+content="(\d{4}-\d{2}-\d{2})', h)
    if m:
        return m.group(1), 'meta'
    m = re.search(r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})', h)
    if m:
        return m.group(1), 'thẻ time'
    m = re.search(r'<meta[^>]+name="citation_publication_date"[^>]+content="[^"]*?'
                  r'(\d{1,2})/(\d{1,2})/(\d{4})', h)
    if m:
        thang, ngay, nam = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= thang <= 12 and 1 <= ngay <= 31:
            return f'{nam:04d}-{thang:02d}-{ngay:02d}', 'citation_publication_date'
    # DVIDS: bảng metadata cuối bài — <td>Date Posted:</td><td>08.22.2026 07:35</td>.
    # Thêm 25/08/2026: DVIDS là nguồn thông cáo quân sự dùng nhiều nhất cho chủ đề CNQS
    # (07 bài trong lô tháng 7, 02 bài lô tháng 8) và KHÔNG có JSON-LD, không og article,
    # không thẻ time — bốn mẫu trên trượt sạch. Neo vào NHÃN "Date Posted", không bắt ngày
    # trôi nổi: cùng trang đó còn "Date Taken" (ngày chụp ảnh, có thể trước hàng tuần).
    m = re.search(r'Date\s+Posted:\s*</td>\s*<td>\s*(\d{2})\.(\d{2})\.(\d{4})', h, re.I)
    if m:
        return f'{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}', 'DVIDS Date Posted'
    return None, 'không có metadata ngày'


def _kho_gia():
    """Kho HTML giả cho bộ test: biến môi trường `NGAYTHAT_KHO_GIA` trỏ tới file JSON
    {url: html}. Có seam này thì ca đo DÂY NỐI (chạy `add_news.py` thật) không cần mạng —
    không có nó, bộ test buộc phải gọi ra internet và sẽ đỏ mỗi lần CI mất mạng, tức là bộ
    test dạy người ta bỏ qua chính nó. Mọi lượt dùng đều IN RA, không có nhánh im lặng."""
    import json as _json
    import os as _os
    duong = _os.environ.get('NGAYTHAT_KHO_GIA')
    if not duong:
        return None
    print('  ⚠ NGÀY THẬT: đang đọc kho HTML GIẢ (%s) — chỉ dùng cho bộ test' % duong)
    return _json.loads(pathlib.Path(duong).read_text(encoding='utf-8'))


def _tai(url):
    """HTML của bài, đi bằng `harvest.curl` (curl → curl_cffi → thang congcu nếu có).

    Dùng lại đúng đường tải của harvest thay vì viết đường thứ hai: nguồn nào bị chặn thì
    hai đường sẽ lệch nhau, và cổng đo bằng đường yếu hơn sẽ câm đúng ở các nguồn khó.
    """
    kho = _kho_gia()
    if kho is not None:
        return kho.get(url, '')
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import harvest  # noqa: PLC0415
    raw = harvest.curl(url, timeout=20)
    return (raw or b"").decode('utf-8', 'ignore')[:300000]


def ngay_dang_that(url, tai=None):
    tai = tai or _tai
    try:
        h = tai(url)
    except Exception as e:                                    # noqa: BLE001
        return None, f'không lấy được ({type(e).__name__})'
    if not h:
        return None, 'không lấy được (rỗng)'
    ngay, cach = doc_ngay(h)
    if ngay:
        return ngay, cach
    # Phân biệt hai cảnh KHÁC HẲN NHAU mà nhìn từ ngoài giống nhau: trang thật sự không in
    # ngày, và trang mình không vào được. Từ 25/08/2026 cảnh thứ nhất bị CHẶN nên xếp nhầm
    # là loại oan tin. Dấu hiệu đo được: bản tải về của trang bị chặn / trang dựng bằng
    # JavaScript không có nổi thẻ <title> — đo thật trên CNN và CNBC ngày 25/08, tải về
    # 300 KB mà không có <title>, trong khi DVIDS/PACOM/war.gov bị xếp cùng nhóm lại có
    # <title> đúng tên bài, tức chúng mới là "trang không in ngày".
    if not re.search(r'<title[^>]*>\s*\S', h, re.I):
        return None, 'không lấy được (bản tải về không có tiêu đề, nghi bị chặn)'
    return None, cach


def kiem_lo(items, ref, tran_theo_cat, tai=None):
    """Đo cả lô. Trả (loi, canh_bao) — hai danh sách chuỗi.

    `items`: list dict có `ctx`, `url`, `date`, `category`.
    `ref`: ngày batch (datetime.date). `tran_theo_cat(category) -> số ngày được lùi`.
    Chặn khi ngày ĐĂNG THẬT cũ hơn `ref - trần`, hoặc ở tương lai so với `ref`.
    """
    loi, canh_bao = [], []
    if not items:
        return loi, canh_bao

    def lam(it):
        ngay, cach = ngay_dang_that(it['url'], tai)
        return it, ngay, cach

    with ThreadPoolExecutor(max_workers=SO_LUONG) as ex:
        ket_qua = list(ex.map(lam, items))

    for it, ngay, cach in ket_qua:
        if not ngay:
            # CHỈ THỊ HUY 25/08/2026, nguyên văn: "trang không ghi ngày thì bỏ đi". Trang
            # không in ngày ở đâu cả thì không có cách nào biết bài cũ hay mới, mà bản tin
            # nhận tin cũ là hỏng thứ Huy đọc. Đo trước khi siết: 20/181 bài lô tháng 8 và
            # 32/200 bài lô tháng 7 rơi vào nhánh này (11% và 16%) — nguồn hay gặp là DVIDS,
            # PACOM, war.gov, Xinhua; riêng DVIDS đã đọc được ngày sau khi thêm mẫu bảng
            # "Date Posted" cùng ngày, nên phần bị loại thật sẽ nhỏ hơn số đo trên.
            # ⚠ Trang KHÔNG MỞ ĐƯỢC thì vẫn giữ (nhánh dưới): chặn theo mạng là để mạng CI
            # kém quyết định bản tin có tin hay không, và nguồn nào bị 403 thì mất trắng.
            if cach.startswith('không lấy được'):
                canh_bao.append(f"⚠ NGÀY THẬT: {it['ctx']} — {cach}, tin vẫn nạp: {it['url']}")
            else:
                loi.append(
                    f"{it['ctx']}: trang KHÔNG in ngày đăng ở dạng đọc được ({cach}) nên không "
                    f"kiểm được bài cũ hay mới — bỏ tin này, thay bằng bài có ngày. "
                    f"URL: {it['url']}")
            continue
        try:
            that = datetime.date.fromisoformat(ngay)
        except ValueError:
            canh_bao.append(f"⚠ NGÀY THẬT: {it['ctx']} — metadata ngày hỏng ({ngay!r}), tin vẫn nạp")
            continue
        tran = tran_theo_cat(it.get('category', ''))
        gioi_han = ref - datetime.timedelta(days=tran)
        if that < gioi_han:
            loi.append(
                f"{it['ctx']}: bài đăng THẬT ngày {that} (đọc bằng {cach}) trong khi lô khai "
                f"date {it['date']} — cũ hơn {tran} ngày so với batch {ref}, tin quá cũ, bỏ hoặc "
                f"thay tin mới hơn. URL: {it['url']}")
        elif that > ref:
            canh_bao.append(
                f"⚠ NGÀY THẬT: {it['ctx']} — metadata ghi {that}, muộn hơn ngày batch {ref} "
                f"(múi giờ nguồn), tin vẫn nạp")
        elif ngay != it['date']:
            canh_bao.append(
                f"⚠ NGÀY THẬT: {it['ctx']} — lô khai {it['date']} nhưng bài đăng {that} "
                f"(vẫn trong khung, đã nạp nguyên trạng)")
    return loi, canh_bao
