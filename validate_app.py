import sys
from app.models.user import User
from app.models.blog import Blog, BlogStatus
from app.schemas.auth import RegisterResponse
from app.schemas.blog import BlogOut
from app.services import auth_service, email_service, blog_service

print("Imports successful.")

# Validate Schema Fields
try:
    print("Validating RegisterResponse schema...")
    assert "access_token" in RegisterResponse.model_fields
    assert "user" not in RegisterResponse.model_fields # Should be flat or specific structure
    print("RegisterResponse schema check passed.")
except AssertionError as e:
    print(f"Schema Validation Failed: {e}")
except Exception as e:
    print(f"Error during schema validation: {e}")

print("Validation script finished.")
