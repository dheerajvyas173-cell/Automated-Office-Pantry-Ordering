# Security considerations

## What is built
### Security roles (in the solution)
| Role | Supply Orders | Order Line Items | Pantry Items / Suppliers | Approval History |
|---|---|---|---|---|
| **Pantry Requester** | Create, read, write **own** (user level) | Create, read, write, delete **own** | Read all | Read all |
| **Pantry Approver** | Read and write **all** | Read all | Read all | Create, read |
| **Pantry Admin** | Full | Full | Full (including stock edits) | Full |

Assign the roles with **Manage roles** on users or teams in the Power Platform admin center. Users also need the app shared with them.

### Enforcement on the server, not in the app
- **Dataverse privileges** decide what each user can read or change. The app's role switcher only changes which screens are shown, for the demo, and grants no access.
- **The approval flow** makes the threshold decision. A modified app can't skip approval for a large order, because the flow re-evaluates the order total and quantities when the order is submitted.
- **The inventory check** runs against live Dataverse data at submit time.

### Audit trail
Every submission, approval (manual or automatic) and rejection writes an **Approval History** row: who, when, comments, and the old and new status. Dataverse auditing can also be turned on for the five tables.

### Flows and connections
- The flows use **connection references**: Dataverse, Approvals and Office 365 Outlook. In production, bind them to a service account so approvals and emails don't depend on one person's account.
- Supplier emails go only to the **Email** stored on the Supplier record. Lines without a supplier are reported to the pantry admin instead of being sent anywhere.
- Recipients and approval limits sit in each flow's first **Settings** step. There are no secrets in the flow definitions.

### Copilot agent
- The agent uses **read-only** Dataverse "List rows" tools, running with the end user's identity (Invoker), so it can't show data the user can't read.
- Its instructions limit it to pantry topics, and web browsing is off.

## Recommended for production
- **DLP policy:** put Dataverse, Approvals and Office 365 Outlook in the Business group, and block other connectors in the pantry environment.
- **Environments:** develop in a Dev environment, then export a **managed** solution to Test and Production.
- **Environment variables:** use them for approval limits, the approver and admin addresses, and the time zone.
- **Entra ID:** require MFA and conditional access for app users.
- **Real roles:** replace the demo role switcher with a check of the user's Dataverse security role.
- **Monitoring:** use flow run history and failure alerts (Power Automate analytics), and Dataverse audit logs.
