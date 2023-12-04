-- SET client_encoding = 'UTF8';

-- IF EXISTS DROP DATABASE "calendar-bot";

-- CREATE DATABASE "calendar-bot";

-- \connect "calendar-bot";

SET client_encoding = 'UTF8';

CREATE TABLE customer (
  customer_id SERIAL PRIMARY KEY,
  telegram_id INT UNIQUE,
  oauth_token VARCHAR(255) UNIQUE,
  email VARCHAR(255),
  name VARCHAR(100),
  surname VARCHAR(100),
  login VARCHAR(100),
  password VARCHAR(100)
);

CREATE TABLE access (
  access_id SERIAL PRIMARY KEY,
  customer_id INT REFERENCES customer (customer_id),
  allowed_customer_id INT REFERENCES customer (customer_id),
  type VARCHAR(20) CHECK (type IN ('no', 'enc', 'full')),
  end_time TIMESTAMP,
  requested BOOLEAN DEFAULT false
);

CREATE TABLE event (
  event_id VARCHAR(100) PRIMARY KEY,
  customer_id INT REFERENCES customer (customer_id),
  event_name VARCHAR(255),
  event_start TIMESTAMP WITH TIME ZONE,
  event_end TIMESTAMP WITH TIME ZONE,
  last_modified TIMESTAMP WITH TIME ZONE
);