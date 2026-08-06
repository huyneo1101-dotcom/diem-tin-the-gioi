#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐỘ GẦN CỦA NGUỒN — tra bảng + cổng chặn tin kênh tuyên truyền đứng một mình.

MỘT hàm kiểm tra duy nhất cho cả repo. Nơi khác GỌI, cấm chép logic sang: hai bản luật song
song thì bản ít người sửa sẽ mục, mà lệch âm thầm (mục 14 + mục 17 CLAUDE.md toàn cục).

VÌ SAO CÓ FILE NÀY (06/08/2026). `CLAUDE.md` mục "THANG XÁC MINH" đã có sẵn dòng luật:
*"Truyền thông nhà nước độc tài (Xinhua, TASS, Global Times, KCNA…): chỉ dùng cho phát ngôn
CỦA CHÍNH HỌ; sự kiện tranh chấp/thương vong phải có nguồn thứ hai."* Luật đúng và đã tồn
tại — thứ thiếu là **chỗ tra**: nó gọi tên LOẠI nguồn chứ không gọi tên HÃNG, nên mỗi lượt
quét lại phải xếp loại bằng phán đoán ("Zona Militar thuộc loại nào?", "The Epoch Times thì
sao?"), phán đoán đó không được ghi lại, và không cổng nào đo được nó đã xảy ra hay chưa.
Bảng `data/do-gan-nguon.json` (109 hãng, đồng bộ từ app Rèn Phân Tích) biến phán đoán ấy
thành một phép tra, và file này biến dòng luật ấy thành một cổng chặn.

Đo trên dữ liệu đang sống ngày 06/08/2026: bảng khớp 61% số tin (388/638), và độ gần 4 xuất
hiện 07 lần — Global Times ×2, The Epoch Times ×1 (tin thế giới) cộng 04 tài khoản mạng xã
hội. Tức cổng này có việc thật để làm, không phải cổng dựng cho đẹp.

HAI ĐƯỜNG QUA CỔNG, cố ý là hai chứ không phải một:
  (1) `nguonThuHai` — URL thứ hai, phải khác TÊN MIỀN GỐC với `sourceUrl`;
  (2) `phatNgonCuaChinhHo: true` — tin là phát ngôn/hành động của chính bên đó.
Đường (2) bắt buộc phải có, nếu không cổng sẽ CHẶN OAN đúng loại tin mà luật gốc cho phép:
đo thật trên 03 tin độ gần 4 đang sống, 02 tin là Trung Quốc công bố hành động của chính
Trung Quốc (Global Times) — hợp lệ theo luật gốc — chỉ 01 tin (The Epoch Times viết về cam
kết của Tổng thống Philippines) mới là ca luật gốc nhắm tới. Cổng nào ở luồng bình thường
luôn phải mở cờ mới qua được là cổng chết, và cờ mở quen tay thì mọi cổng còn lại mất giá
theo. Đường (2) không phải lỗ hổng: nó là một lời khai được GHI vào tin, tức đúng thứ trước
giờ vẫn xảy ra trong đầu người quét mà không để lại dấu vết nào.

PHẠM VI CỐ Ý HẸP — chỉ chặn các luồng trình bày như tin đã thẩm định (`worldNews`,
`usNews`, `baomoiNews`, item của sự kiện/tập trận). `xNews` chỉ CẢNH BÁO, không chặn: luồng
đó được trình bày trên web đúng như bản chất của nó — tiếng nói trên mạng xã hội chưa thẩm
định — nên bắt nó có nguồn thứ hai là đổi bản chất của luồng, không phải vá một lỗ.
"""
import json
import pathlib
import unicodedata
import urllib.parse

REPO = pathlib.Path(__file__).resolve().parent.parent
BANG_PATH = REPO / "data" / "do-gan-nguon.json"

DO_GAN_TUYEN_TRUYEN = 4

# Đuôi tên miền hai bậc: `.co.uk` không phải tên miền gốc, `bbc.co.uk` mới là.
DUOI_HAI_BAC = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "co.jp", "or.jp", "ne.jp", "go.jp",
    "com.au", "net.au", "org.au", "gov.au", "com.cn", "gov.cn", "org.cn",
    "com.vn", "gov.vn", "org.vn", "edu.vn", "co.kr", "or.kr", "go.kr",
    "com.br", "com.sg", "com.ph", "com.tw", "co.in", "co.nz", "com.my",
}

_cache = {}


def chuan_ten(ten: str) -> str:
    """Khoá tra cứu — PHẢI trùng khuôn với `dong_bo_do_gan.chuan_ten`.

    NFC trước mọi phép so khớp tiếng Việt: tên do Huy/Finder gõ ra dạng NFD, chuỗi trong
    JSON do Claude ghi là NFC — nhìn y hệt, khác byte, so khớp trượt mà không báo gì.
    """
    t = unicodedata.normalize("NFC", ten or "")
    return " ".join(t.split()).lower()


def nap(path=None) -> dict:
    """Trả {khoá chuẩn hoá: {'ten','do_gan','kenh','luu_y'}}. Có nhớ tạm theo đường dẫn."""
    p = pathlib.Path(path) if path else BANG_PATH
    khoa_cache = str(p)
    if khoa_cache in _cache:
        return _cache[khoa_cache]
    # Bảng vắng mặt => ném lỗi, CỐ Ý không trả bảng rỗng cho êm. Bảng rỗng nghĩa là mọi
    # nguồn đều "không biết" nên cổng không chặn gì — hỏng câm đúng nghĩa: nạp tin vẫn
    # chạy trơn, bảng vẫn xanh, chỉ là không còn ai canh.
    goc = json.loads(p.read_text(encoding="utf-8"))
    bang = {}
    for h in goc["hang"]:
        bang[chuan_ten(h["ten"])] = h
    _cache[khoa_cache] = bang
    return bang


def tra(ten: str, bang=None):
    """Trả bản ghi của hãng, hoặc None nếu chưa có trong bảng."""
    return (bang if bang is not None else nap()).get(chuan_ten(ten))


def ten_mien_goc(url: str) -> str:
    """`https://www.globaltimes.cn/page/x` -> `globaltimes.cn`. Chuỗi rỗng nếu không đọc được."""
    try:
        net = urllib.parse.urlparse(url).netloc.lower()
    except ValueError:
        return ""
    net = net.split("@")[-1].split(":")[0]
    if net.startswith("www."):
        net = net[4:]
    phan = [x for x in net.split(".") if x]
    if len(phan) < 2:
        return net
    hai = ".".join(phan[-2:])
    if hai in DUOI_HAI_BAC and len(phan) >= 3:
        return ".".join(phan[-3:])
    return hai


def _co_nguon_thu_hai(item: dict) -> tuple:
    """Trả (đạt, lý do trượt). Nguồn thứ hai phải là http VÀ khác tên miền gốc."""
    u2 = (item.get("nguonThuHai") or "").strip()
    if not u2:
        return False, "không khai `nguonThuHai`"
    if not u2.startswith("http"):
        return False, f"`nguonThuHai` không phải URL: {u2!r}"
    d1, d2 = ten_mien_goc(item.get("sourceUrl", "")), ten_mien_goc(u2)
    if not d2:
        return False, f"`nguonThuHai` không đọc được tên miền: {u2!r}"
    if d1 and d1 == d2:
        # Cùng tên miền thì không phải nguồn thứ hai, chỉ là bài thứ hai của cùng một bên.
        return False, f"`nguonThuHai` cùng tên miền với sourceUrl ({d1}) — không độc lập"
    return True, ""


def kiem_mot_item(item: dict, ctx: str, bang=None, chan=True) -> list:
    """Gắn nhãn `doGan` vào item và trả danh sách cảnh báo.

    Ném ValueError khi `chan=True` và item độ gần 4 không đi được đường nào trong hai đường.
    Nguồn chưa có trong bảng thì KHÔNG chặn — cổng chỉ biết cái nó biết; chặn thứ chưa xếp
    loại là chặn oan hàng loạt (đo 06/08: 39% số tin đang sống chưa có tên trong bảng).
    """
    canh_bao = []
    h = tra(item.get("sourceName") or item.get("handle") or "", bang)
    if h is None:
        return canh_bao
    item["doGan"] = h["do_gan"]
    if h["do_gan"] != DO_GAN_TUYEN_TRUYEN:
        return canh_bao

    if item.get("phatNgonCuaChinhHo") is True:
        canh_bao.append(
            f"{ctx} độ gần 4 ({h['ten']}) — khai là phát ngôn của chính họ, cho qua. "
            f"Lưu ý: {h['luu_y']}")
        return canh_bao

    dat, vi_sao = _co_nguon_thu_hai(item)
    if dat:
        canh_bao.append(f"{ctx} độ gần 4 ({h['ten']}) — có nguồn thứ hai độc lập, cho qua.")
        return canh_bao

    thong_diep = (
        f"{ctx} nguồn {h['ten']!r} thuộc ĐỘ GẦN 4 (kênh tuyên truyền) mà {vi_sao}.\n"
        f"      Lưu ý về nguồn: {h['luu_y']}\n"
        f"      Muốn nạp thì chọn MỘT trong hai đường:\n"
        f"        (1) thêm \"nguonThuHai\": \"<url của một hãng khác tên miền>\" — dùng khi tin "
        f"là sự kiện tranh chấp/thương vong hoặc nói về bên thứ ba;\n"
        f"        (2) thêm \"phatNgonCuaChinhHo\": true — dùng khi tin là phát ngôn hoặc hành "
        f"động do CHÍNH bên đó công bố (vd Trung Quốc công bố tập trận của Trung Quốc).\n"
        f"      Không thuộc ca nào trong hai ca đó thì BỎ tin."
    )
    if chan:
        raise ValueError(thong_diep)
    canh_bao.append("[CẢNH BÁO] " + thong_diep)
    return canh_bao


def kiem_lo(new_items: dict, bo_cong: str = "") -> list:
    """Chạy cổng trên cả lô. Trả danh sách dòng cần in ra.

    `bo_cong` là lý do mở cổng (cờ `--bo-cong-do-gan="..."` của add_news.py). Có lý do thì
    hạ cổng xuống mức cảnh báo VÀ in một dòng ghi vết — cờ mở mà không để lại dấu thì lần
    sau không ai biết bản tin đó đã đi qua bằng cửa nào.
    """
    try:
        bang = nap()
    except OSError as e:
        # Bảng mất thì KÊU, không im: mất bảng là mất cổng, mà mất cổng trong im lặng thì
        # bảng kết quả vẫn báo đạt (lỗi phải trả về phía KÊU — mục 17).
        raise ValueError(
            f"không đọc được bảng độ gần {BANG_PATH}: {e}\n"
            f"      Dựng lại bằng `python3 scripts/dong_bo_do_gan.py --sinh`.") from e

    ra = []
    if bo_cong:
        ra.append(f"  [MỞ CỔNG ĐỘ GẦN] lý do: {bo_cong} — cổng hạ xuống mức cảnh báo.")

    for label in ("worldNews", "usNews", "baomoiNews"):
        for i, it in enumerate(new_items.get(label, [])):
            ra += kiem_mot_item(it, f"{label}[{i}]", bang, chan=not bo_cong)

    for key in ("exerciseUpdates", "dipEventUpdates", "newDipEvents", "newExercises"):
        for e_idx, ev in enumerate(new_items.get(key, [])):
            for j, it in enumerate(ev.get("items", [])):
                ra += kiem_mot_item(it, f"{key}[{e_idx}].items[{j}]", bang, chan=not bo_cong)

    # xNews: gắn nhãn + cảnh báo, KHÔNG chặn (xem docstring đầu file).
    for i, it in enumerate(new_items.get("xNews", [])):
        ra += kiem_mot_item(it, f"xNews[{i}]", bang, chan=False)

    return ra
