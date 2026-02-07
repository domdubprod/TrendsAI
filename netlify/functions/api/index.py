from mangum import Mangum
from main import app

# Entry point for Netlify Functions
# This handler wraps the FastAPI app for AWS Lambda / Netlify
handler = Mangum(app)
