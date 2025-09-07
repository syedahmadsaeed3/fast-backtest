create table if not exists public.ticker
(
    id            serial
        primary key,
    symbol        varchar(250),
    company_name  varchar,
    logo          varchar,
    option        boolean,
    is_crypto     boolean,
    __ts_vector__ tsvector generated always as (to_tsvector('english'::regconfig,
                                                            (((symbol)::text || ' '::text) || (company_name)::text))) stored
);

create index if not exists ix_ticker_id
    on public.ticker (id);

create index if not exists ix_video___ts_vector__
    on public.ticker using gin (__ts_vector__);
