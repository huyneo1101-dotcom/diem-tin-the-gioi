# HAI LỖI CÂM CỦA `probe_sources.py` — xẻ khỏi `CLAUDE.md` ngày 18/09/2026

Xẻ ra vì `CLAUDE.md` chạm trần chống phình (`khoe.py::file_luat_mang_phinh`), không phải vì hết
hiệu lực. Bản gốc của luật vẫn là dòng trỏ tới đây trong `CLAUDE.md`, mục nguồn `.mil`.

- **Cơ chế gây vấp:** `probe_sources.py` chỉ gọi **curl trần**, mà curl trần bị Akamai cắt theo dấu
  vân tay TLS ⇒ nó chấm `403` ⇒ bảng ghi "403 cả hai nơi" ⇒ `harvest.py` bỏ nguồn. Không lỗi, không
  cảnh báo, và bảng trông như có căn cứ vì đúng là có số đo — số đo của công cụ sai. Cùng lớp với
  luật *"đừng chẩn đoán từ output do chính mình cắt"*: ở đây là output do chính công cụ của mình bóp.
- **Kèm theo, `probe_sources.py` còn có một nhãn CÂM TỪ NGÀY DỰNG:** nhãn `DNS` chỉ khớp khi stderr
  chứa `Could not resolve host`, nhưng script chạy `curl -s` — cờ đó triệt tiêu luôn thông báo lỗi.
  Bằng chứng: bản local 27/07 và bản CI 30/07 đều có **đúng 0 mục `DNS`** trên 287 URL, trong khi zone
  `.mil` thật sự không phân giải được ở local. Tên miền chết bị dồn vào nhãn `LỖI` chung với timeout —
  hai nguyên nhân khác hẳn nhau và chữa theo hai hướng khác nhau. Đã vá thành `-sS`.

**Vì sao đáng giữ:** cả hai đều là lỗi của CÔNG CỤ ĐO, không phải của thứ được đo — và cả hai đều
làm bảng nguồn trông như có căn cứ. Đây là hình dạng hỏng khó thấy nhất: có số đo, có kết luận, chỉ
là số đo sai. Gặp một nguồn bị chấm "chết" thì đo lại bằng đường khác trước khi tin.
