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
