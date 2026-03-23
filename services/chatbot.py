import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def ask_about_zip(question, zip_data):
    """
    Takes a user question and a dictionary of ZIP code data,
    asks Claude to answer in plain English.
    """

    # Build a summary of the ZIP data to send to Claude
    context = f"""
    Here is the data for ZIP code {zip_data.get('ZIP', 'unknown')}:

    - Median Income: ${zip_data.get('INCOME', 'N/A'):,.0f}
    - Population: {zip_data.get('Population', 'N/A'):,.0f}
    - Median Age: {zip_data.get('MEDIAN_AGE', 'N/A')}
    - Bachelors Degree holders: {zip_data.get('BACHELORS_DEGREE', 'N/A'):,.0f}
    - Fire Stations: {int(zip_data.get('FIRE_STATION_COUNT', 0))}
    - Police Stations: {int(zip_data.get('POLICE_STATION_COUNT', 0))}
    - Public Schools: {int(zip_data.get('PUBLIC_SCHOOL_COUNT', 0))}
    - Private Schools: {int(zip_data.get('PRIVATE_SCHOOL_COUNT', 0))}
    - Parks: {int(zip_data.get('PARK_COUNT', 0))}
    - Hotels/Motels: {int(zip_data.get('HOTEL_COUNT', 0))}
    - Facility Score: {zip_data.get('FACILITY_SCORE_WEIGHTED', 'N/A')}
    - Overall Rating: {zip_data.get('WEIGHTED_RATING', 'N/A')}
    """

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a helpful assistant for a ZIP code explorer app called "Know Your Zip".
                
A user is asking about a ZIP code. Use ONLY the data provided below to answer.
Be conversational, friendly, and concise. Max 3-4 sentences.

{context}

User question: {question}"""
            }
        ]
    )

    return message.content[0].text


if __name__ == "__main__":
    # Test the chatbot
    test_data = {
        "ZIP": "33186",
        "INCOME": 87899,
        "Population": 67597,
        "MEDIAN_AGE": 38.5,
        "BACHELORS_DEGREE": 12000,
        "FIRE_STATION_COUNT": 2,
        "POLICE_STATION_COUNT": 1,
        "PUBLIC_SCHOOL_COUNT": 8,
        "PRIVATE_SCHOOL_COUNT": 25,
        "PARK_COUNT": 5,
        "HOTEL_COUNT": 3,
        "FACILITY_SCORE_WEIGHTED": 103,
        "WEIGHTED_RATING": "High"
    }

    answer = ask_about_zip("Is this a good ZIP code for families?", test_data)
    print(answer)