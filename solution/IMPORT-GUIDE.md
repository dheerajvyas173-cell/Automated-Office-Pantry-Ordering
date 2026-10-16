# Import guide (SharePoint edition)

`PantrySupplyOrdering_SharePoint.zip` (version 2.0.2.0) contains:
- the canvas app;
- four cloud flows, including the one that builds the SharePoint site;
- the Copilot agent;
- the **Pantry SharePoint site** environment variable.

All data lives in five SharePoint lists. There are no Dataverse tables.

## 1. Import (about 2 minutes)
1. make.powerapps.com → pick your environment → **Solutions** → **Import solution**.
2. Browse to `PantrySupplyOrdering_SharePoint.zip` → **Next**.
3. **Connections:** pick, or create, a connection for each:
   - **Pantry - SharePoint** (SharePoint)
   - **Pantry - Office 365 Outlook** (Office 365 Outlook)
4. **Environment variable "Pantry SharePoint site":** keep `https://dheerajvyas173gmail.sharepoint.com/sites/OfficePantry`, or enter another site address. The site doesn't need to exist yet.
5. **Import**.

## 2. Create the site, lists and sample data (one click)
The setup flow uses "Send an HTTP request to SharePoint", which some data loss prevention (DLP) policies block. It imports switched off. If your policy blocks it, create the lists by hand using the columns in [docs/architecture.md](../docs/architecture.md). The other flows use only standard SharePoint actions.

1. In the solution, open the flow **Pantry - Create SharePoint site and lists** → **Turn on** → **Run** → **Run flow**.
2. Wait until it shows **Succeeded** (1–3 minutes). It:
   - creates the site if it doesn't exist;
   - creates the five lists and their columns;
   - adds 5 suppliers and 24 pantry items.

It's safe to run again: lists that already exist are left as they are.

## 3. Turn on the order flows
In the solution, select **Pantry Order Approval** and **Pantry Supplier Order Email** → **Turn on**. They import switched off because their lists only exist after step 2. The low-stock alert is already on.

## 4. Settings
Open each flow → **Edit** → its first step, **Settings**:

| Flow | What to set |
|---|---|
| Pantry Order Approval | `approverEmail` (office manager), `budgetLimit` (5000), `quantityLimit` (50) |
| Pantry Supplier Order Email | `pantryAdminEmail`, `senderName` |
| Pantry Daily Low Stock Alert | `pantryAdminEmail` (runs at 08:00 India Standard Time) |

If you change the limits, also change `cfgBudgetLimit` / `cfgQuantityLimit` in the app (**App** → **Formulas**) so the cart preview matches.

## 5. Connect the app to the lists
1. **Apps** → **Pantry Supply Ordering** → **Edit**.
2. **Data** (cylinder icon) → **Add data** → **SharePoint**, then pick the site.
3. Tick **Pantry Items**, **Pantry Suppliers**, **Pantry Orders**, **Pantry Order Lines** and **Pantry Approval History** → **Connect**.
4. **Save**, then **Publish**.

Do step 5 again after each import of a new app version. Studio can't open an app that is packaged with its data sources.

## 6. Copilot agent
Open Copilot Studio → **Pantry Supply Assistant**.
1. Sign in to the SharePoint connection if prompted.
2. **Publish**.

The agent's four tools read the lists on `https://dheerajvyas173gmail.sharepoint.com/sites/OfficePantry`. If you used a different site, open each tool (**Get pantry stock**, **Get recent supply orders**, **Get recent order line items**, **Get suppliers**) and change **Site Address**.

## 7. People and permissions
SharePoint site permissions control who sees the data:
- **Site Members** (edit): staff who request supplies.
- **Site Owners**: the office manager and pantry admins.

Share the app and the Copilot agent with the same people. For requesters who should only see their own orders, see [docs/security-considerations.md](../docs/security-considerations.md).

## Troubleshooting
| Symptom | Fix |
|---|---|
| "Connection not found" during import | Create the connection first (Power Automate → **Connections** → **New connection**), then import again |
| The setup flow fails at **Create_site** | You may not be allowed to create sites. Create a communication site at the same address in SharePoint, then run the flow again |
| The order flows don't start | Check that they're **On**. They check the Pantry Orders list every minute, so allow 1–2 minutes |
| App formulas show errors | Make sure all five lists are added under **Data** with the names above |
