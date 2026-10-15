# Security considerations (SharePoint edition)

## What is built
### Access to the data
The five lists live on one SharePoint site, so access is the site's permissions:

| Who | SharePoint group | Can |
|---|---|---|
| Staff (requesters) | Site Members (Edit) | Create orders and lines, read the catalog and suppliers |
| Office manager, pantry admins | Site Owners (Full control) | Everything, including stock edits and approvals |

The app's role switcher only changes which screens are shown (for the demo). It grants no access. SharePoint enforces what each person can read or change.

**Requesters seeing only their own orders.** On **Pantry Orders** and **Pantry Order Lines**, open **List settings** → **Advanced settings** → **Item-level permissions**:
- set *Read access* to "Read items that were created by the user";
- set *Create and Edit access* to "Create items and edit items that were created by the user".

Site owners still see everything. The setup flow doesn't change this setting, so you choose whether to apply it.

### Server-side rules
- **The approval flow** makes the threshold decision. A modified app can't skip approval for a large order: the flow recalculates the total units from the order's lines and checks the order's total amount when the order is submitted.
- **The inventory check** re-reads live stock from the list at submit time.

### Audit trail
Every submission, approval (manual or automatic) and rejection writes a row to **Pantry Approval History**: who, when, comments, and the old and new status. SharePoint also keeps version history on every list item (who changed what, and when).

### Flows and connections
- The flows use **connection references** for SharePoint, Approvals and Office 365 Outlook. In production, bind them to a service account that is a site owner, so approvals and emails don't depend on one person.
- The site address is an **environment variable**, so the same solution can point to a test site and a production site.
- Supplier emails only go to the **Email** stored on the supplier item. Lines without a supplier are reported to the pantry admin instead of being sent anywhere.
- Recipients and approval limits sit in each flow's first **Settings** step. There are no secrets in the flow definitions.

### Copilot agent
- Its tools are read-only SharePoint "Get items" actions that run as the end user (Invoker), so it can't show items the user isn't allowed to read.
- Its instructions limit it to pantry topics, and web browsing is off.

## Recommended for production
- **DLP policy:** put SharePoint, Approvals and Office 365 Outlook in the Business group.
- **Item-level permissions** on Pantry Orders and Order Lines (above), plus a **Visitors** group for read-only viewers.
- **Separate sites** for test and production, selected by the environment variable. Export a **managed** solution for production.
- **Entra ID:** require MFA and conditional access for app users.
- **Real roles:** replace the demo role switcher with a check of SharePoint group membership (for example via the Office 365 Groups or SharePoint connector).
- **Monitoring:** use flow run history and failure alerts (Power Automate analytics).
