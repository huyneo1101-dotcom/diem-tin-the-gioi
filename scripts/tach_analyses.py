# -*- coding: utf-8 -*-
"""TÁCH `DATA.analyses` khỏi index.html ra `data/analyses.json` (chạy 30/07/2026).

Chạy MỘT LẦN để chuyển đổi; giữ lại trong repo làm bằng chứng và để chạy lại được nếu
một phiên nào đó lỡ nhồi bài ngược vào index.html (cổng `analyses_store.kiem_index_rong`
sẽ bắt được ca đó).

    python3 scripts/tach_analyses.py --kiem   # chỉ soi, không ghi
    python3 scripts/tach_analyses.py          # tách thật

Idempotent: chạy lần hai trên repo đã tách thì báo "đã tách rồi", không đụng file.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from add_analyses import find_data_span  # noqa: E402
from analyses_store import doc, duong_dan, ghi, kiem_index_rong  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    chi_kiem = "--kiem" in sys.argv
    html_path = REPO / "index.html"
    html = html_path.read_text(encoding="utf-8")
    start, end = find_data_span(html)
    data = json.loads(html[start:end])
    trong_index = data.get("analyses") or []

    da_co_file = duong_dan(REPO).exists()
    # đếm BYTE chứ không phải ký tự — tiếng Việt 3 byte/ký tự, lệch hơn 20% nếu đếm nhầm
    print(f"index.html            : {len(html.encode()):,} byte · DATA.analyses = {len(trong_index)} bài")
    print(f"{'data/analyses.json':22s}: {'có · ' + str(len(doc(REPO))) + ' bài' if da_co_file else 'CHƯA có'}")

    if not trong_index and da_co_file:
        print("→ ĐÃ TÁCH RỒI, không cần làm gì.")
        for e in kiem_index_rong(REPO):
            print(f"⚠️  {e}")
        return 0

    if da_co_file:
        # Ca nguy hiểm: bài nằm ở CẢ HAI nơi. Không tự gộp — gộp mù là nhân đôi hoặc mất bài.
        cu = {a.get("url") for a in doc(REPO)}
        moi = {a.get("url") for a in trong_index}
        print(f"⛔ BÀI NẰM Ở CẢ HAI NƠI: file có {len(cu)} url, index.html có {len(moi)} url, "
              f"trùng {len(cu & moi)}, chỉ-có-trong-index {len(moi - cu)}.")
        print("   Không tự gộp — xem lại script nào vừa ghi vào index.html rồi xử lý tay.")
        return 2

    if chi_kiem:
        print("→ (--kiem) sẽ tách {} bài ra {}".format(len(trong_index), duong_dan(REPO)))
        return 0

    ghi(REPO, trong_index)
    data["analyses"] = []
    html_path.write_text(
        html[:start] + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + html[end:],
        encoding="utf-8",
    )

    lai = html_path.read_text(encoding="utf-8")
    print()
    a, b = len(html.encode()), len(lai.encode())
    print(f"OK: tách {len(trong_index)} bài ra {duong_dan(REPO).relative_to(REPO)}")
    print(f"    index.html: {a:,} → {b:,} byte (giảm {a - b:,} = {100 - b * 100 // a}%)")
    print(f"    data/analyses.json: {duong_dan(REPO).stat().st_size:,} byte")
    for e in kiem_index_rong(REPO):
        print(f"⚠️  {e}")
        return 1
    if len(doc(REPO)) != len(trong_index):
        print("⚠️  số bài đọc lại KHÔNG khớp — dừng, kiểm tay")
        return 1
    print("    Kiểm lại: đọc từ file ra đúng số bài, index.html còn analyses rỗng. ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
