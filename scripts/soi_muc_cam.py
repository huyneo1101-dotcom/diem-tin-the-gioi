#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SOI MỤC CÂM — hỏi câu mà ba cổng cũ của Điểm Tin không cổng nào hỏi:
**mục này đáng lẽ có tin, sao lại rỗng?**

    python3 scripts/soi_muc_cam.py --san     # ĐẦU RA: bản tin vừa gửi, mục nào dưới sàn
    python3 scripts/soi_muc_cam.py --feed    # ĐẦU VÀO: feed nào sống mà câm (gọi mạng)
    python3 scripts/soi_muc_cam.py           # cả hai

VÌ SAO CÓ FILE NÀY (05/09/2026). Huy hỏi *"sao điểm tin sáng nay không có tin của Anh vậy?"*.
Truy ra hai lỗi câm trong `harvest.py` (ngày Atom `+01:00` bị cắt cụt · gán cứng chủ đề chỉ
tra theo tên feed) đã sống từ 01/09 tới 05/09, qua ít nhất 08 phiên quét, **không cổng nào
kêu** — người phát hiện là Huy, không phải máy. Ba cổng đang có đều hỏi đúng câu của chúng và
đều trả lời "đạt":
  · `.github/scripts/canary.py`  — bản tin có dựng ra không, web có lệch bản không
  · `scripts/rss_check.py`       — feed còn item không, bài mới nhất cách bao lâu
  · `HeThong/khoe.py`            — routine có chạy không
Cả ba đo QUY TRÌNH và đo SỰ TỒN TẠI. Không cổng nào đo **nội dung đến được tay Huy**, nên một
nguồn sống nhăn răng mà không đóng góp nổi một tin thì im lặng tuyệt đối.

HAI LỚP, CỐ Ý RỜI NHAU — đừng gộp, chúng trả lời hai câu khác hẳn nhau:

  ── LỚP SÀN (đầu ra) ─────────────────────────────────────────────────────────────
  Mỗi mục của bản tin ĐÃ GỬI phải có tối thiểu `SAN_MOI_MUC` tin. Chỉ thị Huy 05/09/2026,
  nguyên văn: *"tối thiểu mỗi mục phải quét cho tao 2 tin"*, *"nhiều tin thì càng tốt"* —
  tức đây là SÀN, không phải chỉ tiêu; vượt sàn bao nhiêu cũng tốt, dưới sàn là hụt.
  Bằng chứng lấy từ `logs/da-gui-email.json` (danh sách URL của chính bản tin đã đi), không
  lấy từ `logs/scan-gaps.json`: sổ gaps do CHÍNH agent quét tự khai, mà lời tự khai thì
  không phải phép đo — cùng lớp lỗi với trường `date` mà cổng `ngay_that.py` đã phải dựng
  riêng để chặn.
  Phép chia mục đi bằng `make_docx.build_sections`, KHÔNG chép lại: mục mà cổng đếm phải là
  đúng mục Huy đọc trong file Word, lệch một nhánh phân loại là cổng đo một bản tin khác.

  ── LỚP NGUỒN (đầu vào) ──────────────────────────────────────────────────────────
  Với mỗi feed trong bảng nguồn của `CLAUDE.md`, đo hai tỷ lệ trên item thô:
     (a) tỷ lệ đọc được NGÀY  — `harvest.parse_date` khác None
     (b) tỷ lệ neo được CHỦ ĐỀ — `harvest.forced_topic` hoặc `topics.match_topic`
  KÊU hai ca, mỗi ca là một hình dạng hỏng đã xảy ra thật:
     · MÙ NGÀY   feed sống (≥ `NGUONG_ITEM` item) mà 0 item đọc được ngày ⇒ đúng hình dạng
                 gov.uk 05/09 (20/20 item ra ngày `?` rồi bị agent loại).
     · CÂM CHỦ ĐỀ  feed mà bảng nguồn KHAI hẳn một chủ đề ở cột cuối, nhưng 0 item neo được
                 chủ đề nào ⇒ nguồn nằm trong bảng, trả 200, mà chưa từng đóng góp một ứng
                 viên nào. Đo lần đầu 05/09/2026 bắt được 05 nguồn chính thức Mỹ đúng hình
                 dạng này (Nhà Trắng · SEC · FTC · USTR · BEA) — đã vá bằng `FORCE_TOPIC_URL`.

⚠️ HAI CHỖ CỐ Ý KHÔNG KÊU, đừng "siết cho chặt":
  · Feed mà bảng nguồn đã ghi rõ **không ghi ngày** (Tuổi Trẻ · Báo Chính phủ · Nikkei Asia —
    đo 05/09: 0/50 item có thẻ ngày, XML không có thẻ nào) không phải lỗi mà là tính chất của
    feed. Muốn tắt tiếng kêu thì phải GHI sự thật ấy vào bảng trong `CLAUDE.md` — nơi người
    đọc nhìn thấy — chứ không phải nhét tên vào một danh sách trắng trong mã.
  · Feed KHÔNG khai chủ đề ở bảng mà hôm nay 0 item neo được là chuyện thường (BBC World,
    Africanews… vốn là nguồn rộng). Kêu vào đó là kêu oan hàng chục dòng mỗi ngày, mà cảnh
    báo kêu oan vài lần là hết ai đọc — lúc đó cổng chết thật.

⚠️ ĐO KHÔNG ĐƯỢC THÌ IM, không kêu. Feed tải hỏng là việc của `kiem_nguon.py`/`rss_check.py`;
sổ chưa có dòng gửi là việc của chính canary. Lớp này chỉ kêu khi ĐO ĐƯỢC và THẤY HỤT.
"""
import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import pathlib
import re
import sys
import unicodedata

sys.dont_write_bytecode = True

REPO = pathlib.Path(os.environ.get("SOIMUC_REPO",
                                   pathlib.Path(__file__).resolve().parent.parent))

# ⛔ SÀN DO HUY CHỐT 05/09/2026 — không phải con số kỹ thuật, đừng tự nới.
SAN_MOI_MUC = 2
# Dưới ngưỡng này thì "0 item đọc được ngày" không nói lên gì: một feed đang có 1-2 bài thì
# hai bài cùng hỏng là chuyện ngẫu nhiên, kêu vào đó là kêu oan.
NGUONG_ITEM = 3
# Tên 05 chủ đề như chúng được VIẾT trong cột cuối của bảng nguồn (CLAUDE.md). Dò bằng chuỗi
# con vì cột đó viết tự do: "3 CNQS Mỹ", "**Nội bộ Mỹ nhóm 1**", "2 Biển Đông".
TEN_CHU_DE_TRONG_BANG = ("Nội bộ Mỹ", "CNQS Mỹ", "Biển Đông", "Mali", "Tập trận")
# Dấu hiệu người viết bảng đã XÁC NHẬN feed không ghi ngày (xem docstring).
DAU_KHONG_NGAY = "không ghi ngày"


def _nfc(s: str) -> str:
    """macOS trả NFD, chuỗi trong mã là NFC — so khớp tiếng Việt phải chuẩn hoá trước."""
    return unicodedata.normalize("NFC", s or "")


def _nap(ten: str, duong: pathlib.Path):
    spec = importlib.util.spec_from_file_location(ten, duong)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_HARVEST = None


def _harvest():
    """Nạp `harvest.py` MỘT LẦN rồi giữ lại.

    Giữ lại không phải để nhanh (dù có nhanh: ba lớp đo đều gọi hàm này) mà để mọi lớp đo
    nhìn CÙNG MỘT bảng `FORCE_TOPIC_URL`. Nạp lại mỗi lượt thì mỗi lớp cầm một bản riêng,
    và ca 16 của bộ test — dựng một khoá gán cứng mồ côi rồi đòi cổng kêu — sẽ sửa bản này
    mà cổng đọc bản kia, tức test xanh trong khi cổng không có răng.
    """
    global _HARVEST
    if _HARVEST is None:
        sys.path.insert(0, str(REPO / "scripts"))
        _HARVEST = _nap("harvest_soi", REPO / "scripts" / "harvest.py")
    return _HARVEST


def _make_docx():
    return _nap("make_docx_soi", REPO / ".github" / "scripts" / "make_docx.py")


# ═══════════════════════════ LỚP NGUỒN: feed sống mà câm ═══════════════════════════
def khai_trong_bang() -> dict:
    """{url feed: {"chu_de": <tên chủ đề khai ở cột cuối|None>, "khong_ngay": bool}}.

    Đọc thẳng bảng trong `CLAUDE.md` — bảng LÀ nguồn chân lý duy nhất về nguồn tin, chép
    danh sách feed sang script mới là dựng bản thứ hai để hai bản tách nhánh (mục 14 của
    CLAUDE.md toàn cục). Ở đây chỉ đọc thêm phần bảng đã có sẵn mà chưa ai đọc: cột cuối.
    """
    text = _nfc((REPO / "CLAUDE.md").read_text(encoding="utf-8"))
    out = {}
    for line in text.split("\n"):
        if not line.startswith("|"):
            continue
        m = re.search(r"https?://\S+", re.sub(r"`[^`]*`", "", line))
        if not m:
            continue
        url = m.group(0).rstrip("|").strip()
        cols = [c.strip() for c in line.strip("|").split("|")]
        cuoi = cols[-1] if len(cols) >= 4 else ""
        chu_de = next((t for t in TEN_CHU_DE_TRONG_BANG if t in cuoi), None)
        out[url] = {"chu_de": chu_de,
                    "khong_ngay": any(DAU_KHONG_NGAY in c for c in cols)}
    return out


def do_mot_feed(name: str, url: str, H, tai=None) -> dict:
    """Một dòng đo cho một feed. Tải hỏng -> `loi` khác rỗng và KHÔNG kêu."""
    lay = tai or (lambda u: H.curl(u, 20))
    try:
        raw = lay(url)
    except Exception as e:                                             # noqa: BLE001
        return {"ten": name, "url": url, "loi": f"{type(e).__name__}: {e}"[:60],
                "n": 0, "n_ngay": 0, "n_neo": 0, "gan_cung": None}
    items = H.items_of(raw)
    gan = H.forced_topic(name, url)
    n_neo = len(items) if gan else sum(1 for ti, _, _, _ in items if H.match_topic(ti, "both"))
    return {"ten": name, "url": url, "loi": "",
            "n": len(items),
            "n_ngay": sum(1 for _, _, pub, _ in items if H.parse_date(pub)),
            "n_neo": n_neo, "gan_cung": gan}


def soi_feed(feeds=None, tai=None, luong: int = 10) -> list:
    H = _harvest()
    feeds = feeds if feeds is not None else H.feeds_from_claude_md()
    with cf.ThreadPoolExecutor(max(1, luong)) as ex:
        return list(ex.map(lambda nu: do_mot_feed(nu[0], nu[1], H, tai), feeds))


def keu_feed(ket_qua: list, khai: dict = None) -> list:
    """Danh sách dòng cảnh báo cho lớp NGUỒN. Rỗng = không có gì để kêu."""
    khai = khai if khai is not None else khai_trong_bang()
    mu, cam = [], []
    for r in ket_qua:
        if r["loi"] or r["n"] < NGUONG_ITEM:
            continue                      # đo không được thì im (xem docstring)
        k = khai.get(r["url"], {})
        if r["n_ngay"] == 0 and not k.get("khong_ngay"):
            mu.append(f"{r['ten']} ({r['n']} item, 0 đọc được ngày)")
        if r["n_neo"] == 0 and k.get("chu_de"):
            cam.append(f"{r['ten']} (khai «{k['chu_de']}», {r['n']} item, 0 neo)")
    ra = []
    if mu:
        ra.append("🕳 FEED MÙ NGÀY — sống mà mọi item ra ngày «?» nên phiên quét loại sạch:\n  · "
                  + "\n  · ".join(mu)
                  + "\nFeed vốn không ghi ngày thì ghi «(feed không ghi ngày)» vào bảng nguồn "
                    "trong CLAUDE.md; còn lại là lỗi đọc ngày trong harvest.parse_date.")
    if cam:
        ra.append("🕳 NGUỒN CÂM CHỦ ĐỀ — bảng khai hẳn chủ đề mà không item nào neo được:\n  · "
                  + "\n  · ".join(cam)
                  + "\nNguồn chuyên một chủ đề thì khai vào harvest.FORCE_TOPIC_URL.")
    return ra


def khai_gan_cung_tuot() -> list:
    """Khoá `FORCE_TOPIC`/`FORCE_TOPIC_URL` nào không còn khớp feed nào trong bảng nguồn.

    Phép đo OFFLINE, và nó bắt đúng kiểu hồi quy mà lớp đo mạng KHÔNG bắt được: gán cứng cho
    gov.uk có tuột hay không thì đằng nào feed ấy cũng còn 8/20 item tự neo bằng từ khoá, tức
    tỷ lệ neo không về 0 và không dòng nào kêu. Sửa URL trong bảng, đổi tên nguồn, hay xoá
    nhầm một dòng `FORCE_TOPIC_URL` đều làm khoá mồ côi — và mồ côi thì im lặng tuyệt đối.
    """
    H = _harvest()
    feeds = H.feeds_from_claude_md()
    ten = {n for n, _ in feeds}
    urls = [u for _, u in feeds]
    mo_coi = [f"FORCE_TOPIC[{k!r}]" for k in H.FORCE_TOPIC if k not in ten]
    mo_coi += [f"FORCE_TOPIC_URL[{k!r}]" for k in H.FORCE_TOPIC_URL
               if not any(k in u for u in urls)]
    if not mo_coi:
        return []
    return ["🕳 GÁN CỨNG CHỦ ĐỀ TUỘT — khoá không còn khớp feed nào trong bảng nguồn:\n  · "
            + "\n  · ".join(mo_coi)
            + "\nNguồn đó nay chỉ neo được bằng từ khoá tiêu đề, tức mất phần lớn item."]


# ═══════════════════════════ LỚP SÀN: mục nào dưới sàn ═══════════════════════════
def dem_muc(urls, data=None) -> list:
    """[(tên mục, số tin)] cho một bản tin, theo ĐÚNG phép chia của make_docx.

    Mục 3 được tách tiếp thành 03 tiểu mục (Anh · Australia · Biển Đông): tiểu mục Anh rỗng
    chính là thứ Huy bắt được sáng 05/09, mà đếm gộp cả mục 3 thì hôm ấy vẫn ra 02 tin và
    cổng vẫn im. Sàn áp cho từng tiểu mục, không áp cho mục gộp.
    """
    md = _make_docx()
    if data is None:
        data = md.extract_data((REPO / "index.html").read_text(encoding="utf-8"))
    tap = set(urls or [])
    # ⛔ KHÔNG một URL nào của bản tin có mặt trong kho ⇒ KHÔNG ĐO ĐƯỢC, trả rỗng để lớp
    # trên im. Đếm tiếp thì mọi mục ra 0 và cổng kêu "cả bản tin rỗng" — kêu oan ở đúng cái
    # ca mà hai lớp canary cũ đang báo đạt, tức phá luôn cả những lớp đang chạy tốt. Ca đã
    # xảy ra thật lúc dựng: `tests/test-canary-ban-tin.py` bơm sổ giả 12 URL không có trong
    # kho, và 03 ca "phải IM" của nó đỏ ngay. Khớp một phần thì VẪN ĐO — sổ luôn có vài URL
    # ngoài file Word (diễn biến tập trận, tin Jay Lâm), đo 03/09/2026: 17/19 khớp.
    if not tap & {it.get("sourceUrl")
                  for k in ("usNews", "worldNews") for it in (data.get(k) or [])} \
            and not tap & {it.get("sourceUrl") for it in md.event_items(data)}:
        return []
    us = [it for it in data.get("usNews", []) or [] if it.get("sourceUrl") in tap]
    world = [it for it in data.get("worldNews", []) or [] if it.get("sourceUrl") in tap]
    events = [it for it in md.event_items(data) if it.get("sourceUrl") in tap]
    ra = []
    for ten, items in md.build_sections(us, world, events):
        if ten != md.MUC_DIA_BAN:
            ra.append((ten, len(items)))
            continue
        for tm in md.THU_TU_TIEU_MUC:
            ra.append((f"{ten} › {tm}",
                       sum(1 for it in items if it.get(md.KHOA_TIEU_MUC) == tm)))
    return ra


def keu_san(dem: list, san: int = SAN_MOI_MUC) -> list:
    """Dòng cảnh báo cho lớp SÀN. Rỗng = mọi mục đủ sàn."""
    hut = [(t, n) for t, n in dem if n < san]
    if not hut:
        return []
    return [f"📉 MỤC DƯỚI SÀN {san} TIN — {len(hut)}/{len(dem)} mục:\n  · "
            + "\n  · ".join(f"{t}: {n} tin" for t, n in hut)]


def urls_ban_tin(buoi: str, ngay: str) -> list | None:
    """URL của bản tin ca `buoi` ngày `ngay` theo sổ đã gửi; None nếu sổ chưa có dòng nào.

    Dùng lại đúng phép quy đổi ngày của canary (`ngay_ca_tu_iso`) — bản tin tối trôi qua nửa
    đêm vẫn thuộc ca tối hôm trước. Hai bên tính khác nhau là cổng kêu oan mà không ai hiểu.
    """
    can = _nap("canary_soi", REPO / ".github" / "scripts" / "canary.py")
    lan = can.da_gui(buoi, ngay)
    return None if not lan else (lan.get("urls") or [])


# ═══════════════════════════════════ CLI ═══════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(description="Soi mục câm của Điểm Tin")
    ap.add_argument("--san", action="store_true", help="chỉ đo lớp SÀN (đầu ra)")
    ap.add_argument("--feed", action="store_true", help="chỉ đo lớp NGUỒN (gọi mạng)")
    ap.add_argument("--buoi", default="toi", choices=["toi", "sang"])
    ap.add_argument("--ngay", default="", help="YYYY-MM-DD; mặc định lấy lần gửi cuối của ca")
    args = ap.parse_args()
    ca_hai = not (args.san or args.feed)
    canh = []

    if args.san or ca_hai:
        ngay = args.ngay
        if not ngay:
            so = json.loads((REPO / "logs" / "da-gui-email.json").read_text(encoding="utf-8"))
            lan = [l for l in so.get("lan_gui", []) if l.get("buoi") == args.buoi]
            ngay = (lan[-1]["luc"][:10] if lan else "")
        urls = urls_ban_tin(args.buoi, ngay) if ngay else None
        if urls is None:
            print(f"[sàn] sổ chưa có dòng ca «{args.buoi}» ngày {ngay or '?'} — bỏ qua")
        else:
            dem = dem_muc(urls)
            print(f"[sàn] bản tin ca «{args.buoi}» {ngay} — {len(urls)} URL trong sổ")
            for ten, n in dem:
                print(f"    {'✓' if n >= SAN_MOI_MUC else '✗'} {ten}: {n} tin")
            canh += keu_san(dem)

    if args.feed or ca_hai:
        kq = soi_feed()
        khai = khai_trong_bang()
        print(f"\n[nguồn] đo {len(kq)} feed  "
              f"(tải được {sum(1 for r in kq if not r['loi'] and r['n'])})")
        for r in sorted(kq, key=lambda r: (r["n_ngay"], r["n_neo"])):
            if r["loi"] or r["n"] < NGUONG_ITEM:
                continue
            k = khai.get(r["url"], {})
            print(f"    {r['ten'][:36]:<38}{r['n']:>5} item{r['n_ngay']:>5} ngày"
                  f"{r['n_neo']:>5} neo  {k.get('chu_de') or ''}")
        canh += keu_feed(kq, khai)
        canh += khai_gan_cung_tuot()

    print()
    if not canh:
        print("✓ không có mục câm.")
        return 0
    for c in canh:
        print(c + "\n")
    return 3


if __name__ == "__main__":
    sys.exit(main())
