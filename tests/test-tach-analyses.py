#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANH việc tách `DATA.analyses` ra data/analyses.json (30/07/2026).

VÌ SAO CẦN: sau khi tách, mọi mắt xích đều thuộc loại **hỏng thì im lặng** — không có lỗi
nào hiện ra, chỉ có mục 🏛️ Think-tank trống hoặc 442 bài gắn nhãn MỚI:

| Gỡ mất | Hậu quả | Có thấy lỗi không |
|---|---|---|
| `loadAnalyses()` hoặc lời gọi ở boot | mục Think-tank rỗng, khối bài dưới tập trận rỗng | KHÔNG |
| `if(_firstRun)initSeen()` trong loadAnalyses | người vào web lần đầu thấy 442 nhãn MỚI | KHÔNG |
| `importAnalysisConcepts()` sau khi nạp | tab 📚 Khái niệm mất khái niệm rút từ bài | KHÔNG |
| `commitSeen()` sau khi nạp | lần vào sau vẫn 442 nhãn MỚI | KHÔNG |
| `data/analyses.json` khỏi SHELL của sw.js | mở offline thì Think-tank trống | KHÔNG |
| script Python đọc `data["analyses"]` từ index.html | thấy mảng RỖNG → guardrail trùng-url tê liệt, nạp lại cả kho | KHÔNG |

    python3 tests/test-tach-analyses.py
    python3 tests/test-tach-analyses.py --tu-kiem   # chứng minh bộ ca này BẮT ĐƯỢC lỗi
"""
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
INDEX = REPO / "index.html"
SW = REPO / "sw.js"
KHO = REPO / "data" / "analyses.json"


def _index(nguon=None) -> str:
    return (nguon or INDEX).read_text(encoding="utf-8")


# Mỗi ca: (mô tả, hàm kiểm -> None nếu ĐẠT, chuỗi lý do nếu HỎNG)
def ca_kho_ton_tai(html, sw):
    if not KHO.exists():
        return f"không có {KHO.relative_to(REPO)}"
    bai = json.loads(KHO.read_text(encoding="utf-8"))
    if not isinstance(bai, list) or not bai:
        return "kho think-tank rỗng hoặc không phải mảng"
    thieu = [a.get("url") for a in bai if not a.get("takeaway")]
    if thieu:
        return f"{len(thieu)} bài thiếu 'takeaway' (web và email hiển thị field này nổi nhất)"
    return None


def ca_index_rong(html, sw):
    if '"analyses":[]' not in html:
        return 'index.html: DATA.analyses phải RỖNG — có bài nghĩa là script nào đó ghi nhầm chỗ'
    return None


def ca_co_ham_nap(html, sw):
    if "function loadAnalyses(" not in html:
        return "index.html không còn hàm loadAnalyses()"
    if not re.search(r"fetch\('data/analyses\.json", html):
        return "loadAnalyses() không fetch data/analyses.json"
    return None


def ca_goi_o_boot(html, sw):
    """Kho think-tank phải được nạp từ luồng boot — gọi thẳng HOẶC qua một hàm bọc.

    ⚠️ Từ commit 704c880 (21/08/2026, "Hoãn 711 KB kho tới lúc thật sự cần") boot KHÔNG còn
    dòng `loadAnalyses();` ở cấp cao nhất: nó gọi `napKhiRanh()`, và chính hàm đó đẩy
    `loadKho(); loadAnalyses();` vào `requestIdleCallback`. Bản kiểm cũ neo cứng vào
    `^loadAnalyses\(\);` nên báo ĐỎ liên tục từ hôm ấy dù web vẫn nạp kho đủ (đo 25/08/2026
    trên bản đang phục vụ: `data/analyses.json` trả 200 với 824 bài). Ca đỏ trên bản thật làm
    `--tu-kiem` thoát sớm, nên CẢ 09 ca của bộ này ngừng phát hiện trong im lặng suốt
    21→25/08/2026 — đúng loại hỏng câm mà bộ ca này sinh ra để bịt.

    Nay nhận cả hai hình dạng, và KHÔNG neo vào tên `napKhiRanh` để đổi tên hàm bọc không làm
    cổng đỏ oan: tìm mọi lời gọi `<tên>();` ở cấp cao nhất rồi soi thân hàm mang tên đó.
    """
    if re.search(r"^loadAnalyses\(\);", html, re.M):
        return None
    for ten in re.findall(r"^([A-Za-z_$][\w$]*)\(\);", html, re.M):
        if ten != "loadAnalyses" and "loadAnalyses()" in _than_ham(html, ten):
            return None
    return "không có lời gọi loadAnalyses() ở luồng boot — kho không bao giờ được nạp"


def _than_loadAnalyses(html: str) -> str:
    """Thân hàm loadAnalyses, CẮT ĐÚNG ở hàm kế tiếp.

    ⚠️ Trước 21/08/2026 hàm này cắt tới `function loadBaomoi(`. Khi `loadKho()` chen vào giữa
    hai hàm đó, "thân loadAnalyses" nuốt luôn thân loadKho — mà loadKho chép đúng khuôn
    `commitSeen(); if(_firstRun)initSeen(); render();`. Hậu quả: gỡ sạch mấy dòng ấy khỏi
    loadAnalyses mà ca vẫn báo đạt, tức cổng ngừng phát hiện trong im lặng. `--tu-kiem` bắt
    được đúng ca này. Nay cắt ở mốc mở đầu khai báo cấp cao nhất kế tiếp, không neo vào tên.
    """
    return _than_ham(html, "loadAnalyses")


def _than_ham(html: str, ten: str) -> str:
    """Thân hàm `ten`, cắt ở mốc mở đầu khai báo cấp cao nhất kế tiếp. Không có hàm thì trả rỗng."""
    moc = "function %s(" % ten
    if moc not in html:
        return ""
    i = html.index(moc)
    m = re.search(r"\n(?:function |var |/\* )", html[i + 1:])
    return html[i:i + 1 + m.start()] if m else html[i:]


def ca_chay_lai_phu_thuoc(html, sw):
    than = _than_loadAnalyses(html)
    thieu = [t for t in ("importAnalysisConcepts()", "commitSeen()", "render()") if t not in than]
    return f"loadAnalyses() thiếu: {', '.join(thieu)}" if thieu else None


def ca_lan_dau_vao_web(html, sw):
    if "if(_firstRun)initSeen()" not in _than_loadAnalyses(html):
        return ("loadAnalyses() thiếu `if(_firstRun)initSeen()` — người mở web lần đầu sẽ thấy "
                "toàn bộ kho think-tank gắn nhãn MỚI")
    return None


def ca_sw_precache(html, sw):
    # Soi ĐÚNG dòng khai danh sách, không soi cả file: comment trong sw.js cũng nhắc tên file
    # này, nên `"data/analyses.json" in sw` vẫn đúng kể cả khi đã bị gỡ — ca xanh giả.
    # Từ 21/08/2026 hai kho tách ra nằm ở `var KHO` chứ không ở `var SHELL`: `addAll` là
    # tất-cả-hoặc-không, một kho 404 là service worker không cài được. Ca này nhận CẢ HAI chỗ,
    # nhưng bắt buộc tên file phải xuất hiện trong một danh sách ĐƯỢC install() nạp thật.
    khai = "".join(m.group(1) for m in
                   re.finditer(r"^var (?:SHELL|KHO)\s*=\s*\[(.*?)\];", sw, re.M | re.S))
    if not khai:
        return "sw.js: không tìm thấy khai báo `var SHELL = [...]` / `var KHO = [...]`"
    if "data/analyses.json" not in khai:
        return "sw.js: data/analyses.json không nằm trong SHELL/KHO — mở offline thì Think-tank trống"
    if not re.search(r"addEventListener\('install'[\s\S]{0,400}?KHO", sw):
        return "sw.js: `var KHO` khai rồi nhưng install() không nạp — precache chỉ có trên giấy"
    return None


def ca_script_python_khong_doc_index(html, sw):
    """Không script nào được lấy bài think-tank từ `data["analyses"]` của index.html nữa."""
    xau = []
    for p in sorted((REPO / "scripts").glob("*.py")) + sorted((REPO / ".github" / "scripts").glob("*.py")):
        if p.name in ("analyses_store.py", "tach_analyses.py"):
            continue
        s = p.read_text(encoding="utf-8")
        if re.search(r'data\.get\(\s*["\']analyses["\']', s) or re.search(r'data\[\s*["\']analyses["\']\s*\]', s):
            if "analyses_store" not in s:
                xau.append(p.relative_to(REPO).as_posix())
    return f"còn đọc analyses từ index.html: {', '.join(xau)}" if xau else None


def ca_guardrail_trung_url(html, sw):
    """add_analyses phải thấy đủ url think-tank, không thì nạp trùng cả kho mà không kêu."""
    sys.path.insert(0, str(REPO / "scripts"))
    import add_analyses  # noqa: E402
    import analyses_store  # noqa: E402
    s, e = add_analyses.find_data_span(html)
    co = add_analyses.collect_existing_urls(json.loads(html[s:e]))
    kho = {a.get("url") for a in analyses_store.doc(REPO) if a.get("url")}
    thieu = kho - co
    return f"{len(thieu)} url think-tank KHÔNG được guardrail nhìn thấy" if thieu else None


CA = [
    ("kho data/analyses.json tồn tại và đủ takeaway", ca_kho_ton_tai),
    ("index.html giữ DATA.analyses rỗng", ca_index_rong),
    ("index.html có loadAnalyses() fetch đúng file", ca_co_ham_nap),
    ("loadAnalyses() được gọi ở luồng boot", ca_goi_o_boot),
    ("nạp xong chạy lại 3 việc phụ thuộc", ca_chay_lai_phu_thuoc),
    ("người vào web LẦN ĐẦU không thấy 442 nhãn MỚI", ca_lan_dau_vao_web),
    ("sw.js precache kho cho bản offline", ca_sw_precache),
    ("không script Python nào đọc analyses từ index.html", ca_script_python_khong_doc_index),
    ("guardrail trùng-url vẫn thấy đủ kho think-tank", ca_guardrail_trung_url),
]


def chay(html=None, sw=None, im=False) -> int:
    html = html if html is not None else _index()
    sw = sw if sw is not None else SW.read_text(encoding="utf-8")
    hong = 0
    for ten, fn in CA:
        try:
            ly_do = fn(html, sw)
        except Exception as ex:  # noqa: BLE001 — ca lỗi bất ngờ cũng là ca ĐỎ
            ly_do = f"ngoại lệ: {ex}"
        if ly_do:
            hong += 1
        if not im:
            print(f"{'✅' if not ly_do else '❌'} {ten}" + (f"\n     → {ly_do}" if ly_do else ""))
    if not im:
        print()
        print(f"{'TẤT CẢ ĐẠT' if not hong else f'{hong}/{len(CA)} CA ĐỎ'} ({len(CA)} ca)")
    return hong


# --------------------------------------------------------------- tự kiểm
# Mỗi bản hỏng gỡ đúng MỘT lớp bảo vệ, và khai ca nào PHẢI đỏ theo. Khai thừa ca là tự bịt
# mắt mình: `--tu-kiem` sẽ báo trượt vì lý do sai (bài học 29/07 ở QuanSu).
BAN_HONG = [
    # Hai bản hỏng cho MỘT ca, vì từ 21/08/2026 đường từ boot tới kho có HAI mắt nối tiếp:
    # boot gọi hàm bọc, hàm bọc gọi loadAnalyses(). Gỡ mắt nào cũng làm kho không bao giờ về,
    # nên phải chứng minh ca bắt được cả hai — bản hỏng cũ chỉ gỡ dòng `loadAnalyses();` ở cấp
    # cao nhất, mà dòng ấy đã biến mất từ commit 704c880 nên phép thay thành vô hiệu.
    ("gỡ loadAnalyses() khỏi hàm nạp-khi-rảnh", "html",
     lambda h: h.replace("var f=function(){loadKho();loadAnalyses();};",
                         "var f=function(){loadKho();};", 1),
     "loadAnalyses() được gọi ở luồng boot"),
    ("gỡ lời gọi hàm nạp-khi-rảnh ở boot", "html",
     lambda h: h.replace("\nnapKhiRanh();\nloadBaomoi();", "\nloadBaomoi();", 1),
     "loadAnalyses() được gọi ở luồng boot"),
    ("gỡ if(_firstRun)initSeen() trong loadAnalyses", "html",
     lambda h: h.replace("    commitSeen();\n    if(_firstRun)initSeen();\n    render();",
                         "    commitSeen();\n    render();", 1),
     "người vào web LẦN ĐẦU không thấy 442 nhãn MỚI"),
    ("gỡ importAnalysisConcepts() sau khi nạp", "html",
     lambda h: h.replace("    DATA.analyses=arr;\n    importAnalysisConcepts();",
                         "    DATA.analyses=arr;", 1),
     "nạp xong chạy lại 3 việc phụ thuộc"),
    ("gỡ kho analyses khỏi danh sách precache của sw.js", "sw",
     lambda s: s.replace("'./data/analyses.json', ", ""),
     "sw.js precache kho cho bản offline"),
    ("khai KHO nhưng install() không nạp (precache trên giấy)", "sw",
     lambda s: s.replace("return c.addAll(SHELL).then(function () {\n      return Promise.all(KHO.map(function (u) { return c.add(u).catch(function () {}); }));\n    });",
                         "return c.addAll(SHELL);"),
     "sw.js precache kho cho bản offline"),
]


def tu_kiem() -> int:
    print("=== Chạy trên bản THẬT (mọi ca phải xanh) ===")
    if chay():
        print("\n✗ Bản thật đã đỏ — sửa xong hãy tự kiểm.")
        return 1
    html_goc, sw_goc = _index(), SW.read_text(encoding="utf-8")
    hong = 0
    print("\n=== Chạy trên các bản HỎNG (ca đã khai phải ĐỎ) ===")
    for ten, loai, lam_hong, ca_phai_do in BAN_HONG:
        h, s = (lam_hong(html_goc), sw_goc) if loai == "html" else (html_goc, lam_hong(sw_goc))
        goc = html_goc if loai == "html" else sw_goc
        moi = h if loai == "html" else s
        if moi == goc:
            print(f"❌ {ten}: KHÔNG áp được phép thay — chuỗi neo không còn khớp mã nguồn")
            hong += 1
            continue
        fn = dict((t, f) for t, f in CA)[ca_phai_do]
        do = fn(h, s) is not None
        print(f"{'✅' if do else '❌'} {ten}\n     → ca '{ca_phai_do}' {'ĐỎ đúng như khai' if do else 'VẪN XANH — ca đó vô dụng'}")
        hong += 0 if do else 1
    print()
    print("TỰ KIỂM ĐẠT — bộ ca này thật sự bắt được lỗi" if not hong else f"✗ {hong} bản hỏng KHÔNG bị bắt")
    return 1 if hong else 0


if __name__ == "__main__":
    raise SystemExit(tu_kiem() if "--tu-kiem" in sys.argv else (1 if chay() else 0))
