import openai
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict  

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

# Check if the API key is available
if not openai.api_key:
    raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")

# Define State structure for memory
class State(TypedDict):
    messages: list
    memory: list

# Initialize the StateGraph and MemorySaver
graph_builder = StateGraph(State)
memory_saver = MemorySaver()

# Function to get a response from OpenAI's API
def get_openai_response(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Sorry, I encountered an error: {e}"

# Chatbot logic with memory handling (using MemorySaver for memory)
def chatbot(state: State):
    # Retrieve memory and user input from the state
    memory = state.get("memory", [])
    user_input = state["messages"][-1].strip()  # Get the last user input

    # Add user input to memory (conversation history)
    memory.append(f"User: {user_input}")

    # Create a prompt with context (conversation history + current user input)
    conversation_context = "\n".join(memory)
    response = get_openai_response(conversation_context + "\nAssistant:")

    # Add assistant's response to memory
    memory.append(f"Assistant: {response}")

    # Update the state with the latest memory
    state["memory"] = memory

    return {"messages": [response]}

# Define the chatbot node and entry/exit points
graph_builder.add_node("chatbot", chatbot)
graph_builder.set_entry_point("chatbot")
graph_builder.set_finish_point("chatbot")

# Compile the graph with MemorySaver as the checkpointer
graph = graph_builder.compile(checkpointer=memory_saver)

# Example interactive loop
state = {"messages": [], "memory": []}

# Initial message
print("Bot: Hi there! What would you like to talk about? (Type 'bye' to end)")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["bye"]:
        print("Bot: Thank you for chatting! Bye!")
        break
    state["messages"].append(user_input)  # Add user input to the state
    result = chatbot(state)  # Get chatbot response
    print("Bot:", result["messages"][0])  # Print bot response
