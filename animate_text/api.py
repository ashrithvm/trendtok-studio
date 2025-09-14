from diffusers import DiffusionPipeline
from utils import get_accel_device
import os


# Model configuration
STABLE_DIFFUSION_MODEL = "runwayml/stable-diffusion-v1-5"


# Define a function to generate an image from a given description
def generate_image(desc: str, output_path: str) -> None:
    """
    Generates an image from a given description.

    Args:
        desc (str): Description of the image to be generated
        output_path (str): Path where the generated image will be saved

    Returns:
        None

    Examples:
        >>> generate_image("a photo of spiderman eating broccoli", "output.png")
    """
    # Load the Stable Diffusion v1.5 model
    pipe = DiffusionPipeline.from_pretrained(STABLE_DIFFUSION_MODEL)

    # Get the acceleration device to use for the pipeline
    device = get_accel_device()
    pipe = pipe.to(device)

    # Recommended if your computer has less than 64 GB of RAM
    pipe.enable_attention_slicing()

    # Set the prompt and generate the image
    prompt = desc
    image = pipe(prompt).images[0]

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the generated image to the specified file
    image.save(output_path)  # Save the generated image to a file
