"""The CURRENT promote seam, lifted from the real repo — overloaded, the starting point.

``get_or_create_person_customer`` builds a ``Customer`` from a ``Case``'s OWN identity
fields (``buyer_email`` / ``buyer_name`` / ``profile``) and links the case to it — but the
identity stays copied on the case too (the dual-write). There is no ``Lead`` or ``Property``
concept yet; a "house" is just more fields on the ``Case``.

The task is to refactor this into a clean ``promote(lead) -> (Customer, Property | None)``:
  * person identity lives ONLY on the ``Customer`` (single source — no copy on the lead/property),
  * a lead with a house yields a real ``Property`` under the customer; a lead with no house yet
    yields a ``Customer`` only,
  * a second house for the same person (same scope + email) reuses the one ``Customer``,
  * a trunk-only desk (e.g. accounting ``product_line``) yields NO ``Property``,
  * a tombstoned (soft-deleted) customer is never promoted onto again,
  * requirement ownership is routed by ``owner_for`` (trunk → customer, branch → property).
See README for the full acceptance list.
"""

from __future__ import annotations

from domain.models import Case, Customer
from domain.repo import Repo


def get_or_create_person_customer(repo: Repo, case: Case) -> tuple[Customer, bool]:
    """Find-or-create the person customer for ``case``; link the case; return (customer, created).

    Overloaded on purpose (the "before"): it reads identity off the case and leaves that
    identity duplicated there after linking.
    """
    if case.customer_id is not None:
        existing = repo.get_customer(case.customer_id)
        if existing is not None:
            return existing, False
    found = repo.find_customer_for(case.scope, case.buyer_email)
    if found is not None:
        case.customer_id = found.id
        return found, False
    # Identity carried off the case (minus any transient calculator inputs).
    identity = {k: v for k, v in case.profile.items() if k != "calculator"}
    customer = Customer(
        scope=case.scope,
        buyer_email=case.buyer_email,
        buyer_name=case.buyer_name,
        profile=identity,
    )
    repo.add_customer(customer)
    case.customer_id = customer.id
    return customer, True
