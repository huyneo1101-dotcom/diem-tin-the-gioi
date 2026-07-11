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
