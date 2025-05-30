import sys
import json
from typing import Optional
import logging
import yaml

import openai
from azure.storage.blob import ContainerClient
from azure.core import exceptions as azure_exceptions

# Quick logger setup
logger = logging.Logger("AI agent", level=logging.DEBUG)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(levelname)s : %(message)s"))
logger.addHandler(stdout_handler)

# configuration file path
config_path = "config/settings.yaml"

# Load configuration from settings.yaml file
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Azure OpenAI and Blob Storage credentials/configuration
llm_endpoint = config["azure_openai"]["endpoint"]
model_name = config["azure_openai"]["model_name"]
deployment = config["azure_openai"]["deployment"]
api_key = config["azure_openai"]["api_key"]
api_version = config["azure_openai"]["api_version"]

connection_string = config["azure_blob"]["connection_string"]
default_container = config["azure_blob"]["default_container"]

# Function to list all blob files in a given Azure Blob Storage container
def list_blob_files(container_name: Optional[str] = None) -> dict:
    # Use default container if none provided
    if container_name in [None, "", "{}"]:
        container_name = default_container

    # Ensure container_name is a string
    if not isinstance(container_name, str):
        container_name = str(container_name)

    logger.debug(f"Listing blobs in container: '{container_name}'")

    # Create a ContainerClient to interact with the specified container
    container_client = ContainerClient.from_connection_string(
        conn_str=connection_string,
        container_name=container_name
    )

    blob_list = container_client.list_blobs()
    try:
        # Collect all blob names in the container
        files = [blob.name for blob in blob_list]
        logger.debug(f"Found {len(files)} files in container.")
        status = "success"
    except azure_exceptions.HttpResponseError as e:
        # Handle errors from Azure
        logger.error(f"Error listing blobs from container '{container_name}': {e}")
        status = "error"
        files = []

    return {"container_name": container_name, "status": status, "files": files}

# Tool description for OpenAI function calling
tools_description = [
    {
        "type": "function",
        "function": {
            "name": "list_blob_files",
            "description":
                "List all files in a specified Azure Blob Storage container. If no container is " \
                "specified, the default container will be used.",
            "parameters": {
                "type": "object",
                "properties": {
                    "container_name": {
                        "type": "string",
                        "description": "(Optional) The name of the Azure Blob Storage container."
                    }
                },
            #"required": ["container_name"] # If you want to make this a manbdatory field, uncomment this line
            # and update the function definition accordingly.
            }
        }
    }]

# Initialize the Azure OpenAI client
ai_client = openai.AzureOpenAI(
    api_version=api_version,
    azure_endpoint=llm_endpoint,
    api_key=api_key,
    )

# Start the conversation with a system prompt
conversation = [
    {"role": "system", "content": "You are a helpful assistant."}
]

# Main chat loop
while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    # Add user message to conversation history
    conversation.append({"role": "user", "content": user_input})

    # Send conversation to Azure OpenAI and get a response
    response = ai_client.chat.completions.create(
        messages=conversation,
        tools=tools_description,
        model=deployment,
        max_completion_tokens=1000)

    # Check if the response contains tool calls (function calls)
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        logger.debug(f"Function call: {function_name} with arguments: {arguments}")

        if function_name == "list_blob_files":
            # Call the Python function and get the result

            tool_result = list_blob_files(**arguments)
            logger.debug(f"Tool result: {tool_result}")

            # Add the assistant's function call to the conversation
            conversation.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": function_name,
                        "arguments": json.dumps(arguments)
                    }
                }]
            })

            # Add the tool's result to the conversation
            conversation.append({
                "role": "tool",
                "content": json.dumps(tool_result),
                "tool_call_id": tool_call.id
            })

            # Get the assistant's final response after the tool call
            final_response = ai_client.chat.completions.create(
                messages=conversation,
                tools=tools_description,
                model=deployment,
                max_completion_tokens=1000
                )

            reply = final_response.choices[0].message.content
            print(f"Assistant: {reply}")
            conversation.append({"role": "assistant", "content": reply})

        else:
            logger.error(f"Unknown function call: {function_name}")
    else:

        # If no tool call, just print the assistant's reply
        reply = response.choices[0].message.content
        print(f"Assistant: {reply}")
        conversation.append({"role": "assistant", "content": reply})

# Save the conversation history to a file at the end
with open("conversation_history.json", "w") as f:
    json.dump(conversation, f, indent=4)
