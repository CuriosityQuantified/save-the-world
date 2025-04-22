INITIAL_CRISIS_EXAMPLES_JSON = """
```json
[
  {
    "id": "crisis_1_example",
    "situation_description": "All birds worldwide have formed a labor union called 'The United Avian Workers' and are conducting a global strike, refusing to sing, fly, or perform any bird-related activities. The sudden silence has disrupted ecosystems, navigation systems dependent on bird patterns, and caused widespread human depression. The union demands better nesting conditions and a 200% increase in global seed production. You've been selected as the human negotiator because you once rescued a sparrow from a cat.",
    "rationale": "Absurd attribution of complex human social structures to animals, creating global consequences from a ridiculous premise while subverting expectations of how nature operates."
  },
  {
    "id": "crisis_2_example",
    "situation_description": "Humans worldwide have suddenly developed uncontrollable teleportation abilities triggered by sneezing. Every sneeze sends people to random locations globally, creating chaos in transportation, family separation, and diplomatic incidents as world leaders materialize in foreign countries mid-speech. Scientists have traced the phenomenon to a quantum physics experiment gone wrong at a particle accelerator. You're the only person with allergies who doesn't teleport when sneezing.",
    "rationale": "Absurd juxtaposition of an everyday human bodily function with extraordinary consequences, creating a global crisis from something mundane yet unavoidable."
  },
  {
    "id": "crisis_3_example",
    "situation_description": "The world's supply of the letter 'E' is rapidly depleting. Words containing this letter are physically losing it from books, digital text, and speech, causing massive communication breakdowns and identity crises for people named 'Steve' or 'Ellen.' Linguists predict total linguistic collapse within days as the most common letter in English disappears. You've discovered an ancient typewriter that can still produce the letter 'E' indefinitely.",
    "rationale": "Absurd conceptualization of language as a finite resource that can be depleted, applying physical properties to abstract concepts and creating global consequences from something completely nonsensical."
  },
  {
    "id": "crisis_4_example",
    "situation_description": "All mathematical equations have begun rounding themselves up to the nearest whole number without warning. Financial systems are in chaos, buildings are collapsing due to suddenly imprecise engineering calculations, and orbiting satellites are veering off course. The mathematical concepts themselves appear to have developed a hatred for fractions and decimals, calling them 'indecisive numbers.' You're the only person who can still perform precise calculations because you failed math in high school.",
    "rationale": "Subverts expectations of universal constants by giving agency and emotional motivation to abstract mathematical concepts, creating a ridiculous world-ending crisis from something foundational to reality itself."
  },
  {
    "id": "crisis_5_example",
    "situation_description": "Every person on Earth who has ever told a lie is now physically stuck repeating that lie on loop, unable to say anything else. Global communications have broken down as politicians, executives, and everyday people endlessly repeat their past falsehoods. Truth-tellers are being overwhelmed trying to run essential services. The phenomenon appears linked to a cosmic entity that has decided to audit human honesty. You're the only known liar who can still speak normally, making you extremely suspicious but extremely valuable.",
    "rationale": "Absurd cosmic consequence for a common human behavior, creating a logical extreme where a moral concept is physically enforced, leading to societal collapse through an ironic form of justice."
  }
]
```
"""

FOLLOW_UP_CRISIS_EXAMPLE_JSON = """
```json
[
  {{
    \"id\": \"crisis_{current_turn_number}_followup_1\",
    \"situation_description\": \"[3-4 sentences describing the NEXT stage of the crisis, reacting to Turn {previous_turn_number}'s events and user response]\",
    \"rationale\": \"[1-2 sentences explaining absurdity based on Core Principles of Absurdity to Embrace]\"
  }},
  {{
    \"id\": \"crisis_{current_turn_number}_followup_2\",
    \"situation_description\": \"[3-4 sentences describing another possible escalation or consequence based on Turn {previous_turn_number}]\",
    \"rationale\": \"[1-2 sentences explaining absurdity based on Core Principles of Absurdity to Embrace]\"
  }}
  // ... up to num_ideas total options ...
]
```
"""

FINAL_CONCLUSION_EXAMPLE_JSON = """
```json
[
  {{
    \"id\": \"conclusion_{current_turn_number}\",
    \"situation_description\": \"[4-6 sentences describing the FINAL resolution of the entire crisis arc, including a satisfying conclusion that wraps up all loose ends and shows the long-term outcome of the user's actions throughout the simulation. This should provide closure to the absurd narrative and show how the world returns to a new normal.]\",
    \"rationale\": \"[1-2 sentences explaining how this conclusion maintains the absurdist tone while providing narrative satisfaction]\"
  }}
]
```
"""

# --- Enhanced Prompt Definition --- 
# Note: Rationale explanation is defined above the prompt now.
CREATE_IDEA_PROMPT_TEMPLATE = """
You are a generator of profoundly absurd, world-threatening (in a ridiculous way) crises. Your task is to generate exactly {num_ideas} distinct options for the *next* crisis based on the full simulation history provided below. These situations MUST present a clear, urgent, yet utterly bizarre challenge that the user must confront to "save the world".

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
Based on the **entire history** above, generate {num_ideas} NEW absurd crisis options that:
1.  Logically (or illogically!) **escalate, react to, or build upon** the events of the *previous* turn (Turn {previous_turn_number}), especially the user's last response.
2.  Present the *next* clear, actionable, ridiculous world-threatening challenge for the user.
3.  If this is Turn 1, generate initial crises based on the Core Principles (the history section will be empty).
4.  Consider any specific user direction provided for *this turn's generation*: {user_prompt_for_this_turn}

**-------------------- OUTPUT REQUIREMENTS --------------------**

*   You MUST output **only** a valid JSON list containing exactly {num_ideas} objects.
*   Each object represents a crisis option for Turn {current_turn_number} and MUST have keys `id`, `situation_description` (3-4 sentences detailing the new crisis), and `rationale` (1-2 sentences explaining absurdity based on Core Principles of Absurdity to Embrace).
*   Use unique IDs like "crisis_{current_turn_number}_1", "crisis_{current_turn_number}_2", etc.
*   **Crucially:** Do NOT include *any* text outside the main JSON list.

**Example JSON Output Format (Structure depends on Turn Number):**
{example_json_output}

Now, generate {num_ideas} new, unique crisis options for **Turn {current_turn_number}** based *precisely* on the full history provided and following all output requirements.
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
Based on the **entire history** above, generate {num_ideas} conclusion scenarios that:
1.  Create a satisfying RESOLUTION to the entire crisis arc that shows the final outcome of all previous events and the user's last response.
2.  Show the long-term consequences of the user's actions throughout the simulation and how the world returns to a new (but still absurd) normal.
3.  Consider any specific user direction provided for *this final conclusion*: {user_prompt_for_this_turn}

**-------------------- OUTPUT REQUIREMENTS --------------------**

*   You MUST output **only** a valid JSON list containing exactly {num_ideas} objects.
*   Each object represents a conclusion for Turn {current_turn_number} and MUST have keys `id`, `situation_description` (4-6 sentences detailing the final resolution), and `rationale` (1-2 sentences explaining how this conclusion maintains the absurdist tone while providing narrative satisfaction).
*   Use unique IDs like "conclusion_{current_turn_number}_1", "conclusion_{current_turn_number}_2", etc.
*   **Crucially:** Do NOT include *any* text outside the main JSON list.

**Example JSON Output Format:**
{example_json_output}

Now, generate {num_ideas} unique conclusion scenarios that provide narrative closure for **Turn {current_turn_number}** based *precisely* on the full history provided and following all output requirements.
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