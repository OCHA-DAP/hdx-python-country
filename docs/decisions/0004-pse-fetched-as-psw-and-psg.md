# 0004: Fetch PSE as PSW and PSG

## Status

Accepted — 2024-10-31

## Context

WFP treats the State of Palestine as two areas, the West Bank (`PSW`) and the Gaza Strip (`PSG`).
Asking WFP for `PSE` returns nothing. Checked live on 2026-11-04, the markets endpoint gave 0
markets for `PSE`, 12 for `PSW` and 47 for `PSG`.

## Decision

`WFPAPI._countryiso3s` turns `PSE` into `["PSW", "PSG"]`, so every country-filtered endpoint makes
one request per area and returns the combined rows.

## Consequences

- Callers use the ISO 3166 code `PSE` and get both areas' data.
- Saved files are per area, e.g. `MarketPrices_PriceMonthly_PSW.csv`.
