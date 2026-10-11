"""Cloud flow definitions (Power Automate) packaged into the solution as Workflows/*.json."""
import json
import uuid
from xml.sax.saxutils import quoteattr

# Default recipients; each flow exposes these in its first "Settings" step for easy editing.
APPROVER_EMAIL = "dheerajvyas@dheerajvyas173gmail.onmicrosoft.com"
PANTRY_ADMIN_EMAIL = "dheerajvyas@dheerajvyas173gmail.onmicrosoft.com"
TIME_ZONE = "India Standard Time"
# Orders above either limit go to the office manager; smaller orders are approved automatically.
# Keep these in step with cfgBudgetLimit / cfgQuantityLimit in the canvas app (App.Formulas).
BUDGET_LIMIT = 5000      # total amount, INR
QUANTITY_LIMIT = 50      # total units across all lines

# Choice values (see OPTION_SETS in generate_solution.py).
ORDER_SUBMITTED, ORDER_APPROVED, ORDER_REJECTED, ORDER_ORDERED = 100000001, 100000002, 100000003, 100000004
APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_REJECTED = 100000000, 100000001, 100000002
ACTION_SUBMITTED, ACTION_APPROVED, ACTION_REJECTED = 100000000, 100000001, 100000002

DV, APPROVALS, OUTLOOK = "shared_commondataserviceforapps", "shared_approvals", "shared_office365"
CONNECTORS = {
    DV: ("cr_pantry_dataverse", "Pantry - Dataverse"),
    APPROVALS: ("cr_pantry_approvals", "Pantry - Approvals"),
    OUTLOOK: ("cr_pantry_outlook", "Pantry - Office 365 Outlook"),
}

ORDER_ID = "@{triggerOutputs()?['body/cr_supplyorderid']}"
ORDER_NAME = "@{triggerOutputs()?['body/cr_name']}"


def _op(connector, operation, params, webhook=False):
    return {
        "type": "OpenApiConnectionWebhook" if webhook else "OpenApiConnection",
        "inputs": {
            "host": {
                "connectionName": connector,
                "operationId": operation,
                "apiId": f"/providers/Microsoft.PowerApps/apis/{connector}",
            },
            "parameters": params,
            "authentication": "@parameters('$authentication')",
        },
    }


def dataverse_trigger(message, filter_expression):
    # message: 3 = modified, 4 = added or modified; scope 4 = organization
    return _op(DV, "SubscribeWebhookTrigger", {
        "subscriptionRequest/message": message,
        "subscriptionRequest/entityname": "cr_supplyorder",
        "subscriptionRequest/scope": 4,
        "subscriptionRequest/filteringattributes": "cr_orderstatus",
        "subscriptionRequest/filterexpression": filter_expression,
    }, webhook=True)


def list_rows(entity_set, **query):
    return _op(DV, "ListRecords", {"entityName": entity_set, **{f"${k}": v for k, v in query.items()}})


def get_row(entity_set, record_id):
    return _op(DV, "GetItem", {"entityName": entity_set, "recordId": record_id})


def update_order(**fields):
    return _op(DV, "UpdateRecord", {"entityName": "cr_supplyorders", "recordId": ORDER_ID,
                                    **{f"item/{k}": v for k, v in fields.items()}})


def log_history(name, action, approver, comments="", previous=None, new=None):
    fields = {
        "item/cr_name": name,
        "item/cr_supplyorder@odata.bind": f"cr_supplyorders({ORDER_ID})",
        "item/cr_action": action,
        "item/cr_approver": approver,
        "item/cr_actiondate": "@{utcNow()}",
        "item/cr_comments": comments,
    }
    if previous is not None:
        fields["item/cr_previousstatus"] = previous
    if new is not None:
        fields["item/cr_newstatus"] = new
    return _op(DV, "CreateRecord", {"entityName": "cr_approvalhistories", **fields})


def send_email(to, subject, body):
    return _op(OUTLOOK, "SendEmailV2", {
        "emailMessage/To": to, "emailMessage/Subject": subject,
        "emailMessage/Body": body, "emailMessage/Importance": "Normal",
    })


def compose(value):
    return {"type": "Compose", "inputs": value}


def select(source, mapping):
    return {"type": "Select", "inputs": {"from": source, "select": mapping}}


def query(source, where):
    return {"type": "Query", "inputs": {"from": source, "where": where}}


def html_table(source):
    return {"type": "Table", "inputs": {"from": source, "format": "HTML"}}


def chain(steps):
    """Turn [(name, action), ...] into an actions dict where each step runs after the previous one."""
    actions, previous = {}, None
    for name, action in steps:
        action["runAfter"] = {previous: ["Succeeded"]} if previous else {}
        actions[name] = action
        previous = name
    return actions


def condition(expression, if_true, if_false=()):
    return {
        "type": "If",
        "expression": expression,
        "actions": chain(if_true),
        "else": {"actions": chain(if_false)},
    }


def foreach(items, steps, sequential=False):
    loop = {"type": "Foreach", "foreach": items, "actions": chain(steps)}
    if sequential:
        loop["runtimeConfiguration"] = {"concurrency": {"repetitions": 1}}
    return loop


def init_variable(name, type_, value):
    return {"type": "InitializeVariable", "inputs": {"variables": [{"name": name, "type": type_, "value": value}]}}


def increment_variable(name, value):
    return {"type": "IncrementVariable", "inputs": {"name": name, "value": value}}


# --- Flow 1: approval -------------------------------------------------------

def approval_flow():
    response = "first(body('Request_approval')?['responses'])"
    approver = f"@{{{response}?['responder']?['displayName']}}"
    comments = f"@{{{response}?['comments']}}"
    requester_email = "@{outputs('Get_requester')?['body/internalemailaddress']}"

    def decided(status_label, approval_value, order_value, action_value, subject, by=approver, notes=comments):
        return [
            (f"Set_order_{status_label}", update_order(
                cr_approvalstatus=approval_value, cr_orderstatus=order_value,
                cr_approvaldate="@{utcNow()}", cr_approvedby=by, cr_approvercomments=notes)),
            (f"Log_{status_label}", log_history(
                f"{status_label.replace('_', ' ').capitalize()} - {ORDER_NAME}", action_value, by, notes,
                APPROVAL_PENDING, approval_value)),
            (f"Email_requester_{status_label}", send_email(
                requester_email, subject,
                f"<p>Hi @{{outputs('Get_requester')?['body/firstname']}},</p>"
                f"<p>Your pantry order <b>{ORDER_NAME}</b> was <b>{status_label.replace('_', ' ')}</b> by {by}.</p>"
                f"<p><b>Comments:</b> {notes}</p>"
                + ("<p>It has been sent to the supplier.</p>" if approval_value == APPROVAL_APPROVED else ""))),
        ]

    total_amount = "float(coalesce(triggerOutputs()?['body/cr_totalamount'], 0))"
    needs_approval = {"or": [
        {"greater": [f"@{total_amount}", "@outputs('Settings')?['budgetLimit']"]},
        {"greater": ["@variables('TotalQuantity')", "@outputs('Settings')?['quantityLimit']"]},
    ]}
    threshold_note = ("Under the approval limits (total @{triggerOutputs()?['body/cr_totalamount']} of "
                      "@{outputs('Settings')?['budgetLimit']}, @{variables('TotalQuantity')} of "
                      "@{outputs('Settings')?['quantityLimit']} units)")

    triggers = {"When_an_order_is_submitted": dataverse_trigger(4, f"cr_orderstatus eq {ORDER_SUBMITTED}")}
    actions = chain([
        ("Settings", compose({"approverEmail": APPROVER_EMAIL, "budgetLimit": BUDGET_LIMIT,
                              "quantityLimit": QUANTITY_LIMIT})),
        ("Initialize_total_quantity", init_variable("TotalQuantity", "Integer", 0)),
        ("Get_requester", get_row("systemusers", "@triggerOutputs()?['body/_createdby_value']")),
        ("Mark_pending", update_order(cr_approvalstatus=APPROVAL_PENDING)),
        ("Log_submission", log_history(
            f"Submitted - {ORDER_NAME}", ACTION_SUBMITTED,
            "@{outputs('Get_requester')?['body/fullname']}", new=APPROVAL_PENDING)),
        ("List_line_items", list_rows(
            "cr_orderlineitems",
            filter=f"_cr_supplyorder_value eq {ORDER_ID}",
            expand="cr_pantryitem($select=cr_name)")),
        ("Add_up_quantities", foreach("@outputs('List_line_items')?['body/value']", [
            ("Add_line_quantity", increment_variable("TotalQuantity", "@int(coalesce(item()?['cr_quantity'], 0))")),
        ], sequential=True)),
        ("Item_lines", select(
            "@outputs('List_line_items')?['body/value']",
            "@concat('- ', coalesce(item()?['cr_pantryitem']?['cr_name'], item()?['cr_name']), "
            "' x ', string(coalesce(item()?['cr_quantity'], 0)))")),
        ("If_over_approval_limits", condition(needs_approval, [
            ("Request_approval", _op(APPROVALS, "StartAndWaitForAnApproval", {
                "approvalType": "Basic",
                "WebhookApprovalCreationInput/title": f"Pantry order {ORDER_NAME} needs approval",
                "WebhookApprovalCreationInput/assignedTo": "@{outputs('Settings')?['approverEmail']}",
                "WebhookApprovalCreationInput/details":
                    "**Requested by:** @{outputs('Get_requester')?['body/fullname']}\n\n"
                    "**Required by:** @{triggerOutputs()?['body/cr_requiredbydate']}\n\n"
                    "**Total amount:** @{triggerOutputs()?['body/cr_totalamount']}\n\n"
                    "**Justification:** @{triggerOutputs()?['body/cr_justification']}\n\n"
                    "**Items:**\n\n@{join(body('Item_lines'), decodeUriComponent('%0A'))}",
                "WebhookApprovalCreationInput/enableNotifications": True,
                "WebhookApprovalCreationInput/enableReassignment": True,
            }, webhook=True)),
            ("If_approved", condition(
                {"and": [{"equals": ["@body('Request_approval')?['outcome']", "Approve"]}]},
                decided("approved", APPROVAL_APPROVED, ORDER_APPROVED, ACTION_APPROVED,
                        f"Your pantry order {ORDER_NAME} was approved"),
                decided("rejected", APPROVAL_REJECTED, ORDER_REJECTED, ACTION_REJECTED,
                        f"Your pantry order {ORDER_NAME} was not approved"))),
        ], decided("auto_approved", APPROVAL_APPROVED, ORDER_APPROVED, ACTION_APPROVED,
                   f"Your pantry order {ORDER_NAME} was approved automatically",
                   by="Auto-approved (under limits)", notes=threshold_note))),
    ])
    return triggers, actions


# --- Flow 2: daily low-stock alert -------------------------------------------

def low_stock_flow():
    triggers = {"Every_morning": {
        "type": "Recurrence",
        "recurrence": {"frequency": "Day", "interval": 1, "timeZone": TIME_ZONE,
                       "schedule": {"hours": ["8"], "minutes": [0]}},
    }}
    actions = chain([
        ("Settings", compose({"pantryAdminEmail": PANTRY_ADMIN_EMAIL})),
        ("List_active_items", list_rows(
            "cr_pantryitems", filter="statecode eq 0",
            select="cr_name,cr_sku,cr_currentstock,cr_minimumstock,cr_reorderquantity,cr_location",
            expand="cr_preferredsupplier($select=cr_name)")),
        ("Filter_low_stock", query(
            "@outputs('List_active_items')?['body/value']",
            "@lessOrEquals(coalesce(item()?['cr_currentstock'], 0), coalesce(item()?['cr_minimumstock'], 0))")),
        ("If_any_low_stock", condition(
            {"and": [{"greater": ["@length(body('Filter_low_stock'))", 0]}]},
            [
                ("Low_stock_rows", select("@body('Filter_low_stock')", {
                    "Item": "@item()?['cr_name']",
                    "SKU": "@item()?['cr_sku']",
                    "In stock": "@item()?['cr_currentstock']",
                    "Minimum": "@item()?['cr_minimumstock']",
                    "Reorder qty": "@item()?['cr_reorderquantity']",
                    "Supplier": "@item()?['cr_preferredsupplier']?['cr_name']",
                    "Location": "@item()?['cr_location']",
                })),
                ("Low_stock_table", html_table("@body('Low_stock_rows')")),
                ("Email_pantry_admin", send_email(
                    "@{outputs('Settings')?['pantryAdminEmail']}",
                    "Pantry alert: @{length(body('Filter_low_stock'))} item(s) need restocking",
                    "<p>These pantry items are at or below their minimum stock level:</p>"
                    "@{body('Low_stock_table')}"
                    "<p>Create a supply order in the Pantry app to restock them.</p>")),
            ])),
    ])
    return triggers, actions


# --- Flow 3: send approved orders to suppliers --------------------------------

def supplier_flow():
    lines = "@outputs('List_order_lines')?['body/value']"
    supplier = "first(body('Supplier_lines'))?['cr_supplier']"
    triggers = {"When_an_order_is_approved": dataverse_trigger(3, f"cr_orderstatus eq {ORDER_APPROVED}")}
    actions = chain([
        ("Settings", compose({"pantryAdminEmail": PANTRY_ADMIN_EMAIL, "senderName": "Office Pantry Team"})),
        ("List_order_lines", list_rows(
            "cr_orderlineitems",
            filter=f"_cr_supplyorder_value eq {ORDER_ID}",
            expand="cr_pantryitem($select=cr_name,cr_sku),cr_supplier($select=cr_name,cr_email,cr_contactperson)")),
        ("Supplier_ids", select(lines, "@item()?['_cr_supplier_value']")),
        ("Unique_suppliers", compose("@union(body('Supplier_ids'), body('Supplier_ids'))")),
        ("For_each_supplier", foreach("@outputs('Unique_suppliers')", [
            ("If_supplier_set", condition(
                {"and": [{"not": {"equals": ["@empty(items('For_each_supplier'))", True]}}]},
                [
                    ("Supplier_lines", query(lines, "@equals(item()?['_cr_supplier_value'], items('For_each_supplier'))")),
                    ("PO_rows", select("@body('Supplier_lines')", {
                        "Item": "@item()?['cr_pantryitem']?['cr_name']",
                        "SKU": "@item()?['cr_pantryitem']?['cr_sku']",
                        "Quantity": "@item()?['cr_quantity']",
                    })),
                    ("PO_table", html_table("@body('PO_rows')")),
                    ("Email_supplier", send_email(
                        f"@{{{supplier}?['cr_email']}}",
                        f"Purchase order {ORDER_NAME}",
                        f"<p>Dear @{{coalesce({supplier}?['cr_contactperson'], {supplier}?['cr_name'])}},</p>"
                        f"<p>Please supply the following items for order <b>{ORDER_NAME}</b>, "
                        "required by @{triggerOutputs()?['body/cr_requiredbydate']}.</p>"
                        "@{body('PO_table')}"
                        "<p>Delivery address: @{triggerOutputs()?['body/cr_deliveryaddress']}</p>"
                        "<p>Thank you,<br/>@{outputs('Settings')?['senderName']}</p>")),
                ])),
        ])),
        ("Lines_without_supplier", query(lines, "@empty(item()?['_cr_supplier_value'])")),
        ("If_lines_without_supplier", condition(
            {"and": [{"greater": ["@length(body('Lines_without_supplier'))", 0]}]},
            [("Email_admin_missing_supplier", send_email(
                "@{outputs('Settings')?['pantryAdminEmail']}",
                f"Order {ORDER_NAME}: @{{length(body('Lines_without_supplier'))}} line item(s) have no supplier",
                f"<p>Approved order <b>{ORDER_NAME}</b> has line items with no supplier, "
                "so they were not sent to anyone. Please order them manually.</p>"))])),
        ("Mark_ordered", update_order(cr_orderstatus=ORDER_ORDERED, cr_orderdate="@{utcNow()}")),
    ])
    return triggers, actions


FLOWS = [
    ("Pantry Order Approval", "Sends submitted supply orders for approval and records the decision.",
     approval_flow, [DV, APPROVALS, OUTLOOK]),
    ("Pantry Daily Low Stock Alert", "Emails the pantry admin every morning about items at or below minimum stock.",
     low_stock_flow, [DV, OUTLOOK]),
    ("Pantry Supplier Order Email", "Emails each supplier their part of an approved order and marks it Ordered.",
     supplier_flow, [DV, OUTLOOK]),
]


def flow_json(triggers, actions, connectors):
    return json.dumps({
        "properties": {
            "connectionReferences": {
                c: {"runtimeSource": "embedded",
                    "connection": {"connectionReferenceLogicalName": CONNECTORS[c][0]},
                    "api": {"name": c}}
                for c in connectors
            },
            "definition": {
                "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                "contentVersion": "1.0.0.0",
                "parameters": {
                    "$connections": {"defaultValue": {}, "type": "Object"},
                    "$authentication": {"defaultValue": {}, "type": "SecureObject"},
                },
                "triggers": triggers,
                "actions": actions,
            },
            "templateName": "",
        },
        "schemaVersion": "1.0.0.0",
    }, indent=2)


def build():
    """Returns (workflows xml, root components xml, connection references xml, {zip path: content})."""
    wf_xml, roots, files = "\n", "", {}
    for name, description, builder, connectors in FLOWS:
        wid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"pantrysupplyordering/flow/{name}"))
        path = f"Workflows/{name.replace(' ', '')}-{wid.upper()}.json"
        files[path] = flow_json(*builder(), connectors)
        wf_xml += f"""    <Workflow WorkflowId="{{{wid}}}" Name={quoteattr(name)} Description={quoteattr(description)}>
      <JsonFileName>/{path}</JsonFileName>
      <Type>1</Type>
      <Subprocess>0</Subprocess>
      <Category>5</Category>
      <Mode>0</Mode>
      <Scope>4</Scope>
      <OnDemand>0</OnDemand>
      <TriggerOnCreate>0</TriggerOnCreate>
      <TriggerOnDelete>0</TriggerOnDelete>
      <AsyncAutodelete>0</AsyncAutodelete>
      <SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure>
      <StateCode>1</StateCode>
      <StatusCode>2</StatusCode>
      <RunAs>1</RunAs>
      <IsTransacted>1</IsTransacted>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <BusinessProcessType>0</BusinessProcessType>
      <IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers>
      <PrimaryEntity>none</PrimaryEntity>
      <LocalizedNames>
        <LocalizedName languagecode="1033" description={quoteattr(name)} />
      </LocalizedNames>
    </Workflow>
"""
        roots += f'      <RootComponent type="29" id="{{{wid}}}" behavior="0" />\n'
    conn_xml = "  <connectionreferences>\n" + "".join(
        f"""    <connectionreference connectionreferencelogicalname="{logical}">
      <connectionreferencedisplayname>{display}</connectionreferencedisplayname>
      <connectorid>/providers/Microsoft.PowerApps/apis/{connector}</connectorid>
      <iscustomizable>1</iscustomizable>
      <promptingbehavior>0</promptingbehavior>
      <statecode>0</statecode>
      <statuscode>1</statuscode>
    </connectionreference>
""" for connector, (logical, display) in CONNECTORS.items()) + "  </connectionreferences>\n"
    return wf_xml + "  ", roots, conn_xml, files
