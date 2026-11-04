# 0005: Treat WFP dates without a timezone as UTC

## Status

Accepted — 2026-07-20

## Context

WFP's dates have no timezone. Before the move to the DataBridges client (#88), they were parsed
with `parse_date`, which returns UTC datetimes. `data_bridges_client` returns naive datetimes
instead.

## Decision

`WFPExchangeRates.get_currency_historic_rates` sets UTC on any naive quotation date before
converting it to a timestamp. hdx-scraper-wfp-foodprices does the same for price dates.

## Consequences

- Historic rate timestamps are unchanged from the `parse_date` behaviour.
- If WFP starts returning dates with a timezone, they are used as given.
