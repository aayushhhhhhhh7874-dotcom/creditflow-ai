# CreditFlow AI Implementation Guide

## Selected Challenge

This project implements **Task 2: Finance Credit Follow-Up Email Agent** from the AI Enablement Internship brief.

The goal is to support a finance team by automatically preparing professional follow-up emails for overdue invoices while keeping every action auditable and safe. The prototype includes a professional login screen, SQLite database support, and dry-run mode so no real emails are sent during demonstration.

## End-To-End Flow

1. Finance exports pending invoices to `sample_data/invoices.csv`.
2. The agent can seed `data/creditflow.db` from the CSV using `--init-db`.
3. The agent validates required fields: invoice number, client, amount, due date, contact email, follow-up count, risk level, and payment link.
4. The trigger logic calculates days overdue from the selected run date.
5. The escalation engine maps each invoice to the mandatory matrix:
   - 1-7 days: warm and friendly
   - 8-14 days: polite but firm
   - 15-21 days: formal and serious
   - 22-30 days: stern and urgent
   - 30+ days: flag for legal/finance review only
6. The email generator creates a personalised subject and body using source data.
7. The dry-run adapter writes `outputs/email_audit_log.jsonl` and, when `--use-db` is enabled, records generated emails and audit events in SQLite.
8. The dashboard visualises the secure login, queue, generated emails, database layer, and security controls.

## How To Run

```bash
python src/credit_followup_agent.py --input sample_data/invoices.csv --today 2026-05-11 --dry-run
```

Database-backed demo:

```bash
python src/credit_followup_agent.py --init-db --use-db --input sample_data/invoices.csv --today 2026-05-11 --dry-run
```

Expected summary:

```text
Loaded overdue records: 5
Generated dry-run emails: 4
Flagged for manual review: 1
Audit log written to: outputs/email_audit_log.jsonl
```

Open `index.html` in a browser to show the demo dashboard.

## Important Files

- `index.html` - professional dashboard.
- `style.css` - responsive visual design.
- `script.js` - browser-side demo data, queue filtering, and email previews.
- `src/credit_followup_agent.py` - runnable Python agent.
- `sample_data/invoices.csv` - mock finance records.
- `outputs/email_audit_log.jsonl` - sample generated output.
- `database_schema.sql` - SQLite table design for users, invoices, generated emails, and audit events.
- `.env.example` - safe configuration template.
- `README.md` - final submission documentation.

The root-level `credit_followup_agent.py`, `invoices.csv`, and `email_audit_log.jsonl` are kept as convenient copies for quick inspection. The `src/`, `sample_data/`, and `outputs/` folders are the canonical submission layout.

## Demo Script

1. Start on the hero section and explain the business problem: overdue payment follow-ups are repetitive and inconsistent.
2. Sign in with the demo finance manager account.
3. Show the queue table, stage filter, and risk filter.
4. Click through generated email previews to show personalisation and realistic email addresses.
5. Point out that the 30+ day invoice is flagged instead of emailed.
6. Run the SQLite-backed Python command and open the audit log.
7. Finish with the database and security sections.

## Production Upgrade Path

- Replace deterministic templates with an LLM call that returns validated JSON.
- Add SMTP, SendGrid, or Mailgun behind a dry-run flag.
- Replace demo browser authentication with a server-side identity provider, password hashing, MFA, HTTPS-only cookies, and RBAC.
- Move SQLite to Postgres or a finance operations database for multi-user production use.
- Add scheduler support with GitHub Actions, APScheduler, or Celery.
