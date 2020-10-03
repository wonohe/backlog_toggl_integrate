-- Drop table

-- DROP TABLE public.toggl_report;

CREATE TABLE public.toggl_report (
	id serial NOT NULL,
	toggl_id int8 NOT NULL,
	pid int4 NULL,
	tid int4 NULL,
	uid int4 NULL,
	user_name varchar(1000) NULL,
	description text NULL,
	start_time timestamptz NOT NULL,
	end_time timestamptz NOT NULL,
	updated timestamptz NOT NULL,
	dur int4 NOT NULL,
	backlog_issue_key varchar(255) NULL,
	created_at timestamptz NOT NULL DEFAULT now(),
	CONSTRAINT toggl_report_toggl_id_key UNIQUE (toggl_id)
);

-- Permissions

ALTER TABLE public.toggl_report OWNER TO postgres;
GRANT ALL ON TABLE public.toggl_report TO postgres;

-- Index

CREATE INDEX toggl_report_backlog_issue_key_idx ON public.toggl_report USING btree (backlog_issue_key);
CREATE INDEX toggl_report_start_time_idx ON public.toggl_report USING btree (start_time);
CREATE UNIQUE INDEX toggl_report_toggl_id_idx ON public.toggl_report USING btree (toggl_id);

