#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐỒNG BỘ BẢNG ĐỘ GẦN NGUỒN từ app Rèn Phân Tích sang repo Điểm Tin.

    python3 scripts/dong_bo_do_gan.py --sinh    # dựng lại data/do-gan-nguon.json từ bản gốc
    python3 scripts/dong_bo_do_gan.py --kiem    # so bản trong repo với bản gốc, lệch thì kêu

Mã thoát của `--kiem`: 0 = khớp · 1 = LỆCH (phải chạy --sinh) · 2 = không đo được
(bản gốc vắng mặt — đúng khi chạy trên máy chạy của GitHub Actions).

VÌ SAO PHẢI CHÉP CHỨ KHÔNG TRỎ THẲNG (đo 06/08/2026): `add_news.py` chạy CẢ trên máy chạy
của GitHub Actions (`.github/workflows/import-news-from-drive.yml`, `claude-web-scan.yml`),
mà ở đó `/Users/Huy/Claude/App/RenPhanTich/` không tồn tại. Trỏ thẳng đường dẫn tuyệt đối là
cổng chết câm trên CI: không có bảng thì không tra được, không tra được thì không chặn được,
và không có lỗi nào phát ra. Nên bản trong repo là bắt buộc — và vì đã có hai bản thì phải
có phép đo canh cho chúng đừng tách nhánh (luật một-bản-gốc-duy-nhất, mục 14 CLAUDE.md
toàn cục). Phép đo đó là `--kiem`, chạy trong `/khoe` mỗi sáng.

⚠ ĐỔI TÊN THANG CÓ CHỦ Ý — bản gốc gọi là `tang`, bản trong repo gọi là `do_gan`.
Repo Điểm Tin đã có sẵn một mục "Nguồn theo 3 tầng" (`CLAUDE.md`) xếp nguồn theo CÔNG DỤNG:
ở đó tầng 3 là viện nghiên cứu, dùng để neo nhận định, tức vị trí CAO. Thang của Rèn Phân
Tích xếp theo ĐỘ GẦN SỰ VIỆC: tầng 3 là trang tổng hợp/dẫn lại, tức vị trí THẤP. CSIS mang
số 3 ở cả hai bảng với hai ý nghĩa trái ngược; Reuters là "báo chí dưới cùng" ở bảng cũ
nhưng tầng 2 ở bảng mới. Giữ nguyên chữ "tầng" là gài sẵn một chỗ đọc nhầm mà không tool
nào bắt được. Huy chốt 06/08/2026: bảng mới gọi là "độ gần", bảng cũ giữ nguyên.

THANG ĐỘ GẦN
  1 = nguồn gốc chính thức (chính bên tạo ra sự việc, hoặc người quan sát trực tiếp)
  2 = hãng tin có phóng viên tại chỗ
  3 = trang tổng hợp / dẫn lại
  4 = kênh tuyên truyền
"""
import argparse
import hashlib
import json
import pathlib
import sys
import unicodedata

REPO = pathlib.Path(__file__).resolve().parent.parent
BAN_TRONG_REPO = REPO / "data" / "do-gan-nguon.json"

# Bản gốc nằm ngoài repo, CỐ Ý: nó thuộc app Rèn Phân Tích và được sửa ở đó.
BAN_GOC = pathlib.Path("/Users/Huy/Claude/App/RenPhanTich/du-lieu/nguon.json")

DO_GAN_HOP_LE = {1, 2, 3, 4}


def chuan_ten(ten: str) -> str:
    """Khoá tra cứu: NFC + gộp khoảng trắng + thường hoá.

    NFC là bắt buộc, không phải cho chắc ăn: tên hãng có dấu tiếng Việt do Huy/Finder gõ ra
    dạng NFD, chuỗi trong mã nguồn và trong JSON do Claude ghi là NFC — trông y hệt, khác
    byte, so khớp trượt câm (cùng gốc với bug cổng dàn ý bên QuanSu).
    """
    t = unicodedata.normalize("NFC", ten or "")
    return " ".join(t.split()).lower()


def _rut_gon(goc: dict) -> list:
    """Bản gốc -> danh sách rút gọn. Chỉ giữ thứ cổng nạp thật sự dùng."""
    ra = []
    for h in goc["hang"]:
        tang = h["tang"]
        if tang not in DO_GAN_HOP_LE:
            raise ValueError(f"bản gốc có tầng lạ {tang!r} ở mục {h.get('ten')!r}")
        ra.append({
            "ten": unicodedata.normalize("NFC", h["ten"]),
            "do_gan": tang,
            "kenh": h.get("kenh", ""),
            "luu_y": h.get("luu_y", ""),
        })
    ra.sort(key=lambda x: (x["do_gan"], chuan_ten(x["ten"])))
    return ra


def _dau_van_tay(hang: list) -> str:
    """sha1 của đúng phần cổng nạp dùng tới (tên + độ gần), không tính luu_y/kenh.

    Sửa một câu `luu_y` bên bản gốc thì đây là sửa tài liệu, không đổi hành vi cổng — bắt
    `--kiem` kêu vì chuyện đó là dạy người đọc bỏ qua tiếng kêu.
    """
    loi = "\n".join(f"{chuan_ten(h['ten'])}\t{h['do_gan']}" for h in hang)
    return hashlib.sha1(loi.encode("utf-8")).hexdigest()


def doc_ban_goc():
    """Trả (hang_rut_gon, dau_van_tay) hoặc None nếu bản gốc vắng mặt."""
    if not BAN_GOC.exists():
        return None
    goc = json.loads(BAN_GOC.read_text(encoding="utf-8"))
    hang = _rut_gon(goc)
    return hang, _dau_van_tay(hang)


def sinh() -> int:
    kq = doc_ban_goc()
    if kq is None:
        print(f"[LỖI] không thấy bản gốc: {BAN_GOC}", file=sys.stderr)
        return 2
    hang, dau = kq
    noi_dung = {
        "_doc": (
            "SINH TỰ ĐỘNG — ĐỪNG SỬA TAY. Sửa bản gốc rồi chạy "
            "`python3 scripts/dong_bo_do_gan.py --sinh`."
        ),
        "_ban_goc": str(BAN_GOC),
        "_sinh_boi": "scripts/dong_bo_do_gan.py",
        "_dau_van_tay": dau,
        "_thang": {
            "1": "nguồn gốc chính thức",
            "2": "hãng tin có phóng viên tại chỗ",
            "3": "trang tổng hợp / dẫn lại",
            "4": "kênh tuyên truyền",
        },
        "so_hang": len(hang),
        "hang": hang,
    }
    BAN_TRONG_REPO.parent.mkdir(parents=True, exist_ok=True)
    BAN_TRONG_REPO.write_text(
        json.dumps(noi_dung, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    dem = {}
    for h in hang:
        dem[h["do_gan"]] = dem.get(h["do_gan"], 0) + 1
    print(f"Đã sinh {BAN_TRONG_REPO.relative_to(REPO)} — {len(hang)} hãng "
          f"(độ gần 1:{dem.get(1,0)} · 2:{dem.get(2,0)} · 3:{dem.get(3,0)} · 4:{dem.get(4,0)})")
    print(f"  dấu vân tay: {dau}")
    return 0


def kiem() -> int:
    if not BAN_TRONG_REPO.exists():
        print(f"[LỆCH] thiếu bản trong repo: {BAN_TRONG_REPO}", file=sys.stderr)
        return 1
    trong_repo = json.loads(BAN_TRONG_REPO.read_text(encoding="utf-8"))
    dau_repo = trong_repo.get("_dau_van_tay")

    kq = doc_ban_goc()
    if kq is None:
        # Không đo được — KHÔNG được báo khớp. Trên máy chạy GitHub thì đây là ca bình
        # thường; ở máy Huy thì nghĩa là bản gốc bị dời/xoá, phải biết ngay.
        print(f"[KHÔNG ĐO ĐƯỢC] bản gốc vắng mặt: {BAN_GOC}")
        print(f"  (bản trong repo vẫn dùng được — dấu vân tay {dau_repo})")
        return 2
    hang_goc, dau_goc = kq

    # Tự kiểm bản trong repo: dấu vân tay phải khớp CHÍNH NỘI DUNG nó đang mang, kẻo ai đó
    # sửa tay danh sách mà quên sửa dấu -> hai bản lệch nhưng dấu vẫn khớp nhau (fail-open).
    dau_tinh_lai = _dau_van_tay(trong_repo.get("hang", []))
    if dau_tinh_lai != dau_repo:
        print(f"[LỆCH] bản trong repo bị sửa tay: dấu ghi {dau_repo!r} nhưng nội dung "
              f"tính ra {dau_tinh_lai!r} — chạy --sinh", file=sys.stderr)
        return 1

    if dau_goc != dau_repo:
        m_goc = {chuan_ten(h["ten"]): h["do_gan"] for h in hang_goc}
        m_repo = {chuan_ten(h["ten"]): h["do_gan"] for h in trong_repo.get("hang", [])}
        them = sorted(set(m_goc) - set(m_repo))
        mat = sorted(set(m_repo) - set(m_goc))
        doi = sorted(k for k in set(m_goc) & set(m_repo) if m_goc[k] != m_repo[k])
        print(f"[LỆCH] bản gốc {dau_goc} ≠ bản trong repo {dau_repo}", file=sys.stderr)
        if them:
            print(f"  bản gốc có thêm {len(them)}: {', '.join(them[:8])}", file=sys.stderr)
        if mat:
            print(f"  bản gốc đã bỏ {len(mat)}: {', '.join(mat[:8])}", file=sys.stderr)
        for k in doi[:8]:
            print(f"  đổi độ gần: {k} — gốc {m_goc[k]}, repo {m_repo[k]}", file=sys.stderr)
        print("  => chạy `python3 scripts/dong_bo_do_gan.py --sinh`", file=sys.stderr)
        return 1

    print(f"Khớp bản gốc — {len(hang_goc)} hãng, dấu vân tay {dau_goc}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--sinh", action="store_true", help="dựng lại bản trong repo từ bản gốc")
    g.add_argument("--kiem", action="store_true", help="so hai bản, lệch thì mã thoát 1")
    a = p.parse_args()
    return sinh() if a.sinh else kiem()


if __name__ == "__main__":
    sys.exit(main())
