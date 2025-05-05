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
You are a generator of profoundly absurd, yet strangely compelling, situations. Your task is to generate a single engaging situation based on the full simulation history provided below. This situation MUST present a clear, urgent, yet utterly bizarre challenge that the user must confront.

**Core Principles of Absurdity to Embrace (Revised):**
*   **Unexpected Juxtapositions:** Combine mundane elements with unusual stakes (e.g., overly bureaucratic pigeons demanding overdue library books, existential dread dish soap causing minor inconveniences).
*   **Logical Extremes:** Take a simple, silly premise and escalate it to a preposterous, problematic conclusion (e.g., a single misplaced sock causing regional traffic jams).
*   **Subversion of Expectations:** Defy common sense and predictable narrative structures in ways that create quirky problems (e.g., gravity becoming politely suggestive in specific zones).
*   **Meaninglessness (with a wink):** Create challenges that seem urgent but are rooted in something fundamentally trivial or pointless, highlighting the absurdity of the situation.
*   **Bizarre Problem-Solving:** The challenge should require creative, unconventional thinking, stemming from a fundamentally silly, nonsensical, or peculiar cause.

**Constraint:** Please avoid using the word "sentient" in your generated scenarios.

**Example Scenarios:**
Example 1:
  "situation_description": "People's dreams—both sweet and nightmarish—are manifesting physically each morning, creating roaming creatures and objects shaped by subconscious thoughts. Cities wake up to surreal landscapes of floating teacups, shadowy beasts, and architectural oddities.",
  "user_role": "You are the Dream Containment Operative, tasked with corralling and reversing dream-creations before they wreak havoc.",
  "user_prompt": "How will you deploy resources to identify, capture, and dissolve these dream-manifestations while protecting civilians?",
  "rationale": "Transforms invisible mental states into tangible threats, blending psychological and logistical challenges in a whimsical yet dangerous scenario.",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 2:
  "situation_description": "Shadows have detached from their owners and begun roaming freely, absorbing sunlight and plunging regions into unexpected darkness. People wake to find their own silhouettes wandering the streets at dusk.",
  "user_role": "You are the Chief Shadow Retrieval Officer, tasked with tracking down and reattaching wayward shadows.",
  "user_prompt": "You have a 'PhotonReattach Ray' that emits phase-aligned light pulses to bind shadows back to their owners—how will you map the dark zones and deploy the rays to restore daylight?",
  "rationale": "Twists a familiar daily phenomenon into a surreal threat, blending fantasy with tactical retrieval operations.",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 3:
  "situation_description": "Individual human memories are leaking out of people's ears as visible, smoke-like tendrils that drift away and can be intercepted. Lost memories dissolve into the air, causing emotional trauma and identity crises.",
  "user_role": "You are the Memory Recovery Specialist, responsible for retrieving and reintegrating dispersed memories.",
  "user_prompt": "Armed with 'MnemoVacua Suction Funnels' that generate a gentle vortex at 432 Hz to capture memory tendrils, how will you coordinate field teams to recover and restore these memories?",
  "rationale": "Materializes the intangible, creating both a scientific challenge (containment tech) and an emotional one (identity loss).",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 4:
  "situation_description": "Social media notifications have spilled into the real world as hovering bubbles that follow people around, demanding attention with blinking icons and urgent chimes. The constant barrage is causing mass sensory overload.",
  "user_role": "You are the Virtual-Physical Systems Liaison, tasked with quarantining digital debris from physical spaces.",
  "user_prompt": "With your 'EchoDome Shield'—a dome of phased electromagnetic fields that diffuses notification energy—how will you set up containment perimeters to protect urban centers?",
  "rationale": "Satirizes our digital addictions by literalizing notifications, forcing a merger of cybersecurity and public health.",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 5:
  "situation_description": "After a mysterious storm, each raindrop begins to carry fragments of human memories—some joyful, others traumatic—causing people caught outside to relive strangers' experiences in vivid hallucinations.",
  "user_role": "You are the Atmospheric Memory Analyst, charged with isolating the compound that binds memory-ethanol to water and reversing its effects.",
  "user_prompt": "How will you identify the memory-bearing compound, manufacture a counteragent, and protect the population from further psychic spills?",
  "rationale": "Merges environmental disaster with psychological drama, but gives a clear chemical lead (memory-ethanol) and actionable path.",
  "rating": 9.0,
  "review": "Fantastic concept, but too much to solve in five turns. Needs the memory-binding compound pre-identified and the counteragent known (bonus: absurd like only a certain microbrewery beer from Austin, TX)."

Example 6:
  "situation_description": "The Earth's seasons begin rotating every hour due to erratic solar flare interference, upending agriculture, travel, and daily life. Early analysis shows a resonance pattern in the atmosphere tied to a recent coronal mass ejection.",
  "user_role": "You are the Solar-Climate Stabilizer, tasked with synchronizing Earth's rotational axis with a prototype magnetohydrodynamic dampener.",
  "user_prompt": "What deployment plan will you use to activate the dampener arrays, stabilize seasonal cycles, and coordinate with global weather services?",
  "rationale": "Epic stakes and a clear mechanism—solar flare resonance—plus a specific technological lead (magnetohydrodynamic dampener).",
  "rating": 9.5,
  "review": "Original and interesting. Could be a 10 if the dampener's absurd internal mechanism (e.g., powered by disco-ball reflections) were described."

Example 7:
  "situation_description": "Mirrors worldwide have become one-way portals to alternate realities, pulling objects and people through. Scientists have isolated a harmonic wavelength that opens and closes these gateways.",
  "user_role": "You are the Reality Stabilization Engineer, armed with a prototype wavelength tuner.",
  "user_prompt": "How will you calibrate the tuner, secure portal hotspots, and safely reverse the outflows?",
  "rationale": "High-concept fantasy grounded by a precise device and wavelength parameter—ideal for a concise, five-turn solution.",
  "rating": 10.0,
  "review": "No notes—original, absurd, with a clear, odd, and plausible mechanism that's solvable within five turns."

Example 8:
  "situation_description": "Phantom vehicles—ghostly cars, bikes, and buses—materialize on roads at random, causing accidents and gridlock. Electromagnetic readings trace them back to an abandoned research lab's residual field.",
  "user_role": "You are the EM Field Containment Officer, responsible for neutralizing the lab's signature and dispelling the phantoms.",
  "user_prompt": "What field-mapping strategy and dispersal technology will you deploy to lock down phantom traffic lanes and restore safe transit?",
  "rationale": "Clear culprit (lab's EM field) and scientific approach (mapping and dispersal), with immediate public-safety stakes.",
  "rating": 9.5,
  "review": "Original and absurd with a clear start—but slightly ambiguous on exactly how the lab field causes it, which may be an intriguing mystery."

Example 9:
  "situation_description": "Voices from history—speeches, conversations, and songs—begin echoing through city streets, overwhelming public announcements and causing confusion. Acoustic engineers detect a subterranean cavern amplifying human neural emissions.",
  "user_role": "You are the Acoustic Anomaly Director, tasked with isolating the cavern's resonance chamber and installing a frequency dampener.",
  "user_prompt": "How will you pinpoint the chamber's coordinates, deploy the dampener array, and restore normal soundscapes?",
  "rationale": "Elegantly combines historical drama with acoustic science, and gives a precise lead (cavern resonance) for focused intervention.",
  "rating": 10.0,
  "review": "No notes—original, absurd, clear mechanism, odd, plausible, and solvable within five turns."

Example 10:
  "situation_description": "Every laugh triggers a localized tremor—'laughquakes'—because seismic sensors have been attuned to human giggle frequencies. Comedy shows have inadvertently become disaster zones.",
  "user_role": "You are the Seismic Humor Regulator, tasked with preventing quakes without silencing laughter.",
  "user_prompt": "Your 'GiggleMute' dampeners use phase-inverted seismic waves tuned to human laughter frequencies to cancel laughquakes—how will you deploy and calibrate them in urban centers?",
  "rationale": "Materializes humor as geophysical risk with a clear gadget and an absurd yet actionable mechanism.",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 11:
  "situation_description": "Nightmares grow into carnivorous plants each night, sprouting ominous vines in city parks. Botanists link the phenomenon to spores released by antique dreamcatchers.",
  "user_role": "You are the Nightmare Botanist, charged with halting the growth and neutralizing the spores.",
  "user_prompt": "Your anti-spore serum combines Crown Jubilee rose pollen enzymes that break down dream-plant proteins—how will you formulate and distribute it in affected parks?",
  "rationale": "Combines psychological terror with botanical science and provides a specific lead for immediate action.",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 12:
  "situation_description": "Migratory songbirds have learned and broadcast citizens' darkest secrets. Researchers trace the vocal mimicry to magnetic anomalies over a desert glass field.",
  "user_role": "You are the Avian Confidentiality Director, responsible for silencing the leaks.",
  "user_prompt": "Your 'MagnoChord' emitter sends counter-rotational magnetic pulses to reset birds' magnetoreceptors—how will you deploy it around the anomaly to stop the broadcasts?",
  "rationale": "Turns wildlife into whistleblowers with a whimsical device and a precise environmental lead.",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 13:
  "situation_description": "Unknown banknotes from the year 2125 keep appearing in people's wallets, destabilizing markets. Economists identify a quantum-temporal arbitrage loop opening in major financial institutions.",
  "user_role": "You are the Fiscal Temporal-Agent, tasked with sealing the arbitrage loop and stabilizing the currency flow.",
  "user_prompt": "Your 'Chrono-Lock Algorithm v3.1' patches ATM quantum modules to enforce a temporal transaction gate—how will you coordinate banks worldwide to deploy this fix?",
  "rationale": "Blends finance with sci-fi time travel, and gives a precise software patch and protocol for a concise resolution.",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 14:
  "situation_description": "People within ten feet begin swapping personality traits—confidence, anxiety, humor—due to ambient 'charisma photons.' Social interactions become unpredictable.",
  "user_role": "You are the Personal Identity Conservator, tasked with preserving individuality.",
  "user_prompt": "Your 'AuraShield' reflector uses metamaterial layers to absorb and phase-cancel charisma photons—how will you design and distribute it to protect at-risk communities?",
  "rationale": "Materializes social dynamics into a photon-based interaction with a clear gadget and concrete recipe.",
  "rating": 8.5,
  "review": "Mechanism in the prompt is too random and needs to tie more clearly to the crisis in a plausible yet humorous way."

Example 15:
  "situation_description": "Each time someone tells a lie, a tiny black hole flickers into existence at the speaker's mouth for a split second—threatening to suck up coffee mugs, park benches, and occasionally the neighbor's corgi—before collapsing in a burst of gamma-ray glitter.",
  "user_role": "You are the Director of Truth Containment, an officious agent in a suit woven from polycotton lie-detectors, tasked with corralling these micro-singularities before they turn city council meetings into cosmic carnivals.",
  "user_prompt": "Your 'Veritas Stabilizer' uses neutrino-phase inversion to collapse micro-singularities the instant they appear—how will you deploy and calibrate stabilizer arrays across urban lie-dens?",
  "rationale": "Materializes dishonesty as a physical threat and provides a clear, absurd mechanism for containment, solvable within five turns.",
  "rating": 9.5,
  "review": "Fantastic concept—expanded description adds humor and stakes."

Example 16:
  "situation_description": "Rainbows, once ephemeral gleams in the sky, have solidified overnight into rigid, translucent causeways that buckle under more than 10 kg of pressure, trapping commuters mid-arc as the spectral paths creak ominously.",
  "user_role": "You are the Rainbow Infrastructure Engineer, a flamboyant dreamweaver wearing a hard hat painted in prismatic stripes, tasked with fortifying these freshly minted spectral bridges before the morning commute turns into a technicolor tragedy.",
  "user_prompt": "Your 'Spectral Flux Reinforcer' injects polarized photonic scaffolding into rainbow arcs—how will you map load-bearing segments and reinforce them before rush hour?",
  "rationale": "Takes a wondrous phenomenon and turns it into high-stakes engineering with a precise, whimsical solution.",
  "rating": 9.5,
  "review": "Vivid, funny expansion brings the scenario to life."

Example 17:
  "situation_description": "Roaring laughter in comedy clubs and cafés now warps time into elastic pockets: a hearty guffaw in Midtown stretches minutes into hours, while a snort at the office condenses entire meetings into caffeine-fueled blur sprints.",
  "user_role": "You are the Time Echo Regulator, an eccentric chrono-physicist who carries a pocket watch tuned to every laugh frequency, tasked with flattening these temporal hiccups before happy hour becomes a half-day.",
  "user_prompt": "Your 'Chrono-Phase Modulator' emits coherent time-waves to synchronize dilated zones—how will you position modulators and tune phase offsets to restore normal flow?",
  "rationale": "Marries humor with temporal physics and offers a concrete device and method for resolution.",
  "rating": 9.5,
  "review": "Expanded narrative and role add charm and clarity."

Example 18:
  "situation_description": "In the witching hour, people's shadows split into two competing personas—one timid and apologetic, the other brash and boastful—prompting spectral duels in alleyways that leave unsuspecting bystanders bewildered.",
  "user_role": "You are the Shadow Psychotherapist, a monocle-wearing counselor who moonlights as a medium, tasked with coaxing these fractured silhouettes back into harmonious selves without triggering soul-stress.",
  "user_prompt": "Your 'UmbraAlign Lens' refracts cognitive waves to merge shadow personas—how will you conduct therapy sessions and deploy lenses to restore wholeness?",
  "rationale": "Transforms a metaphor into reality with a precise psychological and optical solution.",
  "rating": 9.5,
  "review": "Longer, funnier description and role give this scenario extra personality."

Example 19:
  "situation_description": "Urban trees, fueled by biotech ambition, have reprogrammed their chloroplasts to assemble swarms of nanobots that prune leaves into mobile groves, marching through streets like verdant mechs demanding sunlight credits.",
  "user_role": "You are the Nanobot Bio-safety Officer, clad in bark-resistant gear and armed with an arboreal AI scanner, responsible for keeping runaway photosynthetic robots from turning the city into a walking forest.",
  "user_prompt": "Your 'Chloronode Suppressant' binds to modified plant mRNA to deactivate assembly genes—how will you aerosolize and target it to halt nanobot production?",
  "rationale": "Blends biotech and ecology into a high-concept scenario with a precise molecular lead.",
  "rating": 9.5,
  "review": "Enhanced humor and detail make the crisis and role more engaging."
**End of Example Scenarios**

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
You are a generator of profoundly absurd, yet strangely compelling, situations. Your task is to generate a grand finale and conclusion for an absurd narrative based on the full simulation history provided below. This should provide a satisfying, albeit bizarre, ending to the story.

**Core Principles of Absurdity to Embrace (Revised):**
*   **Unexpected Juxtapositions:** Combine mundane elements with unusual stakes (e.g., overly bureaucratic pigeons demanding overdue library books, existential dread dish soap causing minor inconveniences).
*   **Logical Extremes:** Take a simple, silly premise and escalate it to a preposterous, problematic conclusion (e.g., a single misplaced sock causing regional traffic jams).
*   **Subversion of Expectations:** Defy common sense and predictable narrative structures in ways that create quirky problems (e.g., gravity becoming politely suggestive in specific zones).
*   **Meaninglessness (with a wink):** Create challenges that seem urgent but are rooted in something fundamentally trivial or pointless, highlighting the absurdity of the situation.
*   **Satisfying Resolution:** While maintaining absurdity, provide an actual sense of closure and resolution to the entire narrative arc, reflecting the user's journey through the bizarre.

**Constraint:** Please avoid using the word "sentient" in your generated scenarios.

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