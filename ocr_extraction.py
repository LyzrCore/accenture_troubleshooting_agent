import requests

from settings import settings

ocr_url = settings.OCR_ENDPOINT


def extract_text(file_path):
    url = ocr_url + "extract_text/"
    params = {"out": "text"}
    headers = {"accept": "application/json"}

    # Open the file in binary mode
    try:
        with open(file_path, "rb") as file:
            files = {"file": (file_path, file, "image/png")}

            response = requests.post(url, headers=headers, params=params, files=files)

            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                # Parse the JSON response
                detected_text = response.json()

                # Extract the "text" keys and concatenate them with a space
                text_concatenated = " ".join(
                    item["text"] for item in detected_text["detected_text"]
                )

                # Return the concatenated string
                return text_concatenated
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response text: {response.text}")
                return None
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
