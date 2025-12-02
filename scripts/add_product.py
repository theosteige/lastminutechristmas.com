#!/usr/bin/env python3
"""
Add Product Script

This script helps you efficiently add products to the database with
auto-generated embeddings for semantic search.

Usage:
    python scripts/add_product.py                    # Interactive mode
    python scripts/add_product.py --bulk FILE.json   # Bulk import
"""

import os
import sys
import json
import argparse
from typing import Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate environment variables
if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY]):
    print("❌ Missing required environment variables!")
    print("   Please set: SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY")
    print("   You can copy .env.example to .env and fill in your values.")
    sys.exit(1)

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================================================
# TYPES
# ============================================================================

@dataclass
class ProductInput:
    name: str
    amazon_url: str
    price: float
    min_age: int
    max_age: int
    gender: str  # 'male', 'female', 'unisex'
    category: str
    prime_eligible: bool
    product_description: str  # The actual Amazon listing description
    description: str  # AI-generated semantic description for matching
    tags: Optional[list[str]] = None
    image_url: Optional[str] = None
    amazon_asin: Optional[str] = None


# ============================================================================
# EMBEDDING GENERATION
# ============================================================================

def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text using OpenAI's API"""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def create_embedding_text(product: ProductInput) -> str:
    """
    Create the text that will be embedded for semantic search.
    Combines description with tags and category for richer matching.
    """
    parts = [
        product.description,
        f"Category: {product.category}",
        f"Good for ages {product.min_age} to {product.max_age}",
    ]

    if product.gender != "unisex":
        parts.append(f"Best for {product.gender}")

    if product.tags:
        parts.append(f"Keywords: {', '.join(product.tags)}")

    return ". ".join(filter(None, parts))


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def add_product(product: ProductInput) -> dict:
    """Add a single product to the database"""
    print(f"\n📦 Processing: {product.name}")

    # Generate embedding
    print("   🧠 Generating embedding...")
    embedding_text = create_embedding_text(product)
    embedding = generate_embedding(embedding_text)
    print(f"   ✅ Embedding generated ({len(embedding)} dimensions)")

    # Prepare data for insert
    data = {
        "name": product.name,
        "amazon_url": product.amazon_url,
        "price": product.price,
        "min_age": product.min_age,
        "max_age": product.max_age,
        "gender": product.gender,
        "category": product.category,
        "prime_eligible": product.prime_eligible,
        "product_description": product.product_description,
        "description": product.description,
        "embedding": embedding,
    }

    # Add optional fields if present
    if product.tags:
        data["tags"] = product.tags
    if product.image_url:
        data["image_url"] = product.image_url
    if product.amazon_asin:
        data["amazon_asin"] = product.amazon_asin

    # Insert into database
    print("   💾 Saving to database...")
    try:
        result = supabase.table("products").insert(data).execute()

        if result.data:
            print(f"   ✅ Saved with ID: {result.data[0]['id']}")
            return result.data[0]
        else:
            raise Exception("Insert returned no data")
    except Exception as e:
        error_msg = str(e)
        # Check for common issues
        if "product_description" in error_msg:
            print("   ⚠️  Hint: Run migration 003_add_product_description.sql in Supabase")
        elif "relation" in error_msg and "does not exist" in error_msg:
            print("   ⚠️  Hint: Run migration 001_create_products_table.sql in Supabase")
        raise Exception(f"Database error: {error_msg}")


def add_products_bulk(products: list[ProductInput]) -> None:
    """Add multiple products in bulk"""
    print(f"\n📦 Processing {len(products)} products...\n")

    success_count = 0
    error_count = 0

    for product in products:
        try:
            add_product(product)
            success_count += 1
        except Exception as e:
            error_count += 1
            print(f"   ❌ Failed to add: {product.name} - {e}")

    print(f"\n✅ Complete: {success_count} added, {error_count} failed")


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

def prompt(question: str, default: str = "") -> str:
    """Prompt user for input with optional default"""
    if default:
        result = input(f"{question} [{default}]: ").strip()
        return result if result else default
    return input(f"{question}: ").strip()


def prompt_int(question: str, default: int) -> int:
    """Prompt user for integer input"""
    result = prompt(question, str(default))
    return int(result) if result else default


def prompt_float(question: str) -> float:
    """Prompt user for float input"""
    result = prompt(question)
    return float(result)


def prompt_bool(question: str, default: bool = False) -> bool:
    """Prompt user for yes/no input"""
    default_str = "y" if default else "n"
    result = prompt(f"{question} (y/n)", default_str).lower()
    return result == "y"


def interactive_add_product() -> None:
    """Interactive mode for adding a single product"""
    print("\n🎁 Add a New Product\n")
    print("═" * 50)

    # Required fields
    name = prompt("Product name")
    amazon_url = prompt("Amazon URL")
    price = prompt_float("Price (e.g., 49.99)")

    # Age range
    min_age = prompt_int("Minimum age", 0)
    max_age = prompt_int("Maximum age", 99)

    # Gender
    gender_input = prompt("Gender (male/female/unisex)", "unisex").lower()
    if gender_input not in ["male", "female", "unisex"]:
        gender_input = "unisex"

    # Category
    category = prompt("Category (e.g., electronics, toys, books)")

    # Delivery info
    prime_eligible = prompt_bool("Prime eligible?", False)

    # Product description (Amazon listing)
    print("\n📄 Product Description (from Amazon listing)")
    product_description = prompt("Product description")

    # Description (AI semantic matching)
    print("\n📝 Semantic Description (this is used for AI matching!)")
    print("   Write 1-3 sentences describing who this gift is perfect for.")
    print("   Example: 'Perfect for tech enthusiasts who love smart home")
    print("   gadgets. Great for anyone who enjoys music or podcasts.'\n")
    description = prompt("Description")

    # Tags
    tags_input = prompt("Tags (comma-separated, e.g., tech lover, gamer)", "")
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else None

    # Optional fields
    image_url = prompt("Image URL (optional, press Enter to skip)", "") or None
    amazon_asin = prompt("Amazon ASIN (optional, press Enter to skip)", "") or None

    # Confirm
    print("\n" + "═" * 50)
    print("📋 Product Summary:")
    print(f"   Name: {name}")
    print(f"   Price: ${price}")
    print(f"   Age: {min_age}-{max_age}")
    print(f"   Gender: {gender_input}")
    print(f"   Category: {category}")
    print(f"   Prime: {'Yes' if prime_eligible else 'No'}")
    print(f"   Description: {description[:50]}...")
    print("═" * 50)

    if not prompt_bool("\nAdd this product?", True):
        print("❌ Cancelled")
        return

    # Build product object
    product = ProductInput(
        name=name,
        amazon_url=amazon_url,
        price=price,
        min_age=min_age,
        max_age=max_age,
        gender=gender_input,
        category=category,
        prime_eligible=prime_eligible,
        product_description=product_description,
        description=description,
        tags=tags,
        image_url=image_url,
        amazon_asin=amazon_asin,
    )

    # Add to database
    add_product(product)

    # Ask about adding another
    if prompt_bool("\n🎁 Add another product?", False):
        interactive_add_product()


# ============================================================================
# BULK IMPORT
# ============================================================================

def bulk_import(file_path: str) -> None:
    """Import products from a JSON file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("❌ JSON file must contain an array of products")
        sys.exit(1)

    products = [ProductInput(**item) for item in data]
    add_products_bulk(products)


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("🎄 Last Minute Christmas - Product Manager\n")
    parser = argparse.ArgumentParser(description="Add products to the gift database")
    parser.add_argument("--bulk", metavar="FILE", help="Bulk import from JSON file")
    args = parser.parse_args()

    if args.bulk:
        bulk_import(args.bulk)
    else:
        interactive_add_product()


if __name__ == "__main__":
    main()
