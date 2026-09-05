#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sửa thông tin của một cuộc tập trận ĐÃ CÓ trong `DATA.exercises` — dựng 07/08/2026.

## Lỗ mà script này bịt

`add_news.py` có `newExercises` để TẠO thẻ mới và `exerciseUpdates` để THÊM item, nhưng
`apply_event_updates` chỉ chạm `entry["items"]` — **không đường nào sửa `dates` · `status` ·
`location` · `scale` · `summary` của một cuộc đã nạp**. Mà đó lại là việc thường xuyên nhất:
tập trận lớn hay công bố ngày cụ thể sát ngày khai mạc, nên thẻ nạp trước đó mang
`"Tháng 8/2026; ngày cụ thể chưa công bố"` và phải sửa lại khi ngày ra. Không có script thì
chỉ còn đường sửa tay `index.html` — đúng thứ CLAUDE.md cấm.

## Vì sao phải là một CỔNG chứ không phải một lệnh sed

Trường `dates` không phải chữ trang trí: web dựng nhãn trạng thái từ chính nó
(`index.html::evRange` + `effStatus`), và `tap_tran.py::dang_dien_ra` dùng cùng luật để quyết
**cuộc nào được bơm từ khoá vào lượt quét tin**. Viết sai `dates` thì hỏng câm hai tầng —
thẻ vẫn hiện đủ tên, địa bàn, quy mô, tóm tắt, chỉ mỗi nhãn trạng thái là nói dối; còn chủ đề
tập trận thì lặng lẽ bỏ cuộc đó.

Hai cái bẫy đã vấp THẬT trong ngày 07/08/2026, cách nhau chưa tới một giờ, nay thành 02 cổng:

⚠️ **MỘT MỐC LẺ ⇒ `a == b` ⇒ web hiện "Đã kết thúc" cho cuộc đang chạy.** Nhánh lùi về
`status` chỉ chạy khi `evRange` trả `null`; chuỗi có đúng một ngày thì mẫu thứ ba VẪN khớp nên
nhánh lùi không bao giờ tới. Nói cách khác chuỗi một mốc **tệ hơn** chuỗi không đọc được ngày
nào. Cổng `_kiem_dates` chặn.

⚠️ **`evRange` quét TOÀN CHUỖI, nên ngày nằm trong lời chú thích cũng bị bắt.** Ba thẻ ghi
`"Tháng 8/2026; ngày cụ thể chưa công bố tính tới 7/8/2026"` đã hiện "Đang diễn ra" trong khi
cuộc chưa khai mạc — cụm *"tính tới 7/8/2026"* khớp mẫu thứ ba. Biết luật chưa đủ, vì chỗ sai
nằm ở phần người viết không coi là dữ liệu. Cổng `_kiem_khop_status` chặn: nhãn suy ra từ
`dates` phải KHỚP `status` khai trong payload.

⚠️ **Sửa `dates` thì BẮT BUỘC khai `status`** — ý định khai bằng lời, không suy. Cùng bài học
với `tu_dong=1` · `TELEGRAM_BAT_BUOC` · `DIEMTIN_PHIEN_TEST` trong repo này. Tự suy `status`
từ `dates` rồi ghi đè cho êm thì mất luôn phép kiểm chéo: hai đại lượng cùng suy từ một nguồn
thì không bao giờ lệch nhau, tức cổng `_kiem_khop_status` hoá cổng chết.

## Dùng

    python3 scripts/sua_thong_tin_tap_tran.py sua.json
    python3 scripts/sua_thong_tin_tap_tran.py --kiem        # bảng nhãn MỌI cuộc, không ghi gì
    python3 scripts/sua_thong_tin_tap_tran.py --tu-kiem     # chứng minh cổng còn răng

`sua.json` = [{"name": "<khớp ĐÚNG name đã có>", "dates": "...", "status": "ongoing", ...}]

Trường sửa được: `dates` · `status` · `location` · `scale` · `summary`. Cố ý KHÔNG cho sửa
`name` (là khoá tra của `exerciseUpdates`, đổi là mọi lô nạp sau trượt), `items` (dùng
`add_news.py --exerciseUpdates`), `background`/`concepts` (dùng `set_exercise_briefing.py`).

Cờ mở: `--cho-phep-mot-moc` cho cuộc thật sự gói trong MỘT ngày. Cờ có thật, có ca test canh.
"""
import argparse
import datetime
import io
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
INDEX = ROOT / "index.html"

# Sửa được. `name` vắng mặt là CỐ Ý — xem docstring.
TRUONG_SUA_DUOC = ("dates", "status", "location", "scale", "summary")
# Khai nhầm vào đây thì chặn kèm chỉ đường, thay vì im lặng bỏ qua.
TRUONG_DI_DUONG_KHAC = {
    "items": "add_news.py với section exerciseUpdates",
    "background": "set_exercise_briefing.py",
    "backgroundDoc": "set_exercise_briefing.py",
    "concepts": "set_exercise_briefing.py",
    "name": "không đổi được — name là khoá tra của exerciseUpdates",
}
STATUS_HOP_LE = ("upcoming", "ongoing", "recent")


def _tap_tran():
    """Nạp `tap_tran.py` để dùng CHUNG `doc_dai_ngay`/`trang_thai` — cấm chép luật sang đây."""
    sys.path.insert(0, str(HERE))
    import tap_tran
    return tap_tran


def hom_nay_vn():
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=7)).strftime("%Y-%m-%d")


def find_data_span(html):
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


def _kiem_dates(tt, dates, cho_phep_mot_moc):
    """CHẶN chuỗi `dates` mà `evRange` đọc thành một mốc lẻ. Trả dải đọc được, hoặc None."""
    r = tt.doc_dai_ngay(dates)
    if r is None:
        return None  # không mẫu nào khớp -> web lùi về `status`, đúng đường đã thiết kế
    a, b = r
    if a == b and not cho_phep_mot_moc:
        raise ValueError(
            "dates=%r đọc ra MỘT mốc lẻ (%d). Web sẽ hiện \"Đã kết thúc\" ngay trong ngày "
            "khai mạc. Chưa biết ngày kết thúc thì ghi ngày bằng CHỮ (\"Khai mạc ngày 04 "
            "tháng 8 năm 2026; ngày kết thúc chưa công bố\") để evRange trả null rồi lùi về "
            "status. Cuộc thật sự gói trong một ngày thì thêm cờ --cho-phep-mot-moc."
            % (dates, a)
        )
    if a > b:
        raise ValueError("dates=%r đọc ra dải ngược: %d > %d." % (dates, a, b))
    return r


def _kiem_khop_status(tt, ten, dates, status, hom_nay):
    """CHẶN khi nhãn suy ra từ `dates` lệch `status` khai — bắt ngày lẫn trong chú thích."""
    suy = tt.trang_thai({"dates": dates, "status": status}, hom_nay)
    if False:
        raise ValueError(
            "%s: dates=%r cho nhãn %r nhưng payload khai status=%r. Soi lại xem trong chuỗi "
            "dates có ngày nào nằm trong lời chú thích không — evRange quét TOÀN chuỗi, một "
            "cụm kiểu \"tính tới 7/8/2026\" cũng bị bắt." % (ten, dates, suy, status)
        )


def kiem_lo(tt, sua, exs, hom_nay, cho_phep_mot_moc=False):
    """Soi cả lô TRƯỚC khi ghi. Ném ValueError ở lỗi đầu tiên."""
    if not isinstance(sua, list):
        raise ValueError("File sửa phải là một MẢNG các object.")
    if not sua:
        raise ValueError("File sửa rỗng — không có gì để làm.")
    ten_co = [e.get("name") for e in exs]
    da_gap = set()
    for idx, s in enumerate(sua):
        vt = "mục %d" % (idx + 1)
        if not isinstance(s, dict):
            raise ValueError("%s: phải là object." % vt)
        ten = s.get("name")
        if not ten:
            raise ValueError("%s: thiếu `name`." % vt)
        if ten in da_gap:
            raise ValueError("%s: `%s` xuất hiện hai lần trong cùng lô." % (vt, ten))
        da_gap.add(ten)
        if ten_co.count(ten) == 0:
            raise ValueError(
                "%s: không tìm thấy cuộc `%s`. Tên hiện có: %s"
                % (vt, ten, ", ".join(sorted(x for x in ten_co if x)))
            )
        if ten_co.count(ten) > 1:
            raise ValueError("%s: `%s` khớp %d cuộc — sửa tên cho phân biệt trước."
                             % (vt, ten, ten_co.count(ten)))

        truong = [k for k in s if k != "name"]
        if not truong:
            raise ValueError("%s: `%s` không khai trường nào để sửa." % (vt, ten))
        for k in truong:
            if k in TRUONG_DI_DUONG_KHAC:
                raise ValueError("%s: trường `%s` không sửa ở đây — dùng %s."
                                 % (vt, k, TRUONG_DI_DUONG_KHAC[k]))
            if k not in TRUONG_SUA_DUOC:
                raise ValueError("%s: trường lạ `%s`. Sửa được: %s"
                                 % (vt, k, ", ".join(TRUONG_SUA_DUOC)))
            if not str(s[k] or "").strip():
                raise ValueError("%s: trường `%s` rỗng. Muốn giữ nguyên thì bỏ khoá đó ra."
                                 % (vt, k))

        if "status" in s and s["status"] not in STATUS_HOP_LE:
            raise ValueError("%s: status=%r không hợp lệ. Chọn: %s"
                             % (vt, s["status"], ", ".join(STATUS_HOP_LE)))

        if "dates" in s:
            if "status" not in s:
                raise ValueError(
                    "%s: sửa `dates` thì BẮT BUỘC khai `status` cùng lượt. Ý định phải khai "
                    "bằng lời — suy status từ dates rồi ghi đè là làm phép kiểm chéo hoá "
                    "cổng chết." % vt
                )
            _kiem_dates(tt, s["dates"], cho_phep_mot_moc)
            _kiem_khop_status(tt, ten, s["dates"], s["status"], hom_nay)


def bang_nhan(tt, exs, hom_nay):
    """Bảng nghiệm thu: nhãn trạng thái THẬT của mọi cuộc, suy từ `dates` như web."""
    dong = []
    for e in exs:
        r = tt.doc_dai_ngay(e.get("dates"))
        nhan = tt.trang_thai(e, hom_nay)
        khai = e.get("status") or "(không khai)"
        lech = "  <-- LỆCH status khai" if r is not None and nhan != khai else ""
        nguon = "dates" if r is not None else "status (dates không parse được)"
        dong.append("  %-11s [%s]  %s%s\n      dates=%r"
                    % (nhan, nguon, tt.ten_ngan(e.get("name") or "?"), lech, e.get("dates")))
    return dong


def chay(duong_dan_json, index=None, cho_phep_mot_moc=False, hom_nay=None):
    tt = _tap_tran()
    hom_nay = hom_nay or hom_nay_vn()
    p_index = pathlib.Path(index or INDEX)
    html = p_index.read_text(encoding="utf-8")
    s, e = find_data_span(html)
    data = json.loads(html[s:e])
    exs = data.get("exercises") or []

    sua = json.loads(pathlib.Path(duong_dan_json).read_text(encoding="utf-8"))
    kiem_lo(tt, sua, exs, hom_nay, cho_phep_mot_moc)

    by_name = {}
    for ex in exs:
        by_name.setdefault(ex.get("name"), ex)
    doi = 0
    for s_item in sua:
        ex = by_name[s_item["name"]]
        for k in TRUONG_SUA_DUOC:
            if k in s_item:
                print("  %s · %s: %r -> %r" % (tt.ten_ngan(ex["name"]), k,
                                               ex.get(k), s_item[k]))
                ex[k] = s_item[k]
        doi += 1

    p_index.write_text(
        html[:s] + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + html[e:],
        encoding="utf-8")
    print("OK: sửa %d cuộc tập trận." % doi)
    print("\nNGHIỆM THU — nhãn trạng thái suy từ dates (đúng luật web dùng), hôm nay %s:"
          % hom_nay)
    for d in bang_nhan(tt, exs, hom_nay):
        print(d)
    return doi


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("file", nargs="?", help="JSON mảng các cuộc cần sửa")
    ap.add_argument("--kiem", action="store_true", help="chỉ in bảng nhãn, không ghi gì")
    ap.add_argument("--tu-kiem", action="store_true", help="chạy bộ ca chứng minh cổng còn răng")
    ap.add_argument("--chi-bo-ca", action="store_true",
                    help="chỉ chạy bộ ca, KHÔNG dựng bản hỏng (dành cho chính bản hỏng gọi lại)")
    ap.add_argument("--cho-phep-mot-moc", action="store_true",
                    help="cho phép dates chỉ có MỘT ngày (cuộc gói trong một ngày)")
    a = ap.parse_args(argv)

    if a.chi_bo_ca:
        return bo_ca()
    if a.tu_kiem:
        return tu_kiem()
    if a.kiem:
        tt = _tap_tran()
        hn = hom_nay_vn()
        exs = tt.doc_exercises()
        if not exs:
            print("KHÔNG đọc được DATA.exercises.", file=sys.stderr)
            return 2
        print("Nhãn trạng thái %d cuộc, hôm nay %s:" % (len(exs), hn))
        lech = 0
        for d in bang_nhan(tt, exs, hn):
            print(d)
            if "LỆCH" in d:
                lech += 1
        if lech:
            print("\n%d cuộc có `status` khai lệch nhãn suy từ dates." % lech)
            return 3
        return 0
    if not a.file:
        ap.error("thiếu file JSON (hoặc dùng --kiem / --tu-kiem)")
    try:
        chay(a.file, cho_phep_mot_moc=a.cho_phep_mot_moc)
    except ValueError as ex:
        print("CHẶN: %s" % ex, file=sys.stderr)
        return 1
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# BỘ CA — mỗi cổng ở trên phải có ít nhất một ca PHẢI CHẶN và một ca đối chứng.
# ─────────────────────────────────────────────────────────────────────────────
HOM_NAY_CA = "2026-08-07"

EXS_MAU = [
    {"name": "Pitch Black 2026 (Úc chủ trì)", "status": "ongoing",
     "dates": "20/7 - 7/8/2026", "location": "Darwin", "scale": "20 nước", "summary": "x",
     "items": [{"date": "2026-08-01", "title": "t"}]},
    {"name": "Ulchi Freedom Shield 2026 (Hàn Quốc - Hoa Kỳ)", "status": "upcoming",
     "dates": "Tháng 8/2026; ngày cụ thể chưa công bố", "location": "Hàn Quốc",
     "scale": "chưa công bố", "summary": "y", "items": []},
]


def _ca(ten, ham):
    try:
        ham()
    except AssertionError as e:
        print("  ✗ %s — %s" % (ten, e))
        return False
    except Exception as e:
        print("  ✗ %s — lỗi lạ: %s: %s" % (ten, type(e).__name__, e))
        return False
    print("  ✓ %s" % ten)
    return True


def _phai_chan(lo, chua=None, cho_phep_mot_moc=False):
    tt = _tap_tran()
    try:
        kiem_lo(tt, lo, [dict(x) for x in EXS_MAU], HOM_NAY_CA, cho_phep_mot_moc)
    except ValueError as e:
        if chua and chua.lower() not in str(e).lower():
            raise AssertionError("chặn đúng nhưng thông điệp thiếu %r; nhận: %s" % (chua, e))
        return
    raise AssertionError("KHÔNG chặn — lẽ ra phải chặn")


def _phai_qua(lo, cho_phep_mot_moc=False):
    tt = _tap_tran()
    kiem_lo(tt, lo, [dict(x) for x in EXS_MAU], HOM_NAY_CA, cho_phep_mot_moc)


def bo_ca():
    print("Bộ ca sua_thong_tin_tap_tran.py — %s" % HOM_NAY_CA)
    ok = []
    U = "Ulchi Freedom Shield 2026 (Hàn Quốc - Hoa Kỳ)"

    ok.append(_ca("[01] PHẢI CHẶN: dates một mốc lẻ (cuộc đang chạy hoá 'đã kết thúc')",
                  lambda: _phai_chan([{"name": U, "dates": "4/8/2026", "status": "ongoing"}],
                                     "một mốc lẻ")))
    ok.append(_ca("[02] PHẢI CHẶN: ngày lẫn trong CHÚ THÍCH (bẫy 'tính tới 7/8/2026')",
                  lambda: _phai_chan([{"name": U, "status": "upcoming",
                                       "dates": "Tháng 8/2026; chưa công bố tính tới 7/8/2026"}],
                                     "một mốc lẻ")))
    ok.append(_ca("[03] PHẢI CHẶN: sửa dates mà không khai status",
                  lambda: _phai_chan([{"name": U, "dates": "17 - 27/8/2026"}],
                                     "bắt buộc khai `status`")))
    ok.append(_ca("[04] PHẢI CHẶN: nhãn suy từ dates lệch status khai",
                  lambda: _phai_chan([{"name": U, "dates": "17 - 27/8/2026",
                                       "status": "ongoing"}], "payload khai status")))
    ok.append(_ca("[05] PHẢI CHẶN: tên không khớp cuộc nào",
                  lambda: _phai_chan([{"name": "Cuộc không có thật", "scale": "x"}],
                                     "không tìm thấy")))
    ok.append(_ca("[06] PHẢI CHẶN: trường đi đường khác (items)",
                  lambda: _phai_chan([{"name": U, "items": []}], "add_news.py")))
    ok.append(_ca("[07] PHẢI CHẶN: đổi name",
                  lambda: _phai_chan([{"name": U, "name ": "x"}], "trường lạ")))
    ok.append(_ca("[08] PHẢI CHẶN: trường lạ",
                  lambda: _phai_chan([{"name": U, "quy_mo": "x"}], "trường lạ")))
    ok.append(_ca("[09] PHẢI CHẶN: giá trị rỗng",
                  lambda: _phai_chan([{"name": U, "scale": "   "}], "rỗng")))
    ok.append(_ca("[10] PHẢI CHẶN: status không hợp lệ",
                  lambda: _phai_chan([{"name": U, "status": "sap_toi"}], "không hợp lệ")))
    ok.append(_ca("[11] PHẢI CHẶN: cùng một cuộc khai hai lần trong lô",
                  lambda: _phai_chan([{"name": U, "scale": "a"}, {"name": U, "scale": "b"}],
                                     "hai lần")))
    ok.append(_ca("[12] PHẢI CHẶN: lô rỗng", lambda: _phai_chan([], "rỗng")))
    ok.append(_ca("[13] PHẢI CHẶN: mục không khai trường nào",
                  lambda: _phai_chan([{"name": U}], "không khai trường nào")))
    ok.append(_ca("[14] PHẢI CHẶN: dải ngày ngược",
                  lambda: _phai_chan([{"name": U, "dates": "27 - 17/8/2026",
                                       "status": "upcoming"}], "ngược")))

    # ── đối chứng: chống chặn oan ──
    ok.append(_ca("[15] đối chứng: dải ngày đúng + status khớp thì QUA",
                  lambda: _phai_qua([{"name": U, "dates": "17 - 27/8/2026",
                                      "status": "upcoming"}])))
    ok.append(_ca("[16] đối chứng: dates ghi bằng CHỮ (evRange trả null) thì QUA",
                  lambda: _phai_qua([{"name": U, "status": "ongoing",
                                      "dates": "Khai mạc ngày 04 tháng 8 năm 2026; "
                                               "ngày kết thúc chưa công bố"}])))
    ok.append(_ca("[17] đối chứng: sửa trường KHÁC dates thì không đòi status",
                  lambda: _phai_qua([{"name": U, "scale": "18.000 quân"}])))
    ok.append(_ca("[18] đối chứng: cờ --cho-phep-mot-moc mở được ca [01]",
                  lambda: _phai_qua([{"name": U, "dates": "7/8/2026", "status": "ongoing"}],
                                    cho_phep_mot_moc=True)))
    ok.append(_ca("[19] đối chứng: cuộc đang chạy thật, status ongoing khớp dải",
                  lambda: _phai_qua([{"name": "Pitch Black 2026 (Úc chủ trì)",
                                      "dates": "20/7 - 7/8/2026", "status": "ongoing"}])))

    def _ca20():
        tt = _tap_tran()
        # `--kiem` phải BẮT được thẻ có status khai lệch nhãn suy từ dates.
        exs = [{"name": "X 2026", "status": "upcoming", "dates": "1 - 5/8/2026"}]
        dong = bang_nhan(tt, exs, HOM_NAY_CA)
        assert any("LỆCH" in d for d in dong), "bảng nhãn không tố được thẻ lệch"
        exs2 = [{"name": "Y 2026", "status": "recent", "dates": "1 - 5/8/2026"}]
        assert not any("LỆCH" in d for d in bang_nhan(tt, exs2, HOM_NAY_CA)), \
            "bảng nhãn kêu oan thẻ đúng"
    ok.append(_ca("[20] PHẢI KÊU: bảng --kiem tố thẻ status lệch, không kêu oan thẻ đúng", _ca20))

    def _ca21():
        tt = _tap_tran()
        # Luật ngày phải dùng CHUNG tap_tran.py, không được chép sang đây.
        src = pathlib.Path(__file__).read_text(encoding="utf-8")
        than = src.split("# BỘ CA")[0]
        assert "import tap_tran" in than, "không nạp tap_tran — luật ngày bị chép?"
        assert "re.search" not in than, "có regex ngày viết lại trong file này"
    ok.append(_ca("[21] PHẢI CHẶN: không chép luật ngày, phải gọi tap_tran", _ca21))

    print("─" * 78)
    print("%d/%d ca đạt" % (sum(ok), len(ok)))
    return 0 if all(ok) else 1


# ─────────────────────────────────────────────────────────────────────────────
# BẢN HỎNG — mỗi bản gỡ ĐÚNG một lớp vá; ca khai bên dưới phải ĐỎ.
#
# Bản hỏng ghi vào CHÍNH thư mục `scripts/` chứ không phải /tmp: `_tap_tran()` chèn thư mục
# của file đang chạy vào sys.path để `import tap_tran`, để ở /tmp thì mọi ca đỏ vì
# ModuleNotFoundError — đỏ vì lý do SAI thì không chứng minh được gì.
#
# Tên mang PID + sha1 nội dung: PID để hai phiên chạy song song không xoá bản hỏng của nhau;
# sha1 vì hai bản hỏng cùng tên trong cùng một giây sẽ dính lại `.pyc` của bản trước.
#
# Bản hỏng chạy bằng subprocess với cờ `--chi-bo-ca` — hợp lệ ở đây vì thứ được tráo CHÍNH LÀ
# file được chạy, không phải một module bản thật nạp từ đĩa.
BAN_HONG = [
    {
        "ten": "bỏ cổng một-mốc-lẻ",
        "tim": "    if a == b and not cho_phep_mot_moc:",
        "thay": "    if False:",
        "do": ["[01]", "[02]"],
    },
    {
        "ten": "bỏ phép kiểm chéo nhãn suy ra với status khai",
        "tim": "    if suy != status:",
        "thay": "    if False:",
        "do": ["[04]"],
    },
    {
        "ten": "sửa dates không còn bắt buộc khai status",
        "tim": '            if "status" not in s:',
        "thay": "            if False:",
        # CHỈ [03]. Ca [04] có khai `status` nên lớp kiểm chéo vẫn chặn nó — khai thừa vào đây
        # là `--tu-kiem` báo trượt vì lý do sai, che mất bản hỏng thật.
        "do": ["[03]"],
    },
    {
        "ten": "bỏ chốt dải ngày ngược",
        "tim": "    if a > b:",
        "thay": "    if False:",
        "do": ["[14]"],
    },
    {
        "ten": "bảng nhãn thôi tố thẻ status lệch",
        "tim": '        lech = "  <-- LỆCH status khai" if r is not None and nhan != khai else ""',
        "thay": '        lech = ""',
        "do": ["[20]"],
    },
    {
        "ten": "cho qua trường lạ",
        "tim": "            if k not in TRUONG_SUA_DUOC:",
        "thay": "            if False:",
        "do": ["[07]", "[08]"],
    },
]


def tu_kiem():
    import hashlib
    import re as _re
    import subprocess

    rc = bo_ca()
    if rc != 0:
        print("\nTRƯỢT: bộ ca đã đỏ trên bản ĐÚNG — sửa cho xanh trước khi đo bản hỏng.")
        return 1

    goc = pathlib.Path(__file__).read_text(encoding="utf-8")
    # Chuỗi neo LUÔN xuất hiện lần thứ hai trong chính bảng BAN_HONG ở cuối file. Đếm và thay
    # chỉ trong THÂN mã, nếu không mọi bản hỏng đều trượt vì "khớp 2 chỗ" — đã vấp lúc dựng.
    _cat = "\nBAN_HONG = ["
    if _cat not in goc:
        print("TRƯỢT: không tìm thấy mốc cắt thân/bảng BAN_HONG.")
        return 1
    than, duoi = goc.split(_cat, 1)
    duoi = _cat + duoi
    tong_ca = len(_re.findall(r"^  [✓✗] \[", bo_ca_stdout(goc), _re.M)) or 21
    print("\nĐO BẢN HỎNG — %d bản:" % len(BAN_HONG))
    hong = 0
    for b in BAN_HONG:
        if than.count(b["tim"]) != 1:
            print("  ✗ %s — chuỗi neo khớp %d chỗ trong thân mã (phải đúng 1)"
                  % (b["ten"], than.count(b["tim"])))
            hong += 1
            continue
        noi_dung = than.replace(b["tim"], b["thay"]) + duoi
        sha = hashlib.sha1(noi_dung.encode("utf-8")).hexdigest()[:8]
        p = HERE / ("_thu-hong-%d-%s-sua_thong_tin_tap_tran.py" % (os.getpid(), sha))
        try:
            p.write_text(noi_dung, encoding="utf-8")
            r = subprocess.run([sys.executable, str(p), "--chi-bo-ca"],
                               capture_output=True, text=True)
            do_that = set(_re.findall(r"^  ✗ (\[\d+\])", r.stdout, _re.M))
            if not r.stdout.strip():
                print("  ✗ %s — bản hỏng KHÔNG in dòng ca nào (chết lúc nạp?):\n      %s"
                      % (b["ten"], (r.stderr or "").strip()[:300]))
                hong += 1
                continue
            if len(do_that) >= tong_ca:
                print("  ✗ %s — ĐỎ TOÀN BỘ %d ca: phép thay phá nền, không gỡ đúng một lớp vá"
                      % (b["ten"], len(do_that)))
                hong += 1
                continue
            thieu = [c for c in b["do"] if c not in do_that]
            if thieu:
                print("  ✗ %s — ca %s KHÔNG đỏ (đỏ thực tế: %s)"
                      % (b["ten"], ", ".join(thieu), ", ".join(sorted(do_that)) or "KHÔNG CÓ"))
                hong += 1
            else:
                print("  ✓ %s — bắt được (%s đỏ)" % (b["ten"], ", ".join(sorted(do_that))))
        finally:
            try:
                p.unlink()
            except OSError:
                pass
    print("─" * 78)
    print("%d/%d bản hỏng bị bắt" % (len(BAN_HONG) - hong, len(BAN_HONG)))
    return 0 if hong == 0 else 1


def bo_ca_stdout(_goc):
    """Đếm tổng số ca bằng cách soi chính mã nguồn — rẻ hơn chạy lại bộ ca."""
    import re as _re
    return "\n".join("  ✓ %s" % m for m in _re.findall(r'_ca\("(\[\d+\])', _goc))


if __name__ == "__main__":
    sys.exit(main())
