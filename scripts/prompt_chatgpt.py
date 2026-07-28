#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh prompt HOÀN CHỈNH để dán vào ChatGPT khi hết hạn mức Claude, và nạp JSON nó trả về.

VÌ SAO CÓ FILE NÀY (chỉ thị Huy 28/07/2026): "xuất cho tao quy tắc quét tin buổi tối có thể
sử dụng cho chatgpt, đề phòng tối nay hết token". ChatGPT KHÔNG có repo/Bash/git nên nó chỉ
làm được khâu THẨM ĐỊNH + VIẾT. Phần máy làm (harvest, chống trùng, guardrail, commit) vẫn
chạy trên máy Huy bằng terminal — KHÔNG tốn hạn mức Claude.

Hai chiều dùng:

  1) Sinh prompt (tự chạy harvest + --recent-titles rồi nhúng thẳng vào prompt):
       python3 scripts/prompt_chatgpt.py
     -> ghi /tmp/prompt-chatgpt.md . Mở file, copy TẤT CẢ, dán vào ChatGPT.

  2) Nạp JSON ChatGPT trả về (tự bóc ```json fence, validate rồi gọi add_news.py):
       python3 scripts/prompt_chatgpt.py --nap /tmp/tu-chatgpt.json

Quy tắc nhúng trong prompt lấy từ .claude/skills/quet-tin/SKILL.md + CLAUDE.md. Sửa luật quét
thì sửa hai file đó TRƯỚC, rồi mới đối chiếu lại file này — đừng để hai bộ luật lệch nhau.
"""
import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
OUT = "/tmp/prompt-chatgpt.md"

CATEGORY = "Kinh tế · Chính trị · Công nghệ quân sự · Ngoại giao"
REGION = ("Châu Âu/NATO · Trung Đông · Đông Á · Toàn cầu · Châu Mỹ · "
          "Ấn Độ Dương - Thái Bình Dương")


def chay(cmd, mo_ta):
    print(f"[{mo_ta}] {' '.join(cmd[:3])} ...", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        print(f"⚠️  {mo_ta} lỗi rc={r.returncode}: {r.stderr[-500:]}", file=sys.stderr)
    return r.stdout


def ung_vien(path="/tmp/ung-vien.json"):
    """Đọc lô ứng viên harvest. Chấp cả 2 dạng: mảng phẳng (--json) và payload (--ci-out)."""
    p = pathlib.Path(path)
    if not p.is_file():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    return d.get("ung_vien", []) if isinstance(d, dict) else d


def lo_con_tuoi(path="/tmp/ung-vien.json", hom_nay=None):
    """Lô harvest còn dùng được không: phải có file, mới < 3 tiếng, VÀ có tin của hôm nay.

    ⚠️ Vá sau khi vấp thật 28/07/2026: bản đầu chỉ kiểm `file có tồn tại` nên chạy lúc 14:40
    ngày 28 vẫn lấy nguyên lô 21:23 ngày 27 — prompt đầy tin 26-27/07, tức NGOÀI khung của
    phiên 28. Kiểu hỏng này im lặng tuyệt đối: prompt trông đầy đặn, ChatGPT trả tin đủ số,
    guardrail add_news.py mới chặn ở cuối, lúc đó đã mất công cả vòng.
    """
    p = pathlib.Path(path)
    if not p.is_file():
        return False, "chưa có lô ứng viên"
    tuoi = (datetime.datetime.now(VN)
            - datetime.datetime.fromtimestamp(p.stat().st_mtime, VN)).total_seconds() / 3600
    if tuoi > 3:
        return False, f"lô cũ {tuoi:.1f} tiếng"
    try:
        if not any(h.get("ngay") == str(hom_nay) for h in ung_vien(path)):
            return False, f"lô không có tin nào ngày {hom_nay}"
    except Exception as e:
        return False, f"lô đọc không được ({e})"
    return True, f"lô mới {tuoi:.1f} tiếng"


def khoi_ung_vien(items, hom_nay, hom_qua, cnqs_som_nhat):
    """Nhóm ứng viên theo chủ đề, LỌC LẠI theo khung ngày.

    Hai lý do phải lọc ở đây dù harvest đã lọc: (a) lô có thể được gom ở phiên trước, khung
    ngày đã trôi; (b) harvest nới 3 ngày cho CNQS nên tin 3 ngày tuổi của chủ đề KHÁC vẫn lọt
    vào lô (đo thật ở lô 27/07: 13 tin ngày 24 + 11 tin ngày 25). Đưa nguyên vào prompt là mời
    ChatGPT nạp tin quá hạn.
    BỎ lớp GNEWS/TG: link là redirect news.google.com / t.me, ChatGPT không truy gốc nổi.
    """
    theo, bo_ngay = {}, 0
    for h in items:
        if h.get("lop") in ("GNEWS", "TG"):
            continue
        chu_de = h.get("chu_de", "(không rõ)")
        som_nhat = cnqs_som_nhat if "CNQS" in chu_de else hom_qua
        ngay = h.get("ngay") or ""
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ngay) or not (str(som_nhat) <= ngay <= str(hom_nay)):
            bo_ngay += 1
            continue
        theo.setdefault(chu_de, []).append(h)
    if bo_ngay:
        print(f"   (đã bỏ {bo_ngay} ứng viên ngoài khung ngày / không rõ ngày)", file=sys.stderr)
    if not theo:
        return ("(KHÔNG có lô ứng viên — chạy `python3 scripts/harvest.py --gop-ci "
                "--json /tmp/ung-vien.json` trước, hoặc để ChatGPT tự tìm bằng nguồn gợi ý.)")
    ra = []
    for chu_de, hs in theo.items():
        ra.append(f"\n### {chu_de} ({len(hs)} ứng viên)")
        for h in hs:
            ra.append(f"- [{h.get('ngay','?')}] {h.get('tieu_de','')} — {h.get('nguon','')}\n  {h.get('url','')}")
    return "\n".join(ra)


def sinh():
    now = datetime.datetime.now(VN)
    hom_nay = now.date()
    hom_qua = hom_nay - datetime.timedelta(days=1)
    cnqs_som_nhat = hom_nay - datetime.timedelta(days=3)

    tuoi, ly_do = lo_con_tuoi(hom_nay=hom_nay)
    print(f"[lô ứng viên] {ly_do}", file=sys.stderr)
    if not tuoi:
        chay([sys.executable, "scripts/harvest.py", "--gop-ci", "--json", "/tmp/ung-vien.json"],
             "harvest lại (2-4 phút)")
    da_co = chay([sys.executable, "scripts/add_news.py", "--recent-titles", "20"], "recent-titles")

    p = OUT
    pathlib.Path(p).write_text(f"""Mày là biên tập viên bản tin "Điểm Tin Thế Giới" (tiếng Việt, chuyên quốc phòng — an ninh — quan hệ quốc tế). Việc của mày: từ danh sách ứng viên dưới đây, CHỌN và VIẾT ra JSON tin để nạp vào web. Máy đã đi lấy tin sẵn — mày chỉ thẩm định, viết, và loại tin sai.

## KHUNG NGÀY — TUYỆT ĐỐI KHÔNG VƯỢT
- Chỉ nhận tin có SỰ KIỆN xảy ra ngày **{hom_nay:%d/%m/%Y}** hoặc **{hom_qua:%d/%m/%Y}**. Tin từ {(hom_qua - datetime.timedelta(days=1)):%d/%m/%Y} trở về trước: **BỎ**.
- NGOẠI LỆ DUY NHẤT — chủ đề "CNQS Mỹ" (khí tài/hợp đồng quốc phòng) được lùi tới **{cnqs_som_nhat:%d/%m/%Y}**.
- ⚠️ **Ngày trong danh sách ứng viên là NGÀY ĐĂNG BÀI, KHÔNG phải ngày sự kiện.** Nhiều trang đăng lại tin cũ với ngày mới. Phải mở bài đọc rồi đặt `date` theo NGÀY SỰ KIỆN. Ví dụ thật: bài "US House passes $1.15 trillion defence bill" hiện ngày 26/07 nhưng cuộc bỏ phiếu diễn ra 22/07 → NGOÀI khung, phải bỏ.

## LUẬT SỐ 1 — KHÔNG MỞ ĐƯỢC BÀI THÌ BỎ TIN
Phải mở từng URL và đọc nội dung thật trước khi viết. **Cấm viết `summary`/`significance` suy từ tiêu đề.** Không mở được (403/paywall/không truy cập được) và không xác nhận được nội dung bằng nguồn thứ hai → **BỎ tin đó**, đừng đoán.
Thà trả về 3 tin sạch còn hơn 8 tin có 1 tin bịa. Được phép trả mảng rỗng cho một chủ đề.

## 5 CHỦ ĐỀ (ngoài 5 cái này thì BỎ, kể cả tin hay)
1. **Nội bộ Mỹ** → `usNews`, category `Chính trị` (hoặc `Kinh tế` nếu đúng nội dung). Ưu tiên theo HAI HẠNG: vét cạn hạng 1 trước — (1) **toàn bộ phiên điều trần + toàn bộ kết quả bỏ phiếu thông qua dự luật**. Thiếu chỉ tiêu mới lấy sang 4 nhóm NGANG HÀNG nhau: (2) sáng kiến/chiến lược chính quyền công bố trên kênh chính thống các bộ (sắc lệnh, memorandum, fact sheet) · (3) biểu tình/tuần hành/đình công · (4) kinh tế Mỹ (Fed, thuế quan, trừng phạt, số liệu) + động thái Nhà Trắng/nội các · (5) bầu cử (giữa kỳ, sơ bộ, thăm dò, quy định cử tri, redistricting). Phải là chuyện NỘI BỘ MỸ — tin protest/tariff/election của nước khác thì bỏ.
2. **Úc & Biển Đông** → `worldNews`. AUKUS/quốc phòng Úc (`region: "Ấn Độ Dương - Thái Bình Dương"`) + chủ quyền/tuần tra/tập trận Biển Đông (`region: "Đông Á"`), gồm cả Malaysia, Indonesia, Brunei, Đài Loan, Việt Nam, đàm phán COC ASEAN–Trung Quốc, các thực thể Natuna/Bãi Tư Chính/Luconia/Bãi Cỏ Rong.
3. **CNQS Mỹ** → `usNews`, category `Công nghệ quân sự`. Khí tài/hệ thống CỤ THỂ của Mỹ (tên lửa, phòng không, hải quân, không gian, laser, drone, AI quân sự, hợp đồng quốc phòng). Khí tài nước khác KHÔNG thuộc mục này.
4. **Mỹ – Mali** → `usNews`. Việc Mỹ cân nhắc/triển khai quân sự ở Sahel nhắm JNIM; phản ứng của Mali/Nga/JNIM. Gắn từ Mali/JNIM/Bamako/Sahel.
5. **Tập trận Predator's Run 2026** → `exerciseUpdates`, `name` phải khớp ĐÚNG chuỗi: `Predator's Run 2026 (tập trận Mỹ - Úc - Philippines)`.

Mỗi chủ đề nhắm **5–10 tin**; thiếu thì để ít, KHÔNG nhồi.

## LUẬT NGUỒN
| Nguồn | Cần xác nhận thêm? |
|---|---|
| Chính thức (war.gov, whitehouse.gov, state.gov, navy.mil, defence.gov.au, qdnd.vn, mofa…) | KHÔNG — thông cáo tự nó là xác nhận |
| Wire (Reuters, AP, AFP, Bloomberg) hoặc báo chuyên ngành (Defense News, Breaking Defense, Defense One, Naval News, SpaceNews, DefenseScoop, Janes) | KHÔNG — một nguồn là đủ |
| Báo phổ thông uy tín (BBC, Al Jazeera, SCMP, Nikkei, The Hill, CBS) | KHÔNG — một nguồn là đủ |
| **Trang TỔNG HỢP / DẪN LẠI** (Báo Mới, RealClear*, Yahoo/AOL/MSN, Investing.com) | **CÓ — bắt buộc truy về BÀI GỐC** rồi lấy link gốc. Không ra gốc thì cần 2 nguồn độc lập, không thì BỎ |
| Truyền thông nhà nước độc tài (Xinhua, TASS, Global Times, KCNA) | Chỉ dùng cho phát ngôn CỦA CHÍNH HỌ |

## CẤM
- Bịa tin, bịa link, bịa số liệu. Link phải mở được và KHỚP nội dung tin.
- `sourceUrl` là trang chủ, trang chuyên mục, "live updates"/live-blog, hay trang tổng hợp.
- Link `news.google.com` hoặc `t.me` (đó là radar, không phải nguồn).
- Hai tin cùng một sự kiện (dù khác nguồn, khác cách quy đổi số liệu, khác tiêu đề) → chỉ giữ 1, chọn nguồn tường thuật tốt nhất.
- Trùng với tin ĐÃ CÓ trong danh sách "tin đã nạp" bên dưới — kể cả dưới tiêu đề/góc nhìn khác, trừ khi có diễn biến MỚI HẲN.

## ĐỊNH DẠNG TRẢ VỀ — CHỈ MỘT KHỐI JSON, KHÔNG GIẢI THÍCH GÌ THÊM
```json
{{
  "date": "{hom_nay}",
  "worldNews": [
    {{"date":"YYYY-MM-DD","category":"<{CATEGORY}>","title":"...","summary":"2-4 câu, tiếng Việt, nêu dữ kiện cụ thể (con số, tên khí tài, địa danh, ai làm gì)","sourceName":"...","sourceUrl":"https://...","significance":"1-2 câu Ý NGHĨA chiến lược — vì sao tin này đáng đọc","region":"<{REGION}>"}}
  ],
  "usNews": [
    {{"date":"YYYY-MM-DD","category":"...","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://...","significance":"..."}}
  ],
  "exerciseUpdates": [
    {{"name":"Predator's Run 2026 (tập trận Mỹ - Úc - Philippines)","items":[{{"date":"YYYY-MM-DD","title":"...","summary":"...","sourceName":"...","sourceUrl":"https://..."}}]}}
  ]
}}
```
Quy tắc field: `date` của MỖI tin là ngày sự kiện (trong khung trên). `date` ngoài cùng = ngày TIN MỚI NHẤT trong lô. `category` chỉ 4 giá trị đã nêu. `region` CHỈ dùng cho `worldNews`. Mảng nào không có tin thì để `[]`. Tiếng Việt tự nhiên, không dịch máy, không sáo rỗng ("đánh dấu bước ngoặt", "cho thấy tầm quan trọng" — cấm).

Sau khối JSON, thêm một khối riêng liệt kê ngắn: chủ đề nào không đủ 5 tin và LÝ DO THẬT (nguồn cạn / tin ngoài khung ngày / trùng sự kiện đã có / không mở được bài). Ghi rõ để tao dán vào bản kê "chủ đề thiếu".

---

## TIN ĐÃ NẠP — KHÔNG ĐƯỢC LẶP LẠI
```
{da_co.strip()}
```

---

## ỨNG VIÊN (máy đã gom, đã lọc theo khung ngày + 5 chủ đề)
{khoi_ung_vien(ung_vien(), hom_nay, hom_qua, cnqs_som_nhat)}
""", encoding="utf-8")
    print(f"\n✅ Đã ghi prompt ra {p}")
    print("   Mở file, copy TẤT CẢ, dán vào ChatGPT (bật chế độ duyệt web).")
    print("   ChatGPT trả JSON -> lưu vào /tmp/tu-chatgpt.json -> chạy:")
    print(f"   python3 {ROOT}/scripts/prompt_chatgpt.py --nap /tmp/tu-chatgpt.json")


def nap(path):
    """Bóc ```json fence + lời dẫn, validate, rồi gọi add_news.py."""
    raw = pathlib.Path(path).read_text(encoding="utf-8")
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
    txt = m.group(1) if m else raw[raw.find("{"): raw.rfind("}") + 1]
    try:
        d = json.loads(txt)
    except json.JSONDecodeError as e:
        sys.exit(f"❌ JSON ChatGPT trả về không parse được: {e}\nSửa tay rồi chạy lại.")

    if "date" not in d:
        sys.exit('❌ thiếu khoá "date" ngoài cùng.')
    cho_phep = {"date", "worldNews", "usNews", "baomoiNews", "exerciseUpdates",
                "dipEventUpdates", "newDipEvents", "rejectedNews"}
    la = set(d) - cho_phep
    if la:
        print(f"⚠️  bỏ khoá lạ ChatGPT tự thêm: {sorted(la)}")
        for k in la:
            d.pop(k)
    n = sum(len(d.get(k, [])) for k in ("worldNews", "usNews", "baomoiNews"))
    print(f"Lô: {n} tin thường + {len(d.get('exerciseUpdates', []))} cụm tập trận")

    sach = "/tmp/new_items.json"
    pathlib.Path(sach).write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {sach} — chạy guardrail:\n")
    r = subprocess.run([sys.executable, "scripts/add_news.py", sach], cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit("\n❌ add_news.py CHẶN — sửa/bỏ tin lỗi trong /tmp/new_items.json rồi chạy:\n"
                 f"   python3 {ROOT}/scripts/add_news.py /tmp/new_items.json")
    print("\n✅ Nạp xong. Còn 2 việc BẮT BUỘC trước khi push — xem "
          "docs/quy-trinh-du-phong-chatgpt.md mục 4 (ghi scan-gaps.json + commit).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--nap", metavar="FILE", help="nạp JSON ChatGPT trả về")
    a = ap.parse_args()
    nap(a.nap) if a.nap else sinh()
