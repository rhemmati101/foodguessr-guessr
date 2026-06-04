'''
data processing functions!
'''
import inflect
import unicodedata
import re
#################################### optional string processing

def comma_to_left(string, index) -> bool:
    '''
    Checks if there is a comma to the left of the index in the string, ignoring spaces.
    '''
    while index >= 1:
        if string[index - 1] == ',':
            return True
        if string[index - 1] == ' ':
            index -= 1
        else:
            return False
    return False

def strip_optional_tags(string):
    '''
    Strips "optional" tags from the string, and strips descriptions of ingredients in parentheses
    '''
    # First, remove simple substrings
    string = string.replace("[", "").replace("]", "")
    string = string.replace("optionally", "").replace("optional", "")
    string = string.replace("such as", "")
    string = string.replace(":", "")
    string = string.replace("{", "").replace("}", "")
    
    # Handle parentheses: find all "("s
    # If no comma to the left, delete everything from "(" to ")"
    # If comma to the left, just delete "(" and ")"
    result = []
    i = 0
    while i < len(string):
        if string[i] == '(':
            # Find the closing parenthesis
            close_idx = string.find(')', i)
            if close_idx == -1:
                # No closing paren found, keep the rest
                result.append(string[i:])
                break
            
            # Check if there's a comma to the left
            if comma_to_left(string, i):
                # Just delete "(" and ")", keep the content
                result.append(string[i+1:close_idx])
                i = close_idx + 1
            else:
                # Delete all text from "(" to ")" inclusive
                i = close_idx + 1
        else:
            result.append(string[i])
            i += 1
    
    return ''.join(result)

def strip_optional_ingredients(string): # MAY NOT WORK
    '''
    Strips "optional" ingredients from the string, as well as descriptions of ingredients in parentheses.
    '''
    # First pass: Look for "(" or "[" from left to right
    # If one is found and there's a comma to the left, delete everything from that comma to the end
    i = 0
    while i < len(string):
        if string[i] in '([':
            if comma_to_left(string, i):
                # Delete everything from the comma to the end of the string
                j = i - 1
                while j >= 0:
                    if string[j] == ',':
                        string = string[:j]
                        break
                    j -= 1
                break
        i += 1
    
    # Second pass: Search for "(optional)" and "[optional]" repeatedly
    while True:
        idx1 = string.find("(optional)")
        idx2 = string.find("[optional]")
        
        if idx1 == -1 and idx2 == -1:
            break
        
        # Find which one comes first
        idx = -1
        pattern_len = 0
        if idx1 != -1 and idx2 != -1:
            idx = min(idx1, idx2)
            pattern_len = 10 if idx == idx1 else 10
        elif idx1 != -1:
            idx = idx1
            pattern_len = 10
        else:
            idx = idx2
            pattern_len = 10
        
        # Find the first comma to the left, delete from comma to end of pattern
        j = idx - 1
        comma_idx = -1
        while j >= 0:
            if string[j] == ',':
                comma_idx = j
                break
            j -= 1
        
        if comma_idx != -1:
            # Delete from comma to the end of the pattern
            string = string[:comma_idx] + string[idx + pattern_len:]
        else:
            # No comma found, just remove the pattern
            string = string[:idx] + string[idx + pattern_len:]
    
    # Final pass: Strip everything in parentheses, including the parentheses themselves
    # get rid of the descriptions of ingredients in parentheses, e.g. "kalabasa (squash)"
    result = []
    i = 0
    while i < len(string):
        if string[i] == '(':
            # Find the closing parenthesis
            close_idx = string.find(')', i)
            if close_idx == -1:
                # No closing paren found, keep the rest
                result.append(string[i:])
                break
            # Skip everything from "(" to ")" inclusive
            i = close_idx + 1
        else:
            result.append(string[i])
            i += 1
    
    return ''.join(result).strip()


def clean_ingredient_list(string):
    '''
    Strips whitespace and empty ingredients so that we can easily split by comma to get a clean list
    Also splits on "and", "or" and "/" and removes periods
    '''
    normalized = re.sub(r"\bor\b", ",", string, flags=re.IGNORECASE)
    normalized = re.sub(r"\band\b", ",", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"/", ",", normalized, flags=re.IGNORECASE)
    filtered = [ingredient.lower().replace(".", "").replace("(", "").replace(")", "").strip() for ingredient in normalized.split(",") if ingredient.strip()]
    return [ingredient for ingredient in filtered if ingredient.strip()] # get rid of empty string ings

def countries_to_array(string):
    '''
    Converts a string of countries separated by semicolons into an array of countries, stripping whitespace.
    '''
    return [country.strip() for country in string.split(";") if country.strip()]


################################################ collapse ingredient variants
p = inflect.engine()

# Normalize ingredient strings to collapse accent, apostrophe, and hyphen variants,
# while preserving spaces so canonical multi-word ingredients stay spaced.
def normalize_ingredient(ingredient):
    if not isinstance(ingredient, str):
        return ingredient
    ingredient = unicodedata.normalize('NFKD', ingredient)
    ingredient = ''.join(ch for ch in ingredient if not unicodedata.combining(ch))
    ingredient = ingredient.lower()
    ingredient = ingredient.replace('-', ' ')
    ingredient = re.sub(r"[’`´]", "'", ingredient)
    ingredient = ingredient.replace("'", '')
    ingredient = re.sub(r'\s+', ' ', ingredient).strip()
    return ingredient

# Singularize ingredients after normalization
def singularize_ingredient(ingredient):
    if not isinstance(ingredient, str):
        return ingredient
    
    ingredient = normalize_ingredient(ingredient)
    
    # Split the phrase into individual words
    words = ingredient.split()
    singular_words = []
    
    for word in words:
        # p.singular_noun returns False if the word is already singular
        singular = p.singular_noun(word) # type: ignore
        if singular:
            singular_words.append(singular)
        else:
            singular_words.append(word)
            
    # Rejoin the words into a single string
    return " ".join(singular_words)


################################# base ingredient detection
def most_common_one_word_ings_train(df, how_many=300):
    ingredients = df['ingredients'].explode()
    one_word_ingredients = ingredients[ingredients.str.split().str.len() == 1]
    return one_word_ingredients.value_counts().head(how_many).index.tolist()

#### version for test data
def most_common_one_word_ings(df, how_many=300):
    ingredients = df['ingredients'].explode()
    one_word_ingredients = ingredients[ingredients.str.split("_").str.len() == 1]
    return one_word_ingredients.value_counts().head(how_many).index.tolist()

# look for common one-word ingredients within ingredients list, eg. "garlic" in "minced garlic"
def get_base_ingredient_names(ingredient_list, most_common_ings):
    base_ingredients = []
    for ingredient in ingredient_list:
        for word in ingredient.split():
            if word in most_common_ings and word not in base_ingredients:
                base_ingredients.append(word)
    return base_ingredients

def add_base_ingredients(ingredient_list, most_common_ings):
    base_ingredients = get_base_ingredient_names(ingredient_list, most_common_ings)
    return list(set(ingredient_list) | set(base_ingredients))


################################ ingredient detection within parentheses
# look for the common ings inside the descriptions...
def get_base_ings_from_string(raw_string, most_common_ings):

    if not isinstance(raw_string, str):
        return []

    # normalize
    raw_string = normalize_ingredient(raw_string)

    # singularize EACH TOKEN separately
    tokens = []

    for token in re.findall(r"\b\w+\b", raw_string):

        singular = p.singular_noun(token)

        if singular:
            tokens.append(singular)
        else:
            tokens.append(token)

    normalized_string = " ".join(tokens)

    ings_found = []

    for ing in most_common_ings:

        normalized_ing = singularize_ingredient(
            ing.replace("_", " ")
        )

        pattern = r"\b" + re.escape(normalized_ing) + r"\b"

        if re.search(pattern, normalized_string):
            ings_found.append(ing)

    return list(set(ings_found))

if __name__ == "__main__":
    # optional tag strip tests
    print("Optional tag strip tests:")
    print(strip_optional_tags("salt, sugar, pepper (optional), garlic (optional), onion (optional)"))
    print(strip_optional_tags("salt, (optional: garlic, sugar, etc.)"))
    print(strip_optional_tags("salt, sugar, pepper [optional], garlic [optional], onion [optional]"))
    print(strip_optional_tags("salt, sugar, (optional) pepper, (optional) garlic, (optional) onion"))
    print(strip_optional_tags("salt, [green onions (optional)], [red onions (optional)]"))
    print(strip_optional_tags("salt, (optional: garlic), (optionally: sugar)"))
    print(strip_optional_tags("salt, (optional garlic), (optional sugar)"))
    print(strip_optional_tags("salt, kalabasa (squash)"))
    print(strip_optional_tags("salt, kalabasa (squash), (optional) garlic"))

    print("\n" + strip_optional_tags("salt, sugar, (optionally pepper), (optional garlic)"))
    print(strip_optional_tags("Cold noodles, sliced beef, beef broth, kimchi, boiled egg, cucumber, radish, (optional pickled mustard greens, optional apple slices, optional sesame seeds)."))
    print(strip_optional_tags("salt, (mushrooms optional), (peas optional),"))
    
    # optional ingredient strip tests
    print("\nOptional ingredient strip tests:")
    print(strip_optional_ingredients("salt, sugar, pepper (optional), garlic (optional), onion (optional)"))
    print(strip_optional_ingredients("salt, (optional: garlic, sugar, etc.)"))
    print(strip_optional_ingredients("salt, sugar, pepper [optional], garlic [optional], onion [optional]"))
    print(strip_optional_ingredients("salt, sugar, (optional) pepper, (optional) garlic, (optional) onion"))
    print(strip_optional_ingredients("salt, [green onions (optional)], [red onions (optional)]"))
    print(strip_optional_ingredients("salt, (optional: garlic), (optionally: sugar)"))
    print(strip_optional_ingredients("salt, (optional garlic), (optional sugar)"))
    print(strip_optional_ingredients("salt, kalabasa (squash)"))
    print(strip_optional_ingredients("salt, kalabasa (squash), (optional) garlic"))
    
    # clean ingredient list test
    print("\nClean ingredient list test:")
    print(clean_ingredient_list("salt   , meat or fish, and shrimp,     onion/shallot, etc"))

    # base ingredient detection tests
    print("\nBase ingredient detection tests:")
    print(get_base_ings_from_string("Apples, oranges,,(apples) bananaz kiwis, lemongrass", ["apple", "banana", "lemongrass"]))
