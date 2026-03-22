import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

grok_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(api_key=grok_api_key, model_name="openai/gpt-oss-120b")
output_parser = StrOutputParser()

def get_llm_insights(metadata, data_quality, selected):
    system_prompt = """
        You are a senior data analyst.
        You will be given metadata, data quality report, and selected columns for analysis.
        Your task is to provide a comprehensive analysis of the dataset.
        
        Metadata:
        {metadata}

        Data Quality:
        {data_quality}

        Selected Columns:
        {selected}

        Provide:
            1. Key insights
            2. Data issues
            3. Modelling suggestions
            4. Business interpretation
        
        Keep it clear and concise.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Generate insights based on the above information.")
    ])

    chain = prompt | llm | output_parser
    return chain.invoke({
        "metadata": metadata,
        "data_quality": data_quality,
        "selected": selected
    })