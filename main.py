def extract_data(text):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""
Extract airline invoice data and return JSON with:
invoice_number, invoice_date, pnr, ticket_number,
buyer_gst, buyer_name, seller_gst, seller_name,
basic_fare, other_charges, cgst, sgst, igst, total_amount
{text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        import json
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {"error": str(e)}
