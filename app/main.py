import sys
import base64
import binascii
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator, model_validator
import uvicorn
from starlette.concurrency import run_in_threadpool

from app.agent import (
    MAX_IMAGE_BYTES,
    get_game_help_response,
    get_local_model_status,
    supported_games,
)

app = FastAPI(title="Forge Game Help")
FRONTEND_PATH = Path(__file__).parent / "static" / "index.html"


class GameHelpRequest(BaseModel):
    game: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=1, max_length=2000)
    hint_level: int = Field(ge=1, le=10)
    screenshot_base64: str | None = None
    screenshot_mime_type: str | None = None

    @field_validator("game", "question")
    @classmethod
    def strip_and_validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("screenshot_base64")
    @classmethod
    def validate_screenshot_size_and_encoding(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) > ((MAX_IMAGE_BYTES + 2) // 3) * 4:
            raise ValueError("Screenshot must be 8 MB or smaller.")
        try:
            image_data = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Screenshot data must be valid base64.") from exc
        if not image_data or len(image_data) > MAX_IMAGE_BYTES:
            raise ValueError("Screenshot must be between 1 byte and 8 MB.")
        return value

    @model_validator(mode="after")
    def validate_screenshot_fields(self):
        supported_types = {"image/jpeg", "image/png", "image/webp"}
        if self.screenshot_base64 is None and self.screenshot_mime_type is None:
            return self
        if self.screenshot_base64 is None or self.screenshot_mime_type is None:
            raise ValueError("Screenshot data and MIME type must be provided together.")
        if self.screenshot_mime_type not in supported_types:
            raise ValueError("Screenshot must be a JPEG, PNG, or WebP image.")
        return self


class Source(BaseModel):
    title: str
    url: str


class GameHelpResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/")
async def root():
    return FileResponse(FRONTEND_PATH)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "local_model": get_local_model_status(),
        "supported_games": supported_games(),
    }


@app.post("/api/chat", response_model=GameHelpResponse)
async def chat_endpoint(request: GameHelpRequest):
    result = await run_in_threadpool(
        get_game_help_response,
        game=request.game.strip(),
        question=request.question.strip(),
        hint_level=request.hint_level,
        screenshot_base64=request.screenshot_base64,
        screenshot_mime_type=request.screenshot_mime_type,
    )
    return GameHelpResponse(**result)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)