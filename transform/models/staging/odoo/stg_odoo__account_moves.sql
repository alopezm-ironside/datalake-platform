{{ config(materialized='table', unique_key='id') }}

{#
    Staging model: stg_odoo__account_moves
    Grain: one row per Odoo account.move id (current state).
    Source: Bronze append-only snapshots in raw.account_moves.

    Column convention (Option A — mechanical source mirror):
      Business columns mirror Bronze names exactly.
      Audit/plumbing columns are conformed:
        write_date  -> source_modified_at
        synced_at   -> ingested_at

    Dedup order: source_modified_at DESC (write_date), ingested_at DESC (synced_at).
    NULL write_date rows sort last on DESC (BigQuery NULLS LAST) — correct
    for pre-Slice-1 Bronze rows; ingested_at tiebreaks within the NULL bucket.

    Partition filter: `where date is not null` satisfies BigQuery's
    require_partition_filter=True on the source table during a full-table scan
    (table materialization = full rescan every run).

    Incremental-swap path (do NOT implement here — Slice 3+):
      1. Change config to: materialized='incremental', incremental_strategy='merge', unique_key='id'
      2. Inside the bronze CTE, add after `where date is not null`:
             {% if is_incremental() %}
               and synced_at >= (select coalesce(max(ingested_at), timestamp('1970-01-01')) from {{ this }})
             {% endif %}
         Use the ingestion axis (synced_at / ingested_at), NOT the accounting date axis.
         A mutated move re-enters Bronze with a fresh synced_at regardless of its original date.
      3. Schedule periodic `dbt build --full-refresh` for drift correction.
      4. dedup_latest macro is untouched; only dbt_project.yml config changes.
#}

with bronze as (
    select
        id,
        name,
        move_type,
        date,
        partner_id,
        partner_name,
        company_id,
        company_name,
        journal_id,
        journal_name,
        currency_name,
        amount_untaxed,
        amount_tax,
        amount_total,
        state,
        payment_state,
        ref,
        write_date                      as source_modified_at,
        synced_at                       as ingested_at,
        sync_batch_id
    from {{ source('odoo_raw', 'account_moves') }}
    where date is not null
)

{{ dedup_latest(
    relation='bronze',
    unique_key='id',
    order_by='source_modified_at desc, ingested_at desc'
) }}
