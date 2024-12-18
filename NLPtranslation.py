!pip install langdetect
!pip install --upgrade openai
!pip install underthesea
import pandas as pd
import requests
from underthesea import ner, word_tokenize
import openai
from concurrent.futures import ThreadPoolExecutor
import traceback
from langdetect import detect

# Set OpenAI API Key
openai.api_key = private
# Caching brand validation to reduce API calls
validated_brands_cache = {}

# Utility to log debug messages
def log_debug(message):
    print(f"[DEBUG]: {message}")

# Translate Vietnamese text using OpenAI API
# Updated Translate Vietnamese text using OpenAI API

def translate_to_english(text):
    try:
        log_debug(f"Translating: {text}")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a translator. Translate the following text to English:"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log_debug(f"Translation failed for '{text}': {e}")
        log_debug(traceback.format_exc()) 
        return text  # Return original text on failure


# Extract brands and clean descriptions
def extract_brand_and_description(text):
    try:
        log_debug(f"NER processing for: {text}")
        tokens = ner(text)
        brand_candidates = set()
        description_parts = []
        for word, pos, chunk, entity in tokens:
            if entity == "B-LOC" or entity == "B-PER":  # Treat locations and persons as potential brands
                brand_candidates.add(word)
            else:
                description_parts.append(word)
        return brand_candidates, " ".join(description_parts)
    except Exception as e:
        log_debug(f"NER error: {e}")
        return set(), text

# Validate brand names using caching and OpenCorporates API
def validate_brand(brand_name):
    if brand_name in validated_brands_cache:
        return validated_brands_cache[brand_name]

    url = "https://api.opencorporates.com/v0.4/companies/search"
    params = {"q": brand_name, "api_token": "your_opencorporates_api_key"}
    try:
        log_debug(f"Validating brand: {brand_name}")
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            companies = response.json().get("results", {}).get("companies", [])
            if companies:
                validated_name = companies[0]["company"]["name"]
                validated_brands_cache[brand_name] = validated_name
                return validated_name
        validated_brands_cache[brand_name] = None
        return None
    except Exception as e:
        log_debug(f"Validation failed for '{brand_name}': {e}")
        return None

# Process group items row by row
def process_group_items(row):
    group_id = row['group_id']
    items = row['group_items'].split(",")
    processed_results = []

    for item in items:
        try:
            stripped_item = item.strip()
            detected_lang = detect(stripped_item)
            if detected_lang == "vi":
                translated_item = translate_to_english(stripped_item)
            else:
                translated_item = stripped_item

            brands, description = extract_brand_and_description(translated_item)
            validated_brands = [validate_brand(b) for b in brands if validate_brand(b)]

            processed_results.append({
                "group_id": group_id,
                "original": item.strip(),
                "translated": translated_item,
                "brand": ", ".join(validated_brands),
                "description": description,
                "language": detected_lang
            })
        except Exception as e:
            log_debug(f"Error processing '{item}': {e}")
    return processed_results

# Read file and process
def main():
    # Upload file
    from google.colab import files
    uploaded = files.upload()
    file_path = list(uploaded.keys())[0]

    # Load data
    data = pd.read_excel(file_path)
    log_debug("Limiting dataset to first 250 rows for performance.")
    data = data.head(250)

    # Process rows in parallel
    detailed_rows = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_group_items, row) for _, row in data.iterrows()]
        for future in futures:
            try:
                detailed_rows.extend(future.result())
            except Exception as e:
                log_debug(f"Future processing failed: {e}")

    # Save processed results
    detailed_df = pd.DataFrame(detailed_rows)
    output_file = "cleaned_product_results.xlsx"
    detailed_df.to_excel(output_file, index=False)
    log_debug(f"Processing complete. Results saved to {output_file}.")

if __name__ == "__main__":
    main()
