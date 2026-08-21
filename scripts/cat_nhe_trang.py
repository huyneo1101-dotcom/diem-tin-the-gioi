# -*- coding: utf-8 -*-
"""DỰNG BẢN NHẸ của index.html cho GitHub Pages (21/08/2026).

VÌ SAO: `index.html` trên `main` nặng 1.718.169 byte (485 KB sau nén), trong đó riêng
`var DATA` chiếm 1.521.356 byte = 88,5%. Người mở trang phải tải và phân tích toàn bộ kho
lưu trữ — 513 tin Mỹ, 281 tin thế giới, 29 cuộc tập trận kèm `concepts` (157 KB) và
`backgroundDoc` (89 KB), 75 quán cà phê, 3 bản tuần — chỉ để nhìn thấy vài chục dòng của
trang chủ. Trên điện thoại mạng yếu đó là vài giây màn trắng, hai lần mỗi ngày.

CÁCH LÀM — KHÔNG đụng một dòng nào của 21 script Python đang ghi vào index.html:
`index.html` trong repo VẪN là nguồn sự thật, vẫn đủ dữ liệu, mọi script ghi như cũ. Việc
cắt diễn ra ở BƯỚC DỰNG trong `pages.yml`, ngay trước khi đóng gói artifact đẩy lên Pages:

    index.html (đủ)  ──cat_nhe()──►  index.html (lát đầu)  +  data/kho.json (kho đầy đủ)

Trang nạp lát đầu nên hiện chữ ngay, rồi `loadKho()` kéo `data/kho.json` về và vẽ lại.

⛔ HAI RÀO PHẢI GIỮ:
  (1) `analyses` TUYỆT ĐỐI không được vào `kho.json`. Bài think-tank đã tách sang
      `data/analyses.json` từ 30/07/2026 và `loadAnalyses()` gán `DATA.analyses=arr`.
      Hai lời gọi fetch chạy song song; kho.json mang `analyses:[]` là có xác suất ghi đè
      lên kho think-tank vừa nạp — mục Think-tank trống trơn mà KHÔNG có lỗi nào hiện ra.
  (2) Bản đã cắt mang cờ `DATA._nhe=1`. Cắt lần hai trên bản đã cắt sẽ sinh ra kho.json
      chỉ chứa lát đầu, tức MẤT kho — nên `cat_nhe()` chặn cứng ca đó.

Dùng:
    python3 scripts/cat_nhe_trang.py --kiem      # chỉ đo, không ghi
    python3 scripts/cat_nhe_trang.py --tai-cho   # cắt TẠI CHỖ (chỉ dùng trong pages.yml)
    python3 scripts/cat_nhe_trang.py --tu-kiem   # chứng minh các rào bắt được lỗi

⚠️ `--tai-cho` làm hỏng bản làm việc (index.html mất kho). Đừng chạy trên máy Mac rồi
commit — CI checkout bản sạch mỗi lần nên chỉ CI mới được dùng cờ này.
"""
import gzip
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from add_analyses import find_data_span  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
TEN_KHO = "data/kho.json"

# Tin: giữ lại (mọi bài thuộc N ngày nạp gần nhất) ∪ (M bài mới nhất theo `date`).
# Hai vế vì hai phép khác nhau: trang chủ đánh nhãn MỚI theo `_addedDate`, còn phần "hiện 5
# tin gần nhất" khi hôm nay chưa có tin thì sắp theo `date`. Giữ một vế là mục kia trống.
LAT_TIN = {"usNews": (2, 45), "worldNews": (2, 30), "xNews": (2, 15)}
# Chỉ nằm ở tab con, trang chủ không đọc tới → lát đầu để RỖNG.
BO_HAN = ["workCafes", "weeklyArchive", "weeklyReport", "dipEvents", "rejectedNews"]
# Trường nặng của tập trận, chỉ hiện khi mở hồ sơ một cuộc (renderDrillDoc).
EX_BO_TRUONG = ["concepts", "background", "backgroundDoc"]
EX_GIU_ITEM = 1          # trang chủ chỉ cần dòng "Mới nhất:" của cuộc đang diễn ra
KHONG_TACH = ["analyses"]  # xem rào (1) ở đầu file


def _nen(s: str) -> str:
    return f"{len(gzip.compress(s.encode(), 9)):,}"


def lat_tin(arr: list, so_ngay: int, so_bai: int) -> list:
    ngay = sorted({a.get("_addedDate") for a in arr if a.get("_addedDate")}, reverse=True)[:so_ngay]
    giu = {i for i, a in enumerate(arr) if a.get("_addedDate") in ngay}
    thu_tu = sorted(range(len(arr)), key=lambda i: str(arr[i].get("date", "")), reverse=True)
    giu.update(thu_tu[:so_bai])
    return [arr[i] for i in sorted(giu)]   # giữ nguyên thứ tự gốc, web tự sortD


def lat_tap_tran(exs: list) -> list:
    ra = []
    for e in exs:
        e2 = {k: v for k, v in e.items() if k not in EX_BO_TRUONG}
        if "items" in e:
            e2["items"] = sorted(e["items"] or [],
                                 key=lambda x: str(x.get("date", "")), reverse=True)[:EX_GIU_ITEM]
        ra.append(e2)
    return ra


def tach(data: dict) -> tuple[dict, dict]:
    """(lát đầu nhúng trong index.html, kho đầy đủ ra data/kho.json)."""
    if data.get("_nhe"):
        raise SystemExit("LỖI: DATA đã mang cờ _nhe — bản này CẮT RỒI, cắt lần hai là mất kho.")
    dau, kho = dict(data), {}
    for key, (so_ngay, so_bai) in LAT_TIN.items():
        if isinstance(data.get(key), list):
            kho[key] = data[key]
            dau[key] = lat_tin(data[key], so_ngay, so_bai)
    if isinstance(data.get("exercises"), list):
        kho["exercises"] = data["exercises"]
        dau["exercises"] = lat_tap_tran(data["exercises"])
    for key in BO_HAN:
        if key in data:
            kho[key] = data[key]
            dau[key] = [] if isinstance(data[key], list) else {}
    for key in KHONG_TACH:
        kho.pop(key, None)
    dau["_nhe"] = 1
    return dau, kho


def cat_nhe(html: str) -> tuple[str, str]:
    """(html bản nhẹ, nội dung data/kho.json). Thuần tuý — không đụng đĩa, để canary gọi lại."""
    s, e = find_data_span(html)
    dau, kho = tach(json.loads(html[s:e]))
    nen = json.dumps(dau, ensure_ascii=False, separators=(",", ":"))
    return html[:s] + nen + html[e:], json.dumps(kho, ensure_ascii=False, separators=(",", ":"))


def da_cat(html: str) -> bool:
    try:
        s, e = find_data_span(html)
    except (ValueError, IndexError):
        return False
    return bool(json.loads(html[s:e]).get("_nhe"))


def main() -> int:
    tai_cho = "--tai-cho" in sys.argv
    goc = (REPO / "index.html").read_text(encoding="utf-8")
    nhe, kho = cat_nhe(goc)

    a, b = len(goc.encode()), len(nhe.encode())
    print(f"index.html : {a:,} → {b:,} byte  (nén {_nen(goc)} → {_nen(nhe)}, "
          f"bớt {100 - b * 100 // a}%)")
    print(f"{TEN_KHO:11s}: {len(kho.encode()):,} byte (nén {_nen(kho)}) — nạp sau khi trang đã hiện")

    d_kho = json.loads(kho)
    for k in KHONG_TACH:
        if k in d_kho:
            print(f"⛔ '{k}' LỌT vào {TEN_KHO} — sẽ ghi đè kho đã tách riêng. Dừng.")
            return 2
    d_dau = json.loads(nhe[slice(*find_data_span(nhe))])
    for k, v in d_kho.items():
        if isinstance(v, list) and isinstance(d_dau.get(k), list) and len(d_dau[k]) > len(v):
            print(f"⛔ lát đầu '{k}' ({len(d_dau[k])}) nhiều hơn kho ({len(v)}) — sai. Dừng.")
            return 2

    if not tai_cho:
        print("\n(chỉ đo — thêm --tai-cho để ghi thật; chỉ pages.yml mới nên dùng cờ đó)")
        return 0
    (REPO / "index.html").write_text(nhe, encoding="utf-8")
    (REPO / "data").mkdir(parents=True, exist_ok=True)
    (REPO / TEN_KHO).write_text(kho, encoding="utf-8")
    print(f"\nĐÃ GHI TẠI CHỖ: index.html + {TEN_KHO}")
    return 0


# ------------------------------------------------------------------ tự kiểm
def _tu_kiem() -> int:
    goc = (REPO / "index.html").read_text(encoding="utf-8")
    loi = 0

    def bao(dat: bool, nhan: str, them: str = "") -> None:
        nonlocal loi
        print(f"  {'✅' if dat else '❌'} {nhan}" + (f"\n     → {them}" if them and not dat else ""))
        if not dat:
            loi += 1

    nhe, kho = cat_nhe(goc)
    d_goc = json.loads(goc[slice(*find_data_span(goc))])
    d_dau = json.loads(nhe[slice(*find_data_span(nhe))])
    d_kho = json.loads(kho)

    print("=== PHẢI CHO QUA ===")
    bao(len(nhe.encode()) < len(goc.encode()) * 0.35,
        f"bản nhẹ nhỏ hơn 35% bản gốc ({len(nhe.encode()):,}/{len(goc.encode()):,})")
    bao(d_dau.get("_nhe") == 1, "bản nhẹ mang cờ _nhe")
    thieu = [k for k in d_goc if k not in d_dau]
    bao(not thieu, "bản nhẹ giữ đủ MỌI khoá của DATA", f"thiếu {thieu}")
    mat = [k for k, v in d_goc.items()
           if isinstance(v, list) and v and k not in KHONG_TACH
           and not d_dau.get(k) and not d_kho.get(k)]
    bao(not mat, "không khoá nào bốc hơi khỏi cả hai bản", f"mất hẳn: {mat}")
    # đối chứng CHIỀU NỚI: lát đầu phải THẬT SỰ mỏng, không được lặng lẽ giữ gần hết kho
    beo = [k for k, v in LAT_TIN.items()
           if len(d_dau.get(k, [])) > max(v[1] * 2, len(d_goc.get(k, [])) * 0.5)]
    bao(not beo, "lát đầu của tin vẫn mỏng (canh chiều nới ngưỡng)", f"phình: {beo}")
    # trang chủ phải có chữ ngay: đủ tin để 3 mục lùi về "5 tin gần nhất"
    bao(len(d_dau.get("usNews", [])) >= 20 and len(d_dau.get("worldNews", [])) >= 15,
        f"lát đầu đủ tin cho trang chủ (us {len(d_dau.get('usNews', []))}, "
        f"world {len(d_dau.get('worldNews', []))})")
    bao(all(e.get("name") and e.get("dates") is not None for e in d_dau.get("exercises", [])),
        "lát đầu tập trận còn tên và dải ngày (dải điểm nhấn trang chủ đọc chúng)")
    # phần tử của lát đầu phải LÀ phần tử của kho, không được bịa
    lech = [k for k in LAT_TIN
            if any(json.dumps(x, sort_keys=True) not in
                   {json.dumps(y, sort_keys=True) for y in d_kho.get(k, [])}
                   for x in d_dau.get(k, []))]
    bao(not lech, "mọi bài ở lát đầu đều có trong kho", f"lệch: {lech}")

    print("\n=== PHẢI CHẶN ===")
    for nhan, lam in (
        ("HTML không có var DATA", lambda: cat_nhe("<html>không có gì</html>")),
        ("cắt lần hai trên bản đã cắt", lambda: cat_nhe(nhe)),
    ):
        try:
            lam()
            bao(False, nhan, "LỌT — không chặn")
        except (SystemExit, ValueError, IndexError):
            bao(True, nhan)

    print("\n=== BẢN HỎNG (gỡ đúng một rào, ca tương ứng phải báo không đạt) ===")
    # (1) gỡ rào loại `analyses` khỏi kho
    d2 = dict(d_goc)
    d2.pop("_nhe", None)
    _, kho2 = tach(d2)
    kho2["analyses"] = [{"url": "x"}]
    bao("analyses" in kho2 and main_bat_analyses(kho2),
        "rào (1): kho mang analyses thì phép kiểm bắt được")
    # (2) lát tin trả rỗng = trang chủ trắng
    that = lat_tin(d_goc["usNews"], 2, 45)
    bao(bool(that) and not lat_tin([], 2, 45),
        f"rào (2): lat_tin trên kho thật trả {len(that)} bài, trên mảng rỗng trả 0")

    print()
    print("TỰ KIỂM ĐẠT" if not loi else f"✗ {loi} ca SAI")
    return 1 if loi else 0


def main_bat_analyses(kho: dict) -> bool:
    """Đúng phép kiểm mà main() dùng, tách ra để tự kiểm gọi lại được."""
    return any(k in kho for k in KHONG_TACH)


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        raise SystemExit(_tu_kiem())
    raise SystemExit(main())
