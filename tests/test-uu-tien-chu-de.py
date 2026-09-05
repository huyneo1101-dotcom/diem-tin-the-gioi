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

# Nhãn chủ đề 05 đọc THẲNG từ mã nguồn, không gõ tay (05/08/2026 — trước đây bộ này khai cứng
# `"Pitch Black"` và 03 ca đỏ ngay lượt đổi nhãn). Gõ tay thì đổi nhãn là test đỏ oan, mà đỏ
# oan vài lần là bảng hết được đọc.
CD_TT = HV.topics.CHU_DE_TAP_TRAN

# Chủ đề 05 nay có truy vấn RỖNG cho tới khi `nap_tap_tran_dang_chay()` bơm cuộc đang chạy vào.
# Bộ test phải bơm y như phiên thật, nếu không ca [06]/[08] đo trên bảng rỗng — tức đo nhầm
# nhánh mà bảng kết quả vẫn xanh.
_EX_MAU = [{"name": "Pitch Black 2026 (Úc chủ trì, 20 nước tham gia)",
            "dates": "20/7 – 7/8/2026", "status": "ongoing",
            "location": "RAAF Darwin, Tindal", "summary": "Úc chủ trì"}]


def bom_tap_tran(exs=None, hom_nay="2026-08-05"):
    """Bơm cuộc tập trận vào bảng chủ đề + bảng truy vấn của BẢN ĐANG THỬ."""
    dang = HV.tap_tran.dang_dien_ra(exs if exs is not None else _EX_MAU, hom_nay)
    keys, qs = [], []
    for ex in dang:
        keys.extend(HV.tap_tran.tu_khoa(ex))
        qs.extend(HV.tap_tran.truy_van(ex))
    HV.topics.nap_tu_khoa_tap_tran(keys)
    HV.GNEWS_QUERIES[CD_TT] = qs
    return dang


bom_tap_tran()


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
          ung_vien(CD_TT, u, "Exercise Pitch Black 2026: KC-30A refuels Indian Rafales")]
    ra = khu_trung_theo_url(HV.uu_tien_chu_de(lo))
    assert len(ra) == 1, f"phải còn đúng 1 bài, có {len(ra)}"
    assert ra[0]["chu_de"] == CD_TT, \
        f'bài tập trận bị chủ đề {ra[0]["chu_de"]!r} ăn mất — chủ đề 05 sẽ báo 0 bài'


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
        [ung_vien("Chủ đề chưa khai", u), ung_vien(CD_TT, u)]))
    assert ra[0]["chu_de"] == CD_TT, \
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
    q = " ".join(HV.GNEWS_QUERIES[CD_TT])
    assert "raaf" not in q.lower(), \
        f"truy vấn chủ đề 05 quá rộng, sẽ nuốt tin RAAF thuần: {q!r}"
    # Neo phải là TÊN CUỘC đang chạy, sinh từ `tap_tran.truy_van` — không còn là chuỗi cứng.
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


def _uv_ngay(chu_de, ngay, tieu_de, url=None):
    return {"lop": "RSS", "chu_de": chu_de, "ngay": ngay, "tieu_de": tieu_de,
            "nguon": "X", "url": url or f"https://x.test/{abs(hash(tieu_de))}"}


def ca_11():
    """PHẢI CHẶN — tin ngày `?` KHÔNG được leo lên đầu danh sách in cho agent.

    Lỗi thật 05/09/2026: `sorted(lst, key=lambda x: x["ngay"], reverse=True)` sắp theo CHUỖI,
    mà `?` (0x3F) > `2` (0x32) nên mọi tin không đọc được ngày đứng TRƯỚC mọi tin có ngày —
    đúng nhóm agent loại thẳng. Đo trên lô thật phiên tối 05/09: 13/20 slot của chủ đề 2 bị
    tin ngày `?` chiếm, chỉ còn 07 slot cho tin có ngày thật.
    """
    lo = [_uv_ngay("CNQS Mỹ", "?", f"Tin khong ro ngay {i}") for i in range(5)]
    lo += [_uv_ngay("CNQS Mỹ", "2026-09-05", "Tin hom nay"),
           _uv_ngay("CNQS Mỹ", "2026-09-04", "Tin hom qua")]
    od = HV.sap_ung_vien("CNQS Mỹ", lo)
    assert od[0]["ngay"] == "2026-09-05" and od[1]["ngay"] == "2026-09-04", \
        f"tin có ngày phải đứng trước, đang là {[h['ngay'] for h in od[:3]]}"
    assert all(h["ngay"] == "?" for h in od[-5:]), [h["ngay"] for h in od]


def ca_12():
    """PHẢI CHẶN — nhánh Anh thưa tin không được nhánh Biển Đông đăng dày dìm khỏi trần in.

    Sửa phép sắp xếp thôi KHÔNG cứu: đo lại lô thật 05/09 sau khi chỉ sửa sort, hai bài UK
    Defence Journal chỉ nhích từ hạng 37-38 lên 24-25/46 — vẫn ngoài trần `PER_TOPIC_CAP`.
    Ca dựng đúng hình dạng đó: 30 tin Biển Đông hôm nay, 02 tin Anh hôm qua.
    """
    lo = [_uv_ngay(HV.CHU_DE_DIA_BAN, "2026-09-05",
                   f"Philippines patrol in South China Sea number {i}") for i in range(30)]
    lo += [_uv_ngay(HV.CHU_DE_DIA_BAN, "2026-09-04", "British aircraft carrier deploys"),
           _uv_ngay(HV.CHU_DE_DIA_BAN, "2026-09-04", "Royal Navy warship fires near Falklands")]
    od = HV.sap_ung_vien(HV.CHU_DE_DIA_BAN, lo)
    hang = [i for i, h in enumerate(od[:HV.PER_TOPIC_CAP])
            if HV.nhanh_dia_ban(h["tieu_de"]) == "Anh"]
    assert len(hang) == 2, \
        f"02 tin Anh phải lọt trần in {HV.PER_TOPIC_CAP}, chỉ lọt {len(hang)} — agent không "
    "nhìn thấy thì không có cách nào nạp, và sàn 02 tin mỗi mục đổ ngay tại đây"


def ca_13():
    """Đối chứng — hạn ngạch KHÔNG được lật ngược thành nhánh thưa chiếm hết chỗ.

    Nhánh cạn bài phải tự nhường phần còn lại, không cấp phát cứng: lô chỉ có 01 tin Anh thì
    19 slot còn lại vẫn thuộc về hai nhánh kia.
    """
    lo = [_uv_ngay(HV.CHU_DE_DIA_BAN, "2026-09-05", f"South China Sea patrol {i}")
          for i in range(30)]
    lo += [_uv_ngay(HV.CHU_DE_DIA_BAN, "2026-09-05", "British carrier deploys")]
    od = HV.sap_ung_vien(HV.CHU_DE_DIA_BAN, lo)[:HV.PER_TOPIC_CAP]
    assert sum(1 for h in od if HV.nhanh_dia_ban(h["tieu_de"]) == "Anh") == 1, \
        "chỉ có 01 tin Anh mà chiếm hơn 01 slot"
    assert len(od) == HV.PER_TOPIC_CAP, f"mất slot: {len(od)}"


def ca_14():
    """Nhánh địa bàn dùng CHUNG phép neo với tầng xuất bản, Úc giành trước Anh.

    Tin AUKUS dính cả hai nước phải về nhánh Australia — y hệt `make_docx.tieu_muc_dia_ban`.
    Lệch nhau thì hạn ngạch ở tầng quét cấp cho một nhánh, còn file Word in ra nhánh khác.
    """
    # Fixture PHẢI khớp cả hai phép neo, nếu không ca mất răng: "UK" trần KHÔNG khớp
    # `neo_anh` (cố ý — hai chữ đó khớp bậy khắp nơi), nên câu có "UK" mà không có
    # "Britain"/"British" chỉ khớp nhánh Úc và đảo thứ tự giành cũng ra cùng kết quả.
    # `--tu-kiem` bắt đúng chỗ này lúc dựng: bản hỏng đảo thứ tự vẫn để ca 14 xanh.
    assert HV.nhanh_dia_ban("Australia and Britain sign AUKUS submarine deal") == "Australia"
    assert HV.nhanh_dia_ban("Royal Navy frigate visits Cambodia") == "Anh"
    assert HV.nhanh_dia_ban("Chinese coast guard at Scarborough Shoal") == "Biển Đông"


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
    ("[11] PHẢI CHẶN: tin ngày '?' không leo lên đầu danh sách in", ca_11),
    ("[12] PHẢI CHẶN: nhánh Anh thưa tin vẫn lọt trần in", ca_12),
    ("[13] đối chứng: nhánh cạn bài tự nhường slot, không cấp phát cứng", ca_13),
    ("[14] nhánh địa bàn dùng chung phép neo với tầng xuất bản", ca_14),
]


# ── Tự kiểm ───────────────────────────────────────────────────────────────────
# Mỗi dòng: (nhãn, (chuỗi tìm, chuỗi thay), các ca PHẢI ĐỎ).
# Neo kèm dòng liền kề để không khớp nhầm chỗ khác trong harvest.py.
BAN_HONG = [
    ("sắp ứng viên theo CHUỖI ngày như bản cũ (tin ngày '?' leo lên đầu)",
     ('    return sorted(lst, key=lambda x: (x["ngay"] == "?", -_daykey(x["ngay"])))',
      '    return sorted(lst, key=lambda x: x["ngay"], reverse=True)'),
     [11]),
    ("bỏ hạn ngạch nhánh địa bàn, xếp thuần theo ngày (nhánh Anh bị dìm)",
     ("    if topic == CHU_DE_DIA_BAN:\n        theo_nhanh = {n: [] for n in NHANH_DIA_BAN}",
      "    if False:\n        theo_nhanh = {n: [] for n in NHANH_DIA_BAN}"),
     [12]),
    ("nhánh địa bàn giành Anh TRƯỚC Úc (lệch tầng xuất bản, tin AUKUS rơi nhánh Anh)",
     ('    if neo_uc(tieu_de):\n        return "Australia"\n'
      '    if neo_anh(tieu_de):\n        return "Anh"',
      '    if neo_anh(tieu_de):\n        return "Anh"\n'
      '    if neo_uc(tieu_de):\n        return "Australia"'),
     [14]),
    ("gỡ lời gọi uu_tien_chu_de khỏi main()",
     ("    hits = uu_tien_chu_de(hits)\n    out, seen = [], set()",
      "    out, seen = [], set()"),
     [5]),
    ("đảo thứ tự: chủ đề 02 giành URL trước chủ đề 05 (đúng lỗi 02/08)",
     ('UU_TIEN_CHU_DE = (topics.CHU_DE_TAP_TRAN, "Mỹ – Mali", "CNQS Mỹ", "Úc & Biển Đông", "Nội bộ Mỹ")',
      'UU_TIEN_CHU_DE = ("Úc & Biển Đông", "Mỹ – Mali", "CNQS Mỹ", topics.CHU_DE_TAP_TRAN, "Nội bộ Mỹ")'),
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
    # Neo nằm ở `tap_tran.py` (nơi sinh truy vấn từ 05/08/2026), không còn ở harvest.py.
    ("trả lại `OR RAAF` vào truy vấn chủ đề 05",
     ("""    ra = ['"%s" exercise' % kn]""",
      """    ra = ['"%s" exercise OR RAAF' % kn]"""),
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
    # ⚠️ CHÉP ĐỦ MỌI MODULE `harvest.py` IMPORT — thiếu một cái là tiến trình con chết ngay lúc
    # nạp module, không in được dòng `✓`/`✗` nào, và `--tu-kiem` đọc thành "0 ca đỏ" rồi kết
    # luận *"ca đó không bắt được lỗi"*. Đo thật 05/08/2026: thêm `import tap_tran` vào
    # harvest mà quên dòng này ⇒ **7/7 bản hỏng đều trượt**, trong khi lượt chạy thường vẫn
    # 10/10 xanh — tức bộ test mất sạch khả năng chứng minh mà không dấu hiệu nào.
    (dich / "scripts").mkdir(parents=True, exist_ok=True)
    # Phép thay áp lên file NÀO CHỨA chuỗi neo — từ 05/08/2026 truy vấn chủ đề 05 sinh trong
    # `tap_tran.py` chứ không còn nằm trong `harvest.py`, nên khoá cứng vào harvest là bản
    # hỏng không áp được và `--tu-kiem` báo "0 chỗ khớp" cho một lỗi vẫn tồn tại.
    for ten in ("harvest.py", "topics.py", "tap_tran.py"):
        goc = (REPO / "scripts" / ten).read_text(encoding="utf-8")
        if tim in goc:
            goc = goc.replace(tim, thay)
        (dich / "scripts" / ten).write_text(goc, encoding="utf-8")


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản harvest.py đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    # Đếm trên CẢ BA file mà `_dung_ban_sao` chép — neo có thể nằm ở `tap_tran.py` (truy vấn
    # chủ đề 05 sinh ở đó từ 05/08/2026). Đếm mỗi harvest.py thì bản hỏng hợp lệ bị báo
    # "0 chỗ khớp", tức mất một bản hỏng mà nhìn thông điệp lại tưởng neo hỏng.
    goc = "\n".join((REPO / "scripts" / t).read_text(encoding="utf-8")
                    for t in ("harvest.py", "topics.py", "tap_tran.py"))
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
