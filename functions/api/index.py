from mangum import Mangum
from main import app

# Entry point for Netlify Functions
handler = Mangum(app)
