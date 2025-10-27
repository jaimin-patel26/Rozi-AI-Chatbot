from fastapi import APIRouter, UploadFile, Form ,File, Depends, HTTPException, status
from fastapi.responses import FileResponse,JSONResponse
from sqlalchemy.orm import Session
from app import schemas, models, auth, database
from app.auth import create_access_token
from app.auth import get_current_user,get_current_user_from_api_key
from jose import JWTError, jwt
from app.config import settings
from app.utils import create_api_key
from app.Agent.agent import PropertyAgent
from app.upload_utils import load_document
from app.message_utils import set_messages,get_messages, AIMessage
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from app.Agent.private_main_agent import PrivateAgent
from uuid import UUID
import os
import uuid
import shutil

## Local Upload Files Path
UPLOAD_DIR = "./app/Agent/Vector_Store/Private/uploads"
FAISS_DIR = "./app/Agent/Vector_Store/Private/faiss_indexes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)

PHOTO_UPLOAD_DIR = "photo_uploads"
os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)

print(os.path.abspath(UPLOAD_DIR))

embedding_model = OpenAIEmbeddings(model = "text-embedding-3-large")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = auth.hash_password(user.password)
    user_data = user.model_dump()
    user_data["password"] = hashed_pwd
    new_user = models.User(**user_data)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth.create_access_token(data={"sub": db_user.email})
    refresh_token = auth.create_refresh_token(data={"sub": db_user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/update_user_details")
def update_user_details(
    firstname: str = Form(...),
    lastname: str = Form(...),
    phone: str = Form(None),
    city: str = Form(None),
    country: str = Form(None),
    street: str = Form(None),
    billing_city: str = Form(None),
    state: str = Form(None),
    post_code: str = Form(None),
    billing_country: str = Form(None),
    linkedin: str = Form(None),
    instagram: str = Form(None),
    facebook: str = Form(None),
    x: str = Form(None),
    photo: UploadFile = File(None),current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    

    current_user = db.query(models.User).filter_by(id=current_user.id).first()
    if not firstname.strip() or not lastname.strip():
        raise HTTPException(status_code=400, detail="Firstname and Lastname are required")

    if photo and photo.filename != "":
        if current_user.photo:
            old_photo_path = os.path.basename(current_user.photo)
            old_photo_full_path = os.path.join(PHOTO_UPLOAD_DIR, old_photo_path)
            if os.path.exists(old_photo_full_path):
                os.remove(old_photo_full_path)

        file_ext = photo.filename.split(".")[-1]
        file_name = f"{current_user.id}.{file_ext}"
        file_path = os.path.join(PHOTO_UPLOAD_DIR, file_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
    
        current_user.photo = f"/files/{file_name}"
    update_fields = {
        "firstname": firstname,
        "lastname": lastname,
        "phone": phone,
        "city": city,
        "country": country,
        "street": street,
        "billing_city": billing_city,
        "state": state,
        "post_code": post_code,
        "billing_country": billing_country,
        "linkedin": linkedin,
        "instagram": instagram,
        "facebook": facebook,
        "x": x
    }
    for field, value in update_fields.items():
        if value is not None and value != "":
            setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return JSONResponse({
        "message": "User updated successfully",
        "user": {
            "id": str(current_user.id),
            "firstname": current_user.firstname,
            "lastname": current_user.lastname,
            "email": current_user.email,
            "phone": current_user.phone,
            "city": current_user.city,
            "country": current_user.country,
            "street": current_user.street,
            "billing_city": current_user.billing_city,
            "state": current_user.state,
            "post_code": current_user.post_code,
            "billing_country": current_user.billing_country,
            "linkedin": current_user.linkedin,
            "instagram": current_user.instagram,
            "facebook": current_user.facebook,
            "x": current_user.x,
            "photo": current_user.photo
        }
    })

@router.get("/get_user_detail")
def generate_user_details(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "id": str(current_user.id),
        "firstname": current_user.firstname,
        "lastname": current_user.lastname,
        "email": current_user.email,
        "phone": current_user.phone,
        "city": current_user.city,
        "country": current_user.country,
        "street": current_user.street,
        "billing_city": current_user.billing_city,
        "state": current_user.state,
        "post_code": current_user.post_code,
        "billing_country": current_user.billing_country,
        "linkedin": current_user.linkedin,
        "instagram": current_user.instagram,
        "facebook": current_user.facebook,
        "x": current_user.x,
        "photo_url": current_user.photo
    }




@router.post("/refresh")
async def refresh_token(request: schemas.RefreshRequest):
    try:
        refresh_token = request.refresh_token
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Missing refresh token")
        
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = auth.create_access_token(data={"sub": email})
        return {"access_token": new_access_token, "token_type": "bearer"}
    
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired refresh token")

@router.post("/generate_api_key")
def generate_api_key(api_key_data: schemas.APIKeyCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):

    existing_key = db.query(models.APIKEY).filter(models.APIKEY.user_id == current_user.id,models.APIKEY.agent_id == api_key_data.agent_id).first()

    if existing_key:
        raise HTTPException(
            status_code=400,
            detail=f"API key already exists for ths Agent."
        )
    try:    
        api_key = create_api_key()
        new_apikey = models.APIKEY(user_id=current_user.id,name=api_key_data.name,agent_id=api_key_data.agent_id,api_key=api_key)
        db.add(new_apikey)
        db.commit()
        db.refresh(new_apikey)

        return {
            "api_key": api_key,
            "message": "Store this API key securely. It will not be shown again.",
            "id": new_apikey.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_api_key")
def delete_api_key(
    data: schemas.APIKeyDeleteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    api_key_record = db.query(models.APIKEY).filter_by(id=data.id, user_id=current_user.id).first()

    if not api_key_record:
        raise HTTPException(status_code=404, detail="API key not found or unauthorized")
 
    db.delete(api_key_record)
    db.commit()
 
    return {"message": f"API key with ID {data.id} deleted successfully."}

@router.get("/get_api_keys", response_model=list[schemas.APIKeyInfo])
def get_api_keys_for_current_user(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    api_keys = db.query(models.APIKEY).filter(models.APIKEY.user_id == current_user.id).all()

    response = []
    if not api_keys:
        return response


    for key in api_keys:
        response.append(schemas.APIKeyInfo(
            id=key.id,
            name=key.name,
            api_key=key.api_key,
            agent_id=key.agent_id,
            agent_name=key.agent.name,
            purpose=key.agent.purpose,
            chatbot_type=key.agent.chatbot_type,
            created_at=key.created_at
        ))

    return response

# @router.post("/upload_files")
# def upload_files(file: UploadFile = File(...),current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
#     temp_file_path = ""
#     try:
#         file_ext = os.path.splitext(file.filename)[1].lower()
#         if file_ext not in [".pdf", ".txt", ".csv"]:
#             raise HTTPException(status_code=400, detail="Unsupported file type")

#         user_folder = os.path.join(UPLOAD_DIR, str(current_user.id))
#         os.makedirs(user_folder, exist_ok=True)
#         temp_file_path = os.path.join(user_folder, f"{uuid.uuid4()}_{file.filename}")
#         with open(temp_file_path, "wb") as f:
#             f.write(file.file.read())

#         raw_docs = load_document(temp_file_path, file_ext)
#         chunks = text_splitter.split_documents(raw_docs)

#         faiss_local_dir = os.path.join(FAISS_DIR, str(current_user.id))
#         os.makedirs(faiss_local_dir, exist_ok=True)

#         faiss_index_file = os.path.join(faiss_local_dir, "index.faiss")
#         db_faiss = None
#         if os.path.exists(faiss_index_file):
#             db_faiss = FAISS.load_local(faiss_local_dir, embedding_model, allow_dangerous_deserialization = True)
            
#         if not chunks:
#             raise HTTPException(status_code=400, detail="No readable content in the uploaded file.")

#         documents = [Document(page_content=chunk.page_content, metadata={"source": file.filename}) for chunk in chunks]
        
#         if db_faiss is None:
#             db_faiss = FAISS.from_documents(documents, embedding_model)
#         else:
#             db_faiss.add_documents(documents)
#         db_faiss.save_local(faiss_local_dir)

#         return {
#             "message": f"File uploaded and embedded successfully.",
#             "filename": file.filename,
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_files")
def upload_files(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    temp_file_path = ""
    try:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in [".pdf", ".txt", ".csv"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        user_folder = os.path.join(UPLOAD_DIR, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        temp_file_path = os.path.join(user_folder, f"{file.filename}")
        with open(temp_file_path, "wb") as f:
            f.write(file.file.read())

        # file_size_mb = round(os.path.getsize(temp_file_path) / (1024 * 1024), 2)
        size_bytes = os.path.getsize(temp_file_path)

        file_size = (
            f"{round(size_bytes / 1024, 2)} KB"
            if size_bytes < 1024 * 1024
            else f"{round(size_bytes / (1024 * 1024), 2)} MB"
        )
 
        raw_docs = load_document(temp_file_path, file_ext)
        chunks = text_splitter.split_documents(raw_docs)

        if not chunks:
            raise HTTPException(status_code=400, detail="No readable content in the uploaded file.")
            
        uploaded_file = models.UploadedFile(
                user_id=current_user.id,
                filename=file.filename,
                s3_url=temp_file_path,
                filetype=file_ext,
                filesize=file_size
            )
        
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        
        documents = [
            Document(
                page_content=chunk.page_content,
                metadata={"source": file.filename, "file_id": str(uploaded_file.id)}
            )
            for chunk in chunks
        ]

        faiss_local_dir = os.path.join(FAISS_DIR, str(current_user.id))
        os.makedirs(faiss_local_dir, exist_ok=True)

        faiss_index_file = os.path.join(faiss_local_dir, "index.faiss")
        if os.path.exists(faiss_index_file):
            db_faiss = FAISS.load_local(faiss_local_dir, embedding_model, allow_dangerous_deserialization=True)
            db_faiss.add_documents(documents)
        else:
            db_faiss = FAISS.from_documents(documents, embedding_model)

        db_faiss.save_local(faiss_local_dir)

        return {
            "message": "File uploaded and embedded successfully.",
            "file_id": str(uploaded_file.id),
            "filename": uploaded_file.filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/get_uploaded_files")
def list_files(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        files = db.query(models.UploadedFile).filter(
            models.UploadedFile.user_id == current_user.id
        ).order_by(models.UploadedFile.uploaded_at.desc()).all()

        if not files:
            return []

        return [
            {
                "id": str(f.id),
                "filename": f.filename,
                "filetype": f.filetype,
                "uploaded_at": f.uploaded_at.isoformat(),
                "s3_url": f.s3_url,
                "file_size":f.filesize  
                
            }
            for f in files
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_uploaded_file")
def delete_file(
    file_id: schemas.UploadedFileDelete,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(models.UploadedFile).filter(
        models.UploadedFile.id == file_id.id,
        models.UploadedFile.user_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or not owned by you")

    if os.path.exists(file_record.s3_url):
        try:
            os.remove(file_record.s3_url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting file from disk: {str(e)}")

    faiss_local_dir = os.path.join(FAISS_DIR, str(current_user.id))
    faiss_index_file = os.path.join(faiss_local_dir, "index.faiss")

    if os.path.exists(faiss_index_file):
        db_faiss = FAISS.load_local(faiss_local_dir, embedding_model, allow_dangerous_deserialization=True)

        doc_ids_to_remove = [
            doc_id for doc_id, doc in db_faiss.docstore._dict.items()
            if doc.metadata.get("file_id") == str(file_id.id)
        ]

        if doc_ids_to_remove:
            db_faiss.delete(doc_ids_to_remove)
            db_faiss.save_local(faiss_local_dir)

    db.delete(file_record)
    db.commit()

    return {"message": f"File '{file_record.filename}' deleted successfully and removed from FAISS index."}


@router.post("/chatbot")
def chatbot(query: schemas.ChatbotQuery,user_data: tuple[models.User, UUID] = Depends(get_current_user_from_api_key), db: Session = Depends(get_db)):
    current_user, apikey_id = user_data

    session_id = query.session_id
    if session_id is None:
        create_session = models.ChatSession(
                user_id=current_user.id,
                apikey_id=apikey_id.id,
                agent_id=apikey_id.agent.id,
                name = query.input,
            )
        db.add(create_session)
        db.commit()
        session_id = create_session.id

    chat_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id ,models.ChatSession.user_id == current_user.id,models.ChatSession.apikey_id == apikey_id.id, models.ChatSession.agent_id == apikey_id.agent.id).first()
    if not chat_session:
        raise HTTPException(status_code=400, detail="Session Not Found")    
    
    if apikey_id.agent.chatbot_type == "Public":
        try:
            chat_history = db.query(models.ChatMessages).filter(models.ChatMessages.session_id == chat_session.id,models.ChatMessages.user_id == current_user.id,models.ChatMessages.apikey_id == apikey_id.id,models.ChatMessages.agent_id == apikey_id.agent.id ,models.ChatMessages.chatbot_type == "Public").first()
            agent_name = apikey_id.agent.name
            messages = get_messages(chat_history.messages) if chat_history else []
            file_path = f"{FAISS_DIR}/{current_user.id}"
            main_directory_path = os.getenv("MAIN_DIRECTORY_PATH")
            import pandas as pd
            df = pd.read_csv(main_directory_path+"/app/Public_Data_Files/Final_News_2.csv")
            all_titles = "\n".join(df['title'].astype(str))
            all_titles_wrapped = f'"""\n{all_titles}\n"""'
            bot_instance = PropertyAgent(messages, agent_name,all_titles_wrapped, file_path)
            response = bot_instance.run_conversation(query.input)
            if response['output'] == "Agent stopped due to iteration limit or time limit.":
                response['output'] = "Sorry I don’t have the data related to this query."
            response['chat_history'].append(AIMessage(content=response['output']))
            chatmessage_history = set_messages(response['chat_history'])
            if chat_history:
                chat_history.messages = chatmessage_history
            else:
                chat_history = models.ChatMessages(
                    session_id=chat_session.id,
                    agent_id = apikey_id.agent.id,
                    user_id=current_user.id,
                    apikey_id=apikey_id.id,
                    messages=chatmessage_history,
                    chatbot_type="Public",
                )
                db.add(chat_history)

            db.commit()

            return {"status": "success","response": response['output'],"session_id":chat_session.id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    elif apikey_id.agent.chatbot_type == "Private":
        try:
            chat_history = db.query(models.ChatMessages).filter(models.ChatMessages.session_id == chat_session.id,models.ChatMessages.user_id == current_user.id,models.ChatMessages.apikey_id == apikey_id.id, models.ChatMessages.agent_id == apikey_id.agent.id, models.ChatMessages.chatbot_type == "Private").first()
            agent_name = apikey_id.agent.name

            messages = get_messages(chat_history.messages) if chat_history else []
            file_path = f"{FAISS_DIR}/{current_user.id}"
            bot_instance = PrivateAgent(messages, agent_name, file_path)
            response = bot_instance.run_conversation(query.input)
            if response['output'] == "Agent stopped due to iteration limit or time limit.":
                response['output'] = "Sorry I don’t have the data related to this query."
            response['chat_history'].append(AIMessage(content=response['output']))
            chatmessage_history = set_messages(response['chat_history'])

            if chat_history:
                chat_history.messages = chatmessage_history
            else:
                chat_history = models.ChatMessages(
                    session_id=chat_session.id,
                    agent_id = apikey_id.agent.id,
                    user_id=current_user.id,
                    apikey_id=apikey_id.id, 
                    messages=chatmessage_history,                
                    chatbot_type="Private",
                )
                db.add(chat_history)

            db.commit()
            return {
                "status": "success",
                "response": response['output'],
                "session_id":chat_session.id
            }

        except FileNotFoundError as fnf_error:
            print("FileNotFoundError:", fnf_error)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Please upload your files first, as we couldn't find any resources."
            )

        except RuntimeError as runtime_error:
            print("RuntimeError:", runtime_error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing your query. Please try again later."
            )

        except Exception as general_error:
            print("Unexpected Error:", general_error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chatbot is currently under maintenance. Please try again later."
            )

# @router.post("/chatbot_private")
# def chatbot(query: schemas.ChatbotQuery,user_data: tuple[models.User, UUID] = Depends(get_current_user_from_api_key),db: Session = Depends(get_db)):
#     current_user, apikey_id = user_data
    
#     session_id = query.session_id
#     if session_id is None:
#         create_session = models.ChatSession(
#                 user_id=current_user.id,
#                 apikey_id=apikey_id.id,
#                 agent_id=apikey_id.agent.id,
#             )
#         db.add(create_session)
#         db.commit()
#         session_id = create_session.id

#     chat_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id ,models.ChatSession.user_id == current_user.id,models.ChatSession.apikey_id == apikey_id.id, models.ChatSession.agent_id == apikey_id.agent.id).first()
#     if not chat_session:
#         raise HTTPException(status_code=400, detail="Session Not Found")

#     try:
#         chat_history = db.query(models.ChatMessages).filter(models.ChatMessages.session_id == chat_session.id,models.ChatMessages.user_id == current_user.id,models.ChatMessages.apikey_id == apikey_id.id, models.ChatMessages.agent_id == apikey_id.agent.id, models.ChatMessages.chatbot_type == "Private").first()
#         agent_name = apikey_id.agent.name

#         messages = get_messages(chat_history.messages) if chat_history else []
#         file_path = f"{FAISS_DIR}/{current_user.id}"
#         bot_instance = PrivateAgent(messages, agent_name, file_path)
#         response = bot_instance.run_conversation(query.input)
#         if response['output'] == "Agent stopped due to iteration limit or time limit.":
#             response['output'] = "Sorry I don’t have the data related to this query."
#         response['chat_history'].append(AIMessage(content=response['output']))
#         chatmessage_history = set_messages(response['chat_history'])

#         if chat_history:
#             chat_history.messages = chatmessage_history
#         else:
#             chat_history = models.ChatMessages(
#                 session_id=chat_session.id,
#                 agent_id = apikey_id.agent.id,
#                 user_id=current_user.id,
#                 apikey_id=apikey_id.id,
#                 messages=chatmessage_history,                
#                 chatbot_type="Private",
#             )
#             db.add(chat_history)

#         db.commit()
#         return {
#             "status": "success",
#             "response": response['output']
#         }

#     except FileNotFoundError as fnf_error:
#         print("FileNotFoundError:", fnf_error)
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Please upload your files first, as we couldn't find any resources."
#         )

#     except RuntimeError as runtime_error:
#         print("RuntimeError:", runtime_error)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while processing your query. Please try again later."
#         )

#     except Exception as general_error:
#         print("Unexpected Error:", general_error)
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Public Chatbot is currently under maintenance. Please try again later."
#         )

@router.post("/api/v1")
def api_access(query: schemas.ChatbotAPIEndpointV1,user_data: tuple[models.User, UUID] = Depends(get_current_user_from_api_key), db: Session = Depends(get_db)):
    current_user, apikey_id = user_data

    # session_id = query.session_id
    # if session_id is None:
    #     create_session = models.ChatSession(
    #             user_id=current_user.id,
    #             apikey_id=apikey_id.id,
    #             agent_id=apikey_id.agent.id,
    #         )
    #     db.add(create_session)
    #     db.commit()
    #     session_id = create_session.id

    # chat_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id ,models.ChatSession.user_id == current_user.id,models.ChatSession.apikey_id == apikey_id.id, models.ChatSession.agent_id == apikey_id.agent.id).first()
    # if not chat_session:
    #     raise HTTPException(status_code=400, detail="Session Not Found")    
    messages = []
    if apikey_id.agent.chatbot_type == "Public":
        try:
            # chat_history = db.query(models.ChatMessages).filter(models.ChatMessages.session_id == chat_session.id,models.ChatMessages.user_id == current_user.id,models.ChatMessages.apikey_id == apikey_id.id,models.ChatMessages.agent_id == apikey_id.agent.id ,models.ChatMessages.chatbot_type == "Public").first()
            agent_name = apikey_id.agent.name
            # messages = get_messages(chat_history.messages) if chat_history else []
            
            file_path = f"{FAISS_DIR}/{current_user.id}"
            main_directory_path = os.getenv("MAIN_DIRECTORY_PATH")
            import pandas as pd
            df = pd.read_csv(main_directory_path+"/app/Public_Data_Files/Final_News_2.csv")
            all_titles = "\n".join(df['title'].astype(str))
            all_titles_wrapped = f'"""\n{all_titles}\n"""'
            bot_instance = PropertyAgent(messages, agent_name,all_titles_wrapped, file_path)
            response = bot_instance.run_conversation(query.input)
            if response['output'] == "Agent stopped due to iteration limit or time limit.":
                response['output'] = "Sorry I don’t have the data related to this query."
            response['chat_history'].append(AIMessage(content=response['output']))
            chatmessage_history = set_messages(response['chat_history'])
            # if chat_history:
            #     chat_history.messages = chatmessage_history
            # else:
            #     chat_history = models.ChatMessages(
            #         session_id=chat_session.id,
            #         agent_id = apikey_id.agent.id,
            #         user_id=current_user.id,
            #         apikey_id=apikey_id.id,
            #         messages=chatmessage_history,
            #         chatbot_type="Public",
            #     )
            #     db.add(chat_history)

            # db.commit()

            return {"status": "success","response": response['output']}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    elif apikey_id.agent.chatbot_type == "Private":
        try:
            # chat_history = db.query(models.ChatMessages).filter(models.ChatMessages.session_id == chat_session.id,models.ChatMessages.user_id == current_user.id,models.ChatMessages.apikey_id == apikey_id.id, models.ChatMessages.agent_id == apikey_id.agent.id, models.ChatMessages.chatbot_type == "Private").first()
            agent_name = apikey_id.agent.name

            # messages = get_messages(chat_history.messages) if chat_history else []
            file_path = f"{FAISS_DIR}/{current_user.id}"
            bot_instance = PrivateAgent(messages, agent_name, file_path)
            response = bot_instance.run_conversation(query.input)
            if response['output'] == "Agent stopped due to iteration limit or time limit.":
                response['output'] = "Sorry I don’t have the data related to this query."
            response['chat_history'].append(AIMessage(content=response['output']))
            chatmessage_history = set_messages(response['chat_history'])

            # if chat_history:
            #     chat_history.messages = chatmessage_history
            # else:
            #     chat_history = models.ChatMessages(
            #         session_id=chat_session.id,
            #         agent_id = apikey_id.agent.id,
            #         user_id=current_user.id,
            #         apikey_id=apikey_id.id, 
            #         messages=chatmessage_history,                
            #         chatbot_type="Private",
            #     )
            #     db.add(chat_history)

            # db.commit()
            return {
                "status": "success",
                "response": response['output']
            }

        except FileNotFoundError as fnf_error:
            print("FileNotFoundError:", fnf_error)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Please upload your files first, as we couldn't find any resources."
            )

        except RuntimeError as runtime_error:
            print("RuntimeError:", runtime_error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing your query. Please try again later."
            )

        except Exception as general_error:
            print("Unexpected Error:", general_error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chatbot is currently under maintenance. Please try again later."
            )

# @router.post("/api/v1")
# def chatbot(query: schemas.ChatbotAPIEndpointV1,user_data: tuple[models.User, UUID] = Depends(get_current_user_from_api_key), db: Session = Depends(get_db)):

#     current_user, apikey_id = user_data
#     try:
#         if query.type.lower() =="public":
#             try:
#                 chat_history = db.query(models.ChatMessages).filter(models.ChatMessages.user_id == current_user.id,models.ChatMessages.apikey_id == apikey_id.id, models.ChatMessages.chatbot_type == "Public").first()
#                 messages = get_messages(chat_history.messages) if chat_history else []
#                 file_path = f"{FAISS_DIR}/{current_user.id}"
#                 bot_instance = PropertyAgent(messages, file_path)
#                 response = bot_instance.run_conversation(query.input)
#                 if response['output'] == "Agent stopped due to iteration limit or time limit.":
#                     response['output'] = "Sorry I don’t have the data related to this query."
#                 response['chat_history'].append(AIMessage(content=response['output']))
#                 chatmessage_history = set_messages(response['chat_history'])
#                 if chat_history:
#                     chat_history.messages = chatmessage_history
#                 else:
#                     chat_history = models.ChatMessages(
#                         user_id=current_user.id,
#                         apikey_id=apikey_id.id,
#                         messages=chatmessage_history,
#                         chatbot_type="Public",
#                     )
#                     db.add(chat_history)

#                 db.commit()

#                 return {"status": "success","response": response['output']}
#             except Exception as e:
#                 raise HTTPException(status_code=500, detail=str(e))

#         elif query.type.lower() =="private":
#             try:
#                 chat_history = db.query(models.ChatMessages).filter(models.ChatMessages.user_id == current_user.id,models.ChatMessages.apikey_id == apikey_id.id, models.ChatMessages.chatbot_type == "Private").first()
#                 agentname = db.query(models.AgentName).filter(models.AgentName.user_id == current_user.id, models.AgentName.chatbot_type == "Private").first()

#                 if agentname:
#                     agent_name = agentname.agent_name
#                 else:
#                     agent_name = "Rozi"

#                 messages = get_messages(chat_history.messages) if chat_history else []
#                 file_path = f"{FAISS_DIR}/{current_user.id}"
#                 bot_instance = PrivateAgent(messages, agent_name, file_path)
#                 response = bot_instance.run_conversation(query.input)
#                 if response['output'] == "Agent stopped due to iteration limit or time limit.":
#                     response['output'] = "Sorry I don’t have the data related to this query."
#                 response['chat_history'].append(AIMessage(content=response['output']))
#                 chatmessage_history = set_messages(response['chat_history'])
#                 if chat_history:
#                     chat_history.messages = chatmessage_history
#                 else:
#                     chat_history = models.ChatMessages(
#                         user_id=current_user.id,
#                         apikey_id=apikey_id.id,
#                         messages=chatmessage_history,
#                         chatbot_type="Private",
#                     )
#                     db.add(chat_history)

#                 db.commit()
#                 return {
#                     "status": "success",
#                     "response": response['output']
#                 }

#             except FileNotFoundError as fnf_error:
#                 print("FileNotFoundError:", fnf_error)
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail="Please upload your files first, as we couldn't find any resources."
#                 )

#             except RuntimeError as runtime_error:
#                 print("RuntimeError:", runtime_error)
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="An error occurred while processing your query. Please try again later."
#                 )

#             except Exception as general_error:
#                 print("Unexpected Error:", general_error)
#                 raise HTTPException(
#                     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#                     detail="Chatbot is currently under maintenance. Please try again later."
#                 )
#         else:
#             raise HTTPException(status_code=400, detail="Type mismatch: provided parameter does not match expected type.")
#     except Exception as general_error:
#             print("Unexpected Error:", general_error)
#             raise HTTPException(
#                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#                 detail="Chatbot is currently under maintenance. Please try again later."
#             )

@router.delete("/delete_chat")
def delete_chatbot_history(query: schemas.DeleteSessionRequest,user_data: tuple[models.User, UUID] = Depends(get_current_user_from_api_key),db: Session = Depends(get_db)):
    current_user, apikey_id = user_data
    try:
        chat_history = db.query(models.ChatSession).filter(
            models.ChatSession.id == query.session_id,
            models.ChatSession.user_id == current_user.id,
            models.ChatSession.apikey_id == apikey_id.id,
            models.ChatSession.agent_id == apikey_id.agent.id
        ).first()
        print(chat_history)
        if chat_history:
            db.delete(chat_history)
            db.commit()
            return {"status": "success", "message": "Chatbot history deleted."}
        else:
            raise HTTPException(status_code=404, detail="No chat history found to delete.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# @router.delete("/delete_private_chat")
# def delete_chatbot_history(user_data: tuple[models.User, UUID] = Depends(get_current_user_from_api_key),db: Session = Depends(get_db)):
#     current_user, apikey_id = user_data
#     try:
#         chat_history = db.query(models.ChatMessages).filter(
#             models.ChatMessages.user_id == current_user.id,
#             models.ChatMessages.apikey_id == apikey_id.id,
#             models.ChatMessages.chatbot_type == "Private"
#         ).first()

#         if chat_history:
#             db.delete(chat_history)
#             db.commit()
#             return {"status": "success", "message": "Chatbot history deleted."}
#         else:
#             return {"status": "success", "message": "No chat history found to delete."}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_agent")
def create_agent(data: schemas.AgentCreate ,current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if data.chatbot_type not in ["Public","Private"]:
            raise HTTPException(
                status_code=400,
                detail=f"Please Check the Chatbot Type , It should be Public or Private."
            )
        existing_key = db.query(models.Agent).filter(
            models.Agent.user_id == current_user.id,models.Agent.name == data.name, models.Agent.chatbot_type == data.chatbot_type
        ).first()
        if existing_key:
            raise HTTPException(
                status_code=400,
                detail=f"Agent already exists. Please creating a new agent name."
            )
        
        new_agent = models.Agent(user_id=current_user.id,name=data.name,purpose=data.purpose,chatbot_type=data.chatbot_type)
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)

        return {
            "status": "success",
            "message": "Agent is created Successfully.",
            "agent_id": new_agent.id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get_all_agents", response_model=list[schemas.AgentInfo])
def get_agentname_for_current_user(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    agentnames = db.query(models.Agent).filter(models.Agent.user_id == current_user.id).all()
    if not agentnames:
        return []
    return agentnames
    
@router.delete("/delete_agent")
def delete_agent(data: schemas.AgentDeleteRequest,db: Session = Depends(get_db),current_user: models.User = Depends(get_current_user)):
    agent_record = db.query(models.Agent).filter_by(id=data.id, user_id=current_user.id).first()
 
    if not agent_record:
        raise HTTPException(status_code=404, detail="Agent Not Found or unauthorized")
 
    db.delete(agent_record)
    db.commit()
 
    return {"message": f"Agent with ID {data.id} deleted successfully."}

@router.get("/get_all_session")
def get_all_session_filter_with_agent_and_user(agent_id: UUID,db: Session = Depends(get_db),current_user: models.User = Depends(get_current_user)):
    all_sessions = db.query(models.ChatSession).filter(models.ChatSession.agent_id == agent_id ,models.ChatSession.user_id == current_user.id).all()
    if not all_sessions:
        return []
    return all_sessions

@router.get("/conversation_history", response_model=list[schemas.ConversationHistoryInfo])
def get_all_session_filter_with_agent_and_user(session_id: UUID,db: Session = Depends(get_db),current_user: models.User = Depends(get_current_user)):
    all_conversation = db.query(models.ChatMessages).filter(models.ChatMessages.session_id == session_id ,models.ChatMessages.user_id == current_user.id).all()
    if not all_conversation:
        return []
    return all_conversation


@router.post("/download_file")
def download_file(file_id: schemas.DownloadFileIDRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_record = db.query(models.UploadedFile).filter(
        models.UploadedFile.id == file_id.file_id,
        models.UploadedFile.user_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or not owned by you")

    if not os.path.exists(file_record.s3_url):
        raise HTTPException(status_code=404, detail="File does not exist on server")
    return FileResponse(
        path=file_record.s3_url,
        filename=file_record.filename,
        media_type='application/octet-stream'
    )
