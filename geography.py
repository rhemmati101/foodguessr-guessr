import geopandas as gpd
import pycountry
from scrape import COUNTRIES_AND_TERRITORIES

url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_map_units.geojson"
world = gpd.read_file(url)

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
    "United Kingdom": ["England", "Scotland", "Wales", "N. Ireland"],
    "Palestine": ["West Bank", "Gaza"],
    "South Korea": ["South Korea", "Korean DMZ (south)"],
    "North Korea": ["North Korea", "Korean DMZ (north)"],
    "Syria": ["Syria", "UNDOF Zone"],
    "Iraq" : ["Iraq", "Iraqi Kurdistan"],
    "Somalia" : ["Somalia", "Somaliland", "Puntland"],
    "Belgium" : ["Walloon", "Brussels", "Flemish"],
    "Serbia" : ["Serbia", "Vojvodina"],
    "Bosnia and Herzegovina": ["Rep. Srpska", "Fed. of Bos. & Herz.", "Brcko District"],
    "Georgia": ["Georgia", "Adjara"],
    "United States": "United States of America",
    "Antigua and Barbuda": "Antigua",
    "Bahamas": "Bahamas",
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

# return a list of names (or single name)
def get_map_namelist(foodguessr_name):
    # 1. Check if we have a manual override/mapping
    if foodguessr_name in FOODGUESSR_TO_MAP:
        if isinstance(FOODGUESSR_TO_MAP[foodguessr_name], list):
            return FOODGUESSR_TO_MAP[foodguessr_name]
        else:
            return [FOODGUESSR_TO_MAP[foodguessr_name]]

    # 2. Otherwise, assume the name is already correct
    return [foodguessr_name]

def check_border(name_a, name_b):
    # Convert both names to map-friendly names
    maps_a = get_map_namelist(name_a)
    maps_b = get_map_namelist(name_b)

    # Now look them up in your 'world' dataframe
    geoms_a = [world[world['NAME'] == map].geometry.iloc[0] for map in maps_a]
    geoms_b = [world[world['NAME'] == map].geometry.iloc[0] for map in maps_b]

    return any(geom_a.touches(geom_b) for geom_a in geoms_a for geom_b in geoms_b)

# returns Foodguessr version of names
####### TODO
def bordering_countries(name):
    map_name = get_map_namelist(name)
    country_geom = world[world['NAME'] == map_name].geometry.iloc[0]
    
    neighbors = []
    for idx, row in world.iterrows():
        if row['NAME'] != map_name and country_geom.touches(row.geometry):
            neighbors.append(row['NAME'])
    
    # map back to Foodguessr names
    reverse_map = {v: k for k, v in FOODGUESSR_TO_MAP.items()}
    neighbors = [reverse_map.get(n, n) for n in neighbors]
    neighbors = [n for n in neighbors if n in COUNTRIES_AND_TERRITORIES]

    return neighbors

def get_country_distance(name_a, name_b):
    map_a = get_map_name(name_a)
    map_b = get_map_name(name_b)
    
    res_a = world[world['NAME'] == map_a]
    res_b = world[world['NAME'] == map_b]
    
    if res_a.empty or res_b.empty:
        return None

    geom_a = res_a.geometry.iloc[0]
    geom_b = res_b.geometry.iloc[0]

    # Calculate distance in degrees
    dist_degrees = geom_a.distance(geom_b)
    
    # Simple approximation: 1 degree ≈ 111 km
    dist_km = dist_degrees * 111
    
    return round(dist_km)

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
        ("Gibraltar", "Spain"),

        # Countries with weirder borders...should be True when accounting for all territories
        ('South Korea', 'North Korea'),
        ('Syria', 'Israel'),
        ('Palestine', 'Egypt'),
        ('United Kingdom', 'Ireland'),
        ('Iraq', 'Turkey'),
        ('Somalia', 'Djibouti'),
        ('Serbia', 'Hungary'),
        ('Bosnia and Herzegovina', 'Montenegro'),
    ]

    print(f"{'TEST CASE':<30} | {'RESULT'}")
    print("-" * 50)

    for c1, c2 in test_cases:
        try:
            result = check_border(c1, c2)
            #dist = get_country_distance(c1, c2)
            print(f"{c1 + ' & ' + c2:<30} | {result} (km)")
        except Exception as e:
            print(f"{c1 + ' & ' + c2:<30} | ERROR: {e}")

    #for country in ["Germany", "Russia", "India", "Indonesia", "Iran"]:
    #    print(f"Bordering countries for '{country}':", bordering_countries(country))

    
