DROP TABLE if EXISTS ripe_results;
CREATE TABLE ripe_results (
	serial_time timestamp,
	capability text,
	measure_number int,
	result text
);
