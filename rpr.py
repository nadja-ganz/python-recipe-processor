import json
import sys
import base64
from io import BytesIO
from typing import Dict, Any, List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()  # This loads .env file
except ImportError:
    print("Warning: python-dotenv not installed. Make sure environment variables are set manually.", file=sys.stderr)

try:
    import pdfplumber
    from PIL import Image
except ImportError:
    print("Please install required packages:")
    print("  nix: add pdfplumber and pillow to flake.nix")
    print("  pip: pip install pdfplumber pillow")
    sys.exit(1)


def pdf_to_images(pdf_path: str) -> List[Image.Image]:
    """Convert PDF pages to PIL Images."""
    images = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Convert page to image
                img = page.to_image(resolution=150)
                images.append(img.original)
    except Exception as e:
        raise Exception(f"Error converting PDF to images: {str(e)}")
    return images


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')


def parse_recipe_with_vision_openai(images: List[Image.Image]) -> Dict[str, Any]:
    """
    Use OpenAI's vision model (GPT-4 Vision) to parse recipe from images.
    """
    try:
        from openai import OpenAI
        import os

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("OPENAI_API_KEY not found. Please set it in .env file or as an environment variable.")

        client = OpenAI(api_key=api_key)

        # Prepare image messages
        image_content = []
        for idx, img in enumerate(images):
            base64_image = image_to_base64(img)
            image_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"  # Use "high" for better detail recognition
                }
            })

        # Create the prompt
        prompt = {
            "type": "text",
            "text": """Analyze this recipe image and extract all information into a JSON object with these fields:
- title: recipe name
- servings: number of servings
- prep_time: preparation time
- cook_time: cooking time
- total_time: total time (if specified)
- ingredients: array of ingredient objects with 'amount', 'unit', 'item', and optional 'notes'
- instructions: array of step-by-step instructions (numbered if possible)
- tags: array of relevant tags (e.g., "vegetarian", "dessert", "quick", "easy")
- cuisine: type of cuisine (if identifiable)
- difficulty: difficulty level (if specified)

Return ONLY valid JSON, no other text."""
        }

        # Combine prompt and images
        messages_content = [prompt] + image_content

        response = client.chat.completions.create(
            model="gpt-4o",  # gpt-4o or gpt-4-turbo support vision
            messages=[
                {
                    "role": "user",
                    "content": messages_content
                }
            ],
            max_tokens=2000,
            temperature=0.3
        )

        json_text = response.choices[0].message.content
        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            json_text = json_text.split("```json")[1].split("```")[0].strip()

        return json.loads(json_text)

    except ImportError:
        raise Exception("OpenAI library not installed. Install with: pip install openai")
    except Exception as e:
        raise Exception(f"Vision parsing failed: {e}")


def parse_recipe_with_vision_anthropic(images: List[Image.Image]) -> Dict[str, Any]:
    """
    Use Anthropic's Claude Vision to parse recipe from images.
    """
    try:
        from anthropic import Anthropic
        import os

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY not found. Please set it in .env file or as an environment variable.")

        client = Anthropic(api_key=api_key)

        # Prepare image content
        image_content = []
        for img in images:
            base64_image = image_to_base64(img)
            image_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_image
                }
            })

        # Add text prompt
        content = image_content + [{
            "type": "text",
            "text": """Analyze this recipe image and extract all information into a JSON object with these fields:
- title: recipe name
- servings: number of servings
- prep_time: preparation time
- cook_time: cooking time
- total_time: total time (if specified)
- ingredients: array of ingredient objects with 'amount', 'unit', 'item', and optional 'notes'
- instructions: array of step-by-step instructions
- tags: array of relevant tags
- cuisine: type of cuisine (if identifiable)

Return ONLY valid JSON, no other text."""
        }]

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )

        json_text = response.content[0].text
        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            json_text = json_text.split("```json")[1].split("```")[0].strip()

        return json.loads(json_text)

    except ImportError:
        raise Exception("Anthropic library not installed. Install with: pip install anthropic")
    except Exception as e:
        raise Exception(f"Vision parsing failed: {e}")


def pdf_recipe_to_json(pdf_path: str, provider: str = "openai") -> str:
    """
    Main function: Convert PDF recipe to JSON string using vision AI.

    Args:
        pdf_path: Path to the PDF file
        provider: AI provider to use ("openai" or "anthropic")

    Returns:
        JSON string containing the parsed recipe
    """
    # Convert PDF to images
    print(f"Converting PDF to images...", file=sys.stderr)
    images = pdf_to_images(pdf_path)

    if not images:
        raise ValueError("No pages could be extracted from the PDF")

    print(f"Extracted {len(images)} page(s)", file=sys.stderr)

    # Parse with vision AI
    print(f"Parsing recipe with {provider} vision model...", file=sys.stderr)
    if provider == "anthropic":
        recipe_data = parse_recipe_with_vision_anthropic(images)
    else:
        recipe_data = parse_recipe_with_vision_openai(images)

    # Convert to JSON string
    json_string = json.dumps(recipe_data, indent=2, ensure_ascii=False)

    return json_string


# Example usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rpr.py <path_to_pdf_recipe> [--anthropic]")
        print("\nExamples:")
        print("  python rpr.py recipe.pdf")
        print("  python rpr.py recipe.pdf --anthropic")
        print("\nRequired environment variables:")
        print("  OPENAI_API_KEY      (for OpenAI GPT-4 Vision)")
        print("  ANTHROPIC_API_KEY   (for Claude Vision)")
        print("\nMake sure you have a .env file with your API key:")
        print("  OPENAI_API_KEY=sk-...")
        sys.exit(1)

    pdf_file = sys.argv[1]
    provider = "anthropic" if "--anthropic" in sys.argv else "openai"

    try:
        result = pdf_recipe_to_json(pdf_file, provider=provider)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)