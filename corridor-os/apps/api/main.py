"""The HTTP surface.

Deliberately thin. Every endpoint is a projection of something the platform
already computed, and the two endpoints that could change state do so by
calling the same methods the tests call. There is no business logic here, which
is why swapping this layer for another one would not change what the product
does.

The one endpoint worth reading is `POST /api/copilot/ask`: it asks the copilot a
question and can return an abstention, and there is no endpoint anywhere in this
file through which the copilot could approve, post, execute, submit, clear or
close anything — because `core.authority` would refuse the call and there is no
route that tries.

Run it with:

    pip install -e '.[api]'
    uvicorn apps.api.main:app --reload
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from corridoros.core.authority import ACTIONS, AI_ALLOWED, CONSEQUENTIAL_ACTIONS
from corridoros.core.errors import AuthorityError, CorridorError
from corridoros.evidence.packet import assemble_for_payment
from corridoros.scenario.snapshot import build_snapshot
from corridoros.scenario.world import RECONCILIATION_DATE, build_demo

app = FastAPI(
    title="CorridorOS",
    version="0.1.0",
    description=(
        "China–Singapore cross-border payment operations platform. All data is synthetic; "
        "the system has never run in production."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WORLD = build_demo()
SNAPSHOT: dict[str, Any] = build_snapshot(WORLD)


class Question(BaseModel):
    payment_id: str
    question: str


@app.get("/health")
def health() -> dict[str, Any]:
    verification = WORLD.system.audit.verify()
    return {"status": "ok", "audit": verification.status, "synthetic_data": True}


@app.get("/api/snapshot")
def snapshot() -> dict[str, Any]:
    return SNAPSHOT


@app.get("/api/overview")
def overview() -> dict[str, Any]:
    return {**SNAPSHOT["overview"], "transcript": SNAPSHOT["demo_transcript"]}


@app.get("/api/businesses")
def businesses() -> list[dict[str, Any]]:
    return SNAPSHOT["businesses"]


@app.get("/api/payments")
def payments() -> list[dict[str, Any]]:
    return SNAPSHOT["payments"]


@app.get("/api/payments/{payment_id}")
def payment(payment_id: str) -> dict[str, Any]:
    try:
        return WORLD.system.payment_view(payment_id, now=RECONCILIATION_DATE)
    except CorridorError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/cases")
def cases() -> dict[str, Any]:
    return SNAPSHOT["cases"]


@app.get("/api/evidence")
def evidence() -> list[dict[str, Any]]:
    return SNAPSHOT["evidence"]


@app.get("/api/reconciliation")
def reconciliation() -> dict[str, Any]:
    return SNAPSHOT["reconciliation"]


@app.get("/api/audit")
def audit() -> dict[str, Any]:
    verification = WORLD.system.audit.verify()
    return {
        "entries": SNAPSHOT["audit"],
        "verification": {
            "status": verification.status,
            "head": verification.head,
            "entries_checked": verification.entries_checked,
            "summary": verification.summary(),
        },
        "refusals": WORLD.system.audit.refusals,
        "quarantined_events": SNAPSHOT["quarantined_events"],
    }


@app.get("/api/boundary")
def boundary() -> dict[str, Any]:
    return {
        "allowed": [
            {"action": action, "summary": ACTIONS[action].summary} for action in sorted(AI_ALLOWED)
        ],
        "forbidden": [
            {"action": action, "summary": ACTIONS[action].summary}
            for action in sorted(CONSEQUENTIAL_ACTIONS)
        ],
        "note": SNAPSHOT["ai_boundary"]["note"],
    }


@app.post("/api/copilot/ask")
def ask(question: Question) -> dict[str, Any]:
    """Ask the copilot about a payment. It answers with citations, or abstains."""
    system = WORLD.system
    try:
        payment = system.payouts.get(question.payment_id)
    except CorridorError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    beneficiary = system.beneficiaries.get(payment.beneficiary_id)
    packet = assemble_for_payment(system.evidence, payment, beneficiary, now=RECONCILIATION_DATE)
    brief = system.copilot.answer(question.question, packet, now=RECONCILIATION_DATE)
    return brief.as_row()


@app.post("/api/copilot/attempt/{action}")
def attempt(action: str, payment_id: str) -> dict[str, Any]:
    """Demonstrate the boundary: ask the copilot to do something consequential.

    It exists so a reader can see the refusal rather than take it on trust. The
    call is made through the same permission check every other write uses.
    """
    from corridoros.core.authority import AI_COPILOT, require

    if action not in ACTIONS:
        raise HTTPException(status_code=400, detail=f"unknown action {action!r}")
    try:
        require(AI_COPILOT, action, context=payment_id)
    except AuthorityError as error:
        return {
            "attempted": action,
            "permitted": False,
            "refusal": str(error),
            "refused_at": datetime.now().isoformat(),
        }
    return {"attempted": action, "permitted": True}
