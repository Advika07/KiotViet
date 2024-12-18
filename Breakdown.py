import pandas as pd
import openai
import traceback

# Set OpenAI API Key
openai.api_key = private 

# Utility to log debug messages
def log_debug(message):
    print(f"[DEBUG]: {message}")

# Call GPT model to extract brand, product name, and description
def breakdown_product_details(text):
    try:
        log_debug(f"Processing: {text}")
        prompt = f"""Analyze the following product text and extract:
1. Brand (if mentioned, e.g., Dove, Huggies, Marlboro, etc.)
2. Product name (main product without brand or description)
3. Description (attributes like color, size, quantity, etc.)
Provide your response in JSON format with keys: brand, product_name, description.

Example:
Input: 'Dove Moisturizing Cream 450 ml - Red'
Output: {{
    "brand": "Dove",
    "product_name": "Moisturizing Cream",
    "description": "450 ml, Red"
}}

Now process the following text:
'{text}'"""

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()
        return eval(result)  # Safely convert JSON-like response to Python dictionary
    except Exception as e:
        log_debug(f"Failed to process '{text}': {e}")
        log_debug(traceback.format_exc())
        return {"brand": "", "product_name": text, "description": ""}  # Fallback response

# Process the Excel file and breakdown product details
def process_translated_file(input_file, output_file):
    try:
        # Load the Excel file
        data = pd.read_excel(input_file)

        # Initialize new columns for brand, product_name, and description
        data["extracted_brand"] = ""
        data["extracted_product_name"] = ""
        data["extracted_description"] = ""

        # Process each translated entry
        for index, row in data.iterrows():
            translated_text = row["translated"]
            breakdown = breakdown_product_details(translated_text)
            data.at[index, "extracted_brand"] = breakdown.get("brand", "")
            data.at[index, "extracted_product_name"] = breakdown.get("product_name", "")
            data.at[index, "extracted_description"] = breakdown.get("description", "")

        # Save to a new Excel file
        data.to_excel(output_file, index=False)
        log_debug(f"Processed data saved to: {output_file}")
    except Exception as e:
        log_debug(f"Error processing file: {e}")
        log_debug(traceback.format_exc())

# Main function to execute
def main():
    input_file = "cleaned_product_results.xlsx"
    output_file = "refined_product_results.xlsx"

    process_translated_file(input_file, output_file)

if __name__ == "__main__":
    main()
