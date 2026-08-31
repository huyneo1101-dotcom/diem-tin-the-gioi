#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐO GIỜ BẢN TIN TỚI TAY — phép đo KẾT QUẢ CUỐI, không đo "phiên có chạy không".

⚠ VÌ SAO CÓ FILE NÀY (Huy chốt 31/08/2026, nguyên văn *"nói được không làm được?"*):
Mọi phép đo đang có đều hỏi *quy trình đã chạy chưa* — job nổ đúng giờ chưa, workflow xanh
chưa, khoá state.json có chưa. Cả ba đều báo ĐẠT trong hai đêm 30 và 31/08, trong khi thứ
Huy thật sự nhận được là: bản tin sáng tới lúc 01:08 và 01:25, còn bản tin TỐI mất hẳn.
Không phép đo nào hỏi câu duy nhất đáng hỏi — **bản tin tới tay lúc mấy giờ**.

Nguồn sự thật là `logs/da-gui-email.json` (sổ đã gửi), vì đó là chỗ ghi lại lần gửi THẬT tới
mọi kênh, không phải cờ tiến trình. Phép đo hỏi đúng 03 câu:
  (i)  ca `sang` hôm nay có gửi không, và có kịp HẠN CHÓT 04:30 giờ VN không;
  (ii) ca `toi` hôm qua có gửi không, và có kịp hạn 22:00 không;
  (iii) có ca nào vắng mặt hẳn không.
Cạnh dưới lấy từ `state.py::KHUNG_GIO`, cạnh trên lấy từ `state.py::HAN_CHOT` — MỘT bản
gốc cho mỗi số, không chép số sang đây. Hai cạnh hai nguồn là cố ý: khung khởi động rộng
để lớp chạy bù còn làm được việc, còn hạn chót là cam kết với người đọc.

⛔ HẠN CHÓT CA SÁNG 04:30 do Huy chốt 31/08/2026, đừng nới cho vừa lịch chạy.

Vì sao ca `toi` xét NGÀY HÔM QUA: chạy phép đo lúc 08:00 sáng thì ca tối của hôm nay còn
chưa tới giờ, hỏi nó là kêu oan mỗi sáng.

Dùng:
    python3 scripts/do_gio_ban_tin.py            # bảng người đọc, mã thoát 0/1/2
    python3 scripts/do_gio_ban_tin.py --json     # dữ liệu thô cho khoe.py
Mã thoát: 0 = đúng giờ · 1 = SAI GIỜ hoặc VẮNG ca · 2 = không đo được (sổ hỏng/thiếu).
"""
import argparse
import datetime
import importlib.util
import json
import os
import pathlib
import sys
import zoneinfo

# DOGIO_ROOT: seam CHỈ dùng cho bộ test — bản hỏng nằm ở thư mục tạm vẫn phải trỏ về repo
# thật để đọc state.py và sổ. Không có seam này thì bản hỏng chết vì SAI ĐƯỜNG DẪN, và tự
# kiểm sẽ báo "bắt được lỗi" trong khi thật ra nó chưa hề chạm tới lỗi được cấy.
ROOT = pathlib.Path(os.environ.get("DOGIO_ROOT") or pathlib.Path(__file__).resolve().parent.parent)
SO_MAC_DINH = ROOT / "logs" / "da-gui-email.json"
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Ca có bản tin gửi đi. `sukien` đi kèm ca sáng, không phải bản tin riêng nên không xét giờ.
CA_XET = ("sang", "toi")


def bang_gio() -> tuple[dict, dict]:
    """(KHUNG_GIO, HAN_CHOT) đọc từ chính state.py — một bản gốc, cấm chép số sang đây."""
    sp = importlib.util.spec_from_file_location("st", ROOT / "scripts" / "state.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return dict(m.KHUNG_GIO), dict(m.HAN_CHOT)


def doc_so(duong_dan: pathlib.Path) -> list:
    """Các lần gửi trong sổ. Ném lỗi nếu không đọc được — fail về phía KÊU, không phía im."""
    d = json.loads(duong_dan.read_text(encoding="utf-8"))
    lan = d.get("lan_gui")
    if not isinstance(lan, list):
        raise ValueError("sổ không có mảng `lan_gui`")
    return lan


def lan_gui_cua(lan_gui: list, ca: str, ngay: str):
    """Lần gửi MỚI NHẤT của một ca trong một ngày VN, hoặc None."""
    hop = []
    for l in lan_gui:
        if l.get("buoi") != ca:
            continue
        try:
            t = datetime.datetime.fromisoformat(l["luc"]).astimezone(VN)
        except (KeyError, TypeError, ValueError):
            continue
        if t.date().isoformat() == ngay:
            hop.append(t)
    return max(hop) if hop else None


def do(duong_dan=None, bay_gio=None) -> dict:
    duong_dan = pathlib.Path(duong_dan or SO_MAC_DINH)
    bay_gio = bay_gio or datetime.datetime.now(VN)
    lan_gui = doc_so(duong_dan)
    khung, han = bang_gio()
    hom_nay = bay_gio.date()
    hom_qua = hom_nay - datetime.timedelta(days=1)

    ket = []
    for ca in CA_XET:
        # Ca `toi` xét hôm qua: lúc chạy phép đo (sáng) ca tối hôm nay chưa tới giờ.
        ngay = (hom_qua if ca == "toi" else hom_nay).isoformat()
        # Cạnh dưới lấy từ khung khởi động, cạnh trên là HẠN CHÓT — bản tin tới SỚM hơn
        # khung là chuyện tốt nhưng vẫn bất thường (đúng cảnh 01:25 sáng 31/08), tới MUỘN
        # hơn hạn là vỡ cam kết. Hai cạnh, hai nguồn, cố ý.
        dau = khung[ca][0]
        cuoi = han[ca]
        t = lan_gui_cua(lan_gui, ca, ngay)
        if t is None:
            # Chưa tới hạn thì chưa kết luận vắng — bản tin còn có thể tới.
            phut_gio = bay_gio.hour * 60 + bay_gio.minute
            chua_toi_han = phut_gio <= cuoi if ca == "sang" else False
            ket.append({"ca": ca, "ngay": ngay,
                        "trang_thai": "CHUA_TOI_GIO" if chua_toi_han else "VANG",
                        "gio": None, "khung": [dau, cuoi]})
            continue
        phut = t.hour * 60 + t.minute
        trong = dau <= phut <= cuoi
        ket.append({
            "ca": ca, "ngay": ngay,
            "trang_thai": "DUNG_GIO" if trong else "SAI_GIO",
            "gio": f"{t:%H:%M}", "khung": [dau, cuoi],
        })
    return {"luc_do": f"{bay_gio:%Y-%m-%d %H:%M}", "ket": ket}


def hhmm(phut: int) -> str:
    return f"{phut // 60:02d}:{phut % 60:02d}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--so", help="đường dẫn sổ đã gửi (mặc định logs/da-gui-email.json)")
    ap.add_argument("--gio-gia", help="ghim mốc hiện tại dạng ISO — CHỈ dùng cho bộ test")
    ap.add_argument("--json", action="store_true", help="in dữ liệu thô")
    a = ap.parse_args()

    bay_gio = None
    if a.gio_gia:
        bay_gio = datetime.datetime.fromisoformat(a.gio_gia).astimezone(VN)
    try:
        r = do(a.so, bay_gio)
    except (OSError, ValueError) as e:
        msg = f"KHONG DO DUOC: {e.__class__.__name__}: {e}"
        print(json.dumps({"loi": msg}) if a.json else f"⚠️  {msg}")
        return 2

    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(f"GIỜ BẢN TIN TỚI TAY (đo lúc {r['luc_do']} giờ VN)")
        for k in r["ket"]:
            dau, cuoi = k["khung"]
            bieu = {"DUNG_GIO": "✓", "SAI_GIO": "✗", "VANG": "✗",
                    "CHUA_TOI_GIO": "·"}[k["trang_thai"]]
            gio = k["gio"] or "chưa gửi"
            print(f"  {bieu} ca {k['ca']:<5} {k['ngay']}  gửi {gio:<9} "
                  f"khung {hhmm(dau)}-{hhmm(cuoi)}  {k['trang_thai']}")
    return 1 if any(k["trang_thai"] in ("SAI_GIO", "VANG") for k in r["ket"]) else 0


if __name__ == "__main__":
    sys.exit(main())
