create table if not exists public.backtest
(
    id              serial
        primary key,
    user_id         uuid
        references "auth"."users"                                not null,
    days            integer                                      not null,
    ticker          varchar(250)                                 not null,
    buy_mapping     json                                         not null,
    sell_mapping    json                                         not null,
    buy_expression  varchar                                      not null,
    sell_expression varchar                                      not null,
    status          varchar(20)                                  not null,
    type            varchar(5) default 'Long'::character varying not null,
    strategy_name   varchar(500)                                 not null,
    allocation      integer,
    win             integer                                      not null,
    avg_trade       integer                                      not null,
    return_perc     integer                                      not null,
    trades          integer                                      not null,
    starred         boolean    default false                     not null,
    is_deleted      boolean    default true                      not null
);

create index if not exists ix_backtest_id
    on public.backtest (id);