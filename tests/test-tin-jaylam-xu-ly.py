#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test cho `scripts/tin_jaylam.py` — file Jay Lâm gửi làm BỘ LỌC (Huy đảo nguyên tắc 01/08/2026).

    python3 tests/test-tin-jaylam-xu-ly.py
    python3 tests/test-tin-jaylam-xu-ly.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

Bộ này TRƯỚC 01/08/2026 đo bước "biến tin Jay Lâm thành tin chuẩn để đăng". Vai đó đã bỏ:
file Jay Lâm không còn đóng góp dòng nào vào bản tin. Ba lệnh nay đo ở đây:
  `--liet-ke`   in dữ liệu đối chiếu (toàn văn nếu chưa trích, bảng gọn nếu đã trích) và
                đóng sổ dòng hết khung ngày;
  `--ghi`       lưu BẢNG ĐỐI CHIẾU trích từ file Jay;
  `--ghi-loai`  ghi sổ `logs/trung-jaylam.json` — tin CỦA MÌNH bị bỏ vì Jay Lâm đã có.

Đây là một CỔNG (guardrail cho dữ liệu agent viết ra) nên theo mục 17 CLAUDE.md phải có ca
PHẢI CHẶN thật, không chỉ ca cho-qua: một guardrail câm nhìn y hệt guardrail sạch — đầu vào
đúng thì cả hai đều im lặng cho qua.

Hai chiều lệch KHÁC HẲN nhau, mỗi chiều có ca canh riêng:
  - `--ghi` trích SÓT  -> tin Jay Lâm đã có vẫn lọt vào bản tin (lặp tin, Huy thấy được);
  - `--ghi-loai` khai THỪA -> tin của mình biến mất khỏi bản tin (MẤT TIN, không ai thấy).
Vì thế guardrail của `--ghi-loai` chặt hơn: bắt buộc `trung_voi` để soi ngược được.

Không chạm mạng: `subprocess.run` của module bị thay bằng bản giả ghi lại lệnh PATCH.
Sổ loại được ghim vào file tạm — KHÔNG đọc/ghi sổ thật của repo.
"""
import contextlib
import datetime
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess as SP
import sys
import tempfile
import zoneinfo

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SC = pathlib.Path(os.environ.get("TINJAYLAM_DIR") or (REPO / "scripts"))
sys.path.insert(0, str(SC))

import tin_jaylam as TJ          # noqa: E402

VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
NOW = datetime.datetime(2026, 8, 2, 21, 0, tzinfo=VN)

CA = []


def kiem(ten, dat):
    dat = bool(dat)
    CA.append((ten, dat))
    print(("✓" if dat else "✗") + " " + ten)


def dong(id_, created_at, noi_dung=None, **kw):
    r = {"id": id_, "ten": "Jay Lâm", "ten_file": f"f{id_}.docx",
         "noi_dung": noi_dung if noi_dung is not None else f"Nội dung file số {id_}",
         "created_at": created_at, "da_xu_ly": False, "tom_tat": None}
    r.update(kw)
    return r


HANG_CHO = [dong(1, "2026-08-02T03:00:00Z"), dong(2, "2026-08-01T03:00:00Z")]

TIN_OK = [{"tieu_de": "Hạ viện Mỹ thông qua ngân sách quốc phòng",
           "url": "https://reuters.com/world/bai-cu-the-123"},
          {"tieu_de": "Philippines tuần tra bãi cạn Scarborough", "url": ""}]


class GiaMang:
    """Thay `subprocess.run` của module: GET trả `rows`, PATCH ghi vào `self.patch`."""

    def __init__(self, rows=None, patch_hong=False):
        self.rows = HANG_CHO if rows is None else rows
        self.patch = []
        self.get = []          # URL của các lệnh ĐỌC — xem ca [39]
        self.patch_hong = patch_hong

    def __enter__(self):
        self.goc = TJ.subprocess.run
        self.goc_env = {k: os.environ.get(k) for k in ("SUPABASE_ANON_KEY", "DT_BOT_KEY")}
        os.environ["SUPABASE_ANON_KEY"] = "sb_publishable_test"
        os.environ["DT_BOT_KEY"] = "ma-test"
        rows, patch, get, hong = self.rows, self.patch, self.get, self.patch_hong

        def gia(args, **kw):
            class P:
                returncode = 0
                stdout = ""
                stderr = ""
            if "-X" in args and "PATCH" in args:
                patch.append(args)
                if hong:
                    P.returncode = 22
                return P
            get.extend(a for a in args if str(a).startswith("http"))
            P.stdout = json.dumps(rows, ensure_ascii=False)
            return P

        TJ.subprocess.run = gia
        return self

    def __exit__(self, *a):
        TJ.subprocess.run = self.goc
        for k, v in self.goc_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


class SoGia:
    """Ghim `TJ.SO_LOAI` vào file tạm — ca test TUYỆT ĐỐI không đọc/ghi sổ thật của repo.

    Sổ thật chỉ giữ `GIU_NGAY` ngày nên ca neo vào một ngày cụ thể sẽ tự tắt sau một tuần,
    tức bản hỏng lọt mà bảng vẫn xanh (luật đã đúc ở `loc_jaylam_ca_sang` 01/08/2026).
    """

    def __init__(self, noi=None):
        self.noi = noi

    def __enter__(self):
        self.goc = TJ.SO_LOAI
        self.d = pathlib.Path(tempfile.mkdtemp(prefix="so-loai-"))
        TJ.SO_LOAI = self.d / "logs" / "trung-jaylam.json"
        if self.noi is not None:
            TJ.SO_LOAI.parent.mkdir(parents=True, exist_ok=True)
            TJ.SO_LOAI.write_text(
                self.noi if isinstance(self.noi, str)
                else json.dumps(self.noi, ensure_ascii=False), encoding="utf-8")
        return self

    def doc(self):
        try:
            return json.loads(TJ.SO_LOAI.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def __exit__(self, *a):
        TJ.SO_LOAI = self.goc
        shutil.rmtree(self.d, ignore_errors=True)
        return False


def _chay(ham, muc, rows=None, patch_hong=False):
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    pathlib.Path(tmp).write_text(
        muc if isinstance(muc, str) else json.dumps(muc, ensure_ascii=False),
        encoding="utf-8")
    buf_out, buf_err = io.StringIO(), io.StringIO()
    try:
        with GiaMang(rows, patch_hong) as g, contextlib.redirect_stdout(buf_out), \
                contextlib.redirect_stderr(buf_err):
            ma = ham(tmp, now=NOW)
        return ma, buf_out.getvalue(), buf_err.getvalue(), g.patch
    finally:
        pathlib.Path(tmp).unlink(missing_ok=True)


def chay_ghi(muc, rows=None, patch_hong=False):
    """`--ghi` (bảng đối chiếu). Trả (mã, stdout, stderr, PATCH)."""
    return _chay(TJ.ghi_bang, muc, rows, patch_hong)


def chay_loai(muc, rows=None, so_cu=None):
    """`--ghi-loai` (sổ loại). Trả (mã, stderr, nội dung sổ sau khi ghi)."""
    with SoGia(so_cu) as s:
        ma, _out, err, _p = _chay(TJ.ghi_loai, muc, rows)
        return ma, err, s.doc()


def chay_liet_ke(rows=None):
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with GiaMang(rows) as g, contextlib.redirect_stdout(buf_out), \
            contextlib.redirect_stderr(buf_err):
        ma = TJ.in_hang_cho(now=NOW)
    return ma, buf_out.getvalue(), buf_err.getvalue(), g.patch


BANG_OK = {"id": 1, "tin": TIN_OK}
LOAI_OK = {"url": "https://thehill.com/tin-cua-minh-123",
           "tieu_de": "Uỷ ban Quân vụ điều trần về ngân sách quốc phòng",
           "trung_voi": "Điều trần ngân sách quốc phòng tại Hạ viện", "id_jay": 1}


# ================= A. `--ghi`: bảng đối chiếu =================
ma, out, err, patch = chay_ghi([BANG_OK])
kiem("[01] lô hợp lệ -> mã 0 và có đúng 1 lệnh PATCH", ma == 0 and len(patch) == 1)
_than = json.loads(patch[0][patch[0].index("-d") + 1]) if patch else {}
kiem("[02] PATCH đặt `da_xu_ly` và lưu bảng tin dạng JSON vào `tom_tat`",
     _than.get("da_xu_ly") is True
     and json.loads(_than.get("tom_tat") or "[]")[0]["tieu_de"].startswith("Hạ viện"))

ma, _, err, patch = chay_ghi([{"id": 99, "tin": TIN_OK}])
kiem("[03] PHẢI CHẶN: id không nằm trong khung ngày (id bịa/đã đóng sổ)",
     ma == 1 and not patch and "không nằm trong khung ngày" in err)

ma, _, err, patch = chay_ghi([BANG_OK, {"id": 1, "tin": TIN_OK}])
kiem("[04] PHẢI CHẶN: id xuất hiện hai lần trong file",
     ma == 1 and not patch and "hai lần" in err)

ma, _, err, patch = chay_ghi([{"id": 1, "tin": []}])
kiem("[05] PHẢI CHẶN: `tin` RỖNG — trích 0 tin nghĩa là bước đọc đã hỏng",
     ma == 1 and not patch and "KHÔNG rỗng" in err)

ma, _, err, patch = chay_ghi([{"id": 1, "tin": "mot chuoi"}])
kiem("[06] PHẢI CHẶN: `tin` không phải mảng", ma == 1 and not patch)

ma, _, err, patch = chay_ghi([{"id": 1, "tin": [{"tieu_de": "ngắn", "url": ""}]}])
kiem("[07] PHẢI CHẶN: tiêu đề quá NGẮN", ma == 1 and not patch and "tieu_de" in err)

ma, _, err, patch = chay_ghi([{"id": 1, "tin": [{"tieu_de": "x" * 250, "url": ""}]}])
kiem("[08] PHẢI CHẶN: tiêu đề quá DÀI", ma == 1 and not patch and "tieu_de" in err)

ma, _, err, patch = chay_ghi([{"id": 1, "tin": [{"tieu_de": "Tiêu đề đủ dài để qua cổng",
                                                 "url": "khong-phai-link"}]}])
kiem("[09] url sai dạng -> BỎ url, KHÔNG chặn cả lô (URL chỉ là chốt phụ)",
     ma == 0 and len(patch) == 1 and "bỏ URL" in err)

# Jay Lâm dẫn cả link trang chủ. `add_news.check_url_quality` chặn loại đó — dùng nó ở đây là
# mất nguyên bảng đối chiếu vì một link xấu, tức mất bộ lọc để đổi lấy một chốt phụ.
ma, _, err, patch = chay_ghi([{"id": 1, "tin": [
    {"tieu_de": "Tiêu đề đủ dài để qua cổng", "url": "https://reuters.com/"}]}])
kiem("[10] url TRANG CHỦ vẫn cho qua (KHÔNG dùng check_url_quality của add_news)",
     ma == 0 and len(patch) == 1)

ma, _, err, patch = chay_ghi({"id": 1})
kiem("[11] PHẢI CHẶN: file không phải MẢNG", ma == 1 and not patch)

ma, _, err, patch = chay_ghi([])
kiem("[12] mảng rỗng -> mã 0, không PATCH gì", ma == 0 and not patch)

# ⚠️ Phải đo ĐÚNG NHÁNH: `kiem_mot_bang` cũng chặn (id không thuộc tập rỗng), nên ca chỉ hỏi
# "có chặn không" thì bản hỏng gỡ chốt hàng-chờ-rỗng vẫn xanh — lớp sau che lớp trước. Đo
# chuỗi thông điệp mới phân biệt được hai nhánh.
ma, _, err, patch = chay_ghi([BANG_OK], rows=[])
kiem("[13] PHẢI CHẶN: hàng chờ rỗng -> không ghi mù, và kêu ĐÚNG nhánh đó",
     ma == 1 and not patch and "Hàng chờ rỗng" in err)

ma, _, err, patch = chay_ghi([BANG_OK], patch_hong=True)
kiem("[14] PATCH hỏng -> KÊU và trả mã 1 (không báo xong oan)",
     ma == 1 and "ghi hỏng" in err)

ma, _, err, patch = chay_ghi([BANG_OK, {"id": 2, "tin": [{"tieu_de": "ngắn"}]}])
kiem("[15] một mục sai chặn CẢ LÔ, không PATCH nửa vời", ma == 1 and not patch)

NHIEU_LINK = "\n".join(f"Tin {i} https://vidu.com/bai-{i}" for i in range(12))
ma, _, err, patch = chay_ghi(
    [{"id": 1, "tin": [{"tieu_de": "Chỉ trích được đúng một tin thôi", "url": ""}]}],
    rows=[dong(1, "2026-08-02T03:00:00Z", noi_dung=NHIEU_LINK)])
kiem("[16] file gốc 12 link mà trích 1 tin -> CẢNH BÁO trích sót (vẫn ghi)",
     ma == 0 and "TRÍCH SÓT" in err)

ma, _, err, patch = chay_ghi(
    [{"id": 1, "tin": [{"tieu_de": f"Tiêu đề tin số {i} đủ dài", "url": ""}
                       for i in range(6)]}],
    rows=[dong(1, "2026-08-02T03:00:00Z", noi_dung=NHIEU_LINK)])
kiem("[17] trích 6 tin / 12 link -> KHÔNG kêu oan trích sót",
     ma == 0 and "TRÍCH SÓT" not in err)


# ================= B. `--ghi-loai`: sổ loại =================
ma, err, so = chay_loai([LOAI_OK])
kiem("[18] lô hợp lệ -> mã 0, sổ có đúng 1 dòng kèm ngày",
     ma == 0 and so and len(so) == 1 and so[0]["ngay"] == "2026-08-02"
     and so[0]["url"] == LOAI_OK["url"])

ma, err, so = chay_loai([dict(LOAI_OK, url="")])
kiem("[19] PHẢI CHẶN: thiếu `url` tin của mình", ma == 1 and "url" in err)

ma, err, so = chay_loai([dict(LOAI_OK, url="chi-la-chuoi")])
kiem("[20] PHẢI CHẶN: `url` không phải http(s)", ma == 1)

ma, err, so = chay_loai([{k: v for k, v in LOAI_OK.items() if k != "trung_voi"}])
kiem("[21] PHẢI CHẶN: thiếu `trung_voi` -> không soi ngược được vì sao mất tin",
     ma == 1 and "trung_voi" in err)

ma, err, so = chay_loai([dict(LOAI_OK, trung_voi="ngắn")])
kiem("[22] PHẢI CHẶN: `trung_voi` quá ngắn", ma == 1 and "trung_voi" in err)

ma, err, so = chay_loai([dict(LOAI_OK, tieu_de="ngắn")])
kiem("[23] PHẢI CHẶN: `tieu_de` tin của mình quá ngắn", ma == 1 and "tieu_de" in err)

ma, err, so = chay_loai([{k: v for k, v in LOAI_OK.items() if k != "id_jay"}])
kiem("[24] PHẢI CHẶN: thiếu `id_jay`", ma == 1 and "id_jay" in err)

# Dòng Jay có thể vừa hết khung và bị đóng sổ giữa chừng — chặn ở đây là GIỮ LẠI một tin Huy
# đã xác định là trùng, tức bản tin lặp tin dù đã biết.
ma, err, so = chay_loai([dict(LOAI_OK, id_jay=999)])
kiem("[25] `id_jay` ngoài khung -> CẢNH BÁO nhưng VẪN ghi",
     ma == 0 and so and len(so) == 1 and "không còn trong khung" in err)

ma, err, so = chay_loai([LOAI_OK], so_cu=[
    dict(LOAI_OK, trung_voi="Lời khai CŨ", ngay="2026-08-01")])
kiem("[26] cùng url -> dedupe, bản MỚI thắng",
     ma == 0 and len(so) == 1 and so[0]["trung_voi"] != "Lời khai CŨ")

ma, err, so = chay_loai([LOAI_OK], so_cu=[
    {"url": "https://cu.com/qua-han", "tieu_de": "Tin rất cũ trong sổ",
     "trung_voi": "mảnh cũ bên Jay", "id_jay": 1, "ngay": "2026-07-01"}])
kiem("[27] dòng cũ hơn GIU_NGAY bị cắt khỏi sổ",
     ma == 0 and len(so) == 1 and so[0]["url"] == LOAI_OK["url"])

ma, err, so = chay_loai([LOAI_OK], so_cu=[
    {"url": "https://gan.com/con-han", "tieu_de": "Tin còn trong hạn giữ",
     "trung_voi": "mảnh bên Jay", "id_jay": 1, "ngay": "2026-08-01"}])
kiem("[28] dòng còn trong GIU_NGAY được GIỮ (không cắt oan)",
     ma == 0 and len(so) == 2)

ma, err, so = chay_loai([])
kiem("[29] mảng rỗng -> mã 0, không đụng sổ", ma == 0 and so is None)

ma, err, so = chay_loai([LOAI_OK], so_cu="{ khong phai json")
kiem("[30] sổ CŨ hỏng -> vẫn ghi được lô mới (không mất phần vừa khai)",
     ma == 0 and so and len(so) == 1)


# ================= C. `--liet-ke` =================
ma, out, err, patch = chay_liet_ke([dong(1, "2026-08-02T03:00:00Z",
                                         noi_dung="TOAN VAN FILE JAY")])
kiem("[31] dòng CHƯA trích -> in TOÀN VĂN cho agent đọc",
     ma == 0 and "TOAN VAN FILE JAY" in out and "CHƯA TRÍCH" in out)

DA_TRICH = dong(1, "2026-08-02T03:00:00Z", noi_dung="TOAN VAN FILE JAY",
                da_xu_ly=True,
                tom_tat=json.dumps([{"tieu_de": "Tin đã trích số một",
                                     "url": "https://a.com/1"}], ensure_ascii=False))
ma, out, err, patch = chay_liet_ke([DA_TRICH])
kiem("[32] dòng ĐÃ trích -> in BẢNG gọn, KHÔNG in lại toàn văn",
     ma == 0 and "Tin đã trích số một" in out and "TOAN VAN FILE JAY" not in out)

kiem("[33] dòng ĐÃ trích VẪN nằm trong hàng chờ (còn làm bộ lọc cho bản tin sau)",
     ma == 0 and "CÒN HIỆU LỰC LÀM BỘ LỌC" in out)

ma, out, err, patch = chay_liet_ke([dong(9, "2026-07-20T03:00:00Z")])
kiem("[34] dòng QUÁ KHUNG -> đóng sổ (PATCH da_gop) và không in toàn văn",
     ma == 10 and len(patch) == 1
     and any("da_gop" in str(a) for a in patch[0]))

# Khung phải là khung RỘNG NHẤT (3 ngày). Tin CNQS Mỹ của mình được nới 3 ngày lùi, nên bộ
# lọc phải sống ít nhất bằng đó — cắt ở 2 ngày là để lọt đúng nhóm đăng thưa nhất.
ma, out, err, patch = chay_liet_ke([dong(5, "2026-07-31T03:00:00Z")])
kiem("[35] file gửi 2 ngày trước VẪN trong khung (khung rộng 3 ngày, không phải 1)",
     ma == 0 and "CHƯA TRÍCH" in out and not patch)

ma, out, err, patch = chay_liet_ke([])
kiem("[36] hàng chờ rỗng -> mã 10", ma == 10)

HONG = dong(1, "2026-08-02T03:00:00Z", noi_dung="TOAN VAN FILE JAY",
            da_xu_ly=True, tom_tat="{ khong phai json")
ma, out, err, patch = chay_liet_ke([HONG])
kiem("[37] bảng đối chiếu lưu HỎNG -> lùi về in toàn văn + kêu (không mất bộ lọc)",
     ma == 0 and "TOAN VAN FILE JAY" in out and "lưu hỏng" in err)


# ================= D. định tuyến main() =================
_goc_bang, _goc_loai = TJ.ghi_bang, TJ.ghi_loai
_da_goi = []
TJ.ghi_bang = lambda p, now=None: _da_goi.append("bang") or 0
TJ.ghi_loai = lambda p, now=None: _da_goi.append("loai") or 0
try:
    with contextlib.redirect_stdout(io.StringIO()):
        TJ.main(["--ghi-loai", "/tmp/x.json"])
finally:
    TJ.ghi_bang, TJ.ghi_loai = _goc_bang, _goc_loai
kiem("[38] `--ghi-loai` KHÔNG bị `--ghi` nuốt (hai lệnh khác nhau)", _da_goi == ["loai"])

# ⚠️ Phải đo CHÍNH CHUỖI QUERY, không đo hành vi: `GiaMang` trả `rows` bất kể query, nên một
# bản hỏng thêm lại `da_xu_ly=eq.false` sẽ không đổi kết quả ca nào — bộ test mù với đúng lỗi
# đã có thật trước 01/08/2026 (file chỉ làm bộ lọc được ĐÚNG MỘT phiên rồi biến mất).
with GiaMang() as _g, contextlib.redirect_stdout(io.StringIO()), \
        contextlib.redirect_stderr(io.StringIO()):
    TJ.doc_hang_cho(now=NOW)
kiem("[39] query hàng chờ KHÔNG lọc `da_xu_ly` (file đã trích còn làm bộ lọc 3 ngày)",
     _g.get and all("da_xu_ly=eq.false" not in u for u in _g.get)
     and any("da_gop=eq.false" in u for u in _g.get))


BAN_HONG = [
    ("`tin` rỗng vẫn cho qua -> bảng đối chiếu trống, bộ lọc mất răng",
     '    if not isinstance(tin, list) or not tin:\n'
     '        raise ValueError(f"{ctx}: `tin` phải là mảng KHÔNG rỗng',
     '    if not isinstance(tin, list):\n'
     '        raise ValueError(f"{ctx}: `tin` phải là mảng KHÔNG rỗng'),
    ("bỏ kiểm id thuộc hàng chờ -> ghi vào dòng đã đóng sổ",
     '    if mid not in cho_phep_ids:\n'
     '        raise ValueError(f"{ctx}: không nằm trong khung ngày (đã đóng sổ, hoặc id '
     'bịa)")',
     "    pass"),
    ("bỏ kiểm id trùng trong file",
     '    if mid in da_thay:\n'
     '        raise ValueError(f"{ctx}: xuất hiện hai lần trong file")',
     "    pass"),
    ("bỏ kiểm độ dài tiêu đề trích",
     '        if not TIEU_DE_MIN <= len(td) <= TIEU_DE_MAX:\n'
     '            raise ValueError(f"{c2}: `tieu_de` phải dài {TIEU_DE_MIN}-{TIEU_DE_MAX} '
     'ký tự "\n'
     '                             f"(đang {len(td)})")',
     "        pass"),
    ("url sai dạng -> CHẶN cả lô thay vì bỏ url (mất bộ lọc vì một link xấu)",
     '            print(f"{c2}: `url` không phải http(s) -> bỏ URL, giữ tiêu đề.", '
     'file=sys.stderr)\n'
     '            url = ""',
     '            raise ValueError(f"{c2}: url xau")'),
    ("bỏ cảnh báo TRÍCH SÓT -> sót tin trong im lặng",
     '        print(f"⚠️ {ctx}: file gốc có {so_url} link mà chỉ trích {len(sach)} tin — '
     'nghi TRÍCH "\n'
     '              "SÓT. Tin bỏ sót ở đây là tin sẽ lọt vào bản tin dù Jay Lâm đã có.",\n'
     '              file=sys.stderr)',
     "        pass"),
    ("ghi mù khi hàng chờ rỗng",
     '    if not cho_phep:\n'
     '        print("Hàng chờ rỗng (hoặc không đọc được) — không ghi gì.", file=sys.stderr)\n'
     '        return 1',
     "    pass"),
    ("PATCH hỏng vẫn báo xong (fail-open, bảng đối chiếu không hề được lưu)",
     '    if hong:\n'
     '        print(f"CHẶN: ghi hỏng {len(hong)}/{len(sach)} dòng (id: {hong}).", '
     'file=sys.stderr)\n'
     '        return 1',
     "    pass"),
    ("bỏ kiểm `trung_voi` -> loại tin mà không soi ngược được",
     '    if len(trung_voi) < TRUNG_VOI_MIN:',
     "    if False:"),
    ("bỏ kiểm dạng url tin của mình -> sổ chứa rác, không lọc trúng gì",
     '    if not url.startswith(("http://", "https://")):\n'
     '        raise ValueError(f"`url` phải là link tin CỦA MÌNH (http/https): '
     '{url[:80]!r}")',
     "    pass"),
    ("`id_jay` ngoài khung -> CHẶN (giữ lại tin đã biết là trùng)",
     '        print(f"⚠️ {url[:60]}: `id_jay`={id_jay} không còn trong khung ngày — vẫn '
     'ghi.",\n'
     '              file=sys.stderr)',
     '        raise ValueError("id_jay ngoai khung")'),
    ("bỏ dedupe theo url -> sổ phình mãi, lời khai cũ đè lời khai mới",
     '    for m in sach:\n'
     '        theo_url[m["url"]] = dict(m, ngay=ngay)',
     '    for m in sach:\n'
     '        theo_url.setdefault(m["url"], dict(m, ngay=ngay))'),
    ("bỏ phép cắt GIU_NGAY -> sổ không bao giờ dọn",
     '    giu = [r for r in theo_url.values() if (r.get("ngay") or "") >= han]',
     "    giu = list(theo_url.values())"),
    ("cắt sổ theo hạn 0 ngày -> xoá luôn dòng còn hiệu lực",
     '    han = (now.date() - datetime.timedelta(days=GIU_NGAY)).isoformat()',
     "    han = now.date().isoformat()"),
    # Dựng lại đúng hành vi trước 01/08/2026: hàng chờ lọc `da_xu_ly=eq.false`, tức file đã
    # trích biến mất khỏi bộ lọc ngay sau phiên đầu — đúng cái làm bản tin sau lặp tin.
    ("hàng chờ lọc lại `da_xu_ly=eq.false` -> file chỉ làm bộ lọc được ĐÚNG MỘT phiên",
     '         "&da_gop=eq.false&order=created_at.asc"] + h,',
     '         "&da_gop=eq.false&da_xu_ly=eq.false&order=created_at.asc"] + h,'),
    ("`--liet-ke` không đóng sổ dòng quá khung -> nằm lại vĩnh viễn",
     '        if not dong_so([r.get("id") for r in ngoai if r.get("id") is not None]):',
     "        if False:"),
    ("khung lọc tụt về MAX_AGE_DAYS (1 ngày) -> mất bộ lọc cho tin CNQS 3 ngày",
     "    gioi_han = MAX_AGE_DAYS_CNQS if gioi_han is None else gioi_han",
     "    gioi_han = MAX_AGE_DAYS if gioi_han is None else gioi_han"),
    ("bảng lưu hỏng -> coi như đã trích, không in lại toàn văn (mất bộ lọc trong im lặng)",
     '        print(f"id={row.get(\'id\')}: bảng đối chiếu lưu hỏng (không phải JSON) — sẽ '
     'in lại "\n'
     '              "toàn văn để trích lại.", file=sys.stderr)\n'
     '        return []',
     '        return [{"tieu_de": "x", "url": ""}]'),
    # ⚠️ ĐỔI THỨ TỰ hai dòng KHÔNG phải lỗi — `co in argv` là so BẰNG trên list, `"--ghi"`
    # không khớp `"--ghi-loai"`. Bản hỏng đúng là đổi sang so TIỀN TỐ, lỗi hay gặp thật.
    ("phép so cờ đổi thành khớp TIỀN TỐ -> `--ghi-loai` bị `--ghi` nuốt",
     '    for co, ham in (("--ghi-loai", ghi_loai), ("--ghi", ghi_bang)):\n'
     "        if co in argv:\n"
     "            i = argv.index(co)",
     '    for co, ham in (("--ghi", ghi_bang), ("--ghi-loai", ghi_loai)):\n'
     "        vt = [k for k, a in enumerate(argv) if str(a).startswith(co)]\n"
     "        if vt:\n"
     "            i = vt[0]"),
]

KHAI_DO = {
    "`tin` rỗng vẫn cho qua -> bảng đối chiếu trống, bộ lọc mất răng": ["05"],
    "bỏ kiểm id thuộc hàng chờ -> ghi vào dòng đã đóng sổ": ["03"],
    "bỏ kiểm id trùng trong file": ["04"],
    "bỏ kiểm độ dài tiêu đề trích": ["07", "08"],
    "url sai dạng -> CHẶN cả lô thay vì bỏ url (mất bộ lọc vì một link xấu)": ["09"],
    "bỏ cảnh báo TRÍCH SÓT -> sót tin trong im lặng": ["16"],
    "ghi mù khi hàng chờ rỗng": ["13"],
    "PATCH hỏng vẫn báo xong (fail-open, bảng đối chiếu không hề được lưu)": ["14"],
    "bỏ kiểm `trung_voi` -> loại tin mà không soi ngược được": ["21", "22"],
    "bỏ kiểm dạng url tin của mình -> sổ chứa rác, không lọc trúng gì": ["19", "20"],
    "`id_jay` ngoài khung -> CHẶN (giữ lại tin đã biết là trùng)": ["25"],
    "bỏ dedupe theo url -> sổ phình mãi, lời khai cũ đè lời khai mới": ["26"],
    "bỏ phép cắt GIU_NGAY -> sổ không bao giờ dọn": ["27"],
    "cắt sổ theo hạn 0 ngày -> xoá luôn dòng còn hiệu lực": ["28"],
    "hàng chờ lọc lại `da_xu_ly=eq.false` -> file chỉ làm bộ lọc được ĐÚNG MỘT phiên":
        ["39"],
    "`--liet-ke` không đóng sổ dòng quá khung -> nằm lại vĩnh viễn": ["34"],
    "khung lọc tụt về MAX_AGE_DAYS (1 ngày) -> mất bộ lọc cho tin CNQS 3 ngày": ["35"],
    "bảng lưu hỏng -> coi như đã trích, không in lại toàn văn (mất bộ lọc trong im lặng)":
        ["37"],
    "phép so cờ đổi thành khớp TIỀN TỐ -> `--ghi-loai` bị `--ghi` nuốt": ["38"],
}


def _so_ca(ten):
    return ten[1:3] if ten.startswith("[") else ""


def tu_kiem():
    """Dựng từng bản `tin_jaylam.py` đã GỠ một lớp bảo vệ rồi chạy lại chính bộ ca này.

    Bản hỏng nằm trong thư mục copy riêng mang PID + sha1 NỘI DUNG (mục 17 + 23 CLAUDE.md).
    """
    goc = (SC / "tin_jaylam.py").read_text(encoding="utf-8")
    tong, trot = 0, []
    for ten, tim, thay in BAN_HONG:
        tong += 1
        if goc.count(tim) != 1:
            trot.append(f"{ten}: chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            continue
        hong = goc.replace(tim, thay)
        sha = hashlib.sha1(hong.encode("utf-8")).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"tj-hong-{os.getpid()}-{sha}-"))
        try:
            for f in SC.glob("*.py"):
                shutil.copy2(f, d / f.name)
            (d / "tin_jaylam.py").write_text(hong, encoding="utf-8")
            env = dict(os.environ, TINJAYLAM_DIR=str(d))
            p = SP.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                       capture_output=True, text=True, env=env, timeout=300)
            do = {_so_ca(l[2:]) for l in p.stdout.splitlines() if l.startswith("✗ ")}
            can = set(KHAI_DO.get(ten, []))
            if p.returncode == 0:
                trot.append(f"{ten}: bộ test VẪN XANH -> không bắt được lỗi")
            elif len(do) >= len([l for l in p.stdout.splitlines()
                                 if l[:1] in ("✓", "✗")]):
                trot.append(f"{ten}: ĐỎ TOÀN BỘ ca -> phép thay phá cú pháp, không gỡ lớp vá")
            elif not can & do:
                trot.append(f"{ten}: ca cần đỏ {sorted(can)} vẫn xanh; đỏ thực tế "
                            f"{sorted(do)}")
            else:
                print(f"  ✓ {ten}: bắt được (ca đỏ {sorted(do)})")
        finally:
            shutil.rmtree(d, ignore_errors=True)
    print()
    if trot:
        print(f"TRƯỢT {len(trot)}/{tong} bản hỏng:")
        for t in trot:
            print("  - " + t)
        return 1
    print(f"✅ {tong}/{tong} bản hỏng đều bị bộ test bắt.")
    return 0


so_dat = sum(1 for _, ok in CA if ok)
print(f"\n{so_dat}/{len(CA)} ca đạt")
if "--tu-kiem" in sys.argv:
    if so_dat != len(CA):
        print("Bản THẬT đã đỏ — sửa xong hãy chạy --tu-kiem.")
        sys.exit(1)
    print("\n=== TỰ KIỂM: dựng bản tin_jaylam.py đã gỡ lớp bảo vệ ===")
    sys.exit(tu_kiem())
sys.exit(0 if so_dat == len(CA) else 1)
