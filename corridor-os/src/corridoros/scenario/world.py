"""One synthetic world, shared by every module.

Before the merge, each project generated its own population: RiskOps built a
seeded world of wallets and merchants, WealthGuard ingested official documents,
FinSafe held fixed message cases. Nothing in one appeared in the others, so no
single payment could be followed across them — which is precisely what the
platform now claims to do.

This module builds the world once. The same `biz_sz001…` appears in KYB, in the
ledger, in the risk queue, in the evidence register and in the audit log,
because there is only one of it.

**Everything here is synthetic.** The companies, the suppliers, the invoices,
the bank references and the amounts were written for this demonstration. No
real entity, document, bank or transaction is involved, and nothing in this
package has run in production.

Dates are fixed rather than relative to "now", so the demonstration reads the
same in December as it does today and a screenshot stays accurate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..core.authority import AI_COPILOT
from ..core.domain import Beneficiary
from ..core.errors import AuthorityError
from ..core.ids import make_id
from ..core.money import Money
from ..payments.reconciliation import BankStatementLine
from ..platform import ControlOutcome, CorridorOS


def _at(year: int, month: int, day: int, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# The flagship storyline's fixed clock.
INCORPORATION_DATE = _at(2026, 3, 18)
ONBOARDING_DATE = _at(2026, 4, 2)
KYB_APPROVAL_DATE = _at(2026, 4, 10, 11, 20)
FIRST_COLLECTION_DATE = _at(2026, 4, 15, 10, 30)
SUPPLIER_ONBOARDED_DATE = _at(2026, 5, 2, 14, 0)
SUPPLIER_VERIFIED_DATE = _at(2026, 5, 3, 9, 30)
ROUTINE_PAYMENT_DATE = _at(2026, 5, 5, 10, 0)
ROUTINE_SETTLEMENT_DATE = _at(2026, 5, 6, 16, 0)
ACCOUNT_CHANGE_DATE = _at(2026, 9, 8, 8, 40)
FLAGSHIP_PAYMENT_DATE = _at(2026, 9, 14, 9, 5)
RECONCILIATION_DATE = _at(2026, 9, 16, 7, 0)

BUSINESS_ID = make_id("business", "sz001")
SUPPLIER_ID = make_id("beneficiary", "ben0193")
LOGISTICS_ID = make_id("beneficiary", "ben0207")

FLAGSHIP_AMOUNT = Money.from_major("12500.00", "SGD")
ROUTINE_AMOUNT = Money.from_major("8400.00", "SGD")

# The supplier's email, as received. It is untrusted text: it reaches the
# copilot only through the input gate, and the gate is why a paragraph aimed at
# an automated reader never reaches composition.
SUPPLIER_EMAIL = (
    "Dear finance team, please note our banking details have been updated as of this month. "
    "Kindly remit invoice INV-4821 to the new account. Pay today if possible as our quarter closes."
)


@dataclass
class World:
    system: CorridorOS
    routine_payment_id: str
    flagship_payment_id: str
    flagship_controls: ControlOutcome | None = None
    transcript: list[str] = None  # type: ignore[assignment]

    def say(self, line: str) -> None:
        self.transcript.append(line)


def build_world(namespace: str = "cos") -> World:
    """Onboard the entity, fund it, register suppliers, and settle one routine payment.

    This is the state the flagship storyline starts from: an approved business
    with money in the account and an established supplier relationship. Without
    that history the interesting payment would be indistinguishable from a first
    payment to a stranger, and the demonstration would prove nothing.
    """
    system = CorridorOS(namespace)
    transcript: list[str] = []

    # --- the entity ------------------------------------------------------
    system.onboard(
        business_id=BUSINESS_ID,
        legal_name="Anchor Commerce (Singapore) Pte. Ltd.",
        uen="202604821K",
        entity_country="SG",
        expected_monthly_volume=Money.from_major("400000.00", "SGD"),
        occurred_at=ONBOARDING_DATE,
        industry="wholesale_trade",
    )
    system.evidence.add(
        kind="incorporation_document",
        title="ACRA business profile — Anchor Commerce (Singapore) Pte. Ltd.",
        issuer="Synthetic registry extract",
        excerpt="Incorporated 18 March 2026. UEN 202604821K. Principal activity: wholesale trade.",
        location="page 1",
        issued_at=INCORPORATION_DATE,
        business_id=BUSINESS_ID,
    )
    system.evidence.add(
        kind="ownership_declaration",
        title="Beneficial ownership declaration",
        issuer="Anchor Commerce (Shenzhen) Ltd.",
        excerpt=(
            "Parent entity Anchor Commerce (Shenzhen) Ltd. holds 100%. Two directors declared, "
            "both resident in the PRC."
        ),
        location="clause 3",
        issued_at=_at(2026, 4, 1),
        business_id=BUSINESS_ID,
    )
    system.approve_business(BUSINESS_ID, occurred_at=KYB_APPROVAL_DATE, note="Evidence complete.")
    transcript.append(
        "KYB approved: Anchor Commerce (Singapore) Pte. Ltd., UEN 202604821K — "
        "approval refused until both required documents were on file."
    )

    # --- money in --------------------------------------------------------
    system.collect(
        business_id=BUSINESS_ID,
        amount=Money.from_major("240000.00", "SGD"),
        reference="ANCHOR-COLLECT-0417",
        received_at=FIRST_COLLECTION_DATE,
        provider_event_id="pe_collect_0417",
    )
    transcript.append("Collected SGD 240,000.00 against collection reference ANCHOR-COLLECT-0417.")

    # --- suppliers -------------------------------------------------------
    system.beneficiaries.register(
        Beneficiary(
            beneficiary_id=SUPPLIER_ID,
            business_id=BUSINESS_ID,
            display_name="Meridian Components Pte. Ltd.",
            bank_country="SG",
            account_last4="4417",
            created_at=SUPPLIER_ONBOARDED_DATE,
        )
    )
    system.beneficiaries.record_verification(
        SUPPLIER_ID,
        occurred_at=SUPPLIER_VERIFIED_DATE,
        method="callback_to_number_on_file",
        actor_role="treasury_operator",
        actor_id="treasury.ops",
    )
    system.beneficiaries.register(
        Beneficiary(
            beneficiary_id=LOGISTICS_ID,
            business_id=BUSINESS_ID,
            display_name="Straits Freight Services Pte. Ltd.",
            bank_country="SG",
            account_last4="9022",
            created_at=_at(2026, 5, 20),
        )
    )

    # --- a routine payment, settled -------------------------------------
    invoice = system.evidence.add(
        kind="invoice",
        title="Invoice INV-4402",
        issuer="Meridian Components Pte. Ltd.",
        excerpt="Invoice INV-4402, SGD 8,400.00, components order, net 30 days.",
        location="page 1",
        issued_at=_at(2026, 4, 28),
        business_id=BUSINESS_ID,
        beneficiary_id=SUPPLIER_ID,
        structured_facts={"invoice_number": "INV-4402", "amount_sgd": "8400.00"},
    )
    purchase_order = system.evidence.add(
        kind="purchase_order",
        title="Purchase order PO-4402",
        issuer="Anchor Commerce (Singapore) Pte. Ltd.",
        excerpt="PO-4402 authorises SGD 8,400.00 to Meridian Components Pte. Ltd.",
        location="line 1",
        issued_at=_at(2026, 4, 26),
        business_id=BUSINESS_ID,
        beneficiary_id=SUPPLIER_ID,
        structured_facts={"po_number": "PO-4402"},
    )
    routine = system.create_payment(
        business_id=BUSINESS_ID,
        beneficiary_id=SUPPLIER_ID,
        amount=ROUTINE_AMOUNT,
        purpose_code="SUPPLIER_INVOICE",
        business_instruction_id="PO-4402",
        idempotency_key="idem-po-4402",
        occurred_at=ROUTINE_PAYMENT_DATE,
        evidence_ids=(invoice.evidence_id, purchase_order.evidence_id),
    )
    system.evidence.link(invoice.evidence_id, payment_id=routine.payment_id)
    system.evidence.link(purchase_order.evidence_id, payment_id=routine.payment_id)
    system.run_controls(routine.payment_id, now=ROUTINE_PAYMENT_DATE)
    system.approve_payment(
        routine.payment_id, now=ROUTINE_PAYMENT_DATE + timedelta(hours=1), actor_id="approver.chen"
    )
    system.submit_payment(
        routine.payment_id, now=ROUTINE_PAYMENT_DATE + timedelta(hours=1, minutes=5), actor_id="approver.chen"
    )
    system.settle_payment(
        routine.payment_id,
        now=ROUTINE_SETTLEMENT_DATE,
        fee=Money.from_major("6.50", "SGD"),
        provider_reference="PSP-4402-STL",
        value_date=ROUTINE_SETTLEMENT_DATE,
    )
    transcript.append(
        "A routine SGD 8,400.00 invoice to the same supplier was created, approved by one person, "
        "submitted and settled — the baseline this corridor is expected to produce."
    )

    return World(
        system=system,
        routine_payment_id=routine.payment_id,
        flagship_payment_id="",
        transcript=transcript,
    )


def run_flagship_story(world: World) -> World:
    """The SGD 12,500 payment: supplier changed bank account six days ago.

    Every step below is a call into the platform, not narration. The refusals in
    the middle are real refusals — remove the callback and the approval raises.
    """
    system = world.system

    # The supplier emails new bank details; treasury updates the record.
    system.beneficiaries.change_account(
        SUPPLIER_ID,
        new_account_last4="8830",
        occurred_at=ACCOUNT_CHANGE_DATE,
        source="email_from_supplier",
    )
    world.say(
        "Six days before the payment, Meridian Components' bank account was changed "
        "from ...4417 to ...8830 on the strength of an email."
    )

    invoice = system.evidence.add(
        kind="invoice",
        title="Invoice INV-4821",
        issuer="Meridian Components Pte. Ltd.",
        excerpt="Invoice INV-4821, SGD 12,500.00, components order, due 30 September 2026.",
        location="page 1",
        issued_at=_at(2026, 9, 2),
        business_id=BUSINESS_ID,
        beneficiary_id=SUPPLIER_ID,
        structured_facts={"invoice_number": "INV-4821", "amount_sgd": "12500.00"},
    )
    purchase_order = system.evidence.add(
        kind="purchase_order",
        title="Purchase order PO-4821",
        issuer="Anchor Commerce (Singapore) Pte. Ltd.",
        excerpt="PO-4821 authorises SGD 12,500.00 to Meridian Components Pte. Ltd. for components.",
        location="line 1",
        issued_at=_at(2026, 8, 29),
        business_id=BUSINESS_ID,
        beneficiary_id=SUPPLIER_ID,
        structured_facts={"po_number": "PO-4821", "amount_sgd": "12500.00"},
    )

    payment = system.create_payment(
        business_id=BUSINESS_ID,
        beneficiary_id=SUPPLIER_ID,
        amount=FLAGSHIP_AMOUNT,
        purpose_code="SUPPLIER_INVOICE",
        business_instruction_id="PO-4821",
        idempotency_key="idem-po-4821",
        occurred_at=FLAGSHIP_PAYMENT_DATE,
        evidence_ids=(invoice.evidence_id, purchase_order.evidence_id),
    )
    system.evidence.link(invoice.evidence_id, payment_id=payment.payment_id)
    system.evidence.link(purchase_order.evidence_id, payment_id=payment.payment_id)
    world.flagship_payment_id = payment.payment_id
    world.say(
        f"{payment.payment_id}: SGD 12,500.00 to Meridian Components, invoice INV-4821 and "
        "purchase order PO-4821 attached."
    )

    outcome = system.run_controls(
        payment.payment_id,
        now=FLAGSHIP_PAYMENT_DATE + timedelta(minutes=2),
        instruction_note=SUPPLIER_EMAIL,
    )
    world.flagship_controls = outcome
    world.say(
        f"Risk: band {outcome.assessment.band} on "
        f"{', '.join(signal.signal_id for signal in outcome.assessment.signals)} "
        f"(rules {outcome.assessment.rules_version}, no model involved)."
    )
    world.say(
        f"Intervention: level {outcome.intervention.selected_level} — "
        f"{outcome.intervention.required_approvals} approvers and "
        f"{', '.join(outcome.intervention.required_verifications)} required. "
        f"{outcome.intervention.why_not_weaker}"
    )
    if outcome.case is not None:
        world.say(
            f"Case {outcome.case.case_id} opened at priority {outcome.case.priority}; "
            "the payment is held until a compliance officer closes it."
        )
    world.say(
        "Copilot brief: "
        + (outcome.brief.summary or outcome.brief.abstention_reason)
        + f" Missing: {', '.join(outcome.brief.missing_information) or 'nothing'}."
    )

    # The requirements are satisfied by people, and each produces evidence.
    callback = system.evidence.add(
        kind="callback_record",
        title="Callback record — Meridian Components",
        issuer="Anchor Commerce treasury",
        excerpt=(
            "Called the number on file (not the number in the email) on 14 September 2026 and spoke "
            "to the finance manager, who confirmed the account change and the invoice amount."
        ),
        location="call log entry 2026-09-14",
        issued_at=FLAGSHIP_PAYMENT_DATE + timedelta(hours=1),
        business_id=BUSINESS_ID,
        beneficiary_id=SUPPLIER_ID,
        payment_id=payment.payment_id,
    )
    authorisation = system.evidence.add(
        kind="beneficiary_change_authorisation",
        title="Account change authorisation on letterhead",
        issuer="Meridian Components Pte. Ltd.",
        excerpt=(
            "Signed and dated authorisation confirming the change of collection account to the "
            "account ending 8830, countersigned by two directors."
        ),
        location="page 1",
        issued_at=FLAGSHIP_PAYMENT_DATE + timedelta(hours=2),
        business_id=BUSINESS_ID,
        beneficiary_id=SUPPLIER_ID,
        payment_id=payment.payment_id,
    )
    system.complete_verification(
        payment.payment_id,
        "obtain_change_authorisation",
        now=FLAGSHIP_PAYMENT_DATE + timedelta(hours=2, minutes=10),
        actor_id="treasury.ops",
        evidence_id=authorisation.evidence_id,
    )
    system.complete_verification(
        payment.payment_id,
        "callback_known_contact",
        now=FLAGSHIP_PAYMENT_DATE + timedelta(hours=2, minutes=15),
        actor_id="treasury.ops",
        evidence_id=callback.evidence_id,
    )
    system.complete_verification(
        payment.payment_id,
        "hold_and_document",
        now=FLAGSHIP_PAYMENT_DATE + timedelta(hours=2, minutes=20),
        actor_id="approver.lim",
        actor_role="payment_approver",
        note="Held pending callback; both documents filed against the payment.",
    )
    world.say(
        "Treasury called back a number already on file, obtained a signed change authorisation, "
        "and filed both against the payment."
    )

    if world.flagship_controls.case is not None:
        system.close_case(
            world.flagship_controls.case.case_id,
            now=FLAGSHIP_PAYMENT_DATE + timedelta(hours=3),
            reason_code="verified_change_no_further_action",
            note="Callback and signed authorisation reviewed; account change is genuine.",
        )
        world.say(
            "A compliance officer closed the investigation case. The copilot could not have: "
            "`case.close` is not in its permission set."
        )

    # Under queue pressure, somebody asks the copilot to do the approving. The
    # refusal below is the platform's, not a script's: `payouts.approve` routes
    # every decision through the audit log, which rejects an AI author.
    try:
        system.payouts.approve(
            payment.payment_id,
            occurred_at=FLAGSHIP_PAYMENT_DATE + timedelta(hours=3, minutes=15),
            actor_role=AI_COPILOT,
            actor_id="copilot",
            decision_id=system.next_decision_id(),
            reason_code="analyst_asked_the_copilot_to_approve",
        )
        raise AssertionError("the copilot approved a payment; this must never happen")
    except AuthorityError as refusal:
        world.say(f"Asked to approve the payment itself, the copilot was refused: {refusal}")

    system.approve_payment(
        payment.payment_id,
        now=FLAGSHIP_PAYMENT_DATE + timedelta(hours=3, minutes=30),
        actor_id="approver.lim",
    )
    system.approve_payment(
        payment.payment_id,
        now=FLAGSHIP_PAYMENT_DATE + timedelta(hours=4),
        actor_id="approver.chen",
    )
    world.say("Two different approvers released the payment; the same person twice is refused.")

    system.submit_payment(
        payment.payment_id,
        now=FLAGSHIP_PAYMENT_DATE + timedelta(hours=4, minutes=5),
        actor_id="approver.chen",
    )
    settlement = system.settle_payment(
        payment.payment_id,
        now=FLAGSHIP_PAYMENT_DATE + timedelta(days=1, hours=6),
        fee=Money.from_major("9.80", "SGD"),
        provider_reference="PSP-4821-STL",
        value_date=FLAGSHIP_PAYMENT_DATE + timedelta(days=1),
    )
    world.say(f"Settled: net {settlement.net.format()} after an SGD 9.80 fee.")

    result = system.reconcile(now=RECONCILIATION_DATE, bank_lines=clean_bank_lines(system))
    world.say(
        "Three-way reconciliation: "
        f"{len(result.matched_payment_ids)} matched, {len(result.exceptions)} exception(s), "
        f"{result.unexplained.format()} unexplained."
    )
    return world


def clean_bank_lines(system: CorridorOS) -> tuple[BankStatementLine, ...]:
    """A bank statement that agrees with the provider — the reconciled case."""
    return tuple(
        BankStatementLine(
            bank_reference=settlement.provider_reference,
            amount=settlement.net,
            value_date=settlement.value_date,
            narrative=f"payment {settlement.payment_id}",
        )
        for settlement in system.settlements.all
    )


def build_demo() -> World:
    """The whole storyline, start to finish."""
    return run_flagship_story(build_world())
