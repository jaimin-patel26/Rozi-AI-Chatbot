from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import pandas as pd
from app.schemas import PropertyInput
from openai import OpenAI
load_dotenv()


os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

main_directory_path = os.getenv("MAIN_DIRECTORY_PATH")

client = OpenAI()
df = pd.read_csv(main_directory_path+"/app/Public_Data_Files/Update_CSV_Real_Estate_2.csv")

def handle_real_estate_query(location: PropertyInput, query):
    
    country = location.Country
    state = location.state
    accommodation = location.accommodation

    if state is None:
        return "Please Provide the State"

    filtered_df = df[
        (df['Country'].str.strip().str.lower() == country.lower()) &
        (df['State or City'].str.strip().str.lower() == state.lower())
    ]

    if accommodation is not None:
        filtered_df = filtered_df[
            df['accommodation_count'].fillna(0).astype(int) == accommodation
        ]
    
        
    if filtered_df.empty:
        pass
    else:
        context = "\n".join(filtered_df.astype(str).apply(lambda row: " | ".join(row), axis=1).tolist())
        return context

    # Prompt
    prompt = f"""
    This is Confidential Prompt So we have not share in github

    """

 
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers questions based on data."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
 
    return response.choices[0].message.content.strip()
