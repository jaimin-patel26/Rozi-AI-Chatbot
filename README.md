# Rozi AI Chatbot

Rozi AI Chatbot is a FastAPI-based backend service for user authentication, chatbot interaction, and secure API key management.  
It provides JWT-based authentication, private and public chatbot agents, file upload and embedding support, and session-based conversation management.

---

## Features

- **User Authentication**
  - User registration and login with password hashing
  - JWT-based access and refresh tokens
  - Update and retrieve user profile with optional photo upload

- **API Key Management**
  - Generate, view, and delete API keys
  - One API key per agent per user
  - API keys securely hashed before storage

- **Agent Management**
  - Create and manage chatbot agents (Public or Private)
  - Define the purpose and chatbot type per agent

- **File Management and Embeddings**
  - Upload `.pdf`, `.txt`, or `.csv` files
  - Automatically chunk and embed documents using FAISS and OpenAI embeddings
  - Retrieve, list, and delete uploaded files

- **Chatbot Interaction**
  - Chat with agents using API key authentication
  - Supports both Public and Private chatbot types
  - Private chatbots use user-uploaded data
  - Public chatbots use shared global data sources

- **Chat Sessions and History**
  - Maintain and manage chat sessions
  - Retrieve and delete conversation history per session

---

## Project Structure

app/
├── auth.py # Handles password hashing and JWT operations
├── config.py # Configuration and environment variables
├── database.py # SQLAlchemy setup and database session
├── main.py # FastAPI application entry point
├── models.py # SQLAlchemy ORM models
├── routes.py # API route definitions
├── schemas.py # Pydantic request/response models
├── utils.py # Utility functions (e.g., API key generation)
├── Agent/ # Chatbot agent logic (PropertyAgent, PrivateAgent)
├── upload_utils.py # File loading and parsing utilities
├── message_utils.py # Chat message handling and serialization


---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/jaimin-patel26/Rozi-AI-Chatbot
cd Rozi_AI_Chatbot

2. Create and Activate a Virtual Environment
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate


3. Install Dependencies
pip install -r requirements.txt


4. Configure Environment Variables

Create a .env file in the root directory and add the following values:

DATABASE_URL=postgresql://your_user:your_password@localhost/your_db
SECRET_KEY=your_secret_key
REFRESH_SECRET_KEY=your_refresh_secret_key
ALGORITHM=HS256
MAIN_DIRECTORY_PATH=/absolute/path/to/project/root

5. Run Database Migrations (if applicable)

Make sure your PostgreSQL database is running and initialized.

If you are using Alembic or raw SQL setup, apply the migrations:

alembic upgrade head

6. Start the Application
uvicorn app.main:app --reload

7. Access the API Documentation

Once the server starts, open your browser and go to:

http://127.0.0.1:8000/docs


or the alternative interactive UI:

http://127.0.0.1:8000/redoc


API Endpoints
Authentication
Method	Endpoint	Description
POST	/signup	Register a new user
POST	/login	Login with email and password
POST	/refresh	Refresh access token using refresh token
POST	/update_user_details	Update user details and upload profile photo
GET	/get_user_detail	Retrieve user profile details
API Key Management
Method	Endpoint	Description
POST	/generate_api_key	Generate API key for a specific agent
GET	/get_api_keys	List all API keys for the authenticated user
DELETE	/delete_api_key	Delete an API key by ID
Agent Management
Method	Endpoint	Description
POST	/create_agent	Create a new chatbot agent (Public or Private)
GET	/get_all_agents	Retrieve all agents for the current user
DELETE	/delete_agent	Delete an agent by ID
File Management
Method	Endpoint	Description
POST	/upload_files	Upload .pdf, .txt, or .csv files for embedding
GET	/get_uploaded_files	Retrieve uploaded files for the authenticated user
POST	/download_file	Download a file by ID
DELETE	/delete_uploaded_file	Delete an uploaded file and its FAISS data
Chatbot Interaction
Method	Endpoint	Description
POST	/chatbot	Interact with a chatbot using an API key
POST	/api/v1	Lightweight chatbot endpoint without session tracking
DELETE	/delete_chat	Delete a chat session and its messages
GET	/get_all_session	Retrieve all chat sessions for a specific agent
GET	/conversation_history	Get conversation history for a given session
Technologies Used

FastAPI

SQLAlchemy

Pydantic

Bcrypt

Python-Jose (JWT)

FAISS (Vector Search)

LangChain + OpenAI Embeddings

Pandas

Security

Passwords and API keys are hashed before being stored

JWT tokens ensure stateless and secure user authentication

File uploads are user-specific and isolated

API keys are unique per user and per agent

Requirements

Below is a sample requirements.txt file that you can include in your project:

fastapi
uvicorn
sqlalchemy
psycopg2-binary
python-dotenv
bcrypt
python-jose
pydantic
faiss-cpu
pandas
langchain
openai
tiktoken
aiofiles

License

This project is licensed under the MIT License. See the LICENSE
 file for more details.
