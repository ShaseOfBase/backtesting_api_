from fastapi import FastAPI
from typing import Optional
from dataclasses import dataclass
from fastapi.testclient import TestClient

app = FastAPI()

import routes
