# 0001: Fetch WFP DataBridges data as CSV rather than paged JSON

## Status

Accepted — 2026-11-03

## Context

JSON paging of `market_prices_price_monthly_get` is unstable. Confirmed live on NGA: each run
returned about 1,690 rows twice and left out the same number, so datasets built from it missed
about 1.4% of rows. The endpoint has no sort parameter that would make offset paging
deterministic.

`format="CSV"` returns every row once in a single response and ignores `page` (NGA: 121,669
distinct rows in about 10s, compared with about 800s paged). The other `WFPAPI` endpoints accept
CSV too.

## Decision

Every `WFPAPI` endpoint is called with `format="CSV"` through the generated
`*_without_preload_content` methods, and the JSON paging code is removed.

- CSV headers are the JSON keys with the first letter capitalised, and every value is a string.
  `_csv_converters` builds the int, float, bool and datetime converters from each model's pydantic
  annotations.
- `_get_csv` raises `ApiException` on a non-200 status, as the JSON methods do, so `_with_retry`
  still refreshes the token and retries.
- Saved data is the CSV that WFP returns, one file per call.

## Consequences

- Blank text fields are `""` where JSON gave `None`.
- Commodity `qualities` and `processing` are always `None`, since CSV omits them.
- Datetimes lose milliseconds.
- Data saved in the old JSON format no longer loads.
- A whole country comes back in one response (SYR: 516,907 rows, 103 MB), which can hit the
  gateway timeout (see 0002) and needs care with memory (see 0003).
