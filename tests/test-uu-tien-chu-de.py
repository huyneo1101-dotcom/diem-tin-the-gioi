#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST HỒI QUY: MỘT CHỦ ĐỀ KHÔNG ĐƯỢC ĂN MẤT ỨNG VIÊN CỦA CHỦ ĐỀ KHÁC (vá 02/08/2026).

⚠ CƠ CHẾ GÂY VẤP — đọc trước khi sửa file này.
Khâu gộp cuối của `scripts/harvest.py` khử trùng theo URL trên TOÀN lô ứng viên: bài nào
tới trước thì chủ đề đó giữ, chủ đề tới sau mất bài đó vĩnh viễn. Ngày 02/08/2026 chủ đề 02
"Úc & Biển Đông" được thêm truy vấn `"Pitch Black" Australia exercise` để bắt tin Không quân
Úc — mà trong `GNEWS_QUERIES` chủ đề 02 đứng TRƯỚC chủ đề 05 "Pitch Black". Từ đó:

    truy vấn của chủ đề 05 vẫn trả về 5–8 tin đúng khung ngày,
    nhưng bảng ứng viên in ra "-- Pitch Black (0 bài) --" ở MỌI phiên.

Không lỗi, không cảnh báo, bảng vẫn đủ 5 dòng. Đọc vào chỉ thấy dòng "(không có ứng viên nào
trong khung hôm nay + hôm qua)" và tưởng hôm đó không có tin — trong khi kỳ tập trận đang
chạy và báo chí đăng đều. Đây là hỏng câm: mục tập trận nạp qua `exerciseUpdates` vào đúng
thẻ, nên mất ứng viên nghĩa là thẻ tập trận đứng yên suốt kỳ.

Bản vá khai thứ tự giành URL thành hằng số `UU_TIEN_CHU_DE` thay vì dựa vào thứ tự khai
trong dict — dựa vào thứ tự dict thì người sau sắp lại dict cho gọn sẽ dựng lại đúng lỗ này.

Chạy:
    python3 tests/test-uu-tien-chu-de.py
    python3 tests/test-uu-tien-chu-de.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

`--tu-kiem` dựng bản repo ĐÃ GỠ ĐÚNG DÒNG BẢO VỆ rồi chạy lại chính bộ ca này — mỗi bản hỏng
phải làm ĐỎ đúng những ca đã khai. Xanh trên cả bản đúng lẫn bản hỏng là test vô dụng.

⚠ Bản hỏng KHÔNG ghi đè file thật: mỗi lượt dựng một BẢN SAO repo tối giản trong thư mục tạm,
giữ nguyên thư mục `scripts/` để `harvest.py` vẫn tự tìm `topics.py` — của BẢN SAO. Repo này
thường có nhiều phiên Claude chạy song song (CLAUDE.md toàn cục, mục 9b), ghi đè file thật là
xoá việc của phiên khác.
"""
import hashlib
import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

# Seam để tự kiểm: trỏ sang một BẢN SAO repo khác (xem --tu-kiem).
REPO_THU = pathlib.Path(os.environ.get("UUTIEN_REPO") or REPO)
HARVEST = REPO_THU / "scripts" / "harvest.py"


def _nap(ten: str, path: pathlib.Path):
    """Nạp module từ đường dẫn cụ thể.

    Tên module phải DUY NHẤT theo đường dẫn: nạp hai bản `harvest` khác nhau dưới cùng một
    tên thì bản sau ăn cache `sys.modules` của bản trước, và bản hỏng lặng lẽ chạy bằng mã
    của bản đúng.
    """
    khoa = ten + "_" + hashlib.sha1(str(path).encode()).hexdigest()[:8]
    spec = importlib.util.spec_from_file_location(khoa, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[khoa] = mod
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(REPO_THU / "scripts"))
HV = _nap("harvest", HARVEST)
NGUON = HARVEST.read_text(encoding="utf-8")


def ung_vien(chu_de, url, tieu_de="Tin mẫu"):
    return {"lop": "GNEWS", "chu_de": chu_de, "ngay": "2026-08-02",
            "tieu_de": tieu_de, "nguon": "Janes", "url": url}


def khu_trung_theo_url(hits):
    """Mô phỏng ĐÚNG một việc của khâu gộp: giữ bản ĐẦU của mỗi URL.

    Cố ý chỉ mô phỏng phép khử trùng URL — phần `is_noise`/`same_story` không liên quan tới
    thứ tự chủ đề nên đưa vào đây chỉ làm ca đo nhầm nhánh. Việc `main()` có thật sự gọi
    `uu_tien_chu_de` trước vòng này hay không do ca [05] canh bằng cách đọc mã nguồn.
    """
    ra, seen = [], set()
    for h in hits:
        if h["url"] in seen:
            continue
        seen.add(h["url"])
        ra.append(h)
    return ra


# ── Ca test ───────────────────────────────────────────────────────────────────
def ca_01():
    """PHẢI CHẶN — tin Pitch Black bị chủ đề 02 bắt trước thì vẫn phải về chủ đề 05.

    Dựng đúng lô đã gây lỗi 02/08: cùng một URL, chủ đề 02 khai trước (vì nó đứng trước
    trong GNEWS_QUERIES), chủ đề 05 khai sau.
    """
    u = "https://www.janes.com/pitch-black-kc30a-rafale"
    lo = [ung_vien("Úc & Biển Đông", u, "Exercise Pitch Black 2026: KC-30A refuels Indian Rafales"),
          ung_vien("Pitch Black", u, "Exercise Pitch Black 2026: KC-30A refuels Indian Rafales")]
    ra = khu_trung_theo_url(HV.uu_tien_chu_de(lo))
    assert len(ra) == 1, f"phải còn đúng 1 bài, có {len(ra)}"
    assert ra[0]["chu_de"] == "Pitch Black", \
        f'bài Pitch Black bị chủ đề {ra[0]["chu_de"]!r} ăn mất — chủ đề 05 sẽ báo 0 bài'


def ca_02():
    """Sort phải ỔN ĐỊNH: trong cùng chủ đề, thứ tự cũ giữ nguyên.

    Đây là điều kiện để lô local vẫn đứng trước lô CI (chú thích ở chỗ gộp `doc_ung_vien_ci`)
    và để bản đầu của một sự kiện vẫn là bản được giữ.
    """
    lo = [ung_vien("Úc & Biển Đông", f"https://x/{i}", f"bài {i}") for i in range(6)]
    ra = HV.uu_tien_chu_de(lo)
    assert [h["url"] for h in ra] == [h["url"] for h in lo], \
        "sort đã xáo trộn thứ tự trong cùng một chủ đề"


def ca_03():
    """Chủ đề LẠ (chưa khai trong UU_TIEN_CHU_DE) phải xuống CUỐI, không lên đầu.

    Chiều nới: cho chủ đề lạ lên đầu thì nó giành URL của mọi chủ đề đã khai — đúng lỗ đang vá,
    chỉ đổi thủ phạm.
    """
    u = "https://x/tranh-chap"
    ra = khu_trung_theo_url(HV.uu_tien_chu_de(
        [ung_vien("Chủ đề chưa khai", u), ung_vien("Pitch Black", u)]))
    assert ra[0]["chu_de"] == "Pitch Black", \
        f'chủ đề lạ giành mất URL của chủ đề đã khai (còn lại: {ra[0]["chu_de"]!r})'


def ca_04():
    """Lô rỗng không được ném lỗi — harvest chạy với --rss cũng đi qua đường này."""
    assert HV.uu_tien_chu_de([]) == []


def ca_05():
    """PHẢI CHẶN — `main()` phải GỌI `uu_tien_chu_de`, và gọi TRƯỚC vòng khử trùng URL.

    Hàm sort đúng mà không ai gọi thì lỗ vẫn nguyên: đây là ca canh "cổng còn nằm trên đường
    đi". Đo bằng vị trí trong mã nguồn vì vòng khử trùng nằm trong thân `main()`.
    """
    goi = NGUON.find("hits = uu_tien_chu_de(hits)")
    assert goi != -1, "main() KHÔNG gọi uu_tien_chu_de — bản vá nằm ngoài đường đi"
    khu = NGUON.find('if h["url"] in urls or h["url"] in seen:')
    assert khu != -1, "không tìm thấy vòng khử trùng URL — mã đã đổi, sửa lại test"
    assert goi < khu, "uu_tien_chu_de bị gọi SAU vòng khử trùng → sort xong thì bài đã mất"


def ca_06():
    """PHẢI CHẶN — truy vấn của chủ đề 05 không được chứa `RAAF`.

    Chủ đề 05 giành URL trước, nên một truy vấn rộng sẽ kéo mọi tin Không quân Úc vào mục tập
    trận, kể cả tin không dính kỳ tập trận nào. Đây là chiều hỏng NGƯỢC với ca [01].
    """
    q = " ".join(HV.GNEWS_QUERIES["Pitch Black"])
    assert "raaf" not in q.lower(), \
        f"truy vấn chủ đề 05 quá rộng, sẽ nuốt tin RAAF thuần: {q!r}"
    assert "pitch black" in q.lower(), f"truy vấn chủ đề 05 mất neo tên tập trận: {q!r}"


def ca_07():
    """Đối chứng chống nới tay — chủ đề 02 PHẢI còn truy vấn Không quân Úc.

    Bỏ nó đi thì tin RAAF không dính tập trận lại câm y như trước 02/08 (lỗ Huy bắt được qua
    tin KC-30A tiếp dầu Rafale, Janes 31/07).
    """
    q = " ".join(HV.GNEWS_QUERIES["Úc & Biển Đông"]).lower()
    assert "raaf" in q or "royal australian air force" in q, \
        "chủ đề 02 mất truy vấn Không quân Úc — tin RAAF sẽ không có ai bắt"


def ca_08():
    """PHẢI CHẶN — mọi chủ đề có truy vấn đều phải có tên trong UU_TIEN_CHU_DE.

    Thêm chủ đề mới mà quên khai thứ tự thì nó tự động xuống cuối và bị các chủ đề khác ăn
    mất — hỏng câm y hệt ca [01], chỉ khác thủ phạm.
    """
    thieu = [t for t in HV.GNEWS_QUERIES if t not in HV.UU_TIEN_CHU_DE]
    assert not thieu, f"chủ đề chưa khai thứ tự giành URL: {thieu}"


def ca_09():
    """Đối chứng chống chặn oan — tin Biển Đông thuần vẫn ở chủ đề 02.

    Bản vá chỉ đổi thứ tự GIÀNH url, không được đổi chủ đề của bài không tranh chấp với ai.
    """
    lo = [ung_vien("Úc & Biển Đông", "https://x/scarborough",
                   "China issues new rules around Scarborough Shoal")]
    ra = HV.uu_tien_chu_de(lo)
    assert len(ra) == 1 and ra[0]["chu_de"] == "Úc & Biển Đông"


def ca_10():
    """PHẢI CHẶN — tên chủ đề trong UU_TIEN_CHU_DE phải khớp bảng in cuối `main()`.

    Lệch một ký tự (dấu gạch ngang `–` của "Mỹ – Mali" là chỗ hay lệch nhất) thì chủ đề đó
    rơi xuống cuối trong im lặng, mà bảng vẫn in đủ 5 dòng.
    """
    m = re.search(r'for topic in \((.*?)\):', NGUON, re.S)
    assert m, "không đọc được danh sách chủ đề của bảng in — mã đã đổi, sửa lại test"
    in_bang = set(re.findall(r'"([^"]+)"', m.group(1)))
    assert in_bang <= set(HV.UU_TIEN_CHU_DE), \
        f"chủ đề in ra bảng mà chưa khai thứ tự: {sorted(in_bang - set(HV.UU_TIEN_CHU_DE))}"


CA = [
    ("[01] PHẢI CHẶN: tin Pitch Black không bị chủ đề 02 ăn mất", ca_01),
    ("[02] sort ổn định trong cùng chủ đề", ca_02),
    ("[03] chủ đề lạ xuống cuối, không lên đầu", ca_03),
    ("[04] lô rỗng không ném lỗi", ca_04),
    ("[05] PHẢI CHẶN: main() gọi uu_tien_chu_de TRƯỚC vòng khử trùng", ca_05),
    ("[06] PHẢI CHẶN: truy vấn chủ đề 05 không chứa RAAF", ca_06),
    ("[07] đối chứng: chủ đề 02 còn truy vấn Không quân Úc", ca_07),
    ("[08] PHẢI CHẶN: mọi chủ đề có truy vấn đều đã khai thứ tự", ca_08),
    ("[09] đối chứng: tin Biển Đông thuần vẫn ở chủ đề 02", ca_09),
    ("[10] PHẢI CHẶN: tên chủ đề khớp bảng in cuối main()", ca_10),
]


# ── Tự kiểm ───────────────────────────────────────────────────────────────────
# Mỗi dòng: (nhãn, (chuỗi tìm, chuỗi thay), các ca PHẢI ĐỎ).
# Neo kèm dòng liền kề để không khớp nhầm chỗ khác trong harvest.py.
BAN_HONG = [
    ("gỡ lời gọi uu_tien_chu_de khỏi main()",
     ("    hits = uu_tien_chu_de(hits)\n    out, seen = [], set()",
      "    out, seen = [], set()"),
     [5]),
    ("đảo thứ tự: chủ đề 02 giành URL trước chủ đề 05 (đúng lỗi 02/08)",
     ('UU_TIEN_CHU_DE = ("Pitch Black", "Mỹ – Mali", "CNQS Mỹ", "Úc & Biển Đông", "Nội bộ Mỹ")',
      'UU_TIEN_CHU_DE = ("Úc & Biển Đông", "Mỹ – Mali", "CNQS Mỹ", "Pitch Black", "Nội bộ Mỹ")'),
     [1]),
    ("chủ đề chưa khai được cho lên ĐẦU thay vì xuống cuối",
     ("    return sorted(hits, key=lambda h: thu_tu.get(h.get(\"chu_de\"), len(thu_tu)))",
      "    return sorted(hits, key=lambda h: thu_tu.get(h.get(\"chu_de\"), -1))"),
     [3]),
    ("sort không ổn định — xáo trộn thứ tự trong cùng chủ đề",
     ("    thu_tu = {t: i for i, t in enumerate(UU_TIEN_CHU_DE)}\n"
      "    return sorted(hits, key=lambda h: thu_tu.get(h.get(\"chu_de\"), len(thu_tu)))",
      "    thu_tu = {t: i for i, t in enumerate(UU_TIEN_CHU_DE)}\n"
      "    return sorted(hits, key=lambda h: (thu_tu.get(h.get(\"chu_de\"), len(thu_tu)),\n"
      "                                       h.get(\"url\", \"\")), reverse=True)"),
     [1, 2]),
    ("trả lại `OR RAAF` vào truy vấn chủ đề 05",
     ('''    "Pitch Black": ['"Pitch Black" Australia exercise'],''',
      '''    "Pitch Black": ['"Pitch Black" Australia exercise OR RAAF'],'''),
     [6]),
    ("bỏ truy vấn Không quân Úc khỏi chủ đề 02",
     ("""        '"Royal Australian Air Force" OR RAAF',\n        '"Pitch Black" Australia exercise',""",
      """        '"Pitch Black" Australia exercise',"""),
     [7]),
    ("thêm chủ đề mới mà quên khai thứ tự giành URL",
     ('''    "Mỹ – Mali": ['Mali OR JNIM OR Sahel OR Bamako OR "Africa Corps"'],''',
      '''    "Mỹ – Mali": ['Mali OR JNIM OR Sahel OR Bamako OR "Africa Corps"'],\n'''
      '''    "Chủ đề mới quên khai": ['something'],'''),
     [8]),
]


def chay() -> int:
    print(f"TEST ưu tiên chủ đề khi khử trùng URL — {HARVEST}")
    print("═" * 78)
    do = []
    for nhan, fn in CA:
        try:
            fn()
            print(f"  ✓ {nhan}")
        except Exception as e:
            print(f"  ✗ {nhan}\n        │ {e}")
            do.append(int(nhan[1:3]))
    print("═" * 78)
    print(f"{len(CA) - len(do)}/{len(CA)} ca đạt" + (f" · ĐỎ: {do}" if do else ""))
    return 1 if do else 0


def _dung_ban_sao(dich: pathlib.Path, tim: str, thay: str):
    (dich / "scripts").mkdir(parents=True, exist_ok=True)
    for ten in ("harvest.py", "topics.py"):
        goc = (REPO / "scripts" / ten).read_text(encoding="utf-8")
        if ten == "harvest.py":
            goc = goc.replace(tim, thay)
        (dich / "scripts" / ten).write_text(goc, encoding="utf-8")


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản harvest.py đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    goc = (REPO / "scripts" / "harvest.py").read_text(encoding="utf-8")
    hong = 0
    for nhan, (tim, thay), ca_phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"(cần đúng 1). Mã nguồn đã đổi → sửa lại neo, đừng sửa ca.")
            hong += 1
            continue
        # Thư mục tạm mang PID + sha1 nội dung: hai phiên chạy chồng không xoá bản của nhau,
        # và hai bản hỏng khác nhau không dùng chung đường dẫn (dùng chung thì `.pyc` của bản
        # trước bị đọc lại và bản sau lặng lẽ chạy bằng mã cũ).
        dau = hashlib.sha1((tim + thay).encode()).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"uutien-{os.getpid()}-{dau}-"))
        try:
            _dung_ban_sao(d, tim, thay)
            env = dict(os.environ, UUTIEN_REPO=str(d))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        # Rút số ca bằng regex, đừng cắt chuỗi theo chỉ số: dấu ✗ là một ký tự nhưng nằm sau
        # hai khoảng trắng, đếm lệch một là mọi bản hỏng báo lỗi phân tích thay vì báo kết quả.
        do = {int(m.group(1)) for m in
              (re.match(r"\s*✗ \[(\d+)\]", dong) for dong in r.stdout.splitlines()) if m}
        # Bản hỏng làm ĐỎ HẾT = phép thay làm vỡ cú pháp, không chứng minh được ca nào có
        # răng — nó chỉ chứng minh Python biết báo lỗi.
        if len(do) == len(CA):
            print(f"  ✗ {nhan}\n        │ MỌI ca đều đỏ → phép thay nhiều khả năng làm vỡ "
                  f"cú pháp/nạp module, sửa lại phép thay.")
            hong += 1
            continue
        thieu = sorted(set(ca_phai_do) - do)
        if thieu:
            print(f"  ✗ {nhan}\n        │ ca {thieu} VẪN XANH trên bản hỏng "
                  f"(đỏ thực tế: {sorted(do)}) → ca đó không bắt được lỗi")
            hong += 1
        else:
            print(f"  ✓ {nhan} — ca {sorted(set(ca_phai_do))} đỏ đúng như khai")
    print("═" * 78)
    print("✅ Mọi bản hỏng đều bị bắt" if not hong else f"❌ {hong} bản hỏng LỌT")
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(tu_kiem() if "--tu-kiem" in sys.argv else chay())
