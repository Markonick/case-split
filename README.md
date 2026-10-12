# case-split

A small, **offline** starting point for one refactor: pulling the overloaded `Case` apart
into **Customer + Property + Lead**, built as a runnable vertical slice (API → service →
in-memory "DB") with the **old world and the new world side by side** so you can run and
compare both. No real database, no Clerk — everything runs with `make test`.

## Where this starts (the "old world")

Right now `domain/models.py` has an overloaded `Case` — it's three things fused into one:
- a **Lead** (exists before any customer, `status="lead"`),
- a **Property** (`address`/`price_eur`/`product_line` describe one house),
- a legacy **buyer-application** (`buyer_email`/`buyer_name`/`profile` are the person's
  identity *copied onto the case* — a drift-prone dual-write).

`domain/promote.py` is the current `get_or_create_person_customer` that reads identity off
the `Case`. `domain/repo.py` is an in-memory fake repo (the stand-in for Postgres). The 3
tests in `tests/` pin this current behaviour.

## The task — build the slice (this is what you implement)

Turn this into a runnable **old-vs-new** vertical slice, all offline:

1. **A service seam with two implementations** behind one protocol:
   - **old world** — the current overloaded promote (a house is a `Case`, identity copied
     onto it);
   - **new world** — the clean split: `Lead → (Customer, Property)`, where the person's
     identity lives **only** on the `Customer` and a `Property` is one house under it,
     carrying no identity.
2. **A thin FastAPI layer** (add `fastapi` + `httpx`): endpoints to create a lead, promote
   it, read the customer, and list the customer's houses — with a **faked auth dependency**
   (a `get_current_user` returning a claims dict, overridable in tests). Which world the app
   uses is selectable (e.g. a `WORLD=old|new` switch).
3. **The in-memory repo is the "fake DB"** — no Postgres, no network. A real SQLAlchemy
   adapter would sit behind the same port (a stub is fine; it is not run here).
4. **A way to run and compare the two worlds** — e.g. `make run-old` / `make run-new` and a
   comparison that drives the same scenario through both and shows how they differ.
5. **Tests** for both: the old world stays green; the new world proves the behaviours below.

### New-world behaviours (add a test for each)
- a lead **with** a house → **1 Customer + 1 Property**
- a lead with **no** house yet → a **Customer only**, no Property
- two houses, same person (same `scope` + email) → **1 Customer, 2 Properties**
- trunk doc categories owned by the **Customer**, branch categories by the **Property** (`owner_for`)
- the person identity comes from the **Customer**, **not** copied onto the lead/property
- a **trunk-only desk** (e.g. an accounting `product_line`) → **no Property**
- a **tombstoned** (soft-deleted) customer is never promoted onto again

## Run (all offline, no key, no DB)

```bash
make setup     # uv sync
make test      # the suite (3 passing "before" tests to start; you add the rest)
make lint      # ruff + mypy
# once you've built it:
make run-old   # drive the scenario through the OLD world
make run-new   # ... and the NEW world — compare
```

Python 3.11+ via [uv](https://docs.astral.sh/uv/). Everything is plain Python + (once you
add it) FastAPI — no database, no Clerk, no network beyond installing packages.

## Layout (starting point)

```
case-split/
├── domain/
│   ├── models.py    # Customer + the overloaded Case (+ owner_for, category sets)
│   ├── promote.py   # the current (overloaded) promote — the "old world" to keep + refactor from
│   └── repo.py      # the in-memory fake repo (the stand-in for the DB)
└── tests/           # 3 "before" tests; you add the service/API/new-world tests
```

> This is a slice of a larger private repo; the real app runs on Postgres + Clerk + a React
> UI. Here it's plain Python so the whole thing stays offline and keyless — the UI is out of
> scope. The point is to prove the Customer/Property/Lead split, and compare it to the old
> world, before any migration.
