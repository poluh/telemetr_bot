DROP table if exists users cascade;
DROP table if exists devices cascade;
DROP table if exists sensors cascade;
DROP table if exists scenarios cascade;
DROP TABLE IF EXISTS controllers CASCADE;

CREATE TABLE users
(
    id        SERIAL PRIMARY KEY,
    user_id   INTEGER UNIQUE,
    full_name VARCHAR(255),
    city      VARCHAR(100)
);

CREATE TABLE controllers
(
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER REFERENCES users (user_id),
    type          VARCHAR(50),
    serial_number VARCHAR(100)
);

CREATE TABLE devices
(
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER REFERENCES users (user_id),
    type          VARCHAR(50),
    serial_number VARCHAR(100)
);

CREATE TABLE sensors
(
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER REFERENCES users (user_id),
    device_id     INTEGER REFERENCES devices (id),
    type          VARCHAR(50),
    serial_number BIGINT,
    status        VARCHAR(50),
    value         FLOAT
);

CREATE TABLE scenarios
(
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users (user_id),
    name       VARCHAR(255),
    conditions TEXT,
    type       VARCHAR(50),
    actions    TEXT
);

select * from scenarios;