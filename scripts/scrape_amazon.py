#!/usr/bin/env python3
"""
Amazon Product Scraper

This script scrapes product information from Amazon URLs and outputs
JSON ready for enrich_products.py.

Usage:
    # Single URL
    python scripts/scrape_amazon.py "https://www.amazon.com/LEGO-Ideas-Disney-Pixar-Luxo/dp/B0DRW73TRY?pf_rd_p=a90ff7b9-3e0e-4f4f-8970-dbe4040ee678&pf_rd_r=ASX7RRZ890MBQ17T5M17&sr=1-1-b7319524-e488-4299-b789-97891b0df4ae&linkCode=sl1&tag=xmasgiftrescu-20&linkId=c3657865dd303b53eb2fbd4175ae3bac&language=en_US&ref_=as_li_ss_tl"

    # Multiple URLs
    python scripts/scrape_amazon.py "https://..." "https://..." "https://..."

    # From a file (one URL per line)
    python scripts/scrape_amazon.py --file urls.txt

    # Specify output file
    python scripts/scrape_amazon.py --file urls.txt --output products.json

Output: JSON file ready for enrich_products.py
"""

import os
import sys
import json
import time
import random
import argparse
import re
from typing import Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, parse_qs

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Missing required packages!")
    print("   Please run: pip install requests beautifulsoup4")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Rotate through different user agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Delay between requests (seconds) to be respectful
MIN_DELAY = 2
MAX_DELAY = 5

# Retry configuration
MAX_RETRY_ROUNDS = 5  # Maximum number of retry rounds for failed URLs
RETRY_BASE_DELAY = 30  # Base delay before retrying failed URLs (seconds)


# ============================================================================
# TYPES
# ============================================================================

@dataclass
class ScrapedProduct:
    """Product data scraped from Amazon"""
    name: str
    amazon_url: str
    price: float
    prime_eligible: bool
    image_url: Optional[str]
    product_description: str


# ============================================================================
# URL HANDLING
# ============================================================================

def expand_short_url(url: str) -> str:
    """Expand amzn.to short URLs to full Amazon URLs"""
    if "amzn.to" in url or "a.co" in url:
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.url
        except Exception as e:
            print(f"   ⚠️  Could not expand short URL: {e}")
            return url
    return url


def extract_asin(url: str) -> Optional[str]:
    """Extract ASIN from Amazon URL"""
    # Try /dp/ASIN pattern
    dp_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if dp_match:
        return dp_match.group(1)

    # Try /gp/product/ASIN pattern
    gp_match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
    if gp_match:
        return gp_match.group(1)

    # Try /product/ASIN pattern
    product_match = re.search(r'/product/([A-Z0-9]{10})', url)
    if product_match:
        return product_match.group(1)

    return None


def normalize_amazon_url(url: str) -> str:
    """Convert any Amazon URL to a clean canonical URL"""
    expanded = expand_short_url(url)
    asin = extract_asin(expanded)

    if asin:
        # Return clean canonical URL
        return f"https://www.amazon.com/dp/{asin}"

    return expanded


# ============================================================================
# SCRAPING
# ============================================================================

def get_headers() -> dict:
    """Get request headers with random user agent"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def scrape_product(url: str) -> Optional[ScrapedProduct]:
    """Scrape product information from an Amazon URL"""

    # Normalize the URL
    normalized_url = normalize_amazon_url(url)

    try:
        response = requests.get(normalized_url, headers=get_headers(), timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"   ❌ Failed to fetch page: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Check for CAPTCHA/bot detection
    if "api-services-support@amazon.com" in response.text or "Enter the characters you see below" in response.text:
        print("   ❌ Amazon detected automated access (CAPTCHA). Try again later or use fewer requests.")
        return None

    # Extract product name
    name = None
    name_elem = soup.find("span", {"id": "productTitle"})
    if name_elem:
        name = name_elem.get_text(strip=True)
    else:
        # Fallback: try meta title
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove "Amazon.com: " prefix and " : Everything Else" suffix
            name = re.sub(r'^Amazon\.com:\s*', '', title_text)
            name = re.sub(r'\s*:\s*(Electronics|Home & Kitchen|Toys & Games|Sports & Outdoors|Everything Else|Books|Clothing|Beauty|Health).*$', '', name)

    if not name:
        print("   ❌ Could not find product name")
        return None

    # Extract price
    price = None

    # Try multiple price selectors
    price_selectors = [
        {"class": "a-price-whole"},
        {"id": "priceblock_ourprice"},
        {"id": "priceblock_dealprice"},
        {"id": "priceblock_saleprice"},
        {"class": "a-offscreen"},  # Often contains the price
    ]

    for selector in price_selectors:
        price_elem = soup.find("span", selector)
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Extract numeric value
            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(",", ""))
            if price_match:
                try:
                    price = float(price_match.group())
                    if price > 0:
                        break
                except ValueError:
                    continue

    # Try the combined price container
    if not price:
        price_container = soup.find("span", {"class": "a-price"})
        if price_container:
            offscreen = price_container.find("span", {"class": "a-offscreen"})
            if offscreen:
                price_text = offscreen.get_text(strip=True)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(",", ""))
                if price_match:
                    try:
                        price = float(price_match.group())
                    except ValueError:
                        pass

    if not price:
        print("   ⚠️  Could not find price, using 0.00")
        price = 0.00

    # Check for Prime eligibility
    prime_eligible = False
    prime_indicators = [
        soup.find("span", {"class": "a-icon-prime"}),
        soup.find("i", {"class": "a-icon-prime"}),
        soup.find("span", string=re.compile(r"FREE.*delivery", re.IGNORECASE)),
        soup.find("span", {"data-csa-c-delivery-price": "FREE"}),
    ]
    prime_eligible = any(indicator is not None for indicator in prime_indicators)

    # Also check for Prime text
    if not prime_eligible:
        prime_text = soup.find(string=re.compile(r"Prime FREE", re.IGNORECASE))
        prime_eligible = prime_text is not None

    # Extract main image URL
    image_url = None

    # Try the main product image
    img_selectors = [
        {"id": "landingImage"},
        {"id": "imgBlkFront"},
        {"id": "main-image"},
        {"class": "a-dynamic-image"},
    ]

    for selector in img_selectors:
        img_elem = soup.find("img", selector)
        if img_elem:
            # Try data-old-hires first (high-res image)
            image_url = img_elem.get("data-old-hires")
            if not image_url:
                image_url = img_elem.get("src")
            if image_url and not image_url.startswith("data:"):
                break
            image_url = None

    # Extract product description
    product_description = ""

    # Try feature bullets first
    feature_bullets = soup.find("div", {"id": "feature-bullets"})
    if feature_bullets:
        bullets = feature_bullets.find_all("span", {"class": "a-list-item"})
        bullet_texts = [b.get_text(strip=True) for b in bullets if b.get_text(strip=True)]
        product_description = " ".join(bullet_texts)

    # Try product description section
    if not product_description:
        desc_elem = soup.find("div", {"id": "productDescription"})
        if desc_elem:
            product_description = desc_elem.get_text(strip=True)

    # Try "About this item" section
    if not product_description:
        about_elem = soup.find("div", {"id": "aplus_feature_div"})
        if about_elem:
            product_description = about_elem.get_text(strip=True)[:1000]  # Limit length

    # Fallback: use the product title as description
    if not product_description:
        product_description = name

    # Clean up description
    product_description = re.sub(r'\s+', ' ', product_description).strip()
    # Limit to reasonable length
    if len(product_description) > 2000:
        product_description = product_description[:2000] + "..."

    return ScrapedProduct(
        name=name,
        amazon_url=normalized_url,
        price=price,
        prime_eligible=prime_eligible,
        image_url=image_url,
        product_description=product_description,
    )


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def scrape_batch(urls: list[str], products: list[dict], round_num: int = 1) -> list[str]:
    """
    Scrape a batch of URLs, return list of failed URLs.
    Successfully scraped products are appended to the products list.
    """
    failed_urls = []
    total = len(urls)

    for i, url in enumerate(urls, 1):
        url = url.strip()
        if not url:
            continue

        print(f"[{i}/{total}] 🔍 {url[:60]}...")

        product = scrape_product(url)

        if product:
            products.append(asdict(product))
            print(f"         ✅ {product.name[:50]}...")
            print(f"         💰 ${product.price:.2f} | Prime: {'Yes' if product.prime_eligible else 'No'}")
        else:
            failed_urls.append(url)
            print(f"         ❌ Failed (will retry)")

        # Delay between requests (except for the last one)
        if i < total:
            # Use longer delays in retry rounds
            min_delay = MIN_DELAY * round_num
            max_delay = MAX_DELAY * round_num
            delay = random.uniform(min_delay, max_delay)
            print(f"         ⏳ Waiting {delay:.1f}s...\n")
            time.sleep(delay)
        else:
            print()

    return failed_urls


def process_urls(urls: list[str], output_path: str, max_retries: int = MAX_RETRY_ROUNDS, retry_delay: int = RETRY_BASE_DELAY) -> None:
    """Process multiple URLs and save results, with automatic retry for failures"""
    print(f"🛒 Scraping {len(urls)} Amazon product(s)...\n")

    products = []
    pending_urls = [url.strip() for url in urls if url.strip()]
    total_urls = len(pending_urls)

    # Initial scraping round
    print("─" * 50)
    print("Round 1: Initial scraping")
    print("─" * 50)
    failed_urls = scrape_batch(pending_urls, products, round_num=1)

    # Retry failed URLs with exponential backoff
    retry_round = 1
    while failed_urls and retry_round <= max_retries:
        wait_time = retry_delay * (2 ** (retry_round - 1))  # Exponential backoff
        print(f"\n{'─' * 50}")
        print(f"⚠️  {len(failed_urls)} URL(s) failed. Retrying in {wait_time}s...")
        print(f"Round {retry_round + 1}/{max_retries + 1}: Retry attempt {retry_round}")
        print("─" * 50)

        # Wait before retrying (helps with CAPTCHA cooldown)
        print(f"⏳ Waiting {wait_time}s before retry...\n")
        time.sleep(wait_time)

        # Retry failed URLs
        failed_urls = scrape_batch(failed_urls, products, round_num=retry_round + 1)
        retry_round += 1

    # Save results
    if products:
        with open(output_path, "w") as f:
            json.dump(products, f, indent=2)

    # Final summary
    success_count = len(products)
    final_failed = len(failed_urls)

    print("\n" + "═" * 50)
    print(f"✅ Complete: {success_count}/{total_urls} scraped")

    if final_failed > 0:
        print(f"❌ Failed after {max_retries} retries: {final_failed}")
        print("   Failed URLs:")
        for url in failed_urls:
            print(f"   - {url[:70]}...")

    if products:
        print(f"\n📁 Output saved to: {output_path}")
        print("")
        print("Next steps:")
        print(f"  1. python scripts/enrich_products.py {output_path}")
        print(f"  2. python scripts/add_product.py --bulk {output_path.replace('.json', '_enriched.json')}")
    else:
        print("❌ No products were successfully scraped")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Scrape product information from Amazon URLs"
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="Amazon product URLs to scrape"
    )
    parser.add_argument(
        "--file", "-f",
        help="File containing Amazon URLs (one per line)"
    )
    parser.add_argument(
        "--output", "-o",
        default="scraped_products.json",
        help="Output JSON file (default: scraped_products.json)"
    )
    parser.add_argument(
        "--max-retries", "-r",
        type=int,
        default=MAX_RETRY_ROUNDS,
        help=f"Maximum retry rounds for failed URLs (default: {MAX_RETRY_ROUNDS})"
    )
    parser.add_argument(
        "--retry-delay", "-d",
        type=int,
        default=RETRY_BASE_DELAY,
        help=f"Base delay in seconds before retrying (default: {RETRY_BASE_DELAY}s, doubles each round)"
    )
    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="Disable automatic retry of failed URLs"
    )

    args = parser.parse_args()

    # Collect URLs from arguments and/or file
    urls = list(args.urls) if args.urls else []

    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        with open(args.file, "r") as f:
            file_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            urls.extend(file_urls)

    if not urls:
        print("❌ No URLs provided!")
        print("   Usage: python scripts/scrape_amazon.py <url> [url2] [url3] ...")
        print("   Or:    python scripts/scrape_amazon.py --file urls.txt")
        sys.exit(1)

    # Determine retry settings
    max_retries = 0 if args.no_retry else args.max_retries
    process_urls(urls, args.output, max_retries=max_retries, retry_delay=args.retry_delay)


if __name__ == "__main__":
    main()
