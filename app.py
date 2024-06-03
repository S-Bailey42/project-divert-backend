from fastapi import FastAPI
import ItemEndpoints
import WorkSiteEndpoints
import UserEndpoints
import AuthEndpoints
import RequestEndpoints
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

Image_location = "./images"
app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = RequestEndpoints.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(WorkSiteEndpoints.Router)
app.include_router(AuthEndpoints.Router)
app.include_router(UserEndpoints.Router)
app.include_router(RequestEndpoints.Router)
app.include_router(ItemEndpoints.Router)