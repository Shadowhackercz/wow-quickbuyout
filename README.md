<p align="center"><img src="media/logo.png" width="160" alt="Quick Buyout logo"></p>

# wow-quickbuyout

A World of Warcraft addon for repeated one-click Auction House purchases, with confirmation when the selected item's price exceeds the reference by more than 5 copper. The cheapest auction is selected for you by default. This fork adds a Czech price-increase dialog and recovery from stale auctions to PsyKzz's Quick Buyout.

## Features

- **One-click buyout** - the first purchase and subsequent purchases up to 5 copper above the reference price need only a Buyout click. Armor and weapons are enabled by default.
- **Confirm price increases** - an increase of more than 5 copper above the reference opens a Czech confirmation with both prices. Accept buys the selected auction and, on success, sets a new reference. Cancel or Escape leaves the reference unchanged.
- **Category settings** - enable or disable individual item classes in **Options > AddOns > Quick Buyout**. Other item categories are opt-in; obsolete classes are hidden.
- **Buys what you selected** - pick any auction in the list and Buyout purchases exactly that one.
- **Cheapest selected by default** - when you open an item group, and after each purchase, the cheapest buyable auction (skipping your own and bid-only listings) is selected, so you can click Buyout repeatedly.
- **Double-purchase guard** - extra clicks are ignored while a purchase is in flight, and auctions already bought are never retried while the result list catches up.
- **Stale-auction recovery** - `No item found` skips that unavailable auction, selects the next cheapest buyable listing, and refreshes the results. Other purchase errors and timeouts also refresh results. Recovery never buys another item automatically; the next purchase requires another click.
- **Commodity support** - buy the selected quantity of linen cloth, herbs, and other commodities in enabled categories with one click. Price increases, unavailable quotes, and insufficient funds cancel the purchase with an error. Changing the item or quantity, leaving the commodity view, or closing the Auction House cancels a pending quote.
- **Everything else unchanged** - disabled item categories, bids, and Blizzard's unique-crafted-item warning keep their normal confirmations.

## Compatibility

Works only with the modern (retail-style) Auction House UI (`Blizzard_AuctionHouseUI`):

- Retail
- Mists of Pandaria Classic
- Classic Era / Anniversary clients that use the new Auction House UI

Clients using the legacy Auction House UI are not supported.

## Installation

Install via CurseForge, Wago, or manually by downloading the latest release from GitHub and extracting the `QuickBuyout` folder into `World of Warcraft\<flavor>\Interface\AddOns\`.

## Usage

1. Open the Auction House and search for an item in an enabled category (armor or weapons by default).
2. Click the item group to see its auctions. The cheapest is selected automatically; click another row to pick a different one.
3. Click **Buyout**. The selected auction is bought instantly, and the selection resets to the cheapest.
4. Keep clicking to buy more within 5 copper of the reference or cheaper. Above that limit, the dialog shows the new price and the reference price before you buy.

For example, after a purchase at 1s 20c, you can buy at 1s 25c with one click. A rise to 1s 26c needs confirmation even if you already paid 1s 25c. Once the confirmed purchase at 1s 26c succeeds, offers up to 1s 31c go through directly.

Reference prices are kept separately for each item key (including item level, suffix, and battle-pet species) during the current Auction House session. The first Buyout attempt establishes the reference even if the listing disappears. After that, a successful purchase below the reference lowers it, and a successful purchase explicitly confirmed in the dialog updates it. Small unconfirmed increases never raise the reference. Closing the Auction House or reloading resets these prices. Confirming a dialog revalidates the item, selected auction, current price, category setting, and available money.

To change which items use quick buyout, open **Options > AddOns > Quick Buyout** and toggle the desired categories. There are no slash commands.

For linen cloth and other crafting materials, enable **Trade Goods**, open the commodity, set the quantity, then click **Buy**. Only armor and weapons are enabled by default. If the quoted total rises, the purchase is cancelled; review the refreshed prices before clicking again.

In the AddOns list, Quick Buyout appears under **Auctions** with a coin icon.

## Development

Run the Lua behavior tests with `python -m pip install -r requirements-test.txt` and `python -m unittest discover -s tests`.

Tests simulate the WoW API and verify price confirmations, hardware-event-only item purchases, stale results, error recovery, settings, and existing commodity behavior. Live client behavior still requires an in-game check. The new price-history dialog applies to item auctions; commodities retain the original quote validation described above.

### Creating a Release

This addon uses BigWigs Packager for automated releases. To create a new release:

1. Update the version in your local repository
2. Create and push a git tag:
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```
3. The GitHub Actions workflow will automatically:
   - Package the addon
   - Create a GitHub release
   - Upload to CurseForge (if `CF_API_KEY` secret is configured and `## X-Curse-Project-ID` is set in the TOC)
   - Upload to Wago (if `WAGO_API_TOKEN` secret is configured and `## X-Wago-ID` is set in the TOC)

### Required Secrets

To enable automatic uploads, configure these repository secrets:

- `CF_API_KEY` - CurseForge API key for uploading to CurseForge
- `WAGO_API_TOKEN` - Wago API token for uploading to Wago Addons

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### Logo

`media/logo.png` is the 1:1 (512x512) project logo for CurseForge and Wago. It is excluded from the packaged addon. Regenerate it with `python media/generate_logo.py` (requires Pillow).

## License

All Rights Reserved
