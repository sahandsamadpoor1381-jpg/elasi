# External and execution blockers

Updated: 2026-10-20
These blockers are not resolved by code or by a mock. Continue independent implementation while they remain open.

| Blocker | Evidence/status | Required input or authorization | Safe action until resolved |
| --- | --- | --- | --- |
| SnappPay | Merchant acceptance is inactive | Merchant acceptance, verified current integration documents, sandbox credentials, callback/signature details, and explicit approval for integration testing | Do not activate or initiate a SnappPay payment |
| TorobPay | Merchant acceptance is inactive | Merchant acceptance, verified current integration documents, sandbox credentials, callback/signature details, and explicit approval for integration testing | Keep provider disabled |
| Standard payment gateway | No gateway selected | Merchant's written provider choice, current official documents, merchant account, sandbox credentials and approval | Internal interface/mock only at Stage 3; no real charges |
| SMS delivery | Provider and credentials are not verified | Provider selection, official API/contract, sender registration, test credentials and confirmation of a non-sending test path | Do not send SMS or expose OTPs in logs, tests, screenshots or reports |
| Merchant policies/content | Approved content not supplied/verified | Final shipping/returns/warranty/privacy/terms copy, contact details, product descriptions and approved imagery/pricing/inventory | Do not invent or publish policy, contact, testimonial, product, price or stock claims |
| Approved staging target | Host, environment owner and access are not supplied in this task | Staging URL, authorized test accounts, data owner, service budget and access policy | Keep deployment and mutation testing off |
| Production release controls | Backup/restore evidence, rollback owner, monitoring and written deployment approval are not confirmed | Approved runbook inputs and explicit release authorization | No production deployment, data writes, destructive migrations, or new hosting/service costs |
| Browser acceptance | Chromium binary is absent; the latest `npm run test:e2e` attempt discovered 15 tests, but all stopped before assertions at browser launch | Run `npm run test:e2e:install` and `npm run test:e2e` in an approved browser-enabled environment | Report execution as **BLOCKED (0 assertions)** until the browser launches; no rendered acceptance is established |
| Visual evidence | No screenshots or browser capture were attached/found in the workspace | Approved rendered screenshots or browser access to the current application | Findings in this milestone are based on code inspection; do not claim pixel-level acceptance |
| Requested release branch | Session policy fixes work to `arena/5630017a-elasi` | No branch rename/creation is permitted in this session | Continue only on `arena/5630017a-elasi`; do not switch to `release/elasi-v1` or merge to `main` |

## Items needed next from the merchant/client

1. Name the staging owner and provide a non-production URL plus authorized test accounts.
2. Provide the selected payment provider's current official merchant documentation and sandbox account/credentials through the approved secret channel, plus written authorization for sandbox testing.
3. Provide the selected SMS provider's current official documentation and a non-sending test path; explicitly approve any real test message before one is sent.
4. Confirm shipping, returns, warranty, privacy and terms content, and provide approved product descriptions, images, prices, inventory and contact information.
5. Confirm production hosting/domain ownership, backup and rollback operators, service budget, monitoring recipients, and a written deployment window/approval.
