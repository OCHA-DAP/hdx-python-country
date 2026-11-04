# 0003: Parse WFP CSV with shared values and fields sets

## Status

Accepted — 2026-11-03

## Context

Fetching and parsing IDN's prices (462,027 rows) peaked at 2.31 GB with the first CSV parser, and
the country run was killed on Jenkins (exit code 137). Each row's
`ViewExtendedMonthlyAggregatedPrice` took about 3.2 KB:

| Part | Bytes |
|---|---|
| Object | 72 |
| `__dict__` with 22 fields | 832 |
| `__pydantic_fields_set__`, the 22 field names set on this row | 2,264 |
| Empty `additional_properties` | 64 |

Every row also held its own copies of repeated values such as market names, dates and units.
`io.StringIO` copied the whole text into a buffer of 4 bytes per character.

## Decision

`_parse_csv`:

- Splits lines lazily with `text.split("\n")` instead of `io.StringIO`, re-adding the `\n` to each
  line so quoted fields containing line breaks parse the same.
- Reuses one object per distinct value in each column.
- Gives rows with the same fields one shared `__pydantic_fields_set__`. Pydantic only adds to it
  when a field is assigned, and every field is already in it.

## Consequences

Measured on the saved IDN CSV:

| | Peak memory | Parse time |
|---|---|---|
| `io.StringIO` | 2,310 MB | 9.5s |
| Lazy split | 2,059 MB | |
| Lazy split and reused values | 1,755 MB | |
| Lazy split, reused values and shared fields set | 746 MB | 5.7s |

- The parsed rows are identical to those from the `io.StringIO` parser.
- Rows share value objects. They are immutable (str, int, float, datetime), so this is not visible
  to callers.
