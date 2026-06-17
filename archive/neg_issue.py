import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file first, then initialize OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_negative_issue(title: str, content: str, max_tokens: int = 300, temperature: float = 0.6) -> str:
    """
    Generate upto 3 word negative issue from a review's title and content using OpenAI Chat API.

    Returns lowercase words or raises exception on API errors.
    """
    prompt = f"""Based on the following product review, identify the main negative issue in upto 3 words only.

Title: {title}
Content: {content}

Respond with ONLY the negative issue words, nothing else. Examples: Contaminated creamer, Flavorless overpriced product, Poor delivery handling, Overpriced mediocre product, Bad taste texture, Tooth sensitivity issues, False advertising claims, Product dissatisfaction."""

    response = client.responses.create(
        model="gpt-5.2",
        input=prompt,
        max_output_tokens=max_tokens,
        temperature=temperature,
    )

    # Extract text from response
    text = response.output_text.strip()
    if not text:
        return "unknown"
    # Take first word and lowercase it
    return text.split()[0].lower()
