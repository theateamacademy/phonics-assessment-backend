from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def get_response_from_ai(systemMessage, humanMessage):
    # Ensure you are using the latest OpenAI API client without unexpected arguments
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        # Use the correct method to create a chat completion
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Ensure this is the correct model you are using
            messages=[
                {"role": "system", "content": systemMessage},
                {"role": "user", "content": humanMessage}
            ]
        )
        content = completion.choices[0].message.content
        if content is None or not str(content).strip():
            return ""
        return content
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error with OpenAI request: {e}")
        return ""

