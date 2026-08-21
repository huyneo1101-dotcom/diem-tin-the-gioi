#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANH bước dựng bản nhẹ — tách kho ra data/kho.json (21/08/2026).

VÌ SAO CẦN: `index.html` trên `main` nặng 1.718.169 byte (485 KB nén), riêng `var DATA` chiếm
88,5%. `pages.yml` cắt còn lát đầu (108 KB nén) rồi đẩy kho sang `data/kho.json`; trang nạp kho
sau khi đã hiện chữ. MỌI mắt xích của đường này hỏng theo kiểu KHÔNG PHÁT RA TIẾNG:

| Gỡ mất | Hậu quả | Có thấy lỗi không |
|---|---|---|
| bước dựng trong `pages.yml` | trang nặng như cũ, và canary kêu lệch mỗi ca | KHÔNG (web vẫn chạy) |
| lời gọi `loadKho()` ở boot | mất 468 tin cũ, 28 hồ sơ tập trận, cà phê, bản tuần | KHÔNG |
| rào `k!=='analyses'` trong loadKho | ghi đè kho think-tank vừa nạp → mục Think-tank trống | KHÔNG |
| `importDrillConcepts()` sau khi nạp | tab 📚 Khái niệm mất khái niệm rút từ hồ sơ tập trận | KHÔNG |
| `if(_firstRun)initSeen()` | người vào web lần đầu thấy cả kho gắn nhãn MỚI | KHÔNG |
| `data/kho.json` khỏi precache sw.js | mở offline chỉ còn lát đầu | KHÔNG |
| `ban_mong_doi()` của canary | canary so bản web với bản THÔ → kêu lệch mọi ca → Huy thôi đọc | KHÔNG |
| chạy nhầm `--tai-cho` trên máy rồi commit | `main` mất kho, 21 script Python ghi vào bản cụt | KHÔNG |

    python3 tests/test-cat-nhe-trang.py
    python3 tests/test-cat-nhe-trang.py --tu-kiem   # chứng minh bộ ca này BẮT ĐƯỢC lỗi
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
INDEX = REPO / "index.html"
SW = REPO / "sw.js"
PAGES = REPO / ".github" / "workflows" / "pages.yml"
CANARY = REPO / ".github" / "scripts" / "canary.py"

sys.path.insert(0, str(REPO / "scripts"))
from cat_nhe_trang import LAT_TIN, cat_nhe, da_cat  # noqa: E402


def _than_loadKho(html: str) -> str:
    """Thân hàm loadKho, cắt ở khai báo cấp cao nhất kế tiếp (không neo vào tên hàm sau —
    xem bài học cùng kiểu ở tests/test-tach-analyses.py::_than_loadAnalyses)."""
    i = html.index("function loadKho(")
    m = re.search(r"\n(?:function |var |/\* )", html[i + 1:])
    return html[i:i + 1 + m.start()] if m else html[i:]


# ------------------------------------------------------------------ các ca
def ca_repo_con_du_kho(html, sw, pages, canary):
    """index.html trong repo phải là bản ĐỦ. Cụt là 21 script Python đang ghi vào chỗ mất kho."""
    if da_cat(html):
        return ("index.html trong repo mang cờ _nhe — ai đó chạy `--tai-cho` trên máy rồi commit. "
                "Bản này MẤT kho, mọi script ghi tin vào đây sẽ ghi lên bản cụt.")
    return None


def ca_co_ham_nap(html, sw, pages, canary):
    if "function loadKho(" not in html:
        return "index.html không có hàm loadKho()"
    if not re.search(r"fetch\('data/kho\.json", html):
        return "loadKho() không fetch data/kho.json"
    return None


def ca_goi_o_boot(html, sw, pages, canary):
    if not re.search(r"^loadKho\(\);", html, re.M):
        return "không có lời gọi loadKho() ở luồng boot — kho không bao giờ được nạp"
    return None


def ca_chay_lai_phu_thuoc(html, sw, pages, canary):
    than = _than_loadKho(html)
    thieu = [t for t in ("importDrillConcepts()", "commitSeen()", "render()") if t not in than]
    return f"loadKho() thiếu: {', '.join(thieu)}" if thieu else None


def ca_lan_dau_vao_web(html, sw, pages, canary):
    if "if(_firstRun)initSeen()" not in _than_loadKho(html):
        return "loadKho() thiếu `if(_firstRun)initSeen()` — người mở web lần đầu thấy cả kho gắn nhãn MỚI"
    return None


def ca_khong_de_len_analyses(html, sw, pages, canary):
    """Hai lời gọi fetch chạy song song; kho ghi đè DATA.analyses là mục Think-tank trống."""
    if "k!=='analyses'" not in _than_loadKho(html).replace(" ", ""):
        return "loadKho() không loại 'analyses' — có thể ghi đè kho think-tank vừa nạp"
    return None


def ca_ban_repo_khong_fetch(html, sw, pages, canary):
    """Bản trong repo không có kho tách rời; fetch là 404 vô ích ở mọi lần mở local."""
    if "DATA._nhe" not in _than_loadKho(html):
        return "loadKho() không kiểm cờ DATA._nhe — bản đủ dữ liệu vẫn đi fetch 404"
    return None


def ca_sw_precache(html, sw, pages, canary):
    khai = "".join(m.group(1) for m in
                   re.finditer(r"^var (?:SHELL|KHO)\s*=\s*\[(.*?)\];", sw, re.M | re.S))
    if "data/kho.json" not in khai:
        return "sw.js: data/kho.json không nằm trong SHELL/KHO — mở offline chỉ còn lát đầu"
    return None


def ca_offline_lay_duoc_kho(html, sw, pages, canary):
    """Precache mà không `ignoreSearch` là precache trên giấy.

    `loadKho()`/`loadAnalyses()` gắn `?t=<mốc hiện tại>` để né cache trình duyệt, nên mỗi lần
    mở trang là một URL khác. `caches.match` mặc định so CẢ chuỗi truy vấn ⇒ bản precache
    không khớp, sw rơi xuống trả index.html, `r.json()` ném lỗi và `catch` nuốt gọn: mở
    offline mất kho mà không có dấu hiệu nào. Đo 21/08/2026 trên bản đang chạy:
    `match('data/kho.json?t=999999')` trả undefined, thêm ignoreSearch thì trúng.
    """
    # Soi MÃ, không soi cả file: chính đoạn chú thích ngay trên nhánh catch cũng nhắc
    # `ignoreSearch`, nên `"ignoreSearch" in sw` vẫn đúng kể cả sau khi lời gọi đã bị gỡ —
    # ca xanh giả. `--tu-kiem` bắt được đúng ca này lúc mới viết.
    ma = re.sub(r"(?m)^\s*//.*$", "", sw)
    if "ignoreSearch" not in ma or not re.search(r"caches\.match\(e\.request\s*,", ma):
        return ("sw.js: nhánh catch không dùng ignoreSearch — mọi lần nạp gắn ?t= mới nên bản "
                "precache không bao giờ khớp, mở offline là mất cả hai kho")
    if not re.search(r"self\.location\.origin", ma):
        return ("sw.js: ignoreSearch phải giới hạn ở request CÙNG GỐC — chuỗi truy vấn của "
                "Supabase mang nghĩa, bỏ qua nó là trả nhầm bảng cho nhau")
    return None


def ca_pages_dung_ban_nhe(html, sw, pages, canary):
    if not re.search(r"cat_nhe_trang\.py\s+--tai-cho", pages):
        return "pages.yml không chạy `cat_nhe_trang.py --tai-cho` — trang đẩy lên vẫn nặng nguyên"
    i = pages.index("cat_nhe_trang.py")
    j = pages.find("upload-pages-artifact")
    if j < 0 or j < i:
        return "bước dựng phải đứng TRƯỚC upload-pages-artifact, không thì đóng gói bản chưa cắt"
    return None


def ca_canary_so_ban_da_dung(html, sw, pages, canary):
    if "ban_mong_doi" not in canary:
        return "canary.py không dựng lại bản nhẹ trước khi so — sẽ kêu lệch ở MỌI ca"
    if not re.search(r"tren_main\s*=\s*bam_blob\(mong_doi\)", canary):
        return "canary.py vẫn băm thẳng bytes của index.html thay vì bản dựng ra"
    return None


def ca_cat_that_su_nhe(html, sw, pages, canary):
    nhe, kho = cat_nhe(html)
    a, b = len(html.encode()), len(nhe.encode())
    if b > a * 0.35:
        return f"bản dựng ra vẫn nặng {b:,}/{a:,} byte ({b * 100 // a}%) — ngưỡng là 35%"
    if "analyses" in json.loads(kho):
        return "data/kho.json dựng ra CÓ khoá 'analyses' — sẽ ghi đè kho think-tank"
    return None


def ca_lat_dau_du_cho_trang_chu(html, sw, pages, canary):
    """Trang chủ phải hiện chữ NGAY, trước khi kho về: cần đủ tin cho 3 mục lùi về 5 tin gần nhất."""
    nhe, _ = cat_nhe(html)
    from cat_nhe_trang import find_data_span  # noqa: PLC0415
    d = json.loads(nhe[slice(*find_data_span(nhe))])
    if len(d.get("usNews", [])) < 20 or len(d.get("worldNews", [])) < 15:
        return (f"lát đầu quá mỏng: usNews {len(d.get('usNews', []))}, "
                f"worldNews {len(d.get('worldNews', []))} — trang chủ sẽ trắng tới lúc kho về")
    # CHIỀU NỚI: nới ngưỡng lên gần bằng kho là quay lại trang nặng mà mọi ca vẫn xanh
    beo = [k for k, v in LAT_TIN.items() if v[1] > 120]
    if beo:
        return f"ngưỡng lát đầu bị nới quá tay: {beo} — cắt xong sẽ chẳng nhẹ hơn bao nhiêu"
    if not d.get("exercises"):
        return "lát đầu mất hẳn tập trận — dải điểm nhấn trang chủ sẽ trống"
    return None


CA = [
    ("index.html trong repo vẫn là bản ĐỦ kho", ca_repo_con_du_kho),
    ("index.html có loadKho() fetch đúng data/kho.json", ca_co_ham_nap),
    ("loadKho() được gọi ở luồng boot", ca_goi_o_boot),
    ("nạp xong chạy lại importDrillConcepts + commitSeen + render", ca_chay_lai_phu_thuoc),
    ("người vào web LẦN ĐẦU không thấy cả kho gắn nhãn MỚI", ca_lan_dau_vao_web),
    ("loadKho() KHÔNG ghi đè DATA.analyses", ca_khong_de_len_analyses),
    ("bản đủ dữ liệu trong repo không đi fetch kho", ca_ban_repo_khong_fetch),
    ("sw.js precache data/kho.json cho bản offline", ca_sw_precache),
    ("mở offline lấy được kho dù URL gắn ?t= mới", ca_offline_lay_duoc_kho),
    ("pages.yml dựng bản nhẹ TRƯỚC khi đóng gói artifact", ca_pages_dung_ban_nhe),
    ("canary so bản web với bản ĐÃ DỰNG, không so bản thô", ca_canary_so_ban_da_dung),
    ("bản dựng ra thật sự nhẹ và kho không mang analyses", ca_cat_that_su_nhe),
    ("lát đầu đủ tin cho trang chủ (và ngưỡng không bị nới)", ca_lat_dau_du_cho_trang_chu),
]


def chay(html=None, sw=None, pages=None, canary=None, im=False) -> int:
    html = html if html is not None else INDEX.read_text(encoding="utf-8")
    sw = sw if sw is not None else SW.read_text(encoding="utf-8")
    pages = pages if pages is not None else PAGES.read_text(encoding="utf-8")
    canary = canary if canary is not None else CANARY.read_text(encoding="utf-8")
    hong = 0
    for ten, fn in CA:
        try:
            ly_do = fn(html, sw, pages, canary)
        except Exception as ex:  # noqa: BLE001 — ca lỗi bất ngờ cũng là ca không đạt
            ly_do = f"ngoại lệ: {ex}"
        if ly_do:
            hong += 1
        if not im:
            print(f"{'✅' if not ly_do else '❌'} {ten}" + (f"\n     → {ly_do}" if ly_do else ""))
    if not im:
        print()
        print(f"{'TẤT CẢ ĐẠT' if not hong else f'{hong}/{len(CA)} CA KHÔNG ĐẠT'} ({len(CA)} ca)")
    return hong


# --------------------------------------------------------------- tự kiểm
# Mỗi bản hỏng gỡ đúng MỘT lớp bảo vệ và khai ca nào PHẢI báo không đạt theo. Khai thừa ca là
# tự bịt mắt mình — `--tu-kiem` sẽ báo trượt vì lý do sai.
BAN_HONG = [
    ("gỡ lời gọi loadKho() ở boot", "html",
     lambda h: h.replace("\nloadKho();\nloadAnalyses();", "\nloadAnalyses();"),
     "loadKho() được gọi ở luồng boot"),
    ("gỡ rào k!=='analyses' trong loadKho", "html",
     lambda h: h.replace("Object.keys(kho).forEach(function(k){if(k!=='analyses')DATA[k]=kho[k];});",
                         "Object.keys(kho).forEach(function(k){DATA[k]=kho[k];});", 1),
     "loadKho() KHÔNG ghi đè DATA.analyses"),
    ("gỡ importDrillConcepts() sau khi nạp kho", "html",
     lambda h: h.replace("    Object.keys(kho).forEach(function(k){if(k!=='analyses')DATA[k]=kho[k];});\n    importDrillConcepts();",
                         "    Object.keys(kho).forEach(function(k){if(k!=='analyses')DATA[k]=kho[k];});", 1),
     "nạp xong chạy lại importDrillConcepts + commitSeen + render"),
    ("gỡ if(_firstRun)initSeen() trong loadKho", "html",
     lambda h: h.replace("    commitSeen();\n    if(_firstRun)initSeen();\n    render();\n  }).catch(function(){KHO_LOADED=true;});",
                         "    commitSeen();\n    render();\n  }).catch(function(){KHO_LOADED=true;});", 1),
     "người vào web LẦN ĐẦU không thấy cả kho gắn nhãn MỚI"),
    ("gỡ rào DATA._nhe (bản repo cũng đi fetch 404)", "html",
     lambda h: h.replace("if(KHO_LOADED||!DATA._nhe)return;", "if(KHO_LOADED)return;", 1),
     "bản đủ dữ liệu trong repo không đi fetch kho"),
    ("commit nhầm bản đã cắt lên main", "html",
     lambda h: cat_nhe(h)[0],
     "index.html trong repo vẫn là bản ĐỦ kho"),
    ("gỡ data/kho.json khỏi precache sw.js", "sw",
     lambda s: s.replace(", './data/kho.json'", ""),
     "sw.js precache data/kho.json cho bản offline"),
    ("gỡ ignoreSearch (precache chỉ còn trên giấy)", "sw",
     lambda s: s.replace("caches.match(e.request, nha ? { ignoreSearch: true } : undefined)",
                         "caches.match(e.request)"),
     "mở offline lấy được kho dù URL gắn ?t= mới"),
    ("ignoreSearch áp cho MỌI gốc (trả nhầm bảng Supabase)", "sw",
     lambda s: s.replace("var nha = e.request.url.indexOf(self.location.origin) === 0;", "var nha = true;")
                .replace("nha ? { ignoreSearch: true } : undefined", "{ ignoreSearch: true }"),
     "mở offline lấy được kho dù URL gắn ?t= mới"),
    ("gỡ bước dựng khỏi pages.yml", "pages",
     lambda s: s.replace("        run: python3 scripts/cat_nhe_trang.py --tai-cho\n", ""),
     "pages.yml dựng bản nhẹ TRƯỚC khi đóng gói artifact"),
    ("canary quay lại so bản thô", "canary",
     lambda s: s.replace("tren_main = bam_blob(mong_doi)", "tren_main = bam_blob(raw_cu)"),
     "canary so bản web với bản ĐÃ DỰNG, không so bản thô"),
]


def tu_kiem() -> int:
    print("=== Chạy trên bản THẬT (mọi ca phải đạt) ===")
    if chay():
        print("\n✗ Bản thật đã có ca không đạt — sửa xong hãy tự kiểm.")
        return 1
    goc = {"html": INDEX.read_text(encoding="utf-8"), "sw": SW.read_text(encoding="utf-8"),
           "pages": PAGES.read_text(encoding="utf-8"), "canary": CANARY.read_text(encoding="utf-8")}
    hong = 0
    print("\n=== Chạy trên các bản HỎNG (ca đã khai phải BÁO KHÔNG ĐẠT) ===")
    for ten, loai, lam_hong, ca_phai_do in BAN_HONG:
        moi = dict(goc)
        moi[loai] = lam_hong(goc[loai])
        if moi[loai] == goc[loai]:
            print(f"❌ {ten}: KHÔNG áp được phép thay — chuỗi neo không còn khớp mã nguồn")
            hong += 1
            continue
        fn = dict(CA)[ca_phai_do]
        try:
            do = fn(moi["html"], moi["sw"], moi["pages"], moi["canary"]) is not None
        except Exception:  # noqa: BLE001
            do = True
        print(f"{'✅' if do else '❌'} {ten}\n     → ca '{ca_phai_do}' "
              f"{'báo không đạt, đúng như khai' if do else 'VẪN ĐẠT — ca đó vô dụng'}")
        hong += 0 if do else 1
    print()
    print("TỰ KIỂM ĐẠT — bộ ca này thật sự bắt được lỗi" if not hong
          else f"✗ {hong} bản hỏng KHÔNG bị bắt")
    return 1 if hong else 0


if __name__ == "__main__":
    raise SystemExit(tu_kiem() if "--tu-kiem" in sys.argv else (1 if chay() else 0))
