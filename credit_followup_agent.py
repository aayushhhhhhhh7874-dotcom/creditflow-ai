from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

REQUIRED_FIELDS = {
    "invoice_no",
    "client_name",
    "company",
    "amount_due",
    "due_date",
    "contact_email",
    "follow_up_count",
    "payment_link",
}


@dataclass(frozen=True)
class InvoiceRecord:
    invoice_no: str
    client_name: str
    company: str
    amount_due: float
    due_date: date
    contact_email: str
    follow_up_count: int
    risk_level: str
    payment_link: str


@dataclass(frozen=True)
class EscalationStage:
    stage: str
    tone: str
    key_message: str
    cta: str
    should_send: bool


@dataclass(frozen=True)
class GeneratedEmail:
    invoice_no: str
    client_name: str
    company: str
    contact_email_masked: str
    amount_due: float
    due_date: str
    days_overdue: int
    risk_level: str
    stage: str
    tone: str
    subject: str
    body: str
    send_status: str
    timestamp: str


def parse_invoice(row: dict[str, str]) -> InvoiceRecord:
    missing = REQUIRED_FIELDS.difference(row)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    return InvoiceRecord(
        invoice_no=row["invoice_no"].strip(),
        client_name=row["client_name"].strip(),
        company=row["company"].strip(),
        amount_due=float(row["amount_due"]),
        due_date=datetime.strptime(row["due_date"].strip(), "%Y-%m-%d").date(),
        contact_email=row["contact_email"].strip(),
        follow_up_count=int(row["follow_up_count"]),
        risk_level=row.get("risk_level", "medium").strip() or "medium",
        payment_link=row["payment_link"].strip(),
    )


def load_records(path: Path) -> list[InvoiceRecord]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [parse_invoice(row) for row in reader]


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    mfa_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_no TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    company TEXT NOT NULL,
    amount_due REAL NOT NULL CHECK (amount_due >= 0),
    due_date TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    follow_up_count INTEGER NOT NULL DEFAULT 0 CHECK (follow_up_count >= 0),
    risk_level TEXT NOT NULL DEFAULT 'medium',
    payment_link TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS generated_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT NOT NULL REFERENCES invoices(invoice_no),
    contact_email_masked TEXT NOT NULL,
    days_overdue INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    stage TEXT NOT NULL,
    tone TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    send_status TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor_email TEXT NOT NULL,
    invoice_no TEXT,
    detail TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
"""


def init_database(db_path: Path, seed_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")
    records = load_records(seed_path)

    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            """
            INSERT INTO users (email, role, mfa_enabled, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET role=excluded.role, mfa_enabled=excluded.mfa_enabled
            """,
            ("finance.manager@creditflow.in", "Finance Manager", 1, now),
        )
        for record in records:
            connection.execute(
                """
                INSERT INTO invoices (
                    invoice_no, client_name, company, amount_due, due_date, contact_email,
                    follow_up_count, risk_level, payment_link, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(invoice_no) DO UPDATE SET
                    client_name=excluded.client_name,
                    company=excluded.company,
                    amount_due=excluded.amount_due,
                    due_date=excluded.due_date,
                    contact_email=excluded.contact_email,
                    follow_up_count=excluded.follow_up_count,
                    risk_level=excluded.risk_level,
                    payment_link=excluded.payment_link
                """,
                (
                    record.invoice_no,
                    record.client_name,
                    record.company,
                    record.amount_due,
                    record.due_date.isoformat(),
                    record.contact_email,
                    record.follow_up_count,
                    record.risk_level,
                    record.payment_link,
                    now,
                ),
            )
        connection.execute(
            """
            INSERT INTO audit_events (event_type, actor_email, detail, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            ("DATABASE_INITIALIZED", "finance.manager@creditflow.in", f"Seeded {len(records)} invoice records", now),
        )


def load_records_from_database(db_path: Path) -> list[InvoiceRecord]:
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT invoice_no, client_name, company, amount_due, due_date, contact_email,
                   follow_up_count, risk_level, payment_link
            FROM invoices
            ORDER BY due_date DESC
            """
        ).fetchall()
    return [
        InvoiceRecord(
            invoice_no=row["invoice_no"],
            client_name=row["client_name"],
            company=row["company"],
            amount_due=float(row["amount_due"]),
            due_date=datetime.strptime(row["due_date"], "%Y-%m-%d").date(),
            contact_email=row["contact_email"],
            follow_up_count=int(row["follow_up_count"]),
            risk_level=row["risk_level"],
            payment_link=row["payment_link"],
        )
        for row in rows
    ]


def mask_email(email: str) -> str:
    name, _, domain = email.partition("@")
    if not domain:
        return "masked"
    visible = name[:2] if len(name) > 2 else name[:1]
    return f"{visible}***@{domain}"


def currency(value: float) -> str:
    return f"INR {value:,.0f}"


def resolve_stage(days_overdue: int) -> EscalationStage:
    if days_overdue > 30:
        return EscalationStage("Escalation Flag", "Manual Legal Review", "Human review required; no auto email", "Assign to finance manager", False)
    if days_overdue >= 22:
        return EscalationStage("4th Follow-Up", "Stern & Urgent", "Final reminder before escalation", "Pay immediately or call us", True)
    if days_overdue >= 15:
        return EscalationStage("3rd Follow-Up", "Formal & Serious", "Escalating concern; mention impact", "Respond within 48 hours", True)
    if days_overdue >= 8:
        return EscalationStage("2nd Follow-Up", "Polite but Firm", "Payment still pending; request confirmation", "Confirm payment date", True)
    if days_overdue >= 1:
        return EscalationStage("1st Follow-Up", "Warm & Friendly", "Gentle reminder; assume oversight", "Pay now link / bank details", True)
    return EscalationStage("Not Due", "No Action", "Invoice is not overdue", "No action", False)


def generate_email(record: InvoiceRecord, today: date, dry_run: bool = True) -> GeneratedEmail:
    days = max(0, (today - record.due_date).days)
    stage = resolve_stage(days)
    amount = currency(record.amount_due)

    if stage.stage == "Escalation Flag":
        subject = f"Manual review required - {record.invoice_no} ({days} days overdue)"
        body = (
            f"Invoice {record.invoice_no} for {record.company} is {days} days overdue. "
            "The escalation cap has been reached, so no automatic email was generated. "
            "Assign this account to a finance manager for legal or recovery review."
        )
        status = "FLAGGED_FOR_REVIEW"
    elif stage.stage == "1st Follow-Up":
        subject = f"Quick Reminder - Invoice {record.invoice_no} | {amount} Due"
        body = (
            f"Hi {record.client_name},\n\n"
            f"I hope you are doing well. This is a friendly reminder that Invoice {record.invoice_no} "
            f"for {amount} was due on {record.due_date.isoformat()} and is currently {days} days overdue. "
            f"If payment has already been processed, please disregard this note. Otherwise, you can complete payment here: {record.payment_link}.\n\n"
            "Thank you,\nFinance Team"
        )
        status = "DRY_RUN_LOGGED" if dry_run else "READY_TO_SEND"
    elif stage.stage == "2nd Follow-Up":
        subject = f"Payment Confirmation Requested - Invoice {record.invoice_no}"
        body = (
            f"Dear {record.client_name},\n\n"
            f"Our records show that Invoice {record.invoice_no} for {amount}, due on {record.due_date.isoformat()}, "
            f"is still pending and is now {days} days overdue. Please confirm the expected payment date or complete payment here: {record.payment_link}.\n\n"
            "Regards,\nFinance Team"
        )
        status = "DRY_RUN_LOGGED" if dry_run else "READY_TO_SEND"
    elif stage.stage == "3rd Follow-Up":
        subject = f"IMPORTANT: Outstanding Payment - Invoice {record.invoice_no} ({days} Days Overdue)"
        body = (
            f"Dear {record.client_name},\n\n"
            f"Despite our previous reminders, Invoice {record.invoice_no} ({amount}) remains unpaid as of today, "
            f"now {days} days overdue. Continued non-payment may impact your credit terms. "
            f"Please respond within 48 hours or complete payment here: {record.payment_link}.\n\n"
            "Regards,\nFinance Team"
        )
        status = "DRY_RUN_LOGGED" if dry_run else "READY_TO_SEND"
    else:
        subject = f"FINAL NOTICE - Invoice {record.invoice_no} - Immediate Action Required"
        body = (
            f"Dear {record.client_name},\n\n"
            f"This is our final reminder. Invoice {record.invoice_no} ({amount}) was due on {record.due_date.isoformat()} "
            f"and is now {days} days overdue. Failure to remit payment within 24 hours may result in escalation to our legal and recovery team. "
            f"Please pay immediately using {record.payment_link} or contact finance support today.\n\n"
            "Regards,\nFinance Team"
        )
        status = "DRY_RUN_LOGGED" if dry_run else "READY_TO_SEND"

    return GeneratedEmail(
        invoice_no=record.invoice_no,
        client_name=record.client_name,
        company=record.company,
        contact_email_masked=mask_email(record.contact_email),
        amount_due=record.amount_due,
        due_date=record.due_date.isoformat(),
        days_overdue=days,
        risk_level=record.risk_level,
        stage=stage.stage,
        tone=stage.tone,
        subject=subject,
        body=body,
        send_status=status,
        timestamp=datetime.now().isoformat(timespec="seconds"),
    )


def write_audit_log(emails: Iterable[GeneratedEmail], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for email in emails:
            handle.write(json.dumps(asdict(email), ensure_ascii=False) + "\n")


def write_database_outputs(emails: Iterable[GeneratedEmail], db_path: Path) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as connection:
        connection.execute("DELETE FROM generated_emails")
        for email in emails:
            connection.execute(
                """
                INSERT INTO generated_emails (
                    invoice_no, contact_email_masked, days_overdue, risk_level, stage, tone,
                    subject, body, send_status, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    email.invoice_no,
                    email.contact_email_masked,
                    email.days_overdue,
                    email.risk_level,
                    email.stage,
                    email.tone,
                    email.subject,
                    email.body,
                    email.send_status,
                    email.timestamp,
                ),
            )
            connection.execute(
                """
                INSERT INTO audit_events (event_type, actor_email, invoice_no, detail, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "EMAIL_DRY_RUN_LOGGED",
                    "finance.manager@creditflow.in",
                    email.invoice_no,
                    f"{email.stage}: {email.send_status}",
                    now,
                ),
            )


def run_agent(
    input_path: Path,
    output_path: Path,
    today: date,
    dry_run: bool,
    use_db: bool = False,
    db_path: Path | None = None,
) -> list[GeneratedEmail]:
    records = load_records_from_database(db_path) if use_db and db_path else load_records(input_path)
    overdue = [record for record in records if (today - record.due_date).days > 0]
    emails = [generate_email(record, today=today, dry_run=dry_run) for record in overdue]
    write_audit_log(emails, output_path)
    if use_db and db_path:
        write_database_outputs(emails, db_path)
    return emails


def main() -> None:
    parser = argparse.ArgumentParser(description="Finance credit follow-up email agent")
    parser.add_argument("--input", default="sample_data/invoices.csv", type=Path)
    parser.add_argument("--output", default="outputs/email_audit_log.jsonl", type=Path)
    parser.add_argument("--db", default="data/creditflow.db", type=Path)
    parser.add_argument("--today", default=date.today().isoformat(), help="YYYY-MM-DD; use this for repeatable demos")
    parser.add_argument("--dry-run", action="store_true", help="Log emails without sending")
    parser.add_argument("--init-db", action="store_true", help="Create the SQLite database and seed it from the input CSV")
    parser.add_argument("--use-db", action="store_true", help="Read invoices from SQLite and write generated email records")
    args = parser.parse_args()

    today = datetime.strptime(args.today, "%Y-%m-%d").date()
    if args.init_db:
        init_database(args.db, args.input)
    emails = run_agent(args.input, args.output, today=today, dry_run=args.dry_run, use_db=args.use_db, db_path=args.db)
    send_count = sum(1 for email in emails if email.send_status != "FLAGGED_FOR_REVIEW")
    flag_count = sum(1 for email in emails if email.send_status == "FLAGGED_FOR_REVIEW")

    print(f"Loaded overdue records: {len(emails)}")
    print(f"Generated dry-run emails: {send_count}")
    print(f"Flagged for manual review: {flag_count}")
    print(f"Audit log written to: {args.output}")


if __name__ == "__main__":
    main()
