import contextlib
import os
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# See https://github.com/aio-libs-abandoned/aioredis-py?tab=readme-ov-file#-aioredis-is-now-in-redis-py-420rc1-  # noqa: E501
from redis import asyncio as aioredis
import logging
from dotenv import load_dotenv
import sentry_sdk


load_dotenv(verbose=True)

SENTRY_SDK_DSN = os.getenv("SENTRY_SDK_DSN")

sentry_sdk.init(
    dsn=SENTRY_SDK_DSN,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

PYTHON_LOG_LEVEL = os.getenv("PYTHON_LOG_LEVEL", "DEBUG")

log = logging.getLogger(__name__)
log.setLevel(PYTHON_LOG_LEVEL)
log.addHandler(logging.StreamHandler())


REDIS_HOSTNAME = os.getenv("REDIS_HOSTNAME")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


@contextlib.asynccontextmanager
async def lifespan(app):
    """
    Verify on startup
    - all settings present
    - connections are valid / work
    See also https://www.starlette.io/lifespan/
    """
    assert PYTHON_LOG_LEVEL is not None
    assert REDIS_HOSTNAME is not None
    assert REDIS_PORT is not None
    assert REDIS_PASSWORD is not None

    redis = await aioredis.from_url(
        f"redis://{REDIS_HOSTNAME}", password=REDIS_PASSWORD
    )
    redis_ping_success = await redis.ping()
    log.debug(f"pinging redis host '{REDIS_HOSTNAME}' to verify connection")
    assert redis_ping_success is True
    yield


async def redis_set_value(key, value):
    """Connect to redis and store key value"""
    redis = await aioredis.from_url(
        f"redis://{REDIS_HOSTNAME}", password=REDIS_PASSWORD
    )
    await redis.set(key, value)


async def index(request):
    data = await request.json()
    stripe_connect_account_id = data["stripe_connect_account_id"]
    site_url = data["site_url"]
    log.debug(f"{data}")

    await redis_set_value(stripe_connect_account_id, site_url)

    return JSONResponse(data)


routes = [Route("/", index, methods=["POST"])]

if PYTHON_LOG_LEVEL.lower() == "debug":
    debug = True
else:
    debuf = False

app = Starlette(debug=debug, routes=routes, lifespan=lifespan)
