"""
scripts/clean_knowledge_base.py

Two-pass KB fix:
  1. Replace all {{placeholder}} template variables with sensible generic values
  2. Append hand-written, placeholder-free SOPs for the most common intents

Run:  python scripts/clean_knowledge_base.py
"""

import os
import re
import shutil

KB_PATH    = "data/knowledge_base.txt"
FAISS_PATH = "data/faiss_index"

# ── Placeholder substitutions ─────────────────────────────────────────────────

SUBS: list[tuple[str, str]] = [
    # Contact / support
    (r"\{\{Customer Support Phone Number\}\}", "our support line (available on the Contact Us page)"),
    (r"\{\{Customer Support Email\}\}",        "support@company.com"),
    (r"\{\{Customer Support Hours\}\}",        "24/7"),
    (r"\{\{Customer Support Availability\}\}", "24 hours a day, 7 days a week"),

    # Account
    (r"\{\{Account Category\}\}",   "Standard"),
    (r"\{\{Account Type\}\}",       "account"),
    (r"\{\{Salutation\}\}",         "Dear customer"),
    (r"\{\{Person Name\}\}",        "you"),
    (r"\{\{Username\}\}",           "your username"),
    (r"\{\{Profile Settings\}\}",   "Account Settings"),
    (r"\{\{Security\}\}",           "Security"),
    (r"\{\{Reset Key\}\}",          "Reset Password"),
    (r"\{\{Forgot Key\}\}",         "Forgot Password"),

    # Order / delivery
    (r"\{\{Order Number\}\}",       "your order number"),
    (r"\{\{Order\s*Number\}\}",     "your order number"),
    (r"\{\{Invoice Number\}\}",     "your invoice number"),
    (r"\{\{Delivery City\}\}",      "your city"),
    (r"\{\{Delivery Country\}\}",   "your country"),
    (r"\{\{Delivery Date\}\}",      "the estimated delivery date"),
    (r"\{\{Date Range\}\}",         "the relevant date range"),
    (r"\{\{Tracking Number\}\}",    "your tracking number"),

    # Platform
    (r"\{\{Website URL\}\}",                    "our website"),
    (r"\{\{Online Company Portal Info\}\}",      "your account portal"),
    (r"\{\{Online Order Interaction\}\}",        "the Orders section of your account"),
    (r"\{\{Online Customer Interaction\}\}",     "your account dashboard"),
    (r"\{\{Refund Amount\}\}",                   "the refund amount"),
    (r"\{\{Refund Request Number\}\}",           "your refund request number"),
    (r"\{\{Subscription Type\}\}",               "your subscription"),
    (r"\{\{Cancellation Fee Amount\}\}",         "the applicable cancellation fee"),
    (r"\{\{Product\}\}",                         "the product"),
    (r"\{\{Product Name\}\}",                    "the product"),

    # Catch-all for any remaining {{...}} that weren't matched above
    (r"\{\{[^}]+\}\}", "[see our support portal for details]"),
]

# ── Hand-written SOPs (no placeholders, clear actionable steps) ───────────────

APPENDED_SOPS = """

========================================================================
CATEGORY: Account — Supplementary SOPs
========================================================================

--- Password Reset and Login Issues ---
If a customer cannot log in or their password reset is not working:
1. Ask the customer to go to the login page and click "Forgot Password".
2. Enter the email address associated with the account.
3. Check the inbox (and spam/junk folder) for the reset email — it arrives within 2 minutes.
4. Click the reset link in the email. Links expire after 30 minutes; request a new one if needed.
5. Set a new password that is at least 8 characters and includes a number and a symbol.
6. Clear browser cookies and cache, then try logging in with the new password.
7. If the issue persists after resetting, escalate to Account Support — the account may be locked.

If the reset email never arrives:
- Confirm the email address is spelled correctly.
- Check spam, promotions, and junk folders.
- Wait 5 minutes and try again; sometimes email delivery is delayed.
- As a last resort, ask the customer to contact support with proof of identity to unlock the account manually.

--- Account Locked After Failed Attempts ---
Accounts are temporarily locked after 5 consecutive failed login attempts for security.
The lock expires automatically after 30 minutes.
To unlock immediately, the customer should use the "Forgot Password" flow or contact support.

--- Email Address Change Causing Login Issues ---
If a customer changed their email and can no longer log in:
1. The login must use the NEW email address after the change is saved.
2. If the new email was entered incorrectly, the customer should contact support with the old email for verification.
3. Support can manually update the email after verifying the customer's identity.

--- Two-Factor Authentication (2FA) Issues ---
If a customer is not receiving their 2FA code:
1. Check that the phone number or authenticator app is correctly configured in Account Settings.
2. SMS codes may be delayed by up to 60 seconds.
3. If using an authenticator app, ensure the device clock is synced.
4. As a fallback, offer to disable 2FA after identity verification so the customer can log in.

========================================================================
CATEGORY: Billing — Supplementary SOPs
========================================================================

--- Duplicate or Incorrect Charge ---
If a customer reports being charged twice or charged an incorrect amount:
1. Ask for the order number, transaction date, and amount charged.
2. Verify the charges in the billing system.
3. If a duplicate charge is confirmed, issue a full refund for the duplicate — processing takes 3-5 business days.
4. If the charge is from a failed transaction that was retried, only one charge should apply; refund the other.
5. Send a confirmation email with the refund reference number.

--- Refund Policy ---
Refunds are eligible within 30 days of purchase for unused or defective items.
Digital products may have a different refund window — check the product's terms.
Refunds are returned to the original payment method and take 3-5 business days.
Shipping costs are non-refundable unless the return is due to our error.

--- Invoice Not Received ---
If a customer has not received their invoice:
1. Invoices are sent automatically to the email on file after payment is confirmed.
2. Ask the customer to check their spam or promotions folder.
3. Resend the invoice from the billing system to the customer's email.
4. If the customer needs a VAT invoice, confirm their VAT number and reissue.

========================================================================
CATEGORY: Order — Supplementary SOPs
========================================================================

--- Cancellation ---
Orders can be cancelled within 1 hour of placement if they have not yet been processed.
After 1 hour, cancellation depends on fulfilment status:
- If not yet dispatched: cancel and issue a full refund.
- If dispatched: the customer must wait for delivery and initiate a return.
To cancel, the customer should go to Orders → select the order → click "Cancel Order".
If the button is greyed out, the order is already in fulfilment — advise the return process.

--- Wrong Item or Missing Item ---
1. Ask the customer for the order number and a description or photo of the issue.
2. Confirm the order contents in the system.
3. For a wrong item: arrange a free return and reship the correct item at no extra cost.
4. For a missing item: verify the packing manifest and reship the missing item or issue a partial refund.

========================================================================
CATEGORY: Shipping — Supplementary SOPs
========================================================================

--- Package Marked Delivered But Not Received ---
1. Ask the customer to check with neighbours, building reception, and safe-drop locations.
2. Check the carrier's tracking page for a delivery photo or GPS confirmation.
3. If the package cannot be located within 48 hours, file a claim with the carrier.
4. Issue a replacement shipment or full refund once the claim is acknowledged.

--- Delivery Delayed ---
1. Check the carrier's tracking for the latest update.
2. Delays of 1-3 business days beyond the estimate are within normal variance.
3. If delayed by more than 5 business days with no tracking update, treat as a lost parcel.
4. Open a carrier investigation and offer the customer a replacement or refund.
"""


def clean(text: str) -> str:
    for pattern, replacement in SUBS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def main() -> None:
    if not os.path.exists(KB_PATH):
        print(f"ERROR: {KB_PATH} not found. Run scripts/build_knowledge_base.py first.")
        return

    # Backup original
    backup = KB_PATH + ".bak"
    shutil.copy2(KB_PATH, backup)
    print(f"Backed up original to {backup}")

    with open(KB_PATH, "r", encoding="utf-8") as f:
        original = f.read()

    # Count before
    before = len(re.findall(r"\{\{[^}]+\}\}", original))

    # Pass 1: replace placeholders
    cleaned = clean(original)

    # Pass 2: append hand-written SOPs
    cleaned += APPENDED_SOPS

    with open(KB_PATH, "w", encoding="utf-8") as f:
        f.write(cleaned)

    after = len(re.findall(r"\{\{[^}]+\}\}", cleaned))
    lines = cleaned.count("\n")

    print(f"Placeholders: {before} → {after}")
    print(f"KB size:      {len(original):,} → {len(cleaned):,} chars  ({lines:,} lines)")

    # Rebuild FAISS index
    if os.path.exists(FAISS_PATH):
        shutil.rmtree(FAISS_PATH)
        print(f"Deleted stale FAISS index → will rebuild on next request")

    print("\nDone. Restart the backend to apply changes.")


if __name__ == "__main__":
    main()
