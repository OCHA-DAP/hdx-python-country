# 0002: Split the monthly prices date range on a gateway timeout

## Status

Accepted — 2026-11-03

## Context

A single CSV request for a large country can exceed the API gateway's timeout of about 30s. SYR's
first full request got a 504 after 30s, and the second returned 200 in 35s. Relying on
`_with_retry` is not acceptable, because the country run uses `wait=1800`, i.e. 30 minutes per
retry.

`start_date` and `end_date` are inclusive and split the data cleanly. On BTN, 1990–2019 plus
2020–2030 returned exactly the whole set (1,836 + 6,171 = 8,007 rows).

## Decision

`_get_prices_csv_range` requests the whole range (1990-01-01 to 31 December five years ahead,
since WFP has forecast prices). On a 504 it splits the range at the midpoint and requests each
half, recursively. A 504 on a single day, or any other error, is raised. `_get_prices_csv` joins
the pieces, keeping only the first header row.

## Consequences

- Most countries take one request. Each 504 costs about 30s before the split.
- On 2026-11-04 the server was slower, and IDN's range was split at least three times.
- Saved data is still one file per country, whatever the number of requests.
