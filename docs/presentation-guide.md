# Presentation guide (about 20 minutes)

Requirement-by-requirement notes and the step-by-step demo script are in
[requirements-checklist.md](requirements-checklist.md). This page covers what to say.

## 1. Problem and approach (2 min)
- Today pantry restocking is manual. Items run out, nobody knows the stock level, and approvals happen over email.
- Goal: one flow from **request → inventory check → approval only when needed → supplier email → delivery → stock update**, with an AI assistant on top.
- Everything is one Power Platform solution, `PantrySupplyOrdering_SharePoint.zip`, built from source in this repository. It contains the canvas app, four flows, the Copilot agent and a site-address environment variable. The data is in SharePoint lists.

## 2. Architecture (3 min)
Show the diagram in [architecture.md](architecture.md). Key points:
- **SharePoint** site "Office Pantry" with five lists:
  - Pantry Items (the inventory);
  - Pantry Suppliers;
  - Pantry Orders;
  - Pantry Order Lines;
  - Pantry Approval History.

  They're linked by lookup columns.
- **Canvas app** for staff, approvers and pantry admins. A role switcher demonstrates each persona.
- **Four cloud flows:**
  - approval, triggered when an order is Submitted;
  - supplier email, triggered when an order is Approved;
  - daily low-stock alert at 8 AM;
  - a one-time setup flow that builds the site, lists and sample data.
- **Copilot Studio agent** with read-only SharePoint tools.

## 3. Live demo (10–12 min)
Follow the demo script in [requirements-checklist.md](requirements-checklist.md#demo-script-about-10-minutes). Highlight:
- **Inventory in SharePoint:** show the Pantry Items list, and that receiving an order updates Current Stock there.
- **Inventory check:** well-stocked items are disabled, and the submit step re-checks live stock.
- **Approval preview** in the cart (green or amber), **enforced** by the flow.
- **Two paths:** an auto-approved small order versus a manager-approved large one.
- **Supplier email:** an automatic purchase order grouped by supplier.
- **Status tracker** and **approval history** on My requests.
- **Copilot:** "How many coffee pods are left?" and "When was the last order placed?"

## 4. Technical decisions (3 min)
- **The flow enforces the threshold.** The app only previews it. A user can't skip approval by changing the app, because the flow recalculates the total units from the order lines on the server.
- **Inventory check happens twice:**
  - in the UI (buttons disabled);
  - again at submit against the live Pantry Items list, because the app's cached stock can be stale.
- **Trigger conditions** on "When an item is created or modified": the approval flow only runs for Submitted orders with no approval status yet. Its first action sets the status to Pending, so it never re-triggers itself.
- **Standard SharePoint actions only** in the order flows (Get items, Get item, Create item, Update item), so they pass the tenant's DLP policy, which blocks "Send an HTTP request to SharePoint".
- **Infrastructure as a flow.** The setup flow creates the site, lists, columns (including lookups) and sample data, and is safe to re-run. The site address is an **environment variable** for test and production.
- **Approvals connector** instead of custom emails. The manager can approve from Outlook, Teams or the Power Automate app, and gets reminders and reassignment for free.
- **Audit trail.** Every submit and decision writes a Pantry Approval History item, and SharePoint version history records every change.
- **Canvas app built from source.** The `Src/*.pa.yaml` files are generated from `generate_screens.py`, a small Fluent 2 design system:
  - modern controls and responsive auto-layout;
  - labels with AutoHeight;
  - accessible labels.

  `validate_app.py` checks every property against Microsoft's documentation and lays the screens out at 1280, 1366 and 1920 pixels wide.
- **Delegation.** Order galleries filter SharePoint on the server: equality on text, choice and lookup Id, plus StartsWith. The item catalog is cached in a collection for instant search. It stays far below the 2,000-row limit.

## 5. Security (2 min)
See [security-considerations.md](security-considerations.md). Summary:
- SharePoint site permissions: **Members** request; **Owners** (office manager, pantry admins) approve and manage stock.
- Optional item-level permissions so requesters only see their own orders.
- Server-side enforcement: approval limits in the flow, and an inventory re-check against live data.
- Connection references bound to a service account. The Copilot agent's tools run as the end user.

## 6. Improvements and scalability (2 min)
- **Single source for the limits:** move the approval limits into environment variables, read by both the flow and the app.
- **Real roles:** replace the demo role switcher with a check of SharePoint group membership.
- **Approval timeout and escalation:** use the Approvals action's timeout to escalate to a backup approver after 48 hours.
- **Partial deliveries:** record the received quantity per line.
- **Teams:** publish the agent and app in a Teams channel, and post low-stock alerts there.
- **Analytics:** a Power BI report on the lists (spend per month, top items, supplier lead times).
- **Scale:** if order volume grows into tens of thousands of items, archive old orders, or move to Dataverse for richer security and relational queries. The app and flow logic carry over.

## Q&A prep
- **Why SharePoint?** It was the brief's requirement. It's already licensed with Microsoft 365, admins know it, and it's enough for an office pantry's volume.
- **What are SharePoint's limits?**
  - The 5,000-item list view threshold: the flows filter on the server and the lists are small.
  - Delegation: the app only uses delegable filters on large lists.
  - No row-level security by default: item-level permissions cover it.
- **What if two people request the same low item?** Both requests are allowed. Stock only changes when an order is received, and the approver sees both requests.
- **What if the approver never responds?** Today the approval waits up to the flow's 30-day limit and the Approvals app reminds the approver. Adding a timeout with escalation is listed under Improvements.
- **Why is there a short delay after submitting?** The SharePoint trigger checks for changes every minute. A Power Apps-triggered flow could start instantly if needed.
- **Licensing:** SharePoint, Outlook and Approvals are standard connectors, so most Microsoft 365 licences cover the app and flows. Copilot Studio is billed separately. Check current Microsoft pricing before quoting numbers.

## Checklist before the call
- [ ] Import `PantrySupplyOrdering_SharePoint.zip`.
- [ ] Run **Pantry - Create SharePoint site and lists**.
- [ ] Turn on the approval and supplier flows.
- [ ] Add the five lists to the app, then **Save** and **Publish**.
- [ ] Set your email in the flows' **Settings** steps. Optionally set one supplier's email to yours.
- [ ] Do a dry run of both demo orders (auto-approved and manager-approved).
- [ ] Publish the Copilot agent, and test the sample questions in its test pane.
- [ ] Prepare screenshots of each step in case the live demo fails.
