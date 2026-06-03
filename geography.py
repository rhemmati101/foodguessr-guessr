import geopandas as gpd
import pycountry
from geopy.distance import geodesic
import numpy as np
import math
from shapely.ops import unary_union
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
    "South Sudan" : "S. Sudan",
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
    "Saint Kitts and Nevis": "St. Kitts and Nevis",
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

def get_foodguessr_name(map_name):
    for fg_name, map_list in FOODGUESSR_TO_MAP.items():
        # Handle both list and string values from your dict
        if isinstance(map_list, list):
            if map_name in map_list:
                return fg_name
        elif map_name == map_list:
            return fg_name
    return map_name

########################################################################## BORDERS

def check_border(name_a, name_b):
    # Convert both names to map-friendly names
    maps_a = get_map_namelist(name_a)
    maps_b = get_map_namelist(name_b)

    # Now look them up in your 'world' dataframe
    geoms_a = [world[world['NAME'] == map].geometry.iloc[0] for map in maps_a]
    geoms_b = [world[world['NAME'] == map].geometry.iloc[0] for map in maps_b]

    return any(geom_a.touches(geom_b) for geom_a in geoms_a for geom_b in geoms_b)

# returns Foodguessr version of names
def bordering_countries(name):
    map_name = get_map_namelist(name)
    country_geoms = [world[world['NAME'] == map].geometry.iloc[0] for map in map_name]
    
    neighbors = []
    for idx, row in world.iterrows():
        if row['NAME'] != map_name and any(geom.touches(row.geometry) for geom in country_geoms):
            neighbors.append(row['NAME'])
    
    # map back to Foodguessr names
    neighbors = list(set([get_foodguessr_name(n) for n in neighbors]))
    neighbors = [n for n in neighbors if n in COUNTRIES_AND_TERRITORIES]
    neighbors = [n for n in neighbors if n != name]

    return neighbors

########################################################################## DISTANCE

def get_country_distance(name_a, name_b):
    maps_a = get_map_namelist(name_a)
    maps_b = get_map_namelist(name_b)

    res_a = [world[world['NAME'] == map_a] for map_a in maps_a]
    res_b = [world[world['NAME'] == map_b] for map_b in maps_b]

    if any(res.empty for res in res_a) or any(res.empty for res in res_b):
        raise ValueError(f"Could not find map data for '{name_a}' or '{name_b}'")

    dists_km = []

    for ra in res_a:
        for rb in res_b:
            geom_a = ra.geometry.iloc[0]
            geom_b = rb.geometry.iloc[0]

            point_a = geom_a.representative_point()
            point_b = geom_b.representative_point()

            dist_km = geodesic(
                (point_a.y, point_a.x),
                (point_b.y, point_b.x)
            ).km

            dists_km.append(dist_km)

    return round(min(dists_km))

def get_guess_distance(guess_name, correct_names):
    guess_maps = get_map_namelist(guess_name)
    correct_maps = []
    for name in correct_names:
        correct_maps.extend(get_map_namelist(name))

    dists = []
    for gm in guess_maps:
        for cm in correct_maps:
            dist = get_country_distance(gm, cm)
            if dist is not None:
                dists.append(dist)

    return round(min(dists)) if dists else None

TEMP_THRESHOLDS = {"Very Hot": 500, "Hot": 1250, "Warm": 3500, "Cool": 5000, "Cold": 8000}

def temperature_label_from_distance(dist):
    if dist < TEMP_THRESHOLDS["Very Hot"]:
        return "Very Hot"
    elif dist < TEMP_THRESHOLDS["Hot"]:
        return "Hot"
    elif dist < TEMP_THRESHOLDS["Warm"]:
        return "Warm"
    elif dist < TEMP_THRESHOLDS["Cool"]:
        return "Cool"
    elif dist < TEMP_THRESHOLDS["Cold"]:
        return "Cold"
    else:
        return "Ice Cold"

def temperature_label(name_a, name_b):
    dist = get_country_distance(name_a, name_b)
    if dist is None:
        raise ValueError(f"Could not calculate distance between '{name_a}' and '{name_b}'")
    return temperature_label_from_distance(dist)
    
# mildly conservative thresholds for filtering out predictions
def temp_to_thresholds(label):
    if label == "Very Hot":
        return [0, np.average([TEMP_THRESHOLDS["Very Hot"], TEMP_THRESHOLDS["Hot"]])]
    elif label == "Hot":
        return [np.average([0, TEMP_THRESHOLDS["Very Hot"]]), np.average([TEMP_THRESHOLDS["Hot"], TEMP_THRESHOLDS["Warm"]])]
    elif label == "Warm":
        return [np.average([TEMP_THRESHOLDS["Very Hot"], TEMP_THRESHOLDS["Hot"]]), np.average([TEMP_THRESHOLDS["Warm"], TEMP_THRESHOLDS["Cool"]])]
    elif label == "Cool":
        return [np.average([TEMP_THRESHOLDS["Hot"], TEMP_THRESHOLDS["Warm"]]), np.average([TEMP_THRESHOLDS["Cool"], TEMP_THRESHOLDS["Cold"]])]
    elif label == "Cold":
        return [np.average([TEMP_THRESHOLDS["Warm"], TEMP_THRESHOLDS["Cool"]]), TEMP_THRESHOLDS["Cold"] + 2000]
    elif label == "Ice Cold":
        return [np.average([TEMP_THRESHOLDS["Cool"], TEMP_THRESHOLDS["Cold"]]), np.inf]
    else:
        raise ValueError(f"Invalid temperature label: {label}")

def get_guess_temperature(guess_name, correct_names):
    dist = get_guess_distance(guess_name, correct_names)
    if dist is None:
        return "Unknown"
    return temperature_label_from_distance(dist)

########################################################################## DIRECTION

def calculate_initial_bearing(lat1, lon1, lat2, lon2):
    """Calculates the initial compass bearing between two points."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lon = lon2 - lon1
    
    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(d_lon))
    
    # Convert back to degrees and normalize to 0-360
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def get_representative_coordinate(country_name):
    """Fetches the representative point (lat, lon) for a given foodguessr name."""
    map_names = get_map_namelist(country_name)
    
    # Extract all geometries matching the map names
    geoms = world[world['NAME'].isin(map_names)].geometry
    
    if geoms.empty:
        raise ValueError(f"Geometry not found for: {country_name}")
    
    # If the country is split into multiple map units (e.g., UK), fuse them together
    if len(geoms) > 1:
        merged_geom = unary_union(geoms)
        rep_point = merged_geom.representative_point()
    else:
        rep_point = geoms.iloc[0].representative_point()
        
    # Shapely Point coordinates are accessed via x (Longitude) and y (Latitude)
    return rep_point.y, rep_point.x

def get_guess_direction(guess, correct_countries):
    """
    Accepts a guess and a list of correct countries. 
    Returns the bearing (in degrees) from the guess to the closest correct country.
    """
    if not correct_countries:
        raise ValueError("The list of correct countries is missing or empty.")
        
    # Find the closest country by comparing distances from the guess
    target_country = min(correct_countries, key=lambda c: get_country_distance(guess, c))
    
    # Get coordinates
    guess_lat, guess_lon = get_representative_coordinate(guess)
    target_lat, target_lon = get_representative_coordinate(target_country)
    
    # Calculate and return bearing
    bearing = calculate_initial_bearing(guess_lat, guess_lon, target_lat, target_lon)
    return bearing


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

    #print(f"{'TEST CASE':<30} | {'RESULT'}")
    #print("-" * 50)

    #for c1, c2 in test_cases:
    #    try:
    #        result = check_border(c1, c2)
    #        dist = get_country_distance(c1, c2)
    #        print(f"{c1 + ' & ' + c2:<30} | {result} ({dist} km)")
    #    except Exception as e:
    #        print(f"{c1 + ' & ' + c2:<30} | ERROR: {e}")

    #for country in ["Germany", "Russia", "India", "Indonesia", "Iran", "Palestine", "Iraq", "Somalia", "Serbia", "Bosnia and Herzegovina"]:
    #    print(f"Bordering countries for '{country}':", bordering_countries(country))


    direction_test_cases = [
        # Standard Long-Distance
        {"guess": "Egypt", "targets": ["South Africa"], "desc": "Egypt -> South Africa"},
        {"guess": "India", "targets": ["Mexico"], "desc": "India -> Mexico"},
        {"guess": "Madagascar", "targets": ["Canada"], "desc": "Madagascar -> Canada"},
        {"guess": "Chile", "targets": ["Norway"], "desc": "Chile -> Norway"},
        
        # Custom Dictionary / Merging Units
        {"guess": "United Kingdom", "targets": ["Japan"], "desc": "UK (4 units) -> Japan"},
        {"guess": "South Korea", "targets": ["Germany"], "desc": "South Korea (DMZ merge) -> Germany"},
        {"guess": "United States", "targets": ["Australia"], "desc": "USA (String override) -> Australia"},
        {"guess": "Serbia", "targets": ["Argentina"], "desc": "Serbia (Vojvodina) -> Argentina"},
        {"guess": "Israel", "targets": ["Brazil"], "desc": "Israel -> Brazil"},
        
        # Territories & Islands
        {"guess": "French Polynesia", "targets": ["France"], "desc": "French Polynesia -> France"},
        {"guess": "Saint Vincent and the Grenadines", "targets": ["Bahamas"], "desc": "St. Vincent -> Bahamas"},
        {"guess": "Falkland Islands", "targets": ["Spain"], "desc": "Falkland Is. -> Spain"},
        
        # Math & Geographic Edge Cases
        {"guess": "Russia", "targets": ["Brazil"], "desc": "Russia -> Brazil (Massive landmasses)"},
        {"guess": "Ecuador", "targets": ["Kenya"], "desc": "Ecuador -> Kenya (Equatorial)"},
        {"guess": "New Zealand", "targets": ["Iceland"], "desc": "New Zealand -> Iceland (Antipodes)"},

        {"guess": "Brazil", "targets": ["Japan", "China", "Venezuela"], "desc": "Brazil -> Japan (Crossing the dateline)"},
    ]

    print(f"{'TEST CASE':<40} | {'BEARING':<10} | {'DISTANCE':<12} | {'COORDS'}")
    print("-" * 95)

    for case in direction_test_cases:
        try:
            # 1. Get coordinates
            g_lat, g_lon = get_representative_coordinate(case['guess'])
            t_lat, t_lon = get_representative_coordinate(case['targets'][0])
            
            # 2. Calculate Bearing 
            bearing = get_guess_direction(case['guess'], case['targets'])
            
            # 3. Calculate Distance for context
            dist = geodesic((g_lat, g_lon), (t_lat, t_lon)).km
            
            # 4. Format Output
            print(f"{case['desc']:<40} | {bearing:>7.2f}° | {dist:>8.1f} km | G({g_lat:>5.1f}, {g_lon:>5.1f}) -> T({t_lat:>5.1f}, {t_lon:>5.1f})")
            
        except Exception as e:
            print(f"{case['desc']:<40} | ERROR: {str(e)}")