import json
import sys
from typing import List, Dict, Any

from python_recipe_processor.parsers.imageBase64Converter import image_to_base64

try:
    from PIL import Image
except ImportError:
    print("Please install required packages:")
    sys.exit(1)


def parse_recipe_with_vision_ollama(images: List[Image.Image]) -> Dict[str, Any]:
    """
    Use Ollama's vision model to parse recipe from images.
    """
    try:
        import requests
        import os

        # Get Ollama base URL (default to localhost)
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        model = os.getenv('OLLAMA_MODEL', 'llama3.2-vision')

        # Prepare image content
        image_data = []
        for img in images:
            base64_image = image_to_base64(img)
            image_data.append(base64_image)

        # Create the prompt
        prompt = """Analyze this recipe image and extract all information into a JSON object with these fields:
- title: recipe name
- servings: number of servings
- prep_time: preparation time
- cook_time: cooking time
- total_time: total time (if specified)
- ingredients: array of ingredient objects with 'amount', 'unit', 'item', and optional 'notes'
- instructions: array of step-by-step instructions
- tags: array of relevant tags
- cuisine: type of cuisine (if identifiable)
- difficulty: difficulty level (if specified)

Return ONLY valid JSON, no other text."""

        # Make request to Ollama API
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "images": image_data,
                "stream": False,
                "format": "json"
            },
            timeout=600
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        result = response.json()
        json_text = result.get('response', '')

        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            json_text = json_text.split("```json")[1].split("```")[0].strip()

        return json.loads(json_text)

    except ImportError:
        raise Exception("requests library not installed. Install with: poetry add requests")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Could not connect to Ollama at {ollama_url}. Make sure Ollama is running.")
    except Exception as e:
        raise Exception(f"Vision parsing failed: {e}")
