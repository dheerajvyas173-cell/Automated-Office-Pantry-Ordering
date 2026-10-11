# Automated Office Pantry Supply Ordering

A Power Platform solution that automates ordering coffee, snacks and supplies for the office cafeteria:
- a request app with an inventory check;
- approval only when an order is over the limits;
- automatic supplier emails;
- notifications;
- a Copilot agent for stock questions.

## Import (one file)
1. make.powerapps.com → **Solutions** → **Import solution** → `Step6_Copilot_Agent.zip`.
2. Choose your **Dataverse**, **Approvals** and **Office 365 Outlook** connections, then click **Import**.
3. Load the sample data from `dataverse/sample-data/` (see [sample-data.md](dataverse/sample-data.md)).
4. Open **Pantry Supply Ordering**. The five tables are already connected.
5. In each flow's **Settings** step, set the approver and pantry-admin email addresses.

## What it does
| Requirement | Solution |
|---|---|
| Request form plus inventory check | Canvas app: only items at or below their minimum stock level can be requested, and live stock is re-checked at submit |
| Approval above a threshold | Orders over ₹5,000 or 50 units go to the office manager (Approvals). Smaller ones are approved automatically |
| Supplier order automation | Approved orders are emailed to each supplier as a purchase order, then marked Ordered |
| Copilot agent | Stock levels, reorder guidance, last orders, supplier details |
| Notifications | Approval request, approved / rejected / auto-approved emails, daily 8 AM low-stock email |

The full notes are in [docs/requirements-checklist.md](docs/requirements-checklist.md). Note that inventory is stored in **Dataverse, not SharePoint**; the reasons are in Note 1 there.

## Docs
- [Requirements checklist and demo script](docs/requirements-checklist.md)
- [Architecture](docs/architecture.md)
- [Security](docs/security-considerations.md)
- [Presentation guide](docs/presentation-guide.md)

## Rebuilding from source
```
python3 power-apps/canvas-app/generate_screens.py     # app source (Src/*.pa.yaml)
python3 power-apps/canvas-app/validate_app.py         # property, enum and layout checks
PAC=/path/to/pac python3 power-apps/canvas-app/build_msapp.py
PAC=/path/to/pac python3 copilot-agent/build_agent.py
python3 solution/generate_solution.py                 # writes the Step ZIPs
```
