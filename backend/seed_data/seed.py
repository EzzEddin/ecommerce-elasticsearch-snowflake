"""
Seed script to populate PostgreSQL with realistic e-commerce data.
Run: python -m seed_data.seed
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy import text

from app.config import settings
from app.core.database import async_session_factory, engine, Base
from app.models.product import Category, Inventory, Order, OrderItem, Product

fake = Faker()

CATEGORIES = [
    ("Electronics", "Gadgets, devices, and electronic accessories"),
    ("Clothing", "Apparel and fashion items for all occasions"),
    ("Home & Kitchen", "Furniture, kitchenware, and home decor"),
    ("Books", "Fiction, non-fiction, educational, and reference books"),
    ("Sports & Outdoors", "Equipment and gear for sports and outdoor activities"),
    ("Beauty & Health", "Skincare, cosmetics, vitamins, and wellness products"),
    ("Toys & Games", "Toys, board games, and entertainment for all ages"),
    ("Automotive", "Car parts, accessories, and maintenance products"),
    ("Garden & Tools", "Gardening supplies, power tools, and hardware"),
    ("Food & Grocery", "Gourmet food, snacks, beverages, and pantry staples"),
]

BRANDS_BY_CATEGORY = {
    "Electronics": ["TechVolt", "NovaByte", "PixelPeak", "CircuitPro", "DigiWave"],
    "Clothing": ["UrbanThread", "StitchLine", "VelvetEdge", "PrimeFit", "SilkRoad"],
    "Home & Kitchen": ["CozyNest", "CraftsHome", "KitchenElite", "HomeVibe", "CleanSlate"],
    "Books": ["PageTurner Press", "InkWell", "BrightMind", "EpicReads", "NovelHouse"],
    "Sports & Outdoors": ["TrailBlaze", "IronGrip", "PeakForm", "SwiftStride", "AquaForce"],
    "Beauty & Health": ["GlowUp", "PureSkin", "VitalBloom", "ZenCare", "RadiantYou"],
    "Toys & Games": ["FunFactory", "PlaySpark", "ToyVenture", "GameMaster", "KidJoy"],
    "Automotive": ["AutoEdge", "TurboFit", "DriveMax", "MotorCraft", "RoadReady"],
    "Garden & Tools": ["GreenThumb", "ToolForge", "GardenPro", "IronWorks", "BloomCraft"],
    "Food & Grocery": ["FreshHarvest", "TasteBox", "NutriPick", "GourmetBay", "PantryPlus"],
}

PRODUCT_TEMPLATES = {
    "Electronics": [
        "Wireless {adj} Headphones", "Bluetooth {adj} Speaker", "{adj} Smart Watch",
        "{adj} Mechanical Keyboard", "Portable {adj} Charger",
        "{adj} Webcam HD", "{adj} Wireless Mouse", "LED {adj} Monitor Stand",
        "{adj} Phone Case", "Smart {adj} Light Bulb", "{adj} Power Bank",
    ],
    "Clothing": [
        "{adj} Cotton T-Shirt", "{adj} Slim Fit Jeans", "{adj} Running Shoes",
        "{adj} Winter Jacket", "{adj} Casual Hoodie", "{adj} Dress Shirt",
        "{adj} Yoga Pants", "{adj} Leather Belt", "{adj} Baseball Cap",
        "{adj} Wool Sweater", "{adj} Hiking Boots", "{adj} Linen Shorts",
    ],
    "Home & Kitchen": [
        "{adj} Stainless Steel Pan", "{adj} Coffee Maker", "{adj} Cutting Board Set",
        "{adj} Throw Blanket", "{adj} Storage Organizer", "{adj} Scented Candle",
        "{adj} Kitchen Scale", "{adj} Wine Glass Set", "{adj} Table Lamp",
        "{adj} Spice Rack", "{adj} Dish Towel Set", "{adj} Ceramic Vase",
    ],
    "Books": [
        "The {adj} Journey", "{adj} Coding Mastery", "The Art of {adj} Living",
        "{adj} Python Cookbook", "The {adj} Guide to Data", "{adj} Machine Learning",
        "Understanding {adj} Systems", "The {adj} Startup", "{adj} Leadership",
        "The {adj} Mind", "{adj} History of Science", "The {adj} Algorithm",
    ],
    "Sports & Outdoors": [
        "{adj} Yoga Mat", "{adj} Resistance Bands", "{adj} Water Bottle",
        "{adj} Camping Tent", "{adj} Hiking Backpack", "{adj} Jump Rope",
        "{adj} Dumbbell Set", "{adj} Running Armband", "{adj} Bike Light",
        "{adj} Swim Goggles", "{adj} Tennis Racket", "{adj} Fishing Rod",
    ],
    "Beauty & Health": [
        "{adj} Face Moisturizer", "{adj} Vitamin C Serum", "{adj} Sunscreen SPF 50",
        "{adj} Hair Oil", "{adj} Lip Balm Set", "{adj} Eye Cream",
        "{adj} Body Lotion", "{adj} Protein Powder", "{adj} Multivitamin",
        "{adj} Collagen Supplement", "{adj} Face Mask Pack", "{adj} Essential Oils",
    ],
    "Toys & Games": [
        "{adj} Building Blocks", "{adj} Board Game", "{adj} Puzzle Set",
        "{adj} Remote Control Car", "{adj} Art Kit", "{adj} Science Kit",
        "{adj} Card Game", "{adj} Stuffed Animal", "{adj} Action Figure",
        "{adj} Drone Mini", "{adj} Magic Kit", "{adj} Lego Set",
    ],
    "Automotive": [
        "{adj} Car Phone Mount", "{adj} Dash Cam", "{adj} Tire Inflator",
        "{adj} Car Vacuum", "{adj} Seat Cover Set", "{adj} LED Headlights",
        "{adj} Floor Mats", "{adj} Trunk Organizer", "{adj} Car Charger",
        "{adj} Windshield Cover", "{adj} Oil Filter", "{adj} Jump Starter",
    ],
    "Garden & Tools": [
        "{adj} Garden Hose", "{adj} Pruning Shears", "{adj} Power Drill",
        "{adj} Lawn Mower", "{adj} Plant Pots Set", "{adj} Tool Box",
        "{adj} Work Gloves", "{adj} Measuring Tape", "{adj} LED Flashlight",
        "{adj} Seed Starter Kit", "{adj} Solar Lights", "{adj} Wheelbarrow",
    ],
    "Food & Grocery": [
        "{adj} Organic Honey", "{adj} Coffee Beans", "{adj} Trail Mix",
        "{adj} Olive Oil", "{adj} Dark Chocolate Bar", "{adj} Green Tea",
        "{adj} Protein Bar Pack", "{adj} Hot Sauce Set", "{adj} Granola",
        "{adj} Dried Fruit Mix", "{adj} Pasta Sauce", "{adj} Almond Butter",
    ],
}

ADJECTIVES = [
    "Premium", "Pro", "Ultra", "Classic", "Deluxe", "Essential", "Advanced",
    "Compact", "Elite", "Max", "Eco", "Smart", "Turbo", "Zen", "Vivid",
    "Bold", "Swift", "Prime", "Flex", "Pure", "Nova", "Apex", "Neo",
]

# Category-specific product image URLs
CATEGORY_IMAGES = {
    "Electronics": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop",  # headphones
        "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=400&h=400&fit=crop",  # phone
        "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&h=400&fit=crop",  # laptop
        "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=400&h=400&fit=crop",  # accessories
        "https://plus.unsplash.com/premium_photo-1679865289918-b21aae5a9559?w=400&h=400&fit=crop",  # keyboard
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400&h=400&fit=crop",  # headphones
        "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&h=400&fit=crop",  # speaker
    ],
    "Clothing": [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",  # watch
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop",  # shoe
        "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=400&h=400&fit=crop",  # sneakers
        "https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=400&h=400&fit=crop",  # tshirt
        "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=400&fit=crop",  # jacket
        "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=400&fit=crop",  # clothes
    ],
    "Home & Kitchen": [
        "https://images.unsplash.com/photo-1556911220-bff31c812dba?w=400&h=400&fit=crop",  # kitchen
        "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400&h=400&fit=crop",  # pans
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=400&h=400&fit=crop",  # living room
        "https://images.unsplash.com/photo-1507473885765-e6ed057ab6fe?w=400&h=400&fit=crop",  # candle
        "https://images.unsplash.com/photo-1595428774223-ef52624120d2?w=400&h=400&fit=crop",  # mug
    ],
    "Books": [
        "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&h=400&fit=crop",  # book
        "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&h=400&fit=crop",  # books
        "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400&h=400&fit=crop",  # book cover
        "https://images.unsplash.com/photo-1524578271613-d550eacf6090?w=400&h=400&fit=crop",  # open book
        "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400&h=400&fit=crop",  # books stack
    ],
    "Sports & Outdoors": [
        "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=400&fit=crop",  # gym
        "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50a?w=400&h=400&fit=crop",  # weights
        "https://images.unsplash.com/photo-1599058917765-a780eda07a3e?w=400&h=400&fit=crop",  # yoga mat
        "https://images.unsplash.com/photo-1461896836934-bd45ba48fa7c?w=400&h=400&fit=crop",  # camping
        "https://images.unsplash.com/photo-1530143584546-02191bc84eb5?w=400&h=400&fit=crop",  # bike
    ],
    "Beauty & Health": [
        "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400&h=400&fit=crop",  # skincare bottles
        "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?w=400&h=400&fit=crop",  # cosmetics
        "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=400&h=400&fit=crop",  # serum
        "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=400&h=400&fit=crop",  # skincare
        "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=400&h=400&fit=crop",  # cream
    ],
    "Toys & Games": [
        "https://images.unsplash.com/photo-1558060370-d644479cb6f7?w=400&h=400&fit=crop",  # lego
        "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=400&h=400&fit=crop",  # board game
        "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=400&h=400&fit=crop",  # toys
        "https://images.unsplash.com/photo-1587654780291-39c9404d7dd0?w=400&h=400&fit=crop",  # rubik
        "https://images.unsplash.com/photo-1608889175123-8ee362201f81?w=400&h=400&fit=crop",  # rc car
    ],
    "Automotive": [
        "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=400&h=400&fit=crop",  # car parts
        "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400&h=400&fit=crop",  # car
        "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400&h=400&fit=crop",  # tools
        "https://images.unsplash.com/photo-1549317661-bd32c8ce0afa?w=400&h=400&fit=crop",  # engine
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&h=400&fit=crop",  # car front
    ],
    "Garden & Tools": [
        "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&h=400&fit=crop",  # garden
        "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=400&h=400&fit=crop",  # tools
        "https://images.unsplash.com/photo-1558171813-4c088753af8f?w=400&h=400&fit=crop",  # drill
        "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?w=400&h=400&fit=crop",  # plants
        "https://images.unsplash.com/photo-1592150621744-aca64f48394a?w=400&h=400&fit=crop",  # potted plant
    ],
    "Food & Grocery": [
        "https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=400&h=400&fit=crop",  # coffee
        "https://images.unsplash.com/photo-1553787499-6f9133860278?w=400&h=400&fit=crop",  # honey
        "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?w=400&h=400&fit=crop",  # chocolate
        "https://images.unsplash.com/photo-1474979266404-7eaacdc51815?w=400&h=400&fit=crop",  # fruit
        "https://images.unsplash.com/photo-1563822249548-9a72b6353cd1?w=400&h=400&fit=crop",  # olive oil
    ],
}


def generate_products(categories_map: dict[str, uuid.UUID]) -> list[dict]:
    products = []
    seen_names = set()
    sku_counter = 1000

    for category_name, category_id in categories_map.items():
        templates = PRODUCT_TEMPLATES.get(category_name, [])
        brands = BRANDS_BY_CATEGORY.get(category_name, ["Generic"])

        for template in templates:
            for _ in range(random.randint(3, 5)):
                adj = random.choice(ADJECTIVES)
                name = template.format(adj=adj)

                if name in seen_names:
                    adj = random.choice(ADJECTIVES) + " " + random.choice(["X", "2.0", "V2", "Plus", "Lite"])
                    name = template.format(adj=adj)
                if name in seen_names:
                    continue

                seen_names.add(name)
                sku_counter += 1

                price = round(random.uniform(5.99, 499.99), 2)
                if category_name == "Books":
                    price = round(random.uniform(9.99, 59.99), 2)
                elif category_name == "Food & Grocery":
                    price = round(random.uniform(3.99, 49.99), 2)

                products.append(
                    {
                        "name": name,
                        "slug": name.lower()
                        .replace(" ", "-")
                        .replace(".", "")
                        .replace(",", ""),
                        "description": fake.paragraph(nb_sentences=3),
                        "price": price,
                        "brand": random.choice(brands),
                        "sku": f"SKU-{sku_counter:05d}",
                        "rating": round(random.uniform(2.5, 5.0), 1),
                        "review_count": random.randint(0, 500),
                        "image_url": random.choice(CATEGORY_IMAGES.get(category_name, [])) if CATEGORY_IMAGES.get(category_name) else None,
                        "category_id": category_id,
                    }
                )

    return products


def generate_orders(products: list, count: int = 200) -> list[dict]:
    orders = []
    for i in range(count):
        order_date = datetime.now() - timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        num_items = random.randint(1, 5)
        selected_products = random.sample(
            products, min(num_items, len(products))
        )

        items = []
        total = 0.0
        for prod in selected_products:
            qty = random.randint(1, 3)
            items.append(
                {
                    "product_id": prod["id"],
                    "quantity": qty,
                    "unit_price": prod["price"],
                }
            )
            total += prod["price"] * qty

        orders.append(
            {
                "customer_email": fake.email(),
                "status": random.choice(
                    ["completed", "completed", "completed", "pending", "shipped"]
                ),
                "total_amount": round(total, 2),
                "items": items,
                "created_at": order_date,
            }
        )

    return orders


async def seed():
    print("🌱 Starting database seed...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

    async with async_session_factory() as session:
        # Create categories
        categories_map = {}
        for name, description in CATEGORIES:
            cat = Category(
                name=name,
                slug=name.lower().replace(" & ", "-").replace(" ", "-"),
                description=description,
            )
            session.add(cat)
            await session.flush()
            categories_map[name] = cat.id
        print(f"✅ Created {len(categories_map)} categories")

        # Create products
        product_dicts = generate_products(categories_map)
        product_records = []
        for p_data in product_dicts:
            product = Product(
                name=p_data["name"],
                slug=p_data["slug"],
                description=p_data["description"],
                price=p_data["price"],
                brand=p_data["brand"],
                sku=p_data["sku"],
                rating=p_data["rating"],
                review_count=p_data["review_count"],
                image_url=p_data["image_url"],
                category_id=p_data["category_id"],
            )
            session.add(product)
            await session.flush()
            p_data["id"] = product.id

            inv = Inventory(
                product_id=product.id,
                quantity=random.randint(0, 200),
                reserved=0,
                reorder_level=random.randint(5, 20),
            )
            session.add(inv)
            product_records.append(p_data)

        print(f"✅ Created {len(product_records)} products with inventory")

        # Create orders
        order_dicts = generate_orders(product_records, count=250)
        for o_data in order_dicts:
            order = Order(
                customer_email=o_data["customer_email"],
                status=o_data["status"],
                total_amount=o_data["total_amount"],
                created_at=o_data["created_at"],
            )
            session.add(order)
            await session.flush()

            for item_data in o_data["items"]:
                item = OrderItem(
                    order_id=order.id,
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                )
                session.add(item)

        await session.commit()
        print(f"✅ Created {len(order_dicts)} orders")

    print("🎉 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
