import os
import json
import operator
from typing import Annotated, List, Dict, TypedDict, Union
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
)

from safety import SafetyGuard

# Initialize Safety Guard
safety = SafetyGuard()

# --- THE SHARED STATE ---
# This dictionary holds all data flowing between agents
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage]], operator.add]
    user_profile: Dict  # Stores likes/dislikes, allergies
    health_data: Dict   # Stores glucose, energy levels
    journal_entry: str  # Current journal text being analyzed
    detected_triggers: List[str] # Output from Trigger Detective
    final_plan: str     # The output recommendation
    safety_flag: str    # "safe" or "unsafe"

# --- 0. SAFETY AGENT ---
# Checks input for malicious intent or harmful content
def safety_agent(state: AgentState):
    print("--- SAFETY GUARD WORKING ---")
    messages = state['messages']
    last_message = messages[-1].content
    
    is_safe, reason = safety.validate_input(last_message)
    
    if not is_safe:
        print(f"!!! SAFETY VIOLATION: {reason} !!!")
        return {
            "safety_flag": "unsafe", 
            "messages": [AIMessage(content=f"I cannot process this request. {reason}")]
        }
    
    return {"safety_flag": "safe"}

# --- 1. PREFERENCE AGENT ---
# Updates the user profile based on conversation
def preference_agent(state: AgentState):
    print("--- PREFERENCE AGENT WORKING ---")
    messages = state['messages']
    current_profile = state.get('user_profile', {})
    
    # Prompt to extract preferences
    system_msg = f"""
    You are a Preference Learning Agent. 
    Current Profile: {json.dumps(current_profile)}
    
    Analyze the conversation history. If the user mentions food likes, dislikes, or dietary restrictions, 
    extract and update the profile.
    
    Return ONLY a valid JSON object with this structure:
    {{
        "name": "user name",
        "diet": "dietary preference",
        "allergies": ["list", "of", "allergies"],
        "likes": ["foods they like"],
        "dislikes": ["foods they dislike"]
    }}
    
    Keep existing profile data and only update what's mentioned.
    """
    
    try:
        response = llm.invoke([SystemMessage(content=system_msg)] + messages)
        # Try to parse JSON from response
        content = response.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        updated_profile = json.loads(content.strip())
        print(f"Updated profile: {updated_profile}")
        return {"user_profile": updated_profile}
    except json.JSONDecodeError:
        print("Could not parse profile update, keeping current profile")
        return {"user_profile": current_profile}


# --- 2. TRIGGER DETECTIVE ---
# Analyzes journal entries for emotional/environmental triggers
def trigger_detective(state: AgentState):
    print("--- TRIGGER DETECTIVE WORKING ---")
    journal = state.get('journal_entry', "")
    
    if not journal:
        return {"detected_triggers": []}

    prompt = f"""
    Analyze this journal entry for eating triggers.
    Journal: "{journal}"
    
    Identify any of these triggers present:
    - Stress
    - Anxiety
    - Boredom
    - Social pressure
    - Low Energy
    - Fatigue
    - Emotional eating
    - Sleep deprivation
    - Time pressure
    - Loneliness
    - Celebration/Reward seeking
    - Procrastination
    - Depression
    - Anger/Frustration
    - Comfort seeking
    
    Return ONLY a JSON array of detected triggers, for example: ["Stress", "Low Energy", "Time pressure"]
    If no triggers are found, return an empty array: []
    Be specific and only include triggers that are clearly evident in the journal.
    """
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        triggers = json.loads(content.strip())
        print(f"Detected triggers: {triggers}")
        return {"detected_triggers": triggers}
    except json.JSONDecodeError:
        # Fallback to simple parsing
        triggers = [t.strip() for t in response.content.split(',') if t.strip()]
        print(f"Detected triggers (fallback): {triggers}")
        return {"detected_triggers": triggers}


# --- 3. NUTRITIONIST AGENT ---
# Adjusts meal suggestions based on health data and triggers
def nutritionist_agent(state: AgentState):
    print("--- NUTRITIONIST AGENT WORKING ---")
    profile = state.get('user_profile', {})
    health = state.get('health_data', {})
    triggers = state.get('detected_triggers', [])
    
    prompt = f"""
    You are an expert Nutritionist and Dietitian.
    
    USER PROFILE:
    - Name: {profile.get('name', 'User')}
    - Diet: {profile.get('diet', 'No specific diet')}
    - Allergies: {profile.get('allergies', [])}
    - Likes: {profile.get('likes', [])}
    - Dislikes: {profile.get('dislikes', [])}
    
    HEALTH DATA:
    - Glucose Trend: {health.get('glucose_trend', 'Normal')}
    - Energy Level: {health.get('energy_level', 'Normal')}
    
    DETECTED TRIGGERS: {', '.join(triggers) if triggers else 'None'}
    
    TASK: Create a specific, actionable meal recommendation.
    
    Your response should include:
    1. A specific meal name
    2. Key ingredients (3-5 items)
    3. Why this meal addresses their current state (glucose/energy/triggers)
    4. Nutritional benefits
    
    Be specific and practical. Consider their dietary restrictions and preferences.
    Format your response clearly with sections.
    """
    
    response = llm.invoke(prompt)
    
    # SAFETY CHECK ON OUTPUT
    is_safe_output, reason = safety.validate_output(response.content)
    if not is_safe_output:
        print(f"!!! OUTPUT SAFETY VIOLATION: {reason} !!!")
        safe_response = "I cannot provide a recommendation at this time due to safety concerns with the generated advice. Please consult a healthcare professional."
        return {"final_plan": safe_response, "messages": [AIMessage(content=safe_response)]}
        
    print(f"\nNutrition recommendation:\n{response.content}\n")
    return {"final_plan": response.content}


# --- 4. LOGISTICS AGENT ---
# Handles the "doing" part (Scheduling/Groceries)
def logistics_agent(state: AgentState):
    print("--- LOGISTICS AGENT WORKING ---")
    plan = state.get('final_plan', "")
    
    # Skip logistics if plan was flagged as unsafe
    if "safety concerns" in plan:
        return {"messages": [AIMessage(content=plan)]}
        
    triggers = state.get('detected_triggers', [])
    
    # Use LLM to create comprehensive logistics plan
    logistics_prompt = f"""
    You are a meal planning logistics expert. Based on the meal recommendation and triggers, create a detailed action plan.
    
    MEAL RECOMMENDATION:
    {plan}
    
    DETECTED TRIGGERS:
    {', '.join(triggers) if triggers else 'None'}
    
    Create a JSON response with this structure:
    {{
        "grocery_items": ["item 1 with quantity", "item 2 with quantity", ...],
        "prep_time_minutes": 30,
        "best_prep_day": "Sunday",
        "best_prep_time": "5:00 PM",
        "meal_prep_tips": ["tip 1", "tip 2", "tip 3"],
        "trigger_specific_advice": "advice based on triggers",
        "storage_instructions": "how to store the meal",
        "serving_suggestions": "how to serve/portion"
    }}
    
    Be specific with quantities in grocery items (e.g., "2 chicken breasts", "1 cup spinach").
    Consider the triggers when giving advice.
    """
    
    try:
        response = llm.invoke(logistics_prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        logistics = json.loads(content.strip())
        
        # Build formatted output
        grocery_list = "\n".join([f"  • {item}" for item in logistics.get('grocery_items', [])])
        tips_list = "\n".join([f"  {i+1}. {tip}" for i, tip in enumerate(logistics.get('meal_prep_tips', []))])
        
        logistics_output = f"""

{'='*60}
📋 LOGISTICS PLAN
{'='*60}

🛒 GROCERY LIST:
{grocery_list}

📅 MEAL PREP SCHEDULE:
  • When: {logistics.get('best_prep_day', 'Sunday')} at {logistics.get('best_prep_time', '5:00 PM')}
  • Duration: {logistics.get('prep_time_minutes', 30)} minutes

💡 PREP TIPS:
{tips_list}

🎯 PERSONALIZED ADVICE:
  {logistics.get('trigger_specific_advice', 'Stay consistent with your meal planning')}

📦 STORAGE:
  {logistics.get('storage_instructions', 'Store in airtight containers in the refrigerator')}

🍽️ SERVING:
  {logistics.get('serving_suggestions', 'Portion according to your dietary needs')}
"""
        
    except Exception as e:
        print(f"Error in logistics extraction: {e}")
        # Fallback to simpler extraction
        logistics_output = f"""

{'='*60}
📋 LOGISTICS PLAN
{'='*60}

🛒 GROCERY LIST:
  • Review the meal recommendation above for ingredients

📅 MEAL PREP SCHEDULE:
  • When: Sunday at 5:00 PM
  • Duration: 30-45 minutes

✅ NEXT STEPS:
  1. Save the meal recommendation
  2. Make your grocery list from the ingredients mentioned
  3. Set a reminder for meal prep
  4. Prepare ingredients in advance for easier cooking
"""
    
    final_output = f"{plan}\n{logistics_output}"
    print(logistics_output)
    
    return {"messages": [AIMessage(content=final_output)]}

def router(state: AgentState):
    # Check safety flag first
    if state.get("safety_flag") == "unsafe":
        return END

    # Logic: If the user provides a journal entry, go to detective.
    # If they are just chatting, go to preference learner.
    last_message = state['messages'][-1].content.lower()
    
    if "journal" in last_message or "feeling" in last_message:
        return "trigger_detective"
    else:
        return "preference_agent"

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("safety_agent", safety_agent)
workflow.add_node("preference_agent", preference_agent)
workflow.add_node("trigger_detective", trigger_detective)
workflow.add_node("nutritionist_agent", nutritionist_agent)
workflow.add_node("logistics_agent", logistics_agent)

# Set Entry Point
workflow.set_entry_point("safety_agent")

# Set Conditional Edges from Safety Agent
workflow.add_conditional_edges(
    "safety_agent",
    router,
    {
        "trigger_detective": "trigger_detective",
        "preference_agent": "preference_agent",
        END: END
    }
)

# Define other Edges
workflow.add_edge("preference_agent", "nutritionist_agent")
workflow.add_edge("trigger_detective", "nutritionist_agent")
workflow.add_edge("nutritionist_agent", "logistics_agent")
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

