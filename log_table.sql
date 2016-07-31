-- Table: logs

-- DROP TABLE logs;

CREATE TABLE logs
(
  log_id bigserial NOT NULL,
  method character varying(50),
  action character varying(50),
  url text,
  source character varying(50),
  visited_at timestamp without time zone NOT NULL DEFAULT now(),
  processed boolean DEFAULT false,
  domain text,
  serverside_file_type text,
  file_ext text,
  query text,
  path text
)
WITH (
  OIDS=FALSE
);
ALTER TABLE logs
  OWNER TO postgres;
