import unittest
from pathlib import Path

from lupa import LuaRuntime


SOURCE = (Path(__file__).resolve().parents[1] / "QuickBuyout.lua").read_text()

WOW_API = """
Enum = {ItemClass = {Weapon=2, Armor=4, Consumable=0, Gem=3,
    ItemEnhancement=8, CurrencyTokenObsolete=10, PermanentObsolete=14,
    Miscellaneous=15, Tradegoods=7},
    AuctionHouseError={ItemNotFound=1, NotEnoughMoney=2, IsBusy=3, DatabaseError=4}}
local names = {[2]="Weapons", [4]="Armor", [0]="Consumables",
    [3]="Generic(OBSOLETE)", [8]="Jewelry(OBSOLETE)",
    [10]="Money(OBSOLETE)", [14]="Permanent(OBSOLETE)", [15]="Miscellaneous",
    [7]="Trade Goods"}
local items = {[101]=2, [102]=0, [103]=15, [104]=3, [105]=10, [2589]=7}
C_Item = {
    GetItemInfoInstant = function(id) return id, "", "", "", "", items[id] end,
    GetItemClassInfo = function(id) return names[id] end,
}
QuickBuyoutDB = {["15"]=true, ["3"]=true, ["10"]=true}
Settings = {VarType={Boolean="boolean"}, settings={}}
function Settings.RegisterVerticalLayoutCategory(name) return name end
function Settings.RegisterAddOnSetting(category, id, key, db, kind, name, default)
    if db[key] == nil then db[key] = default end
    Settings.settings[id] = {key=key, name=name, default=default}
    return Settings.settings[id]
end
function Settings.CreateCheckbox() end
function Settings.RegisterAddOnCategory(category) Settings.category = category end
results = {}
C_AuctionHouse = {
    GetNumItemSearchResults = function() return #results end,
    GetItemSearchResultInfo = function(_, i) return results[i] end,
    PlaceBid = function(id, amount)
        assert(hardwareEvent, "Item purchase must run inside a hardware event")
        bidCalls = (bidCalls or 0) + 1
        purchased = {id, amount}
    end,
    StartCommoditiesPurchase = function(id, quantity)
        assert(hardwareEvent, "Quote must start from a hardware event")
        quoteRequests = (quoteRequests or 0) + 1
        quoted = {id, quantity}
    end,
    ConfirmCommoditiesPurchase = function(id, quantity)
        commodityBuys = (commodityBuys or 0) + 1
        commodityPurchased = {id, quantity}
    end,
    CancelCommoditiesPurchase = function() cancellations = (cancellations or 0) + 1 end,
    GetQuoteDurationRemaining = function() return quoteDuration or 30 end,
    MakeItemKey = function(id) return {itemID=id} end,
}
AuctionHouseUtil = {IsOwnedAuction=function(info) return info.owned end}
timers = {}
C_Timer = {After=function(_, fn) timers[#timers+1] = fn end}
errors = {}
UIErrorsFrame = {AddExternalErrorMessage=function(_, message) errors[#errors+1] = message end}
AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY = "Not enough money"
AUCTION_HOUSE_TOOLTIP_TITLE_NONE_AVAILABLE = "None available"
AUCTION_HOUSE_DIALOG_PRICE_UNAVAILABLE = "Price unavailable"
function GetMoney() return money or 10000 end
function GetMoneyString(amount) return tostring(amount) .. "c" end
ACCEPT = "Accept"
CANCEL = "Cancel"
StaticPopupDialogs = {}
function StaticPopup_Hide(which)
    if popup and popup.which == which then
        local old = popup
        popup = nil
        StaticPopupDialogs[which].OnHide(old, old.data)
    end
end
function StaticPopup_Show(which, newPrice, previousPrice, data)
    if failPopup then return nil end
    popup = {which=which, newPrice=newPrice, previousPrice=previousPrice, data=data}
    popupShows = (popupShows or 0) + 1
    return popup
end
function AcceptPrice()
    local dialog = popup
    hardwareEvent = true
    StaticPopupDialogs[dialog.which].OnAccept(dialog, dialog.data)
    hardwareEvent = false
    StaticPopup_Hide(dialog.which)
end
SOUNDKIT = {IG_MAINMENU_OPTION_CHECKBOX_ON=1}
function PlaySound() end
function wipe(t) for key in pairs(t) do t[key] = nil end end
function hooksecurefunc(frame, method, fn)
    local original = frame[method]
    frame[method] = function(self, ...)
        if original then original(self, ...) end
        fn(self, ...)
    end
    if method == "SetItemKey" then frame.onItemKey = function() fn(frame) end end
end
function CreateFrame()
    events = {RegisterEvent=function() end}
    function events:SetScript(_, fn) self.onEvent = fn end
    return events
end
C_AddOns = {IsAddOnLoaded=function() return true end}
local list = {}
function list:GetSelectedEntry() return self.selected end
function list:SetSelectedEntry(info) self.selected = info end
AuctionHouseFrame = {ItemBuyFrame = {ItemList=list, BuyoutFrame={}}}
local frame = AuctionHouseFrame.ItemBuyFrame
frame.scripts = {}
frame.shown = true
function frame:IsShown() return self.shown end
function frame:HookScript(event, fn)
    self.scripts[event] = fn
    if event == "OnEvent" then self.onSearchEvent = fn end
end
function frame:BuyoutItem() self.blizzardBuys = (self.blizzardBuys or 0) + 1 end
function frame.BuyoutFrame:SetBuyoutCallback(fn)
    self.click = function()
        hardwareEvent = true
        fn()
        hardwareEvent = false
    end
end
function frame:GetAuctionHouseFrame() return AuctionHouseFrame end
AuctionHouseSearchContext = {BuyCommodities=1, BuyItems=2}
function AuctionHouseFrame:RefreshSearchResults(context, key)
    refreshCount = (refreshCount or 0) + 1
    refreshed = {context, key.itemID}
end
local display = {itemID=2589, quantity=20, totalPrice=200, shown=true, scripts={}}
AuctionHouseFrame.CommoditiesBuyFrame = {BuyDisplay=display}
function display:GetItemID() return self.itemID end
function display:GetQuantitySelected() return self.quantity end
function display:IsShown() return self.shown end
function display:SetQuantitySelected(quantity) self.quantity = quantity end
function display:SetItemIDAndPrice(id) self.itemID = id end
function display:HookScript(event, fn) self.scripts[event] = fn end
function display:GetAuctionHouseFrame() return AuctionHouseFrame end
display.TotalPrice = {GetAmount=function() return display.totalPrice end}
display.BuyButton = {scripts={}}
function display.BuyButton:GetScript(event) return self.scripts[event] end
function display.BuyButton:SetScript(event, fn) self.scripts[event] = fn end
display.BuyButton:SetScript("OnClick", function()
    if not display.itemID then return end
    blizzardCommodityBuys = (blizzardCommodityBuys or 0) + 1
    C_AuctionHouse.StartCommoditiesPurchase(display.itemID, display.quantity)
end)
function ClickCommodity()
    hardwareEvent = true
    display.BuyButton:GetScript("OnClick")(display.BuyButton)
    hardwareEvent = false
end
"""


class QuickBuyoutTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(WOW_API)
        self.lua.execute(SOURCE)
        self.lua.execute("""
            results = {
                {auctionID=10, buyoutAmount=200},
                {auctionID=11, buyoutAmount=100},
            }
        """)

    def open_item(self):
        self.lua.execute("""
            frame = AuctionHouseFrame.ItemBuyFrame
            frame.itemKey = {itemID=101}
            frame.onItemKey()
        """)

    def test_repeated_price_increases_require_one_explicit_confirmation_each(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            assert(purchased[1] == 11 and not popup)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            frame.BuyoutFrame.click()
            assert(bidCalls == 1 and popup.newPrice == "200c" and popup.previousPrice == "100c")
            frame.BuyoutFrame.click()
            assert(bidCalls == 1 and popupShows == 1)
            AcceptPrice()
            assert(bidCalls == 2 and purchased[1] == 10)
            frame.BuyoutFrame.click()
            assert(bidCalls == 2)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 10)

            results = {{auctionID=12, buyoutAmount=200}, {auctionID=13, buyoutAmount=300}}
            frame.onSearchEvent(frame, "ITEM_SEARCH_RESULTS_UPDATED")
            frame.BuyoutFrame.click()
            assert(bidCalls == 3 and not popup)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 12)
            frame.BuyoutFrame.click()
            assert(bidCalls == 3 and popup.previousPrice == "200c" and popup.newPrice == "300c")
            AcceptPrice()
            assert(bidCalls == 4 and purchased[1] == 13)
        """)

    def test_five_copper_tolerance_does_not_accumulate_and_resets_after_approval(self):
        self.open_item()
        self.lua.execute("""
            results = {{auctionID=11, buyoutAmount=100}, {auctionID=12, buyoutAmount=104},
                {auctionID=13, buyoutAmount=105}, {auctionID=14, buyoutAmount=106},
                {auctionID=15, buyoutAmount=111}, {auctionID=16, buyoutAmount=112}}
            frame.onItemKey()
            for auctionID = 11, 13 do
                frame.BuyoutFrame.click()
                assert(not popup and purchased[1] == auctionID)
                events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", auctionID)
            end
            frame.BuyoutFrame.click()
            assert(bidCalls == 3 and popup.previousPrice == "100c" and popup.newPrice == "106c")
            AcceptPrice()
            assert(bidCalls == 4 and purchased[1] == 14)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 14)
            frame.BuyoutFrame.click()
            assert(bidCalls == 5 and not popup and purchased[1] == 15)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 15)
            frame.BuyoutFrame.click()
            assert(bidCalls == 5 and popup.previousPrice == "106c" and popup.newPrice == "112c")
        """)

    def test_equal_and_lower_prices_buy_directly_then_use_lower_price_as_reference(self):
        self.open_item()
        self.lua.execute("""
            results = {{auctionID=20, buyoutAmount=100}, {auctionID=21, buyoutAmount=100},
                {auctionID=22, buyoutAmount=80}, {auctionID=23, buyoutAmount=90}}
            for _, index in ipairs({1, 2, 3}) do
                frame.ItemList:SetSelectedEntry(results[index])
                frame.BuyoutFrame.click()
                assert(not popup and purchased[1] == results[index].auctionID)
                events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", purchased[1])
            end
            frame.BuyoutFrame.click()
            assert(bidCalls == 3 and popup.previousPrice == "80c" and popup.newPrice == "90c")
        """)

    def test_cancelling_or_dismissing_confirmation_never_raises_reference_price(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            frame.BuyoutFrame.click()
            local dismissed = popup
            StaticPopup_Hide(popup.which)
            StaticPopupDialogs[dismissed.which].OnAccept(dismissed, dismissed.data)
            assert(bidCalls == 1)
            frame.BuyoutFrame.click()
            assert(popup.previousPrice == "100c" and popupShows == 2 and bidCalls == 1)
        """)

    def test_confirmation_revalidates_price_selection_money_and_settings(self):
        for change in (
            "results[1].buyoutAmount = 300",
            "frame.ItemList:SetSelectedEntry({auctionID=99, buyoutAmount=200})",
            "results = {}",
            "money = 150",
            'QuickBuyoutDB["2"] = false',
        ):
            with self.subTest(change=change):
                self.setUp()
                self.open_item()
                self.lua.execute("""
                    frame.BuyoutFrame.click()
                    events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
                    frame.BuyoutFrame.click()
                    assert(popup)
                """ + change + """
                    AcceptPrice()
                    assert(bidCalls == 1)
                """)

    def test_confirmation_can_buy_same_auction_at_a_lower_price(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            frame.BuyoutFrame.click()
            results[1].buyoutAmount = 150
            AcceptPrice()
            assert(bidCalls == 2 and purchased[2] == 150)
        """)

    def test_failed_confirmed_purchase_requires_confirmation_again(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            frame.BuyoutFrame.click()
            AcceptPrice()
            events.onEvent(events, "AUCTION_HOUSE_SHOW_ERROR", Enum.AuctionHouseError.IsBusy)
            frame.BuyoutFrame.click()
            assert(bidCalls == 2 and popupShows == 2 and popup.previousPrice == "100c")
        """)

    def test_failed_first_purchase_still_protects_against_a_more_expensive_replacement(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_SHOW_ERROR", Enum.AuctionHouseError.ItemNotFound)
            frame.BuyoutFrame.click()
            assert(bidCalls == 1 and popup.previousPrice == "100c" and popup.newPrice == "200c")
            AcceptPrice()
            assert(bidCalls == 2 and purchased[1] == 10)
        """)

    def test_missing_auction_is_skipped_without_new_search_and_next_buy_requires_click(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_SHOW_ERROR", Enum.AuctionHouseError.ItemNotFound)
            assert(not refreshed)
            assert(frame.ItemList.selected.auctionID == 10 and bidCalls == 1)
            frame.onSearchEvent(frame, "ITEM_SEARCH_RESULTS_UPDATED")
            assert(frame.ItemList.selected.auctionID == 10 and bidCalls == 1)
            frame.BuyoutFrame.click()
            assert(bidCalls == 1 and popup)
            AcceptPrice()
            assert(bidCalls == 2 and purchased[1] == 10)
        """)

    def test_other_auction_errors_do_not_blacklist_valid_listing(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_SHOW_ERROR", Enum.AuctionHouseError.NotEnoughMoney)
            assert(frame.ItemList.selected.auctionID == 11 and not refreshed)
            frame.BuyoutFrame.click()
            assert(bidCalls == 2 and purchased[1] == 11)
        """)

    def test_missing_selection_and_timeout_advance_without_new_search_or_purchase(self):
        self.open_item()
        self.lua.execute("""
            frame.ItemList.selected = {auctionID=999, buyoutAmount=1}
            frame.BuyoutFrame.click()
            assert(not purchased and not refreshed)
            assert(frame.ItemList.selected.auctionID == 11)
            frame.BuyoutFrame.click()
            timers[1]()
            assert(bidCalls == 1 and not refreshed and frame.ItemList.selected.auctionID == 10)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            frame.BuyoutFrame.click()
            assert(bidCalls == 1 and popup.previousPrice == "100c")
        """)

    def test_old_timeout_cannot_clear_a_new_purchase(self):
        self.open_item()
        self.lua.execute("""
            frame.ItemList.selected = results[1]
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 10)
            frame.BuyoutFrame.click()
            timers[1]()
            frame.BuyoutFrame.click()
            assert(bidCalls == 2 and not refreshed)
        """)

    def test_generic_error_before_success_keeps_purchase_pending_without_reloading(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_SHOW_ERROR", Enum.AuctionHouseError.DatabaseError)
            frame.BuyoutFrame.click()
            assert(bidCalls == 1 and not refreshed and frame.ItemList.selected.auctionID == 11)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            timers[1]()
            assert(not refreshed and frame.ItemList.selected.auctionID == 10)
            frame.BuyoutFrame.click()
            assert(bidCalls == 1 and popup.previousPrice == "100c")
        """)

    def test_generic_error_after_success_preserves_next_price_confirmation(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            frame.BuyoutFrame.click()
            assert(popup and bidCalls == 1)
            events.onEvent(events, "AUCTION_HOUSE_SHOW_ERROR", Enum.AuctionHouseError.DatabaseError)
            assert(popup and not refreshed and frame.ItemList.selected.auctionID == 10)
            AcceptPrice()
            assert(bidCalls == 2 and purchased[1] == 10)
        """)

    def test_item_change_view_hide_and_close_invalidate_pending_confirmation(self):
        for change in (
            "frame.itemKey = {itemID=103}; frame.onItemKey()",
            "frame.shown = false; frame.scripts.OnHide()",
            'events.onEvent(events, "AUCTION_HOUSE_CLOSED")',
        ):
            with self.subTest(change=change):
                self.setUp()
                self.open_item()
                self.lua.execute("""
                    frame.BuyoutFrame.click()
                    events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
                    frame.BuyoutFrame.click()
                    local dismissed = popup
                """ + change + """
                    assert(not popup)
                    hardwareEvent = true
                    StaticPopupDialogs[dismissed.which].OnAccept(dismissed, dismissed.data)
                    hardwareEvent = false
                    assert(bidCalls == 1)
                """)

    def test_reference_price_is_separate_for_item_variants_and_remembered_on_return(self):
        for variant in ("itemID=103", "itemID=101,itemLevel=10", "itemID=101,itemSuffix=5",
                        "itemID=101,battlePetSpeciesID=2"):
            with self.subTest(variant=variant):
                self.setUp()
                self.open_item()
                self.lua.execute("""
                    frame.BuyoutFrame.click()
                    events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
                    results = {{auctionID=20, buyoutAmount=500}}
                    frame.itemKey = {""" + variant + """}
                    frame.onItemKey()
                    frame.BuyoutFrame.click()
                    assert(bidCalls == 2 and not popup)
                    events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 20)
                    frame.itemKey = {itemID=101}
                    results = {{auctionID=30, buyoutAmount=200}}
                    frame.onItemKey()
                    frame.BuyoutFrame.click()
                    assert(bidCalls == 2 and popup.previousPrice == "100c")
                """)

    def test_closing_auction_house_resets_prices_and_unavailable_ids(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            events.onEvent(events, "AUCTION_HOUSE_CLOSED")
            frame.onItemKey()
            frame.BuyoutFrame.click()
            assert(bidCalls == 2 and not popup and purchased[1] == 11)
            events.onEvent(events, "AUCTION_HOUSE_SHOW_ERROR", Enum.AuctionHouseError.ItemNotFound)
            assert(frame.ItemList.selected.auctionID == 10)
            events.onEvent(events, "AUCTION_HOUSE_CLOSED")
            frame.onItemKey()
            assert(frame.ItemList.selected.auctionID == 11)
        """)

    def test_error_after_switching_item_does_not_refresh_or_reselect_new_item(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            frame.itemKey = {itemID=103}
            results = {{auctionID=20, buyoutAmount=500}, {auctionID=21, buyoutAmount=300}}
            frame.onItemKey()
            frame.ItemList.selected = results[1]
            events.onEvent(events, "AUCTION_HOUSE_SHOW_ERROR", Enum.AuctionHouseError.ItemNotFound)
            assert(not refreshed and frame.ItemList.selected.auctionID == 20 and bidCalls == 1)
        """)

    def test_unavailable_popup_blocks_purchase_but_does_not_leave_addon_stuck(self):
        self.open_item()
        self.lua.execute("""
            frame.BuyoutFrame.click()
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            failPopup = true
            frame.BuyoutFrame.click()
            assert(bidCalls == 1 and not popup)
            failPopup = false
            frame.BuyoutFrame.click()
            assert(popup and bidCalls == 1)
        """)

    def test_settings_default_to_gear_and_preserve_saved_categories(self):
        self.lua.execute("""
            assert(Settings.category == "Quick Buyout")
            assert(Settings.settings.QUICKBUYOUT_CLASS_2 and Settings.settings.QUICKBUYOUT_CLASS_4)
            assert(Settings.settings.QUICKBUYOUT_CLASS_0 and Settings.settings.QUICKBUYOUT_CLASS_15)
            assert(not Settings.settings.QUICKBUYOUT_CLASS_3)
            assert(not Settings.settings.QUICKBUYOUT_CLASS_8)
            assert(not Settings.settings.QUICKBUYOUT_CLASS_10)
            assert(not Settings.settings.QUICKBUYOUT_CLASS_14)
            assert(QuickBuyoutDB["2"] and QuickBuyoutDB["4"])
            assert(QuickBuyoutDB["0"] == false and QuickBuyoutDB["15"])
        """)

    def test_only_enabled_classes_use_quick_buyout(self):
        self.lua.execute("""
            local frame = AuctionHouseFrame.ItemBuyFrame
            frame.itemKey = {itemID=101}
            frame.onItemKey()
            assert(frame.ItemList.selected.auctionID == 11)
            frame.ItemList.selected = results[1]
            frame.BuyoutFrame.click()
            assert(purchased[1] == 10 and purchased[2] == 200)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 10)

            frame.itemKey = {itemID=102}
            frame.ItemList.selected = nil
            frame.onItemKey()
            assert(frame.ItemList.selected == nil)
            frame.BuyoutFrame.click()
            assert(frame.blizzardBuys == 1)

            QuickBuyoutDB["0"] = true
            frame.onSearchEvent(frame, "ITEM_SEARCH_RESULTS_UPDATED")
            assert(frame.ItemList.selected.auctionID == 11)
            frame.BuyoutFrame.click()
            assert(purchased[1] == 11)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)

            QuickBuyoutDB["0"] = false
            frame.BuyoutFrame.click()
            assert(frame.blizzardBuys == 2)
            results = {{auctionID=12, buyoutAmount=50}}
            frame.itemKey = {itemID=103}
            frame.ItemList.selected = nil
            frame.onItemKey()
            assert(frame.ItemList.selected.auctionID == 12)
            QuickBuyoutDB["2"] = false
            frame.itemKey = {itemID=101}
            frame.BuyoutFrame.click()
            assert(frame.blizzardBuys == 3)
            for _, itemID in ipairs({104, 105}) do
                frame.itemKey = {itemID=itemID}
                frame.ItemList.selected = nil
                frame.onItemKey()
                assert(frame.ItemList.selected == nil)
                frame.BuyoutFrame.click()
            end
            assert(frame.blizzardBuys == 5)
        """)

    def test_linen_cloth_buys_selected_quantity_after_server_quote(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            assert(quoted[1] == 2589 and quoted[2] == 20)
            assert(not commodityPurchased)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(commodityPurchased and commodityPurchased[1] == 2589
                and commodityPurchased[2] == 20, "Linen cloth was not purchased")
            assert(not blizzardCommodityBuys, "Confirmation dialog was not bypassed")
        """)

    def test_commodity_classes_remain_opt_in(self):
        self.lua.execute("""
            assert(QuickBuyoutDB["7"] == false)
            ClickCommodity()
            assert(blizzardCommodityBuys == 1 and quoted[2] == 20)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(not commodityPurchased)
        """)

    def test_cheaper_commodity_quote_is_accepted(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 9, 180)
            assert(commodityPurchased[2] == 20)
        """)

    def test_price_increase_cancels_and_refreshes(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 11, 201)
            assert(not commodityPurchased and cancellations == 1)
            assert(refreshed[2] == 2589 and #errors == 1)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(not commodityPurchased)
            ClickCommodity()
            assert(quoteRequests == 2)
        """)

    def test_insufficient_money_before_and_after_quote(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            money = 199
            ClickCommodity()
            assert(not quoted and errors[1] == AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
            money = 200
            ClickCommodity()
            money = 199
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(not commodityPurchased and cancellations == 1)
            assert(errors[2] == AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
        """)

    def test_empty_commodity_selection_is_rejected(self):
        for change in ("display.quantity = 0", "display.totalPrice = 0", "display.itemID = nil"):
            with self.subTest(change=change):
                self.setUp()
                self.lua.execute("""
                    QuickBuyoutDB["7"] = true
                    local display = AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay
                """ + change + """
                    ClickCommodity()
                    assert(not commodityPurchased and not quoteRequests)
                """)

    def test_double_clicks_and_duplicate_quotes_do_not_double_buy(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            ClickCommodity()
            assert(quoteRequests == 1)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(commodityBuys == 1 and quoteRequests == 1)
            events.onEvent(events, "COMMODITY_PURCHASE_SUCCEEDED")
            assert(refreshed[2] == 2589)
            ClickCommodity()
            assert(quoteRequests == 2)
            timers[1]()
            assert(#errors == 0)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(commodityBuys == 2)
        """)

    def test_changed_selection_cancels_pending_quote(self):
        for change in (
            "display:SetQuantitySelected(5)",
            "display:SetItemIDAndPrice(101)",
            'display.shown = false; display.scripts.OnHide()',
            'events.onEvent(events, "AUCTION_HOUSE_CLOSED")',
            'QuickBuyoutDB["7"] = false',
        ):
            with self.subTest(change=change):
                self.setUp()
                self.lua.execute("""
                    QuickBuyoutDB["7"] = true
                    ClickCommodity()
                    local display = AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay
                """ + change + """
                    events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
                    assert(not commodityPurchased and cancellations == 1)
                    timers[1]()
                    assert(#errors == 0)
                """)

    def test_blizzard_quantity_reset_does_not_release_in_flight_guard(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay:SetQuantitySelected(1)
            ClickCommodity()
            assert(quoteRequests == 1)
            events.onEvent(events, "COMMODITY_PURCHASE_SUCCEEDED")
            assert(refreshed[2] == 2589)
        """)

    def test_failed_quote_or_purchase_can_be_retried(self):
        for event in ("COMMODITY_PRICE_UNAVAILABLE", "COMMODITY_PURCHASE_FAILED", "AUCTION_HOUSE_SHOW_ERROR"):
            with self.subTest(event=event):
                self.setUp()
                self.lua.execute("""
                    QuickBuyoutDB["7"] = true
                    ClickCommodity()
                """)
                self.lua.globals().events.onEvent(self.lua.globals().events, event)
                self.lua.execute("""
                    assert(cancellations == 1 and not commodityPurchased)
                    ClickCommodity()
                    assert(quoteRequests == 2)
                    events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
                    assert(commodityBuys == 1)
                """)

    def test_timeout_and_expired_quote_do_not_purchase(self):
        for failure in (
            "timers[1]()",
            'quoteDuration = 0; events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)',
            'events.onEvent(events, "COMMODITY_PRICE_UPDATED", 0, 0)',
        ):
            with self.subTest(failure=failure):
                self.setUp()
                self.lua.execute("""
                    QuickBuyoutDB["7"] = true
                    ClickCommodity()
                """ + failure + """
                    assert(not commodityPurchased and cancellations == 1 and #errors == 1)
                    ClickCommodity()
                    assert(quoteRequests == 2)
                """)

    def test_item_and_commodity_purchases_share_in_flight_guard(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            local frame = AuctionHouseFrame.ItemBuyFrame
            frame.itemKey = {itemID=101}
            frame.onItemKey()
            ClickCommodity()
            frame.BuyoutFrame.click()
            assert(not purchased)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            events.onEvent(events, "COMMODITY_PURCHASE_SUCCEEDED")
            frame.BuyoutFrame.click()
            assert(purchased[1] == 11)
            ClickCommodity()
            assert(quoteRequests == 1)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            ClickCommodity()
            assert(quoteRequests == 2)
        """)

    def test_search_updates_keep_manual_selection_and_skip_unbuyable_auctions(self):
        self.lua.execute("""
            local frame = AuctionHouseFrame.ItemBuyFrame
            frame.itemKey = {itemID=101}
            results = {
                {auctionID=10, buyoutAmount=200},
                {auctionID=11, buyoutAmount=100},
                {auctionID=12, buyoutAmount=1, owned=true},
                {auctionID=13, buyoutAmount=0},
            }
            frame.onItemKey()
            assert(frame.ItemList.selected.auctionID == 11)
            frame.ItemList.selected = results[1]
            frame.onSearchEvent(frame, "ITEM_SEARCH_RESULTS_UPDATED")
            assert(frame.ItemList.selected.auctionID == 10)
            frame.BuyoutFrame.click()
            assert(purchased[1] == 10)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 10)
            assert(frame.ItemList.selected.auctionID == 11)
            frame.onSearchEvent(frame, "ITEM_SEARCH_RESULTS_UPDATED")
            frame.BuyoutFrame.click()
            assert(purchased[1] == 11)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            assert(frame.ItemList.selected == nil)
        """)

    def test_switching_views_after_confirmation_keeps_purchase_guard(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            local display = AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay
            display.shown = false
            display.scripts.OnHide()
            display:SetItemIDAndPrice(101)
            display.shown = true
            ClickCommodity()
            assert(quoteRequests == 1 and not cancellations)
            events.onEvent(events, "COMMODITY_PURCHASE_SUCCEEDED")
            assert(not refreshed, "Do not refresh the previous item into a different view")
            ClickCommodity()
            assert(quoteRequests == 2 and quoted[1] == 101)
        """)


if __name__ == "__main__":
    unittest.main()
