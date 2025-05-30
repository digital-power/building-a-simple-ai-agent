# A basic example on how to build an AI Agent using OpenAI enpoints in Azure

This tutorial provides a basic example of how an AI agent can be build using Azure OpenAI endpoints.
For the full article refer to the digital power website: [Building an AI Agent with Azure OpenAI](https://digitalpower.com/building-an-ai-agent-with-azure-openai/).

---

## Getting Started

### Prerequisites
1. **Python 3.13** or higher.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your Azure credentials in `config/settings.yaml`.

Running the AI Agent
1. Start the AI Agent by running the `ai_agent.py` script:
   ```python
   python ai_agent.py
   ```
2. The agent will prompt you for input. You can ask it to perform tasks related to blob listing or any other general
 inquiries.

## Usage

Commands
- Ask a Question: Type your query, and the assistant will respond.
- Exit the Conversation: Type `exit` or `quit` to quit.

Example Interactions
1. List Files in Azure Blob Storage:
    ```
    Human User: List files in the dls Azure Blob Storage container.
    AI assitant: Here are the files in the container:
    - file1.csv
    - file2.xlsx
    ```

## Configuration

`config/settings.yaml` contains the configuration for Azure Blob Storage, Databricks, and other tools. Update it with your credentials and settings.

```yaml
azure_openai:
    endpoint: "https://your-openai-resource-name.openai.azure.com/"
    model_name: "gpt-4"
    deployment: "gpt-4-deployment"
    api_key: "your-azure-openai-api-key"
    api_version: "2024-12-01-preview"

azure_blob:
    connection_string: "DefaultEndpointsProtocol=https;AccountName=youraccountname;AccountKey=youraccountkey;EndpointSuffix=core.windows.net"
    default_container: "dls"

```
