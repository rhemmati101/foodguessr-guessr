import geopandas as gpd
import pycountry

url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_map_units.geojson"
world = gpd.read_file(url)

print(world[world['NAME'].str.contains("French Guiana")][['NAME', 'SOVEREIGNT']])

# Replace -99 or missing codes
def repair_map_data(df):
    code_col = 'ADM0_A3'
    name_col = 'NAME'
    
    for idx, row in df.iterrows():
        val = str(row[code_col])
        if len(val) != 3 or val == "-99":
            try:
                found = pycountry.countries.search_fuzzy(row[name_col])[0]
                df.at[idx, code_col] = found.alpha_3
            except:
                continue
    return df

world = repair_map_data(world)

FOODGUESSR_TO_MAP = {
    # Standard Countries
    "United Kingdom": "England", # map has parts of UK, treat as England for borders
    "United States": "United States of America",
    "Antigua and Barbuda": "Antigua",
    "Bahamas": "Bahamas",
    "Bosnia and Herzegovina": "Fed. of Bos. & Herz.",
    "Cape Verde": "Cabo Verde",
    "Central African Republic": "Central African Rep.",
    "Republic of the Congo": "Congo",
    "DR Congo": "Dem. Rep. Congo",
    "Dominican Republic": "Dominican Rep.",
    "Equatorial Guinea": "Eq. Guinea",
    "Eswatini": "eSwatini",
    "Ivory Coast": "Côte d'Ivoire",
    "Marshall Islands": "Marshall Is.",
    "Saint Vincent and the Grenadines": "St. Vin. and Gren.",
    "São Tomé and Príncipe": "São Tomé and Principe",
    "Vatican City": "Vatican",
    "Czech Republic": "Czechia",

    # Territories & Dependencies
    "British Virgin Islands": "British Virgin Is.",
    "Cayman Islands": "Cayman Is.",
    "Christmas Island": "Christmas I.",
    "Cocos (Keeling) Islands": "Cocos Is.",
    "Cook Islands": "Cook Is.",
    "Falkland Islands": "Falkland Is.",
    "Faroe Islands": "Faeroe Is.",
    "French Polynesia": "Fr. Polynesia",
    "French Southern and Antarctic Lands": "Fr. S. Antarctic Lands",
    "Macau": "Macao",
    "Saint Barthélemy": "St-Barthélemy",
    "Saint Martin": "St-Martin",
    "Saint Pierre and Miquelon": "St. Pierre and Miquelon",
    "Saint Helena, Ascension and Tristan da Cunha": "Saint Helena",
    "Turks and Caicos Islands": "Turks and Caicos Is.",
    "Virgin Islands": "U.S. Virgin Is.",
    "Wallis and Futuna": "Wallis and Futuna Is.",
    "Western Sahara": "W. Sahara",
    "Åland Islands": "Åland"
}

def get_map_name(foodguessr_name):
    # 1. Check if we have a manual override/mapping
    if foodguessr_name in FOODGUESSR_TO_MAP:
        return FOODGUESSR_TO_MAP[foodguessr_name]
    
    # 2. Otherwise, assume the name is already correct
    return foodguessr_name

def check_border(name_a, name_b):
    # Convert both names to map-friendly names
    map_a = get_map_name(name_a)
    map_b = get_map_name(name_b)
    
    print(map_a, map_b)

    # Now look them up in your 'world' dataframe
    geom_a = world[world['NAME'] == map_a].geometry.iloc[0]
    geom_b = world[world['NAME'] == map_b].geometry.iloc[0]

    print("geom_a:", geom_a)
    print("geom_b:", geom_b)

    return geom_a.touches(geom_b)

if __name__ == "__main__":
    test_cases = [
        # Standard Land Borders
        ("Spain", "Portugal"),
        ("United States", "Mexico"),
        ("United States", "Canada"),
        ("Brazil", "Argentina"),
        ("Norway", "Sweden"),
        ("Thailand", "Malaysia"),
        ("Egypt", "Israel"),
        ("Russia", "China"),
        ("India", "Pakistan"),
        ("Turkey", "Greece"),
        ("Germany", "France"),
        ("France", "Spain"),
        ("Iraq", "Iran"),
        ("Vietnam", "China"),
        ("South Korea", "North Korea"),
        
        # Enclaves (Land Border)
        ("South Africa", "Lesotho"),
        ("Italy", "Vatican City"),
        ("Italy", "San Marino"),
        
        # Mapping Overrides (Mismatched Names)
        ("United States", "Canada"),      # Map: United States of America
        ("Tanzania", "Kenya"),           # Map: United Republic of Tanzania
        ("Czech Republic", "Germany"),   # Map: Czechia
        ("DR Congo", "Angola"),          # Map: Democratic Republic of the Congo
        ("Congo", "Gabon"),              # Map: Republic of the Congo
        ("Eswatini", "South Africa"),    # Map: eSwatini
        ("Cape Verde", "Senegal"),       # Maritime - Map: Cabo Verde
        ("Timor-Leste", "Indonesia"),    # Map: East Timor
        
        # Maritime/Close Proximity (Should pass with 0.2-0.5 buffer)
        ("United Kingdom", "France"),
        ("Japan", "South Korea"),
        ("India", "Sri Lanka"),
        ("Australia", "Papua New Guinea"),
        ("Morocco", "Spain"),
        ("Singapore", "Malaysia"),
        ("Finland", "Estonia"),
        ("Denmark", "Sweden"),
        ("Qatar", "Bahrain"),
        ("Taiwan", "China"),
        
        # Non-Bordering (Should be False)
        ("Australia", "New Zealand"),
        ("Iceland", "Norway"),
        ("United States", "Russia"),
        ("Madagascar", "South Africa"),
        ("Brazil", "Chile"),
        ("Portugal", "France"),
        ("Italy", "Greece"),
        ("Philippines", "Vietnam"),
        
        # Overseas Territories/Specific Mappings
        ("Greenland", "Canada"),
        ("Hong Kong", "China"),
        ("Macau", "China"),
        ("French Guiana", "Brazil"),
        ("French Guiana", "Suriname"),
        ("Puerto Rico", "Dominican Republic"),
        ("Guernsey", "France"),
        ("Gibraltar", "Spain")
    ]

    print(f"{'TEST CASE':<30} | {'RESULT'}")
    print("-" * 50)

    #for c1, c2 in test_cases:
    #    try:
    #        result = check_border(c1, c2)
    #        print(f"{c1 + ' & ' + c2:<30} | {result}")
    #    except Exception as e:
    #        print(f"{c1 + ' & ' + c2:<30} | ERROR: {e}")


    check_border("United Kingdom", "France")
