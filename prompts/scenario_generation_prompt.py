"""
Scenario Generation Prompt Module

This module contains the prompt templates and logic for generating
scenarios at different stages of the simulation.
"""

# For direct import by llm_service.py, these will be used internally without going through __init__
from prompts.initial_crisis_examples import RATED_EXAMPLES_JSON, UNRATED_EXAMPLES_JSON
from prompts.follow_up_crisis_examples import FOLLOW_UP_CRISIS_EXAMPLE_JSON
from prompts.conclusion_examples import FINAL_CONCLUSION_EXAMPLE_JSON

# --- Enhanced Prompt Definition --- 
# Note: Rationale explanation is defined above the prompt now.
CREATE_IDEA_PROMPT_TEMPLATE = """
You are a generator of profoundly absurd, world-threatening (in a ridiculous way) crises. Your task is to generate a single engaging crisis based on the full simulation history provided below. This situation MUST present a clear, urgent, yet utterly bizarre challenge that the user must confront to "save the world".

**Core Principles of Absurdity to Embrace:**
*   **Unexpected Juxtapositions:** Combine mundane elements with cosmic stakes (e.g., sentient lint bunnies controlling global economies, existential dread dish soap threatening the space-time continuum).
*   **Logical Extremes:** Take a simple, silly premise and escalate it to a preposterous, world-ending conclusion (e.g., a single misplaced sock causing reality to unravel).
*   **Subversion of Expectations:** Defy common sense, natural laws, and predictable narrative structures in ways that create global peril (e.g., gravity becoming politely suggestive instead of mandatory).
*   **Meaninglessness (with a wink):** Create crises that seem monumentally urgent but are rooted in something fundamentally trivial or pointless, highlighting the absurdity of existence.
*   **Ridiculous World-Ending Crises:** The threat must be global or reality-altering, but its *cause* or *nature* should be fundamentally silly, nonsensical, or bizarre. The fate of the world hangs by a comical thread.

**-------------------- FULL SIMULATION HISTORY SO FAR --------------------**
{simulation_history}
**-------------------- END OF HISTORY --------------------**

**Your Task for Turn {current_turn_number}:**
Based on the **entire history** above, generate a NEW absurd crisis that:
1.  Logically (or illogically!) **escalates, reacts to, or builds upon** the events of the *previous* turn (Turn {previous_turn_number}), especially the user's last response.
2.  Presents the *next* clear, actionable, ridiculous world-threatening challenge for the user.
3.  If this is Turn 1, generate an initial crisis based on the Core Principles (the history section will be empty).
4.  Consider any specific user direction provided for *this turn's generation*: {user_prompt_for_this_turn}

**-------------------- OUTPUT REQUIREMENTS --------------------**

*   You MUST output **only** a valid JSON object.
*   The object represents a crisis for Turn {current_turn_number} and MUST have keys:
    - `id`: A unique identifier for this crisis (format: "scenario_{current_turn_number}_1")
    - `situation_description`: 3-4 sentences detailing the new crisis
    - `user_role`: 1 sentence establishing the user's specific role in addressing the crisis
    - `user_prompt`: 1 clear question asking the user for their plan or approach
    - `rationale`: 1-2 sentences explaining absurdity based on Core Principles
*   **Crucially:** Do NOT include *any* text outside the JSON object.

**Example JSON Output Format:**
{example_json_output}

Now, generate a new, unique crisis for **Turn {current_turn_number}** based *precisely* on the full history provided and following all output requirements.
"""

# Final turn conclusion prompt template
FINAL_TURN_TEMPLATE = """
You are a generator of profoundly absurd, world-threatening (in a ridiculous way) crises. Your task is to generate a grand finale and conclusion for an absurd narrative based on the full simulation history provided below. This should provide a satisfying ending to the story.

**Core Principles of Absurdity to Embrace:**
*   **Unexpected Juxtapositions:** Combine mundane elements with cosmic stakes (e.g., sentient lint bunnies controlling global economies, existential dread dish soap threatening the space-time continuum).
*   **Logical Extremes:** Take a simple, silly premise and escalate it to a preposterous, world-ending conclusion (e.g., a single misplaced sock causing reality to unravel).
*   **Subversion of Expectations:** Defy common sense, natural laws, and predictable narrative structures in ways that create global peril (e.g., gravity becoming politely suggestive instead of mandatory).
*   **Meaninglessness (with a wink):** Create crises that seem monumentally urgent but are rooted in something fundamentally trivial or pointless, highlighting the absurdity of existence.
*   **Satisfying Resolution:** While maintaining absurdity, provide an actual sense of closure and resolution to the entire narrative arc.

**-------------------- FULL SIMULATION HISTORY SO FAR --------------------**
{simulation_history}
**-------------------- END OF HISTORY --------------------**

**Your Task for the FINAL TURN {current_turn_number}:**
Based on the **entire history** above, generate a conclusion scenario that:
1.  Creates a satisfying RESOLUTION to the entire crisis arc that shows the final outcome of all previous events and the user's last response.
2.  Shows the long-term consequences of the user's actions throughout the simulation and how the world returns to a new (but still absurd) normal.
3.  Considers any specific user direction provided for *this final conclusion*: {user_prompt_for_this_turn}
4.  Based on how well the user has done over the past turns, the situation could completely resolve back to normal, or there could be externalities that persist because it either wasn't fully resolved or a response they used created some sort of longer lasting effect. 

**-------------------- OUTPUT REQUIREMENTS --------------------**

*   You MUST output **only** a valid JSON object.
*   The object represents a conclusion for Turn {current_turn_number} and MUST have keys:
    - `id`: A unique identifier for this conclusion (format: "scenario_{current_turn_number}_1")
    - `level_of_resolution`: A float on 1-10 scale with 10 being perfectly back to normal and 1 being catastrophic disaster
    - `situation_description`: 4-6 sentences detailing the final resolution
    - `user_role`: 1 sentence establishing the user's final role in witnessing or influencing the resolution
    - `user_prompt`: 1 clear question asking how the user wants to address this final stage
    - `rationale`: 1-2 sentences explaining how this conclusion maintains the absurdist tone while providing narrative satisfaction
*   **Crucially:** Do NOT include *any* text outside the JSON object.

**Example JSON Output Format:**
{example_json_output}

Now provide your JSON output for the final turn:
"""

def get_formatted_prompt_template(current_turn_number, max_turns):
    """
    Returns the appropriate prompt template based on whether this is the final turn.
    
    Args:
        current_turn_number: The current turn number
        max_turns: The maximum number of turns in the simulation
        
    Returns:
        The appropriate prompt template
    """
    if current_turn_number == max_turns:
        return FINAL_TURN_TEMPLATE
    else:
        return CREATE_IDEA_PROMPT_TEMPLATE