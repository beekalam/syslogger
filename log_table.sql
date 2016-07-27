
-- DROP TABLE logs;

CREATE TABLE logs
(
  log_id serial NOT NULL,
  method character varying(50),
  action character varying(50),
  url character varying,
  source character varying(50),
  login_time timestamp without time zone NOT NULL DEFAULT now()
)
WITH (
  OIDS=FALSE
);
ALTER TABLE logs
  OWNER TO postgres;

