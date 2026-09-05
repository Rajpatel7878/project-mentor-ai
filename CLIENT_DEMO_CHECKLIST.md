# 5-Minute Client Demonstration Checklist

This playbook provides a structured, high-impact demonstration script to showcase **Project Mentor AI** to prospective clients, executives, or technical stakeholders.

---

## Pre-Flight Checklist (2 Minutes Before Demo)
- [ ] Run `start.bat` (or verify Docker containers with `docker-compose up -d`)
- [ ] Confirm Web UI is accessible at `http://localhost:3000`
- [ ] Ensure computer volume is unmuted (to demonstrate JARVIS voice synthesis and audio chimes)
- [ ] Open the **Cost & ROI** tab and click **"Reset Metrics"** so counters start from zero

---

## 5-Minute Live Demonstration Flow

### Minute 1: The JARVIS Experience & System Telemetry
**Goal:** Hook the client immediately with the futuristic, responsive interface.
1. Navigate to the **Assistant Core** tab (`http://localhost:3000`).
2. Point out the holographic particle backdrop, glassmorphism UI, and real-time connection indicator (**SYSTEMS ONLINE**).
3. Demonstrate voice interaction:
   - Click the microphone icon or say: *"Hey Mentor, what is our operational status today?"*
   - Point out the time-aware proactive greeting and audio chime feedback.
4. Click on the **DEVICES & IOT** tab:
   - Show live CPU & RAM hardware telemetry streaming from the host workstation.
   - Click to adjust the Smart Lighting brightness or HVAC thermostat, highlighting real-time state synchronization.

---

### Minute 2: Dynamic Multi-Agent Routing in Action
**Goal:** Prove that Project Mentor AI is not a single generic bot, but a specialized executive council.
1. Return to the **Assistant Core** tab.
2. Ask an architectural question:
   - Type or say: *"How should we design a low-latency caching layer for our Postgres database?"*
   - **Show:** The agent badge changes automatically to **CTO**, with cyan branding and deep architectural recommendations.
3. Next, ask a fundraising/investor question:
   - Type or say: *"What metrics will a Tier-1 VC look for in our Series A pitch deck?"*
   - **Show:** The system dynamically routes to the **VC** agent, prioritizing LTV/CAC ratios, net retention, and runway analysis.
4. Point out the zero-latency contextual follow-up chips below each response.

---

### Minute 3: Enterprise Document RAG (Zero-Hallucination Grounding)
**Goal:** Demonstrate enterprise document retrieval without cloud subscription lock-in.
1. Click the **KNOWLEDGE (RAG)** tab.
2. Show the indexed documents (`architecture.md`, `devices.txt`, etc.) running on self-hosted **ChromaDB**.
3. In the search box, query: *"What communication protocols are supported for IoT hardware?"*
4. **Show:** Instant hybrid retrieval results citing exact chunk relevance scores and source files.
5. Emphasize to the client:
   > *"All document embeddings and vector searches run locally in your environment. Sensitive company SOPs and customer data never leave your infrastructure."*

---

### Minute 4: Client Intake & Architecture Recommendation
**Goal:** Align the product directly with the prospect's specific business bottleneck.
1. Click the **CLIENT INTAKE** tab.
2. Click the **"E-Commerce Customer Support"** preset (or type their custom problem statement).
3. Click **"Generate Solution Recommendation & ROI"**.
4. Review the generated blueprint with the client:
   - **Architecture Fit Score:** (e.g. 95% Match)
   - **Assigned Agents:** Highlight which specialized agents will be deployed.
   - **Financial ROI Card:**
     - Point out the monthly token estimate (e.g. 1.5M tokens).
     - Compare Gemini Flash cost (~$0.35/mo) against GPT-4 (~$15.00/mo).
     - Highlight the **97% recurring cost reduction**.
   - **Implementation Roadmap:** Walk through the 5-phase rollout schedule.

---

### Minute 5: Real-Time Usage & Cost Accounting Dashboard
**Goal:** Deliver complete financial and operational transparency.
1. Click the **COST & ROI** tab.
2. Show the live metrics that accumulated during the demonstration:
   - **Total Invocations:** Shows the exact number of queries processed.
   - **Tokens Processed:** Displays prompt vs. completion token split.
   - **Actual Cost (USD):** Shows sub-penny precision (e.g., `$0.000412 USD`).
   - **Estimated Savings:** Confirms the client saved ~97% versus GPT-4 enterprise pricing.
3. Scroll to the **Agent Persona Usage Breakdown** table:
   - Point out per-agent invocation counts, latency in milliseconds, and individual agent costs.
4. Conclude with:
   > *"With Project Mentor AI, your team gets full executive intelligence and device control with complete cost predictability and zero vendor lock-in."*

---

## Frequently Asked Client Questions & Answers

**Q: Can we add our own proprietary agents (e.g., Compliance, Healthcare, Underwriting)?**  
*A: Yes. The system uses a swappable `AgentRegistry`. Registering a new agent requires only defining an `AgentSpec` with a persona prompt and trigger keywords.*

**Q: What if our internet connection goes down or Google API is unreachable?**  
*A: The system automatically falls back to local storage (JSON memory fallback), local RAG search (ChromaDB), and local system commands.*

**Q: Does our data get trained on?**  
*A: No. Gemini API terms explicitly state that enterprise API requests are not used to train models, and all RAG vector indices reside on your private storage.*
