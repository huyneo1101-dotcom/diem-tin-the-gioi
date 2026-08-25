#!/usr/bin/env python3
"""Dò TOÀN BỘ nguồn: cái nào đọc được bằng RSS, cái nào bằng HTML, cái nào chịu.

Dùng:  python3 scripts/probe_sources.py --json /tmp/probe-local.json
       python3 scripts/probe_sources.py --json docs/probe-ci.json     (chạy trong CI)

VÌ SAO CÓ SCRIPT NÀY (chỉ thị Huy 27/07/2026: "kiểm tra lại toàn bộ các danh sách nguồn xem
cái nào mở được bằng html và cái nào xem được bằng CI chạy ở Mỹ"): môi trường quyết định
nguồn nào sống. Đo thật hôm 27/07:
  - Máy Mac KHÔNG phân giải nổi DNS zone `.mil` (DNSSEC lỗi: EDE(9)/EDE(22)) -> mọi trang
    quân chủng trả `000`, trong khi GitHub runner ở Mỹ phân giải được hết.
  - Ngược lại, một số trang chặn IP datacenter GitHub (403) nhưng mở bình thường từ máy Huy
    (war.gov, spaceforce.mil).
Nghĩa là KHÔNG có một danh sách nguồn đúng cho cả hai nơi. Phải đo ở CẢ HAI rồi hợp nhất.

Phân loại mỗi URL:
  RSS   — tải được và parse ra >=1 <item>/<entry>  -> harvest lớp [RSS] dùng luôn
  HTML  — 200 và body đủ lớn nhưng không phải feed -> harvest lớp [HTML] scrape được
  403   — máy chủ từ chối (WAF/chặn bot)           -> phải qua WebSearch/GNews
  DNS   — không phân giải được tên miền            -> chỉ môi trường khác mới đọc nổi
  LỖI   — timeout / lỗi mạng khác

⚠️ VÁ 30/07/2026 — TRƯỚC ĐÓ SCRIPT NÀY ĐO BẰNG CÔNG CỤ SAI, và đó là lỗi nặng nhất của nó:
nó chỉ gọi `curl` TRẦN, trong khi Akamai/Cloudflare nhận dạng **dấu vân tay TLS (JA3/JA4)** của
curl rồi cắt kết nối. Nên mọi `403` nó ghi ra đều lẫn hai thứ khác hẳn nhau: nguồn bị chặn THẬT,
và nguồn chỉ bị chặn vì công cụ đo. Cái giá đã trả: `docs/probe-ci.json` xếp `pacom.mil`,
`marines.mil`, `navy.mil` vào diện 403 ở CI, rồi bảng CLAUDE.md ghi chúng là "cả hai chịu" và
harvest BỎ chúng — trong khi ở local `curl_cffi` trả 200 cho navy/marines. Một công cụ đo sai
thì đẻ ra kết luận sai hàng loạt, mà bảng vẫn trông như có căn cứ.
Nay mỗi URL nghi bị chặn được **thử lại bậc 2 bằng vân tay Chrome** (`curl_cffi`), đúng cách
`harvest.py` đang đi — kết quả giữ nguyên nhãn `kind` cũ nhưng thêm `qua_van_tay: true` để đọc
được nguồn nào phải nhờ đường đó.

⚠️ Và nguồn nào vẫn hỏng sau bậc 2 thì **đo LẠI LẺ, TUẦN TỰ** (`--workers 1` cho riêng chúng):
vòng dò đa luồng cho kết luận sai — đã vấp thật, `af.mil` và `army.mil` cùng bị chấm `000` khi
dò 8 luồng, đo lẻ thì một cái 200/20 item, cái kia 403. Hai chẩn đoán khác hẳn nhau, và bản đa
luồng sai cả hai.
"""
import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

sys.path.insert(0, str(ROOT / "scripts"))

# Dấu hiệu chặn LẤY TỪ harvest.py, không chép lại: hai bộ luật song song chắc chắn lệch, mà
# lệch âm thầm. Thiếu harvest thì lùi về bộ tối thiểu chứ không tắt phép đo (tắt = câm).
try:
    from harvest import DAU_HIEU_CHAN
except Exception:  # noqa: BLE001
    DAU_HIEU_CHAN = (b"403 forbidden", b"error 403", b"access denied",
                     b"attention required", b"just a moment", b"request forbidden")

# Nhãn kind bị coi là "chưa đọc được" — dùng cho cả bậc 2 lẫn vòng đo lẻ.
KIND_HONG = ("403", "DNS", "LỖI")

_CFFI = None       # None = chưa thử import · False = máy/CI không có curl_cffi
_THIEU_CFFI = []   # sổ ghi vết: URL nghi bị chặn mà không có curl_cffi để thử lại


def nghi_bi_chan(body: bytes) -> bool:
    """403 KHÔNG phải lúc nào cũng lộ ra là rỗng hay ngắn — dò theo DẤU HIỆU, đừng dò theo CỠ.

    Trang lỗi của naval-technology.com dài 19.357 byte và mở đầu bằng `<?xml`, nên bộ parse RSS
    đọc ra 0 item mà không ném lỗi nào; nhìn y hệt nguồn sống mà hôm nay không có bài.
    """
    if not body:
        return True
    dau = body[:3000].lower()
    return any(d in dau for d in DAU_HIEU_CHAN)


def _lay_van_tay(url: str, timeout: int = 25):
    """Thử lại bằng vân tay TLS Chrome. Trả (code, body); (None, b"") nếu không có thư viện.

    Phần gọi curl_cffi cố ý viết riêng thay vì dùng `harvest._lay_bang_van_tay_chrome`: hàm bên
    đó chỉ cần BYTES nên nó nuốt mã trạng thái (trả b"" khi != 200), còn ở đây mã trạng thái
    chính là thứ phải ghi vào bảng. Phần LUẬT (dấu hiệu chặn) vẫn dùng chung ở trên.
    """
    global _CFFI
    if _CFFI is False:
        return None, b""
    if _CFFI is None:
        try:
            from curl_cffi import requests as _r  # noqa: PLC0415
            _CFFI = _r
        except ImportError:
            _CFFI = False
            return None, b""
    try:
        r = _CFFI.get(url, impersonate="chrome", timeout=timeout)
        return str(r.status_code), r.content
    except Exception:  # noqa: BLE001
        return "000", b""


def urls_from(text):
    out = []
    for m in re.finditer(r"https?://[^\s\"'<>)\]|]+", text):
        u = m.group(0).rstrip(".,;").split("?utm_source")[0]
        out.append(u)
    return out


def collect_targets():
    """Gom mọi URL cần dò: bảng RSS + bảng HTML trong CLAUDE.md, và danh sách nguồn chính thức Mỹ."""
    targets = {}

    cm = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    try:
        block = cm[cm.index("## URL RSS"):]
    except ValueError:
        block = ""
    else:
        # Mục nguồn là mục CUỐI file thì không còn tiêu đề `##` nào phía sau — lấy tới hết file
        # (vá 25/08/2026, cùng một lỗ câm với harvest.py::feeds_from_claude_md).
        if "\n## " in block[1:]:
            block = block[: block.index("\n## ", 1)]
    for line in block.split("\n"):
        if not line.startswith("|"):
            continue
        clean = re.sub(r"`[^`]*`", "", line)
        m = re.search(r"https?://\S+", clean)
        if not m:
            continue
        url = m.group(0).rstrip("|").strip()
        name = line.split("|")[1].strip()
        targets.setdefault(url, name or url)

    p = ROOT / "docs" / "nguon-chinh-thuc-my.md"
    if p.exists():
        for u in urls_from(p.read_text(encoding="utf-8", errors="replace")):
            targets.setdefault(u, "nguon-chinh-thuc-my")
    return sorted(targets.items())


def _phan_loai(url, name, code, body, qua_van_tay=False):
    """Xếp một lần tải thành nhãn kind. Dùng CHUNG cho curl trần và cho vân tay Chrome.

    Viết một chỗ để hai bậc không thể lệch nhau về cách phán xét — bậc 2 mà xếp nhãn theo luật
    khác thì so sánh giữa hai bậc thành vô nghĩa.
    """
    size = len(body)
    kw = dict(url=url, name=name, code=code, size=size)
    if qua_van_tay:
        kw["qua_van_tay"] = True
    if code == "200":
        if nghi_bi_chan(body):
            # 200 mà thân mang dấu hiệu chặn: trang challenge/trang lỗi trả mã 200.
            return dict(kind="403", **kw)
        n = 0
        try:
            root = ET.fromstring(body.decode("utf-8", "replace").strip())
            n = sum(1 for e in root.iter() if e.tag.split("}")[-1] in ("item", "entry"))
        except Exception:  # noqa: BLE001
            n = 0
        if n:
            return dict(kind="RSS", items=n, **kw)
        if size > 3000:
            return dict(kind="HTML", **kw)
        return dict(kind="LỖI", **{**kw, "code": "200-rỗng"})
    if code in ("401", "403"):
        return dict(kind="403", **kw)
    return dict(kind="LỖI", **kw)


def probe(item, cho_van_tay=True):
    kq = _probe_curl_tran(item)
    # Bậc 2: chỉ cho nhánh 403/LỖI. KHÔNG cho nhánh DNS — curl_cffi đi cùng resolver hệ thống
    # nên tên miền không phân giải được thì nó cũng hỏng y hệt, thử là tốn thời gian mà không
    # đổi được kết luận.
    if not cho_van_tay or kq["kind"] not in ("403", "LỖI"):
        return kq
    url, name = item
    code2, body2 = _lay_van_tay(url)
    if code2 is None:
        _THIEU_CFFI.append(url)
        return kq
    kq2 = _phan_loai(url, name, code2, body2, qua_van_tay=True)
    # Chỉ nhận bậc 2 khi nó THẬT SỰ tốt hơn, kẻo một lượt hỏng của bậc 2 xoá mất kết quả tốt
    # của bậc 1 (chiều hỏng phải nghiêng về phía giữ nguyên).
    return kq2 if kq2["kind"] in ("RSS", "HTML") else kq


def _probe_curl_tran(item):
    url, name = item
    # KHÔNG dùng -A: một số trang .mil trả 200 với curl mặc định nhưng 403 khi giả trình duyệt
    # (thực tế army.mil). Thử lần 2 kèm UA nếu lần 1 hỏng.
    for flags in ([], ["-A", UA]):
        # `-S` là BẮT BUỘC, đừng gỡ: `-s` một mình triệt tiêu luôn thông báo lỗi ra stderr, nên
        # nhánh nhận nhãn DNS ("Could not resolve host") KHÔNG BAO GIỜ khớp — nó câm từ ngày dựng
        # script. Bằng chứng: cả bản local 27/07 (10 LỖI) lẫn bản CI 30/07 (6 LỖI) đều có ĐÚNG 0
        # mục DNS trên 287 URL, trong khi zone .mil thật sự không phân giải được ở local. Tên
        # miền chết bị dồn vào nhãn LỖI chung với timeout — hai nguyên nhân khác hẳn nhau, mà
        # chữa thì chữa hai hướng khác nhau.
        p = subprocess.run(
            ["curl", "-sSL", "--compressed", "--max-time", "15"] + flags +
            ["-w", "\n__CODE__%{http_code}", url],
            capture_output=True)
        raw = p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        code = "000"
        body = raw
        if "__CODE__" in raw:
            body, _, code = raw.rpartition("\n__CODE__")
        code = code.strip() or "000"
        if code == "000":
            if "Could not resolve host" in err or "Could not resolve host" in raw:
                if flags:
                    return dict(url=url, name=name, kind="DNS", code="000", size=0)
                continue
            if flags:
                return dict(url=url, name=name, kind="LỖI", code="000", size=0)
            continue
        kq = _phan_loai(url, name, code, body.encode("utf-8", "replace"))
        # Giữ nếp cũ: 403 ở lượt không-UA thì thử lại kèm UA trước khi chốt.
        if kq["kind"] == "403" and not flags:
            continue
        return kq
    return dict(url=url, name=name, kind="LỖI", code="000", size=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="PATH", help="ghi kết quả ra JSON")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    targets = collect_targets()
    moi_truong = "CI" if os.environ.get("GITHUB_ACTIONS") else "local"
    print(f"Dò {len(targets)} URL — môi trường: {moi_truong}", file=sys.stderr)

    res = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, r in enumerate(ex.map(probe, targets), 1):
            res.append(r)
            if i % 25 == 0:
                print(f"  ... {i}/{len(targets)}", file=sys.stderr)

    # VÒNG 2 — đo LẠI LẺ, TUẦN TỰ mọi nguồn vừa bị chấm hỏng.
    # Vì sao bắt buộc: dò đa luồng cho kết luận SAI. Đo thật 27/07 — vòng 8 luồng chấm cả
    # `af.mil` lẫn `army.mil` là `000`; đo lẻ thì af.mil ra 200/20 item còn army.mil ra 403.
    # Trước khi gạch tên một nguồn thì phải đo lại lẻ, và ghi rõ "đã thử 2 lần".
    hong = [(i, r) for i, r in enumerate(res) if r["kind"] in KIND_HONG]
    if hong:
        print(f"\nĐo LẠI LẺ {len(hong)} nguồn hỏng (tuần tự, chống kết luận sai do đa luồng)...",
              file=sys.stderr)
        cuu = 0
        for i, r in hong:
            r2 = probe((r["url"], r["name"]))
            r2["da_thu_2_lan"] = True
            if r2["kind"] not in KIND_HONG:
                cuu += 1
                print(f"   CỨU ĐƯỢC: {r['kind']} -> {r2['kind']}  {r['url'][:80]}",
                      file=sys.stderr)
            res[i] = r2
        print(f"   vòng lẻ cứu được {cuu}/{len(hong)} nguồn", file=sys.stderr)

    # Fail-open CÓ TIẾNG: thiếu curl_cffi thì vẫn ra bảng, nhưng phải KÊU — im lặng ở đây là
    # tạo đúng vùng câm mà bản vá bậc 2 sinh ra để bịt, và bảng sẽ ghi "nguồn chết" cho những
    # nguồn chỉ bị chặn vì công cụ đo.
    if _THIEU_CFFI:
        doms = sorted({urllib.parse.urlparse(u).netloc for u in _THIEU_CFFI})
        print(f"\n⚠️  {len(_THIEU_CFFI)} URL ({len(doms)} domain) nghi bị chặn mà máy KHÔNG có "
              f"curl_cffi để thử lại bằng vân tay TLS Chrome.\n"
              f"   Số đo cho những domain này CHƯA kết luận được: {', '.join(doms[:8])}"
              + (" …" if len(doms) > 8 else "")
              + "\n   Cài:  python3 -m pip install --user curl_cffi", file=sys.stderr)

    by = {}
    for r in res:
        by.setdefault(r["kind"], []).append(r)

    print(f"\n=== KẾT QUẢ ({moi_truong}) ===")
    for k in ("RSS", "HTML", "403", "DNS", "LỖI"):
        lst = by.get(k, [])
        print(f"  {k:5s}: {len(lst)}")

    # Nguồn chỉ đọc được nhờ vân tay TLS: phải in ra thành mục riêng, vì đây đúng là nhóm mà
    # bản đo cũ (curl trần) ghi thành "chết" — không in thì bản vá không để lại bằng chứng nào.
    vt = sorted((r for r in res if r.get("qua_van_tay")), key=lambda x: x["url"])
    print(f"\n-- CHỈ đọc được bằng VÂN TAY TLS Chrome ({len(vt)}) --")
    for r in vt:
        extra = f" [{r.get('items')} item]" if r.get("items") else ""
        print(f"   {r['kind']:5s} {urllib.parse.urlparse(r['url']).netloc:30s}{extra} "
              f"{r['url'][:80]}")
    for k in ("RSS", "HTML"):
        print(f"\n-- {k} ({len(by.get(k, []))}) --")
        for r in sorted(by.get(k, []), key=lambda x: x["url"]):
            extra = f" [{r.get('items')} item]" if r.get("items") else ""
            print(f"   {urllib.parse.urlparse(r['url']).netloc:32s}{extra} {r['url'][:88]}")
    for k in ("403", "DNS", "LỖI"):
        doms = sorted(set(urllib.parse.urlparse(r["url"]).netloc for r in by.get(k, [])))
        print(f"\n-- {k}: {len(doms)} domain --")
        for i in range(0, len(doms), 4):
            print("   " + ", ".join(doms[i:i + 4]))

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps({"moi_truong": moi_truong, "ket_qua": res}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\nĐã ghi {len(res)} kết quả ra {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()
