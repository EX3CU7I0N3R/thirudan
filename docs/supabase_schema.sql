create table if not exists public.scrape_cache (
  student_id text primary key,
  session_hash text not null unique,
  refreshed_at bigint not null,
  schedule_note text not null default '',
  "user" text,
  attendance text,
  marks text,
  courses text,
  timetable jsonb
);

create index if not exists scrape_cache_session_hash_idx
  on public.scrape_cache (session_hash);

create table if not exists public.academic_calendar (
  id text primary key,
  date text not null default '',
  month text not null,
  day text not null default '',
  "order" text not null default '',
  event text not null default '',
  created_at bigint not null
);

create index if not exists academic_calendar_month_idx
  on public.academic_calendar (month);
