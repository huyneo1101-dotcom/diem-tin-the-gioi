-- Điểm Tin Thế Giới — thiết lập Supabase cho tính năng tài khoản (bài + khái niệm)
-- Chạy trong Supabase SQL Editor sau khi tạo project.
-- ⚠️ LỊCH SỬ 25/07/2026: kiểm DB thật thì mới lộ ra `saved_items`, `saved_concepts`, `push_subs`
-- CHƯA TỪNG được tạo (chỉ có `votes`) — nên đồng bộ tin đã lưu, khái niệm và push đều hỏng CÂM
-- (code gọi `.then()` không bắt lỗi nên không ai thấy). Đã áp migration
-- `diemtin_saved_items_concepts_push_subs`. File này là bản chuẩn, chạy lại được nhiều lần.
-- Bảo mật: Row Level Security bật để mỗi người dùng chỉ truy cập dữ liệu của chính mình.

-- Bài đã lưu (giữ cả snapshot nội dung để không mất khi tin gốc bị dọn)
create table if not exists saved_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  item_id text not null,        -- id/URL của tin
  kind text,                    -- news / x / analysis / drill / dip
  payload jsonb not null,       -- snapshot tin
  created_at timestamptz default now(),
  unique(user_id, item_id)
);
alter table saved_items enable row level security;
create policy "own_items" on saved_items for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Khái niệm đã lưu. `explanation`/`source` nạp từ mục Tập trận (ex.concepts) hoặc tác vụ
-- hằng ngày; `box`/`due` là tiến độ ôn tập Leitner của tab 📚 Khái niệm (thêm 25/07/2026).
-- `updated_at` dùng để TRỘN 2 chiều: bản nào mới hơn thắng, ôn ở máy này không bị máy khác kéo lùi.
create table if not exists saved_concepts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  term text not null,
  explanation text,
  created_at timestamptz default now(),
  unique(user_id, term)
);
alter table saved_concepts add column if not exists source text;
alter table saved_concepts add column if not exists box smallint default 0 check (box between 0 and 5);
alter table saved_concepts add column if not exists due date;
alter table saved_concepts add column if not exists updated_at timestamptz default now();
alter table saved_concepts enable row level security;
create policy "own_concepts" on saved_concepts for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Thích / không thích (👍/👎) từng bài — mỗi user 1 vote / 1 tin
create table if not exists votes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  item_id text not null,        -- id/URL của tin
  v smallint not null check (v in (-1, 1)),   -- 1 = thích, -1 = không thích
  category text,                -- chuyên mục (để tổng hợp sở thích)
  region text,                  -- khu vực
  source text,                  -- nguồn / handle
  title text,                   -- tiêu đề (tham khảo)
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(user_id, item_id)
);
alter table votes enable row level security;
create policy "own_votes" on votes for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- View TỔNG HỢP công khai (CHỈ số đếm, KHÔNG lộ danh tính) — để session quét đọc bằng
-- publishable key qua REST: GET /rest/v1/vote_stats?select=*  (điều hướng preferences.md).
-- View chạy quyền owner (bỏ qua RLS) nên gộp được toàn bộ user, nhưng chỉ trả count tổng.
create or replace view vote_stats
with (security_invoker = false) as
  select 'category'::text as scope, category as key,
         count(*) filter (where v = 1)  as up,
         count(*) filter (where v = -1) as down,
         coalesce(sum(v), 0)            as net,
         count(*)                       as total
  from votes where category is not null and category <> '' group by category
  union all
  select 'region', region,
         count(*) filter (where v = 1), count(*) filter (where v = -1),
         coalesce(sum(v), 0), count(*)
  from votes where region is not null and region <> '' group by region
  union all
  select 'source', source,
         count(*) filter (where v = 1), count(*) filter (where v = -1),
         coalesce(sum(v), 0), count(*)
  from votes where source is not null and source <> '' group by source;

-- Cho phép đọc view tổng hợp bằng cả anon (publishable) lẫn user đã đăng nhập.
grant select on vote_stats to anon, authenticated;

-- View TIÊU ĐỀ đã vote (để phân tích ĐIỂM CHUNG nội dung thích/không thích) — công khai,
-- gộp theo (dấu vote + tiêu đề), KHÔNG lộ user nào vote. sign=1 thích, sign=-1 không thích.
create or replace view vote_items
with (security_invoker = false) as
  select v as sign, title, category, region, source, count(*) as n
  from votes where title is not null and title <> ''
  group by v, title, category, region, source;
grant select on vote_items to anon, authenticated;


-- =====================================================================
-- THÔNG BÁO ĐẨY (Web Push) — bảng lưu đăng ký thiết bị
-- =====================================================================
-- Mỗi trình duyệt/thiết bị bật thông báo sẽ lưu 1 dòng ở đây. GitHub Action
-- `notify-push.yml` đọc bảng này và gửi push khi bản tin cập nhật.
-- Endpoint KHÔNG thể bị lạm dụng nếu lộ (muốn gửi push hợp lệ phải có khoá
-- riêng VAPID_PRIVATE — chỉ nằm trong GitHub Secret).
create table if not exists push_subs (
  endpoint   text primary key,
  p256dh     text not null,
  auth       text not null,
  created_at timestamptz default now()
);
alter table push_subs enable row level security;

-- Ai cũng được tự đăng ký / cập nhật / xoá đăng ký của thiết bị mình (không cần đăng nhập).
drop policy if exists push_insert on push_subs;
create policy push_insert on push_subs for insert to anon, authenticated with check (true);
drop policy if exists push_update on push_subs;
create policy push_update on push_subs for update to anon, authenticated using (true) with check (true);
drop policy if exists push_delete on push_subs;
create policy push_delete on push_subs for delete to anon, authenticated using (true);
-- Cho phép đọc để Action (dùng publishable key) lấy danh sách thiết bị mà gửi push.
drop policy if exists push_select on push_subs;
create policy push_select on push_subs for select to anon, authenticated using (true);

-- ============================================================================
-- cafe_deleted — danh sách quán cà phê bị XOÁ GLOBAL (áp cho MỌI người dùng).
-- CHỈ user huyneo được ghi (xoá cho tất cả); mọi người (kể cả chưa đăng nhập) ĐỌC
-- danh sách này để lọc bỏ quán khỏi tab Cà phê. User khác vẫn xoá được nhưng chỉ ở
-- máy họ (localStorage), không ghi vào đây.
create table if not exists cafe_deleted (
  cid        text primary key,          -- id quán (name|address, hoặc c:<id> quán tự thêm)
  deleted_by uuid,
  created_at timestamptz default now()
);
alter table cafe_deleted enable row level security;
-- Ai cũng đọc được (để lọc quán bị xoá cho mọi người, kể cả khách chưa đăng nhập).
drop policy if exists cafedel_select on cafe_deleted;
create policy cafedel_select on cafe_deleted for select to anon, authenticated using (true);
-- CHỈ huyneo được ghi (xoá global). Đổi email nếu cần.
drop policy if exists cafedel_insert on cafe_deleted;
create policy cafedel_insert on cafe_deleted for insert to authenticated
  with check ((auth.jwt() ->> 'email') like 'huyneo%');
drop policy if exists cafedel_update on cafe_deleted;
create policy cafedel_update on cafe_deleted for update to authenticated
  using ((auth.jwt() ->> 'email') like 'huyneo%')
  with check ((auth.jwt() ->> 'email') like 'huyneo%');

-- ============================================================================
-- cafe_tags — PHÂN LOẠI quán theo tiêu chí lọc (Làm việc 1 mình / Ngồi bàn / View đẹp /
-- Thú vị / Đẹp-Check-in / 24h / Yên tĩnh). Admin (huyneo) đặt thủ công, GLOBAL cho mọi user
-- (mọi người đọc để lọc; chỉ huyneo ghi). `tags` = jsonb {tag: true/false} (đè auto-detect).
create table if not exists cafe_tags (
  cid        text primary key,
  tags       jsonb not null default '{}'::jsonb,
  updated_by uuid,
  updated_at timestamptz default now()
);
alter table cafe_tags enable row level security;
drop policy if exists cafetags_select on cafe_tags;
create policy cafetags_select on cafe_tags for select to anon, authenticated using (true);
drop policy if exists cafetags_insert on cafe_tags;
create policy cafetags_insert on cafe_tags for insert to authenticated
  with check ((auth.jwt() ->> 'email') like 'huyneo%');
drop policy if exists cafetags_update on cafe_tags;
create policy cafetags_update on cafe_tags for update to authenticated
  using ((auth.jwt() ->> 'email') like 'huyneo%')
  with check ((auth.jwt() ->> 'email') like 'huyneo%');
