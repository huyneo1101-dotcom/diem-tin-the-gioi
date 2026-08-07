#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bộ test cho scripts/don_ton_du.py — dọn tồn dư trước phiên quét local.

Chạy:      python3 tests/test-don-ton-du.py
Tự kiểm:   python3 tests/test-don-ton-du.py --tu-kiem
"""
import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, 'scripts', 'don_ton_du.py')


def _chay(*args, cwd):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def _git_init(d):
    _chay('git', 'init', '-q', '-b', 'main', cwd=d)
    _chay('git', 'config', 'user.email', 'test@test', cwd=d)
    _chay('git', 'config', 'user.name', 'Test', cwd=d)


def _ghi(d, rel, noi_dung, cu_phut=None):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(noi_dung)
    if cu_phut is not None:
        t = time.time() - cu_phut * 60
        os.utime(p, (t, t))
    return p


def _commit_ban_dau(d, files):
    for f in files:
        _chay('git', 'add', f, cwd=d)
    _chay('git', 'commit', '-q', '-m', 'init', cwd=d)


def nap_module(duong=SRC, ten='don_ton_du_ca'):
    spec = importlib.util.spec_from_file_location(ten, duong)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- các ca ---

def ca_01_repo_sach(mod):
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        ma, bc = mod.don(repo=d, im=True)
        rong = not any(bc[k] for k in ('nong', 'sinh', 'ma', 'can_nguoi', 'la'))
        return ma == 0 and rong


def ca_02_nong_khong_commit(mod):
    """PHẢI CHẶN: file vừa sửa (0 phút tuổi) không được tự commit."""
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        _ghi(d, 'scripts/foo.py', 'print(1)\n', cu_phut=0)
        ma, bc = mod.don(repo=d, im=True)
        rc, out, _ = _chay('git', 'status', '--porcelain', cwd=d)
        return (ma == 4 and not bc['da_commit'] and 'scripts/foo.py' in bc['nong']
                and out.strip() != '')


def ca_03_ma_nguon_nguoi_commit(mod):
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        _ghi(d, 'scripts/foo.py', 'print(1)\n', cu_phut=200)
        ma, bc = mod.don(repo=d, im=True)
        rc, out, _ = _chay('git', 'status', '--porcelain', cwd=d)
        return ma == 0 and bc['da_commit'] and out.strip() == ''


def ca_04_can_nguoi_khong_commit(mod):
    """PHẢI CHẶN: index.html nguội mấy cũng không tự commit — cần người xem."""
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        _ghi(d, 'index.html', '<html></html>', cu_phut=200)
        ma, bc = mod.don(repo=d, im=True)
        rc, out, _ = _chay('git', 'status', '--porcelain', cwd=d)
        return ma == 3 and not bc['da_commit'] and 'index.html' in out


def ca_05_sinh_lay_ban_remote(mod):
    """File sinh tự động (logs/) nguội → bỏ thay đổi cục bộ (về bản HEAD đã
    commit), KHÔNG commit gì. Sau đó `pull --rebase` (đúng lượt kế tiếp mà
    routine thật sự chạy) phải THÀNH CÔNG và đưa file về đúng bản REMOTE mới
    nhất — đây mới là phép kiểm đúng ý định: "đừng để lại gì chặn pull",
    không phải "tự đi lấy remote thay routine"."""
    with tempfile.TemporaryDirectory() as base:
        bare = os.path.join(base, 'origin.git')
        os.makedirs(bare)
        _chay('git', 'init', '-q', '--bare', '-b', 'main', bare, cwd=base)

        w1 = os.path.join(base, 'w1')
        rc, _, err = _chay('git', 'clone', '-q', bare, w1, cwd=base)
        _chay('git', 'config', 'user.email', 'test@test', cwd=w1)
        _chay('git', 'config', 'user.name', 'Test', cwd=w1)
        _ghi(w1, 'README.md', 'x')
        _ghi(w1, 'logs/scan.log', 'V1\n')
        _commit_ban_dau(w1, ['README.md', 'logs/scan.log'])
        _chay('git', 'push', '-q', 'origin', 'main', cwd=w1)

        w2 = os.path.join(base, 'w2')
        _chay('git', 'clone', '-q', bare, w2, cwd=base)
        _chay('git', 'config', 'user.email', 'test@test', cwd=w2)
        _chay('git', 'config', 'user.name', 'Test', cwd=w2)

        # w1 đẩy phiên bản mới lên remote — w2 chưa fetch, vẫn ở V1.
        _ghi(w1, 'logs/scan.log', 'V2\n')
        _chay('git', 'commit', '-q', '-am', 'v2', cwd=w1)
        _chay('git', 'push', '-q', 'origin', 'main', cwd=w1)

        # Tồn dư ở w2: sửa tay logs/scan.log rồi để nguội.
        _ghi(w2, 'logs/scan.log', 'LOCAL_STALE\n', cu_phut=200)

        ma, bc = mod.don(repo=w2, im=True)
        rc_pull, _out_pull, err_pull = _chay('git', 'pull', '--rebase', 'origin',
                                             'main', cwd=w2)
        rc, out, _ = _chay('git', 'status', '--porcelain', cwd=w2)
        with open(os.path.join(w2, 'logs', 'scan.log'), encoding='utf-8') as f:
            noi_dung_cuoi = f.read()
        return (ma == 0 and not bc['da_commit'] and rc_pull == 0
                and out.strip() == '' and noi_dung_cuoi == 'V2\n')


def ca_06_untracked_scripts_committed(mod):
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        _ghi(d, 'scripts/moi.py', 'x = 1\n', cu_phut=200)
        ma, bc = mod.don(repo=d, im=True)
        rc, out, _ = _chay('git', 'log', '-1', '--name-only', '--format=', cwd=d)
        return ma == 0 and 'scripts/moi.py' in out


def ca_07_la_khong_commit(mod):
    """PHẢI CHẶN chiều nới: file .py MỚI ở GỐC repo (untracked) không tự commit."""
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        _ghi(d, 'ghi-chu.py', '# ghi chu ca nhan\n', cu_phut=200)
        ma, bc = mod.don(repo=d, im=True)
        rc, out, _ = _chay('git', 'status', '--porcelain', cwd=d)
        return ma == 0 and 'ghi-chu.py' in out and not bc['da_commit']


def ca_08_message_khong_trung_gate(mod):
    """PHẢI ĐÚNG: message commit KHÔNG được khớp tiền tố cổng notify-email."""
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        _ghi(d, 'scripts/foo.py', 'x = 1\n', cu_phut=200)
        mod.don(repo=d, im=True)
        rc, out, _ = _chay('git', 'log', '-1', '--format=%s', cwd=d)
        msg = out.strip()
        return bool(msg) and not any(msg.startswith(p) for p in mod.TIEN_TO_CAM)


def ca_09_khong_phai_git(mod):
    """PHẢI CHẶN: không phải repo git thì trả mã 2, không được đoán 'sạch'."""
    with tempfile.TemporaryDirectory() as d:
        ma, bc = mod.don(repo=d, im=True)
        return ma == 2 and bool(bc['loi'])


def ca_10_nong_khong_chan_phan_khac(mod):
    """File NÓNG không được che luôn việc dọn phần NGUỘI khác trong CÙNG repo."""
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        _ghi(d, 'scripts/moi.py', 'x = 1\n', cu_phut=0)
        _ghi(d, 'scripts/cu.py', 'y = 2\n', cu_phut=200)
        ma, bc = mod.don(repo=d, im=True)
        out = ''
        if bc['da_commit']:
            _, out, _ = _chay('git', 'log', '-1', '--name-only', '--format=', cwd=d)
        return (ma == 4 and bc['da_commit'] and 'scripts/cu.py' in out
                and 'scripts/moi.py' not in out)


def ca_11_bien_nguong(mod):
    with tempfile.TemporaryDirectory() as d:
        _git_init(d)
        _ghi(d, 'README.md', 'x')
        _commit_ban_dau(d, ['README.md'])
        _ghi(d, 'scripts/gan.py', 'x = 1\n', cu_phut=89)
        _ghi(d, 'scripts/xa.py', 'y = 2\n', cu_phut=91)
        ma, bc = mod.don(repo=d, im=True)
        return 'scripts/gan.py' in bc['nong'] and 'scripts/xa.py' in bc['ma']


CAC_CA = [
    ('ca_01_repo_sach', ca_01_repo_sach),
    ('ca_02_nong_khong_commit', ca_02_nong_khong_commit),
    ('ca_03_ma_nguon_nguoi_commit', ca_03_ma_nguon_nguoi_commit),
    ('ca_04_can_nguoi_khong_commit', ca_04_can_nguoi_khong_commit),
    ('ca_05_sinh_lay_ban_remote', ca_05_sinh_lay_ban_remote),
    ('ca_06_untracked_scripts_committed', ca_06_untracked_scripts_committed),
    ('ca_07_la_khong_commit', ca_07_la_khong_commit),
    ('ca_08_message_khong_trung_gate', ca_08_message_khong_trung_gate),
    ('ca_09_khong_phai_git', ca_09_khong_phai_git),
    ('ca_10_nong_khong_chan_phan_khac', ca_10_nong_khong_chan_phan_khac),
    ('ca_11_bien_nguong', ca_11_bien_nguong),
]


def chay_bo_ca(mod, chi=None):
    """Chạy toàn bộ (hoặc `chi` một tập tên ca), trả {ten: bool}."""
    kq = {}
    for ten, hs in CAC_CA:
        if chi is not None and ten not in chi:
            continue
        try:
            kq[ten] = bool(hs(mod))
        except Exception as e:  # noqa: BLE001
            kq[ten] = False
            kq[ten + '__loi'] = str(e)
    return kq


# --------------------------------------------------------- bản hỏng canh ---

BAN_HONG = {
    'bo_chan_nong': {
        'mo_ta': 'Bỏ điều kiện NÓNG — mọi file đều bị coi là đã nguội',
        'tim': 'if tuoi_phut(repo, duong) < nguoi_phut:',
        'thay': 'if False:',
        'ca_do': {'ca_02_nong_khong_commit', 'ca_10_nong_khong_chan_phan_khac',
                  'ca_11_bien_nguong'},
    },
    'bo_can_nguoi': {
        'mo_ta': 'Bỏ nhóm CẦN NGƯỜI — index.html bị coi như mã nguồn thường',
        'tim': ("CAN_NGUOI = ('index.html', 'sw.js', 'manifest.json', "
                "'data/analyses.json',\n             'whats-new.json')"),
        'thay': 'CAN_NGUOI = ()',
        'ca_do': {'ca_04_can_nguoi_khong_commit'},
    },
    'message_trung_gate': {
        'mo_ta': 'Message commit khớp tiền tố cổng notify-email.yml',
        'tim': "NHAN_COMMIT = 'Don ton du truoc phien quet'",
        'thay': "NHAN_COMMIT = 'Cap nhat ban tin (don rac)'",
        'ca_do': {'ca_08_message_khong_trung_gate'},
    },
    'la_thanh_ma': {
        'mo_ta': 'File .py MỚI ở gốc repo bị coi là mã nguồn rồi tự commit',
        'tim': ("        if nhom == 'ma' and untracked and os.sep not in "
                "_nfc(duong):\n"
                "            # File mới ở GỐC repo: không đủ căn cứ để tự "
                "thêm vào repo public.\n"
                "            nhom = 'la'"),
        'thay': '        pass',
        'ca_do': {'ca_07_la_khong_commit'},
    },
}


def _dung_ban_hong(khoa):
    with open(SRC, encoding='utf-8') as f:
        goc = f.read()
    info = BAN_HONG[khoa]
    if goc.count(info['tim']) != 1:
        raise RuntimeError(
            'chuỗi neo của %s khớp %d chỗ (phải đúng 1)' % (khoa, goc.count(info['tim'])))
    hong = goc.replace(info['tim'], info['thay'])
    sha = hashlib.sha1(hong.encode('utf-8')).hexdigest()[:8]
    ten_file = '_thu-hong-%d-%s-%s.py' % (os.getpid(), sha, khoa)
    duong = os.path.join(REPO, 'scripts', ten_file)
    with open(duong, 'w', encoding='utf-8') as f:
        f.write(hong)
    return duong


def tu_kiem():
    print('=== --tu-kiem: chạy bộ ca trên bản ĐÚNG trước ===')
    mod_dung = nap_module()
    kq_dung = chay_bo_ca(mod_dung)
    hong_o_ban_dung = [t for t, v in kq_dung.items() if not t.endswith('__loi') and not v]
    if hong_o_ban_dung:
        print('✗ TRƯỢT ngay trên bản ĐÚNG: %s — dừng, không tự-kiểm được nữa' %
              hong_o_ban_dung)
        return 1
    print('  %d/%d ca đạt trên bản đúng' % (len(kq_dung), len(CAC_CA)))

    tong_bat = 0
    for khoa, info in BAN_HONG.items():
        duong = None
        try:
            duong = _dung_ban_hong(khoa)
            mod_hong = nap_module(duong, ten='don_ton_du_hong_' + khoa)
        except Exception as e:  # noqa: BLE001
            print('  ⚠ %s: bản hỏng không NẠP được (%s) — coi là bắt được '
                  '(fail-closed)' % (khoa, e))
            tong_bat += 1
            if duong and os.path.exists(duong):
                os.unlink(duong)
            continue
        try:
            kq = chay_bo_ca(mod_hong, chi=info['ca_do'])
            do = [t for t in info['ca_do'] if not kq.get(t)]
            if len(do) == len(info['ca_do']):
                print('  ✔ %-24s bắt được (%s đỏ)' % (khoa, ', '.join(sorted(do))))
                tong_bat += 1
            else:
                thieu = info['ca_do'] - set(do)
                print('  ✗ %-24s KHÔNG bắt được — ca %s vẫn xanh trên bản hỏng'
                      % (khoa, sorted(thieu)))
        finally:
            if os.path.exists(duong):
                os.unlink(duong)

    print('=== Tổng: %d/%d bản hỏng bị bắt ===' % (tong_bat, len(BAN_HONG)))
    return 0 if tong_bat == len(BAN_HONG) else 1


def main():
    if '--tu-kiem' in sys.argv:
        return tu_kiem()
    mod = nap_module()
    kq = chay_bo_ca(mod)
    dat = sum(1 for t, v in kq.items() if not t.endswith('__loi') and v)
    for ten, _hs in CAC_CA:
        trang_thai = '✓' if kq.get(ten) else '✗'
        print('%s %s' % (trang_thai, ten))
        if ten + '__loi' in kq:
            print('    lỗi: %s' % kq[ten + '__loi'])
    print('--- %d/%d ca đạt ---' % (dat, len(CAC_CA)))
    return 0 if dat == len(CAC_CA) else 1


if __name__ == '__main__':
    sys.exit(main())
