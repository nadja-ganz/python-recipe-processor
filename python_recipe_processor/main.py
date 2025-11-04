import json
import sys
from typing import List

from python_recipe_processor.parsers.anthropic import parse_recipe_with_vision_anthropic
from python_recipe_processor.parsers.ollama import parse_recipe_with_vision_ollama
from python_recipe_processor.parsers.openapi import parse_recipe_with_vision_openai

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
    print("  pip: poetry add pdfplumber pillow")
    sys.exit(1)


def main():
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
        elif provider == "ollama":
            recipe_data = parse_recipe_with_vision_ollama(images)
        else:
            recipe_data = parse_recipe_with_vision_openai(images)

        # Convert to JSON string
        json_string = json.dumps(recipe_data, indent=2, ensure_ascii=False)

        return json_string

    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_pdf_recipe> [--anthropic]")
        print("\nExamples:")
        print("  python main.py recipe.pdf")
        print("  python main.py recipe.pdf --anthropic")
        print("\nRequired environment variables:")
        print("  OPENAI_API_KEY      (for OpenAI GPT-4 Vision)")
        print("  ANTHROPIC_API_KEY   (for Claude Vision)")
        print("\nMake sure you have a .env file with your API key:")
        print("  OPENAI_API_KEY=sk-...")
        sys.exit(1)

    pdf_file = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == "--anthropic":
        provider = "anthropic"
    elif len(sys.argv) > 2 and sys.argv[2] == "--ollama":
        provider = "ollama"
    else:
        provider = "openai"

    try:
        result = pdf_recipe_to_json(pdf_file, provider=provider)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
