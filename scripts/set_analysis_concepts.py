#!/usr/bin/env python3
"""Gắn KHÁI NIỆM vào bài think-tank trong DATA.analyses (chỉ thị Huy 29/07/2026).

Web có tab 📚 Khái niệm gom khái niệm từ mục Tập trận (`ex.concepts`) — nhưng bài think-tank
thì không có đường nào đưa khái niệm vào đó, dù đây mới là chỗ thuật ngữ lạ xuất hiện dày
nhất. Hàm `importAnalysisConcepts()` trong index.html đọc `a.concepts`; file này là đường ghi.

Dùng:
  python3 scripts/set_analysis_concepts.py concepts.json     # nạp
  python3 scripts/set_analysis_concepts.py --kiem            # soi bài nào chưa có khái niệm
  python3 scripts/set_analysis_concepts.py --tu-kiem         # chứng minh guardrail bắt được lỗi

concepts.json = [
  {"url":"<url ĐÚNG như trong DATA.analyses>",
   "concepts":[{"term":"Chuỗi đảo thứ nhất","def":"Giải thích 1-3 câu, tiếng Việt."}, ...]}
]

Guardrail CHẶN (exit 1, sửa JSON rồi chạy lại):
- `url` không có trong DATA.analyses (gõ sai / bài đã bị prune);
- thiếu `term` hoặc `def`, hoặc `def` ngắn hơn MIN_DEF ký tự (giải thích cụt thì thà không có);
- `term` dài quá MAX_TERM ký tự — web cắt ở 90, để dài hơn là hiện thiếu chữ;
- hai `term` trùng nhau trong CÙNG một bài (sau khi bỏ dấu);
- một bài quá MAX_CONCEPTS khái niệm — nhồi cả bài vào sổ tay thì sổ tay hết tác dụng lọc.

⚠️ Khái niệm trùng với bài KHÁC hoặc trùng với tập trận thì KHÔNG chặn: web dùng chung kho
`dt.concepts` và tự khử trùng theo tên đã bỏ dấu, nên chặn ở đây là chặn oan.
"""
import json
import pathlib
import sys
import unicodedata

MIN_DEF = 40
MAX_TERM = 90
MAX_CONCEPTS = 6


def die(msg: str):
    print(f"✗ CHẶN: {msg}", file=sys.stderr)
    sys.exit(1)


def norm(s: str) -> str:
    """Bỏ dấu để so khớp — cùng quy ước với norm() trong index.html."""
    s = unicodedata.normalize("NFD", (s or "").strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.replace("đ", "d").split())


def find_data_span(html: str):
    marker = "var DATA = "
    start = html.index(marker) + len(marker)
    depth = 0
    in_str = esc = False
    i = start
    while i < len(html):
        c = html[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        i += 1
    raise ValueError("Không tìm thấy điểm kết thúc var DATA")


def doc_data(repo: pathlib.Path):
    html_path = repo / "index.html"
    html = html_path.read_text(encoding="utf-8")
    s, e = find_data_span(html)
    return html_path, html, s, e, json.loads(html[s:e])


def kiem_lo(lo, analyses):
    """Soi lô trước khi ghi. Trả về dict {url: [concepts đã chuẩn hoá]}."""
    theo_url = {a.get("url"): a for a in analyses if a.get("url")}
    ra = {}
    for muc in lo:
        url = (muc or {}).get("url", "").strip()
        if url not in theo_url:
            die(f"url không có trong DATA.analyses: {url!r}")
        ks = muc.get("concepts") or []
        if not ks:
            die(f"lô cho {url!r} không có khái niệm nào")
        if len(ks) > MAX_CONCEPTS:
            die(f"{url!r} có {len(ks)} khái niệm, quá trần {MAX_CONCEPTS}")
        thay = set()
        sach = []
        for k in ks:
            term = (k or {}).get("term", "").strip()
            dinh = (k or {}).get("def", "").strip()
            if not term or not dinh:
                die(f"{url!r}: khái niệm thiếu term hoặc def — {k!r}")
            if len(term) > MAX_TERM:
                die(f"{url!r}: term dài {len(term)} ký tự, web cắt ở {MAX_TERM} — {term!r}")
            if len(dinh) < MIN_DEF:
                die(f"{url!r}: def của {term!r} chỉ {len(dinh)} ký tự, tối thiểu {MIN_DEF}")
            n = norm(term)
            if n in thay:
                die(f"{url!r}: term {term!r} lặp trong cùng một bài")
            thay.add(n)
            sach.append({"term": term, "def": dinh})
        ra[url] = sach
    return ra


def nap(duong_dan_json: str, repo: pathlib.Path):
    lo = json.loads(pathlib.Path(duong_dan_json).read_text(encoding="utf-8"))
    if not isinstance(lo, list):
        die("JSON phải là một MẢNG [{url, concepts:[...]}]")
    html_path, html, s, e, data = doc_data(repo)
    analyses = data.get("analyses") or []
    sach = kiem_lo(lo, analyses)

    hit = them = 0
    for a in analyses:
        ks = sach.get(a.get("url"))
        if not ks:
            continue
        a["concepts"] = ks
        hit += 1
        them += len(ks)
    new = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html_path.write_text(html[:s] + new + html[e:], encoding="utf-8")
    con = sum(1 for a in analyses if not a.get("concepts"))
    print(f"OK: gắn {them} khái niệm cho {hit} bài think-tank. Còn {con}/{len(analyses)} bài chưa có.")


def kiem(repo: pathlib.Path):
    _, _, _, _, data = doc_data(repo)
    analyses = data.get("analyses") or []
    co = [a for a in analyses if a.get("concepts")]
    thieu = [a for a in analyses if not a.get("concepts")]
    tong = sum(len(a["concepts"]) for a in co)
    print(f"{len(analyses)} bài think-tank · {len(co)} bài đã có khái niệm ({tong} khái niệm) "
          f"· {len(thieu)} bài chưa có")
    for a in thieu[:40]:
        print(f"  – [{a.get('date','?')}] {a.get('outlet','?')}: {(a.get('title') or '')[:78]}")
        print(f"    {a.get('url','')}")
    if len(thieu) > 40:
        print(f"  … và {len(thieu)-40} bài nữa")
    return 0 if not thieu else 2


# --------------------------------------------------------------- tự kiểm
def tu_kiem(repo: pathlib.Path):
    """Dựng các lô XẤU rồi khẳng định guardrail thật sự chặn (quy tắc 17: phải có ca PHẢI CHẶN).

    Ca 'phải cho qua' cũng có, để biết guardrail không chặn oan — nhưng chạy trên bản SAO của
    DATA trong bộ nhớ, không đụng index.html.
    """
    _, _, _, _, data = doc_data(repo)
    analyses = data.get("analyses") or []
    if not analyses:
        print("✗ Không có bài think-tank nào để dựng ca thử", file=sys.stderr)
        return 1
    url = analyses[0]["url"]
    dai = "x" * (MIN_DEF + 10)

    CA = [
        ("lô hợp lệ", "QUA",
         [{"url": url, "concepts": [{"term": "Chuỗi đảo thứ nhất", "def": dai}]}]),
        ("hai khái niệm khác nhau trong một bài", "QUA",
         [{"url": url, "concepts": [{"term": "Răn đe khước từ", "def": dai},
                                    {"term": "Sự đã rồi", "def": dai}]}]),
        ("url không có trong DATA", "CHAN",
         [{"url": "https://khong-ton-tai.example/bai", "concepts": [{"term": "A B", "def": dai}]}]),
        ("thiếu def", "CHAN",
         [{"url": url, "concepts": [{"term": "Chuỗi đảo", "def": ""}]}]),
        ("def cụt hơn ngưỡng", "CHAN",
         [{"url": url, "concepts": [{"term": "Chuỗi đảo", "def": "ngắn quá"}]}]),
        ("term dài quá mức web cắt", "CHAN",
         [{"url": url, "concepts": [{"term": "n" * (MAX_TERM + 1), "def": dai}]}]),
        ("hai term trùng nhau (khác dấu)", "CHAN",
         [{"url": url, "concepts": [{"term": "Răn đe", "def": dai},
                                    {"term": "ran de", "def": dai}]}]),
        ("nhồi quá trần khái niệm/bài", "CHAN",
         [{"url": url, "concepts": [{"term": f"Khái niệm {i}", "def": dai}
                                    for i in range(MAX_CONCEPTS + 1)]}]),
        ("bài không có khái niệm nào", "CHAN",
         [{"url": url, "concepts": []}]),
    ]
    loi = 0
    for mo_ta, ky_vong, lo in CA:
        try:
            kiem_lo(lo, analyses)
            that = "QUA"
        except SystemExit:
            that = "CHAN"
        ok = that == ky_vong
        loi += 0 if ok else 1
        print(f"{'✅' if ok else '❌'} {mo_ta:44} kỳ vọng={ky_vong:4} thật={that}")
    print("\n" + ("TẤT CẢ ĐẠT — guardrail chặn đúng 7 ca xấu, không chặn oan 2 ca sạch"
                 if not loi else f"{loi} CA SAI"))
    return 1 if loi else 0


def main():
    repo = pathlib.Path(__file__).resolve().parent.parent
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    arg = sys.argv[1]
    if arg == "--kiem":
        sys.exit(kiem(repo))
    if arg == "--tu-kiem":
        sys.exit(tu_kiem(repo))
    nap(arg, repo)


if __name__ == "__main__":
    main()
