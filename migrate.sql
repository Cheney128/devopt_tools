ALTER TABLE devices ADD COLUMN latency INT NULL;
ALTER TABLE devices ADD COLUMN last_latency_check DATETIME NULL;
ALTER TABLE devices ADD COLUMN latency_check_enabled TINYINT(1) NOT NULL DEFAULT 1;
