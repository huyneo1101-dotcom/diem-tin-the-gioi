#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST LỚP CẢNH BÁO TIN NỐI TIẾP của `scripts/add_news.py::warn_similar_titles`.

⚠ VÌ SAO CÓ FILE NÀY — sự cố thật tối 30/07/2026:
Người đọc bản tin nhắn lại "tin trên bị trùng á" khi thấy tin The Hill *"Trump đòi bổ sung
quyền áp thuế Iran vào dự luật trừng phạt Nga mang tên Graham"* (30/07). Đó KHÔNG phải tin
gửi hai lần — URL xuất hiện đúng 01 lần trong kho, sổ đã gửi 0 lần trước đó. Chỗ chồng nhau
là với bản tin HÔM TRƯỚC: tin Straits Times *"Thượng viện Mỹ bỏ phiếu dự luật trừng phạt
Nga-Iran mang tên cố Thượng nghị sĩ Lindsey Graham"* (29/07). Hai sự kiện khác nhau, nhưng
câu MỞ ĐẦU tóm tắt của tin mới kể lại nguyên sự kiện cũ nên đọc lướt hai dòng đầu thấy y hệt.

Hai lớp chống trùng đang có đều KHÔNG bắt được ca này:
  - `check_duplicate_urls` chặn cứng theo URL  -> hai URL khác nhau, đi qua;
  - `warn_similar_titles` so tiêu đề Jaccard   -> cặp đó đo ra 0.40, dưới ngưỡng cũ 0.6.
Ngưỡng đã hạ về `JACCARD_CANH_BAO_TIEU_DE = 0.4`.

⚠ ĐÂY LÀ LỚP *NHẮC*, KHÔNG PHẢI LỚP *CHẶN* — và lớp nhắc hỏng thì IM LẶNG TUYỆT ĐỐI:
gỡ nó đi thì `add_news.py` vẫn nạp tin, vẫn mã thoát 0, vẫn in "OK", người soạn chỉ đơn giản
mất hẳn lời nhắc mà không có một dấu hiệu nào. Cổng chặn hỏng thì có tin bị chặn nên biết
ngay; lớp nhắc hỏng thì không ai đi tìm. Vì vậy mỗi ca PHẢI KÊU dưới đây đòi ĐỦ BA thứ:
mã thoát vẫn 0 · CÓ dòng cảnh báo · và nêu ĐÚNG lời nhắc (viết lại câu mở), không chỉ đếm
số dòng.

Chạy:
    python3 tests/test-canh-bao-tin-noi-tiep.py
    python3 tests/test-canh-bao-tin-noi-tiep.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

`--tu-kiem` dựng các bản mã nguồn ĐÃ GỠ ĐÚNG DÒNG BẢO VỆ rồi chạy lại chính bộ ca này với
seam `ADDNEWS_MOD` / `MAKEDOCX_MOD` — mỗi bản hỏng phải làm ĐỎ đúng những ca đã khai.
Có bản hỏng cho CẢ HAI CHIỀU: chiều SIẾT (nâng ngưỡng lại 0.6 -> lớp nhắc câm trở lại) và
chiều NỚI (hạ ngưỡng về 0 -> kêu mọi cặp, nhiễu tới mức người soạn bỏ đọc cả mục). Chỉ canh
một chiều thì bản vá sau có thể "chữa" bằng cách mở toang, mà bảng vẫn xanh.
"""
import contextlib
import hashlib
import importlib.util
import io
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SCRIPTS = REPO / "scripts"
GH_SCRIPTS = REPO / ".github" / "scripts"

# Seam tự kiểm: trỏ sang bản mã nguồn khác (xem --tu-kiem).
MOD_PATH = pathlib.Path(os.environ.get("ADDNEWS_MOD") or (SCRIPTS / "add_news.py"))
MAKEDOCX_PATH = pathlib.Path(os.environ.get("MAKEDOCX_MOD") or (GH_SCRIPTS / "make_docx.py"))

# `add_news` tự chèn thư mục của CHÍNH NÓ vào sys.path để `import topics`. Bản hỏng có thể
# nằm chỗ khác nên chèn sẵn scripts/ thật — nếu không ca nào cũng đỏ vì ImportError, mà đỏ
# vì lý do sai thì không chứng minh được gì.
sys.path.insert(0, str(SCRIPTS))


def _nap(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("add_news_duoi_thu", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AN = _nap(MOD_PATH)

CA = []


def kiem(ten, dat):
    dat = bool(dat)
    CA.append((ten, dat))
    print(("  ✓ " if dat else "  ✗ ") + ten)


def tin(title):
    """Tin tối giản — `warn_similar_titles` chỉ đọc field `title`."""
    return {"title": title}


def chay(moi, cu):
    """Gọi lớp cảnh báo, trả về stdout. Bắt stdout thay vì subprocess để `--tu-kiem` tráo
    được bản hỏng (subprocess luôn nạp lại bản THẬT trên đĩa, ca sẽ xanh trên cả hai bản)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        AN.warn_similar_titles(
            {"usNews": [tin(t) for t in moi]},
            {"usNews": [tin(t) for t in cu], "worldNews": [], "xNews": []},
        )
    return buf.getvalue()


# ── Dữ liệu THẬT lấy từ index.html, không bịa ────────────────────────────────
GRAHAM_MOI = ("Trump đòi bổ sung quyền áp thuế Iran vào dự luật trừng phạt Nga mang tên "
              "Graham")
GRAHAM_CU = ("Thượng viện Mỹ bỏ phiếu dự luật trừng phạt Nga-Iran mang tên cố Thượng nghị "
             "sĩ Lindsey Graham")
PHI_MOI = ("Trung Quốc phản đối gay gắt hồ sơ mở rộng thềm lục địa của Philippines lên "
           "Liên Hợp Quốc")
PHI_CU = ("Philippines nộp hồ sơ mở rộng thềm lục địa khu vực Tây Palawan lên Liên hợp quốc")


def main() -> int:
    print("TEST — lớp cảnh báo tin NỐI TIẾP (add_news.warn_similar_titles)")
    print("═" * 78)

    # ── 1-2. Ca sinh ra bộ test này: cặp Graham thật, Jaccard = 0.40 ─────────
    out = chay([GRAHAM_MOI], [GRAHAM_CU])
    kiem("1. PHẢI KÊU — cặp Graham thật (sự cố 30/07) phải ra dòng cảnh báo",
         "[CẢNH BÁO] tiêu đề nghi trùng" in out)
    # Không chỉ đòi "có kêu": lời nhắc mới là thứ người soạn hành động theo. Bản hỏng B gỡ
    # đúng phần này mà ca 1 vẫn xanh — tức thiếu ca 2 thì lớp nhắc rỗng ruột không ai biết.
    kiem("2. PHẢI KÊU ĐÚNG VIỆC — nhắc viết lại câu MỞ của summary, không chỉ báo trùng",
         "vào thẳng phần MỚI" in out and "GIỮ tin" in out)

    # ── 3. Hồi quy con số: neo ngưỡng, kẻo ai đó nâng lại 0.6 trong im lặng ──
    kiem("3. HỒI QUY — ngưỡng cảnh báo phải là 0.4 (cặp Graham đo được đúng 0.40)",
         abs(AN.JACCARD_CANH_BAO_TIEU_DE - 0.4) < 1e-9)

    # ── 4. Đo lại chính con số Jaccard, để ca 3 không thành lời khai suông ───
    a, b = AN.norm_tokens(GRAHAM_MOI), AN.norm_tokens(GRAHAM_CU)
    j = len(a & b) / len(a | b)
    kiem(f"4. ĐO — Jaccard cặp Graham nằm trong [0.4, 0.5) (đo được {j:.2f})",
         0.4 <= j < 0.5)

    # ── 5. Cặp nối tiếp thật thứ hai, đo được 0.52 ──────────────────────────
    kiem("5. PHẢI KÊU — cặp Philippines thềm lục địa (0.52), tin nối tiếp thật",
         "[CẢNH BÁO] tiêu đề nghi trùng" in chay([PHI_MOI], [PHI_CU]))

    # ── 6-7. CHỐNG KÊU OAN — chiều nới ──────────────────────────────────────
    # Nếu ngưỡng bị hạ về 0 thì mọi cặp đều kêu, lớp nhắc thành nhiễu và người soạn bỏ đọc
    # cả mục — cùng hậu quả với việc nó câm hẳn, chỉ khác đường tới.
    kiem("6. CHỐNG KÊU OAN — hai tiêu đề khác hẳn chủ đề thì PHẢI IM",
         "[CẢNH BÁO]" not in chay(
             ["Fed giữ nguyên lãi suất lần thứ 5 liên tiếp giữa lúc nội bộ chia rẽ"],
             ["DARPA tài trợ 7 nhóm nghiên cứu chế tạo pin hạt nhân cỡ pin AA"]))

    lo = [
        "Hải quân Mỹ ký hợp đồng đóng 9 tàu ngầm tấn công Virginia Block VI",
        "Amnesty International yêu cầu điều tra vụ hành quyết 19 binh sĩ Mali",
        "Kinh tế Mỹ tăng trưởng chậm lại còn 1,5% trong quý II",
        "Hàng trăm người biểu tình phản đối Netanyahu tại Washington",
    ]
    kho = [
        "Elon Musk hồi sinh siêu PAC America PAC dốc sức cho đảng Cộng hòa",
        "Mỹ chi 1,4 tỷ USD tháo dỡ tàu sân bay hạt nhân USS Enterprise",
        "Việt Nam – Australia bàn hợp tác quốc phòng và tìm hài cốt liệt sĩ",
    ]
    kiem("7. CHỐNG KÊU OAN — lô 4 tin khác chủ đề nhau, không tin nào được kêu",
         "[CẢNH BÁO]" not in chay(lo, kho))

    # ── 8. Ngưỡng BIÊN: dưới ngưỡng thì im, đúng thiết kế ───────────────────
    # Chọn cặp đo được ~0.33: chung nhiều từ nhưng chưa tới mức nối tiếp.
    t1 = "Trung Quốc siết vòng vây hàng hải quanh Đài Loan bằng tuần tra hải cảnh mới"
    t2 = "Hải cảnh Trung Quốc triển khai trực thăng Z-20 trên tàu tuần tra ở Biển Đông"
    jb = len(AN.norm_tokens(t1) & AN.norm_tokens(t2)) / len(AN.norm_tokens(t1) | AN.norm_tokens(t2))
    kiem(f"8. BIÊN — cặp dưới ngưỡng ({jb:.2f} < 0.4) thì PHẢI IM",
         jb < 0.4 and "[CẢNH BÁO]" not in chay([t1], [t2]))

    # ── 9. Lớp nhắc phải còn NẰM TRÊN ĐƯỜNG ĐI ──────────────────────────────
    # Hàm còn sống mà không ai gọi thì cũng câm y hệt — đây đúng là kiểu hỏng khó thấy nhất.
    src = MOD_PATH.read_text(encoding="utf-8")
    goi = [d for d in src.splitlines()
           if "warn_similar_titles(" in d and not d.lstrip().startswith(("#", "def "))]
    kiem("9. CÒN TRÊN ĐƯỜNG ĐI — `warn_similar_titles` phải được gọi trong luồng nạp",
         len(goi) >= 1)

    # ── 10. `make_docx.py` KHÔNG được dựng lại phép lọc theo TIÊU ĐỀ ────────
    # Ca này TRƯỚC 01/08/2026 canh ngưỡng 0.6 của `make_docx.loc_trung_jaylam` — hàm đó lọc
    # tin Jay Lâm khỏi mục 5 bằng Jaccard tiêu đề. Mục 5 đã bỏ hẳn cùng hàm ấy khi Huy đảo
    # nguyên tắc: file Jay Lâm nay là BỘ LỌC, và phép lọc chạy theo URL trong sổ
    # `logs/trung-jaylam.json` do agent khai, KHÔNG theo độ giống tiêu đề.
    # Giữ ca ở đây (thay vì gỡ) vì nguy cơ vẫn còn nguyên chiều: ai đó thấy hai bên đều "so
    # tiêu đề" rồi dựng lại một phép lọc Jaccard trong `make_docx.py` sẽ tạo lớp LỌC THẬT
    # thứ hai, mà lọc oan ở đó là MẤT TIN — nặng hơn hẳn một dòng cảnh báo thừa.
    md = MAKEDOCX_PATH.read_text(encoding="utf-8")
    kiem("10. KHÔNG LÂY — `make_docx.py` không dựng lại phép lọc Jaccard theo tiêu đề",
         "len(tk | o)" not in md and "loc_trung_jaylam" not in md)

    print("═" * 78)
    do = [t for t, ok in CA if not ok]
    if do:
        print(f"✗ {len(do)}/{len(CA)} ca KHÔNG ĐẠT")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt")
    return 0


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
# (nhãn · file đích · phép thay trong mã nguồn · các ca BẮT BUỘC phải đỏ)
BAN_HONG = [
    # Chiều SIẾT — đúng trạng thái trước sự cố 30/07: lớp nhắc chưa nổ lần nào.
    ("nâng ngưỡng lại 0.6 (trạng thái gây ra sự cố 30/07)",
     "add_news",
     ("JACCARD_CANH_BAO_TIEU_DE = 0.4", "JACCARD_CANH_BAO_TIEU_DE = 0.6"),
     [1, 2, 3, 5]),
    # Lớp nhắc còn kêu nhưng RỖNG RUỘT — ca 1 vẫn xanh, chỉ ca 2 bắt được.
    # ⚠ Phép thay phải gỡ TRỌN khối 4 dòng nhắc, không gỡ mỗi dòng đầu: lần dựng đầu chỉ thay
    # dòng `print` thứ nhất thì ba dòng sau vẫn in ra, mà chuỗi ca 2 neo vào (`vào thẳng phần
    # MỚI` / `GIỮ tin`) nằm ở dòng thứ hai — ca vẫn xanh trên bản hỏng, đúng bẫy "gỡ một lớp
    # thì lớp kia gánh".
    ("gỡ lời nhắc viết lại câu mở (chỉ còn báo trùng suông)",
     "add_news",
     ('                print("      -> Nếu đây là tin NỐI TIẾP (sự kiện mới của cùng một câu chuyện):")\n'
      '                print("         GIỮ tin, nhưng câu ĐẦU của summary phải vào thẳng phần MỚI.")\n'
      '                print("         Phần đã gửi hôm trước dồn về sau, rút còn một vế ngắn.")\n'
      '                print("         Đọc lướt hai dòng đầu mà thấy y hệt hôm qua là người đọc kêu trùng.")',
      '                pass'),
     [2]),
    # Chiều NỚI — "chữa" bằng cách mở toang thì mọi cặp đều kêu, lớp nhắc thành nhiễu.
    # Ca 3 đỏ theo là ĐÚNG (nó neo con số 0.4) — khai vào đây theo số đo thật, không suy luận.
    ("hạ ngưỡng về 0 (kêu mọi cặp -> người soạn bỏ đọc cả mục)",
     "add_news",
     ("JACCARD_CANH_BAO_TIEU_DE = 0.4", "JACCARD_CANH_BAO_TIEU_DE = 0.0"),
     [3, 6, 7, 8]),
    # Hàm còn sống nhưng không ai gọi — câm y hệt lúc bị gỡ hẳn.
    ("gỡ lời gọi khỏi luồng nạp (hàm còn sống, không ai gọi)",
     "add_news",
     ("    warn_similar_titles(new_items, similar_warnings_data)", "    pass"),
     [9]),
    # Dựng lại một lớp LỌC THẬT theo tiêu đề trong `make_docx.py` — đúng thứ ca 10 canh.
    ("dựng lại phép lọc Jaccard theo tiêu đề trong make_docx (lọc oan = mất tin)",
     "make_docx",
     ("def loc_bo_trung_jaylam(items, urls, ten_muc=\"\"):",
      "def loc_trung_jaylam(rows, da_co):\n"
      "    for tk in rows:\n"
      "        for o in da_co:\n"
      "            if len(tk & o) / len(tk | o) >= 0.4:\n"
      "                return []\n"
      "    return rows\n"
      "\n"
      "\n"
      "def loc_bo_trung_jaylam(items, urls, ten_muc=\"\"):"),
     [10]),
]

DICH = {"add_news": (SCRIPTS / "add_news.py", "ADDNEWS_MOD", SCRIPTS),
        "make_docx": (GH_SCRIPTS / "make_docx.py", "MAKEDOCX_MOD", GH_SCRIPTS)}


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản mã nguồn đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, dich, (tim, thay), ca_phai_do in BAN_HONG:
        goc_path, bien_env, thu_muc = DICH[dich]
        goc = goc_path.read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"(cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        noi_dung = goc.replace(tim, thay)
        # Tên bản hỏng mang PID **và sha1 NỘI DUNG** (luật mục 17/23 CLAUDE.md toàn cục):
        #   - PID   -> hai phiên chạy `--tu-kiem` cùng lúc không xoá bản hỏng của nhau;
        #   - sha1  -> bộ này nạp bản hỏng bằng `importlib`, mà hai bản hỏng liên tiếp ghi
        #     cùng tên trong cùng một giây có thể khiến Python đọc lại `.pyc` của bản TRƯỚC,
        #     tức bản hỏng sau chạy bằng bytecode bản trước mà không báo lỗi gì.
        # Bản hỏng phải nằm TRONG thư mục thật của script (nó tự suy repo root từ __file__).
        sha = hashlib.sha1(noi_dung.encode("utf-8")).hexdigest()[:8]
        f = thu_muc / f"_thu-hong-{os.getpid()}-{sha}-{goc_path.name}"
        try:
            f.write_text(noi_dung, encoding="utf-8")
            env = dict(os.environ, **{bien_env: str(f)})
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            f.unlink(missing_ok=True)
        do = {int(d[4:].split(".")[0])
              for d in r.stdout.splitlines() if d.startswith("  ✗ ")}
        # Bản hỏng làm ĐỎ TOÀN BỘ ca = phép thay phá hỏng nền (lỗi cú pháp/ImportError), chứ
        # không phải gỡ đúng một lớp vá — nó không chứng minh được ca nào có răng.
        if len(do) == len(CA) or (not do and not r.stdout.strip()):
            print(f"  ✗ {nhan}\n        │ bản hỏng làm đỏ TOÀN BỘ ca (hoặc không chạy nổi) "
                  f"→ phép thay sai, sửa lại. stderr: {r.stderr.strip()[:180]}")
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
            print(f"        │ ⚠ ca {sorted(thieu)} VẪN XANH trên bản hỏng → test không bắt được lỗi này.")
    print("═" * 78)
    if hong:
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI — bộ test chưa chứng minh "
              f"được là nó bắt được lỗi.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--tu-kiem":
        # `CA` phải có sẵn độ dài để phép đo "đỏ toàn bộ" ở trên có nghĩa.
        with contextlib.redirect_stdout(io.StringIO()):
            main()
        sys.exit(tu_kiem())
    sys.exit(main())
