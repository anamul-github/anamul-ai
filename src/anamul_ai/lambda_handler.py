"""Entry point for AWS Lambda: Mangum turns Lambda's events into normal requests for my FastAPI app."""

from mangum import Mangum

from anamul_ai.api import app

handler = Mangum(app, lifespan="off")
