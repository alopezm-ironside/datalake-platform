{% macro dedup_latest(relation, unique_key, order_by) %}
    {#
        Return exactly one row per `unique_key`, keeping the row that sorts
        first by `order_by` (typically DESC timestamps — latest wins).

        Implementation: subquery ROW_NUMBER(), NOT QUALIFY.
        Rationale: the subquery form is unconditionally valid in ZetaSQL;
        QUALIFY requires a WHERE TRUE guard when the outer query has no WHERE
        clause, making it error-prone in a parametric macro context.

        Usage:
            {{ dedup_latest(
                relation   = 'bronze',       -- CTE name or ref()/source()
                unique_key = 'id',
                order_by   = 'source_modified_at desc, ingested_at desc'
            ) }}
    #}
    select * except(_rn)
    from (
        select
            *,
            row_number() over (
                partition by {{ unique_key }}
                order by {{ order_by }}
            ) as _rn
        from {{ relation }}
    )
    where _rn = 1
{% endmacro %}
