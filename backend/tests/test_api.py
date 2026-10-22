# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import get_db
from main import app
import github_service

# Use in-memory SQLite database for isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["version"] == "1.0.0"

def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"

def test_github_scoring_algorithms():
    # Complexity score tests
    assert github_service.calculate_complexity_score(0, 0, 0) == 10
    score_small = github_service.calculate_complexity_score(50, 10, 5)
    score_huge = github_service.calculate_complexity_score(250000, 40000, 1200)
    assert 1 <= score_small <= 99
    assert score_huge > score_small
    assert score_huge <= 99

    # Health score tests
    assert github_service.calculate_health_score(0, 0, 0) == 50
    health_active = github_service.calculate_health_score(50, 1000, 300)
    health_neglected = github_service.calculate_health_score(3000, 1000, 20)
    assert health_active > health_neglected

def test_email_domain_validation_on_registration():
    # 1. Non-existent domain
    bad_payload = {
        "username": "baduser",
        "email": "baduser@nonexistentdomain999999999.xyz",
        "password": "SecurePassword123!"
    }
    bad_resp = client.post("/api/register", json=bad_payload)
    assert bad_resp.status_code == 400

    # 2. Random unregistered / unapproved domain
    random_payload = {
        "username": "randomuser",
        "email": "skjdnclscw@sjkvnv.com",
        "password": "SecurePassword123!"
    }
    rand_resp = client.post("/api/register", json=random_payload)
    assert rand_resp.status_code == 400
    assert "not accepted" in rand_resp.json()["detail"] or "does not exist" in rand_resp.json()["detail"]

    # 3. Squatted 4-letter domain with parked MX (kjfn.com)
    kjfn_payload = {
        "username": "kjfnuser",
        "email": "sdfncvluws@kjfn.com",
        "password": "SecurePassword123!"
    }
    kjfn_resp = client.post("/api/register", json=kjfn_payload)
    assert kjfn_resp.status_code == 400
    assert "not accepted" in kjfn_resp.json()["detail"]

    # 4. Malformed syntax
    malformed_payload = {
        "username": "baduser2",
        "email": "notanemailaddress",
        "password": "SecurePassword123!"
    }
    malformed_resp = client.post("/api/register", json=malformed_payload)
    assert malformed_resp.status_code == 400

def test_user_registration_and_login_flow():
    # 1. Register with a recognized provider domain (gmail.com)
    user_payload = {
        "username": "testdev",
        "email": "testdev@gmail.com",
        "password": "SecurePassword123!"
    }
    register_resp = client.post("/api/register", json=user_payload)
    assert register_resp.status_code == 201
    user_data = register_resp.json()
    assert user_data["username"] == "testdev"
    assert user_data["email"] == "testdev@gmail.com"
    assert "hashed_password" not in user_data

    # 2. Duplicate registration fails
    dup_resp = client.post("/api/register", json=user_payload)
    assert dup_resp.status_code == 400
    assert "Email is already registered" in dup_resp.json()["detail"]

    # 3. Login with credentials
    login_resp = client.post(
        "/api/login",
        data={"username": "testdev", "password": "SecurePassword123!"}
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 4. Access profile with token
    auth_header = {"Authorization": f"Bearer {token_data['access_token']}"}
    profile_resp = client.get("/api/profile", headers=auth_header)
    assert profile_resp.status_code == 200
    assert profile_resp.json()["username"] == "testdev"

    # 5. Update user skills
    update_resp = client.put(
        "/api/profile",
        json={"skills": "Python, TypeScript", "interests": "Web development, AI"},
        headers=auth_header
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["skills"] == "Python, TypeScript"

def test_unauthorized_access():
    response = client.get("/api/profile")
    assert response.status_code == 401

def test_ai_service_insights_structure():
    import ai_service
    result = ai_service.generate_repo_insights(
        repo_name="test-repo",
        owner="test-owner",
        description="A great open-source project",
        language="Python"
    )
    assert "summary" in result
    assert "roadmap" in result
    assert isinstance(result["roadmap"], list)
    assert len(result["roadmap"]) >= 2
    # Ensure no raw JSON errors leaked into roadmap
    for step in result["roadmap"]:
        assert "Unterminated string" not in step
        assert "JSONDecodeError" not in step
