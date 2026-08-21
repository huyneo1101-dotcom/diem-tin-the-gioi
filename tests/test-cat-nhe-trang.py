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
    """Kho phải được nạp bằng HAI đường, không đường nào thay được đường kia.

    21/08/2026 bỏ lời gọi thẳng ở boot (kéo 711 KB nén cho phần người đọc bản tin không mở
    tới) và thay bằng: (i) nạp khi trang rảnh, để bấm sang tab không phải chờ; (ii) nạp theo
    nhu cầu ở tab / ô tìm kiếm, cho máy chậm chưa kịp rảnh. Mất (i) thì mỗi lần bấm tab phải
    chờ tải; mất (ii) thì máy chậm bấm tab ra trang thiếu tin — cả hai đều KHÔNG phát ra lỗi.
    """
    if not re.search(r"^napKhiRanh\(\);", html, re.M):
        return "luồng boot không gọi napKhiRanh() — kho không bao giờ được nạp"
    than = _than_ham(html, "function napKhiRanh(")
    if "loadKho()" not in than or "loadAnalyses()" not in than:
        return "napKhiRanh() không nạp đủ cả kho lẫn analyses"
    if "requestIdleCallback" not in than:
        return "napKhiRanh() không dùng requestIdleCallback — nạp sẵn lúc rảnh mất tác dụng"
    if "setTimeout" not in than:
        return ("napKhiRanh() không có nhánh lùi setTimeout — Safari cũ không có "
                "requestIdleCallback sẽ KHÔNG BAO GIỜ nạp kho, và không lỗi nào hiện ra")
    if "loadKho()" not in _handler_input(html):
        return "gõ vào ô tìm kiếm không kéo kho về — tìm trên lát đầu, ra thiếu tin"
    if not re.search(r"data-tab'\)\)\{loadKho\(\);", html):
        return "bấm tab không kéo kho về — máy chậm chưa kịp rảnh sẽ mở tab thiếu dữ liệu"
    return None


def _than_ham(html, mo_dau):
    i = html.index(mo_dau)
    m = re.search(r"\n(?:function |var |/\* )", html[i + 1:])
    return html[i:i + 1 + m.start()] if m else html[i:]


def _handler_input(html):
    i = html.index("document.addEventListener('input'")
    return html[i:i + 800]


def ca_tim_kiem_bao_thieu_kho(html, sw, pages, canary):
    """Tìm kiếm quét TOÀN kho. Kho chưa về mà con số vẫn in trơ là người đọc tin rằng
    tìm không ra nghĩa là không có — đúng chiều hỏng câm cả bước tách kho phải né."""
    than = _than_ham(html, "function searchInfo(")
    if "khoSan()" not in than:
        return "searchInfo() không hỏi khoSan() — kết quả thiếu tin mà không dấu hiệu nào"
    return None


def ca_xuat_word_chan_khi_thieu_kho(html, sw, pages, canary):
    """Hai nút xuất Word đều quét toàn kho; xuất khi kho chưa về là ra file thiếu tin."""
    thieu = []
    for nhan in ("data-export-home", "data-export-picked"):
        i = html.index("t.getAttribute('%s')" % nhan)
        if "khoSan()" not in html[i:i + 400]:
            thieu.append(nhan)
    return ("nút %s xuất Word mà không kiểm khoSan() — file ra thiếu tin, không báo"
            % ", ".join(thieu)) if thieu else None


def ca_mang_yeu_khong_nap_san(html, sw, pages, canary):
    """CHẠY THẬT napKhiRanh() bằng node, bốn trạng thái mạng.

    Chiều PHẢI CHẶN: mạng 3G hoặc người dùng bật tiết kiệm dữ liệu thì KHÔNG nạp sẵn 711 KB.
    Chiều CHỐNG CHẶN OAN: mạng 4G và trình duyệt không khai `navigator.connection` (Safari)
    thì VẪN nạp sẵn — bỏ nạp ở đây là mỗi lần bấm tab phải ngồi chờ tải, mà không lỗi nào hiện.
    """
    import subprocess  # noqa: PLC0415
    # Cắt tới dấu `}` ở CỘT 0, không dùng _than_ham: ngay sau hàm là lời gọi
    # `napKhiRanh();` chứ không phải một khai báo, nên _than_ham sẽ nuốt luôn cả
    # phần boot phía dưới và node vấp `loadBaomoi is not defined`.
    m0 = re.search(r"function napKhiRanh\(\)\{.*?\n\}", html, re.S)
    if not m0:
        return "index.html không có hàm napKhiRanh()"
    than = m0.group(0)
    js = ("var goi=0;var navigator={},window={};"
          "function loadKho(){goi++;}function loadAnalyses(){goi++;}"
          # Lời gọi trong mã là `requestIdleCallback(f,...)` TRẦN sau khi kiểm
          # `window.requestIdleCallback` — nên phải khai cả hai, không chỉ khai trên window.
          "var requestIdleCallback=function(f){f();};"
          "window.requestIdleCallback=requestIdleCallback;"
          + than +
          ";function thu(c){goi=0;navigator.connection=c;napKhiRanh();return goi;}"
          "console.log(JSON.stringify([thu(null),thu({effectiveType:'4g'}),"
          "thu({effectiveType:'3g'}),thu({saveData:true,effectiveType:'4g'})]));")
    p = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    if p.returncode != 0:
        return "không chạy được napKhiRanh() bằng node: %s" % p.stderr.strip()[:200]
    ra = json.loads(p.stdout.strip())
    mong = [2, 2, 0, 0]
    if ra != mong:
        return ("napKhiRanh() gọi %s lời nạp, phải là %s cho [không khai mạng · 4g · 3g · "
                "tiết kiệm dữ liệu]" % (ra, mong))
    return None


def ca_khosan_dung_hai_chieu(html, sw, pages, canary):
    """CHẠY THẬT hàm khoSan() bằng node, ba trạng thái. Soi chuỗi thì một phép so bị đảo
    dấu vẫn xanh; chạy thật mới phân biệt được chặn đúng với CHẶN OAN.

    Chặn oan ở đây tốn thật: bản trong repo (mở bằng file:// trên máy) không bao giờ có kho
    tách rời, nên khoSan() trả false là ô tìm kiếm treo dòng ⏳ vĩnh viễn và nút xuất Word
    không bao giờ bấm được."""
    import subprocess  # noqa: PLC0415
    m = re.search(r"function khoSan\(\)\{[^}]*\}", html)
    if not m:
        return "index.html không có hàm khoSan()"
    js = ("var DATA,KHO_LOADED;" + m.group(0) + ";var r=[];"
          "DATA={};KHO_LOADED=false;r.push(khoSan());"
          "DATA={_nhe:1};KHO_LOADED=false;r.push(khoSan());"
          "DATA={_nhe:1};KHO_LOADED=true;r.push(khoSan());"
          "console.log(JSON.stringify(r));")
    p = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    if p.returncode != 0:
        return "không chạy được khoSan() bằng node: %s" % p.stderr.strip()[:200]
    ra = json.loads(p.stdout.strip())
    mong = [True, False, True]
    if ra != mong:
        return ("khoSan() trả %s, phải là %s cho [bản repo đủ kho · bản Pages chưa nạp · "
                "bản Pages đã nạp]" % (ra, mong))
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
    ("kho nạp khi trang rảnh VÀ theo nhu cầu (tab · ô tìm kiếm)", ca_goi_o_boot),
    ("ô tìm kiếm BÁO khi kho chưa về", ca_tim_kiem_bao_thieu_kho),
    ("nút xuất Word CHẶN khi kho chưa về", ca_xuat_word_chan_khi_thieu_kho),
    ("khoSan() đúng cả ba trạng thái (chạy thật, chống chặn oan)", ca_khosan_dung_hai_chieu),
    ("mạng yếu / tiết kiệm dữ liệu KHÔNG nạp sẵn 711 KB (chạy thật)", ca_mang_yeu_khong_nap_san),
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
    ("gỡ lời gọi napKhiRanh() ở boot", "html",
     lambda h: h.replace("\nnapKhiRanh();\nloadBaomoi();", "\nloadBaomoi();"),
     "kho nạp khi trang rảnh VÀ theo nhu cầu (tab · ô tìm kiếm)"),
    ("gỡ nhánh lùi setTimeout (Safari cũ không bao giờ nạp kho)", "html",
     lambda h: h.replace("if(window.requestIdleCallback)requestIdleCallback(f,{timeout:4000});else setTimeout(f,2000);",
                         "if(window.requestIdleCallback)requestIdleCallback(f,{timeout:4000});", 1),
     "kho nạp khi trang rảnh VÀ theo nhu cầu (tab · ô tìm kiếm)"),
    ("gỡ loadKho() khỏi ô tìm kiếm (tìm trên lát đầu, ra thiếu tin)", "html",
     lambda h: h.replace("if(e.target&&e.target.id==='q'){loadKho();", "if(e.target&&e.target.id==='q'){", 1),
     "kho nạp khi trang rảnh VÀ theo nhu cầu (tab · ô tìm kiếm)"),
    ("gỡ loadKho() khỏi nút bấm tab (máy chậm mở tab thiếu dữ liệu)", "html",
     lambda h: h.replace("if(t.getAttribute('data-tab')){loadKho();", "if(t.getAttribute('data-tab')){", 1),
     "kho nạp khi trang rảnh VÀ theo nhu cầu (tab · ô tìm kiếm)"),
    ("ô tìm kiếm thôi báo kho chưa về (kết quả thiếu mà im)", "html",
     lambda h: h.replace("var them=khoSan()?'':' <b style=\"color:#c2410c\">\u23f3 Kho l\u01b0u tr\u1eef \u0111ang t\u1ea3i, k\u1ebft qu\u1ea3 c\u00f2n thi\u1ebfu</b>';",
                         "var them='';", 1),
     "ô tìm kiếm BÁO khi kho chưa về"),
    ("nút xuất Word thôi chặn khi kho chưa về (file ra thiếu tin)", "html",
     lambda h: h.replace("    if(!khoSan()){loadKho();toast('\u0110ang t\u1ea3i kho l\u01b0u tr\u1eef\u2026 b\u1ea5m l\u1ea1i sau v\u00e0i gi\u00e2y \u0111\u1ec3 file \u0111\u1ee7 tin');return;}\n    exportHomeDocx();return;}",
                         "    exportHomeDocx();return;}", 1),
     "nút xuất Word CHẶN khi kho chưa về"),
    ("khoSan() chặn OAN cả bản repo đủ kho (ô tìm kiếm treo ⏳ vĩnh viễn)", "html",
     lambda h: h.replace("function khoSan(){return !DATA._nhe||KHO_LOADED;}",
                         "function khoSan(){return KHO_LOADED;}", 1),
     "khoSan() đúng cả ba trạng thái (chạy thật, chống chặn oan)"),
    ("bỏ rào mạng yếu (3G vẫn kéo 711 KB người đọc không cần)", "html",
     lambda h: h.replace("  if(c&&(c.saveData===true||/^(slow-2g|2g|3g)$/.test(c.effectiveType||'')))return;\n", "", 1),
     "mạng yếu / tiết kiệm dữ liệu KHÔNG nạp sẵn 711 KB (chạy thật)"),
    ("rào mạng chặn OAN cả 4G và trình duyệt không khai connection", "html",
     lambda h: h.replace("if(c&&(c.saveData===true||/^(slow-2g|2g|3g)$/.test(c.effectiveType||'')))return;",
                         "return;", 1),
     "mạng yếu / tiết kiệm dữ liệu KHÔNG nạp sẵn 711 KB (chạy thật)"),
    ("khoSan() luôn nói SẴN (van chặn chết câm)", "html",
     lambda h: h.replace("function khoSan(){return !DATA._nhe||KHO_LOADED;}",
                         "function khoSan(){return true;}", 1),
     "khoSan() đúng cả ba trạng thái (chạy thật, chống chặn oan)"),
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
