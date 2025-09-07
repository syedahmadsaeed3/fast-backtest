create table if not exists public.user_optimizer_profile
(
    id           serial
        primary key,
    user_id      uuid
        references "auth"."users" not null,
    ticker       varchar(25) not null,
    buy_mapping  json        not null,
    sell_mapping json        not null
);

create index if not exists ix_user_optimizer_profile_id
    on public.user_optimizer_profile (id);
