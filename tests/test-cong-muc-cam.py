#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST HỒI QUY: CỔNG «MỤC CÂM» — sàn tin mỗi mục + feed sống mà câm (dựng 05/09/2026).

⚠ VÌ SAO CÓ FILE NÀY. Sáng 05/09/2026 Huy hỏi *"sao điểm tin sáng nay không có tin của Anh
vậy?"*. Hai lỗi câm trong `harvest.py` đã sống từ 01/09 tới 05/09, qua ít nhất 08 phiên quét,
mà **không cổng nào kêu** — canary hỏi bản tin có tới nơi không, `rss_check.py` hỏi feed còn
item không, `khoe.py` hỏi routine có chạy không. Cả ba trả lời đúng và đều "đạt". Không cổng
nào hỏi *mục này đáng lẽ có tin, sao rỗng*. Người phát hiện là Huy, không phải máy.

Cùng ngày Huy chốt sàn, nguyên văn: *"tối thiểu mỗi mục phải quét cho tao 2 tin"*, *"nhiều
tin thì càng tốt"*. `scripts/soi_muc_cam.py` là phép đo, file này là cổng nghiệm thu nó.

⛔ MỌI CA GẮN NHÃN «PHẢI CHẶN» LÀ CA DỰNG ĐÚNG ĐIỀU KIỆN XẤU RỒI KHẲNG ĐỊNH MÃ THẬT SỰ BẮT
ĐƯỢC. Bộ test chỉ có ca "phải cho qua" là chưa test.

Chạy:
    python3 tests/test-cong-muc-cam.py
    python3 tests/test-cong-muc-cam.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

`--tu-kiem` dựng bản sao repo ĐÃ GỠ ĐÚNG DÒNG VÁ rồi chạy lại chính bộ ca này; mỗi bản hỏng
phải làm ĐỎ đúng những ca đã khai. Xanh trên cả bản đúng lẫn bản hỏng là test vô dụng.

⚠ Bản hỏng KHÔNG ghi đè file thật — nhiều phiên Claude chạy song song trên cùng repo
(CLAUDE.md toàn cục mục 9b), ghi đè là xoá việc của phiên khác.

Cả bộ ca chạy OFFLINE: feed giả bơm qua tham số `tai` của `soi_feed`, bảng nguồn giả bơm qua
`khai`, kho tin giả bơm qua `data`. Không lượt mạng nào, nên test không phụ thuộc hôm nay feed
còn bài hay không.
"""
import hashlib
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

# Seam để tự kiểm: trỏ sang một BẢN SAO repo khác.
REPO = pathlib.Path(os.environ.get("MUCCAM_REPO",
                                   pathlib.Path(__file__).resolve().parent.parent))


def _nap(ten, duong):
    spec = importlib.util.spec_from_file_location(ten, duong)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


os.environ["SOIMUC_REPO"] = str(REPO)
sys.path.insert(0, str(REPO / "scripts"))
S = _nap("soi_muc_cam_test", REPO / "scripts" / "soi_muc_cam.py")
MD = _nap("make_docx_test", REPO / ".github" / "scripts" / "make_docx.py")

# ── kho tin giả: mỗi tin rơi vào ĐÚNG một mục của make_docx ───────────────────
def _tin(url, **kw):
    d = {"sourceUrl": url, "title": "", "summary": "", "significance": "",
         "region": "", "category": "Chính trị", "date": "2026-09-05",
         "_addedDate": "2026-09-05", "sourceName": "X"}
    d.update(kw)
    return d


NOI_BO = [_tin(f"https://a.test/nb{i}", title=f"Hạ viện bỏ phiếu dự luật ngân sách số {i}")
          for i in range(1, 4)]
DOI_NGOAI = [_tin(f"https://a.test/dn{i}", category="Ngoại giao",
                  title=f"Ngoại trưởng Mỹ điện đàm lần {i}") for i in range(1, 4)]
KHCN = [_tin(f"https://a.test/kt{i}", category="Công nghệ quân sự",
             title=f"Lầu Năm Góc trao hợp đồng tên lửa lô {i}") for i in range(1, 4)]
UC = [_tin(f"https://b.test/uc{i}", title=f"Úc điều tàu tới Darwin đợt {i}") for i in range(1, 4)]
ANH = [_tin(f"https://b.test/anh{i}",
            title=f"Hải quân Hoàng gia Anh triển khai HMS Tamar tới Ream lượt {i}")
       for i in range(1, 4)]
BIEN_DONG = [_tin(f"https://b.test/bd{i}",
                  title=f"Tàu hải cảnh Trung Quốc ở Bãi Cỏ Mây, Biển Đông ngày {i}")
             for i in range(1, 4)]

DATA_GIA = {"usNews": NOI_BO + DOI_NGOAI + KHCN,
            "worldNews": UC + ANH + BIEN_DONG,
            "exercises": [], "dipEvents": []}


def _urls(*nhom):
    return [it["sourceUrl"] for lst in nhom for it in lst]


def _dem(*nhom):
    return S.dem_muc(_urls(*nhom), data=DATA_GIA)


def _neo(tm):
    """Chuỗi nhận dạng CHẶT của một tiểu mục trong dòng cảnh báo.

    ⚠ Không dùng chuỗi trần `"Anh"` / `"Biển Đông"`: tên mục gộp là *"Địa bàn Australia và
    Anh, Biển Đông"*, tức nó CHỨA SẴN cả hai chuỗi ấy — phép khẳng định trần đậu kể cả khi
    cổng kêu nhầm tiểu mục. Chính bản hỏng "hạ sàn về 1 tin" của `--tu-kiem` bắt được chỗ
    này lúc dựng: ca 05 lẽ ra phải đỏ mà vẫn xanh.
    """
    return f"\u203a {tm}:"


def _do(dem):
    """{tên mục rút gọn: số tin} — rút gọn để ca test đọc được."""
    return {t.split("› ")[-1]: n for t, n in dem}


# ── feed giả cho lớp NGUỒN ────────────────────────────────────────────────────
def _xml(items, co_ngay=True, tieu_de="Bản tin nội bộ số {i}"):
    ng = "<pubDate>Fri, 04 Sep 2026 19:28:18 +0000</pubDate>" if co_ngay else ""
    it = "".join(f"<item><title>{tieu_de.format(i=i)}</title>"
                 f"<link>https://f.test/{i}</link>{ng}</item>" for i in range(items))
    return f"<rss version='2.0'><channel>{it}</channel></rss>".encode()


def _tai(bang):
    def f(url):
        if url not in bang:
            raise RuntimeError("không tải được")
        return bang[url]
    return f


U_MU = "https://mu.test/rss"          # sống, mọi item KHÔNG có ngày
U_THUONG = "https://thuong.test/rss"  # sống, có ngày
U_HONG = "https://hong.test/rss"      # tải hỏng
FEEDS = [("Mù ngày", U_MU), ("Bình thường", U_THUONG), ("Tải hỏng", U_HONG)]
# Tiêu đề CỐ Ý không nhắc tên nước nào -> match_topic không neo được (đúng hình dạng
# thông cáo Nhà Trắng/SEC/FTC đo được 05/09/2026).
BANG_FEED = {U_MU: _xml(10, co_ngay=False), U_THUONG: _xml(10, co_ngay=True)}


def _soi(khai):
    return S.soi_feed(FEEDS, tai=_tai(BANG_FEED)), khai


# ════════════════════════════════ CÁC CA ════════════════════════════════
def ca01():
    """[SÀN] bản tin đủ tin mọi mục -> KHÔNG kêu."""
    dem = _dem(NOI_BO, DOI_NGOAI, KHCN, UC, ANH, BIEN_DONG)
    assert _do(dem) == {"Đối ngoại Mỹ": 3, "Nội bộ Mỹ": 3, "Anh": 3,
                        "Australia": 3, "Biển Đông": 3, "KHCN-QS": 3}, _do(dem)
    assert S.keu_san(dem) == []


def ca02():
    """[SÀN · PHẢI CHẶN] tiểu mục Anh chỉ 01 tin -> KÊU và gọi đúng tên tiểu mục Anh."""
    dem = _dem(NOI_BO, DOI_NGOAI, KHCN, UC, ANH[:1], BIEN_DONG)
    keu = S.keu_san(dem)
    assert keu, "Anh 1 tin mà cổng im — đúng ca sáng 05/09/2026 lọt lưới"
    assert f"{_neo(MD.TM_ANH)} 1 tin" in keu[0], keu
    assert _neo(MD.TM_UC) not in keu[0], ("Australia 3 tin mà bị kêu", keu)


def ca03():
    """[SÀN · PHẢI CHẶN] một mục RỖNG HẲN -> KÊU."""
    dem = _dem(NOI_BO, DOI_NGOAI, KHCN, UC, BIEN_DONG)      # không tin Anh nào
    keu = S.keu_san(dem)
    assert keu and f"{_neo(MD.TM_ANH)} 0 tin" in keu[0], keu


def ca04():
    """[SÀN] mục địa bàn phải TÁCH 03 tiểu mục, không đếm gộp."""
    ten = [t for t, _ in _dem(NOI_BO, DOI_NGOAI, KHCN, UC, ANH, BIEN_DONG)]
    assert len(ten) == 6, ten
    for tm in MD.THU_TU_TIEU_MUC:
        assert any(t.endswith(tm) for t in ten), (tm, ten)
    assert MD.MUC_DIA_BAN not in ten, "mục địa bàn không được đếm gộp"


def ca05():
    """[SÀN · PHẢI CHẶN] mục địa bàn GỘP đủ sàn (3 tin) mà tiểu mục Anh rỗng -> vẫn KÊU.

    Đây là chỗ đếm gộp sẽ che mất lỗi: sáng 05/09 mục địa bàn có 02 tin nên nhìn tổng thì
    "đủ", trong khi tin Anh bằng 0 — đúng thứ Huy bắt được.
    """
    dem = _dem(NOI_BO, DOI_NGOAI, KHCN, UC[:2], BIEN_DONG[:1])
    assert sum(n for t, n in dem if any(t.endswith(x) for x in MD.THU_TU_TIEU_MUC)) == 3
    keu = S.keu_san(dem)
    assert keu, keu
    assert f"{_neo(MD.TM_ANH)} 0 tin" in keu[0], keu
    assert f"{_neo(MD.TM_BIEN_DONG)} 1 tin" in keu[0], keu


def ca06():
    """[SÀN] ranh giới đúng SÀN: 2 tin cho qua, 1 tin bị chặn."""
    assert S.keu_san([("M", 2)]) == []
    assert S.keu_san([("M", 1)])
    assert S.SAN_MOI_MUC == 2, "sàn Huy chốt 05/09/2026 là 2 — đổi phải hỏi Huy"


def ca07():
    """[SÀN] chỉ đếm tin CÓ TRONG SỔ ĐÃ GỬI, không đếm cả kho."""
    dem = _do(_dem(NOI_BO[:2]))
    assert dem["Nội bộ Mỹ"] == 2 and dem["KHCN-QS"] == 0 and dem["Anh"] == 0, dem


def ca08():
    """[NGUỒN · PHẢI CHẶN] feed sống 10 item mà 0 item đọc được ngày -> KÊU MÙ NGÀY."""
    kq, khai = _soi({U_MU: {"chu_de": None, "khong_ngay": False}})
    keu = S.keu_feed(kq, khai)
    assert any("MÙ NGÀY" in k and "Mù ngày" in k for k in keu), keu


def ca09():
    """[NGUỒN] feed mà BẢNG đã ghi «feed không ghi ngày» -> KHÔNG kêu.

    Muốn tắt tiếng kêu thì phải ghi sự thật vào bảng nguồn nơi người đọc nhìn thấy, chứ
    không phải nhét tên vào danh sách trắng trong mã.
    """
    kq, khai = _soi({U_MU: {"chu_de": None, "khong_ngay": True}})
    assert not any("MÙ NGÀY" in k for k in S.keu_feed(kq, khai))


def ca10():
    """[NGUỒN] feed dưới NGUONG_ITEM -> không kêu (2 item cùng hỏng là ngẫu nhiên)."""
    nho = {U_MU: _xml(2, co_ngay=False)}
    kq = S.soi_feed([("Mù ngày", U_MU)], tai=_tai(nho))
    assert S.keu_feed(kq, {U_MU: {"chu_de": None, "khong_ngay": False}}) == []


def ca11():
    """[NGUỒN · PHẢI CHẶN] feed KHAI chủ đề ở bảng mà 0 item neo được -> KÊU CÂM CHỦ ĐỀ.

    Hình dạng đo được thật 05/09/2026: Nhà Trắng · SEC · FTC · USTR · BEA, 86 item sống,
    ngày đọc được 86/86, mà 0 item neo được chủ đề nào.
    """
    kq, khai = _soi({U_THUONG: {"chu_de": "Nội bộ Mỹ", "khong_ngay": False}})
    keu = S.keu_feed(kq, khai)
    assert any("CÂM CHỦ ĐỀ" in k and "Bình thường" in k for k in keu), keu


def ca12():
    """[NGUỒN] feed KHÔNG khai chủ đề mà 0 neo -> KHÔNG kêu (nguồn rộng, kêu là kêu oan)."""
    kq, khai = _soi({U_THUONG: {"chu_de": None, "khong_ngay": False}})
    assert not any("CÂM CHỦ ĐỀ" in k for k in S.keu_feed(kq, khai))


def ca13():
    """[NGUỒN] feed TẢI HỎNG -> im. Đo không được thì không kêu."""
    kq = S.soi_feed([("Tải hỏng", U_HONG)], tai=_tai(BANG_FEED))
    assert kq[0]["loi"], kq
    assert S.keu_feed(kq, {U_HONG: {"chu_de": "CNQS Mỹ", "khong_ngay": False}}) == []


def ca14():
    """[NGUỒN] feed có gán cứng chủ đề -> mọi item tính là neo được."""
    H = S._harvest()
    url = next(iter(H.FORCE_TOPIC_URL))
    kq = S.soi_feed([("Gán cứng", f"https://x.test/{url}")],
                    tai=lambda _u: _xml(10, co_ngay=True))
    assert kq[0]["gan_cung"] and kq[0]["n_neo"] == 10, kq


def ca15():
    """[GÁN CỨNG] bảng nguồn thật hiện tại: mọi khoá gán cứng đều còn khớp một feed."""
    assert S.khai_gan_cung_tuot() == [], S.khai_gan_cung_tuot()


def ca16():
    """[GÁN CỨNG · PHẢI CHẶN] khoá mồ côi -> KÊU.

    Lớp này bắt kiểu hồi quy mà lớp đo mạng KHÔNG bắt được: gỡ gán cứng của gov.uk thì feed
    ấy vẫn còn 8/20 item tự neo bằng từ khoá, tỷ lệ neo không về 0 nên không dòng nào kêu.
    """
    H = S._harvest()
    goc = dict(H.FORCE_TOPIC_URL)
    try:
        H.FORCE_TOPIC_URL["khong-he-co-trong-bang.invalid"] = "Nội bộ Mỹ"
        keu = S.khai_gan_cung_tuot()
    finally:
        H.FORCE_TOPIC_URL.clear()
        H.FORCE_TOPIC_URL.update(goc)
    assert keu and "khong-he-co-trong-bang.invalid" in keu[0], keu


def ca17():
    """[GÁN CỨNG] 05 nguồn chính thức Mỹ vá 05/09/2026 phải còn nguyên trong bảng gán cứng."""
    H = S._harvest()
    for manh in ("whitehouse.gov/presidential-actions", "sec.gov/news/pressreleases",
                 "ftc.gov/feeds/press-release", "ustr.gov/rss.xml", "bea.gov/news/rss"):
        assert H.FORCE_TOPIC_URL.get(manh) == "Nội bộ Mỹ", manh


def ca18():
    """[ĐẦU-CUỐI · PHẢI CHẶN] canary gọi lớp mục câm và kêu khi bản tin thật hụt mục.

    Đi qua ĐÚNG đường canary chạy trên CI: nạp `canary.py`, đưa vào một `lan` như sổ đã gửi,
    và để nó tự tìm `scripts/soi_muc_cam.py` bằng `sys.path`. Không thay hàm nào — thay hàm
    thì ca này chỉ chứng minh cái giả lập chạy được, không chứng minh canary có gọi thật.
    Bản tin dựng cố ý chỉ có 01 URL thật lấy từ kho, nên mọi mục còn lại đều dưới sàn.
    """
    can = _nap("canary_test", REPO / ".github" / "scripts" / "canary.py")
    md = _nap("make_docx_e2e", REPO / ".github" / "scripts" / "make_docx.py")
    data = md.extract_data((REPO / "index.html").read_text(encoding="utf-8"))
    mot = next(it["sourceUrl"] for it in data["usNews"] if it.get("sourceUrl"))
    keu = can.canh_bao_muc_cam("toi", "toi", {"urls": [mot]})
    assert any("DƯỚI SÀN" in k for k in keu), keu


def ca19():
    """[ĐẦU-CUỐI] CANARY_BO_SOI_MUC=1 tắt sạch lớp mới, canary vẫn chạy như cũ."""
    can = _nap("canary_test2", REPO / ".github" / "scripts" / "canary.py")
    os.environ["CANARY_BO_SOI_MUC"] = "1"
    try:
        assert can.canh_bao_muc_cam("sang", "sang", {"urls": []}) == []
    finally:
        os.environ.pop("CANARY_BO_SOI_MUC", None)


def ca20():
    """[ĐẦU-CUỐI] sổ chưa có dòng gửi (lan=None) -> lớp sàn không chạy, không kêu oan.

    Bản tin chưa đi thì canary đã kêu ở lớp một; kêu thêm "mọi mục 0 tin" là hai tin nhắn
    cho cùng một sự cố.
    """
    can = _nap("canary_test3", REPO / ".github" / "scripts" / "canary.py")
    assert not any("DƯỚI SÀN" in k for k in can.canh_bao_muc_cam("toi", "toi", None))


def ca21():
    """[SÀN] bản tin toàn URL lạ (không URL nào trong kho) -> KHÔNG đo được, im.

    Đếm tiếp thì mọi mục ra 0 và cổng kêu "cả bản tin rỗng" ngay lúc hai lớp canary cũ đang
    báo đạt. Ca đã xảy ra thật lúc dựng: sổ giả của `tests/test-canary-ban-tin.py` làm 03 ca
    "phải IM" của bộ ấy đỏ.
    """
    assert S.dem_muc(["https://khong-he-co.invalid/1"], data=DATA_GIA) == []
    assert S.keu_san([]) == []


def ca22():
    """[SÀN · PHẢI CHẶN] khớp MỘT PHẦN thì VẪN phải đo và VẪN phải kêu.

    Canh chiều nới tay của cái rào ở ca 21: sổ luôn có vài URL nằm ngoài file Word (diễn biến
    tập trận, tin Jay Lâm) — đo 03/09/2026 khớp 17/19. Bỏ qua cả lô khi khớp một phần là tắt
    cổng đúng những ngày bản tin mỏng nhất.
    """
    dem = S.dem_muc(_urls(NOI_BO[:1]) + ["https://khong-he-co.invalid/1"] * 3, data=DATA_GIA)
    assert dem, "khớp một phần mà bỏ cả lô -> cổng chết đúng ngày bản tin mỏng"
    assert _do(dem)["Nội bộ Mỹ"] == 1, _do(dem)
    assert S.keu_san(dem), "mọi mục dưới sàn mà cổng im"


CA = [
    (1, "[SÀN] đủ tin mọi mục -> im", ca01),
    (2, "[SÀN · PHẢI CHẶN] tiểu mục Anh 1 tin -> KÊU", ca02),
    (3, "[SÀN · PHẢI CHẶN] mục rỗng hẳn -> KÊU", ca03),
    (4, "[SÀN] tách 03 tiểu mục, không đếm gộp", ca04),
    (5, "[SÀN · PHẢI CHẶN] gộp đủ sàn mà tiểu mục rỗng -> vẫn KÊU", ca05),
    (6, "[SÀN] ranh giới sàn 2: 2 qua, 1 chặn", ca06),
    (7, "[SÀN] chỉ đếm tin trong sổ đã gửi", ca07),
    (8, "[NGUỒN · PHẢI CHẶN] feed sống mà mù ngày -> KÊU", ca08),
    (9, "[NGUỒN] bảng đã ghi «feed không ghi ngày» -> im", ca09),
    (10, "[NGUỒN] dưới ngưỡng item -> im", ca10),
    (11, "[NGUỒN · PHẢI CHẶN] khai chủ đề mà 0 neo -> KÊU", ca11),
    (12, "[NGUỒN] không khai chủ đề, 0 neo -> im", ca12),
    (13, "[NGUỒN] tải hỏng -> im", ca13),
    (14, "[NGUỒN] gán cứng thì mọi item tính là neo", ca14),
    (15, "[GÁN CỨNG] bảng thật: không khoá nào mồ côi", ca15),
    (16, "[GÁN CỨNG · PHẢI CHẶN] khoá mồ côi -> KÊU", ca16),
    (17, "[GÁN CỨNG] 05 nguồn chính thức Mỹ còn nguyên", ca17),
    (18, "[ĐẦU-CUỐI · PHẢI CHẶN] canary nhận cảnh báo mục hụt", ca18),
    (19, "[ĐẦU-CUỐI] cờ tắt lớp mới", ca19),
    (20, "[ĐẦU-CUỐI] chưa gửi thì không kêu oan", ca20),
    (21, "[SÀN] toàn URL lạ -> không đo được thì im", ca21),
    (22, "[SÀN · PHẢI CHẶN] khớp một phần thì vẫn đo, vẫn kêu", ca22),
]

# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
# (nhãn · file · phép thay · các ca BẮT BUỘC phải đỏ)
BAN_HONG = [
    ("sàn: hạ sàn về 1 tin (mục 1 tin lọt lưới)",
     "scripts/soi_muc_cam.py", "SAN_MOI_MUC = 2", "SAN_MOI_MUC = 1", [2, 5, 6]),

    ("sàn: đếm GỘP mục địa bàn, không tách tiểu mục (che đúng lỗi tin Anh)",
     "scripts/soi_muc_cam.py",
     '''        if ten != md.MUC_DIA_BAN:
            ra.append((ten, len(items)))
            continue''',
     '''        if True:
            ra.append((ten, len(items)))
            continue''',
     [1, 2, 4, 5]),

    ("sàn: keu_san luôn trả rỗng (cổng chết, cái gì cũng cho qua)",
     "scripts/soi_muc_cam.py",
     '''    hut = [(t, n) for t, n in dem if n < san]''',
     '''    hut = []''',
     [2, 3, 5, 6, 18]),

    ("sàn: rào «đo không được» nới thành bỏ qua cả khi khớp MỘT PHẦN (cổng chết ngày mỏng)",
     "scripts/soi_muc_cam.py",
     '''    if not tap & {it.get("sourceUrl")''',
     '''    if not tap >= {it.get("sourceUrl")''',
     [22]),

    ("sàn: gỡ rào «đo không được», bản tin toàn URL lạ vẫn bị đem ra kêu",
     "scripts/soi_muc_cam.py",
     '''            and not tap & {it.get("sourceUrl") for it in md.event_items(data)}:
        return []''',
     '''            and False:
        return []''',
     [21]),

    ("nguồn: bỏ hẳn phép đo mù ngày",
     "scripts/soi_muc_cam.py",
     '''        if r["n_ngay"] == 0 and not k.get("khong_ngay"):''',
     '''        if False:''',
     [8]),

    ("nguồn: kêu mù ngày kể cả khi bảng đã ghi «feed không ghi ngày» (kêu oan)",
     "scripts/soi_muc_cam.py",
     '''        if r["n_ngay"] == 0 and not k.get("khong_ngay"):''',
     '''        if r["n_ngay"] == 0:''',
     [9]),

    ("nguồn: bỏ ngưỡng item (feed 2 bài cũng bị kêu)",
     "scripts/soi_muc_cam.py", "NGUONG_ITEM = 3", "NGUONG_ITEM = 0", [10]),

    ("nguồn: bỏ phép đo câm chủ đề",
     "scripts/soi_muc_cam.py",
     '''        if r["n_neo"] == 0 and k.get("chu_de"):''',
     '''        if False:''',
     [11]),

    ("nguồn: kêu câm chủ đề cả với feed bảng KHÔNG khai chủ đề (kêu oan hàng chục dòng)",
     "scripts/soi_muc_cam.py",
     '''        if r["n_neo"] == 0 and k.get("chu_de"):''',
     '''        if r["n_neo"] == 0:''',
     [12]),

    ("nguồn: feed tải hỏng vẫn bị đem ra kêu",
     "scripts/soi_muc_cam.py",
     '''        if r["loi"] or r["n"] < NGUONG_ITEM:
            continue                      # đo không được thì im (xem docstring)''',
     '''        if False:
            continue''',
     [13]),

    ("gán cứng: bỏ phép dò khoá mồ côi",
     "scripts/soi_muc_cam.py",
     '''    if not mo_coi:
        return []''',
     '''    return []
    if not mo_coi:
        return []''',
     [16]),

    ("harvest: gỡ 05 nguồn chính thức Mỹ khỏi gán cứng (mở lại lỗ đo được 05/09)",
     "scripts/harvest.py",
     '''    "whitehouse.gov/presidential-actions": "Nội bộ Mỹ",''',
     '''''',
     [17]),

    ("canary: nuốt lớp mục câm, không gọi phép đo nào",
     ".github/scripts/canary.py",
     '''    if os.environ.get("CANARY_BO_SOI_MUC") == "1":
        return []''',
     '''    return []''',
     [18]),
]

CHEP = ("scripts/soi_muc_cam.py", "scripts/harvest.py", "scripts/topics.py",
        "scripts/tap_tran.py", "scripts/tg_api.py", "scripts/state.py",
        ".github/scripts/canary.py", ".github/scripts/make_docx.py", "CLAUDE.md")


def chay_ca() -> int:
    print(f"BỘ CA — cổng mục câm: sàn tin mỗi mục + feed sống mà câm  (repo: {REPO})")
    print("=" * 78)
    do = 0
    for so, mo_ta, fn in CA:
        try:
            fn()
            print(f"  ✓ {so}. {mo_ta}")
        except Exception as e:                                         # noqa: BLE001
            do += 1
            print(f"  ✗ {so}. {mo_ta}\n        │ {type(e).__name__}: {e}")
    print("=" * 78)
    if do:
        print(f"✗ {do}/{len(CA)} ca ĐỎ")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca xanh")
    return 0


def _dung_ban_sao(d: pathlib.Path, tep: str, tim: str, thay: str):
    goc = pathlib.Path(__file__).resolve().parent.parent
    for f in CHEP:
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(goc / f, d / f)
    shutil.copy2(goc / "index.html", d / "index.html")
    p = d / tep
    p.write_text(p.read_text(encoding="utf-8").replace(tim, thay, 1), encoding="utf-8")


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản repo đã gỡ dòng vá, các ca đã khai PHẢI ĐỎ")
    print("=" * 78)
    goc_dir = pathlib.Path(__file__).resolve().parent.parent
    hong = 0
    for nhan, tep, tim, thay, ca_phai_do in BAN_HONG:
        noi_dung = (goc_dir / tep).read_text(encoding="utf-8")
        if noi_dung.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {noi_dung.count(tim)} chỗ "
                  f"khớp trong {tep} (cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        dau = hashlib.sha1((tep + tim + thay).encode()).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"muccam-{os.getpid()}-{dau}-"))
        try:
            _dung_ban_sao(d, tep, tim, thay)
            env = dict(os.environ, MUCCAM_REPO=str(d), SOIMUC_REPO=str(d))
            env.pop("CANARY_BO_SOI_MUC", None)
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        do = {int(dong[4:].split(".")[0])
              for dong in r.stdout.splitlines() if dong.startswith("  ✗ ")}
        if len(do) == len(CA):
            print(f"  ✗ {nhan}\n        │ MỌI ca đều đỏ → phép thay nhiều khả năng làm vỡ "
                  f"cú pháp chứ không chứng minh ca nào có răng.")
            hong += 1
            continue
        thieu = set(ca_phai_do) - do
        thua = do - set(ca_phai_do)
        ok = not thieu
        print(f"  {'✓' if ok else '✗'} {nhan}")
        print(f"        │ ca đỏ: {sorted(do) or 'KHÔNG CÓ CA NÀO ĐỎ'} · cần đỏ: {ca_phai_do}"
              + (f" · đỏ thêm ngoài dự kiến: {sorted(thua)}" if thua else ""))
        if not ok:
            hong += 1
    print("=" * 78)
    if hong:
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI — bộ test chưa chứng minh "
              "được là có răng.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    return chay_ca()


if __name__ == "__main__":
    sys.exit(main())
