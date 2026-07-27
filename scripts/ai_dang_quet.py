#!/usr/bin/env python3
"""AI ĐANG QUÉT? — trả lời trong 5 giây: CI có chạy không, ai giữ khoá, bản tin tới đâu.

Dùng:  python3 scripts/ai_dang_quet.py

VÌ SAO CÓ FILE NÀY (Huy hỏi 27/07/2026: *"làm sao để biết github có đang quét hay không"*):
Hệ thống có HAI lớp quét (CI GitHub = mốc chính, máy Mac = lưới dự phòng) và một khoá
idempotent đồng bộ qua git. Muốn biết trạng thái phải ghép 3 nguồn — `gh run list`,
`logs/state.json`, `DATA.generatedAt` — mà không ai nhớ nổi cả ba lệnh.

⚠️ Điều quan trọng nhất script này phát hiện: **GitHub HAY BỎ CRON**. Đo thật 27/07: cả 4 mốc
CI (21:00 · 22:00 tối 26/07, 04:00 · 05:00 sáng 27/07) thì 3 mốc không nổ, mốc còn lại trễ
54 phút. Workflow vẫn `active`, cron vẫn đúng — GitHub chỉ đơn giản không chạy. Đó là lý do
lớp local tồn tại, và là lý do đừng kết luận "hỏng" khi thấy CI im.
"""
import datetime
import json
import pathlib
import subprocess
import sys
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
REPO = "huyneo1101-dotcom/diem-tin-the-gioi"

# Mốc CI theo lịch (giờ VN) — để đối chiếu "đáng lẽ đã chạy mấy lần rồi".
MOC_CI = {
    "claude-web-scan.yml": [(21, 0), (22, 0), (4, 0), (5, 0)],
    "claude-event-scan.yml": [(8, 45), (9, 45)],
}


def gio_vn(iso: str):
    """'2026-07-26T15:54:01Z' -> datetime giờ VN."""
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(VN)


def truoc_day(dt: datetime.datetime) -> str:
    giay = (datetime.datetime.now(VN) - dt).total_seconds()
    if giay < 90:
        return "vừa xong"
    phut = giay / 60
    if phut < 90:
        return f"{phut:.0f} phút trước"
    gio = phut / 60
    return f"{gio:.0f} tiếng trước" if gio < 48 else f"{gio/24:.0f} ngày trước"


def runs(wf: str, limit: int = 6):
    p = subprocess.run(
        ["gh", "run", "list", "--repo", REPO, "--workflow", wf, "--limit", str(limit),
         "--json", "createdAt,status,conclusion"],
        capture_output=True, text=True, timeout=60,
    )
    if p.returncode != 0:
        print(f"   (không gọi được gh: {p.stderr.strip()[:120]})")
        return []
    return json.loads(p.stdout or "[]")


def bao_cao_ci():
    print("═══ 1. CI GitHub ═══")
    dang_chay = False
    for wf, moc in MOC_CI.items():
        rs = runs(wf)
        ten = wf.replace("claude-", "").replace(".yml", "")
        if not rs:
            print(f"\n▸ {ten}: KHÔNG CÓ RUN NÀO")
            continue
        chay = [r for r in rs if r["status"] in ("in_progress", "queued")]
        moi = gio_vn(rs[0]["createdAt"])
        if chay:
            dang_chay = True
            print(f"\n▸ {ten}: 🟢 ĐANG CHẠY ({len(chay)} run)")
        else:
            print(f"\n▸ {ten}: ⚪ không chạy")
        print(f"   lần cuối: {moi:%d/%m %H:%M} ({truoc_day(moi)}) "
              f"— {rs[0]['status']}/{rs[0].get('conclusion') or '—'}")
        # Có bỏ mốc nào trong 24h qua không?
        gio_qua = [gio_vn(r["createdAt"]) for r in rs
                   if (datetime.datetime.now(VN) - gio_vn(r["createdAt"])).days < 1]
        print(f"   24h qua: chạy {len(gio_qua)}/{len(moc)} mốc theo lịch", end="")
        print(" ⚠️ GitHub BỎ CRON" if len(gio_qua) < len(moc) else " ✅")
    return dang_chay


def bao_cao_khoa():
    print("\n═══ 2. Khoá idempotent (logs/state.json trên origin) ═══")
    p = subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin", "main"],
                       capture_output=True, text=True, timeout=90)
    p = subprocess.run(["git", "-C", str(ROOT), "show", "origin/main:logs/state.json"],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        print("   (không đọc được state.json)")
        return
    st = json.loads(p.stdout)
    for ten in ("web-scan", "event-scan"):
        o = st.get(ten) or {}
        if not o:
            continue
        lan = o.get("lastRunAt", "?")
        try:
            khi = truoc_day(datetime.datetime.fromisoformat(lan))
        except ValueError:
            khi = "?"
        trang = o.get("lastStatus", "?")
        icon = "🟢 ĐANG CHẠY" if trang == "RUNNING" else f"⚪ {trang}"
        print(f"\n▸ {ten}: {icon}  ô `{o.get('lastSlot', '?')}`  ({khi})")
        if o.get("note"):
            print(f"   ghi chú: {o['note'][:150]}")
        print(f"   xong gần nhất: {o.get('lastSuccess', {})}")


def bao_cao_ban_tin():
    print("\n═══ 3. Bản tin trên web ═══")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    i = html.index("var DATA = ") + len("var DATA = ")
    d, j = 0, i
    while True:
        if html[j] == "{":
            d += 1
        elif html[j] == "}":
            d -= 1
            if d == 0:
                break
        j += 1
    data = json.loads(html[i:j + 1])
    hom_nay = datetime.datetime.now(VN).date().isoformat()
    gen = data.get("generatedAt", "?")
    n = sum(1 for k in ("worldNews", "usNews")
            for it in (data.get(k) or [])
            if it.get("_addedDate") == gen or it.get("date") == gen)
    print(f"   generatedAt: {gen}" + ("  ✅ hôm nay" if gen == hom_nay else "  ⚠️ KHÔNG phải hôm nay"))
    print(f"   tin của ngày đó: {n}")


def main():
    print(f"Bây giờ: {datetime.datetime.now(VN):%d/%m/%Y %H:%M} giờ VN\n")
    dang = bao_cao_ci()
    bao_cao_khoa()
    bao_cao_ban_tin()
    print("\n" + "─" * 60)
    print("🟢 CI ĐANG QUÉT" if dang else
          "⚪ CI không quét lúc này — bình thường nếu ngoài mốc; nếu ĐÚNG mốc thì lớp local sẽ gánh.")


if __name__ == "__main__":
    sys.exit(main() or 0)
