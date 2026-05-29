---
name: shop-inspector
description: >
  Product inspection skill using OpenCLI browser automation. When user shares a product link
  (e.g., from JD/Taobao/Pinduoduo/1688/Amazon/eBay/Shopee) or asks to inspect/check/view a product,
  use this skill to open the link in browser, capture page content, and extract key product information.
license: MIT
metadata:
  version: "1.0"
  category: productivity
  sources:
    - https://github.com/jackwener/opencli
---

# Shop Inspector

Automated product page inspection using OpenCLI browser bridge + AnySearch for external reviews.

## Workflow

### Step 1: Ensure OpenCLI is Available
**Assumption:** OpenCLI is always installed (`opencli` command available). Skip verification.

### Step 2: Ensure Chrome is Running
```bash
# Check if Chrome is already running
if ! tasklist | findstr /I "chrome.exe" > nul 2>&1; then
  start chrome
  timeout /t 5 > nul
fi
```

### Step 3: Open Product Link In Browser
```bash
opencli browser open "<product_url>"
```

**Important URL handling:**

| Platform | Recommended URL | Notes |
|----------|----------------|-------|
| JD (京东) | `item.m.jd.com/product/<id>.html` | Use **mobile URL** (`item.m.jd.com`), not desktop. Desktop may redirect to login. |
| JD Short Link | `3.cn/xxx` | Short links redirect to mobile URLs automatically. Works fine. |
| Taobao (淘宝) | `item.taobao.com/item.htm?id=...` | Use desktop URL |
| Pinduoduo (拼多多) | `mobile.pinduoduo.com/goods.html?goodsID=...` | Use mobile URL |
| 1688 | `detail.1688.com/offer/...` | Use desktop URL |
| Amazon | `www.amazon.com/dp/...` | Use desktop URL |
| eBay | `www.ebay.com/itm/...` | Use desktop URL |
| Shopee | `shopee.tw/product/...` | Use desktop URL |

**Tip:** If user provides a short link (3.cn, t.cn, etc.), it's usually fine — short links auto-expand to the correct mobile/desktop URL.

### Step 4: Verify Page Loaded (Check for Login Redirect)

**CRITICAL:** After opening the page, ALWAYS check the actual URL:

```bash
opencli browser state 2>&1
```

**Check for login redirect indicators:**
- URL contains `login` or `plogin` → User needs to login first
- Title contains "登录" or "注册" → User needs to login first

**If redirected to login:**
1. Tell user: "页面跳转到了登录页面，请先在Chrome里手动登录京东/淘宝，然后我再重试"
2. Do NOT proceed without login

**If login required, use AnySearch as fallback:**
```bash
node "<anysearch-path>/scripts/anysearch_cli.js" batch_search \
  --query "<product_name> 评测" \
  --query "<product_name> 怎么样" \
  --query "<product_name> 用户评价"
```
*(Replace `<anysearch-path>` with the local path to the anysearch skill, or use `web_search` as a built-in fallback.)*

### Step 5: Wait for Page Load (if not redirected)
```bash
timeout /t 4 > nul
```

### Step 6: Capture Page Content

Use `opencli browser state` to get page structure:

```bash
opencli browser state 2>&1
```

This returns:
- Current URL
- Page title
- Interactive elements (buttons, links, inputs)
- Text content

**Common page elements to look for:**
- Product title: `document.title` or `h1`, `#itemName`
- Price: elements with `price` in class/id
- Shop name: elements with `shop` in class/id
- Sales info: elements with `sale` or `comment` in class/id

### Step 7: Search for Product Reviews and Evaluations

Use AnySearch to gather external information:

**Command:**
```bash
node "<anysearch-path>/scripts/anysearch_cli.js" batch_search \
  --query "<product_name> 评测" \
  --query "<product_name> 怎么样" \
  --query "<product_name> 用户评价" \
  --query "<product_name> 优缺点"
```

**Single search:**
```bash
node "<anysearch-path>/scripts/anysearch_cli.js" search "<product_name> 评测 评价" --max_results 10
```

**AnySearch Fallback (if service unavailable):**
```bash
web_search "<product_name> 评测 评价" --count 10
```

### Step 8: Synthesize Results

After collecting information, compile a product report:
- Product title, price, shop info
- Key features and specifications
- Expert reviews and evaluations
- User reviews and ratings
- Pros and cons summary

## Common Issues & Solutions

### Issue 1: Redirected to Login Page
**Symptom:** URL shows `plogin.m.jd.com/login/` or similar
**Solution:*o User must login in Chrome first. Use AnySearch fallback for product info.

### Issue 2: Wrong Page Loaded
**Symptom:** Page shows homepage or wrong product
**Solution:** Check `opencli browser state` to see actual URL after redirect. User may need to provide direct product URL.

### Issue 3: AnySearch Service Unavailable
**Symptom:** "Connection Error" or "temporarily unavailable"
**Solution:** Fall back to `web_search` (MCP matrix tool) for search results.

### Issue 4: Page Content Empty
**Symptom:** `opencli browser state` shows empty body
**Solution:** Wait longer (6-8 seconds), or scroll the page first with `opencli browser scroll down`

## Prerequisites

- OpenCLI installed (`npm install -g @jackwener/opencli`)
- OpenCLI browser extension installed in Chrome
- Chrome browser (auto-started if not running)
- AnySearch skill installed (optional, for enhanced search; falls back to `web_search` if unavailable)
- User logged into shopping platforms in Chrome (for non-public product pages)

## Notes

1. **Assumption:** OpenCLI is always functional — do not verify installation.
2. **Login state:** Uses local browser cookies. If redirected to login, prompt user to login first.
3. **Mobile URLs preferred:** For JD/Pinduoduo, use mobile URLs to avoid login issues.
4. **Short links work:** 3.cn, t.cn etc. auto-redirect correctly, no special handling needed.
5. **AnySearch fallback:** If service unavailable, use `web_search` as backup.
6. **Always check URL:** After opening, verify actual URL matches expected product page.
7. **Wait time:** 4 seconds after navigation, more for lazy-loaded content.