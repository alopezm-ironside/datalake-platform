{{ config(materialized='table') }}

{#
    Staging model: stg_odoo__account_move_lines
    Grain: one row per Odoo account.move.line id (current state).
    Source: Bronze append-only snapshots in raw.account_move_lines.

    Column convention (Option A — mechanical source mirror):
      Business columns mirror Bronze names exactly.
      Audit/plumbing columns are conformed:
        write_date  -> source_modified_at
        synced_at   -> ingested_at

    Dedup order: source_modified_at DESC (write_date), ingested_at DESC (synced_at).
    SYMMETRIC with stg_odoo__account_moves — write_date was added to Bronze lines by the
    Slice 2 pre-step (FR-0). NULL write_date on pre-FR-0 rows sorts LAST on DESC
    (BigQuery NULLS LAST); ingested_at tiebreaks within the NULL bucket.

    Partition filter: `where date is not null` satisfies BigQuery's
    require_partition_filter=True on the source table during a full-table scan.

    Incremental-swap path (do NOT implement here — Slice 3+):
      Same as stg_odoo__account_moves. Change config to incremental/merge, add synced_at
      lookback predicate inside the bronze CTE using the ingestion axis only.
      dedup_latest macro is untouched.
#}

with bronze as (
    select
        id,
        account_move_id,
        product_id,
        description,
        date,
        quantity,
        price_unit,
        discount,
        price_subtotal,
        price_total,
        account_id,
        account_name,
        debit,
        credit,
        tax_ids,
        tax_rate,
        tax_amount,
        write_date                      as source_modified_at,
        synced_at                       as ingested_at,
        sync_batch_id
    from {{ source('odoo_raw', 'account_move_lines') }}
    where date is not null
)

{{ dedup_latest(
    relation='bronze',
    unique_key='id',
    order_by='source_modified_at desc, ingested_at desc'
) }}
