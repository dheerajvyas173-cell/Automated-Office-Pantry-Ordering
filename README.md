# Automated Office Pantry Supply Ordering

A Power Platform solution that automates ordering coffee, snacks and supplies for the office cafeteria, with **inventory stored in SharePoint**. It provides:
- a request app with an inventory check;
- approval only when an order is over the limits;
- automatic supplier emails;
- notifications;
- a Copilot agent for stock questions.

## Set up (one file, a few clicks)
1. make.powerapps.com → **Solutions** → **Import solution** → `PantrySupplyOrdering_SharePoint.zip`.
2. Choose your **SharePoint**, **Approvals** and **Office 365 Outlook** connections. Keep the suggested site address, then click **Import**.
3. Run the flow **Pantry - Create SharePoint site and lists**. It creates the site, the five lists and the sample data.
4. Turn on **Pantry Order Approval** and **Pantry Supplier Order Email**.
5. Open **Pantry Supply Ordering** → **Edit** → **Data** → **Add data** → **SharePoint**, and add the five Pantry lists. Then **Save** and **Publish**.

Full steps and troubleshooting are in [solution/IMPORT-GUIDE.md](solution/IMPORT-GUIDE.md).

## What it does
| Requirement | Solution |
|---|---|
| Request form plus inventory check (SharePoint) | Canvas app over five SharePoint lists. Only items at or below their minimum stock level can be requested, and live stock is re-checked at submit |
| Approval above a threshold | Orders over ₹5,000 or 50 units go to the office manager (Approvals). Smaller ones are approved automatically |
| Supplier order automation | Approved orders are emailed to each supplier as a purchase order, then marked Ordered |
| Copilot agent | Stock levels, reorder guidance, last orders, supplier details, read from the lists |
| Notifications | Approval request, approved / rejected / auto-approved emails, daily 8 AM low-stock email |

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
python3 solution/generate_solution.py                 # writes PantrySupplyOrdering_SharePoint.zip
```

The earlier Dataverse edition is in the git history (up to commit "Stop shipping Dataverse tables inside the canvas app").
