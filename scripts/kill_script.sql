-- Kill all IDLE connections (safe - won't kill active queries)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'dp-sigcom'  -- Your database name
  AND state = 'idle'
  AND pid != pg_backend_pid();  -- Don't kill your own connection

-- To see all current connections first:
-- SELECT pid, usename, application_name, client_addr, state, state_change, query
-- FROM pg_stat_activity
-- WHERE datname = 'dp-sigcom'
-- ORDER BY state_change DESC;
