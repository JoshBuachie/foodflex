# SmartCart — Project Documentation

**Live URL:** https://joshbuachie.github.io/foodflex
**Developer:** Joshua Seth-Buachie
**Contact:** joshuaseth1@msn.com
**GitHub:** https://github.com/JoshBuachie/foodflex
**Backend:** https://livia-stannic-karla.ngrok-free.dev (ngrok tunnel — requires Mac to be running)

---

## What SmartCart Is

SmartCart is a grocery price comparison app that helps users find the cheapest prices on their grocery list across nearby stores. Users enter a zip code and a list of ingredients, and the app returns:

- Real-time prices from Kroger and Harris Teeter stores
- Nutrition grades (A–E) from Open Food Facts for every product
- NOVA group processing scores and allergen flags
- A Nutri-Score filter to highlight the healthiest option per ingredient across stores
- A savings summary showing how much cheaper the best store is vs. the most expensive

The core differentiator: SmartCart combines **price comparison AND nutrition grading** in one view. No other free grocery app does this.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript — hosted on GitHub Pages |
| Backend | Python Flask — running locally on Mac, tunneled via ngrok |
| Grocery Prices | Kroger Public API (OAuth2 client credentials) |
| Nutrition Data | Open Food Facts API (free, no key required) |
| Tunnel | ngrok (free tier — URL: livia-stannic-karla.ngrok-free.dev) |
| Analytics | Google Analytics (Measurement ID: G-W10WEGQFWJ) |
| Version Control | GitHub (JoshBuachie/foodflex) |

---

## Kroger API Credentials

- **Client ID:** `foodflex-bbcch7r7`
- **Client Secret:** Stored in `.env` file locally and in Replit Secrets
- **Scope:** `product.compact`
- **Developer Portal:** https://developer.kroger.com/manage/apps

**Important:** The Kroger client secret expires periodically. When the app returns a 401 error, go to the Kroger developer portal and reset the secret, then update the `.env` file locally.

---

## Infrastructure Problem — Akamai/Kroger CDN Block

Kroger's API is protected by Akamai's CDN which blocks requests from cloud datacenter IPs. This means the backend **cannot be hosted on Replit, Render, Railway, DigitalOcean, or similar cloud providers.** It must run from a residential IP (your home internet) tunneled through ngrok.

**Active emails sent to resolve this:**
- Kroger Developer Support (developer@kroger.com) — requested IP whitelist and list of approved hosting providers
- Three emails sent, no response as of May 2026

---

## Data Sources

### Kroger Public API
- Covers: Kroger, Harris Teeter, Fred Meyer, Ralph's, King Soopers, Smith's, Mariano's, Pick 'n Save, QFC, Dillons, Baker's, Gerbes
- Provides: Real-time product prices, promo prices, product images, store locations and hours
- Requires: Free developer account at developer.kroger.com
- Limitation: Blocked by Akamai on cloud hosting — must run from residential IP

### Open Food Facts API
- Covers: 3 million+ products globally, US-filtered
- Provides: Nutri-Score grade (A–E), NOVA group, allergens, product images
- Requires: No API key — completely free
- Limitation: Crowdsourced database — some US products missing nutrition grades
- Note: Grades return as lowercase from the API — must call `.strip().upper()` before comparing

---

## Features Built

### Core Features
- Zip code entry with 5-digit validation — button hides on valid zip, reappears when cleared
- Ingredient input with quick-add buttons (Chicken, Eggs, Milk, Broccoli, Rice, Olive Oil, Bananas, Yogurt, Ground Beef, Bread)
- Search radius selector (5 mi, 10 mi, 25 mi)
- Real-time store price comparison across up to 4 nearby stores
- Product images, brand names, and sizes displayed per item
- Sale/promo badge on discounted items
- Savings bar showing total savings vs. most expensive store

### Nutrition Features
- Nutri-Score grade badge (A–E) shown per product, color coded
- NOVA group pill showing processing level
- Allergen pills showing up to 2 allergens per product
- Grade filter bar (All / A / B / C / D / E) — highlights healthiest option per ingredient across all stores, dims non-matching items

### UI/UX
- Light teal theme (SmartCart brand colors)
- Fonts: Outfit (headers) + Nunito (body)
- Soft radial gradient background (replaced graph paper pattern after user feedback)
- "More stores coming soon" banner showing Aldi, Publix, Whole Foods, Wegmans, Costco, Safeway, H-E-B, Walmart
- Best Value badge on cheapest store card — moved to inline position above store name (was overlapping price)
- Product names truncate with ellipsis on narrow screens (prevents price/text collision)
- Google Analytics tracking with search event logging

---

## Bugs Fixed During Development

| Bug | Cause | Fix |
|---|---|---|
| 401 Unauthorized | Kroger client secret expired | Reset secret at developer portal, update .env |
| 403 Forbidden (cloud) | Akamai CDN blocks datacenter IPs | Use ngrok from home IP |
| Auto-detects Virginia Beach zip | ipapi.co returns developer's IP, not user's | Disabled auto-detect, manual zip entry only |
| Nutrition grades all null | API returns lowercase grades ("a") not uppercase ("A") | Added `.strip().upper()` to grade comparison |
| Nutrition grades still null | Open Food Facts timeout (European servers) | Increased timeout to 15s, added retry logic, added US country filter |
| Port 5000 already in use | Multiple backend processes running | `fuser -k 5000/tcp` or `pkill -f backend.py` |
| Best Value badge covers price | `position: absolute; right: 14px` overlapped total price | Moved badge to inline position above store name |
| Price/text collision on mobile | `.item-name` had no overflow protection | Added `text-overflow: ellipsis; white-space: nowrap` |
| Graph paper background | CSS grid pattern looked unfinished | Replaced with soft radial gradient |

---

## Outreach & Partnership Status

| Contact | Email | Sent | Status |
|---|---|---|---|
| Kroger Developer Support | developer@kroger.com | March 20, 2026 | No response |
| Kroger Follow-up | developer@kroger.com | April 3, 2026 | No response |
| Kroger Hosting Question | developer@kroger.com | April 14, 2026 | No response |
| Instacart Developer Program | developers@instacart.com | March 2026 | Waitlisted |
| Instacart Reapplication | developers@instacart.com | April 12, 2026 | Awaiting response |
| Lila Santos (Instacart PM) | Lila.santos@instacart.com | April 16, 2026 | Awaiting response |
| Lila Santos Follow-up | Lila.santos@instacart.com | May 2026 | Awaiting response |
| Micheal Waldroup (Grocery Dealz) | micheal@grocerydealz.com | April 13, 2026 | No response |
| Micheal Waldroup Follow-up | micheal@grocerydealz.com | May 2026 | Awaiting response |

---

## Stores Researched — API Availability

| Store | Public Price API | Notes |
|---|---|---|
| Kroger / Harris Teeter | ✅ Free | Working — blocked on cloud hosting |
| Instacart (1,400+ stores) | Partner approval required | Applied — on waitlist |
| Walmart | ❌ | Partners/sellers only — no public API |
| Target | ❌ | No public developer API |
| Albertsons / Safeway | ❌ | Advertisers only |
| Aldi | ❌ | No public API — blocks datacenter IPs |
| Lidl | ❌ | No public API |
| Costco | ❌ | Membership club — no public API |
| Sam's Club | ❌ | Advertising API only |
| Flipp | ❌ | B2B retailer platform — not for developers |

---

## Deployment Setup

### Local Development
```bash
cd ~/Documents/My_Stuff/FoodFlex_App
python3 backend.py
# In separate terminal:
ngrok http 5000
# In separate terminal (prevents Mac sleep):
caffeinate -i
```

### GitHub Pages (Frontend)
- Repo: github.com/JoshBuachie/foodflex
- Branch: main
- File: index.html
- URL: https://joshbuachie.github.io/foodflex

### Updating the App
1. Edit `index.html` locally or on GitHub
2. If editing locally: `git add . && git commit -m "message" && git push`
3. If editing on GitHub: pencil icon → edit → commit directly to main
4. GitHub Pages rebuilds automatically within 2 minutes

### Important: ngrok URL
The ngrok URL (`livia-stannic-karla.ngrok-free.dev`) is set in `index.html`:
```javascript
const API = "https://livia-stannic-karla.ngrok-free.dev/api";
```
If ngrok restarts and generates a new URL, this line must be updated and pushed to GitHub.

---

## Next Steps / Open Items

1. **Resolve Kroger hosting block** — waiting on Kroger developer support response about approved hosting providers
2. **Instacart Partner API approval** — would unlock Aldi, Publix, Costco, Wegmans, Safeway and 1,400+ more stores
3. **Permanent hosting** — once Kroger responds, move backend to a VPS so app doesn't require Mac to be running
4. **Receipt scanning** — allow users to photograph receipts to crowdsource prices for stores without APIs
5. **Price alerts** — notify users when an item drops below a target price
6. **User accounts** — save grocery lists between sessions

---

## Key Lessons Learned

- Kroger is the only major US grocery chain with a free public pricing API
- All major cloud hosting providers (Replit, Render, Railway, DigitalOcean) are blocked by Kroger's Akamai CDN
- Open Food Facts is reliable for nutrition grades when US country filter is applied and timeout is set to 15s+
- Instacart Partner API has fewer than 100 spots — direct outreach to program manager is required
- Grocery Dealz uses an unidentified third-party data provider for multi-store pricing — this is a key lead
- ngrok free tier works but requires Mac to stay on and awake (`caffeinate -i` prevents sleep)
- Always validate Kroger client secret before debugging code — it expires regularly
