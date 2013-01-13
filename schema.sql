-- schema for einkauf-o-matic

-- This file is part of einkauf-o-matic.
-- 
-- einkauf-o-matic is licensed under Attribution-NonCommercial-ShareAlike 3.0
-- Unported (CC BY-NC-SA 3.0).
-- 
-- <http://creativecommons.org/licenses/by-nc-sa/3.0/>


-- table of stores with c-base accounts
drop table if exists stores;
create table stores (
    id integer primary key autoincrement,   -- store id
    name string not null,                   -- store name
    url string not null,                    -- http://fqdn/
    minorder integer not null,              -- 0 or value in the stores currency
    state string not null,                  -- where comes the stuff from
    currency string not null,               -- currency used by this store
    shipping float not null,                -- shipping to c-base in currency
    comment string                          -- comment about special conditions
);

-- table of currently running queues
drop table if exists queues;
create table queues (
    id integer primary key autoincrement,   -- queue id
    owner integer not null,                 -- member id (ldap) of the creater
    store integer not null,                 -- store id
    title string not null,                  -- somename for the queue
    deadline string not null,               -- timestamp when the queue will be ordered
    status string not null                  -- status of the queue i.e. 'shipping'
);

-- table of items in the queues
drop table if exists items;
create table items (
    id integer primary key autoincrement,   -- item id
    queue integer not null,                 -- queue id
    member integer not null,                -- c-base member id (ldap)
    name string not null,                   -- item name
    num integer not null,                   -- item quantity
    price real not null,                    -- single price
    url string not null,                    -- link to item in store
    paid real not null                      -- amount of money already paid
);
