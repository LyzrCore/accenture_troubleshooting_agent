# import requests

# from settings import settings

# ocr_url = settings.OCR_ENDPOINT


# def detect_corrosion(file_path):
#     url = ocr_url + "detect_corrosion"
#     params = {"mode": "detection"}
#     headers = {"accept": "*/*"}

#     # Open the file in binary mode
#     try:
#         with open(file_path, "rb") as file:
#             files = {"file": (file_path, file, "image/jpeg")}

#             response = requests.post(url, headers=headers, params=params, files=files)

#             # Check if the response status code is 200 (OK)
#             if response.status_code == 200:
#                 # Save the response content as an image file
#                 output_file_path = "detected_corrosion.png"
#                 with open(output_file_path, "wb") as output_file:
#                     output_file.write(response.content)
#                 print(f"Image saved as {output_file_path}")
#                 return output_file_path
#             else:
#                 print(f"Request failed with status code: {response.status_code}")
#                 print(f"Response text: {response.text}")
#                 return None
#     except FileNotFoundError:
#         print(f"Error: The file '{file_path}' was not found.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
import os

import requests

from settings import settings

# Get the OCR URL from environment variables or settings
ocr_url = settings.OCR_ENDPOINT


def detect_corrosion(file_path):
    """Detects corrosion in an image by sending it to the OCR service."""

    # Ensure OCR URL is correctly formatted
    if not ocr_url.endswith("/"):
        ocr_url += "/"

    url = ocr_url + "detect_corrosion"
    params = {"mode": "detection"}
    headers = {"accept": "*/*"}

    if not os.path.isfile(file_path):
        return f"Error: File '{file_path}' not found."

    try:
        # Open the image file in binary mode
        with open(file_path, "rb") as file:
            files = {"file": (file_path, file, "image/jpeg")}

            response = requests.post(url, headers=headers, params=params, files=files)
            response.raise_for_status()  # Raise exception for HTTP errors

            # Save the response content as an image file
            output_dir = os.getenv("OUTPUT_DIR", ".")  # Default to current directory
            output_file_path = os.path.join(output_dir, "detected_corrosion.png")

            with open(output_file_path, "wb") as output_file:
                output_file.write(response.content)

            print(f"Image saved as {output_file_path}")
            return output_file_path

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None
