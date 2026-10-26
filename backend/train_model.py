import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import json

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    a = np.sin(np.radians(lat2 - lat1)/2)**2 + np.cos(np.radians(lat1))*np.cos(np.radians(lat2))*np.sin(np.radians(lon2 - lon1)/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

def train_merged():
    # === 1. Load BOTH datasets ===
    print("Loading original Excel dataset...")
    df_old = pd.read_excel('/Users/alialqhtani/Desktop/AqaarMeter/Real state for Aseer 2.xlsx')
    df_old = df_old[df_old['category_text'].str.contains('بيع', na=False)]
    print(f"  Original: {len(df_old)} rows")

    print("Loading Live Aqar.fm scraped dataset...")
    df_new = pd.read_csv('/Users/alialqhtani/Desktop/AqaarMeter/backend/aqar_live_data.csv')
    print(f"  Scraped:  {len(df_new)} rows")

    # === 2. Harmonize columns ===
    df_new = df_new.rename(columns={
        'lift': 'elevator',
        'fl': 'floor number',
        'lat': 'location.lat',
        'lng': 'location.lng',
    })
    df_new['category_text'] = 'بيع'
    df_new['district'] = df_new['district_id'].astype(str)
    df_new['smart home'] = 0
    df_new['has fiber'] = 0
    df_new['water supply type'] = 'Unknown'

    # === 3. Select common features and merge ===
    common_cols = ['price', 'area', 'beds', 'livings', 'wc', 'age', 'street_width',
                   'street_direction', 'location.lat', 'location.lng',
                   'ketchen', 'furnished', 'elevator', 'ac',
                   'category_text', 'district', 'floor number',
                   'car_entrance', 'basement', 'backyard', 'pool']

    for col in common_cols:
        if col not in df_old.columns:
            df_old[col] = np.nan
        if col not in df_new.columns:
            df_new[col] = np.nan

    df_combined = pd.concat([df_old[common_cols], df_new[common_cols]], ignore_index=True)
    print(f"\n✅ Combined dataset: {len(df_combined)} rows")

    # === 4. Clean ===
    df = df_combined.dropna(subset=['price', 'area', 'beds', 'wc'])
    df = df[(df['price'] >= 250000) & (df['price'] <= 2500000)]
    df = df[(df['area'] >= 90) & (df['area'] <= 1000)]
    print(f"After filtering: {len(df)} rows")

    for col in ['beds', 'livings', 'wc', 'age', 'street_width', 'floor number',
                'ketchen', 'furnished', 'elevator', 'ac', 'car_entrance', 'basement', 'backyard', 'pool']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # === 5. Feature Engineering ===
    ABHA_LAT, ABHA_LNG = 18.2164, 42.5053
    df['distance_to_center'] = haversine(df['location.lat'], df['location.lng'], ABHA_LAT, ABHA_LNG)
    df['total_rooms'] = df['beds'] + df['livings'] + df['wc']
    df['space_per_room'] = df['area'] / (df['beds'] + df['livings']).replace(0, 1)
    df['bathroom_ratio'] = df['wc'] / df['beds'].replace(0, 1)
    df['luxury_score'] = df['elevator'] + df['ac'] + df['pool'] + df['furnished']
    df['infra_score'] = df['car_entrance'] + df['basement'] + df['backyard']

    num_features = ['area', 'beds', 'livings', 'wc', 'street_width', 'age',
                    'location.lat', 'location.lng', 'distance_to_center',
                    'space_per_room', 'bathroom_ratio', 'luxury_score', 'total_rooms',
                    'floor number', 'infra_score', 'ketchen']
    cat_features = ['district', 'category_text']

    for c in num_features:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(df[c].median())
    for c in cat_features:
        df[c] = df[c].fillna('Unknown').astype(str)

    X = df[num_features + cat_features]
    y = df['price']

    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), num_features),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_features)
    ])
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', XGBRegressor(n_estimators=700, learning_rate=0.04, max_depth=8,
                              colsample_bytree=0.8, subsample=0.8, random_state=42, n_jobs=-1))
    ])

    # === 6. K-Fold Cross Validation ===
    print("\n🧠 5-Fold Cross Validation on MERGED dataset...")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    r2s, maes = [], []
    for i, (tr, te) in enumerate(kf.split(X), 1):
        pipeline.fit(X.iloc[tr], y.iloc[tr])
        p = pipeline.predict(X.iloc[te])
        r2s.append(r2_score(y.iloc[te], p))
        maes.append(mean_absolute_error(y.iloc[te], p))
        print(f"Fold {i} - R2: {r2s[-1]*100:.2f}% | MAE: SAR {int(maes[-1]):,}")

    print(f"\n{'='*50}")
    print(f"🏆 MERGED DATA K-FOLD RESULTS (Excel + Aqar.fm Live):")
    print(f"{'='*50}")
    print(f"Average R2:  {np.mean(r2s)*100:.2f}%")
    print(f"Average MAE: SAR {int(np.mean(maes)):,}")
    print(f"{'='*50}")

    # === 7. Train final on ALL data and save ===
    print("\nTraining final production model on 100% merged data...")
    pipeline.fit(X, y)
    joblib.dump(pipeline, '/Users/alialqhtani/Desktop/AqaarMeter/backend/predictive_model.pkl')
    with open('/Users/alialqhtani/Desktop/AqaarMeter/backend/features.json', 'w', encoding='utf-8') as f:
        json.dump({"num_features": num_features, "cat_features": cat_features}, f, ensure_ascii=False)
    print("✅ Model saved to backend/predictive_model.pkl")

if __name__ == "__main__":
    train_merged()
