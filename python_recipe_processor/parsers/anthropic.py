import json
import sys
from typing import List, Dict, Any

from python_recipe_processor.parsers.imageBase64Converter import image_to_base64

try:
    from PIL import Image
except ImportError:
    print("Please install required packages:")
    print("  pip: poetry add pdfplumber pillow")
    sys.exit(1)


def parse_recipe_with_vision_anthropic(images: List[Image.Image]) -> Dict[str, Any]:
    """
    Use Anthropic's Claude Vision to parse recipe from images.
    """
    try:
        from anthropic import Anthropic
        import os

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise Exception(
                "ANTHROPIC_API_KEY not found. Please set it in .env file or as an environment variable.")

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
            model="claude-sonnet-4-5-20250929",
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
        raise Exception("Anthropic library not installed. Install with: poetry add anthropic")
    except Exception as e:
        raise Exception(f"Vision parsing failed: {e}")
