"""
Fake past incident data for the knowledge base.
In a real system this would come from ServiceNow exports, JIRA, etc.
Each incident has a title, the original problem, and how it was resolved.
"""

INCIDENTS = [
    {
        "id": "INC-001",
        "title": "Payment API returning 500 errors",
        "description": "Payment service started returning HTTP 500 errors at ~30% rate during peak traffic. Customers unable to complete checkout.",
        "resolution": "Root cause: connection pool exhaustion on the database. Increased pool size from 20 to 50 and added connection timeout. Restarted payment-service pods.",
    },
    {
        "id": "INC-002",
        "title": "Login service slow response times",
        "description": "Login API p95 latency jumped from 200ms to 4 seconds. Users reporting timeouts.",
        "resolution": "Found a missing database index on the users.email column. Added index, latency returned to baseline within 5 minutes.",
    },
    {
        "id": "INC-003",
        "title": "Cron job failing silently",
        "description": "Daily reports cron job not running. No emails sent for 3 days. No alerts fired.",
        "resolution": "Cron service was disabled after a server restart. Re-enabled cron service and added a monitoring alert for cron service status.",
    },
    {
        "id": "INC-004",
        "title": "Disk space full on log server",
        "description": "Log ingestion stopped. Splunk indexer reporting disk full at 98%.",
        "resolution": "Old log archives were not being rotated. Manually deleted logs older than 90 days. Added a scheduled cleanup script via cron.",
    },
    {
        "id": "INC-005",
        "title": "Memory leak in notification service",
        "description": "Notification service pods being OOM-killed every 4-6 hours. Java heap usage grows continuously until crash.",
        "resolution": "Identified memory leak in the email template caching layer (cache had no eviction policy). Patched template cache to use LRU with 500 entry limit.",
    },
    {
        "id": "INC-006",
        "title": "Kafka consumer lag spiking",
        "description": "Order processing Kafka consumer lag at 2 million messages and growing. Orders not getting processed in real time.",
        "resolution": "Scaled consumer group from 3 to 10 instances. Added back-pressure handling. Lag drained within 90 minutes.",
    },
    {
        "id": "INC-007",
        "title": "SSL certificate expired",
        "description": "Customers getting SSL warnings on the main website. Some API integrations failing with cert errors.",
        "resolution": "Cert had expired without auto-renewal kicking in. Manually renewed via Let's Encrypt and fixed the renewal cron. Added 30-day expiry alert.",
    },
    {
        "id": "INC-008",
        "title": "Search service returning stale results",
        "description": "Product search showing items that were deleted hours ago. Inventory mismatches reported by support.",
        "resolution": "Elasticsearch indexer process had crashed silently. Restarted indexer and re-ran full reindex job. Added health-check endpoint with alerting.",
    },
    {
        "id": "INC-009",
        "title": "Auth service 503 errors after deploy",
        "description": "After 14:00 UTC deployment, auth service returning 503s sporadically. About 5% of login attempts failing.",
        "resolution": "Rolled back the deploy. New code had a misconfigured connection retry policy. Fix prepared, will redeploy with proper config in next release.",
    },
    {
        "id": "INC-010",
        "title": "S3 upload failures from mobile app",
        "description": "Mobile app users unable to upload profile photos. Backend logs show S3 PutObject errors with AccessDenied.",
        "resolution": "IAM role policy had been modified during a security review and lost s3:PutObject permission on the user-photos bucket. Restored the missing IAM permission.",
    },
]