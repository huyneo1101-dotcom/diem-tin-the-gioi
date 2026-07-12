-- Điểm Tin Thế Giới — thiết lập Supabase cho tính năng tài khoản (bài + khái niệm)
-- Chạy trong Supabase SQL Editor sau khi tạo project.
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

-- Khái niệm đã lưu (explanation do tác vụ hàng ngày điền — tính năng ④)
create table if not exists saved_concepts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  term text not null,
  explanation text,
  created_at timestamptz default now(),
  unique(user_id, term)
);
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
