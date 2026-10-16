"""Cloud flow definitions (Power Automate) packaged into the solution as Workflows/*.json.

All data is in SharePoint lists (see sharepoint.py). Flows read and write the lists with the
SharePoint connector's "Send an HTTP request to SharePoint" action, so columns are addressed by
their internal names and lookups by their Id, whatever the list's display settings.
"""
import json
import uuid
from xml.sax.saxutils import quoteattr

import sharepoint as sp

# Default recipients; each flow exposes these in its first "Settings" step for easy editing.
APPROVER_EMAIL = "dheerajvyas@dheerajvyas173gmail.onmicrosoft.com"
PANTRY_ADMIN_EMAIL = "dheerajvyas@dheerajvyas173gmail.onmicrosoft.com"
TIME_ZONE = "India Standard Time"
# Orders above either limit go to the office manager; smaller orders are approved automatically.
# Keep these in step with cfgBudgetLimit / cfgQuantityLimit in the canvas app (App.Formulas).
BUDGET_LIMIT = 5000      # total amount, INR
QUANTITY_LIMIT = 50      # total units across all lines

SHAREPOINT, APPROVALS, OUTLOOK = "shared_sharepointonline", "shared_approvals", "shared_office365"
CONNECTORS = {
    SHAREPOINT: ("cr_pantry_sharepoint", "Pantry - SharePoint"),
    APPROVALS: ("cr_pantry_approvals", "Pantry - Approvals"),
    OUTLOOK: ("cr_pantry_outlook", "Pantry - Office 365 Outlook"),
}

ORDER_ID = "@{triggerOutputs()?['body/ID']}"
ORDER_NAME = "@{triggerOutputs()?['body/Title']}"
JSON_LIGHT = "application/json;odata=nometadata"
VERBOSE = "application/json;odata=verbose"


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


def http(method, uri, body=None, merge=False, verbose=False, site=sp.SITE):
    """Send an HTTP request to SharePoint. `body` is a JSON string (may contain @{...} expressions)."""
    kind = VERBOSE if verbose else JSON_LIGHT
    headers = {"Accept": kind, "Content-Type": kind}
    if merge:
        headers.update({"X-HTTP-Method": "MERGE", "IF-MATCH": "*"})
    params = {"dataset": site, "parameters/method": method, "parameters/uri": uri,
              "parameters/headers": headers}
    if body is not None:
        params["parameters/body"] = body
    return _op(SHAREPOINT, "HttpRequest", params)


def items_uri(list_title, item_id=None, query=""):
    uri = f"_api/web/lists/getbytitle('{list_title}')/items"
    if item_id is not None:
        uri += f"({item_id})"
    return uri + (f"?{query}" if query else "")


# The order flows use only the standard SharePoint actions (Get items, Get item, Create item,
# Update item): data loss prevention policies often block "Send an HTTP request to SharePoint".
CHOICE_FIELDS = {"OrderStatus", "ApprovalStatus", "ApprovalAction", "PreviousStatus", "NewStatus"}
LOOKUP_FIELDS = {"SupplyOrderId": "SupplyOrder"}


def item_params(fields):
    params = {}
    for k, v in fields.items():
        if k in CHOICE_FIELDS:
            params[f"item/{k}/Value"] = v
        elif k in LOOKUP_FIELDS:
            params[f"item/{LOOKUP_FIELDS[k]}/Id"] = v
        else:
            params[f"item/{k}"] = v
    return params


def get_items(list_title, top=5000):
    return _op(SHAREPOINT, "GetItems", {"dataset": sp.SITE, "table": list_title, "$top": top})


def get_item(list_title, item_id):
    return _op(SHAREPOINT, "GetItem", {"dataset": sp.SITE, "table": list_title, "id": item_id})


def write_steps(name, list_title, fields, item_id=None):
    """Create (or, with item_id, update) a list item with the standard SharePoint actions."""
    params = {"dataset": sp.SITE, "table": list_title, **item_params(fields)}
    if item_id is not None:
        params["id"] = item_id
    return [(name, _op(SHAREPOINT, "PatchItem" if item_id is not None else "PostItem", params))]


def sp_trigger(list_title, condition_expression):
    """Polls the list every minute for new or changed items that match the condition."""
    trigger = _op(SHAREPOINT, "GetOnUpdatedItems", {"dataset": sp.SITE, "table": list_title})
    trigger.update({
        "recurrence": {"interval": 1, "frequency": "Minute"},
        "splitOn": "@triggerOutputs()?['body/value']",
        "conditions": [{"expression": condition_expression}],
    })
    return trigger


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


def init_variable(name, type_, value):
    return {"type": "InitializeVariable", "inputs": {"variables": [{"name": name, "type": type_, "value": value}]}}


def set_variable(name, value):
    return {"type": "SetVariable", "inputs": {"name": name, "value": value}}


def increment_variable(name, value):
    return {"type": "IncrementVariable", "inputs": {"name": name, "value": value}}


def append_variable(name, value):
    return {"type": "AppendToArrayVariable", "inputs": {"name": name, "value": value}}


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


def until(expression, steps, count=40, timeout="PT20M"):
    return {"type": "Until", "expression": expression, "limit": {"count": count, "timeout": timeout},
            "actions": chain(steps)}


def delay(seconds):
    return {"type": "Wait", "inputs": {"interval": {"count": seconds, "unit": "Second"}}}


def log_history(name, title, action, approver, comments="", previous=None, new=None):
    fields = {
        "Title": title,
        "SupplyOrderId": "@int(triggerOutputs()?['body/ID'])",
        "ApprovalAction": action,
        "Approver": approver,
        "ActionDate": "@{utcNow()}",
        "Comments": comments,
    }
    if previous:
        fields["PreviousStatus"] = previous
    if new:
        fields["NewStatus"] = new
    return write_steps(name, sp.HISTORY, fields)


def update_order(name, **fields):
    return write_steps(name, sp.ORDERS, fields, item_id=ORDER_ID)


# --- Flow 1: approval -------------------------------------------------------

def approval_flow():
    response = "first(body('Request_approval')?['responses'])"
    approver = f"@{{{response}?['responder']?['displayName']}}"
    comments = f"@{{coalesce({response}?['comments'], '')}}"
    requester_email = "@{triggerOutputs()?['body/RequestedBy']}"
    requester_name = "@{coalesce(triggerOutputs()?['body/RequesterName'], triggerOutputs()?['body/RequestedBy'])}"

    def decided(label, approval_status, order_status, action, subject, by=approver, notes=comments):
        tag = label.replace(" ", "_")
        return [
            *update_order(f"Set_order_{tag}", ApprovalStatus=approval_status, OrderStatus=order_status,
                          ApprovalDate="@{utcNow()}", ApprovedBy=by, ApproverComments=notes),
            *log_history(f"Log_{tag}", f"{label.capitalize()} - {ORDER_NAME}", action, by, notes,
                         "Pending", approval_status),
            (f"Email_requester_{tag}", send_email(
                requester_email, subject,
                f"<p>Hi {requester_name},</p>"
                f"<p>Your pantry order <b>{ORDER_NAME}</b> was <b>{label}</b> by {by}.</p>"
                f"<p><b>Comments:</b> {notes}</p>"
                + ("<p>It has been sent to the supplier.</p>" if approval_status == "Approved" else ""))),
        ]

    lines = "@body('Get_order_lines')"
    total_amount = "float(coalesce(triggerOutputs()?['body/TotalAmount'], 0))"
    needs_approval = {"or": [
        {"greater": [f"@{total_amount}", "@outputs('Settings')?['budgetLimit']"]},
        {"greater": ["@variables('TotalQuantity')", "@outputs('Settings')?['quantityLimit']"]},
    ]}
    under_limits = ("Under the approval limits (total @{triggerOutputs()?['body/TotalAmount']} of "
                    "@{outputs('Settings')?['budgetLimit']}, @{variables('TotalQuantity')} of "
                    "@{outputs('Settings')?['quantityLimit']} units)")

    # Submitted and not yet picked up: the flow sets Approval Status to Pending straight away, so
    # its own updates (and later edits) don't start it again.
    triggers = {"When_an_order_is_submitted": sp_trigger(
        sp.ORDERS,
        "@and(equals(triggerOutputs()?['body/OrderStatus/Value'], 'Submitted'), "
        "empty(triggerOutputs()?['body/ApprovalStatus/Value']))")}
    actions = chain([
        ("Settings", compose({"approverEmail": APPROVER_EMAIL, "budgetLimit": BUDGET_LIMIT,
                              "quantityLimit": QUANTITY_LIMIT})),
        ("Initialize_total_quantity", init_variable("TotalQuantity", "Integer", 0)),
        *update_order("Mark_pending", ApprovalStatus="Pending"),
        *log_history("Log_submission", f"Submitted - {ORDER_NAME}", "Submitted", requester_name, new="Pending"),
        ("Get_all_order_lines", get_items(sp.LINES)),
        ("Get_order_lines", query("@body('Get_all_order_lines')?['value']",
                                  "@equals(item()?['SupplyOrder']?['Id'], int(triggerOutputs()?['body/ID']))")),
        ("Add_up_quantities", foreach(lines, [
            ("Add_line_quantity", increment_variable("TotalQuantity", "@int(coalesce(item()?['Quantity'], 0))")),
        ], sequential=True)),
        ("Item_lines", select(lines, "@concat('- ', item()?['Title'], ' x ', string(coalesce(item()?['Quantity'], 0)))")),
        ("If_over_approval_limits", condition(needs_approval, [
            ("Request_approval", _op(APPROVALS, "StartAndWaitForAnApproval", {
                "approvalType": "Basic",
                "WebhookApprovalCreationInput/title": f"Pantry order {ORDER_NAME} needs approval",
                "WebhookApprovalCreationInput/assignedTo": "@{outputs('Settings')?['approverEmail']}",
                "WebhookApprovalCreationInput/details":
                    f"**Requested by:** {requester_name}\n\n"
                    "**Required by:** @{triggerOutputs()?['body/RequiredByDate']}\n\n"
                    "**Total amount:** @{triggerOutputs()?['body/TotalAmount']}\n\n"
                    "**Total units:** @{variables('TotalQuantity')}\n\n"
                    "**Justification:** @{triggerOutputs()?['body/Justification']}\n\n"
                    "**Items:**\n\n@{join(body('Item_lines'), decodeUriComponent('%0A'))}",
                "WebhookApprovalCreationInput/enableNotifications": True,
                "WebhookApprovalCreationInput/enableReassignment": True,
            }, webhook=True)),
            ("If_approved", condition(
                {"and": [{"equals": ["@body('Request_approval')?['outcome']", "Approve"]}]},
                decided("approved", "Approved", "Approved", "Approved",
                        f"Your pantry order {ORDER_NAME} was approved"),
                decided("rejected", "Rejected", "Rejected", "Rejected",
                        f"Your pantry order {ORDER_NAME} was not approved"))),
        ], decided("auto approved", "Approved", "Approved", "Approved",
                   f"Your pantry order {ORDER_NAME} was approved automatically",
                   by="Auto-approved (under limits)", notes=under_limits))),
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
        ("Get_pantry_items", get_items(sp.ITEMS)),
        ("Filter_low_stock", query(
            "@body('Get_pantry_items')?['value']",
            "@lessOrEquals(coalesce(item()?['CurrentStock'], 0), coalesce(item()?['MinimumStock'], 0))")),
        ("If_any_low_stock", condition(
            {"and": [{"greater": ["@length(body('Filter_low_stock'))", 0]}]},
            [
                ("Low_stock_rows", select("@body('Filter_low_stock')", {
                    "Item": "@item()?['Title']",
                    "SKU": "@item()?['SKU']",
                    "In stock": "@item()?['CurrentStock']",
                    "Minimum": "@item()?['MinimumStock']",
                    "Reorder qty": "@item()?['ReorderQuantity']",
                    "Supplier": "@item()?['PreferredSupplier']?['Value']",
                    "Location": "@item()?['StorageLocation']",
                })),
                ("Low_stock_table", html_table("@body('Low_stock_rows')")),
                ("Email_pantry_admin", send_email(
                    "@{outputs('Settings')?['pantryAdminEmail']}",
                    "Pantry alert: @{length(body('Filter_low_stock'))} item(s) need restocking",
                    "<p>These pantry items are at or below their minimum stock level:</p>"
                    "@{body('Low_stock_table')}"
                    "<p>Create a supply request in the Pantry app to restock them.</p>")),
            ])),
    ])
    return triggers, actions


# --- Flow 3: send approved orders to suppliers --------------------------------

def supplier_flow():
    lines = "@body('Get_order_lines')"
    supplier = "body('Get_supplier')"
    triggers = {"When_an_order_is_approved": sp_trigger(
        sp.ORDERS, "@equals(triggerOutputs()?['body/OrderStatus/Value'], 'Approved')")}
    actions = chain([
        ("Settings", compose({"pantryAdminEmail": PANTRY_ADMIN_EMAIL, "senderName": "Office Pantry Team"})),
        ("Get_all_order_lines", get_items(sp.LINES)),
        ("Get_order_lines", query("@body('Get_all_order_lines')?['value']",
                                  "@equals(item()?['SupplyOrder']?['Id'], int(triggerOutputs()?['body/ID']))")),
        ("Supplier_ids", select(lines, "@item()?['Supplier']?['Id']")),
        ("Unique_suppliers", compose("@union(body('Supplier_ids'), body('Supplier_ids'))")),
        ("For_each_supplier", foreach("@outputs('Unique_suppliers')", [
            ("If_supplier_set", condition(
                {"and": [{"greater": ["@int(coalesce(items('For_each_supplier'), 0))", 0]}]},
                [
                    ("Get_supplier", get_item(sp.SUPPLIERS, "@items('For_each_supplier')")),
                    ("Supplier_lines", query(lines, "@equals(item()?['Supplier']?['Id'], items('For_each_supplier'))")),
                    ("PO_rows", select("@body('Supplier_lines')", {
                        "Item": "@coalesce(item()?['PantryItem']?['Value'], item()?['Title'])",
                        "Quantity": "@item()?['Quantity']",
                    })),
                    ("PO_table", html_table("@body('PO_rows')")),
                    ("Email_supplier", send_email(
                        f"@{{{supplier}?['Email']}}",
                        f"Purchase order {ORDER_NAME}",
                        f"<p>Dear @{{coalesce({supplier}?['ContactPerson'], {supplier}?['Title'])}},</p>"
                        f"<p>Please supply the following items for order <b>{ORDER_NAME}</b>, "
                        "required by @{triggerOutputs()?['body/RequiredByDate']}.</p>"
                        "@{body('PO_table')}"
                        "<p>Delivery address: @{triggerOutputs()?['body/DeliveryAddress']}</p>"
                        "<p>Thank you,<br/>@{outputs('Settings')?['senderName']}</p>")),
                ])),
        ])),
        ("Lines_without_supplier", query(lines, "@equals(int(coalesce(item()?['Supplier']?['Id'], 0)), 0)")),
        ("If_lines_without_supplier", condition(
            {"and": [{"greater": ["@length(body('Lines_without_supplier'))", 0]}]},
            [("Email_admin_missing_supplier", send_email(
                "@{outputs('Settings')?['pantryAdminEmail']}",
                f"Order {ORDER_NAME}: @{{length(body('Lines_without_supplier'))}} line item(s) have no supplier",
                f"<p>Approved order <b>{ORDER_NAME}</b> has line items with no supplier, "
                "so they were not sent to anyone. Please order them manually.</p>"))])),
        *update_order("Mark_ordered", OrderStatus="Ordered", OrderDate="@{utcNow()}"),
    ])
    return triggers, actions


# --- Flow 4: one-time setup of the SharePoint site and lists --------------------

def setup_flow():
    """Creates the site (if missing), the five lists with their columns, and the sample data.

    Safe to run again: existing lists are left as they are and get no sample data.
    """
    root = "@{first(split(outputs('Settings')?['siteUrl'], '/sites/'))}"
    site_status = ("_api/SPSiteManager/status?url='@{encodeUriComponent(outputs('Settings')?['siteUrl'])}'")
    steps = [
        ("Settings", compose({"siteUrl": sp.SITE, "siteTitle": sp.SITE_TITLE,
                              "owner": "@{triggerOutputs()?['headers']?['x-ms-user-email']}"})),
        *[(f"Initialize_{sp.key(t)}_id", init_variable(f"{sp.key(t)}Id", "String", "")) for t, _, _ in sp.LISTS],
        ("Initialize_supplier_ids", init_variable("SupplierIds", "Array", [])),
        ("Check_site", http("GET", site_status, site=root)),
        ("If_site_missing", condition(
            {"not": {"equals": ["@body('Check_site')?['SiteStatus']", 2]}},
            [
                ("Create_site", http("POST", "_api/SPSiteManager/create", json.dumps({"request": {
                    "Title": "@{outputs('Settings')?['siteTitle']}",
                    "Url": "@{outputs('Settings')?['siteUrl']}",
                    "Lcid": 1033, "ShareByEmailEnabled": False, "Description": "Office pantry supply ordering",
                    "WebTemplate": "SITEPAGEPUBLISHING#0", "Owner": "@{outputs('Settings')?['owner']}",
                }}), site=root)),
                ("Wait_for_site", until(
                    "@equals(body('Get_site_status')?['SiteStatus'], 2)",
                    [("Wait_15_seconds", delay(15)), ("Get_site_status", http("GET", site_status, site=root))])),
            ])),
    ]
    for title, description, fields in sp.LISTS:
        k = sp.key(title)
        create_fields = [
            (f"Add_{k}_{name}", http("POST", f"_api/web/lists(guid'@{{variables('{k}Id')}}')/fields/CreateFieldAsXml",
                                     json.dumps({"parameters": {
                                         "__metadata": {"type": "SP.XmlSchemaFieldCreationInformation"},
                                         "SchemaXml": sp.field_xml(name, display, type_, opts),
                                         "Options": 24}}),  # internal name from Name, add to default view
                                     verbose=True))
            for name, display, type_, opts in fields
        ]
        seed = []
        if title == sp.SUPPLIERS:
            seed = [("Add_sample_suppliers", foreach("@outputs('Sample_suppliers')", [
                ("Create_supplier", http("POST", items_uri(title), "@{string(item())}")),
                ("Remember_supplier_id", append_variable(
                    "SupplierIds", {"name": "@{item()?['Title']}", "id": "@body('Create_supplier')?['Id']"})),
            ], sequential=True))]
            seed.insert(0, ("Sample_suppliers", compose(sp.sample_suppliers())))
        elif title == sp.ITEMS:
            seed = [
                ("Sample_items", compose(sp.sample_items())),
                ("Add_sample_items", foreach("@outputs('Sample_items')", [
                    ("Find_supplier", query("@variables('SupplierIds')", "@equals(item()?['name'], items('Add_sample_items')?['supplier'])")),
                    ("Item_values", compose("@removeProperty(addProperty(items('Add_sample_items'), 'PreferredSupplierId', "
                                            "first(body('Find_supplier'))?['id']), 'supplier')")),
                    ("Create_item", http("POST", items_uri(title), "@{string(outputs('Item_values'))}")),
                ], sequential=True)),
            ]
        steps += [
            (f"Find_{k}", http("GET", f"_api/web/lists?$select=Id&$filter=Title eq '{title}'")),
            (f"If_{k}_missing", condition(
                {"equals": [f"@length(body('Find_{k}')?['value'])", 0]},
                [
                    (f"Create_{k}", http("POST", "_api/web/lists", json.dumps({
                        "__metadata": {"type": "SP.List"}, "Title": title, "Description": description,
                        "BaseTemplate": 100, "AllowContentTypes": True}), verbose=True)),
                    (f"Remember_{k}_id", set_variable(f"{k}Id", f"@{{body('Create_{k}')?['d']?['Id']}}")),
                    *create_fields,
                    *seed,
                ],
                [(f"Use_existing_{k}", set_variable(f"{k}Id", f"@{{first(body('Find_{k}')?['value'])?['Id']}}"))])),
        ]
    steps.append(("Done", compose("Pantry site and lists are ready: @{outputs('Settings')?['siteUrl']}")))
    triggers = {"manual": {"type": "Request", "kind": "Button",
                           "inputs": {"schema": {"type": "object", "properties": {}, "required": []}}}}
    return triggers, chain(steps)


FLOWS = [
    ("Pantry Order Approval", "Sends submitted orders over the approval limits to the office manager, "
     "approves smaller ones automatically and records the decision.", approval_flow, [SHAREPOINT, APPROVALS, OUTLOOK]),
    ("Pantry Daily Low Stock Alert", "Emails the pantry admin every morning about items at or below minimum stock.",
     low_stock_flow, [SHAREPOINT, OUTLOOK]),
    ("Pantry Supplier Order Email", "Emails each supplier their part of an approved order and marks it Ordered.",
     supplier_flow, [SHAREPOINT, OUTLOOK]),
    ("Pantry - Create SharePoint site and lists", "Run once: creates the pantry SharePoint site, its five lists "
     "and the sample data.", setup_flow, [SHAREPOINT]),
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
                    sp.SITE_PARAM: {"defaultValue": sp.SITE_URL, "type": "String",
                                    "metadata": {"schemaName": sp.SITE_VAR,
                                                 "description": "SharePoint site that holds the pantry lists"}},
                },
                "triggers": triggers,
                "actions": actions,
            },
            "templateName": "",
        },
        "schemaVersion": "1.0.0.0",
    }, indent=2)


def build(only=None, switched_on=()):
    """Returns (workflows xml, root components xml, connection references xml, {zip path: content}).

    only: flow names to include (default all). switched_on: extra flows to import switched on.
    """
    wf_xml, roots, files = "\n", "", {}
    flows = [f for f in FLOWS if only is None or f[0] in only]
    used = {c for f in flows for c in f[3]}
    for name, description, builder, connectors in flows:
        # The list-triggered flows import switched off: their lists only exist once the setup flow
        # has run. The setup flow imports off too: it uses "Send an HTTP request to SharePoint",
        # which DLP policies may block, so it is turned on only where that is allowed.
        on = builder is low_stock_flow or name in switched_on
        wid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"pantrysupplyordering/flow/{name}"))
        path = f"Workflows/{''.join(c for c in name if c.isalnum())}-{wid.upper()}.json"
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
      <StateCode>{1 if on else 0}</StateCode>
      <StatusCode>{2 if on else 1}</StatusCode>
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
""" for connector, (logical, display) in CONNECTORS.items() if connector in used) + "  </connectionreferences>\n"
    return wf_xml + "  ", roots, conn_xml, files
