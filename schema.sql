-- schema for einkauf-o-matic

-- table of stores with c-base accounts
drop table if exists stores;
create table stores (
    id integer primary key autoincrement,   -- store id
    name string not null,                   -- store name
    url string not null,                    -- fqdn
    minorder integer not null               -- 0 or value in usd
);

-- table of members and passwords
drop table if exists members;
create table members (
    id integer primary key autoincrement,   -- member id
    nick string not null,                   -- member nick name
    hash string not null,                   -- sha1(salt+pass)
    salt string not null,                   -- per user generated salt
    mail string not null                    -- mail for pass recovery
);

-- table of currently running queues
drop table if exists queues;
create table queues (
    id integer primary key autoincrement,   -- queue id
    store integer not null,                 -- store id
    title string not null,                  -- somename for the queue
    deadline string not null                -- timestamp when the queue will be ordered
);

-- table of items in the queues
drop table if exists items;
create table items (
    id integer primary key autoincrement,   -- item id
    queue integer not null,                 -- queue id
    name string not null,                   -- item name
    num integer not null,                   -- item quantity
    price real not null,                    -- single price
    member integer not null,                -- member id
    url string not null                     -- link to item in store
);
