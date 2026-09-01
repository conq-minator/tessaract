import os

def get_auth_headers() -> dict:
    """
    Returns the standard headers required for internal microservice communication.
    Uses the TESSERACT_INTERNAL_SECRET from the environment if present.
    """
    secret = os.getenv("TESSERACT_INTERNAL_SECRET", "dev_secret")
    return {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json"
    }
