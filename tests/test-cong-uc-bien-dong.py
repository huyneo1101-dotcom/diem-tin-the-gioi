#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST HỒI QUY CHO CỔNG CHỦ ĐỀ 2 "ÚC & BIỂN ĐÔNG" — hai tầng, vá 01/08/2026.

⚠ VÌ SAO CÓ FILE NÀY (Huy bắt 01/08/2026: *"hàn quốc liên quan đ gì đến biển đông và Úc mà
cứ cho vào???"*). Bản tối 01/08 mục "Úc và Biển Đông" có 04 tin thì 03 sai: Nhật phóng
Tomahawk từ JS Chokai · Trung Quốc phóng YJ-20 · Hàn ký 7,8 nghìn tỷ won với Hanwha Ocean.

HAI TẦNG cùng hỏng, và tầng dưới làm tầng trên VÔ HÌNH:
  - Tầng QUÉT (`scripts/add_news.py`): chủ đề 2 khai *"hoạt động của Nhật/Ấn/Hàn TẠI VÙNG
    BIỂN NÀY"*, nhưng không cổng nào kiểm chủ đề — chỉ kiểm ngày · URL · trùng.
  - Tầng DỰNG FILE (`.github/scripts/make_docx.py`): mục 2 = **mọi worldNews trừ Mali**,
    tức một cái thùng. Tin nào lọt tầng quét cũng được dán nhãn "Úc và Biển Đông" và trông
    như đúng chỗ — nếu mục có tên trung thực thì lỗi tầng quét đã lộ từ nhiều bản tin trước.

Cổng loại này hỏng thì IM LẶNG: không chặn gì cũng im, mà chết cũng im y hệt. => Mọi ca gắn
nhãn "PHẢI CHẶN" là ca dựng đúng điều kiện xấu rồi khẳng định cổng THẬT SỰ chặn. Test chỉ có
ca "phải cho qua" là chưa test.

Chạy:
    python3 tests/test-cong-uc-bien-dong.py
    python3 tests/test-cong-uc-bien-dong.py --tu-kiem   # chứng minh test BẮT ĐƯỢC lỗi

`--tu-kiem` dựng bản repo ĐÃ GỠ ĐÚNG DÒNG BẢO VỆ rồi chạy lại chính bộ ca này — mỗi bản
hỏng phải làm ĐỎ đúng những ca đã khai. Xanh trên cả bản đúng lẫn bản hỏng là test vô dụng.

⚠ Bản hỏng KHÔNG ghi đè file thật: mỗi lượt dựng một BẢN SAO repo tối giản trong thư mục
tạm (`scripts/` + `.github/scripts/`), giữ nguyên cấu trúc thư mục để `make_docx.py` vẫn tự
tìm được `../../scripts/topics.py` — của BẢN SAO, không phải bản thật. Vì có nhiều phiên
Claude chạy song song trên cùng repo (CLAUDE.md toàn cục, mục 9b), ghi đè file thật là xoá
việc của phiên khác.
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
SCRIPTS = REPO / "scripts"
MAKE_DOCX = REPO / ".github" / "scripts" / "make_docx.py"

# Seam để tự kiểm: trỏ sang một BẢN SAO repo khác (xem --tu-kiem).
REPO_THU = pathlib.Path(os.environ.get("UCBD_REPO") or REPO)

HOM_NAY = datetime.date.today().isoformat()


def _nap(ten: str, path: pathlib.Path):
    """Nạp một module từ đường dẫn cụ thể.

    Tên module phải DUY NHẤT theo đường dẫn: nạp hai bản `topics` khác nhau dưới cùng một
    tên thì bản sau ăn cache `sys.modules` của bản trước, và bản hỏng lặng lẽ chạy bằng mã
    của bản đúng.
    """
    khoa = ten + "_" + hashlib.sha1(str(path).encode()).hexdigest()[:8]
    spec = importlib.util.spec_from_file_location(khoa, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[khoa] = mod
    spec.loader.exec_module(mod)
    return mod


# `add_news` và `make_docx` đều tự chèn thư mục `scripts/` của CHÍNH BẢN ĐANG CHẠY vào
# sys.path để `import topics`. Với bản sao thì đó là scripts/ của bản sao — đúng ý.
sys.path.insert(0, str(REPO_THU / "scripts"))
AN = _nap("add_news", REPO_THU / "scripts" / "add_news.py")
MD = _nap("make_docx", REPO_THU / ".github" / "scripts" / "make_docx.py")


def tin(title, **kw):
    """Một tin đủ field bắt buộc; chỉ `title` là thứ ca test quan tâm."""
    d = {
        "date": HOM_NAY,
        # Phải là category THẬT (`VALID_CATEGORIES`), kẻo mọi ca đỏ/xanh vì cổng category
        # chứ không vì cổng đang đo — đo nhầm nhánh mà bảng kết quả vẫn trông bình thường.
        "category": "Công nghệ quân sự",
        "title": title,
        "summary": kw.pop("summary", "Nội dung tóm tắt."),
        "significance": kw.pop("significance", "Ý nghĩa."),
        "sourceName": "Reuters",
        "sourceUrl": kw.pop("sourceUrl", "https://reuters.com/a/" +
                            hashlib.sha1(title.encode()).hexdigest()[:12]),
    }
    d.update(kw)
    return d


# ── 03 tin THẬT đã lọt vào bản tối 01/08 (Huy chê) ────────────────────────────
TIN_NHAT = tin("Nhật Bản lần đầu phóng thử tên lửa hành trình Tomahawk từ tàu khu trục JS Chokai")
TIN_TQ = tin("Trung Quốc phóng thử tên lửa siêu vượt âm chống hạm YJ-20 từ khu trục hạm")
TIN_HAN = tin("Hàn Quốc ký hợp đồng cuối cùng 7,8 nghìn tỷ won cho dự án tàu khu trục với Hanwha Ocean")
# ── tin ĐÚNG mục 2 trong cùng bản tin đó ──────────────────────────────────────
TIN_AUKUS = tin("Công ty thép Bisalloy của Úc nhận đơn hàng đầu tiên trong chuỗi cung ứng AUKUS")
# ── đối chứng chống chặn oan: NHẬT/HÀN CÓ gắn Biển Đông hoặc gắn Úc ───────────
TIN_NHAT_CO_NEO = tin("Japan and the Philippines conduct a joint patrol in the South China Sea")
TIN_HAN_CO_NEO = tin("Hàn Quốc cử tàu khu trục tham gia tập trận chung với Úc")
# ── chủ đề 4 (Mỹ–Mali) đôi khi nằm ở worldNews — có mục riêng, không được chặn ─
TIN_MALI = tin("Mỹ cân nhắc không kích JNIM tại Mali sau loạt tấn công ở Bamako")
# ── bẫy substring: "thúc đẩy" chứa chuỗi "uc" sau khi bỏ dấu ──────────────────
TIN_BAY_THUC = tin("Nhật Bản thúc đẩy chương trình tên lửa nội địa thế hệ mới",
                   summary="Chính phủ thúc đẩy ngân sách quốc phòng.")
# ── MỞ RỘNG 02/08/2026 (chỉ thị Huy): chủ đề 2 gồm cả tin quân sự của Úc NÓI CHUNG và
#    chiến tranh VÙNG XÁM ở Biển Đông. Vùng xám cố ý KHÔNG vào bảng neo (không tự neo được
#    vào vùng biển này) — nó vào mục 2 nhờ neo sẵn có, và ca 19 canh đúng chỗ đó.
TIN_VUNG_XAM = tin("Tàu hải cảnh Trung Quốc dùng vòi rồng với tàu tiếp tế Philippines ở Bãi Cỏ Mây",
                   summary="Hoạt động vùng xám leo thang trên Biển Đông trong tuần qua.")
# ⚠ Tin mẫu này CỐ Ý chỉ mang ĐÚNG MỘT neo là chuỗi viết tắt "RAAF": bản đầu còn chữ "Úc"
#   trong tiêu đề nên neo "uc" gánh, gỡ dòng neo Không quân đi ca vẫn xanh — đúng bẫy hai
#   lớp chồng nhau. Không thêm "Úc", "Australia", "Tindal", "Pitch Black" vào đây.
TIN_UC_QUAN_SU = tin("RAAF tiếp nhận thêm máy bay tiếp dầu KC-30A cho phi đội vận tải",
                     summary="Hợp đồng mở rộng phi đội tiếp dầu vừa được công bố.")
# ── đối chứng: vùng xám ở BIỂN KHÁC — phải CHẶN, kẻo mục 2 lại thành cái thùng ──
TIN_VUNG_XAM_BALTIC = tin("NATO cảnh báo hoạt động vùng xám của Nga nhắm cáp ngầm ở biển Baltic",
                          summary="Gray zone, cắt cáp, vòi rồng — nhưng ở Baltic.")
# ── tin usNews / baomoiNews: cổng CHỈ áp cho worldNews ────────────────────────
TIN_US = tin("Hạ viện Mỹ thông qua dự luật ngân sách quốc phòng NDAA", category="Chính trị")
TIN_BAOMOI = tin("Fed giữ nguyên lãi suất trong cuộc họp tháng 8", category="Kinh tế",
                 sourceName="Báo Mới", sourceUrl="https://baomoi.com/fed-giu-lai-suat-9.epi")


def nap_world(*items, label="worldNews"):
    """Chạy guardrail tầng quét. Trả (bị_chặn, thông_điệp)."""
    ref = datetime.date.fromisoformat(HOM_NAY)
    try:
        AN.validate_news_items(list(items), label, ref)
    except ValueError as e:
        return True, str(e)
    return False, ""


def dung_muc(us=(), world=(), events=()):
    """Chạy tầng dựng file. Trả (dict tên_mục -> [tiêu đề], chữ cảnh báo ở stderr)."""
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        secs = MD.build_sections(list(us), list(world), list(events))
    return {ten: [it.get("title") for it in items] for ten, items in secs}, err.getvalue()


# ═════════════════════════════ các ca thử ═════════════════════════════
CA = []


def ca(ten):
    def deco(f):
        CA.append((ten, f))
        return f
    return deco


@ca('1. Tin Nhật (Tomahawk/JS Chokai) vào worldNews → PHẢI CHẶN')
def _():
    chan, msg = nap_world(TIN_NHAT)
    return chan and "neo" in msg, msg


@ca('2. Tin Trung Quốc (YJ-20) vào worldNews → PHẢI CHẶN')
def _():
    chan, msg = nap_world(TIN_TQ)
    return chan, msg


@ca('3. Tin Hàn Quốc (Hanwha Ocean) vào worldNews → PHẢI CHẶN')
def _():
    chan, msg = nap_world(TIN_HAN)
    return chan, msg


@ca('4. Tin Úc/AUKUS (Bisalloy) → phải CHO QUA (chống chặn oan)')
def _():
    chan, msg = nap_world(TIN_AUKUS)
    return not chan, msg


@ca('5. Tin Nhật CÓ gắn Biển Đông + Philippines → phải CHO QUA (chống chặn oan)')
def _():
    # Đây là đúng nguyên văn khai của chủ đề 2: "hoạt động của Nhật/Ấn/Hàn TẠI VÙNG BIỂN NÀY".
    # Chặn ca này là siết quá tay, giết luôn phần chủ đề vốn hợp lệ.
    chan, msg = nap_world(TIN_NHAT_CO_NEO)
    return not chan, msg


@ca('6. Tin Hàn Quốc CÓ gắn Úc → phải CHO QUA (chống chặn oan)')
def _():
    chan, msg = nap_world(TIN_HAN_CO_NEO)
    return not chan, msg


@ca('7. Tin Mỹ–Mali nằm ở worldNews → phải CHO QUA (chủ đề 4 có mục riêng)')
def _():
    chan, msg = nap_world(TIN_MALI)
    return not chan, msg


@ca('8. Bẫy substring: "thúc đẩy" chứa "uc" → PHẢI CHẶN (khớp theo ranh giới từ)')
def _():
    # Khớp thô `k in text` thì "uc" tìm thấy trong "thuc" và tin Nhật thuần tuý này lọt vào
    # mục Úc — đúng con bug đã sửa một lần ở cổng Báo Mới, nay tái diễn ở chỗ khác.
    chan, msg = nap_world(TIN_BAY_THUC)
    return chan, msg


@ca('9. Tin usNews KHÔNG neo Úc/Biển Đông → phải CHO QUA (cổng chỉ áp worldNews)')
def _():
    chan, msg = nap_world(TIN_US, label="usNews")
    return not chan, msg


@ca('10. Tin baomoiNews (Fed) → phải CHO QUA (luồng Báo Mới có cổng riêng)')
def _():
    chan, msg = nap_world(TIN_BAOMOI, label="baomoiNews")
    return not chan, msg


@ca('11. Dựng file: 03 tin sai KHÔNG được vào mục địa bàn (Úc/Anh/Biển Đông) → PHẢI CHẶN')
def _():
    muc, _ = dung_muc(world=[TIN_NHAT, TIN_TQ, TIN_HAN, TIN_AUKUS])
    sec2 = muc[MD.MUC_DIA_BAN]
    return sec2 == [TIN_AUKUS["title"]], f"mục 2 đang có: {sec2}"


@ca('12. Dựng file: tin rớt KHÔNG được biến mất → vẫn nằm trong file (lưới an toàn)')
def _():
    # Mất tin tệ hơn xếp nhầm mục — lưới cố ý gom về mục 1.
    muc, _ = dung_muc(world=[TIN_NHAT, TIN_TQ, TIN_HAN, TIN_AUKUS])
    co_het = all(t["title"] in sum(muc.values(), []) for t in (TIN_NHAT, TIN_TQ, TIN_HAN))
    return co_het, f"các mục: { {k: len(v) for k, v in muc.items()} }"


@ca('13. Dựng file: lưới PHẢI KÊU đúng nguyên nhân "tầng quét", không kêu chung chung')
def _():
    # Hai nguyên nhân rơi khác nhau (thiếu category vs lạc chủ đề) mà in cùng một câu thì
    # người đọc đi sửa nhầm chỗ.
    _, err = dung_muc(world=[TIN_NHAT, TIN_AUKUS])
    return "KHÔNG neo được vào Úc/Biển Đông" in err and "TẦNG QUÉT" in err, err


@ca('14. Dựng file: tin đúng mục 2 KHÔNG được làm lưới kêu (chống kêu oan)')
def _():
    _, err = dung_muc(world=[TIN_AUKUS, TIN_NHAT_CO_NEO, TIN_HAN_CO_NEO])
    return err.strip() == "", err


@ca('15. Dựng file: tin Mali ở worldNews RỜI khỏi .docx, KHÔNG lọt mục 2, KHÔNG làm lưới kêu')
def _():
    # ⚠️ ĐỔI 05/08/2026 — mục "Mỹ – Mali" đã BỎ khỏi .docx (chỉ thị Huy: tin Mali nay đi ở bản
    # sáng 🎖️). Ca này vì thế đổi phép đo: không còn hỏi "Mali vào đúng mục Mali" mà hỏi
    # "Mali KHÔNG lọt sang mục nào khác" — phần lọc phải giữ nguyên, chỉ mục là bỏ.
    # Lưới an toàn cũng KHÔNG được kêu: tin Mali bị bỏ có chủ ý, không phải tin rớt vì lạc mục.
    muc, err = dung_muc(world=[TIN_MALI, TIN_AUKUS])
    return ("Mỹ – Mali" not in muc
            and all(TIN_MALI["title"] not in ds for ds in muc.values())
            and muc[MD.MUC_DIA_BAN] == [TIN_AUKUS["title"]]
            and "KHÔNG neo được" not in err), f"{muc} || {err}"


@ca('17. Vùng xám Biển Đông (vòi rồng, hải cảnh) → phải CHO QUA (mở rộng 02/08)')
def _():
    chan, msg = nap_world(TIN_VUNG_XAM)
    return not chan, msg


@ca('18. Tin quân sự Úc nói chung, KHÔNG có chữ AUKUS → phải CHO QUA (mở rộng 02/08)')
def _():
    # Lỗ thật 02/08: bảng neo chỉ có "royal australian navy", nên tin của KHÔNG QUÂN Úc
    # viết tắt "RAAF" không khớp neo nào. Ca này chết là lỗ đó mở lại.
    chan, msg = nap_world(TIN_UC_QUAN_SU)
    return not chan, msg


@ca('19. ĐỐI CHỨNG: vùng xám ở biển Baltic → PHẢI CHẶN (chống nới tay khi mở phạm vi)')
def _():
    # Mở phạm vi sang "chiến tranh vùng xám" rất dễ bị hiểu thành "thêm gray zone/vòi rồng
    # vào bảng neo". Làm thế là mục 2 nuốt cả Baltic, Bắc Cực, eo biển Đài Loan — đúng cái
    # thùng mà cổng này sinh ra để phá.
    chan, msg = nap_world(TIN_VUNG_XAM_BALTIC)
    return chan, msg


@ca('16. make_docx PHẢI dùng chung bảng neo của topics.py (một nguồn sự thật)')
def _():
    # Cổng sống mà mỗi tầng một bảng thì hai bảng tách nhánh ở lần vá sau, âm thầm. Ca này
    # chạy make_docx như một script thật để bắt cả lỗi import chéo thư mục.
    r = subprocess.run([sys.executable, str(REPO_THU / ".github" / "scripts" / "make_docx.py")],
                       capture_output=True, text=True, cwd=str(REPO_THU))
    loi_import = "ImportError" in r.stderr or "ModuleNotFoundError" in r.stderr
    src = (REPO_THU / ".github" / "scripts" / "make_docx.py").read_text(encoding="utf-8")
    return (not loi_import) and "from topics import neo_uc_bien_dong" in src, r.stderr[-600:]


# ═══════════════════════════ tự kiểm: bản hỏng ═══════════════════════════
# (nhãn · file · phép thay trong mã nguồn · các ca BẮT BUỘC phải đỏ)
BAN_HONG = [
    ("make_docx: trả mục 2 về 'mọi worldNews trừ Mali' (dựng lại cái thùng)",
     "make_docx",
     ("    sec2 = [it for it in world                                        # 2. Úc & Biển Đông\n"
      "            if khong_phai_mali(it) and la_uc_bien_dong(it)]",
      "    sec2 = [it for it in world if khong_phai_mali(it)]"),
     [11, 13]),

    ("add_news: gỡ lời gọi cổng khỏi validate_news_items (cổng sống, không ai gọi)",
     "add_news",
     ("        if label == \"worldNews\":\n            check_neo_chu_de_2(item, ctx)",
      "        pass"),
     [1, 2, 3, 8]),

    ("topics: neo_uc_bien_dong luôn trả True (cổng câm cả hai tầng)",
     "topics",
     ("    hay = bo_dau(text)\n    return any(p.search(hay) for p in _RE_NEO)",
      "    return True"),
     [1, 2, 3, 8, 11, 13]),

    ("topics: bỏ ranh giới từ, khớp substring ('thúc' chứa 'uc')",
     "topics",
     ("_RE_NEO = [re.compile(r\"(?<!\\w)\" + re.escape(k) + r\"(?!\\w)\", re.IGNORECASE)\n"
      "           for k in NEO_UC_BIEN_DONG]",
      "_RE_NEO = [re.compile(re.escape(k), re.IGNORECASE) for k in NEO_UC_BIEN_DONG]"),
     # Khai LẤY TỪ SỐ ĐO, không từ suy luận: chuỗi "uc" còn nằm trong "khu trục" -> "khu
     # truc", nên cả 03 tin Huy chê đều lọt chứ không riêng ca bẫy "thúc đẩy".
     [1, 2, 3, 8, 11, 13]),

    ("topics: quên bỏ dấu trước khi khớp (mọi từ khoá tiếng Việt hoá câm)",
     "topics",
     ("    hay = bo_dau(text)\n    return any(p.search(hay) for p in _RE_NEO)",
      "    hay = str(text or '').lower()\n    return any(p.search(hay) for p in _RE_NEO)"),
     # Ca 14 đỏ theo vì tin "tập trận chung với Úc" mất neo -> lưới kêu oan.
     [6, 14]),

    ("add_news: gỡ ngoại lệ Mali (chặn oan chủ đề 4)",
     "add_news",
     ("    if any(k in strip_accents(hay).lower() for k in MALI_KEYS_ADD):\n        return",
      "    pass"),
     [7]),

    ("add_news: áp cổng cho MỌI mảng (chặn oan usNews và Báo Mới)",
     "add_news",
     ("        if label == \"worldNews\":\n            check_neo_chu_de_2(item, ctx)",
      "        if True:\n            check_neo_chu_de_2(item, ctx)"),
     [9, 10]),

    ("make_docx: gộp lại một dòng cảnh báo chung (mất chỉ dẫn 'lỗi TẦNG QUÉT')",
     "make_docx",
     ('        if lac_muc2:\n            print(f"⚠️  {len(lac_muc2)} tin worldNews KHÔNG neo '
      'được vào Úc/Biển Đông -> "',
      '        if False:\n            print(f"⚠️  {len(lac_muc2)} tin worldNews KHÔNG neo '
      'được vào Úc/Biển Đông -> "'),
     [13]),

    # CHIỀU NỚI — mỗi lần siết một ngưỡng phải có ca canh chiều nới lại.
    ("topics: nới bảng neo bằng từ vùng xám (mục 2 nuốt cả Baltic/Bắc Cực)",
     "topics",
     ('NEO_UC_BIEN_DONG = [',
      'NEO_UC_BIEN_DONG = ["vung xam", "gray zone", "voi rong", "water cannon", "cat cap",'),
     [19]),
    ("topics: bỏ neo Không quân Úc (dựng lại lỗ làm sót tin Pitch Black 31/07)",
     "topics",
     ('    "raaf", "royal australian air force", "pitch black", "talisman sabre",\n    "tindal", "amberley",',
      '    '),
     [18]),
    ("topics: nới bảng neo, thêm thẳng japan/korea/china (mục 2 lại thành thùng)",
     "topics",
     ('    # -- Úc\n    "uc", "australia",',
      '    "japan", "nhat ban", "korea", "han quoc", "china", "trung quoc",\n'
      '    # -- Úc\n    "uc", "australia",'),
     # Ca 8/11/13 đỏ theo vì tin bẫy cũng mang chữ "Nhật Bản".
     [1, 2, 3, 8, 11, 13]),

    ("make_docx: bỏ luôn lưới an toàn (tin rớt biến mất khỏi file, im lặng)",
     "make_docx",
     ("        sec1 = sec1 + roi", "        sec1 = sec1"),
     [12]),
]

TEN_FILE = {
    "topics": ("scripts", "topics.py"),
    "add_news": ("scripts", "add_news.py"),
    "make_docx": (".github/scripts", "make_docx.py"),
}


def _dung_ban_sao(dich: pathlib.Path, file_hong=None, tim="", thay=""):
    """Chép 03 file nguồn sang bản sao repo, giữ nguyên cấu trúc thư mục."""
    (dich / "scripts").mkdir(parents=True, exist_ok=True)
    (dich / ".github" / "scripts").mkdir(parents=True, exist_ok=True)
    for ten, (thu_muc, ten_file) in TEN_FILE.items():
        goc = (REPO / thu_muc / ten_file).read_text(encoding="utf-8")
        if ten == file_hong:
            goc = goc.replace(tim, thay)
        (dich / thu_muc / ten_file).write_text(goc, encoding="utf-8")
    # make_docx đọc index.html của repo khi chạy thật (ca 16) — chép cho đủ.
    shutil.copy2(REPO / "index.html", dich / "index.html")


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản repo đã gỡ dòng bảo vệ, các ca đã khai PHẢI ĐỎ")
    print("═" * 78)
    hong = 0
    for nhan, file_hong, (tim, thay), ca_phai_do in BAN_HONG:
        thu_muc, ten_file = TEN_FILE[file_hong]
        goc = (REPO / thu_muc / ten_file).read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print(f"  ✗ {nhan}\n        │ KHÔNG áp được phép thay: tìm thấy "
                  f"{goc.count(tim)} chỗ khớp (cần đúng 1). Mã nguồn đã đổi → sửa lại test.")
            hong += 1
            continue
        # Thư mục tạm mang PID + sha1 nội dung: hai phiên chạy chồng không xoá bản của nhau,
        # và hai bản hỏng khác nhau không bao giờ dùng chung một đường dẫn (nếu dùng chung
        # thì `.pyc` của bản trước bị đọc lại và bản sau lặng lẽ chạy bằng mã cũ).
        dau = hashlib.sha1((tim + thay).encode()).hexdigest()[:8]
        d = pathlib.Path(tempfile.mkdtemp(prefix=f"ucbd-{os.getpid()}-{dau}-"))
        try:
            _dung_ban_sao(d, file_hong, tim, thay)
            env = dict(os.environ, UCBD_REPO=str(d))
            r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve())],
                               capture_output=True, text=True, env=env)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        do = {int(dong[4:].split(".")[0])
              for dong in r.stdout.splitlines() if dong.startswith("  ✗ ")}
        # Bản hỏng làm ĐỎ HẾT = phép thay làm vỡ cú pháp, không chứng minh được ca nào có
        # răng — nó chỉ chứng minh Python biết báo lỗi.
        if len(do) == len(CA):
            print(f"  ✗ {nhan}\n        │ MỌI ca đều đỏ → phép thay nhiều khả năng làm hỏng "
                  f"cú pháp/nạp module, sửa lại phép thay.")
            hong += 1
            continue
        thieu = set(ca_phai_do) - do
        thua = do - set(ca_phai_do)
        ok = not thieu
        print(f"  {'✓' if ok else '✗'} {nhan}")
        print(f"        │ ca đỏ: {sorted(do) or 'KHÔNG CÓ CA NÀO ĐỎ'} · cần đỏ: {ca_phai_do}"
              + (f" · đỏ thêm ngoài dự kiến: {sorted(thua)}" if thua else ""))
        if not ok:
            hong += 1
            print(f"        │ ⚠ ca {sorted(thieu)} VẪN XANH trên bản hỏng → test không bắt được lỗi này.")
    print("═" * 78)
    if hong:
        print(f"✗ {hong}/{len(BAN_HONG)} phép thử tự kiểm THẤT BẠI — bộ test chưa chứng minh "
              f"được là nó bắt được lỗi.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — bộ test này có giá trị.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST CỔNG CHỦ ĐỀ 2 'ÚC & BIỂN ĐÔNG' — mọi ca 'PHẢI CHẶN' phải thật sự chặn")
    print(f"(bản đang thử: {REPO_THU})")
    print("─" * 78)
    hong = 0
    for ten, f in CA:
        try:
            ok, out = f()
        except Exception as e:                                   # noqa: BLE001
            ok, out = False, f"LỖI CHẠY: {e.__class__.__name__}: {e}"
        print(f"  {'✓' if ok else '✗'} {ten}")
        if not ok:
            hong += 1
            for dong in (str(out) or "(không có đầu ra)").strip().split("\n")[:6]:
                print(f"        │ {dong}")
    print("─" * 78)
    if hong:
        print(f"✗ {hong}/{len(CA)} ca HỎNG — mục 'Úc và Biển Đông' không còn được canh, "
              f"sửa trước khi quét tin.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — cổng chủ đề 2 còn sống.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
