local PENDING_TIMEOUT = 5
local PRICE_INCREASE_TOLERANCE = 5 -- copper
local NO_AUCTION_SELECTED_ERROR = "Quick Buyout: select an auction first."

local GetItemInfoInstant = (C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant
local GetItemClassInfo = (C_Item and C_Item.GetItemClassInfo) or GetItemClassInfo

QuickBuyoutDB = QuickBuyoutDB or {}

local itemBuyFrame
local commodityBuyDisplay
local pendingAuctionID
local pendingCommodity
local pendingToken = 0
-- Auctions we already bought; the result list can lag behind the server.
local boughtAuctionIDs = {}
local unavailableAuctionIDs = {}
local attemptedPurchases = {}
local referenceItemPrices = {}
local priceConfirmation
local PRICE_INCREASE_DIALOG = "QUICKBUYOUT_PRICE_INCREASE"

local function ItemKeyID(itemKey)
	if not itemKey then
		return nil
	end
	return table.concat({ itemKey.itemID, itemKey.itemLevel or 0,
		itemKey.itemSuffix or 0, itemKey.battlePetSpeciesID or 0 }, ":")
end

local function CancelPriceConfirmation()
	priceConfirmation = nil
	StaticPopup_Hide(PRICE_INCREASE_DIALOG)
end

local function RefreshItemResults(itemKey)
	if itemBuyFrame and itemBuyFrame:IsShown() and itemBuyFrame.itemKey
		and (not itemKey or ItemKeyID(itemKey) == ItemKeyID(itemBuyFrame.itemKey)) then
		itemBuyFrame:GetAuctionHouseFrame():RefreshSearchResults(
			AuctionHouseSearchContext.BuyItems, itemBuyFrame.itemKey
		)
	end
end

local function IsObsoleteClass(classID, name)
	return classID == Enum.ItemClass.CurrencyTokenObsolete
		or classID == Enum.ItemClass.PermanentObsolete
		or (name and name:upper():find("OBSOLETE", 1, true) ~= nil)
end

local function IsEnabled(itemKey)
	if not itemKey or not itemKey.itemID then
		return false
	end
	local classID = select(6, GetItemInfoInstant(itemKey.itemID))
	if not classID or IsObsoleteClass(classID, GetItemClassInfo(classID)) then
		return false
	end
	local enabled = QuickBuyoutDB[tostring(classID)]
	if enabled == nil then
		return classID == Enum.ItemClass.Weapon or classID == Enum.ItemClass.Armor
	end
	return enabled
end

local function IsOwned(info)
	if AuctionHouseUtil and AuctionHouseUtil.IsOwnedAuction then
		return AuctionHouseUtil.IsOwnedAuction(info)
	end
	return info.containsOwnerItem
end

local function IsBuyable(info)
	return info and info.buyoutAmount and info.buyoutAmount > 0
		and not boughtAuctionIDs[info.auctionID]
		and not unavailableAuctionIDs[info.auctionID] and not IsOwned(info)
end

-- Returns the cheapest buyable auction, plus the fresh result for wantedAuctionID if it is still buyable.
local function ScanResults(itemKey, wantedAuctionID)
	local cheapest, wanted
	for i = 1, C_AuctionHouse.GetNumItemSearchResults(itemKey) do
		local info = C_AuctionHouse.GetItemSearchResultInfo(itemKey, i)
		if IsBuyable(info) then
			if not cheapest or info.buyoutAmount < cheapest.buyoutAmount then
				cheapest = info
			end
			if info.auctionID == wantedAuctionID then
				wanted = info
			end
		end
	end
	return cheapest, wanted
end

-- Selects the cheapest auction. Unless forced, a still-buyable selection is left alone.
local function SelectCheapest(force)
	local itemKey = itemBuyFrame.itemKey
	if not itemBuyFrame:IsShown() or not IsEnabled(itemKey) then
		return
	end

	local selected = itemBuyFrame.ItemList:GetSelectedEntry()
	local cheapest, current = ScanResults(itemKey, selected and selected.auctionID)
	if current and not force then
		return
	end

	if cheapest then
		if not selected or selected.auctionID ~= cheapest.auctionID then
			-- Select without scrolling: the ScrollBox may not have its data provider yet.
			itemBuyFrame.ItemList:SetSelectedEntry(cheapest)
		end
	elseif selected then
		itemBuyFrame.ItemList:SetSelectedEntry(nil)
	end
end

local function ClearPending()
	pendingAuctionID = nil
end

local function QuickBuy(approval)
	if not itemBuyFrame:IsShown() then
		return
	end
	local itemKey = itemBuyFrame.itemKey
	if not IsEnabled(itemKey) then
		if not approval then
			itemBuyFrame:BuyoutItem()
		end
		return
	end

	if pendingAuctionID or pendingCommodity or priceConfirmation then
		return
	end

	local selected = itemBuyFrame.ItemList:GetSelectedEntry()
	local _, target = ScanResults(itemKey, selected and selected.auctionID)
	if approval and (approval.itemKeyID ~= ItemKeyID(itemKey) or not target
		or target.auctionID ~= approval.auctionID or target.buyoutAmount > approval.price) then
		UIErrorsFrame:AddExternalErrorMessage("Quick Buyout: nabídka se změnila. Zkontrolujte cenu a klikněte znovu na Buyout.")
		SelectCheapest(false)
		RefreshItemResults()
		return
	end
	if not target then
		UIErrorsFrame:AddExternalErrorMessage(NO_AUCTION_SELECTED_ERROR)
		SelectCheapest(true)
		RefreshItemResults()
		return
	end

	if target.buyoutAmount > GetMoney() then
		UIErrorsFrame:AddExternalErrorMessage(AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
		return
	end

	local itemKeyID = ItemKeyID(itemKey)
	local referencePrice = referenceItemPrices[itemKeyID]
	if referencePrice and target.buyoutAmount > referencePrice + PRICE_INCREASE_TOLERANCE and not approval then
		local confirmation = {
			itemKeyID = itemKeyID, auctionID = target.auctionID, price = target.buyoutAmount,
		}
		priceConfirmation = confirmation
		if not StaticPopup_Show(PRICE_INCREASE_DIALOG, GetMoneyString(target.buyoutAmount),
			GetMoneyString(referencePrice), confirmation) then
			priceConfirmation = nil
		end
		return
	end

	-- Keep Blizzard's warning for unique crafted items (retail only).
	if AuctionHouseUtil.IsAuctionIDUniqueShadowlandsCrafted
		and AuctionHouseUtil.IsAuctionIDUniqueShadowlandsCrafted(target.auctionID) then
		itemBuyFrame:GetAuctionHouseFrame():StartItemBuyout(target.auctionID, target.buyoutAmount)
		return
	end

	-- Keep the first clicked price as a reference even if its auction disappears.
	if not referencePrice then
		referenceItemPrices[itemKeyID] = target.buyoutAmount
	end
	pendingAuctionID = target.auctionID
	attemptedPurchases[target.auctionID] = {
		itemKeyID = itemKeyID, price = target.buyoutAmount, approvedIncrease = approval ~= nil,
		itemKey = { itemID = itemKey.itemID, itemLevel = itemKey.itemLevel or 0,
			itemSuffix = itemKey.itemSuffix or 0, battlePetSpeciesID = itemKey.battlePetSpeciesID or 0 },
	}
	pendingToken = pendingToken + 1
	local token = pendingToken
	local purchase = attemptedPurchases[target.auctionID]
	C_Timer.After(PENDING_TIMEOUT, function()
		if token == pendingToken and pendingAuctionID then
			ClearPending()
			RefreshItemResults(purchase.itemKey)
		end
	end)

	-- Runs synchronously from Buyout or the user's explicit price-confirmation click.
	C_AuctionHouse.PlaceBid(target.auctionID, target.buyoutAmount)
end

StaticPopupDialogs[PRICE_INCREASE_DIALOG] = {
	text = "Opravdu chcete koupit za %s?\nSrovnávací cena byla %s.",
	button1 = ACCEPT,
	button2 = CANCEL,
	OnAccept = function(_, data)
		if priceConfirmation == data then
			priceConfirmation = nil
			QuickBuy(data)
		end
	end,
	OnHide = function(_, data)
		if priceConfirmation == data then
			priceConfirmation = nil
		end
	end,
	timeout = 0,
	whileDead = true,
	hideOnEscape = true,
	showAlert = true,
	exclusive = true,
	preferredIndex = 3,
}

local function ClearCommodityPending(refresh)
	local purchase = pendingCommodity
	if not purchase then
		return
	end
	pendingCommodity = nil
	C_AuctionHouse.CancelCommoditiesPurchase()
	if refresh and commodityBuyDisplay:IsShown() and commodityBuyDisplay:GetItemID() == purchase.itemID then
		commodityBuyDisplay:GetAuctionHouseFrame():RefreshSearchResults(
			AuctionHouseSearchContext.BuyCommodities, C_AuctionHouse.MakeItemKey(purchase.itemID)
		)
	end
end

local function CancelCommodityQuote()
	if pendingCommodity and not pendingCommodity.confirming then
		ClearCommodityPending(false)
	end
end

local function FailCommodityPurchase(message)
	ClearCommodityPending(true)
	UIErrorsFrame:AddExternalErrorMessage(message)
end

local function QuickBuyCommodity()
	if pendingCommodity or pendingAuctionID then
		return
	end

	local itemID = commodityBuyDisplay:GetItemID()
	local quantity = commodityBuyDisplay:GetQuantitySelected()
	local totalPrice = commodityBuyDisplay.TotalPrice:GetAmount()
	if not itemID or quantity <= 0 or totalPrice <= 0 then
		UIErrorsFrame:AddExternalErrorMessage(AUCTION_HOUSE_TOOLTIP_TITLE_NONE_AVAILABLE)
		return
	end
	if totalPrice > GetMoney() then
		UIErrorsFrame:AddExternalErrorMessage(AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
		return
	end

	local purchase = { itemID = itemID, quantity = quantity, totalPrice = totalPrice }
	pendingCommodity = purchase
	C_Timer.After(PENDING_TIMEOUT, function()
		if pendingCommodity == purchase then
			FailCommodityPurchase("Quick Buyout: commodity purchase timed out. Search again before retrying.")
		end
	end)

	-- Quote requests require the Buy button's hardware event; confirmation waits for the server quote.
	C_AuctionHouse.StartCommoditiesPurchase(itemID, quantity)
end

local function ConfirmCommodityQuote(unitPrice, totalPrice)
	local purchase = pendingCommodity
	if not purchase or purchase.confirming then
		return
	end
	if not commodityBuyDisplay:IsShown()
		or commodityBuyDisplay:GetItemID() ~= purchase.itemID
		or commodityBuyDisplay:GetQuantitySelected() ~= purchase.quantity
		or not IsEnabled({ itemID = purchase.itemID }) then
		ClearCommodityPending(false)
		return
	end
	if unitPrice <= 0 or totalPrice <= 0 or C_AuctionHouse.GetQuoteDurationRemaining() <= 0 then
		FailCommodityPurchase(AUCTION_HOUSE_DIALOG_PRICE_UNAVAILABLE)
		return
	end
	if totalPrice > purchase.totalPrice then
		FailCommodityPurchase("Quick Buyout: commodity price increased. Search again before retrying.")
		return
	end
	if totalPrice > GetMoney() then
		FailCommodityPurchase(AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
		return
	end

	purchase.confirming = true
	C_AuctionHouse.ConfirmCommoditiesPurchase(purchase.itemID, purchase.quantity)
end

local function Setup()
	if itemBuyFrame or not AuctionHouseFrame or not AuctionHouseFrame.ItemBuyFrame then
		return
	end

	itemBuyFrame = AuctionHouseFrame.ItemBuyFrame
	itemBuyFrame.BuyoutFrame:SetBuyoutCallback(function()
		QuickBuy()
	end)
	itemBuyFrame:HookScript("OnHide", CancelPriceConfirmation)

	itemBuyFrame:HookScript("OnEvent", function(_, event)
		if event == "ITEM_SEARCH_RESULTS_UPDATED" or event == "ITEM_SEARCH_RESULTS_ADDED" then
			SelectCheapest(false)
		end
	end)
	hooksecurefunc(itemBuyFrame, "SetItemKey", function()
		if priceConfirmation and priceConfirmation.itemKeyID ~= ItemKeyID(itemBuyFrame.itemKey) then
			CancelPriceConfirmation()
		end
		SelectCheapest(true)
	end)

	if AuctionHouseFrame.CommoditiesBuyFrame then
		commodityBuyDisplay = AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay
		local buyButton = commodityBuyDisplay.BuyButton
		local originalOnClick = buyButton:GetScript("OnClick")
		buyButton:SetScript("OnClick", function(button, ...)
			if pendingCommodity or pendingAuctionID then
				return
			end
			if not IsEnabled({ itemID = commodityBuyDisplay:GetItemID() }) then
				originalOnClick(button, ...)
				return
			end
			QuickBuyCommodity()
			PlaySound(SOUNDKIT.IG_MAINMENU_OPTION_CHECKBOX_ON)
		end)
		commodityBuyDisplay:HookScript("OnHide", function()
			CancelCommodityQuote()
		end)
		hooksecurefunc(commodityBuyDisplay, "SetItemIDAndPrice", function()
			CancelCommodityQuote()
		end)
		hooksecurefunc(commodityBuyDisplay, "SetQuantitySelected", function()
			if pendingCommodity
				and commodityBuyDisplay:GetQuantitySelected() ~= pendingCommodity.quantity then
				CancelCommodityQuote()
			end
		end)
	end
end

local function RegisterSettings()
	local category = Settings.RegisterVerticalLayoutCategory("Quick Buyout")
	local classes = {}
	local seen = {}
	for _, classID in pairs(Enum.ItemClass) do
		if type(classID) == "number" and not seen[classID] then
			seen[classID] = true
			local name = GetItemClassInfo(classID)
			if name and not IsObsoleteClass(classID, name) then
				classes[#classes + 1] = { id = classID, name = name }
			end
		end
	end
	table.sort(classes, function(a, b)
		return a.name < b.name
	end)

	for _, class in ipairs(classes) do
		local default = class.id == Enum.ItemClass.Weapon or class.id == Enum.ItemClass.Armor
		local setting = Settings.RegisterAddOnSetting(
			category, "QUICKBUYOUT_CLASS_" .. class.id, tostring(class.id), QuickBuyoutDB,
			Settings.VarType.Boolean, class.name, default
		)
		Settings.CreateCheckbox(category, setting,
			"Quick buy in this category. Item price increases over 5 copper require confirmation. Commodity quote increases cancel the purchase.")
	end
	Settings.RegisterAddOnCategory(category)
end

RegisterSettings()

local events = CreateFrame("Frame")
events:RegisterEvent("ADDON_LOADED")
events:RegisterEvent("AUCTION_HOUSE_PURCHASE_COMPLETED")
events:RegisterEvent("AUCTION_HOUSE_SHOW_ERROR")
events:RegisterEvent("AUCTION_HOUSE_CLOSED")
events:RegisterEvent("COMMODITY_PRICE_UPDATED")
events:RegisterEvent("COMMODITY_PRICE_UNAVAILABLE")
events:RegisterEvent("COMMODITY_PURCHASE_SUCCEEDED")
events:RegisterEvent("COMMODITY_PURCHASE_FAILED")
events:SetScript("OnEvent", function(_, event, arg1, arg2)
	if event == "ADDON_LOADED" then
		if arg1 == "Blizzard_AuctionHouseUI" then
			Setup()
		end
	elseif event == "AUCTION_HOUSE_PURCHASE_COMPLETED" then
		boughtAuctionIDs[arg1] = true
		local purchase = attemptedPurchases[arg1]
		if purchase then
			-- Small increases must never accumulate into a higher reference price.
			if purchase.approvedIncrease or purchase.price < referenceItemPrices[purchase.itemKeyID] then
				referenceItemPrices[purchase.itemKeyID] = purchase.price
			end
			attemptedPurchases[arg1] = nil
		end
		if arg1 == pendingAuctionID then
			ClearPending()
		end
		if itemBuyFrame then
			SelectCheapest(true)
		end
	elseif event == "AUCTION_HOUSE_SHOW_ERROR" then
		local purchase = pendingAuctionID and attemptedPurchases[pendingAuctionID]
		local itemNotFound = Enum.AuctionHouseError and arg1 == Enum.AuctionHouseError.ItemNotFound
		if purchase and itemNotFound then
			unavailableAuctionIDs[pendingAuctionID] = true
		end
		ClearPending()
		CancelPriceConfirmation()
		ClearCommodityPending(true)
		if purchase then
			if itemBuyFrame:IsShown() and ItemKeyID(itemBuyFrame.itemKey) == purchase.itemKeyID then
				SelectCheapest(itemNotFound)
			end
			RefreshItemResults(purchase.itemKey)
		end
	elseif event == "AUCTION_HOUSE_CLOSED" then
		ClearPending()
		CancelPriceConfirmation()
		ClearCommodityPending(false)
		wipe(boughtAuctionIDs)
		wipe(unavailableAuctionIDs)
		wipe(attemptedPurchases)
		wipe(referenceItemPrices)
	elseif event == "COMMODITY_PRICE_UPDATED" then
		ConfirmCommodityQuote(arg1, arg2)
	elseif event == "COMMODITY_PURCHASE_SUCCEEDED" then
		ClearCommodityPending(true)
	elseif (event == "COMMODITY_PRICE_UNAVAILABLE" or event == "COMMODITY_PURCHASE_FAILED")
		and pendingCommodity then
		FailCommodityPurchase(AUCTION_HOUSE_DIALOG_PRICE_UNAVAILABLE)
	end
end)

local IsAddOnLoaded = (C_AddOns and C_AddOns.IsAddOnLoaded) or IsAddOnLoaded
if IsAddOnLoaded("Blizzard_AuctionHouseUI") then
	Setup()
end
