import json
import sys
from typing import List, Dict, Any

from python_recipe_processor.parsers.imageBase64Converter import image_to_base64

try:
    from PIL import Image
except ImportError:
    print("Please install required packages:")
    sys.exit(1)


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
        raise Exception("OpenAI library not installed. Install with: poetry add openai")
    except Exception as e:
        raise Exception(f"Vision parsing failed: {e}")
