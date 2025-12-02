#!/usr/bin/env python3
"""
Product Pipeline - Full Automation

This script automates the complete product import pipeline:
1. Scrape product data from Amazon URLs
2. Enrich products with AI-generated attributes
3. Add products to the database with embeddings

Usage:
    # With URLs directly
    python scripts/pipeline.py "https://amazon.com/..." "https://amazon.com/..."

    # From a file of URLs
    python scripts/pipeline.py --file urls.txt

    # Keep intermediate files (for debugging)
    python scripts/pipeline.py --file urls.txt --keep-files
"""

import os
import sys
import argparse
import tempfile

# Add scripts directory to path for imports
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from scrape_amazon import process_urls
from enrich_products import process_products
from add_product import bulk_import


def run_pipeline(urls: list[str], keep_files: bool = False, output_dir: str = None) -> None:
    """Run the complete product import pipeline"""

    if not urls:
        print("❌ No URLs provided!")
        sys.exit(1)

    print("🎄 Last Minute Christmas - Product Import Pipeline")
    print("═" * 60)
    print(f"📋 Processing {len(urls)} URL(s)\n")

    # Determine where to save intermediate files
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        scraped_path = os.path.join(output_dir, "scraped_products.json")
        enriched_path = os.path.join(output_dir, "enriched_products.json")
    elif keep_files:
        scraped_path = "scraped_products.json"
        enriched_path = "enriched_products.json"
    else:
        # Use temp directory
        temp_dir = tempfile.mkdtemp(prefix="xmas_pipeline_")
        scraped_path = os.path.join(temp_dir, "scraped.json")
        enriched_path = os.path.join(temp_dir, "enriched.json")

    try:
        # Step 1: Scrape Amazon
        print("═" * 60)
        print("STEP 1/3: Scraping Amazon Products")
        print("═" * 60)
        process_urls(urls, scraped_path)

        # Check if scraping produced any results
        if not os.path.exists(scraped_path):
            print("\n❌ Scraping failed - no output file produced")
            sys.exit(1)

        with open(scraped_path, "r") as f:
            import json
            scraped_data = json.load(f)

        if not scraped_data:
            print("\n❌ No products were successfully scraped")
            sys.exit(1)

        print(f"\n✅ Scraped {len(scraped_data)} product(s)\n")

        # Step 2: Enrich with AI
        print("═" * 60)
        print("STEP 2/3: Enriching Products with AI")
        print("═" * 60)
        process_products(scraped_path, enriched_path)

        # Check enrichment results
        with open(enriched_path, "r") as f:
            enriched_data = json.load(f)

        if not enriched_data:
            print("\n❌ No products were successfully enriched")
            sys.exit(1)

        print(f"\n✅ Enriched {len(enriched_data)} product(s)\n")

        # Step 3: Add to database
        print("═" * 60)
        print("STEP 3/3: Adding Products to Database")
        print("═" * 60)
        bulk_import(enriched_path)

        # Final summary
        print("\n" + "═" * 60)
        print("🎉 PIPELINE COMPLETE!")
        print("═" * 60)
        print(f"✅ Successfully processed {len(enriched_data)} product(s)")

        if keep_files or output_dir:
            print(f"\n📁 Intermediate files saved:")
            print(f"   Scraped:  {scraped_path}")
            print(f"   Enriched: {enriched_path}")

    finally:
        # Cleanup temp files unless keeping them
        if not keep_files and not output_dir and 'temp_dir' in locals():
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Complete product import pipeline: scrape → enrich → add to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/pipeline.py "https://amazon.com/dp/B0123456789"
    python scripts/pipeline.py "https://..." "https://..." "https://..."
    python scripts/pipeline.py --file urls.txt
    python scripts/pipeline.py --file urls.txt --keep-files
    python scripts/pipeline.py --file urls.txt --output-dir ./data
        """
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="Amazon product URLs to process"
    )
    parser.add_argument(
        "--file", "-f",
        help="File containing Amazon URLs (one per line)"
    )
    parser.add_argument(
        "--keep-files", "-k",
        action="store_true",
        help="Keep intermediate JSON files (scraped_products.json, enriched_products.json)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="Directory to save intermediate files"
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
        print("   Usage: python scripts/pipeline.py <url> [url2] [url3] ...")
        print("   Or:    python scripts/pipeline.py --file urls.txt")
        sys.exit(1)

    run_pipeline(urls, keep_files=args.keep_files, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
