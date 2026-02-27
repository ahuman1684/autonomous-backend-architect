"""Offline curated PostgreSQL best practices reference tool."""

from langchain_core.tools import tool

POSTGRES_BEST_PRACTICES = {
    "uuid": (
        "Use UUID primary keys for distributed systems and external exposure. "
        "In PostgreSQL 13+, prefer gen_random_uuid() (built-in, no extension needed). "
        "For older versions use uuid_generate_v4() from the uuid-ossp extension. "
        "Declare the column as: id UUID PRIMARY KEY DEFAULT gen_random_uuid(). "
        "UUIDs prevent enumeration attacks and work across shards/replicas."
    ),
    "timestamps": (
        "Always use TIMESTAMPTZ (TIMESTAMP WITH TIME ZONE) instead of plain TIMESTAMP "
        "to store UTC-normalized instants. "
        "Standard columns: created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). "
        "Keep updated_at in sync via a trigger or application logic. "
        "Never store local wall-clock times without a timezone offset."
    ),
    "indexing": (
        "Index types: B-tree (default, equality/range), GIN (JSONB, arrays, full-text), "
        "GiST (geometric, full-text, range types), BRIN (very large append-only tables), "
        "Hash (equality-only, rarely preferred). "
        "Partial indexes: CREATE INDEX … WHERE condition — smaller, faster for sparse queries. "
        "Covering indexes: INCLUDE (col1, col2) to avoid heap fetches (index-only scans). "
        "Always index foreign key columns to avoid sequential scans on joins. "
        "Composite indexes: column order matters — put equality columns first. "
        "Monitor with pg_stat_user_indexes; drop unused indexes to reduce write overhead."
    ),
    "constraints": (
        "NOT NULL: enforce on every column that must have a value. "
        "UNIQUE: single or multi-column uniqueness; creates an implicit index. "
        "CHECK: domain validation, e.g. CHECK (price > 0). "
        "FOREIGN KEY … REFERENCES with ON DELETE CASCADE / SET NULL / RESTRICT as appropriate. "
        "EXCLUSION constraints: prevent overlapping ranges/periods, e.g. "
        "EXCLUDE USING gist (room WITH =, during WITH &&). "
        "PRIMARY KEY implies NOT NULL + UNIQUE. "
        "Prefer declarative constraints over application-level validation for data integrity."
    ),
    "performance": (
        "Use connection pooling (PgBouncer) to reduce connection overhead. "
        "VACUUM and AUTOVACUUM reclaim dead tuples; tune autovacuum_vacuum_scale_factor. "
        "Use EXPLAIN (ANALYZE, BUFFERS) to diagnose slow queries. "
        "Partition large tables by range or list to improve query pruning. "
        "Materialised views cache expensive aggregations; refresh with REFRESH MATERIALIZED VIEW. "
        "Set work_mem appropriately for sort/hash operations. "
        "Use prepared statements to reduce parse/plan overhead. "
        "Consider read replicas for heavy read workloads."
    ),
    "security": (
        "Use SCRAM-SHA-256 authentication (pg_hba.conf). "
        "Principle of least privilege: grant only necessary permissions. "
        "Use separate roles for application (read/write) and migrations (DDL). "
        "Never connect as superuser from application code. "
        "Use row-level security (RLS) for multi-tenant data isolation: "
        "ALTER TABLE … ENABLE ROW LEVEL SECURITY; CREATE POLICY …. "
        "Encrypt sensitive columns with pgcrypto; use TLS for connections. "
        "Audit access with pgaudit extension."
    ),
    "naming": (
        "Use snake_case for all identifiers (tables, columns, indexes, functions). "
        "Table names should be plural nouns, e.g. users, orders, line_items. "
        "Primary key: id; foreign keys: <table_singular>_id, e.g. user_id. "
        "Boolean columns: use is_ or has_ prefix, e.g. is_active, has_verified_email. "
        "Timestamps: created_at, updated_at, deleted_at (soft-delete). "
        "Index naming convention: idx_<table>_<columns>, e.g. idx_orders_user_id. "
        "Constraint naming: uq_<table>_<col> for UNIQUE, fk_<table>_<col> for FK, "
        "ck_<table>_<col> for CHECK."
    ),
}


@tool
def lookup_postgres_best_practices(topic: str) -> str:
    """Look up offline curated PostgreSQL best practices for a given topic.

    Args:
        topic: The PostgreSQL topic to look up (e.g. 'uuid', 'indexing', 'security').

    Returns:
        Best-practices guidance for the topic, or all practices if no match found.
    """
    topic_lower = topic.lower().strip()

    # Direct match
    if topic_lower in POSTGRES_BEST_PRACTICES:
        return POSTGRES_BEST_PRACTICES[topic_lower]

    # Fuzzy match: key is in topic or topic is in key
    for key, value in POSTGRES_BEST_PRACTICES.items():
        if key in topic_lower or topic_lower in key:
            return value

    # No match — return all practices
    all_practices = "\n\n".join(
        f"[{key.upper()}]\n{value}"
        for key, value in POSTGRES_BEST_PRACTICES.items()
    )
    return f"No exact match for '{topic}'. Here are all available practices:\n\n{all_practices}"
