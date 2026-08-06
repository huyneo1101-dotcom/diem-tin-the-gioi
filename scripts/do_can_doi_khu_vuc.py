#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canh hai nguyên nhân làm bốn khu vực gần như TRẮNG BÀI trong mục Think-tank.

VÌ SAO CÓ PHÉP ĐO NÀY. Ngày 06/08/2026 Huy hỏi *"tại sao mục think-tank trên web ít bài Nam Á,
châu Phi, Trung Á và Bắc Cực thế"*. Đo trên kho 616 bài hôm đó: Châu Âu/NATO 188 · Đông Á 174 ·
Ấn Độ Dương-TBD 134, trong khi **Châu Phi 07 · Bắc Cực 04 · Nam Á 01 · Trung Á 01**. Truy ra
HAI nguyên nhân chồng nhau, và nguyên nhân thứ hai che mất nguyên nhân thứ nhất:

  (1) NGUỒN — bảng `THINKTANK_FEEDS` + `THINKTANK_HTML` không có viện chuyên nào của Nam Á và
      Bắc Cực; bốn vùng ấy chỉ có bài khi một viện Anh-Mỹ-Úc tình cờ viết tới.
  (2) NHÃN — kho **CÓ** 27 bài thật về Ấn Độ/Pakistan, nhưng 16 bài mang nhãn `Ấn Độ Dương -
      Thái Bình Dương` và chỉ **01** mang nhãn `Nam Á`. Nội dung có sẵn, chỉ là không hiện ở
      mục người đọc đang mở.

Cơ chế gây vấp, và đây mới là phần đáng sợ: **cả hai đều không phát ra dấu hiệu nào.** Mục
Think-tank vẫn có bài mới mỗi sáng, `--candidates` vẫn đầy ứng viên, không cổng nào đỏ. Chúng
chỉ lộ ra khi Huy tự mở web rồi tự hỏi. Vá tay bốn vùng hôm nay không chặn được vùng thứ năm
mai mốt — nó sẽ hỏng y hệt, cùng một cách, và cũng im lặng y hệt.

    python3 scripts/do_can_doi_khu_vuc.py             # báo cáo; mã 3 khi nhánh NHÃN kêu
    python3 scripts/do_can_doi_khu_vuc.py --tu-kiem   # chứng minh phép đo BẮT ĐƯỢC lỗi

PHÉP ĐO NHÁNH NHÃN. Với mỗi khu vực có bảng từ khoá tin được, đếm hai con số trên kho:
  (a) số bài MANG nhãn đó;
  (b) số bài mà **TIÊU ĐỀ** nhắc tới vùng đó theo bảng từ khoá.
Tỉ lệ a/b tụt dưới `NGUONG_TY_LE` (và b đủ `NGUONG_BAI`) ⇒ KÊU, kèm danh sách bài nghi gán
nhãn quá rộng.

⚠️ CHỈ SOI TIÊU ĐỀ, KHÔNG SOI `summary`/`takeaway` — đã thử và LOẠI. Quét cả phần tóm tắt thì
"nói về vùng" biến thành "có nhắc tới vùng": Nam Á vọt từ 35 lên 76 bài, Trung Đông từ 47 lên
131, vì một bài Nga-Ukraine nhắc Iran một câu cũng bị tính. Kêu ở mức đó là kêu oan hàng loạt,
mà bảng bị kêu oan vài lần thì hết được đọc. Tiêu đề thì nói lên chủ đề chính.

⚠️ NGƯỠNG LẤY TỪ SỐ ĐO, KHÔNG TỪ MONG MUỐN (đo 06/08/2026, hai kho thật):

    khu vực      kho CŨ (656 bài, trước khi vá)   kho NAY (733 bài, sau khi vá)
    Nam Á        1 nhãn / 15 tiêu đề = 0,07       16 / 35 = 0,46
    Trung Á      1 / 4  = 0,25                     8 / 8  = 1,00
    Bắc Cực      4 / 5  = 0,80                     4 / 5  = 0,80
    Châu Phi     7 / 8  = 0,88                     9 / 10 = 0,90
    Trung Đông   52 / 41 = 1,27                    57 / 47 = 1,21
    Châu Mỹ      10 / 3 = 3,33                     11 / 3 = 3,67

`NGUONG_TY_LE = 0,35` nằm giữa khoảng trũng 0,25 ↔ 0,46, cách đều hai bên. Nghiệm thu: cổng
**ĐỎ** trên kho cũ (Nam Á 0,07) và **IM** trên kho nay. Đổi ngưỡng thì phải đo lại cả hai kho
rồi sửa bảng này — bảng này là dòng khai HIỆN HÀNH, không phải nhật ký.

⚠️ TỈ LỆ CÓ THỂ VƯỢT 1,0 và đó là bình thường: bài về vùng đó mà tiêu đề không gọi tên vùng
(Châu Mỹ 3,67). Chỉ chiều TỤT mới là dấu hiệu nhãn bị hút đi, nên cổng cố ý chỉ canh một chiều.

PHÉP ĐO NHÁNH NGUỒN. Khu vực nào không có feed/trang HTML nào khai nhãn khớp nó ⇒ KÊU VÀNG.
**Cố ý KHÔNG đưa vào mã thoát**: Bắc Cực không vá được (viện chuyên duy nhất
`thearcticinstitute.org` chặn theo vân tay TLS ở mọi bậc của thang `congcu/lay_trang.py`, chỉ
còn đường trình duyệt mà trình duyệt chỉ có ở phiên local), nên để nó ĐỎ là đỏ vĩnh viễn — và
bảng đỏ vĩnh viễn thì hết được đọc, lúc nhánh NHÃN kêu thật cũng không ai thấy.

⚠️ BA CÁI BẪY CÙNG MỘT HỌ — tên vùng NHỎ nằm lọt trong tên vùng LỚN. Cả ba đều làm phép đo sai
trong im lặng, và cả ba đều đã có ca test riêng:
  · `Ấn Độ` khớp trong `Ấn Độ Dương` — đếm thô ra 52 bài thay vì 27, dẫn thẳng tới kết luận sai
    *"19 bài Ấn Độ bị gán nhầm Đông Á"*;
  · `Nam Á` khớp trong `Đông Nam Á` — bắt được lúc dựng chính file này, làm 2 bài Đông Nam Á
    lọt vào nhóm Nam Á;
  · cùng chuỗi đó ở NHÁNH NGUỒN: nhãn nguồn `Đông Nam Á` (Fulcrum) và `Đông Á · Đông Nam Á`
    (East Asia Forum) làm Nam Á tưởng đã có nguồn ⇒ cổng câm đúng chỗ đau nhất.
Vì thế mọi biểu thức phải neo bằng lookahead/lookbehind, và **cấm dùng cụm trần** (`á`, `mỹ`).

⚠️ CHUẨN HOÁ NFC TRƯỚC MỌI PHÉP SO KHỚP TIẾNG VIỆT. Bài do người dán tay từ macOS/Word vào kho
ra dạng NFD (dấu thanh tách rời) — trông y hệt, khác byte, nên so khớp trượt câm.

GIỚI HẠN, đừng đọc bảng sạch thành "mọi khu vực đã cân đối": phép đo chỉ phủ những vùng có
bảng từ khoá tin được. `Toàn cầu` · `Châu Âu/NATO` · `Đông Á` · `Ấn Độ Dương - Thái Bình Dương`
nằm NGOÀI (xem `KHONG_DO`) — chúng là vùng LỚN, chính là bên HÚT nhãn chứ không phải bên bị
hút, và không có bộ từ khoá nào khoanh được chúng mà không nuốt nửa kho.
"""
import collections
import importlib.util
import json
import os
import pathlib
import re
import sys
import unicodedata

sys.dont_write_bytecode = True

REPO = pathlib.Path(__file__).resolve().parent.parent
KHO = pathlib.Path(os.environ.get("DO_KHU_VUC_KHO", REPO / "data" / "analyses.json"))
ADD_ANALYSES = pathlib.Path(
    os.environ.get("ADD_ANALYSES", REPO / "scripts" / "add_analyses.py"))

# Số bài tiêu đề tối thiểu mới kết luận. Dưới ngưỡng thì tỉ lệ là nhiễu thuần: 1 nhãn / 2 tiêu
# đề ra 0,50 mà chẳng nói lên gì. Đo 06/08: Trung Á kho cũ chỉ 4 tiêu đề nên rơi dưới ngưỡng —
# chấp nhận bỏ sót nó, vì Nam Á (15 tiêu đề) đã đủ làm cổng đỏ trên kho cũ.
NGUONG_BAI = 5

# Dòng khai HIỆN HÀNH của ngưỡng tỉ lệ — sửa ĐÚNG dòng này khi đo lại, đừng sửa bảng số đo
# trong docstring (bảng đó là nhật ký hai kho).
NGUONG_TY_LE = 0.35

# Khu vực CỐ Ý không đo, kèm lý do. Đây là các vùng LỚN — bên HÚT nhãn, không phải bên bị hút.
KHONG_DO = {
    "Toàn cầu": "không có tên riêng nào để khoanh — mọi bài đều 'toàn cầu' ở mức nào đó",
    "Châu Âu/NATO": "vùng lớn, bên hút nhãn; bộ từ khoá đủ rộng để khoanh nó sẽ nuốt nửa kho",
    "Đông Á": "như trên",
    "Ấn Độ Dương - Thái Bình Dương": "như trên — và chính là nhãn đã hút mất bài Nam Á",
}

# Từ khoá nhận diện vùng trong TIÊU ĐỀ. Mọi biểu thức so trên chuỗi đã chuẩn hoá NFC + hạ chữ.
# ⚠️ Neo bằng lookahead/lookbehind ở đúng ba chỗ tên-nhỏ-nằm-trong-tên-lớn (xem docstring).
# ⚠️ `\bmali\b` phải có word boundary: "soMALIa" chứa nguyên chuỗi "mali".
# ⚠️ Cố ý KHÔNG có `georgia` cho Trung Á — trùng bang Georgia của Mỹ.
TU_KHOA_KHU_VUC = {
    "Nam Á": [
        r"ấn độ(?![\s-]*dương)", r"\bindia\b", r"\bindian\b", r"pakistan", r"bangladesh",
        r"sri lanka", r"\bnepal", r"maldives", r"afghanistan", r"new delhi", r"islamabad",
        r"kashmir", r"(?<!đông )nam á", r"south asia",
    ],
    "Trung Á": [
        r"kazakh", r"uzbek", r"turkmen", r"kyrgyz", r"tajik", r"caucasus", r"kavkaz",
        r"trung á", r"azerbaijan", r"armenia", r"central asia",
    ],
    "Bắc Cực": [
        r"bắc cực", r"arctic", r"greenland", r"svalbard", r"northern sea route",
    ],
    "Châu Phi": [
        r"châu phi", r"africa", r"sahel", r"\bmali\b", r"nigeria", r"ethiopia", r"somalia",
        r"\bsudan", r"\bcongo", r"\bkenya", r"\bniger\b", r"burkina",
    ],
    "Châu Mỹ": [
        r"mỹ latinh", r"latin america", r"brazil", r"mexico", r"argentina", r"venezuela",
        r"colombia", r"\bchile", r"caribbean", r"caribe",
    ],
    "Trung Đông": [
        r"trung đông", r"middle east", r"israel", r"\biran", r"saudi", r"ả rập", r"\bqatar",
        r"\buae\b", r"\bsyria", r"\biraq", r"lebanon", r"\byemen", r"\bgaza", r"hezbollah",
        r"\bhouthi",
    ],
}

# Cụm nhận diện vùng trong NHÃN của nguồn (`THINKTANK_FEEDS` cột 3 · `THINKTANK_HTML` cột 4).
# Nhãn ở đó là chữ tự do do người khai ("Ấn Độ Dương - TBD", "Bắc Âu · Bắc Cực") chứ không phải
# giá trị trong `VALID_REGIONS`, nên phải có bảng ánh xạ riêng — đừng so thẳng hai bên.
# ⚠️ `nam á` neo lookbehind y như nhánh nhãn: `Đông Nam Á` của Fulcrum không được tính thành
# nguồn Nam Á, nếu không cổng câm đúng vùng thiếu nguồn nhất.
CUM_NGUON = {
    "Nam Á": [r"(?<!đông )nam á", r"south asia", r"\bấn độ(?![\s-]*dương)"],
    "Trung Á": [r"trung á", r"central asia", r"caucasus", r"kavkaz"],
    "Bắc Cực": [r"bắc cực", r"arctic"],
    "Châu Phi": [r"châu phi", r"africa", r"sahel"],
    "Châu Mỹ": [r"châu mỹ", r"mỹ latinh", r"latin america"],
    "Trung Đông": [r"trung đông", r"middle east", r"vùng vịnh", r"\bgulf\b"],
    "Toàn cầu": [r"toàn cầu", r"global"],
    "Châu Âu/NATO": [r"châu âu", r"đông âu", r"bắc âu", r"baltic", r"\bnato\b", r"\bnga\b",
                     r"\banh\b", r"xuyên đại tây dương", r"europe"],
    "Đông Á": [r"đông á", r"trung quốc", r"china", r"nhật bản", r"japan", r"biển đông"],
    "Ấn Độ Dương - Thái Bình Dương": [r"ấn độ dương", r"\btbd\b", r"indo-pacific", r"\búc\b",
                                      r"đông nam á"],
}

# Vùng ĐÃ SOI TẬN NƠI ở nhánh NHÃN — kèm lý do, để lần chạy sau không kêu lại. Đây là chỗ ghi
# kết quả triage, KHÔNG phải chỗ giấu vùng khó: mỗi dòng phải nói được đã soi cái gì.
NHAN_DA_DUYET = {}

# Như trên, cho nhánh NGUỒN. Nhánh này vốn chỉ in VÀNG nên bảng dùng để tắt tiếng vùng đã kết
# luận là không vá được, khỏi đọc lại mỗi lần.
NGUON_DA_DUYET = {
    "Bắc Cực":
        "SOI 06/08/2026 — KHÔNG vá được bằng nguồn chuyên. Viện chuyên duy nhất "
        "`thearcticinstitute.org` trượt HẾT mọi bậc thang `congcu/lay_trang.py`, chỉ còn "
        "đường trình duyệt (local-only, cắm vào là local và CI ra kết quả khác nhau). "
        "`highnorthnews` · `thebarentsobserver` · `arctictoday` sống nhưng là BÁO, không phải "
        "viện. Đang bù bằng FIIA + ICDS (hai viện Bắc Âu có mảng Bắc Cực).",
}


def nfc(s):
    """Chuẩn hoá NFC rồi hạ chữ. Bài dán tay từ macOS/Word vào kho ra dạng NFD — trông y hệt,
    khác byte, nên mọi phép so khớp tiếng Việt phải đi qua đây."""
    return unicodedata.normalize("NFC", s or "").lower()


def _bien_dich(bang):
    return {k: [re.compile(p, re.I) for p in v] for k, v in bang.items()}


MAU_KHU_VUC = _bien_dich(TU_KHOA_KHU_VUC)
MAU_NGUON = _bien_dich(CUM_NGUON)


def doc_kho(duong: pathlib.Path):
    """Đọc kho bài. Hỏng thì KÊU chứ không trả rỗng — kho rỗng và kho không đọc được cho ra
    cùng một bảng sạch, mà đó là hai chuyện khác hẳn nhau."""
    try:
        d = json.loads(duong.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"✗ Không có kho bài: {duong}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print(f"✗ Kho bài hỏng JSON ({duong}): {e}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(d, list):
        print(f"✗ Kho bài phải là một MẢNG, đọc ra {type(d).__name__}: {duong}", file=sys.stderr)
        raise SystemExit(2)
    return d


def nhan_nguon():
    """Tập nhãn khu vực đang khai trong bảng nguồn (feed + trang HTML), đã chuẩn hoá."""
    spec = importlib.util.spec_from_file_location("aa_do_khu_vuc", ADD_ANALYSES)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ra = [nfc(hang[2]) for hang in mod.THINKTANK_FEEDS]
    ra += [nfc(hang[3]) for hang in mod.THINKTANK_HTML]
    return ra


def do_nhan(bai):
    """{khu vực: (số bài mang nhãn, số bài tiêu đề nhắc tới, [bài lệch])} cho vùng có đo."""
    mang = collections.Counter(nfc((b or {}).get("region")) for b in bai)
    ra = {}
    for kv, mau in MAU_KHU_VUC.items():
        noi = [b for b in bai if any(m.search(nfc((b or {}).get("title"))) for m in mau)]
        lech = [b for b in noi if nfc(b.get("region")) != nfc(kv)]
        ra[kv] = (mang.get(nfc(kv), 0), len(noi), lech)
    return ra


def nhan_keu(bai):
    """[(khu vực, số nhãn, số tiêu đề, tỉ lệ, [bài lệch])] — vùng nhãn bị hút đi."""
    ra = []
    for kv, (a, n, lech) in do_nhan(bai).items():
        # `max(..., 1)` không phải để cho gọn: vùng 0 bài tiêu đề thì tỉ lệ vô định, và phép
        # chia phía dưới sẽ ném ZeroDivisionError. Trước khi vá, chỗ này chỉ được che GIÁN TIẾP
        # bởi việc `NGUONG_BAI` tình cờ ≥ 1 — hạ ngưỡng là cả script sập, tức một phép đo tưởng
        # là an toàn lại phụ thuộc vào giá trị của một hằng số khác. Bản hỏng "nới ngưỡng số
        # bài về 0" lộ ra đúng lỗ này lúc dựng.
        if n < max(NGUONG_BAI, 1):
            continue
        ty = a / n
        if ty < NGUONG_TY_LE:
            ra.append((kv, a, n, ty, lech))
    ra.sort(key=lambda x: x[3])
    return ra


def nguon_thieu(nhan=None):
    """[khu vực] không có nguồn nào khai nhãn khớp. Vùng ngoài `CUM_NGUON` thì không kết luận
    được nên bỏ qua — im khác hẳn 'đã kiểm và thấy đủ'."""
    co = nhan_nguon() if nhan is None else [nfc(x) for x in nhan]
    ra = []
    for kv, mau in MAU_NGUON.items():
        if not any(m.search(x) for x in co for m in mau):
            ra.append(kv)
    return ra


def bao_cao(kho=None):
    bai = doc_kho(kho or KHO)
    print(f"=== CÂN ĐỐI KHU VỰC MỤC THINK-TANK ({len(bai)} bài) ===\n")

    print(f"① NHÁNH NHÃN — nhãn vùng nhỏ có bị nhãn vùng lớn hút đi không "
          f"(ngưỡng tỉ lệ {NGUONG_TY_LE} · tối thiểu {NGUONG_BAI} bài)")
    do = do_nhan(bai)
    for kv, (a, n, _) in sorted(do.items(), key=lambda x: (x[1][0] / x[1][1]) if x[1][1] else 9):
        ty = f"{a / n:.2f}" if n else "  — "
        co = "" if n >= NGUONG_BAI else f"   (dưới {NGUONG_BAI} bài, không kết luận)"
        print(f"    {kv:12s} nhãn {a:4d} · tiêu đề {n:4d} · tỉ lệ {ty}{co}")
    for kv, ly_do in KHONG_DO.items():
        print(f"    {kv:12s} — KHÔNG ĐO: {ly_do}")

    keu = [x for x in nhan_keu(bai) if x[0] not in NHAN_DA_DUYET]
    if keu:
        for kv, a, n, ty, lech in keu:
            print(f"\n  ✗ {kv}: chỉ {a} bài mang nhãn trong khi {n} bài có tiêu đề nói về vùng "
                  f"này (tỉ lệ {ty:.2f} < {NGUONG_TY_LE}). Nhãn đang bị hút về vùng lớn.")
            dem = collections.Counter(b.get("region") or "(rỗng)" for b in lech)
            print(f"     Nhãn của {len(lech)} bài lệch: "
                  + " · ".join(f"{k} ({v})" for k, v in dem.most_common(5)))
            for b in lech[:12]:
                print(f"       [{b.get('region')}] "
                      + unicodedata.normalize('NFC', b.get('title') or '')[:88])
            if len(lech) > 12:
                print(f"       … và {len(lech) - 12} bài nữa")
    else:
        print("\n  ✓ Không vùng nào có nhãn bị hút đi quá ngưỡng.")

    thieu = nguon_thieu()
    print(f"\n② NHÁNH NGUỒN — khu vực nào chưa có viện chuyên trong bảng nguồn "
          f"(VÀNG, KHÔNG vào mã thoát)")
    if thieu:
        for kv in thieu:
            print(f"    ⚠️ {kv}: không feed/trang HTML nào khai nhãn khớp vùng này")
            if kv in NGUON_DA_DUYET:
                print(f"       ↳ đã soi: {NGUON_DA_DUYET[kv]}")
        con = [k for k in thieu if k not in NGUON_DA_DUYET]
        if con:
            print(f"    Việc phải làm cho {' · '.join(con)}: tìm viện chuyên của vùng, đọc thẻ "
                  f"<link rel=\"alternate\"> lấy feed (đường đã tìm ra feed RUSI và CACI), khai "
                  f"vào THINKTANK_FEEDS. Không có thì ghi một dòng NGUON_DA_DUYET kèm lý do.")
    else:
        print("    ✓ Mọi khu vực đều có ít nhất một nguồn khai nhãn khớp.")

    if keu:
        print("\n   Việc phải làm cho nhánh ①: mở các bài lệch, sửa `region` về vùng hẹp khi "
              "vùng đó là chủ đề chính. Bài quan hệ SONG PHƯƠNG (Úc-Ấn, Nhật-Ấn) mang nhãn "
              "vùng của đối tác là hợp lệ — soi xong mà kết luận nhãn đang đúng thì ghi một "
              "dòng NHAN_DA_DUYET kèm lý do.")
        return 3
    return 0


# ─────────────────────────── tự kiểm ───────────────────────────

def _bai(tieu_de, region):
    return {"title": tieu_de, "region": region, "url": "https://x.org/a"}


def _kho_gia(rows):
    """rows = [(tiêu đề, region, số bản)] -> danh sách bài giả."""
    ra = []
    for td, rg, n in rows:
        ra += [_bai(f"{td} {i}", rg) for i in range(n)]
    return ra


def cac_ca():
    """[(tên ca, đạt, lời)] — ca có ★ là ca PHẢI KÊU."""
    ra = []

    # ── 01 ★ đúng hình dạng lỗ Nam Á: 15 bài tiêu đề nói về vùng, chỉ 1 mang nhãn
    kho = _kho_gia([("Ấn Độ và Pakistan đàm phán", "Ấn Độ Dương - Thái Bình Dương", 14),
                    ("Pakistan tăng chi quốc phòng", "Nam Á", 1)])
    k = [x[0] for x in nhan_keu(kho)]
    ra.append(("★ 01 nhãn bị hút — 1/15 bài mang nhãn Nam Á ⇒ phải kêu",
               k == ["Nam Á"], f"không kêu Nam Á, kêu: {k}"))

    # ── 02 đối chứng chống kêu oan: tỉ lệ đủ cao thì im
    kho = _kho_gia([("Ấn Độ và Pakistan đàm phán", "Nam Á", 8),
                    ("Ấn Độ tăng chi quốc phòng", "Ấn Độ Dương - Thái Bình Dương", 4)])
    ra.append(("02 đối chứng — 8/12 mang nhãn đúng (0,67) ⇒ KHÔNG kêu",
               not nhan_keu(kho), f"kêu oan vùng đã cân đối: {nhan_keu(kho)}"))

    # ── 03 đối chứng chống siết quá tay: dưới ngưỡng số bài thì không kết luận
    # ⚠️ GHIM CỨNG số 4, tuyệt đối đừng viết `NGUONG_BAI - 1`: ca neo động theo chính hằng số
    # nó đo thì bản hỏng nới ngưỡng về 0 cũng kéo kho thử về rỗng, ca vẫn xanh và ngưỡng mất
    # người canh. Đã vấp đúng thế lúc dựng (mục 25 CLAUDE.md toàn cục).
    kho = _kho_gia([("Pakistan mua tiêm kích", "Đông Á", 4)])
    ra.append((f"03 đối chứng — 4 bài (dưới ngưỡng {NGUONG_BAI}) ⇒ KHÔNG kêu",
               not nhan_keu(kho), f"kêu oan vùng dưới ngưỡng: {nhan_keu(kho)}"))

    # ── 04 ★ BẪY: `Ấn Độ` khớp trong `Ấn Độ Dương`. Đếm thô ra 52 thay vì 27 bài, dẫn thẳng
    #    tới kết luận sai "19 bài Ấn Độ bị gán nhầm Đông Á".
    kho = _kho_gia([("An ninh Ấn Độ Dương và cán cân quyền lực", "Đông Á", 20)])
    ra.append(("★ 04 bẫy — `Ấn Độ Dương` KHÔNG được đếm thành bài Nam Á",
               do_nhan(kho)["Nam Á"][1] == 0,
               f"đếm nhầm {do_nhan(kho)['Nam Á'][1]} bài Ấn Độ Dương thành Nam Á"))

    # ── 05 ★ BẪY cùng họ: `Nam Á` khớp trong `Đông Nam Á`. Bắt được lúc dựng chính file này.
    kho = _kho_gia([("Bộ công cụ ứng phó khủng hoảng của Đông Nam Á", "Đông Á", 20)])
    ra.append(("★ 05 bẫy — `Đông Nam Á` KHÔNG được đếm thành bài Nam Á",
               do_nhan(kho)["Nam Á"][1] == 0,
               f"đếm nhầm {do_nhan(kho)['Nam Á'][1]} bài Đông Nam Á thành Nam Á"))

    # ── 06 đối chứng chống NỚI quá tay của ca 04+05: `Ấn Độ` thật vẫn phải đếm được
    kho = _kho_gia([("Xuất khẩu quốc phòng Ấn Độ tăng mạnh", "Đông Á", 6)])
    ra.append(("06 đối chứng — `Ấn Độ` thật VẪN phải đếm là bài Nam Á",
               do_nhan(kho)["Nam Á"][1] == 6,
               f"lọc quá tay, mất bài Ấn Độ thật: {do_nhan(kho)['Nam Á'][1]}/6"))

    # ── 07 ★ BẪY nhánh NGUỒN, cùng chuỗi: nhãn nguồn `Đông Nam Á` không phải nguồn Nam Á
    ra.append(("★ 07 bẫy nguồn — nhãn `Đông Nam Á` KHÔNG tính là có nguồn Nam Á",
               "Nam Á" in nguon_thieu(["Đông Nam Á", "Đông Á · Đông Nam Á"]),
               "Fulcrum/East Asia Forum bị đọc thành nguồn Nam Á ⇒ cổng câm đúng vùng thiếu"))

    # ── 08 đối chứng nguồn chống nới tay của ca 07: nhãn `Nam Á` thật phải được nhận
    ra.append(("08 đối chứng — nhãn nguồn `Nam Á` thật ⇒ KHÔNG báo thiếu",
               "Nam Á" not in nguon_thieu(["Nam Á", "Đông Nam Á"]),
               "lọc quá tay, nguồn Nam Á thật vẫn bị báo thiếu"))

    # ── 09 ★ NFD: bài dán tay từ macOS/Word ra dạng NFD — trông y hệt, khác byte
    nfd = unicodedata.normalize("NFD", "Nam Á")
    kho = _kho_gia([(unicodedata.normalize("NFD", "Pakistan và Ấn Độ đàm phán"), nfd, 8)])
    ra.append(("★ 09 NFD — nhãn và tiêu đề dạng NFD vẫn phải khớp",
               do_nhan(kho)["Nam Á"] [:2] == (8, 8),
               f"NFD trượt câm: {do_nhan(kho)['Nam Á'][:2]} (phải là (8, 8))"))

    # ── 10 ★ CA VÀNG ĐẢO trên kho THẬT: gỡ hết nhãn Nam Á ⇒ phải kêu. Tất định, không phụ
    #    thuộc kho cũ trong git, mà vẫn chạy trên dữ liệu thật.
    that = doc_kho(KHO)
    goc = [dict(b, region="Đông Á") if nfc(b.get("region")) == nfc("Nam Á") else b
           for b in that]
    ra.append(("★ 10 ca vàng đảo — kho THẬT bị gỡ hết nhãn Nam Á ⇒ phải kêu",
               "Nam Á" in [x[0] for x in nhan_keu(goc)],
               "gỡ sạch nhãn Nam Á khỏi kho thật mà cổng vẫn im — phép đo mất răng"))

    # ── 11 ★ CA VÀNG trên kho THẬT: hiện không vùng nào được phép kêu
    con = [x[0] for x in nhan_keu(that) if x[0] not in NHAN_DA_DUYET]
    ra.append(("★ 11 ca vàng — kho THẬT không còn vùng nào chưa soi", not con,
               "chưa soi: " + " · ".join(con) + " — sửa `region` các bài lệch, hoặc ghi một "
               "dòng NHAN_DA_DUYET kèm lý do đã soi"))

    # ── 12 ★ kho hỏng phải KÊU, không được trả bảng sạch
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        xau = pathlib.Path(t) / "hong.json"
        xau.write_text('{"analyses": []}', encoding="utf-8")
        try:
            doc_kho(xau)
            ok = False
        except SystemExit as e:
            ok = e.code == 2
    ra.append(("★ 12 kho không phải MẢNG ⇒ kêu mã 2, không trả bảng sạch", ok,
               "kho hỏng bị nuốt — kho rỗng và kho không đọc được ra cùng một bảng"))
    return ra


def tu_kiem_chay():
    ra = cac_ca()
    hong = 0
    for ten, dat, loi in ra:
        print(("  ✓ " if dat else "  ✗ ") + ten + ("" if dat else "  — " + loi))
        hong += 0 if dat else 1
    print(f"\n{len(ra) - hong}/{len(ra)} ca đạt" + ("" if not hong else f" · {hong} KHÔNG ĐẠT"))
    return 1 if hong else 0


def tu_kiem():
    """Dựng bản CHÍNH FILE NÀY đã gỡ đúng một lớp vá, rồi chứng minh ca tương ứng ĐỎ."""
    import hashlib
    import subprocess
    # Import TRONG hàm: file này chạy được cả ở nơi không có `~/Claude/HeThong` (chỉ `--tu-kiem`
    # mới cần), nên phụ thuộc ngoài repo không được đứng ở đầu file.
    sys.path.insert(0, "/Users/Huy/Claude/HeThong")
    from khung_tu_kiem import LoiNeo, neo_hai_dong

    goc = pathlib.Path(__file__).read_text(encoding="utf-8")
    if tu_kiem_chay():
        print("\n✗ TRƯỢT: bộ ca đã ĐỎ trên bản ĐÚNG — sửa chỗ đó trước, dựng bản hỏng lúc "
              "này không chứng minh được gì.")
        return 1
    tong = 0
    for ten, tim, thay, ca_do in BAN_HONG:
        try:
            tim, thay = neo_hai_dong(goc, tim, thay)
        except LoiNeo as e:
            print(f"  ✗ {ten} — {e}")
            tong += 1
            continue
        noi = goc.replace(tim, thay, 1)
        # Bản hỏng phải nằm CÙNG thư mục `scripts/` (nó suy REPO từ vị trí chính nó), và tên
        # mang PID + sha1 nội dung: hai phiên chạy chồng thì không xoá bản hỏng của nhau, và
        # hai bản hỏng cùng giây không dính lại `.pyc` của bản trước (mục 17 CLAUDE.md).
        dich = pathlib.Path(__file__).parent / ("_thu-hong-%d-%s-%s" % (
            os.getpid(), hashlib.sha1(noi.encode()).hexdigest()[:8], pathlib.Path(__file__).name))
        dich.write_text(noi, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(dich), "--ca"],
                               capture_output=True, text=True)
            do = [ln for ln in r.stdout.splitlines() if ln.startswith("  ✗")]
            tong_ca = len([l for l in r.stdout.splitlines() if l.startswith(("  ✓", "  ✗"))])
            # Bản hỏng làm tiến trình CHẾT thì stdout không có dòng ca nào, và nếu chỉ đọc
            # danh sách ca đỏ thì nó hiện ra thành "đỏ thực tế: KHÔNG CÓ" — nghe y như phép đo
            # không có răng, trong khi nguyên nhân thật là ngoại lệ chưa bắt. Mất 3 lượt chẩn
            # đoán sai hướng lúc dựng vì đúng chỗ này, nên nhánh ấy phải tự khai kèm stderr.
            if tong_ca == 0:
                print(f"  ✗ {ten} — bản hỏng làm tiến trình CHẾT, không in được ca nào. "
                      f"stderr: {(r.stderr or '').strip().splitlines()[-1:] or '(rỗng)'}")
                tong += 1
                continue
            het_do = len(do) == tong_ca
            if het_do and do:
                print(f"  ✗ {ten} — MỌI ca đều đỏ: phép thay phá hỏng nền chứ không gỡ một "
                      f"lớp vá, sửa lại phép thay")
                tong += 1
                continue
            can = [f"[{i}]" for i in ca_do]
            bat = r.returncode != 0 and all(any(f" {i:02d} " in ln for ln in do) for i in ca_do)
            print(("  ✓ " if bat else "  ✗ ") + ten
                  + ("" if bat else f" — cần ca {can} đỏ; đỏ thực tế: {do or 'KHÔNG CÓ'}"))
            tong += 0 if bat else 1
        finally:
            dich.unlink(missing_ok=True)
    print(f"\n{len(BAN_HONG) - tong}/{len(BAN_HONG)} bản hỏng bị bắt")
    return 1 if tong else 0


# Bảng đặt CUỐI FILE, sau mã: neo trỏ vào chính dòng khai thì bản hỏng "hỏng" ở bảng chứ không
# ở mã — vẫn chạy, vẫn không lỗi, chỉ là chứng minh mất sạch giá trị (mục 17 CLAUDE.md).
# `neo_hai_dong()` tự nới neo lên dòng liền trước, nên ở đây khai MỘT dòng đích là đủ.
BAN_HONG = [
    ("gỡ lookahead `Ấn Độ Dương` — đếm bài vùng lớn thành bài Nam Á",
     r'        r"ấn độ(?![\s-]*dương)", r"\bindia\b", r"\bindian\b", r"pakistan", r"bangladesh",',
     r'        r"ấn độ", r"\bindia\b", r"\bindian\b", r"pakistan", r"bangladesh",', [4]),
    ("gỡ lookbehind `Đông Nam Á` ở nhánh NHÃN",
     r'        r"kashmir", r"(?<!đông )nam á", r"south asia",',
     r'        r"kashmir", r"nam á", r"south asia",', [5]),
    ("gỡ lookbehind `Đông Nam Á` ở nhánh NGUỒN — cổng câm đúng vùng thiếu nguồn nhất",
     r'    "Nam Á": [r"(?<!đông )nam á", r"south asia", r"\bấn độ(?![\s-]*dương)"],',
     r'    "Nam Á": [r"nam á", r"south asia", r"\bấn độ(?![\s-]*dương)"],', [7]),
    # ⚠️ Neo có XUỐNG DÒNG thì phần chứa `\n` phải là chuỗi THƯỜNG, không phải raw — trong raw
    # string `\n` là hai ký tự literal nên neo không bao giờ khớp. Đã vấp lúc dựng.
    ("lọc quá tay — bỏ hẳn từ khoá `ấn độ`, mất bài Ấn Độ thật",
     r'        r"ấn độ(?![\s-]*dương)", r"\bindia\b", r"\bindian\b", r"pakistan", r"bangladesh",'
     + "\n" + r'        r"sri lanka", r"\bnepal", r"maldives", r"afghanistan", r"new delhi", r"islamabad",',
     r'        r"pakistan", r"bangladesh",'
     + "\n" + r'        r"sri lanka", r"\bnepal", r"maldives", r"afghanistan", r"new delhi", r"islamabad",',
     [6]),
    ("bỏ chuẩn hoá NFC — bài dán tay từ macOS trượt câm",
     '    return unicodedata.normalize("NFC", s or "").lower()',
     '    return (s or "").lower()', [9]),
    ("nới ngưỡng tỉ lệ về 0 — cổng không bao giờ kêu",
     "NGUONG_TY_LE = 0.35",
     "NGUONG_TY_LE = 0.0", [1, 10]),
    ("siết ngưỡng tỉ lệ lên 1,0 — kêu oan mọi vùng",
     "NGUONG_TY_LE = 0.35",
     "NGUONG_TY_LE = 1.0", [2, 11]),
    ("nới ngưỡng số bài về 0 — kêu cả vùng vài bài",
     "NGUONG_BAI = 5",
     "NGUONG_BAI = 0", [3]),
    ("nhánh nguồn không bao giờ báo thiếu — phép đo mất răng",
     "        if not any(m.search(x) for x in co for m in mau):\n            ra.append(kv)",
     "        if False:\n            ra.append(kv)", [7]),
    ("kho hỏng thì nuốt, trả mảng rỗng cho êm",
     '        print(f"✗ Kho bài phải là một MẢNG, đọc ra {type(d).__name__}: {duong}", file=sys.stderr)\n        raise SystemExit(2)',
     "        return []", [12]),
]


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        sys.exit(tu_kiem())
    if "--ca" in sys.argv:            # chạy bộ ca, dùng bởi chính --tu-kiem
        sys.exit(tu_kiem_chay())
    sys.exit(bao_cao())
