create table if not exists public.user_activity_backtest
(
    id              serial
        primary key,
    user_id         uuid
        references "auth"."users" not null,
    days            integer      not null,
    ticker          varchar(250) not null,
    buy_expression  varchar      not null,
    sell_expression varchar      not null,
    buy_mapping     json         not null,
    sell_mapping    json         not null
);


create index if not exists ix_user_activity_backtest_id
    on public.user_activity_backtest (id);
