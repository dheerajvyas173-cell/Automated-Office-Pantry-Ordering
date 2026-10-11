"""Generates the canvas app screens (Src/*.pa.yaml) from a small Fluent 2 design system.

Run: python3 power-apps/canvas-app/generate_screens.py
Control types/versions follow Microsoft's modern controls docs (2026 updates).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Src")

TEXT, BUTTON, INPUT, NUMBER = "ModernText@1.0.0", "ModernButton@1.0.0", "ModernTextInput@1.0.0", "ModernNumberInput@1.0.0"
DATE, COMBO, BADGE, TABS = "ModernDatePicker@1.0.0", "ModernCombobox@1.0.0", "ModernBadge@1.0.0", "ModernTabList@1.0.0"
ICON, AVATAR, SPINNER = "ModernIcon@1.1.0", "ModernAvatar@1.0.0", "ModernSpinner@1.1.0"
CONTAINER, GALLERY, RECT = "GroupContainer@1.4.0", "Gallery@2.15.0", "Rectangle@2.3.0"
GALLERY_VARIANT = "BrowseLayout_Vertical_OneTextVariant_ver5.0"

OS = "[@'Order Status']"
OPEN_STATUSES = ["Draft", "Submitted", "Approved", "Ordered", "'Partially Received'"]
DONE_STATUSES = ["Received", "Rejected", "Cancelled"]
MONEY = '"#,##0.00"'


# --- YAML emitter -------------------------------------------------------------

def _formula(key, value, ind):
    value = str(value)
    if "\n" in value or ": " in value or " #" in value or value.endswith(":"):
        lines = ("=" + value).split("\n")
        return [f"{ind}{key}: |-"] + [f"{ind}  {line}" for line in lines]
    return [f"{ind}{key}: ={value}"]


def _control(c, ind):
    out = [f"{ind}- {c['name']}:", f"{ind}    Control: {c['type']}"]
    if c.get("variant"):
        out.append(f"{ind}    Variant: {c['variant']}")
    if c["props"]:
        out.append(f"{ind}    Properties:")
        for k in sorted(c["props"]):
            out += _formula(k, c["props"][k], ind + "      ")
    if c.get("children"):
        out.append(f"{ind}    Children:")
        for child in c["children"]:
            out += _control(child, ind + "      ")
    return out


def screen_yaml(name, props, children):
    out = ["Screens:", f"  {name}:", "    Properties:"]
    for k in sorted(props):
        out += _formula(k, props[k], "      ")
    out.append("    Children:")
    for child in children:
        out += _control(child, "      ")
    return "\n".join(out) + "\n"


def ctl(name, type_, variant=None, children=None, **props):
    return {"name": name, "type": type_, "variant": variant, "props": props, "children": children or []}


# --- Design system components ---------------------------------------------------

def text(name, value, size=14, weight="Normal", color="clrTextPrimary", **p):
    p.setdefault("Height", max(20, int(size * 1.6)))
    return ctl(name, TEXT, Text=value, Size=size, FontWeight=f"FontWeight.{weight}", Color=color, **p)


def button(name, label, on_select, appearance="Primary", icon=None, **p):
    if icon:
        p.setdefault("Icon", f'"{icon}"')
    p.setdefault("Height", 36)
    return ctl(name, BUTTON, Text=label, OnSelect=on_select, Appearance=f"ButtonAppearance.{appearance}", **p)


def badge(name, content, intent, **p):
    p.setdefault("Height", 24)
    return ctl(name, BADGE, Content=content, Intent=intent, Appearance="BadgeAppearance.Tint",
               Shape="BadgeShape.Rounded", **p)


def icon(name, glyph, color="clrTextSecondary", **p):
    p.setdefault("Width", 20)
    p.setdefault("Height", 20)
    return ctl(name, ICON, Icon=f'"{glyph}"', IconColor=color, **p)


def box(name, direction, children, gap=8, pad=0, **p):
    props = dict(LayoutDirection=f"LayoutDirection.{direction}", LayoutGap=gap,
                 PaddingTop=pad, PaddingBottom=pad, PaddingLeft=pad, PaddingRight=pad,
                 DropShadow="DropShadow.None", Fill="Color.Transparent")
    props.update(p)
    return ctl(name, CONTAINER, "AutoLayout", children, **props)


def card(name, direction, children, gap=12, pad=16, **p):
    p.setdefault("Fill", "clrSurface")
    p.setdefault("BorderColor", "clrStroke")
    p.setdefault("BorderThickness", 1)
    for corner in ("RadiusTopLeft", "RadiusTopRight", "RadiusBottomLeft", "RadiusBottomRight"):
        p.setdefault(corner, 8)
    return box(name, direction, children, gap=gap, pad=pad, **p)


def spacer(name):
    return box(name, "Horizontal", [], FillPortions=1, LayoutMinWidth=0, LayoutMinHeight=0)


def gallery(name, items, template_size, children, **p):
    p.setdefault("FillPortions", 1)
    p.setdefault("LayoutMinHeight", 120)
    return ctl(name, GALLERY, GALLERY_VARIANT, children, Items=items, TemplateSize=template_size,
               TemplatePadding=0, ShowScrollbar="true", BorderThickness=0, Fill="Color.Transparent", **p)


def row_divider(name):
    return ctl(name, RECT, Fill="clrStroke", Height=1, Width="Parent.TemplateWidth", Y="Parent.TemplateHeight - 1")


def empty_state(name, message, visible):
    return text(name, f'"{message}"', 13, color="clrTextSecondary", Align="Align.Center",
                Visible=visible, Height=48)


def section_title(name, value):
    return text(name, value, 16, "Semibold", Height=28)


# --- Shared formulas ----------------------------------------------------------------

def status_intent(expr):
    return (f'Switch(Text({expr}), "Received", BadgeIntent.Positive, "Ordered", BadgeIntent.Positive, '
            f'"Approved", BadgeIntent.Highlight, "Submitted", BadgeIntent.Informative, '
            f'"Partially Received", BadgeIntent.Caution, "Rejected", BadgeIntent.Critical, BadgeIntent.Neutral)')


def stock_label(item):
    return (f'If({item}.\'Current Stock\' <= 0, "Out of stock", '
            f'{item}.\'Current Stock\' <= {item}.\'Minimum Stock Level\', "Low stock", "In stock")')


def stock_intent(item):
    return (f"If({item}.'Current Stock' <= 0, BadgeIntent.Critical, "
            f"{item}.'Current Stock' <= {item}.'Minimum Stock Level', BadgeIntent.Caution, BadgeIntent.Positive)")


def add_to_cart(item, qty):
    return f"""With({{existing: LookUp(colCart, Item.'Pantry Item' = {item}.'Pantry Item'), qty: {qty}}},
    If(IsBlank(existing),
        Collect(colCart, {{Item: {item}, Qty: qty}}),
        Patch(colCart, existing, {{Qty: existing.Qty + qty}})
    )
);
If({item}.'Current Stock' > {item}.'Minimum Stock Level',
    Notify({item}.'Item Name' & " added. Note: the pantry still has " & {item}.'Current Stock' & " in stock.", NotificationType.Warning),
    Notify({item}.'Item Name' & " added to your request.", NotificationType.Success)
)"""


def status_filter(statuses):
    return "(" + " || ".join(f"'Order Status' = {OS}.{s}" for s in statuses) + ")"


MY_ORDERS = "'Requested By' = gUserEmail"


# --- Page frame: navigation rail + header ------------------------------------------------

NAV = [
    ("Home", "Dashboard", "Home", "HomeScreen"),
    ("NewOrder", "New request", "Add", "NewOrderScreen"),
    ("MyOrders", "My requests", "DocumentBulletList", "MyOrdersScreen"),
    ("Inventory", "Inventory", "Box", "InventoryScreen"),
]


def nav_rail(prefix, current):
    items = []
    for key, label, glyph, screen in NAV:
        selected = key == current
        caption = f'"{label}"'
        if key == "NewOrder":
            caption = f'"{label}" & If(CountRows(colCart) > 0, " (" & CountRows(colCart) & ")", "")'
        items.append(button(
            f"{prefix}Nav{key}", caption, f"Navigate({screen}, ScreenTransition.None)",
            "Secondary" if selected else "Subtle", glyph,
            IconStyle="IconStyle.Filled" if selected else "IconStyle.Outline",
            Layout="If(App.Width < 900, ButtonLayout.IconOnly, ButtonLayout.IconBefore)",
            Tooltip=f'"{label}"', AccessibleLabel=f'"{label}"', Height=40))
    return box(f"{prefix}NavRail", "Vertical", [
        box(f"{prefix}Brand", "Horizontal", [
            icon(f"{prefix}BrandIcon", "FoodPizza", "clrBrand", Width=28, Height=28, IconStyle="IconStyle.Filled"),
            text(f"{prefix}BrandName", '"Office Pantry"', 16, "Semibold", Visible="App.Width >= 900",
                 FillPortions=1, Height=28),
        ], gap=10, Height=48, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        *items,
        spacer(f"{prefix}NavSpacer"),
        box(f"{prefix}UserRow", "Horizontal", [
            ctl(f"{prefix}UserAvatar", AVATAR, Name="User().FullName", Image="User().Image",
                Shape="AvatarShape.Circular", Width=32, Height=32, Tooltip="User().FullName"),
            text(f"{prefix}UserName", "User().FullName", 13, Visible="App.Width >= 900", FillPortions=1,
                 Height=32, VerticalAlign="VerticalAlign.Middle"),
        ], gap=10, Height=48, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
    ], gap=4, pad=12, Width="If(App.Width < 900, 72, 232)", FillPortions=0, Fill="clrSurface",
        LayoutAlignItems="LayoutAlignItems.Stretch")


def page(name, prefix, current, title, subtitle, actions, body, overlays=(), screen_props=None):
    header = box(f"{prefix}Header", "Horizontal", [
        box(f"{prefix}TitleBlock", "Vertical", [
            text(f"{prefix}Title", f'"{title}"', 24, "Semibold", Height=36),
            text(f"{prefix}Subtitle", subtitle, 14, color="clrTextSecondary", Height=22),
        ], gap=2, FillPortions=1, LayoutJustifyContent="LayoutJustifyContent.Center"),
        box(f"{prefix}Actions", "Horizontal", actions, gap=8, FillPortions=0, Width=f"{150 * max(1, len(actions))}",
            LayoutJustifyContent="LayoutJustifyContent.End", LayoutAlignItems="LayoutAlignItems.Center"),
    ], Height=64, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center")
    main = box(f"{prefix}Main", "Vertical", [header, *body], gap=16, pad=24, FillPortions=1,
               LayoutAlignItems="LayoutAlignItems.Stretch")
    root = box(f"{prefix}Root", "Horizontal", [nav_rail(prefix, current), main], gap=0,
               Width="Parent.Width", Height="Parent.Height", X=0, Y=0, Fill="clrCanvas",
               LayoutAlignItems="LayoutAlignItems.Stretch")
    busy = ctl(f"{prefix}Busy", CONTAINER, "ManualLayout", [
        ctl(f"{prefix}BusyCard", CONTAINER, "ManualLayout", [
            ctl(f"{prefix}BusySpinner", SPINNER, Label='"Saving your request..."', Width=240, Height=80,
                X=20, Y=20, LabelPosition="SpinnerLabelPosition.Below"),
        ], Fill="clrSurface", Width=280, Height=120, X="(Parent.Width - Self.Width) / 2",
            Y="(Parent.Height - Self.Height) / 2", RadiusTopLeft=8, RadiusTopRight=8, RadiusBottomLeft=8,
            RadiusBottomRight=8),
    ], Fill="RGBA(0, 0, 0, 0.35)", Width="Parent.Width", Height="Parent.Height", X=0, Y=0, Visible="locBusy")
    props = {"Fill": "clrCanvas"}
    props.update(screen_props or {})
    return screen_yaml(name, props, [root, *overlays, busy])


def confirm_dialog(prefix, visible, title, message, confirm_label, on_confirm, on_cancel):
    return ctl(f"{prefix}Dialog", CONTAINER, "ManualLayout", [
        card(f"{prefix}DialogCard", "Vertical", [
            text(f"{prefix}DialogTitle", f'"{title}"', 20, "Semibold", Height=32),
            text(f"{prefix}DialogText", f'"{message}"', 14, color="clrTextSecondary", Height=60,
                 VerticalAlign="VerticalAlign.Top"),
            box(f"{prefix}DialogButtons", "Horizontal", [
                spacer(f"{prefix}DialogSpacer"),
                button(f"{prefix}DialogCancel", '"Keep request"', on_cancel, "Secondary", Width=140),
                button(f"{prefix}DialogConfirm", f'"{confirm_label}"', on_confirm, "Primary", Width=160),
            ], Height=40, FillPortions=0),
        ], gap=16, pad=24, Width=440, Height=200, X="(Parent.Width - Self.Width) / 2",
            Y="(Parent.Height - Self.Height) / 2"),
    ], Fill="RGBA(0, 0, 0, 0.35)", Width="Parent.Width", Height="Parent.Height", X=0, Y=0, Visible=visible)


# --- Screens ----------------------------------------------------------------------

def kpi(prefix, key, caption, value, hint, glyph, accent="clrBrand"):
    return card(f"{prefix}Kpi{key}", "Vertical", [
        box(f"{prefix}Kpi{key}Head", "Horizontal", [
            icon(f"{prefix}Kpi{key}Icon", glyph, accent, IconStyle="IconStyle.Filled"),
            text(f"{prefix}Kpi{key}Caption", f'"{caption}"', 13, "Semibold", color="clrTextSecondary",
                 FillPortions=1, Height=20),
        ], Height=24, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        text(f"{prefix}Kpi{key}Value", value, 30, "Semibold", Height=44),
        text(f"{prefix}Kpi{key}Hint", f'"{hint}"', 12, color="clrTextSecondary", Height=18),
    ], gap=4, FillPortions=1, LayoutMinWidth=160)


def home_screen():
    p = "Hm"
    low = "Filter(colItems, 'Current Stock' <= 'Minimum Stock Level')"
    on_visible = f"""Concurrent(
    UpdateContext({{locMyOpen: CountRows(Filter('Supply Orders', {MY_ORDERS} && {status_filter(["Submitted", "Approved", "Ordered"])}))}}),
    UpdateContext({{locAwaiting: CountRows(Filter('Supply Orders', {MY_ORDERS} && 'Order Status' = {OS}.Submitted))}}),
    UpdateContext({{locRecent: FirstN(Sort(Filter('Supply Orders', {MY_ORDERS}), 'Created On', SortOrder.Descending), 6)}})
)"""
    kpis = box(f"{p}Kpis", "Horizontal", [
        kpi(p, "Low", "Low stock items", f"CountRows({low})", "At or below minimum level", "Warning",
            f"If(CountRows({low}) > 0, clrDanger, clrSuccess)"),
        kpi(p, "Open", "My open requests", "locMyOpen", "Submitted, approved or ordered", "DocumentBulletList"),
        kpi(p, "Awaiting", "Awaiting approval", "locAwaiting", "Waiting for your approver", "Clock"),
        kpi(p, "Catalog", "Items in catalog", "CountRows(colItems)", "Pantry items you can request", "Box"),
    ], gap=16, Height=124, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Stretch")

    restock = card(f"{p}Restock", "Vertical", [
        box(f"{p}RestockHead", "Horizontal", [
            section_title(f"{p}RestockTitle", '"Needs restocking"'),
            spacer(f"{p}RestockSpacer"),
            button(f"{p}RestockAll", '"View inventory"',
                   "Navigate(InventoryScreen, ScreenTransition.None)", "Subtle",
                   "ArrowRight", Layout="ButtonLayout.IconAfter", Width=150),
        ], Height=36, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        gallery(f"{p}RestockList", f"Sort({low}, 'Current Stock')", 60, [
            text(f"{p}RsName", "ThisItem.'Item Name'", 14, "Semibold", X=8, Y=8, Width="Parent.TemplateWidth - 260"),
            text(f"{p}RsMeta", '"In stock " & Coalesce(ThisItem.\'Current Stock\', 0) & "  ·  Minimum " & Coalesce(ThisItem.\'Minimum Stock Level\', 0)',
                 12, color="clrTextSecondary", X=8, Y=32, Width="Parent.TemplateWidth - 260"),
            badge(f"{p}RsBadge", stock_label("ThisItem"), stock_intent("ThisItem"),
                  X="Parent.TemplateWidth - 240", Y=18, Width=100),
            button(f"{p}RsAdd", '"Request"', add_to_cart("ThisItem", "Coalesce(ThisItem.'Reorder Quantity', 1)"),
                   "Outline", "Add", X="Parent.TemplateWidth - 128", Y=12, Width=116, Height=34,
                   Tooltip='"Add the reorder quantity to your request"'),
            row_divider(f"{p}RsDivider"),
        ]),
        empty_state(f"{p}RestockEmpty", "Everything is well stocked.", f"IsEmpty({p}RestockList.AllItems)"),
    ], FillPortions=1, LayoutMinWidth=320, LayoutAlignItems="LayoutAlignItems.Stretch")

    recent = card(f"{p}Recent", "Vertical", [
        box(f"{p}RecentHead", "Horizontal", [
            section_title(f"{p}RecentTitle", '"My recent requests"'),
            spacer(f"{p}RecentSpacer"),
            button(f"{p}RecentAll", '"All requests"', "Navigate(MyOrdersScreen, ScreenTransition.None)",
                   "Subtle", "ArrowRight", Layout="ButtonLayout.IconAfter", Width=140),
        ], Height=36, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        gallery(f"{p}RecentList", "locRecent", 60, [
            text(f"{p}RcNumber", "ThisItem.'Order Number'", 14, "Semibold", X=8, Y=8, Width="Parent.TemplateWidth - 160"),
            text(f"{p}RcMeta", f'Text(ThisItem.\'Created On\', "dd mmm yyyy") & "  ·  " & Text(Coalesce(ThisItem.\'Total Amount\', 0), {MONEY})',
                 12, color="clrTextSecondary", X=8, Y=32, Width="Parent.TemplateWidth - 160"),
            badge(f"{p}RcBadge", "Text(ThisItem.'Order Status')", status_intent("ThisItem.'Order Status'"),
                  X="Parent.TemplateWidth - 140", Y=18, Width=128),
            row_divider(f"{p}RcDivider"),
        ], OnSelect="Set(gSelOrder, ThisItem); Navigate(MyOrdersScreen, ScreenTransition.None)"),
        empty_state(f"{p}RecentEmpty", "You have no requests yet.", f"IsEmpty({p}RecentList.AllItems)"),
    ], FillPortions=1, LayoutMinWidth=320, LayoutAlignItems="LayoutAlignItems.Stretch")

    body = [kpis, box(f"{p}Panels", "Horizontal", [restock, recent], gap=16, FillPortions=1,
                      LayoutAlignItems="LayoutAlignItems.Stretch")]
    actions = [
        button(f"{p}Refresh", '"Refresh"', "Refresh('Pantry Items'); ClearCollect(colItems, Sort('Pantry Items', 'Item Name'))",
               "Subtle", "ArrowClockwise", Width=120),
        button(f"{p}New", '"New request"', "Navigate(NewOrderScreen, ScreenTransition.None)", "Primary", "Add", Width=150),
    ]
    return page("HomeScreen", p, "Home", "Dashboard", '"Welcome back, " & First(Split(User().FullName, " ")).Value',
                actions, body, screen_props={"OnVisible": on_visible})


def new_order_screen():
    p = "No"
    catalog_items = (f"Sort(Filter(colItems, (IsBlank({p}Search.Text) || StartsWith('Item Name', {p}Search.Text)) && "
                     f"(IsBlank({p}Category.Selected) || Category = {p}Category.Selected.Value)), 'Item Name')")
    total = "Sum(colCart, Qty * Coalesce(Item.'Unit Price', 0))"
    submit = f"""If(IsBlank({p}RequiredBy.SelectedDate),
    Notify("Choose a required-by date.", NotificationType.Error),
    UpdateContext({{locBusy: true}});
    IfError(
        Set(gNewOrder, Patch('Supply Orders', Defaults('Supply Orders'), {{
            'Order Number': "PO-" & Text(Now(), "yyyymmdd-hhmmss"),
            'Order Status': {OS}.Draft,
            'Required By Date': {p}RequiredBy.SelectedDate,
            Justification: {p}Justification.Text,
            'Delivery Address': {p}Location.Text,
            'Requested By': gUserEmail,
            'Total Amount': {total}
        }}));
        Collect('Order Line Items', ForAll(colCart As L, {{
            'Line Item Name': L.Item.'Item Name',
            'Supply Order': gNewOrder,
            'Pantry Item': L.Item,
            Supplier: L.Item.'Preferred Supplier',
            Quantity: L.Qty,
            'Unit Price': L.Item.'Unit Price',
            'Total Cost': L.Qty * Coalesce(L.Item.'Unit Price', 0)
        }}));
        Patch('Supply Orders', gNewOrder, {{'Order Status': {OS}.Submitted}});
        Notify("Request " & gNewOrder.'Order Number' & " submitted for approval.", NotificationType.Success);
        Clear(colCart);
        Reset({p}Justification);
        Reset({p}Location);
        Set(gSelOrder, gNewOrder);
        UpdateContext({{locBusy: false}});
        Navigate(MyOrdersScreen, ScreenTransition.None),
        UpdateContext({{locBusy: false}});
        Notify("Your request couldn't be submitted: " & FirstError.Message, NotificationType.Error)
    )
)"""
    catalog = card(f"{p}Catalog", "Vertical", [
        section_title(f"{p}CatalogTitle", '"1. Choose items"'),
        box(f"{p}Toolbar", "Horizontal", [
            ctl(f"{p}Search", INPUT, Placeholder='"Search items"', Type="TextInputType.Search",
                TriggerOutput="TriggerOutput.Delayed", AccessibleLabel='"Search items"', FillPortions=1, Height=36),
            ctl(f"{p}Category", COMBO, Items="Choices([@'Item Category'])", SelectMultiple="false",
                InputTextPlaceholder='"All categories"', AccessibleLabel='"Filter by category"', Width=220, Height=36),
        ], Height=36, FillPortions=0),
        gallery(f"{p}Items", catalog_items, 72, [
            text(f"{p}ItName", "ThisItem.'Item Name'", 14, "Semibold", X=8, Y=10, Width="Parent.TemplateWidth - 380"),
            text(f"{p}ItMeta", f'Text(ThisItem.Category) & "  ·  " & Text(ThisItem.\'Unit of Measure\') & "  ·  " & Text(Coalesce(ThisItem.\'Unit Price\', 0), {MONEY})',
                 12, color="clrTextSecondary", X=8, Y=36, Width="Parent.TemplateWidth - 380"),
            badge(f"{p}ItStock", f"{stock_label('ThisItem')} & \" (\" & Coalesce(ThisItem.'Current Stock', 0) & \")\"",
                  stock_intent("ThisItem"), X="Parent.TemplateWidth - 364", Y=24, Width=130),
            ctl(f"{p}ItQty", NUMBER, Default=1, Min=1, Max=999, Step=1, Precision="DecimalPrecision.'0'",
                AccessibleLabel='"Quantity of " & ThisItem.\'Item Name\'', X="Parent.TemplateWidth - 222", Y=18,
                Width=96, Height=36),
            button(f"{p}ItAdd", '"Add"', add_to_cart("ThisItem", f"{p}ItQty.Value"), "Outline", "Add",
                   X="Parent.TemplateWidth - 116", Y=18, Width=104),
            row_divider(f"{p}ItDivider"),
        ]),
        empty_state(f"{p}ItemsEmpty", "No items match your search.", f"IsEmpty({p}Items.AllItems)"),
    ], FillPortions=1, LayoutMinWidth=420, LayoutAlignItems="LayoutAlignItems.Stretch")

    field_label = lambda name, value: text(name, value, 13, "Semibold", Height=20)
    cart = card(f"{p}Cart", "Vertical", [
        box(f"{p}CartHead", "Horizontal", [
            section_title(f"{p}CartTitle", '"2. Your request"'),
            spacer(f"{p}CartSpacer"),
            badge(f"{p}CartCount", 'CountRows(colCart) & If(CountRows(colCart) = 1, " item", " items")',
                  "BadgeIntent.Informative", Width=80),
        ], Height=28, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        empty_state(f"{p}CartEmpty", "Add items from the catalog to start a request.", "IsEmpty(colCart)"),
        gallery(f"{p}CartList", "colCart", 56, [
            text(f"{p}CtName", "ThisItem.Item.'Item Name'", 13, "Semibold", X=4, Y=6, Width="Parent.TemplateWidth - 150"),
            text(f"{p}CtLine", f"Text(ThisItem.Qty * Coalesce(ThisItem.Item.'Unit Price', 0), {MONEY})", 12,
                 color="clrTextSecondary", X=4, Y=30, Width="Parent.TemplateWidth - 150"),
            ctl(f"{p}CtQty", NUMBER, Default="ThisItem.Qty", Min=1, Max=999, Step=1, Precision="DecimalPrecision.'0'",
                OnChange="Patch(colCart, ThisItem, {Qty: Self.Value})",
                AccessibleLabel='"Quantity of " & ThisItem.Item.\'Item Name\'',
                X="Parent.TemplateWidth - 140", Y=10, Width=88, Height=36),
            ctl(f"{p}CtRemove", ICON, Icon='"Delete"', IconColor="clrDanger", OnSelect="Remove(colCart, ThisItem)",
                Tooltip='"Remove"', AccessibleLabel='"Remove " & ThisItem.Item.\'Item Name\'',
                X="Parent.TemplateWidth - 40", Y=16, Width=24, Height=24),
            row_divider(f"{p}CtDivider"),
        ], LayoutMinHeight=112, Visible="!IsEmpty(colCart)"),
        box(f"{p}TotalRow", "Horizontal", [
            text(f"{p}TotalLabel", '"Estimated total"', 14, "Semibold", FillPortions=1),
            text(f"{p}TotalValue", f"Text({total}, {MONEY})", 16, "Semibold", Align="Align.Right", Width=140),
        ], Height=28, FillPortions=0),
        field_label(f"{p}RequiredByLabel", '"Required by"'),
        ctl(f"{p}RequiredBy", DATE, DefaultDate="DateAdd(Today(), 3, TimeUnit.Days)", StartDate="Today()",
            Placeholder='"Select a date"', AccessibleLabel='"Required by date"', Height=36),
        field_label(f"{p}LocationLabel", '"Delivery location"'),
        ctl(f"{p}Location", INPUT, Placeholder='"For example: 3rd floor pantry"', AccessibleLabel='"Delivery location"', Height=36),
        field_label(f"{p}JustificationLabel", '"Justification (optional)"'),
        ctl(f"{p}Justification", INPUT, Placeholder='"Why is this needed?"', Type="TextInputType.Multiline",
            TriggerOutput="TriggerOutput.FocusOut", MaxLength=1000, AccessibleLabel='"Justification"', Height=72),
        button(f"{p}Submit", '"Submit for approval"', submit, "Primary", "Send", Height=40,
               DisplayMode="If(IsEmpty(colCart) || locBusy, DisplayMode.Disabled, DisplayMode.Edit)"),
    ], gap=10, Width="If(App.Width < 1200, 340, 400)", FillPortions=0, LayoutAlignItems="LayoutAlignItems.Stretch",
        LayoutOverflowY="LayoutOverflow.Scroll")

    body = [box(f"{p}Body", "Horizontal", [catalog, cart], gap=16, FillPortions=1,
                LayoutAlignItems="LayoutAlignItems.Stretch")]
    actions = [button(f"{p}Clear", '"Clear request"', "Clear(colCart)", "Subtle", "Dismiss", Width=150,
                      DisplayMode="If(IsEmpty(colCart), DisplayMode.Disabled, DisplayMode.Edit)")]
    return page("NewOrderScreen", p, "NewOrder", "New request",
                '"Pick the supplies you need. Your approver is notified when you submit."', actions, body)


def my_orders_screen():
    p = "Mo"
    search = f"StartsWith('Order Number', {p}Search.Text)"
    base = f"{MY_ORDERS} && {search}"
    items = f"""Sort(
    Switch({p}Tabs.Selected.Value,
        "Open", Filter('Supply Orders', {base} && {status_filter(OPEN_STATUSES)}),
        "Completed", Filter('Supply Orders', {base} && {status_filter(DONE_STATUSES)}),
        Filter('Supply Orders', {base})
    ),
    'Created On', SortOrder.Descending
)"""
    selected = f"!IsBlank(gSelOrder) && ThisItem.'Supply Order' = gSelOrder.'Supply Order'"
    order_list = card(f"{p}List", "Vertical", [
        ctl(f"{p}Tabs", TABS, Items='["All", "Open", "Completed"]', Default='"All"',
            Appearance="TabListAppearance.Subtle", Alignment="TabListAlignment.Start",
            AccessibleLabel='"Filter requests"', Height=40),
        ctl(f"{p}Search", INPUT, Placeholder='"Search by request number"', Type="TextInputType.Search",
            TriggerOutput="TriggerOutput.Delayed", AccessibleLabel='"Search requests"', Height=36),
        gallery(f"{p}Orders", items, 68, [
            ctl(f"{p}OrSelectedBar", RECT, Fill="clrBrand", Width=3, Height="Parent.TemplateHeight - 16", X=0, Y=8,
                Visible=selected),
            text(f"{p}OrNumber", "ThisItem.'Order Number'", 14, "Semibold", X=12, Y=10, Width="Parent.TemplateWidth - 160"),
            text(f"{p}OrMeta", f'Text(ThisItem.\'Created On\', "dd mmm yyyy") & "  ·  " & Text(Coalesce(ThisItem.\'Total Amount\', 0), {MONEY})',
                 12, color="clrTextSecondary", X=12, Y=36, Width="Parent.TemplateWidth - 160"),
            badge(f"{p}OrBadge", "Text(ThisItem.'Order Status')", status_intent("ThisItem.'Order Status'"),
                  X="Parent.TemplateWidth - 140", Y=22, Width=128),
            row_divider(f"{p}OrDivider"),
        ], OnSelect="Set(gSelOrder, ThisItem)", TemplateFill=f"If({selected}, clrBrandTint, Color.Transparent)"),
        empty_state(f"{p}OrdersEmpty", "No requests found.", f"IsEmpty({p}Orders.AllItems)"),
    ], gap=10, Width="If(App.Width < 1200, 360, 420)", FillPortions=0, LayoutAlignItems="LayoutAlignItems.Stretch")

    o = "gSelOrder"
    field = lambda key, caption, value: box(f"{p}F{key}", "Vertical", [
        text(f"{p}F{key}Caption", f'"{caption}"', 12, color="clrTextSecondary", Height=18),
        text(f"{p}F{key}Value", value, 14, "Semibold", Height=22),
    ], gap=2, FillPortions=1, LayoutMinWidth=120)
    history = f"Sort(Filter('Approval History Records', 'Supply Order'.'Supply Order' = {o}.'Supply Order'), 'Action Date', SortOrder.Descending)"
    detail_body = box(f"{p}DetailBody", "Vertical", [
        box(f"{p}DetailHead", "Horizontal", [
            text(f"{p}DetailNumber", f"{o}.'Order Number'", 20, "Semibold", FillPortions=1, Height=32),
            badge(f"{p}DetailBadge", f"Text({o}.'Order Status')", status_intent(f"{o}.'Order Status'"), Width=140, Height=28),
            button(f"{p}CancelBtn", '"Cancel request"', "UpdateContext({locConfirmCancel: true})", "Outline", "Dismiss",
                   Width=160, Visible=f"Text({o}.'Order Status') in [\"Draft\", \"Submitted\"]"),
        ], gap=12, Height=40, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center"),
        box(f"{p}Fields", "Horizontal", [
            field("Created", "Created", f'Text({o}.\'Created On\', "dd mmm yyyy")'),
            field("Required", "Required by", f'Text({o}.\'Required By Date\', "dd mmm yyyy")'),
            field("Total", "Estimated total", f"Text(Coalesce({o}.'Total Amount', 0), {MONEY})"),
            field("Approval", "Approval", f'Coalesce(Text({o}.\'Approval Status\'), "Not started")'),
        ], gap=16, Height=44, FillPortions=0),
        text(f"{p}Comments", f'"Approver comments: " & {o}.\'Approver Comments\'', 13, color="clrTextSecondary",
             Visible=f"!IsBlank({o}.'Approver Comments')", Height=40, VerticalAlign="VerticalAlign.Top"),
        box(f"{p}DetailCols", "Horizontal", [
            box(f"{p}LinesCol", "Vertical", [
                section_title(f"{p}LinesTitle", '"Items"'),
                gallery(f"{p}Lines", f"Filter('Order Line Items', 'Supply Order'.'Supply Order' = {o}.'Supply Order')", 56, [
                    text(f"{p}LnName", "ThisItem.'Line Item Name'", 13, "Semibold", X=4, Y=6, Width="Parent.TemplateWidth - 120"),
                    text(f"{p}LnSupplier", 'Coalesce(ThisItem.Supplier.\'Supplier Name\', "No supplier set")', 12,
                         color="clrTextSecondary", X=4, Y=30, Width="Parent.TemplateWidth - 120"),
                    text(f"{p}LnQty", '"× " & ThisItem.Quantity', 14, "Semibold", Align="Align.Right",
                         X="Parent.TemplateWidth - 112", Y=14, Width=104),
                    row_divider(f"{p}LnDivider"),
                ]),
            ], gap=8, FillPortions=1, LayoutAlignItems="LayoutAlignItems.Stretch"),
            box(f"{p}HistoryCol", "Vertical", [
                section_title(f"{p}HistoryTitle", '"Approval history"'),
                gallery(f"{p}History", history, 64, [
                    ctl(f"{p}HsDot", ICON, Icon='"CircleSmall"', IconColor="clrBrand", IconStyle="IconStyle.Filled",
                        X=0, Y=8, Width=20, Height=20),
                    text(f"{p}HsAction", 'Text(ThisItem.Action) & " by " & Coalesce(ThisItem.Approver, "system")', 13,
                         "Semibold", X=24, Y=6, Width="Parent.TemplateWidth - 28"),
                    text(f"{p}HsMeta", 'Text(ThisItem.\'Action Date\', "dd mmm yyyy, hh:mm") & If(IsBlank(ThisItem.Comments), "", "  ·  " & ThisItem.Comments)',
                         12, color="clrTextSecondary", X=24, Y=30, Width="Parent.TemplateWidth - 28"),
                ]),
                empty_state(f"{p}HistoryEmpty", "No approval activity yet.", f"IsEmpty({p}History.AllItems)"),
            ], gap=8, FillPortions=1, LayoutAlignItems="LayoutAlignItems.Stretch"),
        ], gap=24, FillPortions=1, LayoutAlignItems="LayoutAlignItems.Stretch"),
    ], gap=16, FillPortions=1, Visible=f"!IsBlank({o})", LayoutAlignItems="LayoutAlignItems.Stretch")
    detail = card(f"{p}Detail", "Vertical", [
        detail_body,
        empty_state(f"{p}DetailEmpty", "Select a request to see its items and approval history.", f"IsBlank({o})"),
    ], gap=16, pad=24, FillPortions=1, LayoutMinWidth=420, LayoutAlignItems="LayoutAlignItems.Stretch")

    cancel = f"""UpdateContext({{locConfirmCancel: false, locBusy: true}});
IfError(
    Patch('Supply Orders', {o}, {{'Order Status': {OS}.Cancelled}});
    Set({o}, LookUp('Supply Orders', 'Supply Order' = {o}.'Supply Order'));
    Notify("Request cancelled.", NotificationType.Success),
    Notify("Couldn't cancel the request: " & FirstError.Message, NotificationType.Error)
);
UpdateContext({{locBusy: false}})"""
    dialog = confirm_dialog(p, "locConfirmCancel", "Cancel this request?",
                            "The request will be marked as cancelled and won't be sent to suppliers.",
                            "Cancel request", cancel, "UpdateContext({locConfirmCancel: false})")
    body = [box(f"{p}Body", "Horizontal", [order_list, detail], gap=16, FillPortions=1,
                LayoutAlignItems="LayoutAlignItems.Stretch")]
    actions = [
        button(f"{p}Refresh", '"Refresh"', f"Refresh('Supply Orders'); If(!IsBlank({o}), Set({o}, LookUp('Supply Orders', 'Supply Order' = {o}.'Supply Order')))",
               "Subtle", "ArrowClockwise", Width=120),
        button(f"{p}New", '"New request"', "Navigate(NewOrderScreen, ScreenTransition.None)", "Primary", "Add", Width=150),
    ]
    on_visible = f"If(!IsBlank({o}), Set({o}, LookUp('Supply Orders', 'Supply Order' = {o}.'Supply Order')))"
    return page("MyOrdersScreen", p, "MyOrders", "My requests", '"Track your supply requests and their approvals."',
                actions, body, overlays=[dialog], screen_props={"OnVisible": on_visible})


def inventory_screen():
    p = "Iv"
    items = (f"Sort(Filter(colItems, (IsBlank({p}Search.Text) || StartsWith('Item Name', {p}Search.Text) || StartsWith(SKU, {p}Search.Text)) && "
             f"(IsBlank({p}Category.Selected) || Category = {p}Category.Selected.Value) && "
             f"Switch({p}Tabs.Selected.Value, \"Low stock\", 'Current Stock' <= 'Minimum Stock Level', "
             f"\"Out of stock\", 'Current Stock' <= 0, true)), 'Item Name')")
    # (key, header, cell formula, x fraction, width fraction, align)
    cols = [
        ("Item", "Item", "ThisItem.'Item Name'", 0.00, 0.24, "Left"),
        ("Cat", "Category", "Text(ThisItem.Category)", 0.24, 0.14, "Left"),
        ("Stock", "In stock", "Coalesce(ThisItem.'Current Stock', 0)", 0.38, 0.08, "Right"),
        ("Min", "Minimum", "Coalesce(ThisItem.'Minimum Stock Level', 0)", 0.46, 0.08, "Right"),
        ("Price", "Unit price", f"Text(Coalesce(ThisItem.'Unit Price', 0), {MONEY})", 0.54, 0.09, "Right"),
        ("Loc", "Location", "Coalesce(ThisItem.'Storage Location', \"-\")", 0.65, 0.12, "Left"),
    ]
    header_cells = [text(f"{p}H{k}", f'"{h}"', 12, "Semibold", color="clrTextSecondary", Align=f"Align.{a}",
                         X=f"Parent.Width * {x} + 12", Y=8, Width=f"Parent.Width * {w} - 8", Height=20)
                    for k, h, _, x, w, a in cols]
    header_cells.append(text(f"{p}HStatus", '"Status"', 12, "Semibold", color="clrTextSecondary",
                             X="Parent.Width * 0.78 + 12", Y=8, Width=120, Height=20))
    row_cells = [text(f"{p}C{k}", f, 13, "Semibold" if k == "Item" else "Normal", Align=f"Align.{a}",
                      X=f"Parent.TemplateWidth * {x} + 12", Y=14, Width=f"Parent.TemplateWidth * {w} - 8", Height=24)
                 for k, _, f, x, w, a in cols]
    row_cells += [
        badge(f"{p}CStatus", stock_label("ThisItem"), stock_intent("ThisItem"),
              X="Parent.TemplateWidth * 0.78 + 12", Y=14, Width=110),
        button(f"{p}CAdd", '"Request"', add_to_cart("ThisItem", "Coalesce(ThisItem.'Reorder Quantity', 1)"), "Subtle", "Add",
               X="Parent.TemplateWidth - 124", Y=8, Width=112, Height=36,
               Tooltip='"Add the reorder quantity to your request"'),
        row_divider(f"{p}CDivider"),
    ]
    toolbar = box(f"{p}Toolbar", "Horizontal", [
        ctl(f"{p}Tabs", TABS, Items='["All", "Low stock", "Out of stock"]', Default='"All"',
            Appearance="TabListAppearance.Subtle", Alignment="TabListAlignment.Start",
            AccessibleLabel='"Filter by stock level"', Width=340, Height=40),
        spacer(f"{p}ToolbarSpacer"),
        ctl(f"{p}Search", INPUT, Placeholder='"Search by name or SKU"', Type="TextInputType.Search",
            TriggerOutput="TriggerOutput.Delayed", AccessibleLabel='"Search inventory"', Width=280, Height=36),
        ctl(f"{p}Category", COMBO, Items="Choices([@'Item Category'])", SelectMultiple="false",
            InputTextPlaceholder='"All categories"', AccessibleLabel='"Filter by category"', Width=220, Height=36),
    ], gap=12, Height=40, FillPortions=0, LayoutAlignItems="LayoutAlignItems.Center")
    table = card(f"{p}Table", "Vertical", [
        ctl(f"{p}HeaderRow", CONTAINER, "ManualLayout", header_cells, Height=36, FillPortions=0,
            Fill="clrCanvas", RadiusTopLeft=4, RadiusTopRight=4, RadiusBottomLeft=4, RadiusBottomRight=4),
        gallery(f"{p}Rows", items, 52, row_cells),
        empty_state(f"{p}RowsEmpty", "No items match these filters.", f"IsEmpty({p}Rows.AllItems)"),
        text(f"{p}Count", f'CountRows({p}Rows.AllItems) & " of " & CountRows(colItems) & " items"', 12,
             color="clrTextSecondary", Height=18),
    ], gap=8, FillPortions=1, LayoutAlignItems="LayoutAlignItems.Stretch")
    actions = [button(f"{p}Refresh", '"Refresh"', "Refresh('Pantry Items'); ClearCollect(colItems, Sort('Pantry Items', 'Item Name'))",
                      "Subtle", "ArrowClockwise", Width=120)]
    return page("InventoryScreen", p, "Inventory", "Inventory",
                '"Current stock for every pantry item. Request anything that is running low."',
                actions, [toolbar, table])


APP = """App:
  Properties:
    Formulas: |-
      =clrBrand = ColorValue("#0F6CBD");
      clrBrandTint = ColorValue("#EBF3FC");
      clrCanvas = ColorValue("#F5F5F5");
      clrSurface = Color.White;
      clrStroke = ColorValue("#E0E0E0");
      clrTextPrimary = ColorValue("#242424");
      clrTextSecondary = ColorValue("#616161");
      clrSuccess = ColorValue("#107C10");
      clrDanger = ColorValue("#C50F1F");
      gUserEmail = Lower(User().Email);
    OnStart: =ClearCollect(colItems, Sort('Pantry Items', 'Item Name'))
    Theme: =PantryTheme
"""

EDITOR_STATE = """EditorState:
  ScreensOrder:
    - HomeScreen
    - NewOrderScreen
    - MyOrdersScreen
    - InventoryScreen
"""


def main():
    for f in os.listdir(SRC):
        if f.endswith(".pa.yaml"):
            os.remove(os.path.join(SRC, f))
    files = {
        "App.pa.yaml": APP,
        "_EditorState.pa.yaml": EDITOR_STATE,
        "HomeScreen.pa.yaml": home_screen(),
        "NewOrderScreen.pa.yaml": new_order_screen(),
        "MyOrdersScreen.pa.yaml": my_orders_screen(),
        "InventoryScreen.pa.yaml": inventory_screen(),
    }
    for name, content in files.items():
        with open(os.path.join(SRC, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Wrote Src/{name}")


if __name__ == "__main__":
    main()
