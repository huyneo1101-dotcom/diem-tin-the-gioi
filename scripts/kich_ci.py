#!/usr/bin/env python3
"""KÍCH WORKFLOW CI ĐÚNG GIỜ từ máy Mac — thay cho cron GitHub (vốn trễ 54' – 3h45).

Chạy bởi LaunchAgent `com.huy.diemtin-kich-ci` (xem ~/Library/LaunchAgents/).

    python3 scripts/kich_ci.py            # khớp mốc gần nhất rồi kích
    python3 scripts/kich_ci.py --kiem     # KIỂM CHÉO: chưa có bản tin thì kích lại
    python3 scripts/kich_ci.py --wf X.yml # kích thẳng một workflow, bỏ qua lịch

VÌ SAO (Huy hỏi 27/07/2026 "github kém vậy, phương án?"):
`schedule` của GitHub xếp hàng chung toàn cầu — đo thật 10 mốc/24h: 8 mốc có chạy nhưng
KHÔNG mốc nào đúng giờ (08:00→11:30, 08:45→12:30, 21:00→22:09). Mốc 21:00 trễ 69' làm bản
tin tối 26/07 vỡ hạn email 22:00. Ngược lại `workflow_dispatch` gọi qua API chạy NGAY.

VÌ SAO KHÔNG DÙNG cron-job.org: cách đó không phụ thuộc máy Mac, nhưng cần tạo tài khoản +
token dán sang dịch vụ bên thứ ba. Máy này đã có `gh` đăng nhập sẵn nên kích được ngay,
không đẻ thêm credential. Hướng dẫn vẫn giữ ở `docs/cron-ngoai.md` nếu sau muốn thoát ly.

═══ HUY YÊU CẦU "ĐẢM BẢO LUÔN CHẠY ĐÚNG GIỜ" — nên đây KHÔNG chỉ là lệnh gọi ═══
Bốn kiểu hỏng CÂM đã lường và cách bịt:
 1. `gh workflow run` trả về 0 nhưng GitHub không thật sự tạo run
    -> XÁC MINH: đếm run trước/sau, phải thấy run mới. Không thấy thì thử lại.
 2. Lỗi mạng/`gh` hết hạn đăng nhập
    -> THỬ LẠI 3 lần cách nhau 20s, rồi báo bằng notification macOS + ghi log.
 3. Máy ngủ đúng mốc -> không kích được gì
    -> `--kiem` chạy ở mốc muộn hơn: đọc `state.json` trên origin, hôm nay chưa xong thì
       kích lại. Cộng lớp cron GitHub (trễ nhưng có) và lớp local tự quét.
 4. Hỏng mà không ai biết
    -> mọi lần chạy ghi `/tmp/diemtin-kich-ci.log`; `scripts/ai_dang_quet.py` đọc được
       trạng thái thật bất cứ lúc nào.
"""
import argparse
import datetime
import json
import subprocess
import sys
import time
import zoneinfo

GH = "/opt/homebrew/bin/gh"
REPO = "huyneo1101-dotcom/diem-tin-the-gioi"
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# (giờ, phút) -> [workflow cần kích]. Phải KHỚP với StartCalendarInterval trong plist
# `com.huy.diemtin-kich-ci` — sửa một bên mà quên bên kia thì script fire nhưng không khớp
# mốc nào và im lặng không kích gì.
LICH = {
    (20, 45): ["harvest-ci.yml"],
    (21, 0): ["claude-web-scan.yml"],
    (22, 0): ["claude-web-scan.yml"],          # lớp vét
    (4, 30): ["harvest-ci.yml", "claude-web-scan.yml"],
    # (8, 45) claude-event-scan.yml đã BỎ 28/07/2026: pipeline event-scan nay chạy gộp
    # trong CHÍNH job claude-web-scan.yml của phiên sáng sớm (04:00/05:00), không còn
    # mốc riêng để kích.
}
DUNG_SAI_PHUT = 20
SO_LAN_THU = 3
CHO_GIUA_HAI_LAN = 20     # giây


def log(msg):
    print(f"[{datetime.datetime.now(VN):%d/%m %H:%M:%S}] {msg}", flush=True)


def bao_dong(msg):
    """Kênh báo cuối cùng khi mọi thứ hỏng. Máy KHÔNG có token Telegram (secret chỉ nằm trên
    GitHub) nên đành dùng notification của macOS — chỉ thấy được nếu Huy đang ở máy. Vì vậy
    nó KHÔNG phải lớp bảo vệ chính; lớp chính là `--kiem` + cron GitHub + local tự quét."""
    log(f"🚨 {msg}")
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{msg}" with title "Điểm Tin — kích CI HỎNG"'],
            capture_output=True, timeout=15)
    except Exception:                        # noqa: BLE001
        pass


def dem_run(wf):
    """Số run gần đây của workflow — dùng để xác minh lệnh kích có ăn không."""
    p = subprocess.run(
        [GH, "run", "list", "--repo", REPO, "--workflow", wf, "--limit", "5",
         "--json", "databaseId"],
        capture_output=True, text=True, timeout=90)
    if p.returncode != 0:
        return None
    try:
        return {r["databaseId"] for r in json.loads(p.stdout or "[]")}
    except ValueError:
        return None


def kich(wf) -> bool:
    """Kích + XÁC MINH đã có run mới. Trả True nếu chắc chắn ăn."""
    for lan in range(1, SO_LAN_THU + 1):
        truoc = dem_run(wf)
        p = subprocess.run([GH, "workflow", "run", wf, "--repo", REPO],
                           capture_output=True, text=True, timeout=120)
        if p.returncode != 0:
            log(f"   ❌ lần {lan}/{SO_LAN_THU} {wf}: {(p.stderr or p.stdout).strip()[:160]}")
            time.sleep(CHO_GIUA_HAI_LAN)
            continue
        # GitHub cần vài giây mới hiện run trong danh sách.
        time.sleep(8)
        sau = dem_run(wf)
        if truoc is None or sau is None:
            log(f"   ⚠️  {wf}: gọi lệnh OK nhưng KHÔNG xác minh được (gh run list lỗi)")
            return True          # lệnh đã trả 0 — coi như ăn, đừng kích chồng
        if sau - truoc:
            log(f"   ✅ {wf} — đã tạo run mới")
            return True
        log(f"   ❌ lần {lan}/{SO_LAN_THU} {wf}: lệnh trả 0 nhưng KHÔNG có run mới")
        time.sleep(CHO_GIUA_HAI_LAN)
    return False


def moc_gan_nhat(now):
    tot, cach = None, None
    for (h, m), wfs in LICH.items():
        moc = now.replace(hour=h, minute=m, second=0, microsecond=0)
        d = abs((now - moc).total_seconds()) / 60
        if d <= DUNG_SAI_PHUT and (cach is None or d < cach):
            tot, cach = wfs, d
    return tot, cach


def da_xong_hom_nay(o_khoa: str) -> bool:
    """Đọc logs/state.json TRÊN ORIGIN (bản local có thể cũ hàng giờ) xem ô đã xong chưa."""
    root = "/Users/Huy/Claude/diem-tin-the-gioi"
    subprocess.run(["git", "-C", root, "fetch", "-q", "origin", "main"],
                   capture_output=True, timeout=120)
    p = subprocess.run(["git", "-C", root, "show", "origin/main:logs/state.json"],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        log("   ⚠️  không đọc được state.json — coi như CHƯA xong (thà kích thừa còn hơn thiếu)")
        return False
    try:
        st = json.loads(p.stdout)
    except ValueError:
        return False
    hom_nay = datetime.datetime.now(VN).date().isoformat()
    xong = (st.get("web-scan") or {}).get("lastSuccess", {}).get(o_khoa)
    log(f"   state.json: web-scan ô `{o_khoa}` xong gần nhất = {xong} (hôm nay {hom_nay})")
    return xong == hom_nay


def che_do_kiem() -> int:
    """KIỂM CHÉO — chạy sau mốc chính. Chưa có bản tin thì kích lại.

    Đây là lớp bịt kiểu hỏng nguy hiểm nhất: máy ngủ ĐÚNG lúc mốc chính nên không kích được
    gì, mà cũng không có lỗi nào bật lên.
    """
    now = datetime.datetime.now(VN)
    o = "toi" if now.hour >= 14 else "sang"
    log(f"KIỂM CHÉO ô `{o}`")
    if da_xong_hom_nay(o):
        log("   ✅ đã có bản tin hôm nay — không cần kích lại.")
        return 0
    log("   ⚠️  CHƯA có bản tin — kích lại claude-web-scan.yml")
    if kich("claude-web-scan.yml"):
        return 0
    bao_dong(f"Chưa có bản tin ô {o} và kích lại CŨNG HỎNG sau {SO_LAN_THU} lần.")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kiem", action="store_true",
                    help="kiểm chéo: chưa có bản tin hôm nay thì kích lại")
    ap.add_argument("--wf", metavar="FILE", help="kích thẳng workflow này, bỏ qua lịch")
    args = ap.parse_args()

    if args.kiem:
        return che_do_kiem()

    if args.wf:
        return 0 if kich(args.wf) else 1

    now = datetime.datetime.now(VN)
    wfs, cach = moc_gan_nhat(now)
    if not wfs:
        log(f"không khớp mốc nào trong ±{DUNG_SAI_PHUT}' — không kích gì.")
        return 0
    log(f"khớp mốc (lệch {cach:.0f}') -> kích {', '.join(wfs)}")
    hong = [wf for wf in wfs if not kich(wf)]
    if hong:
        bao_dong(f"Kích CI HỎNG sau {SO_LAN_THU} lần: {', '.join(hong)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
