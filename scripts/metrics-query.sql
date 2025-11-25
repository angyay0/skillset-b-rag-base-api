-- Get conversation stats with user names
SELECT users.name, users.phone_number, cm.mcnt as total_messages, wm.total as warnings FROM public.conversations as conv
INNER JOIN public.users as users ON conv.user_id = users.id
JOIN (SELECT count(id) as mcnt, conversation_id as cid FROM public.messages GROUP BY conversation_id) as cm ON cm.cid = conv.id
JOIN (SELECT count(id) as total, conversation_id FROM public.metrics GROUP BY conversation_id) as wm ON wm.conversation_id = conv.id;

-- Get all metrics with user names
SELECT users.name, metric_type, severity, message as description 
FROM public.metrics
JOIN public.users users on users.id = user_id;

-- Get phone numbers with no associated user
SELECT 
    m.phone_number,
    COUNT(*) AS attempt_count,
    MAX(m.created_at) AS last_attempt,
    MIN(m.created_at) AS first_attempt,
    m.channel
FROM metrics m
LEFT JOIN users u ON m.phone_number = u.phone_number
WHERE u.id IS NULL 
  AND m.phone_number IS NOT NULL
GROUP BY m.phone_number, m.channel
ORDER BY attempt_count DESC;

-- Get all users with their message and warning counts
SELECT 
    u.name,
    u.phone_number,
    COALESCE(cm.mcnt, 0) as total_messages,
    COALESCE(wm.total, 0) as total_warnings
FROM public.users u
LEFT JOIN (
    SELECT count(id) as mcnt, conversation_id 
    FROM public.messages 
    GROUP BY conversation_id
) cm ON cm.conversation_id = u.id
LEFT JOIN (
    SELECT count(id) as total, conversation_id 
    FROM public.metrics 
    GROUP BY conversation_id
) wm ON wm.conversation_id = u.id
ORDER BY u.name;


-- Get peak interaction hours throughout the day
SELECT 
    EXTRACT(HOUR FROM m.created_at) as hour_of_day,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT m.conversation_id) as unique_users
FROM public.messages m
JOIN public.conversations conv ON m.conversation_id = conv.id
GROUP BY EXTRACT(HOUR FROM m.created_at)
ORDER BY interaction_count DESC;

