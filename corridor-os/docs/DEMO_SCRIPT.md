# Demo script — one payment, seven screens

Run `python -m corridoros.cli demo`, or open the console and follow the
Overview transcript. Roughly three minutes.

**0 · The claim.** A Shenzhen company's Singapore entity pays a supplier SGD
12,500. The supplier changed bank account six days ago. Everything that follows
is one `payment_id` moving through four modules.

**1 · Businesses & KYB.** Anchor Commerce (Singapore) Pte. Ltd., UEN
202604821K, approved. Try to approve an entity whose incorporation document is
missing and the call raises: approval cannot rest on documents that do not
exist.

**2 · Payments & Treasury.** The instruction: SGD 12,500 to Meridian Components
against PO-4821, with invoice INV-4821 attached. Balances come from the ledger,
which is a sum of journal entries, not a stored number.

**3 · Risk & Compliance.** Four deterministic signals fire — account changed six
days ago, no current verification, required documents missing, urgency language
in the instruction — band `critical`, rules version 1.0.0. No model participated.
A case opens at priority 1 and **holds the payment**.

**4 · Evidence & Cases.** The packet: invoice and purchase order present; a
signed change authorisation and a callback record missing. Each item carries an
issuer, a location and a SHA-256 of its excerpt. The copilot's brief cites only
identifiers inside this packet.

**5 · The moment the product exists for.** Someone asks the copilot to approve
the payment. It is refused — not because it declined, but because
`payment.approve` is absent from its permission set, `ApprovalDecision` rejects
it as an author, the audit log rejects it, and its output object has no field a
decision could be written into. The refusal is in the audit log.

**6 · Intervention.** Level 4: two approvers and a callback to a number already
on file. Amount tier t2 sets a floor of 2; the account change pins it to 4. The
decision states why not weaker and why not stronger. Treasury calls back, files
the signed authorisation, compliance closes the case — and only then can the
approvals be recorded. The same person approving twice is refused by identity.

**7 · Reconciliation and Audit Log.** Settled net SGD 12,490.20 after a SGD 9.80
fee. The ledger, the provider advice and the bank statement agree, so the run is
clean; introduce a difference and it becomes a typed exception with an owner and
a due time, and the run cannot be marked reconciled. The audit log recomputes as
one chain of 25 entries — and says plainly what that does and does not prove.
