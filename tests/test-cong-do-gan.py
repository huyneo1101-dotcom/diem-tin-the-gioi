#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG ĐỘ GẦN NGUỒN — tin từ kênh tuyên truyền không được đứng một mình (06/08/2026).

Chạy:
    python3 tests/test-cong-do-gan.py
    python3 tests/test-cong-do-gan.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

⚠ VÌ SAO PHẢI CÓ CA "PHẢI CHẶN". Cổng loại này hỏng thì im lặng tuyệt đối: lô không có tin
độ gần 4 thì cổng im là ĐÚNG, mà cổng chết cũng im y hệt. Chạy trăm lần thấy nó không kêu
không chứng minh được gì. Nên mọi ca gắn nhãn PHẢI CHẶN là ca dựng đúng điều kiện xấu rồi
khẳng định cổng THẬT SỰ chặn.

⚠ VÀ PHẢI CÓ CA CHỐNG CHẶN OAN. Cổng này đứng trước một luật đã có sẵn trong `CLAUDE.md`
mục THANG XÁC MINH: kênh tuyên truyền *được* dùng cho phát ngôn của chính họ. Đo trên 03 tin
độ gần 4 đang sống ngày 06/08: 02 tin là Trung Quốc công bố việc của chính Trung Quốc, tức
hợp lệ theo luật gốc. Một cổng chặn cả hai tin đó là cổng chặn oan, và cổng nào ở luồng bình
thường luôn phải mở cờ mới qua được thì nó dạy người dùng phản xạ mở cờ — mở cờ quen tay
thì mọi cổng còn lại mất giá theo.

⚠ HAI TẦNG ĐO, cố ý giữ cả hai:
  - Ca 1-12 gọi thẳng `do_gan.kiem_lo()` — đo LUẬT.
  - Ca 13-15 chạy `add_news.py` thật trên một BẢN SAO repo — đo DÂY NỐI. Luật đúng mà không
    ai gọi thì cũng bằng không, và một bản hỏng chỉ gỡ lời gọi sẽ lọt hết ca 1-12.
Bản sao repo dựng trong thư mục tạm mang PID + sha1 nội dung phép thay: nhiều phiên Claude
chạy song song trên cùng repo (mục 9b), ghi đè file thật là xoá việc của phiên khác; và hai
bản hỏng khác nhau không bao giờ dùng chung một đường dẫn, kẻo `.pyc` của bản trước bị đọc
lại và bản sau lặng lẽ chạy bằng mã cũ.
"""
import contextlib
import datetime
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

# Seam để tự kiểm: trỏ sang một BẢN SAO repo khác (xem --tu-kiem).
REPO_THU = pathlib.Path(os.environ.get("DOGAN_REPO") or REPO)

HOM_NAY = datetime.date.today().isoformat()

# Tên có dấu tiếng Việt, lấy từ chính bảng — dùng cho ca NFD.
TEN_CO_DAU = "Bộ Ngoại giao Mỹ"


def _nap(ten: str, path: pathlib.Path):
    """Nạp module từ đường dẫn cụ thể. Tên module DUY NHẤT theo đường dẫn: nạp hai bản
    `do_gan` khác nhau dưới cùng một tên thì bản sau đè bản trước trong sys.modules."""
    dau = hashlib.sha1(str(path).encode()).hexdigest()[:8]
    ten_that = f"{ten}_{dau}"
    spec = importlib.util.spec_from_file_location(ten_that, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten_that] = mod
    spec.loader.exec_module(mod)
    return mod


def do_gan_mod():
    return _nap("do_gan", REPO_THU / "scripts" / "do_gan.py")


def _tin(**kw):
    """Một tin usNews hợp lệ với MỌI cổng khác — cố ý tái dùng khuôn đã sạch.

    Viết mới một tin cho ca PHẢI CHẶN rất dễ dính một cổng ĐỨNG TRƯỚC (ngày, URL, category,
    neo chủ đề 2) rồi ca đỏ vì lý do khác — đo nhầm cổng mà nhìn bảng vẫn thấy "đã chặn".
    """
    it = {
        "date": HOM_NAY,
        "category": "Chính trị",
        "title": "Tin thử cổng độ gần",
        "summary": "Nội dung thử, không nạp lên web.",
        "significance": "Chỉ dùng cho bộ test.",
        "sourceName": "The Epoch Times",
        "sourceUrl": "https://www.theepochtimes.com/world/bai-thu-123",
    }
    it.update(kw)
    return it


def _lo(**kw):
    lo = {"date": HOM_NAY}
    lo.update(kw)
    return lo


def _chan(lo, bo_cong=""):
    """Trả thông điệp chặn, hoặc None nếu cổng cho qua."""
    dg = do_gan_mod()
    try:
        dg.kiem_lo(lo, bo_cong)
        return None
    except ValueError as e:
        return str(e)


# ---------------------------------------------------------------------------
# Ca 1-12 — đo LUẬT
# ---------------------------------------------------------------------------

def ca_01():
    """PHẢI CHẶN: độ gần 4 trong usNews, không nguồn thứ hai, không khai phát ngôn."""
    msg = _chan(_lo(usNews=[_tin()]))
    assert msg is not None, "cổng KHÔNG chặn tin độ gần 4 đứng một mình"
    assert "ĐỘ GẦN 4" in msg, f"thông điệp không nêu độ gần 4: {msg!r}"


def ca_02():
    """PHẢI CHẶN: nguồn thứ hai CÙNG tên miền — bài thứ hai của cùng một bên, không độc lập."""
    msg = _chan(_lo(usNews=[_tin(
        nguonThuHai="https://www.theepochtimes.com/china/bai-khac-456")]))
    assert msg is not None, "cổng nhận nguồn thứ hai cùng tên miền là độc lập"
    assert "cùng tên miền" in msg, f"thông điệp không nêu đúng lý do: {msg!r}"


def ca_03():
    """PHẢI CHẶN: nguồn thứ hai không phải URL."""
    msg = _chan(_lo(usNews=[_tin(nguonThuHai="Reuters có đưa tin")]))
    assert msg is not None, "cổng nhận một câu chữ làm nguồn thứ hai"


def ca_04():
    """PHẢI CHẶN: độ gần 4 nằm trong worldNews (không chỉ usNews)."""
    tin = _tin(sourceName="Global Times",
               sourceUrl="https://www.globaltimes.cn/page/202608/bai-789.shtml",
               title="Tin thử Biển Đông", region="Biển Đông",
               summary="Tin thử về Biển Đông và Philippines, dùng cho bộ test.")
    msg = _chan(_lo(worldNews=[tin]))
    assert msg is not None, "cổng bỏ qua worldNews"


def ca_05():
    """PHẢI CHẶN: độ gần 4 nằm trong items của một sự kiện."""
    ev = {"items": [_tin()]}
    msg = _chan(_lo(dipEventUpdates=[ev]))
    assert msg is not None, "cổng bỏ qua items của sự kiện"


def ca_06():
    """CHO QUA: có nguồn thứ hai khác tên miền."""
    msg = _chan(_lo(usNews=[_tin(
        nguonThuHai="https://www.reuters.com/world/asia-pacific/bai-999/")]))
    assert msg is None, f"chặn oan tin đã có nguồn thứ hai độc lập: {msg}"


def ca_07():
    """CHO QUA: khai là phát ngôn của chính họ — đúng luật gốc THANG XÁC MINH."""
    msg = _chan(_lo(usNews=[_tin(phatNgonCuaChinhHo=True)]))
    assert msg is None, f"chặn oan tin phát ngôn của chính họ: {msg}"


def ca_08():
    """CHO QUA: nguồn độ gần 2 đứng một mình là bình thường."""
    msg = _chan(_lo(usNews=[_tin(
        sourceName="Reuters",
        sourceUrl="https://www.reuters.com/world/bai-111/")]))
    assert msg is None, f"chặn oan nguồn độ gần 2: {msg}"


def ca_09():
    """CHO QUA: nguồn chưa có trong bảng — cổng chỉ biết cái nó biết."""
    lo = _lo(usNews=[_tin(sourceName="Một Trang Chưa Xếp Loại",
                          sourceUrl="https://vidu.example.com/bai-1")])
    msg = _chan(lo)
    assert msg is None, f"chặn oan nguồn chưa có trong bảng: {msg}"
    assert "doGan" not in lo["usNews"][0], "gắn nhãn cho nguồn chưa xếp loại"


def ca_10():
    """CHO QUA: xNews độ gần 4 chỉ CẢNH BÁO, không chặn (phạm vi cố ý hẹp)."""
    dg = do_gan_mod()
    lo = _lo(xNews=[{"handle": "@WarMonitor3", "name": "War Monitor",
                     "date": HOM_NAY, "title": "t", "summary": "s",
                     "significance": "s", "url": "https://x.com/i/status/1"}])
    ra = dg.kiem_lo(lo, "")
    assert lo["xNews"][0].get("doGan") == 4, "không gắn nhãn độ gần cho xNews"
    assert any("CẢNH BÁO" in d for d in ra), f"xNews độ gần 4 không hề cảnh báo: {ra}"


def ca_11():
    """CHO QUA + GHI VẾT: cờ `--bo-cong-do-gan` hạ cổng xuống cảnh báo.

    Cờ được quảng cáo mà không có thật còn tệ hơn không có cờ — ca này canh đúng chỗ đó.
    """
    dg = do_gan_mod()
    lo = _lo(usNews=[_tin()])
    ra = dg.kiem_lo(lo, "lý do thử của bộ test")
    assert any("MỞ CỔNG ĐỘ GẦN" in d for d in ra), f"mở cổng mà không ghi vết: {ra}"
    assert any("lý do thử của bộ test" in d for d in ra), f"không in lý do: {ra}"


def ca_12():
    """PHẢI CHẶN: tên nguồn dạng NFD vẫn phải tra ra (bug NFD tên tiếng Việt trên macOS).

    Đối chứng cho chính phép chuẩn hoá: dạng NFC phải cho cùng kết quả. Hai dạng nhìn y hệt
    nhau, khác byte — thiếu chuẩn hoá thì tra trượt câm và cổng im lặng cho qua.
    """
    import unicodedata
    dg = do_gan_mod()
    nfc = unicodedata.normalize("NFC", TEN_CO_DAU)
    nfd = unicodedata.normalize("NFD", TEN_CO_DAU)
    assert nfc != nfd, "ca dựng sai: hai dạng chuẩn hoá trùng nhau, không đo được gì"
    h_nfc, h_nfd = dg.tra(nfc), dg.tra(nfd)
    assert h_nfc is not None, f"không tra được {nfc!r} ở dạng NFC"
    assert h_nfd is not None, f"không tra được {nfd!r} ở dạng NFD (thiếu chuẩn hoá NFC)"
    assert h_nfc["do_gan"] == h_nfd["do_gan"], "hai dạng chuẩn hoá ra hai độ gần khác nhau"


# ---------------------------------------------------------------------------
# Ca 13-15 — đo DÂY NỐI: chạy `add_news.py` THẬT trên bản sao repo
# ---------------------------------------------------------------------------

def _ban_sao_repo() -> pathlib.Path:
    """Bản sao repo tối giản đủ để `add_news.py` chạy: scripts/ + data/ + index.html."""
    d = pathlib.Path(tempfile.mkdtemp(prefix=f"dogan-e2e-{os.getpid()}-"))
    (d / "scripts").mkdir()
    for f in (REPO_THU / "scripts").glob("*.py"):
        shutil.copy2(f, d / "scripts" / f.name)
    shutil.copytree(REPO_THU / "data", d / "data")
    shutil.copy2(REPO / "index.html", d / "index.html")
    for ten in ("baomoi-saved.json", "baomoi-topics.json"):
        if (REPO / ten).exists():
            shutil.copy2(REPO / ten, d / ten)
    return d


def _kho_ngay_gia(d: pathlib.Path, lo: dict) -> pathlib.Path:
    """Kho HTML giả cho CỔNG NGÀY ĐĂNG THẬT — mọi URL của lô đều khai đăng HÔM NAY.

    Vì sao phải có: cổng ngày (`scripts/ngay_that.py`, dựng 25/08/2026) mở từng `sourceUrl` để
    đọc metadata ngày, mà URL của bộ này là URL BỊA. Không cắm kho giả thì ca 13-15 đỏ vì cổng
    NGÀY chặn trước, tức đo nhầm cổng — cổng độ gần có bị gỡ cũng vẫn thấy đỏ. Đây đúng seam
    `NGAYTHAT_KHO_GIA` mà cổng ngày mở sẵn cho bộ test, không phải đường vòng.
    """
    kho = {}
    for muc in ("usNews", "worldNews", "xNews", "baomoiNews"):
        for tin in lo.get(muc) or []:
            u = tin.get("sourceUrl") or tin.get("url")
            if u:
                kho[u] = ('<html><head><title>bài thử của bộ test cổng độ gần</title>'
                          f'<meta property="article:published_time" content="{HOM_NAY}">'
                          "</head><body>thân bài</body></html>")
    p = d / "kho-ngay-gia.json"
    p.write_text(json.dumps(kho, ensure_ascii=False), encoding="utf-8")
    return p


def _chay_add_news(lo: dict, them_co=()) -> tuple:
    d = _ban_sao_repo()
    try:
        f = d / "lo.json"
        f.write_text(json.dumps(lo, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(d / "scripts" / "add_news.py"), str(f), *them_co],
            capture_output=True, text=True,
            env={**os.environ, "NGAYTHAT_KHO_GIA": str(_kho_ngay_gia(d, lo))})
        return r.returncode, (r.stdout + r.stderr)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def ca_13():
    """PHẢI CHẶN (đầu-cuối): `add_news.py` từ chối lô có tin độ gần 4 đứng một mình.

    Đây là ca duy nhất chứng minh cổng ĐƯỢC GỌI. Bản hỏng chỉ gỡ lời gọi khỏi `add_news.py`
    sẽ lọt sạch ca 1-12 vì luật trong `do_gan.py` vẫn nguyên vẹn.
    """
    rc, out = _chay_add_news(_lo(usNews=[_tin()]))
    assert rc != 0, f"add_news.py NẠP tin độ gần 4 đứng một mình (rc={rc})\n{out[-1500:]}"
    assert "ĐỘ GẦN 4" in out, f"chặn nhưng không phải vì cổng độ gần:\n{out[-1500:]}"


def ca_14():
    """CHO QUA (đầu-cuối): cùng tin đó, khai phát ngôn của chính họ thì nạp được.

    Đối chứng bắt buộc: không có nó thì ca 13 đỏ vì bất kỳ lý do gì cũng trông như "đã chặn".
    """
    rc, out = _chay_add_news(_lo(usNews=[_tin(phatNgonCuaChinhHo=True)]))
    assert rc == 0, f"chặn oan tin đã khai phát ngôn của chính họ (rc={rc})\n{out[-1500:]}"


def ca_15():
    """CHO QUA (đầu-cuối): cờ `--bo-cong-do-gan` thật sự mở được cổng VÀ để lại dấu."""
    rc, out = _chay_add_news(_lo(usNews=[_tin()]),
                             them_co=['--bo-cong-do-gan=thử cờ mở của bộ test'])
    assert rc == 0, f"cờ mở cổng không có tác dụng (rc={rc})\n{out[-1500:]}"
    assert "MỞ CỔNG ĐỘ GẦN" in out, f"mở cổng mà không ghi vết:\n{out[-1500:]}"


def ca_16():
    """PHẢI CHẶN (đầu-cuối): cờ mở cổng KHÔNG kèm lý do thì từ chối, không mở im lặng.

    Cờ mở mà không bắt khai lý do thì dấu vết để lại là một dòng rỗng — bằng không có dấu.
    Canh cả hai dạng gõ: cờ trần và cờ có `=` nhưng lý do rỗng.
    """
    for co in ("--bo-cong-do-gan", "--bo-cong-do-gan="):
        rc, out = _chay_add_news(_lo(usNews=[_tin()]), them_co=[co])
        assert rc != 0, f"{co!r} mở được cổng mà không cần lý do (rc={rc})"
        assert "phải kèm LÝ DO" in out, f"{co!r} bị từ chối nhưng không nói vì sao:\n{out[-600:]}"


CAC_CA = [
    (1, "PHẢI CHẶN — độ gần 4 đứng một mình (usNews)", ca_01),
    (2, "PHẢI CHẶN — nguồn thứ hai cùng tên miền", ca_02),
    (3, "PHẢI CHẶN — nguồn thứ hai không phải URL", ca_03),
    (4, "PHẢI CHẶN — độ gần 4 trong worldNews", ca_04),
    (5, "PHẢI CHẶN — độ gần 4 trong items sự kiện", ca_05),
    (6, "cho qua — có nguồn thứ hai khác tên miền", ca_06),
    (7, "cho qua — khai phát ngôn của chính họ", ca_07),
    (8, "cho qua — nguồn độ gần 2 đứng một mình", ca_08),
    (9, "cho qua — nguồn chưa có trong bảng", ca_09),
    (10, "cho qua — xNews chỉ cảnh báo, không chặn", ca_10),
    (11, "cho qua — cờ mở cổng có thật và ghi vết", ca_11),
    (12, "PHẢI CHẶN — tên nguồn dạng NFD vẫn tra ra", ca_12),
    (13, "PHẢI CHẶN (đầu-cuối) — add_news.py từ chối lô", ca_13),
    (14, "cho qua (đầu-cuối) — khai phát ngôn thì nạp được", ca_14),
    (15, "cho qua (đầu-cuối) — cờ mở cổng chạy thật", ca_15),
    (16, "PHẢI CHẶN (đầu-cuối) — cờ mở cổng thiếu lý do", ca_16),
]


def chay() -> list:
    do = []
    for so, nhan, fn in CAC_CA:
        try:
            fn()
            print(f"  ✓ [{so:02d}] {nhan}")
        except Exception as e:
            print(f"  ✗ [{so:02d}] {nhan}\n        │ {e}")
            do.append(so)
    return do


# ---------------------------------------------------------------------------
# --tu-kiem
# ---------------------------------------------------------------------------

TEN_FILE = {
    "do_gan": ("scripts", "do_gan.py"),
    "add_news": ("scripts", "add_news.py"),
}

BAN_HONG = [
    ("add_news: cờ mở cổng nhận lý do RỖNG (dấu vết để lại bằng không có dấu)",
     "add_news",
     ("    if co_co and not bo_cong_do_gan:",
      "    if False:"),
     [16]),

    ("add_news: gỡ lời gọi cổng (luật còn sống, không ai gọi)",
     "add_news",
     ("    for dong in do_gan.kiem_lo(new_items, bo_cong_do_gan):\n        print(\"  \" + dong)",
      "    pass"),
     [13, 15]),

    ("do_gan: kiem_mot_item không bao giờ chặn (cổng câm)",
     "do_gan",
     ("    canh_bao = []\n    h = tra(item.get(\"sourceName\") or item.get(\"handle\") or \"\", bang)",
      "    canh_bao = []\n    return canh_bao\n    h = tra(item.get(\"sourceName\") or item.get(\"handle\") or \"\", bang)"),
     [1, 2, 3, 4, 5, 10, 13]),

    ("do_gan: bỏ phép so tên miền (nguồn thứ hai cùng nhà cũng nhận)",
     "do_gan",
     ("    if d1 and d1 == d2:",
      "    if False:"),
     [2]),

    ("do_gan: bỏ chuẩn hoá NFC trong khoá tra cứu",
     "do_gan",
     ("    t = unicodedata.normalize(\"NFC\", ten or \"\")\n    return \" \".join(t.split()).lower()",
      "    return \" \".join((ten or \"\").split()).lower()"),
     [12]),

    ("do_gan: lờ cờ mở cổng (cờ được quảng cáo mà không ai đọc)",
     "do_gan",
     ("            ra += kiem_mot_item(it, f\"{label}[{i}]\", bang, chan=not bo_cong)",
      "            ra += kiem_mot_item(it, f\"{label}[{i}]\", bang, chan=True)"),
     [11, 15]),

    ("do_gan: chặn luôn xNews (nới phạm vi, đổi bản chất luồng mạng xã hội)",
     "do_gan",
     ("        ra += kiem_mot_item(it, f\"xNews[{i}]\", bang, chan=False)",
      "        ra += kiem_mot_item(it, f\"xNews[{i}]\", bang, chan=True)"),
     [10]),

    ("do_gan: bỏ đường 'phát ngôn của chính họ' (chặn oan đúng ca luật gốc cho phép)",
     "do_gan",
     ("    if item.get(\"phatNgonCuaChinhHo\") is True:",
      "    if False:"),
     [7, 14]),

    # Khai ĐÚNG một ca 8, không khai thêm 6/14 dù hai ca đó cũng là "cho qua": cả hai dùng
    # nguồn ĐỘ GẦN 4 nên phép thay không đi qua nhánh chúng đo — chúng qua cổng bằng đường
    # nguồn-thứ-hai và đường phát-ngôn-của-chính-họ, hai đường vẫn nguyên vẹn ở bản hỏng này.
    # Khai thừa thì `--tu-kiem` báo trượt vì lý do sai và che mất bản hỏng thật.
    ("do_gan: chặn mọi độ gần chứ không riêng độ gần 4 (chặn oan hàng loạt)",
     "do_gan",
     ("    if h[\"do_gan\"] != DO_GAN_TUYEN_TRUYEN:\n        return canh_bao",
      "    if False:\n        return canh_bao"),
     [8]),

    ("do_gan: nguồn chưa có trong bảng cũng bị chặn (chặn oan 39% số tin)",
     "do_gan",
     ("    if h is None:\n        return canh_bao",
      "    if h is None:\n        raise ValueError(ctx + ' nguồn chưa xếp loại')"),
     [9]),
]


def _dung_ban_sao(d: pathlib.Path, file_hong: str, tim: str, thay: str) -> None:
    (d / "scripts").mkdir(parents=True, exist_ok=True)
    for f in (REPO / "scripts").glob("*.py"):
        shutil.copy2(f, d / "scripts" / f.name)
    shutil.copytree(REPO / "data", d / "data")
    thu_muc, ten_file = TEN_FILE[file_hong]
    p = d / thu_muc / ten_file
    p.write_text(p.read_text(encoding="utf-8").replace(tim, thay, 1), encoding="utf-8")


def tu_kiem() -> int:
    print("Chạy bộ ca trên BẢN ĐÚNG trước — ca đỏ ở đây thì dựng bản hỏng cũng vô nghĩa.")
    r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print("✗ TRƯỢT: bộ ca đã ĐỎ trên bản đúng. Sửa cho xanh rồi mới tự kiểm.")
        return 1
    print(f"  bản đúng: {len(CAC_CA)}/{len(CAC_CA)} ca đạt\n")

    hong = 0
    for nhan, file_hong, (tim, thay), ca_phai_do in BAN_HONG:
        thu_muc, ten_file = TEN_FILE[file_hong]
        goc = (REPO / thu_muc / ten_file).read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: {goc.count(tim)} chỗ khớp "
                  f"(cần đúng 1). Mã nguồn đã đổi → sửa lại neo, đừng sửa ca.")
            hong += 1
            continue
        dau = hashlib.sha1((tim + thay).encode()).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"dogan-{os.getpid()}-{dau}-"))
        try:
            _dung_ban_sao(d, file_hong, tim, thay)
            env = dict(os.environ, DOGAN_REPO=str(d))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
            do_that = set()
            for dong in r.stdout.splitlines():
                if dong.strip().startswith("✗ ["):
                    do_that.add(int(dong.split("[")[1].split("]")[0]))
            # Bản hỏng làm ĐỎ TOÀN BỘ ca = phép thay hỏng cú pháp, không phải gỡ lớp vá.
            # Nó chỉ chứng minh Python biết báo lỗi, không chứng minh ca nào có răng.
            if len(do_that) == len(CAC_CA):
                print(f"  ✗ {nhan}\n        │ MỌI ca đều đỏ → phép thay làm hỏng cú pháp, "
                      f"sửa lại phép thay.")
                hong += 1
                continue
            thieu = set(ca_phai_do) - do_that
            thua = do_that - set(ca_phai_do)
            if thieu:
                print(f"  ✗ {nhan}\n        │ ca {sorted(thieu)} VẪN XANH trên bản hỏng "
                      f"→ ca đó không bắt được lỗi. Đỏ thực tế: {sorted(do_that)}")
                hong += 1
            elif thua:
                print(f"  ✗ {nhan}\n        │ đỏ THÊM ca {sorted(thua)} ngoài khai báo "
                      f"→ khai lại cho đúng, kẻo che mất bản hỏng thật")
                hong += 1
            else:
                print(f"  ✓ {nhan} → đỏ đúng ca {sorted(do_that)}")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    print()
    if hong:
        print(f"✗ TRƯỢT: {hong}/{len(BAN_HONG)} bản hỏng KHÔNG bị bắt.")
        return 1
    print(f"✅ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print(f"CỔNG ĐỘ GẦN NGUỒN — {len(CAC_CA)} ca (repo đo: {REPO_THU})")
    do = chay()
    print()
    if do:
        print(f"✗ {len(do)}/{len(CAC_CA)} ca HỎNG: {do}")
        return 1
    print(f"✅ {len(CAC_CA)}/{len(CAC_CA)} ca đạt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
