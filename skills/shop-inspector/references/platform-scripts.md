# Platform-Specific Extraction Scripts

## JD.com (京东)

```javascript
(() => {
  const title = document.querySelector('.sku-title')?.textContent?.trim() || 
                document.querySelector('#name .p-name')?.textContent?.trim() ||
                document.querySelector('h1')?.textContent?.trim() || '';
  const price = document.querySelector('.price J-p-3565089')?.textContent?.trim() ||
                document.querySelector('[class*="price"]')?.textContent?.trim() || '';
  const shop = document.querySelector('.shop-name')?.textContent?.trim() ||
                document.querySelector('[class*="shop"]')?.textContent?.trim() || '';
  const sales = document.querySelector('.comment-count J-p-3565089')?.textContent?.trim() ||
                document.querySelector('[class*="sales"]')?.textContent?.trim() || '';
  const stock = document.querySelector('.stock')?.textContent?.trim() || '';
  return JSON.stringify({ title, price, shop, sales, stock });
})()
```

## Taobao (淘宝)

```javascript
(() => {
  const title = document.querySelector('.ItemHeader__title')?.textContent?.trim() ||
                document.querySelector('h1')?.textContent?.trim() || '';
  const price = document.querySelector('.price')?.textContent?.trim() ||
                document.querySelector('[class*="price"]')?.textContent?.trim() || '';
  const shop = document.querySelector('.shop-name')?.textContent?.trim() ||
                document.querySelector('[class*="shop"]')?.textContent?.trim() || '';
  const location = document.querySelector('.location')?.textContent?.trim() || '';
  return JSON.stringify({ title, price, shop, location });
})()
```

## Pinduoduo (拼多多)

```javascript
(() => {
  const title = document.querySelector('.goods-title')?.textContent?.trim() ||
                document.querySelector('h1')?.textContent?.trim() || '';
  const price = document.querySelector('.price')?.textContent?.trim() ||
                document.querySelector('[class*="price"]')?.textContent?.trim() || '';
  const sales = document.querySelector('.sales')?.textContent?.trim() ||
                document.querySelector('[class*="sale"]')?.textContent?.trim() || '';
  return JSON.stringify({ title, price, sales });
})()
```

## 1688 (阿里巴巴)

```javascript
(() => {
  const title = document.querySelector('.title-content')?.textContent?.trim() ||
                document.querySelector('h1')?.textContent?.trim() || '';
  const price = document.querySelector('.price')?.textContent?.trim() ||
                document.querySelector('[class*="price"]')?.textContent?.trim() || '';
  const moq = document.querySelector('.moq')?.textContent?.trim() ||
               document.querySelector('[class*="moq"]')?.textContent?.trim() || '';
  const shop = document.querySelector('.company-name')?.textContent?.trim() || '';
  return JSON.stringify({ title, price, moq, shop });
})()
```

## Amazon

```javascript
(() => {
  const title = document.querySelector('#productTitle')?.textContent?.trim() || '';
  const price = document.querySelector('.a-price-whole')?.textContent?.trim() || 
                document.querySelector('#priceblock_ourprice')?.textContent?.trim() || '';
  const rating = document.querySelector('.a-icon-alt')?.textContent?.trim() || '';
  const reviews = document.queryElement('#acrCustomerReviewText')?.textContent?.trim() || '';
  const seller = document.querySelector('#sellerStoreName')?.textContent?.trim() || '';
  return JSON.stringify({ title, price, rating, reviews, seller });
})()
```

## Generic Fallback

```javascript
(() => {
  return JSON.stringify({
    url: window.location.href,
    title: document.title || '',
    h1: document.querySelector('h1')?.textContent?.trim() || '',
    metaDescription: document.querySelector('meta[name="description"]')?.content || '',
    metaKeywords: document.querySelector('meta[name="keywords"]')?.content || '',
    price: Array.from(document.querySelectorAll('*')).find(el => 
      /price|价格|价钱|售价/i.test(el.className) && el.textContent?.match(/[\d,.]+/)
    )?.textContent?.trim() || ''
  });
})()
```

## Full Page Content Capture

For complete content including dynamically loaded sections:

```javascript
(() => {
  // Scroll to load dynamic content
  const scrollStep = 500;
  const maxScrolls = 10;
  let scrolls = 0;
  
  const scrollAndCapture = async () => {
    while (scrolls < maxScrolls) {
      window.scrollBy(0, scrollStep);
      await new Promise(r => setTimeout(r, 500));
      scrolls++;
    }
    window.scrollTo(0, 0);
    
    return JSON.stringify({
      url: window.location.href,
      title: document.title,
      body: document.body?.innerText?.slice(0, 5000) || '',
      images: Array.from(document.querySelectorAll('img')).map(img => ({
        src: img.src,
        alt: img.alt
      })).slice(0, 20)
    });
  };
  
  return scrollAndCapture();
})()
```