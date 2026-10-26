import os
import sqlite3
import pandas as pd
import numpy as np

def import_data():
    db_path = "/Users/alialqhtani/Desktop/AqaarMeter/AqaarMeterAPI/appraisals.db"
    excel_path = "/Users/alialqhtani/Desktop/AqaarMeter/Real state for Aseer 2.xlsx"
    csv_path = "/Users/alialqhtani/Desktop/AqaarMeter/backend/aqar_live_data.csv"

    print("Checking database directory...")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    print("1. Loading original Excel dataset...")
    try:
        df_old = pd.read_excel(excel_path)
        df_old = df_old[df_old['category_text'].str.contains('بيع', na=False)]
        print(f"   Loaded {len(df_old)} rows from Excel.")
    except Exception as e:
        print(f"   Error reading Excel: {e}")
        df_old = pd.DataFrame()

    print("2. Loading Live Aqar scraped dataset...")
    try:
        df_new = pd.read_csv(csv_path)
        df_new = df_new.rename(columns={
            'lift': 'elevator',
            'fl': 'floor number',
            'lat': 'location.lat',
            'lng': 'location.lng',
        })
        df_new['category_text'] = 'بيع'
        df_new['district'] = df_new['district_id'].astype(str)
        print(f"   Loaded {len(df_new)} rows from CSV.")
    except Exception as e:
        print(f"   Error reading CSV: {e}")
        df_new = pd.DataFrame()

    # Align columns
    common_cols = [
        'price', 'area', 'beds', 'livings', 'wc', 'age', 'street_width',
        'location.lat', 'location.lng', 'category_text', 'district'
    ]

    for col in common_cols:
        if col not in df_old.columns and not df_old.empty:
            df_old[col] = np.nan
        if col not in df_new.columns and not df_new.empty:
            df_new[col] = np.nan

    dfs = []
    if not df_old.empty:
        dfs.append(df_old[common_cols])
    if not df_new.empty:
        dfs.append(df_new[common_cols])

    if not dfs:
        print("❌ No data loaded. Aborting.")
        return

    df_combined = pd.concat(dfs, ignore_index=True)
    print(f"Combined dataset: {len(df_combined)} rows.")

    # Drop rows without critical values
    df_clean = df_combined.dropna(subset=['price', 'area', 'location.lat', 'location.lng'])
    print(f"After dropping missing critical values: {len(df_clean)} rows.")

    # Convert coordinates and prices to proper numeric types
    df_clean['price'] = pd.to_numeric(df_clean['price'], errors='coerce')
    df_clean['area'] = pd.to_numeric(df_clean['area'], errors='coerce')
    df_clean['beds'] = pd.to_numeric(df_clean['beds'], errors='coerce').fillna(0).astype(int)
    df_clean['livings'] = pd.to_numeric(df_clean['livings'], errors='coerce').fillna(0).astype(int)
    df_clean['wc'] = pd.to_numeric(df_clean['wc'], errors='coerce').fillna(0).astype(int)
    df_clean['age'] = pd.to_numeric(df_clean['age'], errors='coerce').fillna(0)
    df_clean['street_width'] = pd.to_numeric(df_clean['street_width'], errors='coerce').fillna(0)
    df_clean['location.lat'] = pd.to_numeric(df_clean['location.lat'], errors='coerce')
    df_clean['location.lng'] = pd.to_numeric(df_clean['location.lng'], errors='coerce')

    df_clean = df_clean.dropna(subset=['price', 'area', 'location.lat', 'location.lng'])
    print(f"After cleaning numeric fields: {len(df_clean)} rows.")

    # Connect to SQLite and write
    print("Connecting to SQLite database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if not exists (matching EF Core schema names)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MarketTransactions (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Price REAL NOT NULL,
        Area REAL NOT NULL,
        Beds INTEGER NOT NULL,
        Livings INTEGER NOT NULL,
        Wc INTEGER NOT NULL,
        Age REAL NOT NULL,
        StreetWidth REAL NOT NULL,
        Latitude REAL NOT NULL,
        Longitude REAL NOT NULL,
        District TEXT NOT NULL,
        PropertyType TEXT NOT NULL
    )
    """)

    # Create geo index
    cursor.execute("CREATE INDEX IF NOT EXISTS IX_MarketTransactions_Lat_Lng ON MarketTransactions (Latitude, Longitude)")
    cursor.execute("CREATE INDEX IF NOT EXISTS IX_MarketTransactions_District ON MarketTransactions (District)")

    # Clear existing rows to prevent duplication
    cursor.execute("DELETE FROM MarketTransactions")
    
    # Prepare batch insert
    records = []
    for _, row in df_clean.iterrows():
        # Map category_text to standard readable property types
        cat = str(row['category_text'])
        prop_type = "Land" # Default
        if "فيلا" in cat:
            prop_type = "Villa"
        elif "شقة" in cat:
            prop_type = "Apartment"
        elif "دور" in cat:
            prop_type = "Duplex"
        elif "بيع" in cat:
            prop_type = "Villa" # default sold property to Villa if unknown but contains 'sale' and has rooms
            if row['beds'] == 0:
                prop_type = "Land"

        records.append((
            float(row['price']),
            float(row['area']),
            int(row['beds']),
            int(row['livings']),
            int(row['wc']),
            float(row['age']),
            float(row['street_width']),
            float(row['location.lat']),
            float(row['location.lng']),
            str(row['district']),
            prop_type
        ))

    print(f"Inserting {len(records)} records into MarketTransactions...")
    cursor.executemany("""
    INSERT INTO MarketTransactions (Price, Area, Beds, Livings, Wc, Age, StreetWidth, Latitude, Longitude, District, PropertyType)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)

    conn.commit()
    
    # Verify count
    cursor.execute("SELECT COUNT(*) FROM MarketTransactions")
    count = cursor.fetchone()[0]
    print(f"✅ Success! {count} transactions imported successfully into SQLite database.")
    
    conn.close()

if __name__ == "__main__":
    import_data()
