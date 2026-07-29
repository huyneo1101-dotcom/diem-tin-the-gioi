# -*- coding: utf-8 -*-
"""NGUỒN SỰ THẬT của mục 🏛️ Think-tank = `data/analyses.json` (tách 30/07/2026).

VÌ SAO TÁCH: `index.html` chạm 1,54 MB, trong đó riêng `DATA.analyses` (442 bài) chiếm
520 KB thô / 147 KB sau nén — 34% dung lượng lần tải đầu, cho một mục nằm ở tab con
(Phân tích → Think-tank) mà người đọc bản tin ít khi mở. Tách ra rồi web nạp bất đồng bộ
sau khi trang đã hiện.

⛔ SAU KHI TÁCH, `DATA.analyses` TRONG `index.html` LUÔN LÀ MẢNG RỖNG.
Nó chỉ còn để code JS gọi `DATA.analyses||[]` không vỡ trước lúc fetch xong; web ghi đè
bằng dữ liệu thật trong `loadAnalyses()`. Mọi script Python đọc/ghi bài think-tank PHẢI đi
qua module này, TUYỆT ĐỐI không đọc `data["analyses"]` từ index.html nữa — làm vậy sẽ thấy
mảng rỗng và:
  (a) guardrail "url ĐÃ CÓ trong DATA" của add_analyses.py mất tác dụng → nạp trùng cả kho;
  (b) ghi vào đó là ghi vào chỗ không ai đọc → mất bài, KHÔNG có thông báo lỗi nào.
Đó là lý do `doc()` CHẶN CỨNG khi file thiếu/hỏng thay vì trả rỗng cho êm chuyện: rỗng êm
đúng là kiểu hỏng câm mà mục 17 quy tắc toàn cục cấm.

Dùng:
    from analyses_store import doc, ghi, kiem_index_rong
    bai = doc(repo_root)            # -> list, chặn nếu file thiếu/hỏng
    ghi(repo_root, bai)             # ghi lại, giữ cách nén của add_analyses.py

Tự kiểm (chứng minh cổng bắt được lỗi):
    python3 scripts/analyses_store.py --tu-kiem
"""
import json
import pathlib
import sys

TEN_FILE = "data/analyses.json"


def duong_dan(repo_root) -> pathlib.Path:
    return pathlib.Path(repo_root) / "data" / "analyses.json"


def doc(repo_root) -> list:
    """Đọc mảng bài think-tank. CHẶN CỨNG nếu thiếu/hỏng — xem docstring đầu file."""
    p = duong_dan(repo_root)
    if not p.exists():
        raise SystemExit(
            f"LỖI: không thấy {TEN_FILE} — đây là nguồn sự thật của mục Think-tank.\n"
            f"       Kiểm: file có bị xoá nhầm không, hoặc đang chạy ở thư mục khác repo.\n"
            f"       Đường dẫn mong đợi: {p}"
        )
    try:
        bai = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"LỖI: {TEN_FILE} không phải JSON hợp lệ: {e}")
    if not isinstance(bai, list):
        raise SystemExit(f"LỖI: {TEN_FILE} phải là MẢNG bài, đang là {type(bai).__name__}")
    return bai


def ghi(repo_root, bai: list) -> None:
    """Ghi lại mảng bài. Nén giống add_analyses.py để diff không phình vô cớ."""
    if not isinstance(bai, list):
        raise SystemExit(f"LỖI: ghi() cần một MẢNG, nhận {type(bai).__name__}")
    p = duong_dan(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(bai, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def kiem_index_rong(repo_root) -> list:
    """CỔNG HỒI QUY: `DATA.analyses` trong index.html phải RỖNG.

    Không rỗng = có script cũ vừa ghi bài vào index.html thay vì vào data/analyses.json.
    Kiểu hỏng đó hoàn toàn im lặng (web vẫn chạy, bài vẫn hiện nhờ mảng trong index đè lên
    mảng fetch về hoặc ngược lại tuỳ thứ tự) nên phải có cổng đo, không thể trông vào mắt.
    Trả về danh sách lỗi (rỗng = sạch).
    """
    p = pathlib.Path(repo_root) / "index.html"
    if not p.exists():
        return [f"không thấy index.html tại {p}"]
    html = p.read_text(encoding="utf-8")
    if '"analyses":[]' in html:
        return []
    if '"analyses":' not in html:
        return ['index.html KHÔNG còn khoá "analyses" — code JS DATA.analyses sẽ là undefined']
    return ['index.html còn bài trong "analyses" — phải rỗng, bài phải nằm ở ' + TEN_FILE]


# ---------------------------------------------------------------- tự kiểm
_CA = [
    ("thiếu file", "xoa"),
    ("JSON hỏng", "hong"),
    ("JSON không phải mảng", "khong-mang"),
]


def _tu_kiem() -> int:
    """Dựng đúng điều kiện xấu rồi khẳng định doc() THẬT SỰ chặn (mục 17 quy tắc toàn cục)."""
    import shutil
    import tempfile

    repo = pathlib.Path(__file__).resolve().parent.parent
    that = duong_dan(repo)
    goc = that.read_bytes() if that.exists() else None
    loi = 0
    try:
        # --- ca PHẢI CHO QUA: file thật, đọc được
        try:
            bai = doc(repo)
            print(f"  ✅ PHẢI CHO QUA · file thật đọc được {len(bai)} bài")
            if not bai:
                print("  ❌ nhưng mảng RỖNG — kho think-tank trống là bất thường")
                loi += 1
        except SystemExit as e:
            print(f"  ❌ PHẢI CHO QUA nhưng bị chặn: {e}")
            loi += 1

        # --- các ca PHẢI CHẶN
        for ten, kieu in _CA:
            if kieu == "xoa":
                that.unlink(missing_ok=True)
            elif kieu == "hong":
                that.write_text('[{"url":"x"', encoding="utf-8")
            elif kieu == "khong-mang":
                that.write_text('{"analyses":[]}', encoding="utf-8")
            try:
                doc(repo)
                print(f"  ❌ PHẢI CHẶN · {ten} — nhưng LỌT")
                loi += 1
            except SystemExit:
                print(f"  ✅ PHẢI CHẶN · {ten}")
            if goc is not None:
                that.parent.mkdir(parents=True, exist_ok=True)
                that.write_bytes(goc)

        # --- cổng hồi quy index.html
        print(f"  {'✅' if not kiem_index_rong(repo) else '❌'} index.html: "
              f"{kiem_index_rong(repo) or 'DATA.analyses rỗng, đúng thiết kế'}")
        if kiem_index_rong(repo):
            loi += 1

        # ca PHẢI CHẶN cho chính cổng hồi quy: dựng bản index có bài trong analyses
        with tempfile.TemporaryDirectory() as tmp:
            gia = pathlib.Path(tmp)
            (gia / "index.html").write_text('var DATA = {"analyses":[{"url":"x"}]};', encoding="utf-8")
            if kiem_index_rong(gia):
                print("  ✅ PHẢI CHẶN · index.html còn bài trong analyses")
            else:
                print("  ❌ PHẢI CHẶN · index.html còn bài trong analyses — nhưng LỌT")
                loi += 1
    finally:
        if goc is not None:
            that.parent.mkdir(parents=True, exist_ok=True)
            that.write_bytes(goc)
    print()
    print("KẾT QUẢ: " + ("TẤT CẢ ĐẠT" if not loi else f"{loi} ca SAI"))
    return 1 if loi else 0


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        raise SystemExit(_tu_kiem())
    repo = pathlib.Path(__file__).resolve().parent.parent
    print(f"{TEN_FILE}: {len(doc(repo))} bài think-tank")
    for e in kiem_index_rong(repo):
        print(f"⚠️  {e}")
