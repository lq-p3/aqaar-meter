import pandas as pd
import numpy as np
import joblib
import json

def haversine_vectorized(lat1, lon1, lat2, lon2):
    R = 6371.0
    a = np.sin(np.radians(lat2 - lat1)/2)**2 + np.cos(np.radians(lat1))*np.cos(np.radians(lat2))*np.sin(np.radians(lon2 - lon1)/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

def is_positive(val):
    if pd.isna(val): return 0
    val_str = str(val).strip()
    return 1 if 'نعم' in val_str or 'مفروش' == val_str else 0

def test_model_manually():
    print("⏳ جاري تحميل العقل الذكي...")
    model_path = '/Users/alialqhtani/Desktop/AqaarMeter/backend/predictive_model.pkl'
    enc_path   = '/Users/alialqhtani/Desktop/AqaarMeter/backend/district_encodings.json'

    try:
        model = joblib.load(model_path)
        with open(enc_path, 'r', encoding='utf-8') as f:
            encodings = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ ملف مفقود: {e}")
        return

    print("✅ تم تحميل المودل بنجاح!\n")

    # --------------------------------------------------------
    # عدّل هذه البيانات يدوياً لتجربة أي عقار تريد تقييمه
    # --------------------------------------------------------
    property_data = {
        'area':              [450],
        'beds':              [5],
        'livings':           [2],
        'wc':                [4],
        'street_width':      [15],
        'age':               [3],
        'location.lat':      [18.2465],
        'location.lng':      [42.5117],
        'district':          ['حي المنسك'],
        'category_text':     ['فيلا'],
        'street_direction':  ['شمالي'],
        'furnished':         ['مفروش'],
        'ketchen':           ['نعم'],
        'water supply type': ['شبكة'],
        'elevator':          ['نعم'],
        'smart home':        ['نعم'],
        'has fiber':         ['نعم'],
    }

    df = pd.DataFrame(property_data)

    # ─── Feature Engineering (identical to train_model.py) ───
    ABHA_LAT, ABHA_LNG = 18.2164, 42.5053
    df['distance_to_center'] = haversine_vectorized(
        df['location.lat'], df['location.lng'], ABHA_LAT, ABHA_LNG)

    df['total_rooms'] = df['beds'] + df['livings'] + df['wc']

    total_living = (df['beds'] + df['livings']).replace(0, 1)
    df['space_per_room'] = df['area'] / total_living

    df['bathroom_ratio'] = df['wc'] / df['beds'].replace(0, 1)

    df['lux_elevator'] = df['elevator'].apply(is_positive)
    df['lux_smart']    = df['smart home'].apply(is_positive)
    df['lux_fiber']    = df['has fiber'].apply(is_positive)
    df['lux_furnish']  = df['furnished'].apply(is_positive)
    df['luxury_score'] = df['lux_elevator'] + df['lux_smart'] + df['lux_fiber'] + df['lux_furnish']

    # District Encoding (Target Encoding lookup)
    district_name = df['district'][0]
    district_map  = encodings['district_avg_sqm']
    global_avg    = encodings['global_avg_sqm']
    df['district_encoded'] = df['district'].map(district_map).fillna(global_avg)

    # ─── Match exact feature columns used in training ───
    num_features = ['area', 'beds', 'livings', 'wc', 'street_width', 'age',
                    'location.lat', 'location.lng', 'distance_to_center',
                    'space_per_room', 'bathroom_ratio', 'luxury_score',
                    'total_rooms', 'district_encoded']
    cat_features = ['category_text', 'street_direction', 'ketchen', 'water supply type']

    df_input = df[num_features + cat_features]

    # ─── Predict ───
    predicted_price = model.predict(df_input)[0]

    print("🏠 مواصفات العقار:")
    print(f"  - النوع:      {property_data['category_text'][0]}")
    print(f"  - الحي:       {district_name}  (متوسط متره {int(district_map.get(district_name, global_avg)):,} ريال/م²)")
    print(f"  - المساحة:    {property_data['area'][0]} م²")
    print(f"  - الرفاهية:   {int(df['luxury_score'][0])}/4")
    print(f"  - م²/غرفة:    {int(df['space_per_room'][0])}")
    print("-" * 35)
    print(f"\n🎯 السعر المتوقع: {int(predicted_price):,} ريال سعودي\n")

if __name__ == '__main__':
    test_model_manually()
