# Hamburger Method: Real-Time Chat Between Customers and Support Agents

Let's apply the Hamburger Method to slice this feature into small, deliverable vertical pieces.

---

## First: A Critical Question Before We Start

Before identifying layers, we need to challenge the core assumption embedded in this request.

**"Real-time" is an implementation detail, not a user need.**

The user need is: **"A customer can get help from a support agent."**

Real-time delivery is ONE way to satisfy that need — but it is not the only way, and it is expensive to build correctly. WebSockets, presence detection, message queues, and connection management add significant complexity.

**Ask yourself:** Can we validate that customers actually want to communicate with support agents via chat — before investing in real-time infrastructure? Can we prove this channel generates value before scaling it?

The answer is almost always yes. Let's structure the layers to reflect this.

---

## Layers Identified

The full chat flow decomposes into these 5 functional layers:

1. **Message Input** — Customer submits a message asking for help
2. **Message Routing / Delivery** — Message reaches a support agent
3. **Agent Response** — Agent reads the message and sends a reply
4. **Message Display** — Customer sees the agent's reply
5. **Conversation History / Persistence** — Messages are stored and retrievable

---

## Options Per Layer

### Layer 1 — Message Input (Customer submits a message)

- **1.1**: Customer fills out a static HTML form and submits it by email (no JS, no database)
- **1.2**: Customer fills out a web form that POSTs to a backend endpoint and stores in a database table
- **1.3**: Customer uses a chat widget (floating button) with a text input that sends messages via HTTP polling
- **1.4**: Customer uses a chat widget with WebSocket connection that sends messages in real-time
- **1.5**: Customer uses a fully integrated chat widget with typing indicators, file uploads, and rich text

### Layer 2 — Message Routing / Delivery (Message reaches a support agent)

- **2.1**: Form submission triggers an email to a shared support inbox (support@company.com) — agent checks email manually
- **2.2**: Message is stored in a database; a cron job emails a digest of new messages every 15 minutes to the support team
- **2.3**: Message is stored in a database; a webhook or email notification is sent immediately when a new message arrives
- **2.4**: Messages are queued in a job queue (e.g., Redis/Sidekiq); agents are assigned conversations automatically
- **2.5**: Messages flow through a real-time pub/sub broker (Kafka, Pusher, Ably) with intelligent routing, load balancing, and SLA tracking

### Layer 3 — Agent Response (Agent reads and replies)

- **3.1**: Agent replies by email — their email reply is manually copy-pasted into a database entry by a human operator
- **3.2**: Agent accesses a simple internal admin page (read-only list of messages), and replies via a plain text form on that page
- **3.3**: Agent accesses a basic internal dashboard showing open conversations and can type and submit replies
- **3.4**: Agent uses a purpose-built support interface with conversation assignment, status tracking, and canned responses
- **3.5**: Agent uses a full CRM-integrated tool (Intercom, Zendesk-like) with macros, tags, SLA timers, and team collaboration

### Layer 4 — Message Display (Customer sees the reply)

- **4.1**: Customer receives the reply via email to their inbox — no in-app display needed
- **4.2**: Customer visits a dedicated "check your support request" page and manually refreshes to see new replies
- **4.3**: Customer's chat widget polls the server every 5–10 seconds and displays new replies automatically
- **4.4**: Customer's chat widget uses long polling or Server-Sent Events (SSE) for near-real-time updates
- **4.5**: Customer's chat widget uses WebSockets for true real-time bidirectional communication with typing indicators

### Layer 5 — Conversation History / Persistence

- **5.1**: No persistence — conversation exists only in email threads (inbox is the record)
- **5.2**: Messages are stored in a single database table with customer ID, message text, and timestamp
- **5.3**: Full conversation model in the database (threads, messages, statuses: open/pending/resolved)
- **5.4**: Conversation history is surfaced to both customer (chat history) and agent (full timeline with metadata)
- **5.5**: Conversation history integrated with customer profile, with search, analytics, and export capabilities

---

## Filtering: What to Eliminate for Slice 1

Eliminate anything that:
- Requires new infrastructure (WebSocket server, Redis, Kafka, message brokers)
- Requires building a real-time connection layer
- Takes more than 1–2 days to deploy end-to-end
- Cannot be tested with a real customer interaction today

---

## Smallest Vertical Slice (Ship by Tomorrow)

**Slice 1: Email-Backed Chat Stub**

| Layer | Option | Implementation |
|-------|--------|----------------|
| Message Input | **1.2** | Web form that stores message in a database |
| Message Routing | **2.1** | Form submission sends email to shared support inbox |
| Agent Response | **3.1** | Agent replies via email; reply is manually entered into DB by operator |
| Message Display | **4.1** | Customer receives reply via email to their inbox |
| History | **5.2** | Messages stored in a single DB table for record-keeping |

**What this slice delivers:**
- A customer can submit a support request through the UI
- A support agent receives it in their existing email inbox (zero new tooling)
- The agent can reply, and the customer receives an answer
- The interaction is persisted for audit purposes

**What this slice does NOT need:**
- WebSockets
- Redis, Kafka, or any message broker
- A real-time connection layer
- A custom agent dashboard
- Presence/status indicators
- Polling or push notifications

**Why this slice is valid:**
This slice answers the most important question: **Do customers actually use this channel to get support?** If the answer is no — if customers don't submit messages, or agents don't respond, or the resolution rate is poor — then none of the real-time infrastructure would have been worth building. Validating the core interaction (customer asks, agent answers, customer gets help) before investing in real-time delivery is the correct sequencing.

**Estimated build time:** 4–8 hours for a developer familiar with the stack.

---

## Follow-Up Slices

### Slice 2: Self-Service Reply Checking (Eliminate email dependency for customers)

Upgrade Layer 4 from email reply to in-app polling:

- Layer 4: **4.3** — Customer's chat widget polls for new replies every 10 seconds
- Everything else stays the same
- Customer no longer needs to check their email inbox — replies appear in the chat widget automatically
- Still no WebSockets required

**Value:** Improves perceived responsiveness without real infrastructure cost.

---

### Slice 3: Dedicated Agent View (Eliminate manual email forwarding)

Upgrade Layers 2 and 3 to remove the human-operator bottleneck:

- Layer 2: **2.3** — Webhook sends an immediate Slack or email notification when a new message arrives
- Layer 3: **3.3** — Agent uses a basic internal dashboard to read messages and send replies directly
- Everything else stays the same
- No manual copy-paste needed; agents work from a single screen

**Value:** Removes the manual operator crutch, makes the system viable at moderate volume.

---

### Slice 4: Near-Real-Time Experience (Begin real-time investment only after validation)

Upgrade Layers 4 and 2 for near-real-time feel:

- Layer 2: **2.4** — Job queue for message delivery with agent assignment
- Layer 4: **4.4** — SSE (Server-Sent Events) for near-real-time display without WebSocket complexity
- Layer 5: **5.3** — Full conversation model with statuses

**Value:** Delivers the "real-time" feel that was in the original requirement — but only after validating that the channel generates value and that volume justifies the infrastructure investment.

---

## Self-Check

- [x] Identified 5 clear functional layers (not "frontend/backend/database")
- [x] Generated at least 4–5 options per layer with quality gradient
- [x] Options follow manual → scripted → automated → scalable → enterprise
- [x] Forced radical slicing: "ship by tomorrow" test applied
- [x] Smallest vertical slice uses level 1–2 options from each layer
- [x] Smallest slice delivers real value (customer gets help) to at least one real user
- [x] Smallest slice does NOT require WebSockets, Kafka, Redis, or real-time infrastructure
- [x] Explicitly challenged whether "real-time" is needed for Slice 1
- [x] Included manual/crutch option per layer (email inbox, manual copy-paste, page refresh)
- [x] Follow-up slices show clear incremental progression toward real-time

---

## Key Insight

The instinct when hearing "real-time chat" is to immediately reach for WebSockets, Redis pub/sub, and a message broker. This is the infrastructure-first trap. The Hamburger Method forces us to ask: **what is the smallest thing that validates whether customers and agents will actually use this channel?**

That answer is almost never "build WebSockets first." It is almost always: prove the interaction has value with email, polling, or manual steps — then invest in real-time infrastructure only once demand justifies the cost.
