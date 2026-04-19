import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    user_id: uuid.UUID
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    display_name: str
    created_at: datetime
    subscription_tier: str
    is_active: bool
    is_admin: bool


class PreferencesIn(BaseModel):
    genre_ids: list[int] = Field(default_factory=list)
    preferred_language: str = Field(default="en", min_length=2, max_length=5)
    maturity_rating: str = Field(default="PG-13")
    onboarding_complete: bool = False

    @field_validator("maturity_rating")
    @classmethod
    def validate_maturity(cls, v: str) -> str:
        allowed = {"G", "PG", "PG-13", "R", "NC-17", "TV-Y", "TV-G", "TV-PG", "TV-14", "TV-MA"}
        if v not in allowed:
            raise ValueError(f"maturity_rating must be one of {sorted(allowed)}")
        return v


class PreferencesOut(PreferencesIn):
    model_config = ConfigDict(from_attributes=True)
    updated_at: datetime
