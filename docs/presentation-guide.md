# Presentation guide (about 20 minutes)

Requirement-by-requirement notes and the step-by-step demo script are in
[requirements-checklist.md](requirements-checklist.md). This page covers what to say.

## 1. Problem and approach (2 min)
- Today pantry restocking is manual. Items run out, nobody knows the stock level, and approvals happen over email.
- Goal: one flow from **request → inventory check → approval only when needed → supplier email → delivery → stock update**, with an AI assistant on top.
- Everything is one Power Platform solution, `Step6_Copilot_Agent.zip`, built from source in this repository. It contains the tables, security roles, flows, canvas app and Copilot agent.

## 2. Architecture (3 min)
Show the diagram in [architecture.md](architecture.md). Key points:
- **Dataverse** holds five tables: Pantry Items, Suppliers, Supply Orders, Order Line Items and Approval History.
- **Canvas app** for staff, approvers and pantry admins. A role switcher demonstrates each persona.
- **Three cloud flows:**
  - approval, triggered on Submitted;
  - supplier email, triggered on Approved;
  - daily low-stock alert at 8 AM.
- **Copilot Studio agent** with read-only Dataverse tools.

**SharePoint deviation (say it before they ask).** The brief says SharePoint. I chose Dataverse for:
- per-user security (requesters see only their own orders);
- real lookups between orders, lines, items and suppliers;
- server-side filtering without list thresholds;
- packaging everything in one solution.

Switching to SharePoint means swapping five tables for five lists. The app and flow logic stay the same.

## 3. Live demo (10–12 min)
Follow the demo script in [requirements-checklist.md](requirements-checklist.md#demo-script-about-10-minutes). Highlight:
- **Inventory check:** well-stocked items are disabled, and the submit step re-checks live stock.
- **Approval preview** in the cart (green or amber), **enforced** by the flow.
- **Two paths:** an auto-approved small order versus a manager-approved large one.
- **Supplier email:** an automatic purchase order grouped by supplier.
- **Status tracker** and **approval history** on My requests.
- **Copilot:** "How many coffee pods are left?" and "When was the last order placed?"

## 4. Technical decisions (3 min)
- **The flow enforces the threshold.** The app only previews it. A user can't skip approval by changing the app, because the decision happens in Power Automate on the server.
- **Inventory check happens twice:**
  - in the UI (buttons disabled);
  - again at submit against live Dataverse data, because the app's cached stock can be stale.
- **Approvals connector** instead of custom emails. The manager can approve from Outlook, Teams or the Power Automate app, and gets reminders and reassignment for free.
- **Audit trail.** Every submit and decision writes an Approval History row: who, when, comments, and the old and new status.
- **Connection references.** The flows use connection references (Dataverse, Approvals, Outlook), so the solution imports into any environment with the user's own connections.
- **Canvas app built from source.** The `Src/*.pa.yaml` files are generated from `generate_screens.py`, a small Fluent 2 design system:
  - modern controls and responsive auto-layout;
  - labels with AutoHeight;
  - accessible labels.

  `validate_app.py` checks every property against Microsoft's documentation and lays the screens out at 1280, 1366 and 1920 pixels wide to catch overlap and clipping.
- **Delegation.** Galleries filter Dataverse on the server. Only the item catalog, about 2,000 rows at most, is cached in a collection for instant search.

## 5. Security (2 min)
See [security-considerations.md](security-considerations.md). Summary:
- **Three security roles:**
  - **Pantry Requester:** creates and reads only their own orders.
  - **Pantry Approver:** reads all orders and updates their status.
  - **Pantry Admin:** full access, including stock edits.
- **Server-side enforcement.** Dataverse privileges and the approval flow, not app visibility rules. (The role switcher in the app is a demo convenience. In production the app reads the user's real security role. See Improvements.)
- The flows run with connection references owned by a service account. Email goes only to known supplier addresses stored in Dataverse.
- Suggest a DLP policy that keeps Dataverse, Approvals and Outlook in the Business group.

## 6. Improvements and scalability (2 min)
- **Single source for the limits:** move the approval limits into Dataverse **environment variables**, read by both the flow and the app.
- **Real roles:** replace the demo role switcher with a check of the user's Dataverse security role or Entra ID group.
- **Approval timeout and escalation:** use the Approvals action's timeout to escalate to a backup approver after 48 hours.
- **Partial deliveries:** record the received quantity per line (the "Partially Received" status already exists).
- **Teams:** publish the agent and app to a Teams channel, and post low-stock alerts there.
- **Analytics:** a Power BI report on spend per month, top items and supplier lead times.
- **Scale out:** add a Location table to support several offices, with location-scoped security.
- **Predictive reordering:** use AI Builder to predict when items will run out from consumption history.

## Q&A prep
- **What if two people request the same low item?** Both requests are allowed. Stock only changes when an order is received, and the approver sees both requests.
- **What if the approver never responds?** Today the approval waits up to the flow's 30-day limit and the Approvals app reminds the approver. Adding a timeout with escalation is listed under Improvements.
- **How do you change the limits?** Today, in the flow's Settings step and the app formulas, which must match. The next step is environment variables.
- **Why not a model-driven app?** Staff need a simple, guided request flow. A model-driven app suits back-office administration and could be added for admins.
- **Licensing:** Dataverse and premium connectors need Power Apps / Power Automate premium (or per-app) licences, and Copilot Studio is billed by messages. Check current Microsoft pricing before quoting numbers.

## Checklist before the call
- [ ] Import `Step6_Copilot_Agent.zip`, and check that the three flows are **On** and their connections are green.
- [ ] Load the sample data (`dataverse/sample-data/`).
- [ ] Open the app once, and set yourself as approver and admin (the flows' **Settings** step).
- [ ] Do a dry run of both demo orders (auto-approved and manager-approved).
- [ ] Publish the Copilot agent, and test the sample questions in its test pane.
- [ ] Prepare screenshots of each step in case the live demo fails.
