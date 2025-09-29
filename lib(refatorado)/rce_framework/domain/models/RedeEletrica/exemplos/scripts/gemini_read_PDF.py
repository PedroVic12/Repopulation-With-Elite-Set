from google import genai
from google.genai import types
import pathlib 

client = genai.Client(api_key="YOUR_API_KEY")

filepath = pathlib.Path(__file__).parent / "test.pdf"

prompt_user = "Resuma este documento .md"

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(
            data = filepath.read_bytes(),
            mime_type="application/pdf"
        ),
        prompt_user
    ]
)

print(response.text)
