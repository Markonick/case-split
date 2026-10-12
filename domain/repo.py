"""The persistence port + an in-memory fake, so the domain logic stays DB-free.

In the real app the adapter behind this port is SQLAlchemy over Postgres. Here the
``InMemoryRepo`` stands in for it, so every test runs offline with no database and no
Clerk. A real SQLAlchemy adapter would implement the same ``Repo`` protocol (written,
not exercised in this slice — see README).
"""

from __future__ import annotations

import uuid
from typing import Protocol

from domain.models import Customer


class Repo(Protocol):
    """What the promote logic needs from persistence — nothing more."""

    def find_customer_for(self, scope: str, email: str) -> Customer | None: ...
    def add_customer(self, customer: Customer) -> None: ...
    def get_customer(self, customer_id: uuid.UUID) -> Customer | None: ...


class InMemoryRepo:
    """Dict-backed stand-in for the real SQLAlchemy repository — no DB, no network."""

    def __init__(self) -> None:
        self.customers: dict[uuid.UUID, Customer] = {}

    def find_customer_for(self, scope: str, email: str) -> Customer | None:
        """One customer per (firm scope, email), case-insensitive; tombstoned ones excluded."""
        for c in self.customers.values():
            if (
                c.scope == scope
                and c.buyer_email.lower() == email.lower()
                and c.deleted_at is None
            ):
                return c
        return None

    def add_customer(self, customer: Customer) -> None:
        self.customers[customer.id] = customer

    def get_customer(self, customer_id: uuid.UUID) -> Customer | None:
        return self.customers.get(customer_id)
