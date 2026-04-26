# Hamburger Method: Real-Time Chat Between Customers and Support Agents

## Feature Description

Implement a real-time chat feature between customers and support agents.

---

## Step 1: Identify Layers

The complete flow involves these functional layers:

1. **Customer initiates contact** — how a customer starts a conversation
2. **Route to agent** — how the message reaches the right support agent
3. **Message exchange** — how messages are sent and received
4. **Conversation persistence** — how messages are stored and retrievable
5. **Agent availability / status** — how the system knows if an agent can take the conversation
6. **Conversation resolution** — how a chat session ends and is closed

---

## Step 2: Options per Layer (4-5 each, manual → enterprise)

### Layer 1 — Customer Initiates Contact

- **1.1** Customer sends an email to support@company.com — agent replies manually
- **1.2** Customer fills a static HTML form; form data is emailed to a shared inbox
- **1.3** Customer clicks a "Chat with us" button that opens a pre-built chat widget (e.g., Crisp free tier, Tawk.to)
- **1.4** Custom chat widget embedded on the site, opens a WebSocket connection to the backend
- **1.5** Omnichannel entry: widget, WhatsApp, in-app SDK, all unified under one interface

### Layer 2 — Route to Agent

- **2.1** All chats go to one person (the only agent) — no routing needed
- **2.2** Chats land in a shared inbox; any agent picks them up manually
- **2.3** Round-robin assignment: backend assigns new chats to agents in order
- **2.4** Skill-based routing: assign based on topic/language/product area
- **2.5** AI-powered routing: classify intent and route to best available agent

### Layer 3 — Message Exchange

- **3.1** Exchange happens via email replies — no real-time component
- **3.2** Customer submits a form; agent replies via email; page polls every 30s for replies
- **3.3** Long-polling: client checks the server every few seconds for new messages
- **3.4** WebSocket connection for true bidirectional real-time messaging
- **3.5** WebSocket with presence indicators, typing indicators, read receipts, file attachments

### Layer 4 — Conversation Persistence

- **4.1** No persistence — conversation exists only in email thread or browser session
- **4.2** Messages stored in a single DB table (conversation_id, sender, text, timestamp)
- **4.3** Structured storage with conversation states (open, resolved, escalated)
- **4.4** Full conversation history, searchable, with attachments stored in object storage
- **4.5** Audit-grade storage: immutable log, compliance retention, GDPR-exportable

### Layer 5 — Agent Availability / Status

- **5.1** No status — agents just check the inbox when they feel like it
- **5.2** Agent manually sets a flag in a spreadsheet or Slack to say "I'm available"
- **5.3** Simple toggle in the agent dashboard: "online / offline"
- **5.4** Automatic status: agent goes offline after N minutes of inactivity
- **5.5** Real-time presence with capacity limits (max N concurrent chats per agent)

### Layer 6 — Conversation Resolution

- **6.1** No formal close — conversation just goes cold
- **6.2** Agent manually marks the email thread as resolved in their inbox
- **6.3** Agent clicks "Close chat" button; status set to resolved in DB
- **6.4** Auto-close after N hours of inactivity with customer notification
- **6.5** Resolution triggers CSAT survey, analytics update, SLA reporting

---

## Step 3: Force Radical Slicing

> **"If you had to ship something by tomorrow, what would you build?"**

Pick the lowest option from each layer that still forms a usable end-to-end flow:

| Layer | Pick | Description |
|---|---|---|
| 1 — Initiate contact | **1.2** | Static HTML form; submission emailed to shared inbox |
| 2 — Route to agent | **2.1** | One agent receives all; no routing logic needed |
| 3 — Message exchange | **3.1** | Email thread back-and-forth; no real-time transport |
| 4 — Persistence | **4.1** | Email thread IS the persistence; no DB needed |
| 5 — Agent availability | **5.1** | Agent checks inbox whenever available |
| 6 — Resolution | **6.2** | Agent archives/marks email thread as resolved |

**This slice requires zero new infrastructure.** No WebSockets, no Redis, no Kafka, no new database tables. It delivers value to a real customer (they get an answer) and to a real agent (they can respond) — today.

---

## Step 4: Filter & Prioritize

Options eliminated for the first slice:
- Everything requiring WebSocket infrastructure (3.4, 3.5) — too slow to set up
- Routing logic (2.3–2.5) — premature before knowing conversation volume
- Dedicated DB persistence (4.2–4.5) — email provides acceptable durability for slice 1
- Agent presence system (5.3–5.5) — unnecessary until multiple agents exist
- Auto-close / CSAT (6.4–6.5) — adds complexity with no immediate learning value

---

## Step 5: Smallest Vertical Slice (Slice 1)

**Name:** "Email-backed support contact form"

**What it is:**
A simple HTML form on the website (or product). Customer fills in name, email, and message. The form POSTs to a minimal backend endpoint that sends an email to the support team inbox. The agent replies from that inbox. The customer receives the reply by email.

**Who gets value:** Any customer who needs help gets a response. The support agent has a single, familiar inbox to work from.

**Decision it answers:** "Can customers reach a human and get a response?" — validated before investing in any chat infrastructure.

**Build time:** 2–4 hours (HTML form + one email-send endpoint + environment variable for the inbox address).

**Zero downtime risk:** Purely additive; nothing existing is changed.

**Testable in production:** Yes — send a test message yourself and verify the reply flow end-to-end.

---

## Step 6: Follow-Up Slices

**Slice 2 — Add a chat widget (upgrade Layer 1 + 3)**
Replace the static form with a free-tier hosted widget (Tawk.to, Crisp, or similar). Agents get a real-time notification when a customer opens a chat. No backend code required for the transport layer. Adds genuine real-time feel without building WebSocket infrastructure.
- Layers changed: 1.3, 3.3 (long-poll handled by the SaaS widget)
- Layers unchanged: routing still manual (2.1–2.2), persistence inside widget (4.2 provided by SaaS)
- Extra effort: ~1 day (account setup + embed script + test)

**Slice 3 — Store conversations in your own DB (upgrade Layer 4)**
Once volume grows, start persisting conversations in a simple `conversations` + `messages` table. This allows you to search history, build reporting, and eventually migrate away from the SaaS widget.
- Layers changed: 4.2 (your own DB)
- Prerequisite: Slice 2 is live and generating real data
- Extra effort: ~1–2 days

**Slice 4 — Add agent availability toggle (upgrade Layer 5) + shared inbox routing (upgrade Layer 2)**
Add an "online/offline" toggle to the agent dashboard so the widget can show "We're online / We're offline" to customers. Add a shared inbox view so multiple agents can see and claim open conversations.
- Layers changed: 5.3, 2.2
- Extra effort: ~2–3 days

---

## Self-Check

- [x] 3-6 clear functional layers identified (6 layers)
- [x] 4-5 options per layer following quality gradient
- [x] Radical slicing question explicitly asked and answered
- [x] Smallest vertical slice uses level 1-2 options from each layer
- [x] Smallest slice delivers value to a real user (customer gets support)
- [x] Smallest slice buildable in less than 1 day (2-4 hours)
- [x] **No new infrastructure required in Slice 1** (no WebSockets, no Redis, no message broker)
- [x] 3 follow-up slices proposed with clear incremental improvement
