const DEMO_USER = {
  email: "finance.manager@creditflow.in",
  password: "Demo@2026!",
  role: "Finance Manager"
};

const invoices = [
  {
    client: "Rajesh Kapoor",
    company: "Kapoor Retail Pvt Ltd",
    invoice: "INV-2026-001",
    amount: 45000,
    dueDate: "2026-05-07",
    email: "accounts.payable@kapoorretail.in",
    followUps: 0,
    risk: "low",
    paymentLink: "https://pay.creditflow.in/invoices/INV-2026-001"
  },
  {
    client: "Ananya Mehta",
    company: "Mehta Design Studio LLP",
    invoice: "INV-2026-014",
    amount: 78500,
    dueDate: "2026-04-30",
    email: "finance@mehtadesignstudio.in",
    followUps: 1,
    risk: "medium",
    paymentLink: "https://pay.creditflow.in/invoices/INV-2026-014"
  },
  {
    client: "Vikram Sinha",
    company: "Sinha Logistics Pvt Ltd",
    invoice: "INV-2026-022",
    amount: 132000,
    dueDate: "2026-04-22",
    email: "billing@sinhagroup.co.in",
    followUps: 2,
    risk: "high",
    paymentLink: "https://pay.creditflow.in/invoices/INV-2026-022"
  },
  {
    client: "Priya Nair",
    company: "Nair Foods Exporters",
    invoice: "INV-2026-031",
    amount: 26800,
    dueDate: "2026-04-14",
    email: "payments@nairfoods.in",
    followUps: 3,
    risk: "high",
    paymentLink: "https://pay.creditflow.in/invoices/INV-2026-031"
  },
  {
    client: "Arjun Rao",
    company: "Rao Infra Works Pvt Ltd",
    invoice: "INV-2026-044",
    amount: 214500,
    dueDate: "2026-04-05",
    email: "arjun.rao@raoinfraworks.in",
    followUps: 4,
    risk: "critical",
    paymentLink: "https://pay.creditflow.in/invoices/INV-2026-044"
  }
];

const today = new Date("2026-05-11T00:00:00+05:30");
const loginScreen = document.getElementById("loginScreen");
const appShell = document.getElementById("appShell");
const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");
const logoutButton = document.getElementById("logoutButton");
const stageFilter = document.getElementById("stageFilter");
const riskFilter = document.getElementById("riskFilter");
const invoiceRows = document.getElementById("invoiceRows");
const emailList = document.getElementById("emailList");
const emailPreview = document.getElementById("emailPreview");
const terminalOutput = document.getElementById("terminalOutput");
const runAgentButton = document.getElementById("runAgentButton");

let failedAttempts = 0;

function currency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(value);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;"
  })[char]);
}

function daysOverdue(dueDate) {
  const due = new Date(`${dueDate}T00:00:00+05:30`);
  return Math.max(0, Math.round((today - due) / 86400000));
}

function stageFor(days) {
  if (days > 30) return { key: "legal", label: "Manual review", tone: "Legal Review", cta: "Assign to finance manager" };
  if (days >= 22) return { key: "4", label: "Stage 4", tone: "Stern & Urgent", cta: "Pay within 24 hours or call finance" };
  if (days >= 15) return { key: "3", label: "Stage 3", tone: "Formal & Serious", cta: "Respond within 48 hours" };
  if (days >= 8) return { key: "2", label: "Stage 2", tone: "Polite but Firm", cta: "Confirm payment date" };
  return { key: "1", label: "Stage 1", tone: "Warm & Friendly", cta: "Use secure payment link" };
}

function emailFor(record) {
  const days = daysOverdue(record.dueDate);
  const stage = stageFor(days);
  if (stage.key === "legal") {
    return {
      record,
      stage,
      subject: `Manual review required - ${record.invoice} (${days} days overdue)`,
      body: `No automatic email was generated because ${record.invoice} is ${days} days overdue. Assign ${record.company} to a finance manager for legal or recovery review before any customer contact.`,
      status: "Flagged for review"
    };
  }

  const common = `Invoice ${record.invoice} for ${currency(record.amount)} was due on ${record.dueDate} and is currently ${days} days overdue.`;
  const bodies = {
    "1": `Hi ${record.client},\n\nI hope you are doing well. This is a friendly reminder that ${common} If payment has already been processed, please disregard this note. Otherwise, you can complete payment through our secure portal: ${record.paymentLink}.\n\nThank you,\nCreditFlow Finance Team`,
    "2": `Dear ${record.client},\n\nOur records show that ${common} Please confirm the expected payment date or complete payment using this secure link: ${record.paymentLink}.\n\nRegards,\nCreditFlow Finance Team`,
    "3": `Dear ${record.client},\n\nDespite our previous reminders, ${common} Continued delay may affect your credit terms with us. Please respond within 48 hours with payment confirmation or complete payment here: ${record.paymentLink}.\n\nRegards,\nCreditFlow Finance Team`,
    "4": `Dear ${record.client},\n\nThis is a final reminder that ${common} Failure to remit payment within 24 hours may result in escalation to our legal and recovery team. Please pay immediately using ${record.paymentLink} or contact finance support today.\n\nRegards,\nCreditFlow Finance Team`
  };
  const subjects = {
    "1": `Quick Reminder - ${record.invoice} | ${currency(record.amount)} Due`,
    "2": `Payment Confirmation Requested - ${record.invoice}`,
    "3": `IMPORTANT: Outstanding Payment - ${record.invoice} (${days} Days Overdue)`,
    "4": `FINAL NOTICE - ${record.invoice} - Immediate Action Required`
  };
  return { record, stage, subject: subjects[stage.key], body: bodies[stage.key], status: "Dry-run logged" };
}

const generated = invoices.map(emailFor);

function openDashboard() {
  loginScreen.classList.add("is-hidden");
  appShell.classList.remove("is-hidden");
  renderMetrics();
  renderQueue();
  renderEmails();
  animateTerminal();
}

function renderMetrics() {
  const overdue = invoices.filter((item) => daysOverdue(item.dueDate) > 0);
  const emails = generated.filter((item) => item.stage.key !== "legal");
  const escalated = generated.filter((item) => item.stage.key === "legal");
  const amount = overdue.reduce((sum, item) => sum + item.amount, 0);
  document.getElementById("metricOverdue").textContent = overdue.length;
  document.getElementById("metricEmails").textContent = emails.length;
  document.getElementById("metricEscalated").textContent = escalated.length;
  document.getElementById("metricAmount").textContent = currency(amount);
}

function renderQueue() {
  const selectedStage = stageFilter.value;
  const selectedRisk = riskFilter.value;
  invoiceRows.innerHTML = "";

  generated
    .filter((item) => selectedStage === "all" || item.stage.key === selectedStage)
    .filter((item) => selectedRisk === "all" || item.record.risk === selectedRisk)
    .forEach((item) => {
      const row = document.createElement("tr");
      const days = daysOverdue(item.record.dueDate);
      row.innerHTML = `
        <td><strong>${escapeHtml(item.record.company)}</strong><small>${escapeHtml(item.record.client)}</small></td>
        <td>${escapeHtml(item.record.invoice)}</td>
        <td>${escapeHtml(item.record.email)}</td>
        <td>${currency(item.record.amount)}</td>
        <td>${days}</td>
        <td><span class="badge risk-${item.record.risk}">${escapeHtml(item.record.risk)}</span></td>
        <td><span class="badge ${item.stage.key === "legal" ? "legal" : `stage-${item.stage.key}`}">${escapeHtml(item.stage.label)} - ${escapeHtml(item.stage.tone)}</span></td>
        <td><span class="badge ${item.stage.key === "legal" ? "flagged" : "sent"}">${escapeHtml(item.status)}</span></td>`;
      invoiceRows.appendChild(row);
    });
}

function renderEmails(activeIndex = 0) {
  emailList.innerHTML = "";
  generated.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = index === activeIndex ? "active" : "";
    button.innerHTML = `
      <strong>${escapeHtml(item.record.invoice)}</strong>
      <span>${escapeHtml(item.record.company)}</span>
      <small>${escapeHtml(item.stage.tone)} - ${escapeHtml(item.record.email)}</small>`;
    button.addEventListener("click", () => renderEmails(index));
    emailList.appendChild(button);
  });

  const item = generated[activeIndex];
  emailPreview.innerHTML = `
    <div class="email-header">
      <span>To: ${escapeHtml(item.record.email)}</span>
      <span>From: collections@creditflow.in</span>
    </div>
    <div class="subject">${escapeHtml(item.subject)}</div>
    ${item.body.split("\n\n").map((para) => `<p>${escapeHtml(para).replaceAll("\n", "<br>")}</p>`).join("")}
    <div class="meta">
      <span class="badge ${item.stage.key === "legal" ? "legal" : `stage-${item.stage.key}`}">${escapeHtml(item.stage.tone)}</span>
      <span class="badge ${item.stage.key === "legal" ? "flagged" : "sent"}">${escapeHtml(item.status)}</span>
      <span class="badge stage-1">CTA: ${escapeHtml(item.stage.cta)}</span>
    </div>`;
}

function animateTerminal() {
  const lines = [
    "$ python src/credit_followup_agent.py --init-db --use-db --today 2026-05-11 --dry-run",
    "Authenticated role: Finance Manager",
    "Opened SQLite database: data/creditflow.db",
    "Loaded 5 overdue invoice records",
    "Resolved escalation: 4 emails queued, 1 manual review flagged",
    "Wrote generated email rows and audit events",
    "Dry-run complete: no emails were sent"
  ];
  terminalOutput.textContent = "";
  let i = 0;
  const timer = setInterval(() => {
    terminalOutput.textContent += `${lines[i]}\n`;
    i += 1;
    if (i >= lines.length) clearInterval(timer);
  }, 220);
}

loginForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (failedAttempts >= 3) {
    loginMessage.textContent = "Account locked for this demo session after repeated failures.";
    return;
  }

  const email = document.getElementById("loginEmail").value.trim().toLowerCase();
  const password = document.getElementById("loginPassword").value;
  const isValid = email === DEMO_USER.email && password === DEMO_USER.password;

  if (!isValid) {
    failedAttempts += 1;
    loginMessage.textContent = `Invalid credentials. ${3 - failedAttempts} attempt(s) remaining.`;
    return;
  }

  sessionStorage.setItem("creditflowSession", JSON.stringify({
    email: DEMO_USER.email,
    role: DEMO_USER.role,
    signedInAt: new Date().toISOString()
  }));
  openDashboard();
});

logoutButton.addEventListener("click", () => {
  sessionStorage.removeItem("creditflowSession");
  appShell.classList.add("is-hidden");
  loginScreen.classList.remove("is-hidden");
  loginMessage.textContent = "Signed out securely.";
});

stageFilter.addEventListener("change", renderQueue);
riskFilter.addEventListener("change", renderQueue);
runAgentButton.addEventListener("click", animateTerminal);

if (sessionStorage.getItem("creditflowSession")) {
  openDashboard();
}
