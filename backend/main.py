from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import engine, get_db
import models
import schemas
import auth

# Synchronize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Open Source Navigator API")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Open Source Navigator API!",
        "status": "Database tables synchronized successfully."
    }

@app.post("/api/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if the email already exists in the database
    existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    # 2. Check if the username already exists
    existing_username = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken."
        )

    # 3. Hash the plain text password securely using bcrypt
    hashed_password = auth.get_password_hash(user_data.password)

    # 4. Create a new User model instance
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    # 5. Save the user to our Neon Postgres database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Refreshes the instance to get the auto-generated ID from the DB

    # FastAPI will automatically filter this through schemas.UserResponse 
    # to make sure the hashed_password is never sent back to the client!
    return new_user

@app.post("/api/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # 1. Fetch user by username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # 2. Verify user exists and password is correct
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create JWT token storing user ID and username
    access_token = auth.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    # 4. Return token
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/profile", response_model=schemas.UserResponse)
def get_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    """Returns the currently logged-in user's profile details."""
    return current_user

@app.put("/api/profile", response_model=schemas.UserResponse)
def update_user_profile(
    profile_data: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Updates skills and interests for the authenticated user."""
    current_user.skills = profile_data.skills
    current_user.interests = profile_data.interests
    
    db.commit()
    db.refresh(current_user)
    return current_user