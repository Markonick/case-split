# case-split

A small, **offline** pure-Python slice for one refactor: pulling the overloaded `Case`
apart into **Customer + Property + Lead**. No database, no Clerk — just dataclasses and an
in-memory fake repo, so everything runs with `make test`.

## The problem

Today `Case` is three things fused into one (`domain/models.py`):
- a **Lead** — it exists before any customer (calculator funnel),
- a **Property** — `address` / `price_eur` / `product_line` describe one house,
- a legacy **buyer-application** — `buyer_email` / `buyer_name` / `profile` are the person's
  identity *copied onto the case* (a drift-prone dual-write).

So a buyer with two houses becomes two `Case`s with the identity duplicated on each, instead
of **one Customer + two Properties**.

## The task

Refactor `domain/promote.py` from the current `get_or_create_person_customer` (which reads
identity off the `Case`) into a clean split:

- a **`Customer`** that is the single home of the person's identity + shared trunk,
- a **`Property`** = one house under a customer,
- a **`Lead`** = the pre-customer funnel record,
- `promote(lead) -> (Customer, Property | None)`,

with these behaviours (add tests for each):

- a lead **with** a house → **1 Customer + 1 Property**
- a lead with **no** house yet → a **Customer only**, no Property
- two houses, same person (same `scope` + email) → **1 Customer, 2 Properties**
- trunk doc categories owned by the **Customer**, branch categories by the **Property** (`owner_for`)
- the person identity comes from the **Customer**, not copied onto the lead/property
- a **trunk-only desk** (e.g. an accounting `product_line`) → **no Property**
- a **tombstoned** (soft-deleted) customer is never promoted onto again

A real SQLAlchemy adapter would sit behind the `Repo` protocol (`domain/repo.py`); writing a
thin stub of it is fine, but it is **not** exercised here — the point is to prove the split at
the logic level before any migration or Clerk wiring.

## Run (all offline, no key, no DB)

```bash
make setup     # uv sync — just pytest/ruff/mypy
make test      # the deterministic suite
make lint      # ruff + mypy
```

Python 3.11+ via [uv](https://docs.astral.sh/uv/).

## Layout

```
case-split/
├── domain/
│   ├── models.py    # Customer + the overloaded Case (+ owner_for, category sets)
│   ├── promote.py   # the current (overloaded) promote seam — the thing to refactor
│   └── repo.py      # the Repo port + an in-memory fake (no DB)
└── tests/           # starting-state tests (the "before"); the task adds the split behaviours
```

> This is a slice of a larger private repo; the real app runs on Postgres + Clerk. Here it's
> plain Python so the whole thing is offline and keyless.
