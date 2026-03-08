import asyncio
import os
import ssl
import json
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(database_url, sslmode='require', connect_timeout=30)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
    return conn

def process_pending_jobs(conn):
    jobs_processed = 0
    while True:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # Atomically claim one queued job
        cur.execute("""
            UPDATE pgqueuer
            SET status = 'picked',
                updated = NOW()
            WHERE id = (
                SELECT id FROM pgqueuer
                WHERE status = 'queued'
                AND execute_after <= NOW()
                ORDER BY priority DESC, created ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING id, entrypoint, payload, headers;
        """)
        job = cur.fetchone()
        if not job:
            cur.close()
            break

        job_id = job['id']
        payload = job['payload']
        headers = job['headers']
        logger.info(f"Processing job {job_id}")

        try:
            # Convert payload bytes to string if needed
            if isinstance(payload, memoryview):
                payload = bytes(payload)
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')

            # Convert headers to JSON string
            if headers is None:
                headers_str = '{}'
            elif isinstance(headers, dict):
                headers_str = json.dumps(headers)
            elif isinstance(headers, (memoryview, bytes)):
                headers_str = bytes(headers).decode('utf-8') if isinstance(headers, memoryview) else headers.decode('utf-8')
            else:
                headers_str = str(headers)

            # Call the process_scan function
            cur.execute("SELECT process_scan(%s::bytea, %s::jsonb)", (payload.encode('utf-8'), headers_str))
            conn.commit()

            # Mark as successful
            cur.execute("DELETE FROM pgqueuer WHERE id = %s", (job_id,))
            conn.commit()

            logger.info(f"Completed job {job_id}")
            jobs_processed += 1

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            conn.rollback()
            cur.execute("""
                UPDATE pgqueuer SET status = 'exception', updated = NOW()
                WHERE id = %s
            """, (job_id,))
            conn.commit()

        cur.close()

    return jobs_processed

def main():
    logger.info("Starting polling worker...")
    consecutive_empty = 0
    
    while True:
        try:
            conn = get_db_connection()
            jobs = process_pending_jobs(conn)
            conn.close()

            if jobs == 0:
                consecutive_empty += 1
                # Back off: 2s normally, up to 10s when idle
                sleep_time = min(2 * consecutive_empty, 10)
                logger.debug(f"No jobs, sleeping {sleep_time}s")
            else:
                consecutive_empty = 0
                sleep_time = 1
                logger.info(f"Processed {jobs} jobs, polling again in {sleep_time}s")

            import time
            time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            import time
            time.sleep(5)

if __name__ == "__main__":
    main()
