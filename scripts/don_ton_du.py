#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dọn tồn dư chưa commit TRƯỚC khi phiên quét chạy `git pull --rebase`.

VÌ SAO CÓ FILE NÀY (chỉ thị Huy 07/08/2026: *"lần sau phải tự động đẩy việc dở,
không được để ảnh hưởng đến việc quét tin"*).

Sáng 07/08/2026 mốc quét local 04:30 chết ngay dòng ĐẦU TIÊN của Bước 1:
`cannot pull with rebase: You have unstaged changes` — vì một phiên khác dựng
`scripts/do_can_doi_khu_vuc.py` + sửa `CLAUDE.md` lúc 21:37 tối trước rồi kết
phiên mà không commit. Cùng đêm đó GitHub không cấp máy chạy (mọi run từ 22:56
tới 04:45 chết sau 15 phút, 0 bước), nên lưới local lẽ ra phải gánh — và nó
không gánh được vì lý do chẳng liên quan gì tới việc quét. Bản tin sáng muộn
một tiếng (05:45 thay vì ~04:35).

Luật cũ ở Bước 1 là *"KHÔNG stash, KHÔNG commit hộ file lạ, KẾT THÚC"*. Luật đó
đúng khi phiên khác ĐANG gõ dở — nhưng nó không phân biệt được *đang gõ dở* với
*bỏ quên 12 tiếng*, nên nó biến mọi tồn dư nguội thành một mốc quét chết. Script
này phân biệt bằng TUỔI FILE (mtime không nói dối) rồi xử theo nhóm.

BỐN NHÓM, mỗi nhóm một cách xử — xem bảng `NHOM` bên dưới:

  NÓNG (mtime < NGUOI_PHUT)   → KHÔNG đụng, kêu, mã 4. Phiên khác đang gõ thật.
  SINH tự động                → lấy lại bản remote (checkout FETCH_HEAD).
  MÃ NGUỒN / tài liệu         → commit + push, message KHÔNG khớp gate notify.
  CẦN NGƯỜI (index.html, …)   → KHÔNG đụng, kêu, mã 3.

⚠️ `index.html` CỐ Ý nằm ở nhóm CẦN NGƯỜI, đừng "dọn cho gọn" đưa nó sang nhóm
   commit: đó là nội dung bản tin đi thẳng ra web công khai, và tồn dư của nó
   nghĩa là `add_news.py` chết giữa chừng — commit hộ là đẩy một bản tin dở dang
   lên trang. Hướng lệch có chủ ý: thà một mốc quét chết (mốc sau gánh) còn hơn
   xuất bản nội dung chưa ai nhìn.

⚠️ Message commit TUYỆT ĐỐI không được bắt đầu bằng `Cap nhat ban tin` /
   `Cap nhat su kien` — hai tiền tố đó là cổng 1 của `notify-email.yml`, trùng
   vào là script này tự gửi một bản tin rỗng cho người đọc. Ca [09] canh.

⚠️ File **untracked** KHÔNG chặn `pull --rebase` (đã đo, xem bảng ở Bước 1 của
   `docs/routine-web-scan.md`). Nên chúng chỉ được commit khi nằm trong thư mục
   mã nguồn đã khai; untracked lạ thì BỎ QUA và báo — repo này PUBLIC, tự commit
   một file lạ có thể đẩy dữ liệu riêng lên GitHub. Ca [07] canh chiều nới tay.

Mã thoát:
  0 — repo sạch, hoặc đã dọn xong và `pull --rebase` chạy được
  3 — còn thứ thuộc nhóm CẦN NGƯỜI
  4 — còn file NÓNG (phiên khác đang gõ dở)
  2 — không đo được (không phải repo git, lệnh git hỏng)

Dùng:
  python3 scripts/don_ton_du.py            # dọn thật
  python3 scripts/don_ton_du.py --kiem     # chỉ soi, không ghi gì
  python3 scripts/don_ton_du.py --tu-kiem  # chứng minh bộ ca bắt được lỗi
"""
import argparse
import os
import subprocess
import sys
import time
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ngưỡng NGUỘI. 90 phút: phiên quét dài nhất đo được là ~30 phút, phiên người
# ngồi sửa tay thì lưu liên tục — 90 phút đủ rộng để không bao giờ giật file
# khỏi tay ai, đủ hẹp để tồn dư qua đêm luôn được dọn trước mốc 03:47.
NGUOI_PHUT = 90

# File do máy sinh lại mỗi lượt chạy — bản remote luôn mới hơn hoặc bằng, nên
# lấy lại bản remote là đúng. TUYỆT ĐỐI không commit chúng: hai phiên cùng ghi
# thì commit local đè lô của phiên kia.
FILE_SINH = (
    'baomoi-saved.json',
    'baomoi-topics.json',
    'docs/ung-vien-ci.json',
    'docs/probe-ci.json',
    'preferences.json',
)
THU_MUC_SINH = ('logs/',)

# Thư mục/đuôi được phép commit tự động.
THU_MUC_MA = ('scripts/', 'tests/', 'docs/', '.github/', '.claude/')
DUOI_MA = ('.py', '.md', '.yml', '.yaml', '.sql', '.txt')

# Cần người xem tận mắt — nội dung đi thẳng ra web hoặc ra người đọc.
CAN_NGUOI = ('index.html', 'sw.js', 'manifest.json', 'data/analyses.json',
             'whats-new.json')

# Tiền tố cổng 1 của notify-email.yml / notify-morning.yml. Message dọn không
# bao giờ được bắt đầu bằng chúng.
TIEN_TO_CAM = ('Cap nhat ban tin', 'Cap nhat su kien', 'Dang bao cao tuan')

NHAN_COMMIT = 'Don ton du truoc phien quet'


def _chay(*args, cwd=None):
    """Chạy một lệnh, trả (rc, stdout, stderr). Không bao giờ ném."""
    try:
        p = subprocess.run(args, cwd=cwd or REPO, capture_output=True,
                           text=True, timeout=180)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:  # noqa: BLE001 — lỗi nào cũng phải thành mã, không thành traceback
        return 127, '', str(e)


def _nfc(s):
    """macOS liệt kê tên file dạng NFD; bảng trong mã nguồn là NFC."""
    return unicodedata.normalize('NFC', s)


def doc_trang_thai(repo):
    """Đọc `git status --porcelain` → [(ma, duong_dan)]. Ném LoiDo nếu không đo được.

    ⚠️ Khi CẢ MỘT THƯ MỤC chưa từng được track, git gộp thành một dòng
    `?? <thư_mục>/` thay vì liệt từng file bên trong. Đo tuổi của dòng đó là
    đo tuổi THƯ MỤC — mà thư mục vừa đổi mtime ngay khi có file mới sinh bên
    trong nó, nên mọi file cũ trong một thư mục MỚI đều bị hiểu nhầm là vừa
    sửa (NÓNG). Bắt được bằng test: file 200 phút tuổi trong thư mục
    `scripts/` mới toanh vẫn bị chặn commit vì tuổi đo ra là thư mục = 0
    phút. Phải bung thư mục đó ra từng file trước khi đo tuổi.
    """
    rc, out, err = _chay('git', '-C', repo, 'status', '--porcelain', cwd=repo)
    if rc != 0:
        raise LoiDo('git status rc=%d: %s' % (rc, (err or out).strip()[:200]))
    ds = []
    for dong in out.splitlines():
        if len(dong) < 4:
            continue
        ma, duong = dong[:2], _nfc(dong[3:].strip())
        # Tên có khoảng trắng được git bọc nháy kép.
        if duong.startswith('"') and duong.endswith('"'):
            duong = duong[1:-1]
        # Đổi tên: "cũ -> mới", lấy vế mới.
        if ' -> ' in duong:
            duong = duong.split(' -> ', 1)[1]
        if duong.endswith('/'):
            goc = os.path.join(repo, duong)
            for dpath, _dirs, files in os.walk(goc):
                for fn in files:
                    rel = os.path.relpath(os.path.join(dpath, fn), repo)
                    ds.append((ma, _nfc(rel)))
            continue
        ds.append((ma, duong))
    return ds


class LoiDo(Exception):
    """Không đo được hiện trạng — phải trả mã 2, không được đoán là 'sạch'."""


def tuoi_phut(repo, duong):
    """Tuổi file tính bằng phút. Không đọc được mtime ⇒ trả 0.0 = coi là NÓNG.

    Fail về phía KHÔNG ĐỤNG: hàm này cấp đại lượng để so ngưỡng, mà hướng lệch
    an toàn ở đây là bỏ qua một file (mốc quét vẫn có thể chết) chứ không phải
    commit nhầm việc dở của người đang gõ.
    """
    try:
        mt = os.path.getmtime(os.path.join(repo, duong))
    except OSError:
        return 0.0
    return max(0.0, (time.time() - mt) / 60.0)


def phan_nhom(duong, ma):
    """Trả một trong: 'sinh' · 'ma' · 'can_nguoi' · 'la'."""
    d = _nfc(duong)
    if d in CAN_NGUOI:
        return 'can_nguoi'
    if d in FILE_SINH or d.startswith(THU_MUC_SINH):
        return 'sinh'
    if d.startswith(THU_MUC_MA) or (os.sep not in d and d.endswith(DUOI_MA)):
        return 'ma'
    return 'la'


def _co_remote(repo):
    rc, out, _ = _chay('git', '-C', repo, 'remote', cwd=repo)
    return rc == 0 and out.strip() != ''


def don(repo=REPO, chi_kiem=False, nguoi_phut=NGUOI_PHUT, im=False):
    """Dọn tồn dư. Trả (ma_thoat, bao_cao_dict)."""
    def noi(*a):
        if not im:
            print(*a)

    bc = {'nong': [], 'sinh': [], 'ma': [], 'can_nguoi': [], 'la': [],
          'sinh_untracked': [], 'da_commit': False, 'da_push': False, 'loi': []}

    try:
        ds = doc_trang_thai(repo)
    except LoiDo as e:
        noi('✗ KHÔNG ĐO ĐƯỢC: %s' % e)
        bc['loi'].append(str(e))
        return 2, bc

    if not ds:
        noi('✓ repo sạch, không có gì phải dọn')
        return 0, bc

    for ma, duong in ds:
        untracked = ma == '??'
        if tuoi_phut(repo, duong) < nguoi_phut:
            bc['nong'].append(duong)
            continue
        nhom = phan_nhom(duong, ma)
        if nhom == 'ma' and untracked and os.sep not in _nfc(duong):
            # File mới ở GỐC repo: không đủ căn cứ để tự thêm vào repo public.
            nhom = 'la'
        if nhom == 'sinh' and untracked:
            bc['sinh_untracked'].append(duong)
        bc[nhom].append(duong)

    for ten, ds_f in (('NÓNG (phiên khác đang gõ)', bc['nong']),
                      ('sinh tự động', bc['sinh']),
                      ('mã nguồn/tài liệu', bc['ma']),
                      ('CẦN NGƯỜI', bc['can_nguoi']),
                      ('lạ — bỏ qua', bc['la'])):
        if ds_f:
            noi('  %-28s %s' % (ten + ':', ', '.join(ds_f)))

    if chi_kiem:
        return _ma_thoat(bc), bc

    # 1) File sinh tự động: BỎ thay đổi cục bộ, quay về bản đã commit gần
    #    nhất — thuần local, không cần mạng. Trước đây thử `fetch` rồi
    #    `checkout FETCH_HEAD -- <file>` để lấy đúng bản REMOTE, nhưng cách
    #    đó luôn để lại một diff ĐÃ STAGE (index khác HEAD cũ vì repo chưa
    #    `pull`) — và đúng diff đó lại tự chặn `pull --rebase` của bước kế
    #    tiếp, tức dựng lại chính lỗi đang vá. Nội dung các file này do
    #    CHÍNH pipeline ghi lại ngay trong lượt chạy này, nên bỏ bản tồn dư
    #    là an toàn; `pull --rebase` ở Bước 1 sẽ tự lấy đúng bản remote mới
    #    nhất ngay sau đó vì không còn gì để xung đột.
    tracked_sinh = [f for f in bc['sinh'] if f not in bc['sinh_untracked']]
    if tracked_sinh:
        rc, _, err = _chay('git', '-C', repo, 'checkout', '--', *tracked_sinh, cwd=repo)
        if rc != 0:
            bc['loi'].append('checkout -- sinh rc=%d: %s' % (rc, err.strip()[:150]))
        else:
            noi('  ↺ bỏ thay đổi cục bộ (đã track): %s' % ', '.join(tracked_sinh))
    if bc['sinh_untracked']:
        # Untracked KHÔNG chặn `pull --rebase` (đã đo — xem bảng ở Bước 1
        # của docs/routine-web-scan.md) nên không cần đụng vào, chỉ báo.
        noi('  · untracked, không chặn pull nên bỏ qua: %s'
            % ', '.join(bc['sinh_untracked']))

    # 2) Mã nguồn/tài liệu: commit + push.
    if bc['ma']:
        rc, _, err = _chay('git', '-C', repo, 'add', '-N', *bc['ma'], cwd=repo)
        if rc != 0:
            bc['loi'].append('add -N rc=%d: %s' % (rc, err.strip()[:150]))
        msg = ('%s\n\nXe tu phien truoc chua commit; de nguyen thi `pull --rebase`\n'
               'cua phien quet chet ngay dong dau.\n' % NHAN_COMMIT)
        rc, out, err = _chay('git', '-C', repo, 'commit', *bc['ma'], '-m', msg, cwd=repo)
        if rc == 0:
            bc['da_commit'] = True
            noi('  ✔ commit %d file: %s' % (len(bc['ma']), ', '.join(bc['ma'])))
            if _co_remote(repo):
                for _ in range(3):
                    rc, _, err = _chay('git', '-C', repo, 'push', 'origin', 'main', cwd=repo)
                    if rc == 0:
                        bc['da_push'] = True
                        break
                    _chay('git', '-C', repo, 'pull', '--rebase', 'origin', 'main', cwd=repo)
                if bc['da_push']:
                    noi('  ✔ push OK')
                else:
                    bc['loi'].append('push hỏng: %s' % err.strip()[:150])
                    noi('  ⚠ push hỏng — commit vẫn còn ở local, pull sẽ chạy được')
        else:
            bc['loi'].append('commit rc=%d: %s' % (rc, (err or out).strip()[:200]))
            noi('  ✗ commit hỏng: %s' % (err or out).strip()[:150])

    return _ma_thoat(bc), bc


def _ma_thoat(bc):
    if bc['nong']:
        return 4
    if bc['can_nguoi']:
        return 3
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--kiem', action='store_true', help='chỉ soi, không ghi gì')
    ap.add_argument('--tu-kiem', action='store_true', help='chạy bộ ca tự kiểm')
    ap.add_argument('--repo', default=REPO)
    ap.add_argument('--nguoi-phut', type=int, default=NGUOI_PHUT)
    a = ap.parse_args(argv)

    if a.tu_kiem:
        import runpy
        bo = os.path.join(REPO, 'tests', 'test-don-ton-du.py')
        sys.argv = [bo, '--tu-kiem']
        runpy.run_path(bo, run_name='__main__')
        return 0

    ma, _ = don(repo=a.repo, chi_kiem=a.kiem, nguoi_phut=a.nguoi_phut)
    if ma == 4:
        print('⚠ còn file NÓNG — phiên khác đang gõ dở, KHÔNG đụng vào')
    elif ma == 3:
        print('⚠ còn file CẦN NGƯỜI — không tự commit, xử theo Bước 1')
    return ma


if __name__ == '__main__':
    sys.exit(main())
