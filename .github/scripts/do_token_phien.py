#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đo mức tiêu thụ token của phiên `claude -p` vừa chạy trên máy GitHub.

VÌ SAO CẦN (đo thật 10/08/2026):
  Phiên quét chạy bằng `CLAUDE_CODE_OAUTH_TOKEN`, tức ăn CÙNG gói Claude của Huy như
  mọi phiên trên máy Mac, nhưng bản ghi phiên nằm trên máy GitHub rồi biến mất cùng
  máy đó. Công cụ `do-token.py` ở nhà chỉ cộng được bản ghi local nên phần này bằng 0
  trong mọi bảng, trong khi job thật chạy 53,6 phút với --max-turns 700.
  Không đo được khoản này thì mọi ngân sách cho routine đêm đều tính thiếu đúng phần
  cạnh tranh trực tiếp với mốc quét tin 04:00.

⛔ CHỈ IN CON SỐ. Repo này CÔNG KHAI, và tệp đính kèm của job công khai thì ai đăng
  nhập cũng tải được. Vì thế:
   - KHÔNG đẩy bản ghi phiên lên làm tệp đính kèm;
   - KHÔNG in nội dung tin nhắn, tên file, đường dẫn hay bất cứ mẩu văn bản nào bóc
     từ bản ghi — chỉ in tổng token, số lượt và số phiên.
  Bộ test `tests/test-do-token-phien.py` có ca canh đúng điều này.

⚠ KHÔNG ĐƯỢC LÀM GÃY JOB. Bước này chạy sau khi bản tin đã quét xong; nó chỉ đọc.
  Mọi lỗi đều nuốt và trả mã 0 — nhưng phải IN RÕ "KHÔNG ĐO ĐƯỢC" kèm lý do, chứ
  tuyệt đối không in "0 token" như thể đã đo và không có gì.

Dùng:
  python3 .github/scripts/do_token_phien.py
  python3 .github/scripts/do_token_phien.py --goc <thư mục projects>
"""
import json
import os
import sys

# Cùng bộ trọng số với `~/Claude/HeThong/do-token.py` để hai bên so được với nhau:
# input×1 + cache_write×1,25 + cache_read×0,1 + output×5. Đây là thước so sánh, không
# phải tiền. Cộng token trần thì cache_read (rẻ nhất, đông nhất) sẽ át hết phần còn lại.
TRONG_SO = {'in': 1.0, 'cc': 1.25, 'cr': 0.1, 'out': 5.0}


def goc_mac_dinh():
    return os.path.join(os.path.expanduser('~'), '.claude', 'projects')


def tim_ban_ghi(goc):
    """Mọi file .jsonl dưới thư mục projects. Trả danh sách đường dẫn."""
    out = []
    for thu_muc, _, files in os.walk(goc):
        for f in files:
            if f.endswith('.jsonl'):
                out.append(os.path.join(thu_muc, f))
    return sorted(out)


def cong(duong_dan):
    """Cộng usage của một danh sách file. Trả (đếm, số phiên có số).

    Dòng không có usage bị bỏ — đó là dòng người dùng, dòng kết quả công cụ, dòng hệ
    thống. Chỉ dòng trả lời của mô hình mới mang usage."""
    c = {'in': 0, 'cc': 0, 'cr': 0, 'out': 0, 'luot': 0}
    phien = 0
    for p in duong_dan:
        co = False
        try:
            f = open(p, encoding='utf-8')
        except OSError:
            continue
        with f:
            for line in f:
                if '"usage"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                u = ((d.get('message') or {}).get('usage')) or {}
                if not u:
                    continue
                c['in'] += u.get('input_tokens', 0) or 0
                c['cc'] += u.get('cache_creation_input_tokens', 0) or 0
                c['cr'] += u.get('cache_read_input_tokens', 0) or 0
                c['out'] += u.get('output_tokens', 0) or 0
                c['luot'] += 1
                co = True
        if co:
            phien += 1
    return c, phien


def quy_doi(c):
    return (c['in'] * TRONG_SO['in'] + c['cc'] * TRONG_SO['cc']
            + c['cr'] * TRONG_SO['cr'] + c['out'] * TRONG_SO['out'])


def bao_cao(goc):
    """Trả chuỗi báo cáo. Chỉ số, không một mẩu nội dung nào."""
    if not os.path.isdir(goc):
        return ('KHÔNG ĐO ĐƯỢC — không có thư mục bản ghi phiên (%s).\n'
                'Đây là lời thú nhận, KHÔNG phải "phiên này tiêu 0 token".' % goc)
    dd = tim_ban_ghi(goc)
    if not dd:
        return ('KHÔNG ĐO ĐƯỢC — thư mục bản ghi phiên rỗng (%s).\n'
                'Đây là lời thú nhận, KHÔNG phải "phiên này tiêu 0 token".' % goc)
    c, phien = cong(dd)
    if c['luot'] == 0:
        return ('KHÔNG ĐO ĐƯỢC — có %d file bản ghi nhưng không dòng nào mang số liệu '
                'token.\nĐây là lời thú nhận, KHÔNG phải "phiên này tiêu 0 token".'
                % len(dd))
    q = quy_doi(c)
    return '\n'.join([
        'MỨC TIÊU THỤ CỦA PHIÊN QUÉT TRÊN MÁY GITHUB',
        '  quy đổi   : %.1f triệu  (input×1 + cache_write×1,25 + cache_read×0,1 + output×5)' % (q / 1e6),
        '  input     : %d' % c['in'],
        '  cache ghi : %d' % c['cc'],
        '  cache đọc : %d' % c['cr'],
        '  output    : %d' % c['out'],
        '  số lượt   : %d' % c['luot'],
        '  số phiên  : %d' % phien,
        'JSON %s' % json.dumps({'quy_doi': round(q), 'in': c['in'], 'cc': c['cc'],
                                'cr': c['cr'], 'out': c['out'], 'luot': c['luot'],
                                'phien': phien}, ensure_ascii=False),
    ])


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    goc = goc_mac_dinh()
    if '--goc' in argv:
        goc = argv[argv.index('--goc') + 1]
    try:
        bc = bao_cao(goc)
    except Exception as e:                      # đọc file mà hỏng cũng không được làm gãy job
        bc = 'KHÔNG ĐO ĐƯỢC — %s: %s' % (type(e).__name__, e)
    print(bc)
    # Đưa lên bảng tóm tắt của job cho dễ đọc. Hỏng thì thôi, không kêu.
    tt = os.environ.get('GITHUB_STEP_SUMMARY')
    if tt:
        try:
            with open(tt, 'a', encoding='utf-8') as f:
                f.write('\n```\n' + bc + '\n```\n')
        except OSError:
            pass
    return 0                                    # LUÔN 0 — bước đo không được làm gãy bản tin


if __name__ == '__main__':
    sys.exit(main())
