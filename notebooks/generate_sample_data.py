"""
Script to generate sample data for testing the application
"""
import pandas as pd
from pathlib import Path
import random
from datetime import datetime, timedelta

# Create data directory if it doesn't exist
data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(exist_ok=True)

# Sample data generators
companies = [
    "ThyssenKrupp Steel", "ArcelorMittal", "Voestalpine AG", "Salzgitter AG",
    "SSAB", "Outokumpu", "Tata Steel Europe", "Liberty Steel", "Dillinger Hütte",
    "Klöckner & Co", "Schmolz + Bickenbach", "Deutsche Edelstahlwerke",
    "Georgsmarienhütte", "Peiner Träger", "Stahlwerk Thüringen"
]

industries = ["Steel Production", "Metal Processing", "Automotive Steel", "Construction Steel", "Special Steel"]
regions = ["Germany", "Austria", "Sweden", "Finland", "Netherlands", "Belgium", "France", "UK"]
ratings = ["A", "A", "B", "B", "B", "C", "C", "C", "D", "E"]

# Generate CRM data
crm_data = []
for i, company in enumerate(companies):
    crm_data.append({
        "customer_id": f"CUST_{i+1:03d}",
        "name": company,
        "industry": random.choice(industries),
        "region": random.choice(regions),
        "address": f"{random.randint(1, 999)} Industrial Street, {random.choice(regions)}",
        "fte": random.randint(100, 5000),
        "revenue": f"€{random.randint(50, 500)}M",
        "rating": random.choice(ratings),
        "owner": "Independent" if random.random() > 0.3 else random.choice(companies),
        "management": f"CEO: {chr(65+random.randint(0,25))}. {chr(65+random.randint(0,25))}.",
        "buying_center": "Procurement Department",
        "focus": "High-quality steel production and processing",
        "esg_notes": "ISO 14001 certified" if random.random() > 0.5 else "ESG assessment pending",
        "agreements": "Frame agreement 2024-2026" if random.random() > 0.6 else "No active agreements",
        "projects_count": random.randint(0, 15),
        "last_purchase_months": random.randint(1, 48)
    })

crm_df = pd.DataFrame(crm_data)
crm_df.to_excel(data_dir / "crm_export.xlsx", index=False)
print(f"✓ Created CRM data: {len(crm_df)} customers")

# Generate BCG market data
bcg_data = []
for i, company in enumerate(companies):
    bcg_data.append({
        "customer_id": f"CUST_{i+1:03d}",
        "company_name": company,
        "market_share": f"{random.uniform(1, 15):.1f}%",
        "growth_rate": f"{random.uniform(-5, 10):.1f}%",
        "market_position": random.choice(["Leader", "Challenger", "Follower", "Niche"]),
        "competitive_intensity": random.choice(["High", "Medium", "Low"]),
        "technology_level": random.choice(["Advanced", "Standard", "Basic"]),
        "investment_capacity": random.choice(["High", "Medium", "Low"])
    })

bcg_df = pd.DataFrame(bcg_data)
bcg_df.to_excel(data_dir / "bcg_data.xlsx", index=False)
print(f"✓ Created BCG data: {len(bcg_df)} records")

# Generate installed base data
equipment_types = [
    "Blast Furnace", "Electric Arc Furnace", "Rolling Mill", "Continuous Casting",
    "Pickling Line", "Galvanizing Line", "Annealing Furnace", "Coating Line"
]

installed_base = []
for i, company in enumerate(companies):
    # Each company has 2-5 installations
    num_installations = random.randint(2, 5)
    
    for j in range(num_installations):
        installed_base.append({
            "customer_id": f"CUST_{i+1:03d}",
            "customer_name": company,
            "location": f"Plant {chr(65+j)}, {random.choice(regions)}",
            "equipment": random.choice(equipment_types),
            "equipment_id": f"EQ_{i+1:03d}_{j+1:02d}",
            "installation_year": random.randint(1995, 2023),
            "capacity": f"{random.randint(100, 2000)} kt/year",
            "products": random.choice(["Hot Rolled Coils", "Cold Rolled Sheets", "Galvanized Steel", "Special Alloys"]),
            "oem": random.choice(["SMS group", "Primetals", "Danieli", "Other"]),
            "last_maintenance": (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d")
        })

installed_df = pd.DataFrame(installed_base)
installed_df.to_excel(data_dir / "installed_base.xlsx", index=False)
print(f"✓ Created installed base data: {len(installed_df)} equipment records")

print("\n✅ Sample data generation complete!")
print(f"Files created in: {data_dir}")
print("\nYou can now:")
print("1. Run the application: streamlit run app/main.py")
print("2. Click 'Load Data' in the sidebar")
print("3. Start exploring!")
