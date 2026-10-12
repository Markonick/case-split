"""Starting-state tests — the current ("before") behaviour, all passing.

These pin what works today so a refactor can't silently break it. The task adds the
Lead/Customer/Property split behaviours on top (see README / the task brief).
"""

from __future__ import annotations

import uuid

from domain.models import BRANCH_CATEGORIES, TRUNK_CATEGORIES, Case, owner_for
from domain.promote import get_or_create_person_customer
from domain.repo import InMemoryRepo


def test_promote_creates_and_links_a_customer() -> None:
    repo = InMemoryRepo()
    case = Case(scope="org_1", buyer_email="a@b.com", buyer_name="A B", profile={"vat_registered": True})
    customer, created = get_or_create_person_customer(repo, case)
    assert created is True
    assert case.customer_id == customer.id
    assert customer.buyer_email == "a@b.com"
    assert customer.profile == {"vat_registered": True}


def test_second_case_same_person_reuses_the_customer() -> None:
    repo = InMemoryRepo()
    c1 = Case(scope="org_1", buyer_email="a@b.com")
    cust1, _ = get_or_create_person_customer(repo, c1)
    c2 = Case(scope="org_1", buyer_email="A@B.com")  # same person (case-insensitive email)
    cust2, created = get_or_create_person_customer(repo, c2)
    assert created is False
    assert cust2.id == cust1.id
    assert len(repo.customers) == 1


def test_owner_for_routes_trunk_to_customer_and_branch_to_case() -> None:
    cid, caseid = uuid.uuid4(), uuid.uuid4()
    assert owner_for(category=TRUNK_CATEGORIES[0], case_id=caseid, customer_id=cid) == {
        "customer_id": cid,
        "case_id": None,
    }
    assert owner_for(category=BRANCH_CATEGORIES[0], case_id=caseid, customer_id=cid) == {
        "customer_id": None,
        "case_id": caseid,
    }
    # No customer → falls back to the case (keeps exactly-one-owner).
    assert owner_for(category=TRUNK_CATEGORIES[0], case_id=caseid, customer_id=None) == {
        "customer_id": None,
        "case_id": caseid,
    }
