import os
import operator
from typing import Annotated, List, Dict, TypedDict, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# Load env variables (Ensure OPENAI_API_KEY is set in your environment)
# from dotenv import load_dotenv
# load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# --- THE SHARED STATE ---
# This dictionary holds all data flowing between agents
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage]], operator.add]
    user_profile: Dict  # Stores likes/dislikes, allergies
    health_data: Dict   # Stores glucose, energy levels
    journal_entry: str  # Current journal text being analyzed
    detected_triggers: List[str] # Output from Trigger Detective
    final_plan: str     # The output recommendation

# --- 1. PREFERENCE AGENT ---
# Updates the user profile based on conversation
def preference_agent(state: AgentState):
    print("--- PREFERENCE AGENT WORKING ---")
    messages = state['messages']
    current_profile = state.get('user_profile', {})
    
    # Prompt to extract preferences
    system_msg = f"""
    You are a Preference Learning Agent. 
    Current Profile: {current_profile}
    Analyze the conversation history. If the user mentions food likes, dislikes, or dietary restrictions, 
    update the profile JSON. Return ONLY the updated JSON profile.
    """
    
    response = llm.invoke([SystemMessage(content=system_msg)] + messages)
    
    # In a real app, parse the JSON properly. Here we mock a simple extraction.
    # For the hackathon, you can use structured output/function calling here.
    return {"user_profile": current_profile} # Placeholder for actual update logic


# --- 2. TRIGGER DETECTIVE ---
# Analyzes journal entries for emotional/environmental triggers
def trigger_detective(state: AgentState):
    print("--- TRIGGER DETECTIVE WORKING ---")
    journal = state.get('journal_entry', "")
    
    if not journal:
        return {"detected_triggers": []}

    prompt = f"""
    Analyze this journal entry for eating triggers (Stress, Boredom, Social pressure, Low Energy).
    Journal: "{journal}"
    Return a comma-separated list of triggers detected.
    """
    response = llm.invoke(prompt)
    triggers = [t.strip() for t in response.content.split(',')]
    
    return {"detected_triggers": triggers}


# --- 3. NUTRITIONIST AGENT ---
# Adjusts meal suggestions based on health data and triggers
def nutritionist_agent(state: AgentState):
    print("--- NUTRITIONIST AGENT WORKING ---")
    profile = state.get('user_profile', {})
    health = state.get('health_data', {})
    triggers = state.get('detected_triggers', [])
    
    prompt = f"""
    You are an expert Dietitian.
    User Profile: {profile}
    Health Data: Glucose trend is {health.get('glucose_trend')}, Energy is {health.get('energy_level')}.
    Detected Triggers: {triggers}
    
    Task: Suggest a specific meal and explain WHY it helps with the current glucose/energy state.
    If stress is detected, suggest comfort foods that are still healthy.
    """
    
    response = llm.invoke(prompt)
    return {"final_plan": response.content}


# --- 4. LOGISTICS AGENT ---
# Handles the "doing" part (Scheduling/Groceries)
def logistics_agent(state: AgentState):
    print("--- LOGISTICS AGENT WORKING ---")
    plan = state.get('final_plan', "")
    
    # Mocking a tool call
    schedule_result = "Added meal prep to Calendar for Sunday at 5 PM."
    grocery_result = "Added ingredients to Instacart cart."
    
    final_output = f"{plan}\n\n[Logistics]: {schedule_result} | {grocery_result}"
    
    return {"messages": [AIMessage(content=final_output)]}

def router(state: AgentState):
    # Logic: If the user provides a journal entry, go to detective.
    # If they are just chatting, go to preference learner.
    last_message = state['messages'][-1].content.lower()
    
    if "journal" in last_message or "feeling" in last_message:
        return "trigger_detective"
    else:
        return "preference_agent"

  workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("preference_agent", preference_agent)
workflow.add_node("trigger_detective", trigger_detective)
workflow.add_node("nutritionist_agent", nutritionist_agent)
workflow.add_node("logistics_agent", logistics_agent)

# Set Entry Point (Conditional)
workflow.set_conditional_entry_point(
    router,
    {
        "trigger_detective": "trigger_detective",
        "preference_agent": "preference_agent"
    }
)

# Define Edges (The Flow)
# After preferences are updated, we might want to just end or suggest food.
# For this demo, let's route everything to the Nutritionist to give immediate value.
workflow.add_edge("preference_agent", "nutritionist_agent")
workflow.add_edge("trigger_detective", "nutritionist_agent")

# After Nutritionist decides the meal, Logistics handles the prep
workflow.add_edge("nutritionist_agent", "logistics_agent")

# End
workflow.add_edge("logistics_agent", END)

# Compile
app = workflow.compile()

if __name__ == "__main__":
    # --- SCENARIO 1: JOURNAL ENTRY WITH STRESS & LOW ENERGY ---
    print("\n\n### SCENARIO: Stress Eating Detection ###")
    
    initial_state = {
        "messages": [HumanMessage(content="Here is my journal: I've been so stressed with work today, and my energy crashed around 3pm. I just want to eat pizza.")],
        "user_profile": {"name": "Alex", "diet": "Low Carb", "allergies": ["Peanuts"]},
        "health_data": {"glucose_trend": "Spiking", "energy_level": "Low"},
        "journal_entry": "I've been so stressed with work today, and my energy crashed around 3pm. I just want to eat pizza."
    }

    result = app.invoke(initial_state)
    
    print("\n--- FINAL AGENT RESPONSE ---")
    print(result['messages'][-1].content)
