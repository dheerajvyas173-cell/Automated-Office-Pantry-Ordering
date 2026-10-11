# Import guide

`Step6_Copilot_Agent.zip` contains the whole solution (version 1.1.3.0): tables, choices, three security roles, three cloud flows, the canvas app and the Copilot agent. It upgrades any earlier import of `PantrySupplyOrdering`.

The other ZIPs (`PantrySupplyOrdering_1_0_0_0.zip` and `Step3`–`Step5`) are the earlier step-by-step layers. They aren't needed if you import Step 6.

## 1. Import
1. make.powerapps.com → pick your environment → **Solutions** → **Import solution**.
2. Browse to `Step6_Copilot_Agent.zip` → **Next**.
3. **Connections:** pick, or create, a connection for each:
   - **Pantry - Dataverse** (Microsoft Dataverse)
   - **Pantry - Approvals** (Approvals)
   - **Pantry - Office 365 Outlook** (Office 365 Outlook)
4. **Import**. The flows are switched on as part of the import.

## 2. Settings
Open each flow → **Edit** → its first step, **Settings**:

| Flow | What to set |
|---|---|
| Pantry Order Approval | `approverEmail` (office manager), `budgetLimit` (5000), `quantityLimit` (50) |
| Pantry Supplier Order Email | `pantryAdminEmail`, `senderName` |
| Pantry Daily Low Stock Alert | `pantryAdminEmail` (runs at 08:00 India Standard Time) |

If you change the limits, also change `cfgBudgetLimit` / `cfgQuantityLimit` in the app (**App** → **Formulas**) so the cart preview matches.

## 3. Sample data
Import `dataverse/sample-data/1_Suppliers.csv` first, then `2_PantryItems.csv`. Steps are in [../dataverse/sample-data.md](../dataverse/sample-data.md).

## 4. Security roles
In the Power Platform admin center → **Users** → **Manage security roles**, give:
- **Pantry Requester** to staff;
- **Pantry Approver** to the office manager;
- **Pantry Admin** to cafeteria and pantry staff.

Share the app with the same people.

## 5. Canvas app
1. **Apps** → **Pantry Supply Ordering** → **Edit**.
2. **Data** (cylinder icon) → **Add data** → **Dataverse**, then add Pantry Items, Suppliers, Supply Orders, Order Line Items and Approval History Records. Do this again after each import of a new version.
3. **Save**, then **Publish**.

The tables can't be shipped inside the app: an app packed with its Dataverse tables fails to open in Studio ("Error opening file").

## 6. Copilot agent
Open Copilot Studio → **Pantry Supply Assistant**.
1. Sign in to the Dataverse connection if prompted.
2. **Publish**.
3. Optionally, add it to Teams under **Channels**.

Test it with "How many coffee pods are left?" or "When was the last order placed?".

## Troubleshooting
| Symptom | Fix |
|---|---|
| "Connection not found" during import | Create the connection first (Power Automate → **Connections** → **New connection**), then import again |
| A flow is Off after import | Open it, fix any connection marked red, then **Turn on** |
| Approval email never arrives | Check `approverEmail` in the approval flow's Settings step, and the flow's run history |
| Small orders aren't auto-approved | The flow uses the order's **Total Amount** and the sum of line quantities. Check that both are under the limits |
