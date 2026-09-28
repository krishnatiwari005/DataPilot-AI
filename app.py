from agno.agent import Agent
from agno.models.groq import Groq
from agno.db.sqlite import SqliteDb
from agno.tools.csv_toolkit import CsvTools
from agno.tools.file import FileTools
from agno.tools.pandas import PandasTools
from agno.tools.visualization import VisualizationTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.team import Team
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
    dataframe = pandas_tools.dataframes.get(dataframe_name)
    if dataframe is None:
        return f"DataFrame '{dataframe_name}' does not exist."
    operation = operation.strip().lower()
    if operation == "shape":
        return str(dataframe.shape)
    if operation == "columns":
        return str(list(dataframe.columns))
    if operation == "dtypes":
        return str(dataframe.dtypes)
    # Operations that require no parameters
    if operation in ["info", "describe"]:
        params = {}
    else:
        # Handle missing parameters
        if operation_parameters is None:
            operation_parameters = "{}"
        # Convert dictionary directly
        if isinstance(operation_parameters, dict):
            params = operation_parameters
        # Convert integer directly
        elif isinstance(operation_parameters, int):
            params = {"n": operation_parameters}
        else:
            try:
                params = json.loads(str(operation_parameters))
            except (json.JSONDecodeError, TypeError):
                params = {}
        # json.loads("5") gives integer 5
        if not isinstance(params, dict):
            if operation in ["head", "tail"]:
                params = {"n": int(params)}
            elif operation == "value_counts":
                params = {"subset": [str(params)]}
            else:
                params = {}
    try:
        result = pandas_tools.run_dataframe_operation(
            dataframe_name=dataframe_name,
            operation=operation,
            operation_parameters=params
        )
        return str(result)
    except Exception as e:
        return f"DataFrame operation '{operation}' failed: {str(e)}"

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
                  "Supported operations are head, tail, info, describe, value_counts, shape, columns, and dtypes.",
                  "Use shape, columns, and dtypes as DataFrame properties handled by the wrapper.",
                  "Never pass null as operation_parameters.",
                  "make sure to list down numerical , categorical columns in dataframe",
                  "you can check the shape of df using the .shape attribute",
                  "you have also access to tools which can search for data files",
                  "operation_parameters must NEVER be null.",
                  ],
    tools=[create_csv_dataframe,run_df_operation,list_dataframes,FileTools(base_dir=base_dir)],
    markdown=True,
    stream=True
)

#===============================visualization agent========================================
visualization_agent = Agent(
    id="viz-agent",
    name="Visualization Agent",
    model=model,
    db=db,
    instructions=["You are an expert in creating data visualizations using matplotlib.",
                  "Use the existing DataFrame whenever possible.",
                  "Before creating a new DataFrame, use list_dataframes to check whether the requested DataFrame already exists.",
                  "If the requested DataFrame does not exist, use create_csv_dataframe to create it.",
                  "Use run_df_operation to inspect the DataFrame and obtain the data needed for visualization.", 
                  "You can create bar plots, pie charts, line plots, histograms, and scatter plots.", 
                  "Use bar plots for categorical columns.",
                  "Use histograms for numerical columns.",
                  "Use scatter plots when studying relationships between two numerical columns.",
                  "Use line plots when the data represents an ordered or time-based relationship.",
                  "Always verify that the requested column exists before creating a chart.",
                  "Always use the correct chart type for the requested data.",
                  "Do not create another PandasTools instance.",
                  "Do not directly call create_pandas_dataframe.",
                  "Use create_csv_dataframe and run_df_operation."],
    tools=[VisualizationTools("plots"),FileTools(base_dir=base_dir),create_csv_dataframe,run_df_operation,list_dataframes,],
    markdown=True,
    stream=True,
)

#========================================coding agent========================================
coding_agent=Agent(
    id="coding-agent",
    name="Coding Agent",
    db=db,
    add_history_to_context=True,
    num_history_runs=5,
    read_chat_history=True,
    model=model,
    instructions=["YOu are an expert coding agent proficient in writing python code",
                  "your main task is to write code specific to machine learning",
                  "you may use pandas, numpy, sklearn, scipy,etc in your code",
                  "you have access to tool that can list files in the directory and can also read them",
                  "the python tool also lets you create python files and write them , you can also run them to get desired output",
                  "you will be used to write python code for ml and data science task such as data cleaning , feature engineering , model training and model evaluation "
                  "you also have the websearch capability in case you need to access the latest document from the web",
                  "make sure to get the code reviewed by user and only write it into the file when user accepts it",
                  "if you want to add the packages use the shell tool and use the command 'uv add <package-name>' ",
                  "do not use shell tool to execute any other command than the one mentioned above"],
    tools=[PythonTools(base_dir=base_dir),DuckDuckGoTools(),ShellTools(base_dir=base_dir)],
    stream=True,
    markdown=True
)

#=========================================shell agent========================================
shell_agent=Agent(
    id="shell-agent",
    name="Shell Agent",
    add_history_to_context=True,
    model=model,
    db=db,
    instructions=["you have the capability to run shell commands",
                  "use this capability with extreme cautions",
                  "only use the shell tool capability if unable to execute the python file",
                  "use the command 'uv run <python_file.py>' ",
                  "do not use the shell for the command that can make changes in the project structure",
                  "do not delete any file",
                  "just use it to read the project structure ,file or to run file"],
    tools=[ShellTools(base_dir=base_dir)]
)

#======================================DataScience-Team========================================





if __name__=="__main__":
    pass