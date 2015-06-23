create_id_table = "CREATE TABLE IF NOT EXISTS {0} (username TEXT, probe_id INT4, first_start TEXT, location TEXT)"
create_raw_table = '''CREATE TABLE IF NOT EXISTS {0} (
            uri text,
            request_ts datetime,
            content_type text,
            httpid int8,
            session_start datetime,
            session_url text,
            local_ip text,
            local_port int,
            remote_ip text,
            remote_port int,
            body_bytes int,
            syn_time int,
            first_bytes_rcv datetime,
            app_rtt int,
            end_time datetime,
            rcv_time int,
            full_load_time int,
            cpu_percent int,
            mem_percent int,
            probe_id int8,
            sid int,
            unique(sid, httpid)
        )
        '''
create_active_table = '''CREATE TABLE IF NOT EXISTS {0} (
            ip_dest text,
            sid int,
            session_url text,
            remote_ip text,
            ping blob,
            trace blob,
            unique(sid, remote_ip)
            )
        '''
create_aggregate_summary = '''CREATE TABLE IF NOT EXISTS {0} (
            sid INT unique,
            session_url TEXT,
            session_start datetime,
            server_ip TEXT,
            full_load_time INT,
            page_dim INT,
            cpu_percent INT,
            mem_percent INT,
            is_sent int
        ) '''
create_aggregate_details = '''CREATE TABLE IF NOT EXISTS {0} (
            sid INT,
            base_url TEXT,
            ip TEXT,
            netw_bytes INT,
            nr_obj INT,
            sum_syn INT,
            sum_http INT,
            sum_rcv_time INT,
            unique(sid, base_url, ip)
        ) '''
create_local_diagnosis = '''CREATE TABLE IF NOT EXISTS {0} (
            url TEXT unique,
            flt INT,
            http INT,
            tcp INT,
            dim INT,
            t1 real,
            d1 real,
            d2 real,
            dh real,
            count int
        )'''
create_local_diagnosis_result = '''CREATE TABLE IF NOT EXISTS {0} (
            sid INT,
            url TEXT,
            when_browsed datetime,
            diagnosis TEXT,
            unique(sid, url)
        )'''
