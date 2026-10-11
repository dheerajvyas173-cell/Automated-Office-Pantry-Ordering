"""Builds the importable Dataverse solution ZIPs in the format Dataverse itself exports.

Run: python3 solution/generate_solution.py
Outputs: PantrySupplyOrdering_1_0_0_0.zip (full) and PantrySupplyOrdering_TEST.zip (one table, diagnostic).
"""
import os
import zipfile
from xml.sax.saxutils import quoteattr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLUTION_DIR = os.path.join(ROOT, "solution")
PREFIX = "cr"
ORG_VERSION = "9.2.24094.198"


def label(text):
    return quoteattr(text)


def common_attr(type_, logical, required, display_mask, custom=True, ime="auto"):
    c = "1" if custom else "0"
    return f"""            <Type>{type_}</Type>
            <Name>{logical}</Name>
            <LogicalName>{logical}</LogicalName>
            <RequiredLevel>{required}</RequiredLevel>
            <DisplayMask>{display_mask}</DisplayMask>
            <ImeMode>{ime}</ImeMode>
            <ValidForUpdateApi>{"1" if custom else "0"}</ValidForUpdateApi>
            <ValidForReadApi>1</ValidForReadApi>
            <ValidForCreateApi>1</ValidForCreateApi>
            <IsCustomField>{c}</IsCustomField>
            <IsAuditEnabled>{c}</IsAuditEnabled>
            <IsSecured>0</IsSecured>
            <IntroducedVersion>1.0.0.0</IntroducedVersion>
            <IsCustomizable>{c}</IsCustomizable>
            <IsRenameable>{c}</IsRenameable>
            <CanModifySearchSettings>{c}</CanModifySearchSettings>
            <CanModifyRequirementLevelSettings>{c}</CanModifyRequirementLevelSettings>
            <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
            <SourceType>0</SourceType>
            <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled>
            <IsSortableEnabled>0</IsSortableEnabled>
            <CanModifyGlobalFilterSettings>1</CanModifyGlobalFilterSettings>
            <CanModifyIsSortableSettings>1</CanModifyIsSortableSettings>
            <IsDataSourceSecret>0</IsDataSourceSecret>
            <AutoNumberFormat></AutoNumberFormat>
            <IsSearchable>{c}</IsSearchable>
            <IsFilterable>0</IsFilterable>
            <IsRetrievable>{c}</IsRetrievable>
            <IsLocalizable>0</IsLocalizable>
"""


def wrap_attr(logical, body, display, desc=""):
    return f"""          <attribute PhysicalName="{logical}">
{body}            <displaynames>
              <displayname description={label(display)} languagecode="1033" />
            </displaynames>
            <Descriptions>
              <Description description={label(desc)} languagecode="1033" />
            </Descriptions>
          </attribute>
"""


GRID_MASK = "ValidForAdvancedFind|ValidForForm|ValidForGrid"


def a_primarykey(logical, display):
    body = common_attr("primarykey", logical, "systemrequired",
                       "ValidForAdvancedFind|RequiredForGrid", custom=False)
    return wrap_attr(logical, body, display, "Unique identifier for entity instances")


def a_primaryname(logical, display, max_len=200):
    body = common_attr("nvarchar", logical, "required",
                       "PrimaryName|ValidForAdvancedFind|ValidForForm|ValidForGrid|RequiredForForm")
    body += f"""            <Format>text</Format>
            <MaxLength>{max_len}</MaxLength>
            <Length>{max_len * 2}</Length>
"""
    return wrap_attr(logical, body, display)


def a_text(logical, display, max_len=100, required="none", fmt="text"):
    body = common_attr("nvarchar", logical, required, GRID_MASK)
    body += f"""            <Format>{fmt}</Format>
            <MaxLength>{max_len}</MaxLength>
            <Length>{max_len * 2}</Length>
"""
    return wrap_attr(logical, body, display)


def a_memo(logical, display, max_len=4000):
    body = common_attr("memo", logical, "none", GRID_MASK)
    body += f"""            <Format>text</Format>
            <MaxLength>{max_len}</MaxLength>
"""
    return wrap_attr(logical, body, display)


def a_int(logical, display, min_v=0, max_v=1000000, required="none"):
    body = common_attr("int", logical, required, GRID_MASK)
    body += f"""            <Format></Format>
            <MinValue>{min_v}</MinValue>
            <MaxValue>{max_v}</MaxValue>
"""
    return wrap_attr(logical, body, display)


def a_decimal(logical, display, min_v=0, max_v=100000000, accuracy=2):
    body = common_attr("decimal", logical, "none", GRID_MASK)
    body += f"""            <MinValue>{min_v}</MinValue>
            <MaxValue>{max_v}</MaxValue>
            <Accuracy>{accuracy}</Accuracy>
"""
    return wrap_attr(logical, body, display)


def a_datetime(logical, display, date_only=False):
    body = common_attr("datetime", logical, "none", GRID_MASK, ime="inactive")
    body += f"""            <Format>{"date" if date_only else "datetime"}</Format>
            <CanChangeDateTimeBehavior>1</CanChangeDateTimeBehavior>
            <Behavior>1</Behavior>
"""
    return wrap_attr(logical, body, display)


def a_choice(logical, display, optionset, required="none"):
    body = common_attr("picklist", logical, required, GRID_MASK)
    body += f"""            <AppDefaultValue>-1</AppDefaultValue>
            <OptionSetName>{optionset}</OptionSetName>
"""
    return wrap_attr(logical, body, display)


def a_lookup(logical, display, required="none"):
    body = common_attr("lookup", logical, required, GRID_MASK)
    body += """            <LookupStyle>single</LookupStyle>
            <LookupTypes />
"""
    return wrap_attr(logical, body, display)


RIBBON = """    <RibbonDiffXml>
      <CustomActions />
      <Templates>
        <RibbonTemplates Id="Mscrm.Templates"></RibbonTemplates>
      </Templates>
      <CommandDefinitions />
      <RuleDefinitions>
        <TabDisplayRules />
        <DisplayRules />
        <EnableRules />
      </RuleDefinitions>
      <LocLabels />
    </RibbonDiffXml>
"""


def entity(logical, display, plural, desc, attrs):
    flags = {
        "IsDuplicateCheckSupported": 0, "IsBusinessProcessEnabled": 0, "IsRequiredOffline": 0,
        "IsInteractionCentricEnabled": 0, "IsCollaboration": 0, "AutoRouteToOwnerQueue": 0,
        "IsConnectionsEnabled": 0, "EntityColor": "", "IsDocumentManagementEnabled": 0,
        "AutoCreateAccessTeams": 0, "IsOneNoteIntegrationEnabled": 0,
        "IsKnowledgeManagementEnabled": 0, "IsSLAEnabled": 0,
        "IsDocumentRecommendationsEnabled": 0, "IsBPFEntity": 0,
        "OwnershipTypeMask": "UserOwned", "IsAuditEnabled": 0, "IsRetrieveAuditEnabled": 0,
        "IsRetrieveMultipleAuditEnabled": 0, "IsActivity": 0, "ActivityTypeMask": "",
        "IsActivityParty": 0, "IsReplicated": 0, "IsReplicationUserFiltered": 0,
        "IsMailMergeEnabled": 0, "IsVisibleInMobile": 0, "IsVisibleInMobileClient": 1,
        "IsReadOnlyInMobileClient": 0, "IsOfflineInMobileClient": 0,
        "DaysSinceRecordLastModified": 0, "MobileOfflineFilters": "",
        "IsMapiGridEnabled": 1, "IsReadingPaneEnabled": 1, "IsQuickCreateEnabled": 1,
        "SyncToExternalSearchIndex": 0, "IntroducedVersion": "1.0.0.0",
        "IsCustomizable": 1, "IsRenameable": 1, "IsMappable": 1,
        "CanModifyAuditSettings": 1, "CanModifyMobileVisibility": 1,
        "CanModifyMobileClientVisibility": 1, "CanModifyMobileClientReadOnly": 1,
        "CanModifyMobileClientOffline": 1, "CanModifyConnectionSettings": 1,
        "CanModifyDuplicateDetectionSettings": 1, "CanModifyMailMergeSettings": 1,
        "CanModifyQueueSettings": 1, "CanCreateAttributes": 1, "CanCreateForms": 1,
        "CanCreateCharts": 1, "CanCreateViews": 1, "CanModifyAdditionalSettings": 1,
        "CanEnableSyncToExternalSearchIndex": 1, "EnforceStateTransitions": 0,
        "CanChangeHierarchicalRelationship": 1, "EntityHelpUrlEnabled": 0,
        "ChangeTrackingEnabled": 0, "CanChangeTrackingBeEnabled": 1,
        "IsEnabledForExternalChannels": 0, "IsMSTeamsIntegrationEnabled": 0,
        "IsSolutionAware": 0, "HasRelatedNotes": "False", "HasRelatedActivities": "False",
    }
    flag_xml = "".join(f"        <{k}>{v}</{k}>\n" for k, v in flags.items())
    return f"""  <Entity>
    <Name LocalizedName={label(display)} OriginalName={label(display)}>{logical}</Name>
    <EntityInfo>
      <entity Name="{logical}">
        <LocalizedNames>
          <LocalizedName description={label(display)} languagecode="1033" />
        </LocalizedNames>
        <LocalizedCollectionNames>
          <LocalizedCollectionName description={label(plural)} languagecode="1033" />
        </LocalizedCollectionNames>
        <Descriptions>
          <Description description={label(desc)} languagecode="1033" />
        </Descriptions>
        <attributes>
{"".join(attrs)}        </attributes>
        <EntitySetName>{logical[:-1] + 'ies' if logical.endswith('y') else logical + 's'}</EntitySetName>
{flag_xml}      </entity>
    </EntityInfo>
{RIBBON}  </Entity>
"""


def relationship(referenced, referencing, attr):
    name = f"{referencing}_{attr.removeprefix(PREFIX + '_')}_{referenced.removeprefix(PREFIX + '_')}"
    return f"""    <EntityRelationship Name="{name}">
      <EntityRelationshipType>OneToMany</EntityRelationshipType>
      <IsCustomizable>1</IsCustomizable>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <IsHierarchical>0</IsHierarchical>
      <ReferencingEntityName>{referencing}</ReferencingEntityName>
      <ReferencedEntityName>{referenced}</ReferencedEntityName>
      <CascadeAssign>NoCascade</CascadeAssign>
      <CascadeDelete>RemoveLink</CascadeDelete>
      <CascadeReparent>NoCascade</CascadeReparent>
      <CascadeShare>NoCascade</CascadeShare>
      <CascadeUnshare>NoCascade</CascadeUnshare>
      <CascadeRollupView>NoCascade</CascadeRollupView>
      <IsValidForAdvancedFind>1</IsValidForAdvancedFind>
      <ReferencingAttributeName>{attr}</ReferencingAttributeName>
      <RelationshipDescription>
        <Descriptions>
          <Description description="" languagecode="1033" />
        </Descriptions>
      </RelationshipDescription>
      <EntityRelationshipRoles>
        <EntityRelationshipRole>
          <NavPaneDisplayOption>UseCollectionName</NavPaneDisplayOption>
          <NavPaneArea>Details</NavPaneArea>
          <NavPaneOrder>10000</NavPaneOrder>
          <NavigationPropertyName>{attr}</NavigationPropertyName>
          <RelationshipRoleType>1</RelationshipRoleType>
        </EntityRelationshipRole>
        <EntityRelationshipRole>
          <NavigationPropertyName>{name}</NavigationPropertyName>
          <RelationshipRoleType>0</RelationshipRoleType>
        </EntityRelationshipRole>
      </EntityRelationshipRoles>
    </EntityRelationship>
"""


def optionset(name, display, options):
    opts = "".join(
        f"""        <option value="{100000000 + i}">
          <labels>
            <label description={label(text)} languagecode="1033" />
          </labels>
        </option>
""" for i, text in enumerate(options))
    return f"""    <optionset Name="{name}">
      <OptionSetType>picklist</OptionSetType>
      <IsGlobal>1</IsGlobal>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <displaynames>
        <displayname description={label(display)} languagecode="1033" />
      </displaynames>
      <Descriptions>
        <Description description="" languagecode="1033" />
      </Descriptions>
      <options>
{opts}      </options>
    </optionset>
"""


OPTION_SETS = {
    "cr_itemcategory": ("Item Category", ["Beverages", "Snacks", "Coffee & Tea", "Dairy", "Fruits",
                                          "Cleaning Supplies", "Paper Products", "Kitchen Supplies", "Other"]),
    "cr_itemunit": ("Item Unit", ["Each", "Pack", "Box", "Case", "Bag", "Bottle", "Carton", "Roll", "Kg"]),
    "cr_orderstatus": ("Order Status", ["Draft", "Submitted", "Approved", "Rejected", "Ordered",
                                        "Partially Received", "Received", "Cancelled"]),
    "cr_approvalstatus": ("Approval Status", ["Pending", "Approved", "Rejected", "Returned for Revision"]),
    "cr_approvalaction": ("Approval Action", ["Submitted", "Approved", "Rejected", "Returned",
                                              "Cancelled", "Resubmitted"]),
    "cr_suppliercategory": ("Supplier Category", ["Food & Beverage", "Office Supplies", "Cleaning Products",
                                                  "Kitchen Equipment", "Paper Products", "General"]),
}

FULL_ENTITIES = [
    ("cr_supplier", "Supplier", "Suppliers", "Supplier contact information and details", [
        a_primarykey("cr_supplierid", "Supplier"),
        a_primaryname("cr_name", "Supplier Name"),
        a_text("cr_contactperson", "Contact Person"),
        a_text("cr_email", "Email", 200, fmt="email"),
        a_text("cr_phone", "Phone", 50, fmt="phone"),
        a_text("cr_address", "Address", 500),
        a_text("cr_website", "Website", 200, fmt="url"),
        a_choice("cr_category", "Category", "cr_suppliercategory"),
        a_memo("cr_notes", "Notes"),
    ]),
    ("cr_pantryitem", "Pantry Item", "Pantry Items", "Inventory catalog of all pantry supplies", [
        a_primarykey("cr_pantryitemid", "Pantry Item"),
        a_primaryname("cr_name", "Item Name"),
        a_text("cr_sku", "SKU", 50),
        a_choice("cr_category", "Category", "cr_itemcategory"),
        a_choice("cr_unit", "Unit of Measure", "cr_itemunit"),
        a_int("cr_currentstock", "Current Stock"),
        a_int("cr_minimumstock", "Minimum Stock Level"),
        a_int("cr_reorderquantity", "Reorder Quantity"),
        a_decimal("cr_unitprice", "Unit Price"),
        a_lookup("cr_preferredsupplier", "Preferred Supplier"),
        a_text("cr_location", "Storage Location", 200),
        a_memo("cr_description", "Description"),
    ]),
    ("cr_supplyorder", "Supply Order", "Supply Orders", "Supply order requests and their approval status", [
        a_primarykey("cr_supplyorderid", "Supply Order"),
        a_primaryname("cr_name", "Order Number"),
        a_choice("cr_orderstatus", "Order Status", "cr_orderstatus"),
        a_choice("cr_approvalstatus", "Approval Status", "cr_approvalstatus"),
        a_datetime("cr_orderdate", "Order Date", date_only=True),
        a_datetime("cr_requiredbydate", "Required By Date", date_only=True),
        a_datetime("cr_approvaldate", "Approval Date"),
        a_decimal("cr_totalamount", "Total Amount"),
        a_text("cr_requestedby", "Requested By", 200),
        a_text("cr_approvedby", "Approved By", 200),
        a_memo("cr_justification", "Justification"),
        a_memo("cr_approvercomments", "Approver Comments"),
        a_text("cr_deliveryaddress", "Delivery Address", 500),
    ]),
    ("cr_orderlineitem", "Order Line Item", "Order Line Items", "Individual items within a supply order", [
        a_primarykey("cr_orderlineitemid", "Order Line Item"),
        a_primaryname("cr_name", "Line Item Name"),
        a_lookup("cr_supplyorder", "Supply Order"),
        a_lookup("cr_pantryitem", "Pantry Item"),
        a_lookup("cr_supplier", "Supplier"),
        a_int("cr_quantity", "Quantity"),
        a_decimal("cr_unitprice", "Unit Price"),
        a_decimal("cr_totalcost", "Total Cost"),
        a_memo("cr_notes", "Notes"),
    ]),
    ("cr_approvalhistory", "Approval History", "Approval History Records", "Audit trail for all approval decisions", [
        a_primarykey("cr_approvalhistoryid", "Approval History"),
        a_primaryname("cr_name", "Approval Record"),
        a_lookup("cr_supplyorder", "Supply Order"),
        a_choice("cr_action", "Action", "cr_approvalaction"),
        a_text("cr_approver", "Approver", 200),
        a_datetime("cr_actiondate", "Action Date"),
        a_memo("cr_comments", "Comments"),
        a_choice("cr_previousstatus", "Previous Status", "cr_approvalstatus"),
        a_choice("cr_newstatus", "New Status", "cr_approvalstatus"),
    ]),
]

# (referenced/parent, referencing/child, lookup attribute on child)
FULL_RELATIONSHIPS = [
    ("cr_supplier", "cr_pantryitem", "cr_preferredsupplier"),
    ("cr_supplyorder", "cr_orderlineitem", "cr_supplyorder"),
    ("cr_pantryitem", "cr_orderlineitem", "cr_pantryitem"),
    ("cr_supplier", "cr_orderlineitem", "cr_supplier"),
    ("cr_supplyorder", "cr_approvalhistory", "cr_supplyorder"),
]

TEST_ENTITIES = [
    ("cr_supplier", "Supplier", "Suppliers", "Supplier contact information and details", [
        a_primarykey("cr_supplierid", "Supplier"),
        a_primaryname("cr_name", "Supplier Name"),
    ]),
]


def customizations_xml(entities, relationships, optionsets):
    ents = "".join(entity(*e) for e in entities)
    rels = "".join(relationship(*r) for r in relationships)
    opts = "".join(optionset(n, d, o) for n, (d, o) in optionsets.items())
    rel_block = f"  <EntityRelationships>\n{rels}  </EntityRelationships>\n" if rels else "  <EntityRelationships />\n"
    opt_block = f"  <optionsets>\n{opts}  </optionsets>\n" if opts else "  <optionsets />\n"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="{ORG_VERSION}" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.24094.00198">
  <Entities>
{ents}  </Entities>
  <Roles></Roles>
  <Workflows></Workflows>
  <FieldSecurityProfiles></FieldSecurityProfiles>
  <Templates />
  <EntityMaps />
{rel_block}  <OrganizationSettings />
{opt_block}  <CustomControls />
  <EntityDataProviders />
  <Languages>
    <Language>1033</Language>
  </Languages>
</ImportExportXml>
"""


ADDRESS_FIELDS = ["City", "County", "Country", "Fax", "FreightTermsCode", "ImportSequenceNumber",
                  "Latitude", "Line1", "Line2", "Line3", "Longitude", "Name", "PostalCode",
                  "PostOfficeBox", "PrimaryContactName"]
ADDRESS_FIELDS_2 = ["StateOrProvince", "Telephone1", "Telephone2", "Telephone3",
                    "TimeZoneRuleVersionNumber", "UPSZone", "UTCOffset", "UTCConversionTimeZoneCode"]


def address(number):
    nil = lambda fields: "".join(f'          <{f} xsi:nil="true"></{f}>\n' for f in fields)
    return f"""        <Address>
          <AddressNumber>{number}</AddressNumber>
          <AddressTypeCode>1</AddressTypeCode>
{nil(ADDRESS_FIELDS)}          <ShippingMethodCode>1</ShippingMethodCode>
{nil(ADDRESS_FIELDS_2)}        </Address>
"""


def solution_xml(version, entities, optionsets):
    roots = "".join(f'      <RootComponent type="1" schemaName="{e[0]}" behavior="0" />\n' for e in entities)
    roots += "".join(f'      <RootComponent type="9" schemaName="{n}" behavior="0" />\n' for n in optionsets)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml version="{ORG_VERSION}" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" OrganizationVersion="{ORG_VERSION}" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.24094.00198" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SolutionManifest>
    <UniqueName>PantrySupplyOrdering</UniqueName>
    <LocalizedNames>
      <LocalizedName description="Pantry Supply Ordering" languagecode="1033" />
    </LocalizedNames>
    <Descriptions>
      <Description description="Automated Office Pantry Supply Ordering System" languagecode="1033" />
    </Descriptions>
    <Version>{version}</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>PantryDev</UniqueName>
      <LocalizedNames>
        <LocalizedName description="Pantry Dev" languagecode="1033" />
      </LocalizedNames>
      <Descriptions>
        <Description description="Publisher for Pantry Supply Ordering solution" languagecode="1033" />
      </Descriptions>
      <EMailAddress xsi:nil="true"></EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>{PREFIX}</CustomizationPrefix>
      <CustomizationOptionValuePrefix>10000</CustomizationOptionValuePrefix>
      <Addresses>
{address(1)}{address(2)}      </Addresses>
    </Publisher>
    <RootComponents>
{roots}    </RootComponents>
    <MissingDependencies />
  </SolutionManifest>
</ImportExportXml>
"""


CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/octet-stream" /></Types>"""


def build_zip(path, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    print(f"Wrote {path}")


def keep_attrs(entities, predicate):
    return [(*e[:4], [a for a in e[4] if predicate(a)]) for e in entities]


def is_core(attr):
    return "<Type>primarykey</Type>" in attr or "PrimaryName|" in attr


def is_not_lookup(attr):
    return "<Type>lookup</Type>" not in attr


def write_zip(filename, version, entities, relationships, optionsets):
    build_zip(os.path.join(ROOT, filename), {
        "[Content_Types].xml": CONTENT_TYPES,
        "customizations.xml": customizations_xml(entities, relationships, optionsets),
        "solution.xml": solution_xml(version, entities, optionsets)})


def main():
    full_cust = customizations_xml(FULL_ENTITIES, FULL_RELATIONSHIPS, OPTION_SETS)
    full_sol = solution_xml("1.0.0.0", FULL_ENTITIES, OPTION_SETS)
    for name, content in [("customizations.xml", full_cust), ("solution.xml", full_sol),
                          ("[Content_Types].xml", CONTENT_TYPES)]:
        with open(os.path.join(SOLUTION_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)
    write_zip("PantrySupplyOrdering_TEST.zip", "0.0.0.1", TEST_ENTITIES, [], {})
    # Staged builds: each one upgrades the previous, adding one layer.
    write_zip("Step1_Tables_and_Choices.zip", "0.0.1.0",
              keep_attrs(FULL_ENTITIES, is_core), [], OPTION_SETS)
    write_zip("Step2_All_Columns.zip", "0.0.2.0",
              keep_attrs(FULL_ENTITIES, is_not_lookup), [], OPTION_SETS)
    write_zip("PantrySupplyOrdering_1_0_0_0.zip", "1.0.0.0",
              FULL_ENTITIES, FULL_RELATIONSHIPS, OPTION_SETS)


if __name__ == "__main__":
    main()
