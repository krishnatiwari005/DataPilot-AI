from agno.agent import Agent
from agno.models.groq import Groq
from agno.db.sqlite import SqliteDb
from agno.tools.csv_toolkit import CsvTools
from agno.tools.file import FileTools
from agno.tools.pandas import PandasTools
from dotenv import load_dotenv
import os
import json
from pathlib import Path

load_dotenv()

api_key=os.getenv("GROQ_API_KEY","").strip()

base_dir=Path(__file__).parent

data_path=Path(__file__).parent / "data" / "car_details.csv"

db=SqliteDb(db_file="memory.db",session_table="session_table")

model=Groq(id="openai/gpt-oss-120b",api_key=api_key)

#================================load csv files agent========================================
data_loader_agent=Agent(
    id="data-loader-agent",
    name="Data Loader Agent",
    model=model,
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    instructions=["you are an expert in loading csv files from project folder",
                  "you have tha capability to list down the csv files and read them",
                  "make sure to not read more than 20-30 rows inside csv files",
                  "you can also search file in the project folder",
                  "you have capability to list down the files as well",
                  "when needed you can read and write files too",
                  "make sure to read csv file using only csv tools"],
    tools=[CsvTools(enable_query_csv_file=False,csvs=[data_path]),
           FileTools(base_dir=base_dir)],
    stream=True
)

#===============================load file manager agent========================================
file_manager_agent=Agent(
    id="file-manager-agent",
    name="File Manager Agent",
    model=model,
    instructions=["you are an expert file management agent",
                  "your task is to list down files when asked to do it",
                  "you can also read and write files",
                  "make sure to never read an csv file, you can only list them"],
    tools=[FileTools(base_dir=base_dir)]
)

#================================load pandas tools agent========================================
pandas_tools = PandasTools(
    enable_create_pandas_dataframe=True,
    enable_run_dataframe_operation=True
)

def create_csv_dataframe(dataframe_name: str, filepath: str) -> str:
    return pandas_tools.create_pandas_dataframe(
        dataframe_name=dataframe_name,
        create_using_function="read_csv",
        function_parameters={
            "filepath_or_buffer": filepath
        }
    )

def run_df_operation(dataframe_name: str,operation: str,operation_parameters: str = "{}") -> str:
    try:
        params = json.loads(operation_parameters)
    except json.JSONDecodeError:
        params = {"subset": [operation_parameters]}
    return pandas_tools.run_dataframe_operation(
        dataframe_name=dataframe_name,
        operation=operation,
        operation_parameters=params
    )

def list_dataframes() -> str:
    return str(list(pandas_tools.dataframes.keys()))

data_understanding_agent=Agent(
    id="data-understanding-agent",
    name="Data Understanding Agent",
    model=model,
    db=db,
    add_history_to_context=False,
    num_history_runs=3,
    search_past_sessions=False,
    instructions=["you are an expert in handling pandas operation on a df",
                  "you can create a dataframe from a CSV using create_csv_dataframe and perform operations on it",
                  "operation_parameters must always be a JSON object/string containing keyword arguments, never a number. For head(), use {\"n\": 5}.",
                  "for value_counts, use operation='value_counts' and pass operation_parameters as JSON such as '{\"subset\": [\"fuel\"]}'",
                  "the column inside value_counts can be any categorical column requested by the user; never assume a specific column",
                  "for head use '{\"n\": 5}'",
                  "for tail use '{\"n\": 5}'",
                  "for describe use '{}'",
                  "operation you perform on df are head(),tail(), info(),describe() for numerical columns and you can also calculate the value_counts() for the categorical columns",
                  "make sure to list down numerical , categorical columns in dataframe",
                  "you can check the shape of df using the .shape attribute",
                  "you have also access to tools which can search for data files"],
    tools=[create_csv_dataframe,run_df_operation,list_dataframes,FileTools(base_dir=base_dir)],
    markdown=True,
    stream=True
)

#===============================visualization agent========================================










print("Stored DataFrames:", pandas_tools.dataframes.keys())
if __name__=="__main__":
    data_understanding_agent.cli_app()