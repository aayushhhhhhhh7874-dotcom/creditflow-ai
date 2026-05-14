# CreditFlow AI

CreditFlow AI is a secure dry-run finance follow-up agent for overdue invoices. It includes a professional login screen, a dashboard for finance users, CSV and SQLite-backed invoice records, realistic business contact emails, and auditable JSONL/database logs without sending real email.

## Selected Internship Task

Task 2: Finance Credit Follow-Up Email Agent

## What It Demonstrates

- CSV ingestion and required-field validation.
- Optional SQLite database initialization and audit persistence.
- Deterministic trigger logic for overdue invoices.
- Escalation-aware subject and body generation.
- 30+ day invoices flagged for manual finance/legal review.
- Dry-run audit logging with masked contact emails.
- Secure-looking browser dashboard with login, role display, queue filters, generated email review, database status, and security controls.

## Project Structure

```text
.
+-- index.html
+-- style.css
+-- script.js
+-- src/
|   +-- credit_followup_agent.py
+-- sample_data/
|   +-- invoices.csv
+-- outputs/
|   +-- email_audit_log.jsonl
+-- database_schema.sql
+-- requirements.txt
+-- .env.example
+-- PROJECT_IMPLEMENTATION_GUIDE.md
```

Root-level copies of the agent, sample CSV, and audit log are included for quick inspection. The foldered layout above is the canonical submission layout.

## Run The Agent

Install dependencies if needed:

```bash
pip install -r requirements.txt
```

Run a repeatable dry-run demo:

```bash
python src/credit_followup_agent.py --input sample_data/invoices.csv --today 2026-05-11 --dry-run
```

Run the database-backed version:

```bash
python src/credit_followup_agent.py --init-db --use-db --input sample_data/invoices.csv --today 2026-05-11 --dry-run
```

Expected output:

```text
Loaded overdue records: 5
Generated dry-run emails: 4
Flagged for manual review: 1
Audit log written to: outputs/email_audit_log.jsonl
```

Open `index.html` in a browser to view the dashboard. Demo login:

```text
Email: finance.manager@creditflow.in
Password: Demo@2026!
```

## Escalation Matrix

| Days overdue | Action |
| --- | --- |
| 1-7 | Warm, friendly reminder |
| 8-14 | Polite but firm payment confirmation |
| 15-21 | Formal follow-up with 48-hour response request |
| 22-30 | Stern final notice before escalation |
| 30+ | Manual finance/legal review only |

## Safety Notes

This prototype is dry-run first. It does not send emails, stores only masked contact emails in the audit log, and uses deterministic templates so invoice data cannot override system behavior. The browser login is a demo experience; production use should move authentication server-side with hashed passwords, HTTPS-only cookies, MFA, CSRF protection, sender-domain controls, role-based approvals, and a reviewed email transport such as SendGrid, Mailgun, or SMTP.
