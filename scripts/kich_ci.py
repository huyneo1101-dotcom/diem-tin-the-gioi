#!/usr/bin/env python3
"""KÍCH WORKFLOW CI ĐÚNG GIỜ từ máy Mac — thay cho cron GitHub (vốn trễ 54' – 3h45).

Chạy bởi LaunchAgent `com.huy.diemtin-kich-ci` (xem ~/Library/LaunchAgents/).

VÌ SAO (Huy hỏi 27/07/2026 "github kém vậy, phương án?"):
`schedule` của GitHub xếp hàng chung toàn cầu — đo thật 10 mốc/24h: 8 mốc có chạy nhưng
KHÔNG mốc nào đúng giờ (08:00→11:30, 08:45→12:30, 21:00→22:09). Mốc 21:00 trễ 69' làm bản
tin tối 26/07 vỡ hạn email 22:00.
Ngược lại `workflow_dispatch` gọi qua API thì chạy NGAY, không qua hàng đợi đó.

VÌ SAO KHÔNG DÙNG cron-job.org: cách đó đúng giờ hơn (không phụ thuộc máy Mac) nhưng cần
tạo tài khoản + Personal Access Token dán sang dịch vụ bên thứ ba. Máy này đã có `gh` đăng
nhập sẵn nên kích được ngay, không đẻ thêm credential nào. Hướng dẫn cron-job.org vẫn giữ ở
`docs/cron-ngoai.md` nếu sau này muốn thoát ly hẳn khỏi máy Mac.

ĐIỂM MẠNH SO VỚI LỚP LOCAL SẴN CÓ: lớp local (`web-scan-diem-tin-toi`) phải giữ máy thức
suốt ~20 phút quét. Cái này chỉ cần máy thức **vài giây** để gửi một lệnh API — phần quét
chạy trên GitHub. Máy đóng nắp ngay sau đó cũng không sao.
"""
import datetime
import subprocess
import sys
import zoneinfo

GH = "/opt/homebrew/bin/gh"
REPO = "huyneo1101-dotcom/diem-tin-the-gioi"
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# (giờ, phút) -> [workflow cần kích]. LaunchAgent fire đúng các mốc này; script tự khớp mốc
# GẦN NHẤT trong vòng 20 phút để không phụ thuộc jitter của launchd.
LICH = {
    (20, 45): ["harvest-ci.yml"],
    (21, 0): ["claude-web-scan.yml"],
    (22, 0): ["claude-web-scan.yml"],          # lớp vét
    (4, 30): ["harvest-ci.yml", "claude-web-scan.yml"],
    (8, 45): ["claude-event-scan.yml"],
}
DUNG_SAI_PHUT = 20


def moc_gan_nhat(now):
    tot, cach = None, None
    for (h, m), wfs in LICH.items():
        moc = now.replace(hour=h, minute=m, second=0, microsecond=0)
        d = abs((now - moc).total_seconds()) / 60
        if d <= DUNG_SAI_PHUT and (cach is None or d < cach):
            tot, cach = wfs, d
    return tot, cach


def main():
    now = datetime.datetime.now(VN)
    wfs, cach = moc_gan_nhat(now)
    print(f"[{now:%d/%m %H:%M}] ", end="")
    if not wfs:
        print(f"không khớp mốc nào trong ±{DUNG_SAI_PHUT}' — không kích gì.")
        return 0
    print(f"khớp mốc (lệch {cach:.0f}') -> kích {', '.join(wfs)}")
    loi = 0
    for wf in wfs:
        p = subprocess.run([GH, "workflow", "run", wf, "--repo", REPO],
                           capture_output=True, text=True, timeout=120)
        if p.returncode == 0:
            print(f"   ✅ {wf}")
        else:
            loi += 1
            print(f"   ❌ {wf}: {(p.stderr or p.stdout).strip()[:200]}")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
