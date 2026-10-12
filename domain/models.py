"""The CURRENT (overloaded) domain — before the split.

Today ``Case`` is three things fused into one:
  * a **Lead** — it exists before any customer (``customer_id is None``, ``status="lead"``),
  * a **Property** — ``address`` / ``price_eur`` / ``product_line`` describe one house,
  * a legacy **buyer-application** — ``buyer_email`` / ``buyer_name`` / ``profile`` are the
    person's identity *copied onto the case* (the drift-prone dual-write we want gone).

The task is to pull those apart into ``Customer`` (the person / shared trunk),
``Property`` (one house under a customer) and ``Lead`` (the pre-customer funnel). See README.

``owner_for`` is kept verbatim from the real repo: it routes a document requirement to its
single owner — a trunk (person-scoped) category goes to the customer, a branch
(property-scoped) category to the case/property.
"""

from __future__ import annotations

import uuid
from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import datetime

# The six pre-approval journey stages, in order. The first two are person/trunk
# (shared across a buyer's properties); the rest are property/branch.
PLAN_CATEGORIES: tuple[str, ...] = (
    "application",
    "pre_approval",
    "property_check",
    "final_approval",
    "contract",
    "disbursement",
)
TRUNK_CATEGORIES: tuple[str, ...] = PLAN_CATEGORIES[:2]
BRANCH_CATEGORIES: tuple[str, ...] = PLAN_CATEGORIES[2:]


def owner_for(
    *,
    category: str,
    case_id: uuid.UUID | None,
    customer_id: uuid.UUID | None,
    person_stage_keys: Collection[str] | None = None,
) -> dict[str, uuid.UUID | None]:
    """Route a requirement to its single owner: a trunk (person-scoped) category belongs
    to the shared customer; a branch (property-scoped) category to the case/property.
    Falls back to the case when there is no customer, keeping exactly-one-owner satisfied."""
    person_keys: Collection[str] = (
        person_stage_keys if person_stage_keys is not None else TRUNK_CATEGORIES
    )
    if category in person_keys and customer_id is not None:
        return {"customer_id": customer_id, "case_id": None}
    return {"customer_id": None, "case_id": case_id}


def _new_id() -> uuid.UUID:
    return uuid.uuid4()


@dataclass
class Customer:
    """The person / client — owner of the shared trunk (identity + person-scoped docs)."""

    scope: str  # the firm scope: an org_id, or a solo broker's own id
    buyer_email: str
    buyer_name: str | None = None
    profile: dict = field(default_factory=dict)
    shared_with: list[str] = field(default_factory=list)
    deleted_at: datetime | None = None  # soft-delete / tombstone
    id: uuid.UUID = field(default_factory=_new_id)


@dataclass
class Case:
    """OVERLOADED: a lead + a property + the buyer's identity, all in one row."""

    scope: str
    buyer_email: str  # ← identity copied onto the case (dual-write to remove)
    buyer_name: str | None = None  # ← identity
    profile: dict = field(default_factory=dict)  # ← identity
    product_line: str | None = None  # the desk/vertical, e.g. "home_resident" / "accounting_*"
    status: str = "lead"  # "lead" (no customer yet) | "active"
    address: str | None = None  # property attributes (a house)
    price_eur: int | None = None
    customer_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=_new_id)


@dataclass
class Requirement:
    """A document requirement. Owner is exactly one of (customer_id, case_id) — see owner_for."""

    category: str
    customer_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=_new_id)
