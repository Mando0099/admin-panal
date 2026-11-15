# Before going live
- Verify written permission to collect for multiple merchants under one master account.
- Confirm exact Fawaterak API base URL, authentication, invoice fields and currency precision.
- Confirm webhook signature header/algorithm, event schema and status inquiry API.
- Confirm transaction history, balance inquiry, settlement report, fee details and refund APIs.
- Confirm whether a payout/transfer API exists and is enabled for your account.
- Implement verified payment-to-ledger posting, refund reversals, holds, reserves, payout reservation and reconciliation before live funds.
- Add Alembic migrations, rate limiting, 2FA, audit retention, monitoring, backup restore tests and independent security review.
- Do not treat a payment success redirect as proof of payment.
