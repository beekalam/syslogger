-- Database: weblog

-- DROP DATABASE weblog;

CREATE DATABASE weblog
  WITH OWNER = postgres
       ENCODING = 'UTF8'
       TABLESPACE = pg_default
       LC_COLLATE = 'en_US.UTF-8'
       LC_CTYPE = 'en_US.UTF-8'
       CONNECTION LIMIT = -1;

-- Table: weblogs

-- DROP TABLE weblogs;

CREATE TABLE weblogs
(
  weblog_id serial NOT NULL,
  username text,
  url text,
  visited_at timestamp without time zone DEFAULT now(),
  ip text,
  action text,
  domain text,
  serverside_file_type text,
  file_ext text,
  query text,
  path text,
  method text,
  nas_ip text,
  params text
)
WITH (
  OIDS=FALSE
);
ALTER TABLE weblogs
  OWNER TO postgres;

-- Table: nases

-- DROP TABLE nases;

CREATE TABLE nases
(
  nas_id serial NOT NULL,
  nasip text,
  username text,
  password text,
  description text,
  CONSTRAINT nases_pkey PRIMARY KEY (nas_id),
  CONSTRAINT nases_nasip_unique UNIQUE (nasip)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE nases
  OWNER TO postgres;


-- Table: exclusion_rules

-- DROP TABLE exclusion_rules;

CREATE TABLE exclusion_rules
(
  exclusion_rules_id serial NOT NULL,
  exclusion_name text NOT NULL,
  exclusion_value text NOT NULL,
  CONSTRAINT exclusion_rules_pkey PRIMARY KEY (exclusion_rules_id),
  CONSTRAINT exclusion_rules_exclusion_name_exclusion_value_key UNIQUE (exclusion_name, exclusion_value)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE exclusion_rules
  OWNER TO postgres;
