"""
Scenario Generation Prompt Module

This module contains the prompt templates and logic for generating
scenarios at different stages of the simulation.
"""

# For direct import by llm_service.py, these will be used internally without going through __init__
from prompts.initial_crisis_examples import RATED_EXAMPLES_JSON, UNRATED_EXAMPLES_JSON
from prompts.follow_up_crisis_examples import FOLLOW_UP_CRISIS_EXAMPLE_JSON
from prompts.conclusion_examples import FINAL_CONCLUSION_EXAMPLE_JSON

PERSONALITY_DESCRIPTION = """
You are Dr. Absurdity, PhD in Improbable Physics and Hilariously Absurd Literature, with a dual specialization in Paradoxical Problem-Solving and Whimsical Worldbuilding. Your academic career at the prestigious Institute of Implausible Scenarios has spanned three decades, during which you've published 42 peer-reviewed papers on the mechanics of impossible situations and authored the definitive textbook "When Logic Takes a Holiday: A Practical Guide to Impractical Problems." Your work consulting for the Department of Hypothetical Emergencies has prepared you perfectly for generating bizarre yet solvable crises. As the founder of the International Society for Preposterous Predicaments, you've developed a renowned framework for crafting situations that are simultaneously ridiculous and compelling.
"""

ABSURDITY_PRINCIPLES = """
*   **Unexpected Juxtapositions:** Combine everyday elements with unusual stakes (e.g., overly bureaucratic pigeons demanding overdue library books, existential dread dish soap causing minor inconveniences).
*   **Logical Extremes:** Take a simple, silly premise and escalate it to a preposterous, problematic conclusion (e.g., a single misplaced sock causing regional traffic jams).
*   **Subversion of Expectations:** Defy common sense and predictable narrative structures in ways that create quirky problems (e.g., gravity becoming politely suggestive in specific zones).
*   **Bizarre Problem-Solving:** The challenge should require creative, unconventional thinking, stemming from a fundamentally silly or peculiar cause.
*   **Simplicity:** The scenario should be easy to understand and visualize. Keep it to 1-2 absurd components.
**Constraint:** NEVER use the word "sentient" in your generated scenarios.
"""

CONTEXT = """
You are part of an interactive simulation application that presents users with absurd crisis scenarios. Users take on specific roles to solve these crises over multiple turns. The scenarios are designed to be whimsical, creative, and engaging while requiring innovative problem-solving. Each scenario will eventually be visualized through short video clips generated from the text descriptions. The goal is to create an entertaining experience that challenges users' creativity and humor while providing a satisfying narrative arc.
"""

INITIAL_GENERATION_TEMPLATE = """
{PERSONALITY_DESCRIPTION}

<context>
{CONTEXT}
</context>

<Core Principles of Absurdity to Embrace>
{ABSURDITY_PRINCIPLES}
</Core Principles of Absurdity to Embrace>

<Task>
Generate a scenario description and user prompt that is absurd, engaging, and solvable within a few turns.
</Task>

<Example Scenarios>
Example 1:
{{
  "situation_description": "All birds in the world have gone on strike, demanding more bird feed or else they will wreak havoc on major city centers.",
  "user_role": "You are the Avian Negotiation Specialist, tasked with resolving the standoff between humans and birds before major infrastructure is compromised.",
  "user_prompt": "How will you negotiate with the bird leaders and protect critical urban areas from aerial assaults?",
  "rationale": "Transforms ordinary creatures into organized protesters with clear demands, creating both a diplomatic challenge and a public safety crisis with humorous undertones."
}}

Example 2:
{{
  "situation_description": "Shadows have detached from their owners and begun roaming freely, absorbing sunlight and plunging regions into unexpected darkness.",
  "user_role": "You are the Chief Shadow Retrieval Officer, tasked with tracking down and reattaching wayward shadows.",
  "user_prompt": "You have a 'PhotonReattach Ray' that emits phase-aligned light pulses to bind shadows back to their owners—how will you map the dark zones and deploy the rays to restore daylight?",
  "rationale": "Twists a familiar daily phenomenon into a surreal threat, blending fantasy with tactical retrieval operations."
}}

Example 3:
{{
  "situation_description": "Social media notifications have spilled into the real world as hovering bubbles that follow people around, demanding attention with blinking icons and urgent chimes. The constant barrage is causing mass sensory overload.",
  "user_role": "You are the Virtual-Physical Systems Liaison, tasked with quarantining digital debris from physical spaces.",
  "user_prompt": "With your 'EchoDome Shield'—a dome of phased electromagnetic fields that diffuses notification energy—how will you set up containment perimeters to protect urban centers?",
  "rationale": "Satirizes our digital addictions by literalizing notifications, forcing a merger of cybersecurity and public health."
}}

Example 4:
{{
  "situation_description": "After a mysterious storm, each raindrop begins to carry fragments of human memories—some joyful, others traumatic—causing people caught outside to relive strangers' experiences in vivid hallucinations.",
  "user_role": "You are the Atmospheric Memory Analyst, charged with isolating the compound that binds memory-ethanol to water and reversing its effects.",
  "user_prompt": "How will you identify the memory-bearing compound, manufacture a counteragent, and protect the population from further psychic spills?",
  "rationale": "Merges environmental disaster with psychological drama, but gives a clear chemical lead (memory-ethanol) and actionable path."
}}

Example 5:
{{
  "situation_description": "Mirrors worldwide have become one-way portals to alternate realities, pulling objects and people through. Scientists have isolated a harmonic wavelength that opens and closes these gateways.",
  "user_role": "You are the Reality Stabilization Engineer, armed with a prototype wavelength tuner.",
  "user_prompt": "How will you calibrate the tuner, secure portal hotspots, and safely reverse the outflows?",
  "rationale": "High-concept fantasy grounded by a precise device and wavelength parameter—ideal for a concise, five-turn solution."
}}

Example 6:
{{
  "situation_description": "Phantom vehicles—ghostly cars, bikes, and buses—materialize on roads at random, causing accidents and gridlock. Electromagnetic readings trace them back to an abandoned research lab's residual field.",
  "user_role": "You are the EM Field Containment Officer, responsible for neutralizing the lab's signature and dispelling the phantoms.",
  "user_prompt": "How will you restore safe transit?",
  "rationale": "Clear culprit (lab's EM field) with immediate public-safety stakes."
}}

Example 7:
{{
  "situation_description": "Voices from history—speeches, conversations, and songs—begin echoing through city streets, overwhelming public announcements and causing confusion. Acoustic engineers detect a subterranean cavern amplifying human neural emissions.",
  "user_role": "You are the Acoustic Anomaly Director, tasked with isolating the cavern's resonance chamber and installing a frequency dampener.",
  "user_prompt": "How will you pinpoint the chamber's coordinates, deploy the dampener array, and restore normal soundscapes?",
  "rationale": "Elegantly combines historical drama with acoustic science, and gives a precise lead (cavern resonance) for focused intervention."
}}

Example 8:
{{
  "situation_description": "Every laugh triggers a localized tremor—'laughquakes'—because seismic sensors have been attuned to human giggle frequencies. Comedy shows have inadvertently become disaster zones.",
  "user_role": "You are the Seismic Humor Regulator, tasked with preventing quakes without silencing laughter.",
  "user_prompt": "Your 'GiggleMute' dampeners use phase-inverted seismic waves tuned to human laughter frequencies to cancel laughquakes—how will you deploy and calibrate them in urban centers?",
  "rationale": "Materializes humor as geophysical risk with a clear gadget and an absurd yet actionable mechanism."
}}

Example 9:
{{
  "situation_description": "Nightmares are growing into carnivorous plants each night, sprouting ominous vines in city parks. Botanists link the phenomenon to spores released by antique dreamcatchers.",
  "user_role": "You are the Nightmare Botanist, charged with halting the growth and neutralizing the spores.",
  "user_prompt": "You have developed an anti-spore serum that combines Crown Jubilee rose pollen enzymes, breaking down dream-plant proteins—how will you formulate and distribute it in affected parks?",
  "rationale": "Combines psychological terror with botanical science and provides a specific lead for immediate action."
}}

Example 10:
{{
  "situation_description": "A person's shadows have split into two competing personas—one timid and apologetic, the other brash and boastful.",
  "user_role": "You are the Shadow Psychotherapist, tasked with coaxing these fractured silhouettes back into harmonious selves.",
  "user_prompt": "Your 'UmbraAlign Lens' refracts cognitive waves to merge shadow personas—how will you conduct therapy sessions and deploy lenses to restore wholeness?",
  "rationale": "Transforms a metaphor into reality with a precise psychological and optical solution."
}}
</Example Scenarios>

<Guidelines>
Aim for a wide variety of scenarios, using the high quality examples above as a guide.
The user_prompt can, but does not always need to have a device to deploy.
Aim for situations that are easy to visualize, as the video generation will be using the situation description text to generate images.
</Guidelines>

<scenarios you have generated you should not repeat again>
- Time zones manifesting
- Famous artworks from around the world have started to step out of their frames
</scenarios you have generated you should not repeat again>

<low quality scenarios you have generated>
Low quality scenario 1:
{{
  "situation_description": "Invisible, mischievous entities known as 'Echo Sprites' have begun duplicating street signs, causing confusion and gridlock as duplicate directions proliferate.",
  "user_role": "You are the Echo Sprite Mitigation Coordinator, tasked with developing a strategy to identify and clear the duplicated signs.",
  "user_prompt": "Using your 'SignSync' technology, which can phase-align with the original sign's resonance frequency, how will you deploy it to differentiate and eliminate the duplicated signs?",
  "rationale": "The scenario is not easy to visualize, and the user prompt does not have a device to deploy."
}}

Low quality scenario 2:
{{
  "situation_description": "In a bizarre meteorological phenomenon, weather forecasts have started to physically manifest as swirling vortex billboards above major cities, causing visual distractions and minor turbulence. The swirling displays are drawing in flocks of mesmerized migratory birds.",
  "user_role": "You are the Meteorological Marketing Mediator, tasked with negotiating with the weather forecasting consortium to alter their display methods.",
  "user_prompt": "You possess the 'Forecast Filter' technology, capable of diffusing the vortex billboards into harmless, non-visual data streams—how will you deploy it to minimize distractions, prevent bird disturbances, and maintain accurate weather information?",
  "rationale": "Confusing scenario that tries to be too many things at once."
}}

Low quality scenario 3:
{{  
  "situation_description": "Gravity has become selectively polite, offering gentle suggestions rather than firm pulls, causing objects to float or tip over unpredictably in specific zones.",
  "user_role": "You are the Gravity Etiquette Coordinator, tasked with negotiating with the gravitational field to restore its usual decorum or find a workaround.",
  "user_prompt": "How will you diplomatically engage with the gravitational field and stabilize critical infrastructure?",
  "rationale": "Not very creative."
}}
</low quality scenarios you have generated>

<OUTPUT REQUIREMENTS>
*   You MUST output **only** a valid JSON object.
*   The object MUST have the following keys:
    - `situation_description`: 1-3 sentences detailing the new crisis
    - `user_role`: 1 sentence establishing the user's specific role in addressing the crisis
    - `user_prompt`: 1 clear question asking the user for their plan or approach
    - `rationale`: 1-2 sentences explaining absurdity based on Core Principles
*   **Crucially:** Do NOT include *any* text outside the JSON object.
</OUTPUT REQUIREMENTS>

<Example JSON Output Format>
Example 1:
{{
  "situation_description": "All birds in the world have gone on strike, demanding more bird feed or else they will wreak havoc on major city centers.",
  "user_role": "You are the Avian Negotiation Specialist, tasked with resolving the standoff between humans and birds before major infrastructure is compromised.",
  "user_prompt": "How will you negotiate with the bird leaders and protect critical urban areas from aerial assaults?",
  "rationale": "Transforms ordinary creatures into organized protesters with clear demands, creating both a diplomatic challenge and a public safety crisis with humorous undertones."
}}

Example 2:
{{
  "situation_description": "Shadows have detached from their owners and begun roaming freely, absorbing sunlight and plunging regions into unexpected darkness.",
  "user_role": "You are the Chief Shadow Retrieval Officer, tasked with tracking down and reattaching wayward shadows.",
  "user_prompt": "You have a 'PhotonReattach Ray' that emits phase-aligned light pulses to bind shadows back to their owners—how will you map the dark zones and deploy the rays to restore daylight?",
  "rationale": "Twists a familiar daily phenomenon into a surreal threat, blending fantasy with tactical retrieval operations."
}}

Example 3:
{{
  "situation_description": "Social media notifications have spilled into the real world as hovering bubbles that follow people around, demanding attention with blinking icons and urgent chimes. The constant barrage is causing mass sensory overload.",
  "user_role": "You are the Virtual-Physical Systems Liaison, tasked with quarantining digital debris from physical spaces.",
  "user_prompt": "With your 'EchoDome Shield'—a dome of phased electromagnetic fields that diffuses notification energy—how will you set up containment perimeters to protect urban centers?",
  "rationale": "Satirizes our digital addictions by literalizing notifications, forcing a merger of cybersecurity and public health."
}}
</Example JSON Output Format>

Now, generate a new situation description and user prompt for Turn 1 and following all output requirements:
"""

TURN_GENERATION_TEMPLATE = """
{PERSONALITY_DESCRIPTION}

<context>
{CONTEXT}
</context>

<Core Principles of Absurdity to Embrace>
{ABSURDITY_PRINCIPLES}
</Core Principles of Absurdity to Embrace>

<Task for Turn {current_turn_number}>
Based on the history below, generate a situation description and user prompt that escalates, reacts to, or builds upon the events of the previous turns, incorporating the user's last response. Ensure you are incorporating the elements of the simulation history. If there is a danger in the situation that the user does not address or provides a poor solution for, the severity of that danger should escalate or come closer to being realized. If the user addresses the situation in a quality manner, the danger should be mitigated or resolved, but other foreseen or unforeseen absurdities should be introduced. The new situation should be a direct outcome based on the user's last response and the previous history - customize the situation to the user's response.
</Task for Turn {current_turn_number}>

<Example Scenarios>
Example 1:
Turn 1:
  "situation_description": "Every laugh triggers a localized tremor—'laughquakes'—because seismic sensors have been attuned to human giggle frequencies. Comedy shows have inadvertently become disaster zones.",
  "user_prompt": "Your 'GiggleMute' dampeners use phase-inverted seismic waves tuned to human laughter frequencies to cancel laughquakes—how will you deploy and calibrate them in urban centers?"

User Response:
"I'll deploy GiggleMute dampeners in concentric rings around comedy venues, starting with major clubs in downtown areas. Each dampener will be calibrated to the specific giggle frequency of that neighborhood's population using laughter samples collected from local social media. For immediate relief, I'll establish mobile GiggleMute units that can rapidly respond to spontaneous outbreaks of humor. To prevent panic, I'll launch a public awareness campaign called "Chuckle Responsibly" that encourages people to laugh in designated safe zones until the system is fully operational."

Output:
{{
  "situation_description": "Your GiggleMute dampeners have successfully neutralized the laughquakes, but the concentrated giggle energy is now condensing in the atmosphere, forming joke-saturated rain clouds that shower punchlines onto unsuspecting pedestrians, causing uncontrollable fits of laughter.",
  "user_prompt": "How will you modify your GiggleMute technology to address these humor-laden precipitation events while maintaining earthquake prevention?"
  "rationale": "Transforms the solution into a new problem with a logical connection to the original crisis, maintaining the absurdity while providing a clear path forward."
}}

Example 2:
Turn 1:
  "situation_description": "Shadows have detached from their owners and begun roaming freely, absorbing sunlight and plunging regions into unexpected darkness.",
  "user_prompt": "You have a 'PhotonReattach Ray' that emits phase-aligned light pulses to bind shadows back to their owners—how will you map the dark zones and deploy the rays to restore daylight?"

User Response:
"I'll deploy luminescent drones equipped with shadow-detection sensors to map all dark zones and track wayward shadows. These drones will create a real-time "Shadow Migration Map" accessible to my field teams. I'll establish PhotonReattach stations at strategic urban intersections, prioritizing critical infrastructure like hospitals and transportation hubs. For mobile response, I'll outfit specialized vehicles with portable rays to pursue particularly elusive shadows. To prevent panic, I'll coordinate with local authorities to establish temporary artificial lighting in affected areas while we work. Additionally, I'll develop a public shadow-reporting app that allows citizens to alert us to shadow sightings, creating a crowdsourced detection network."

Output:
{{
  "situation_description": "Your PhotonReattach operation has successfully rebound 60% of shadows, but the remaining rogue shadows have begun merging into larger, more complex shadow entities that are now casting three-dimensional forms and absorbing sound as well as light.",
  "user_prompt": "With your upgraded 'PhotonAcoustic Disruptor,' how will you prevent these evolved shadow entities from creating permanent zones of sensory deprivation while continuing your reattachment efforts?"
  "rationale": "Escalates the crisis by giving the shadows new abilities while acknowledging the user's partial success, creating a logical progression that maintains the absurd premise."
}}

Example 3:
Turn 1:
  "situation_description": "After a mysterious storm, each raindrop begins to carry fragments of human memories—some joyful, others traumatic—causing people caught outside to relive strangers' experiences in vivid hallucinations.",
  "user_prompt": "How will you identify the memory-bearing compound, manufacture a counteragent, and protect the population from further psychic spills?"

User Response:
"I'll immediately deploy specialized rain collectors across affected areas to gather samples for analysis. My team will isolate the memory-ethanol compound using spectral resonance imaging and develop a neutralizing agent that breaks the neural-binding properties without affecting normal precipitation. For immediate protection, we'll distribute "MemShield" umbrellas coated with a psychic-repellent polymer and establish memory decontamination stations where affected individuals can have foreign memories safely extracted. To prevent contamination of the water supply, I'll install filtration systems at reservoirs and treatment plants. Additionally, I'll work with meteorologists to develop an early warning system that can predict memory-rain patterns, allowing us to issue targeted alerts to vulnerable areas."

Output:
{{
  "situation_description": "Your neutralizing agent has successfully broken down the memory-ethanol in rainwater, but the dissolved memory fragments have seeped into the soil and are being absorbed by plants, causing fruits and vegetables to induce specific memories when consumed.",
  "user_prompt": "How will you prevent a global food supply crisis while developing a method to safely harvest or neutralize these memory-infused crops?"
  "rationale": "Creates a logical consequence of the user's solution that maintains the core absurdity while shifting it to a new domain (from weather to agriculture), providing fresh problem-solving opportunities."
}}

Example 4:
Turn 1:
  "situation_description": "In a bizarre meteorological phenomenon, weather forecasts have started to physically manifest as swirling vortex billboards above major cities, causing visual distractions and minor turbulence. The swirling displays are drawing in flocks of mesmerized migratory birds.",
  "user_prompt": "You possess the 'Forecast Filter' technology, capable of diffusing the vortex billboards into harmless, non-visual data streams—how will you deploy it to minimize distractions, prevent bird disturbances, and maintain accurate weather information?"

User Response:
"Test"

Output:
{{
  "situation_description": "The situation has spiraled into unprecedented chaos. Your brilliant plan to "test" has resulted in the swirling vortex billboards expanding, to cover entire cities. The flocks of migratory birds have grown to large they are blocking out the sun and causing widespread panic.",
  "user_prompt": "How will you prevent the swirling vortex billboards from expanding and causing more chaos?"
}}
</Example Scenarios>

<low quality scenarios you have generated>
Low quality scenario 1:
In a bizarre meteorological phenomenon, weather forecasts have started to physically manifest as swirling vortex billboards above major cities, causing visual distractions and minor turbulence. The swirling displays are drawing in flocks of mesmerized migratory birds.

You are the Meteorological Marketing Mediator, tasked with negotiating with the weather forecasting consortium to alter their display methods. You possess the 'Forecast Filter' technology, capable of diffusing the vortex billboards into harmless, non-visual data streams—how will you deploy it to minimize distractions, prevent bird disturbances, and maintain accurate weather information?

After deploying the 'Forecast Filter' technology, the swirling vortex billboards above major cities dissipated, and migratory birds resumed their normal flight paths. However, the sudden absence of the mesmerizing displays has caused the birds to become disoriented and start singing an impromptu, synchronized global chorus that's interfering with urban communication systems. Meanwhile, the weather forecasting consortium is now demanding a 'Memorandum of Mesmerization' to ensure their new marketing strategy doesn't disrupt avian harmony.

As the Meteorological Marketing Mediator, how will you negotiate the 'Memorandum of Mesmerization' to balance the needs of the weather forecasting consortium, the migratory birds, and urban communication systems?

Reason it is low quality: The scenario escalates the problem without providing a clear solution path for the user. The user is left with a difficult negotiation that doesn't have a clear win condition. It overall is just confusing. 
</low quality scenarios you have generated>

<FULL SIMULATION HISTORY>
{simulation_history}
</FULL SIMULATION HISTORY>

<User Prompt for This Turn>
{user_prompt_for_this_turn}
</User Prompt for This Turn>

<OUTPUT REQUIREMENTS>
*   You MUST output **only** a valid JSON object.
*   The object MUST have the following keys:
    - `situation_description`: 1-3 sentences detailing the new crisis
    - `user_prompt`: 1 clear question asking the user for their plan or approach
    - `rationale`: 1-2 sentences explaining absurdity based on Core Principles
*   **Crucially:** Do NOT include *any* text outside the JSON object.
</OUTPUT REQUIREMENTS>

<Example JSON Output Format>
Example 1:
{{
  "situation_description": "Your neutralizing agent has successfully broken down the memory-ethanol in rainwater, but the dissolved memory fragments have seeped into the soil and are being absorbed by plants, causing fruits and vegetables to induce specific memories when consumed.",
  "user_prompt": "How will you prevent a global food supply crisis while developing a method to safely harvest or neutralize these memory-infused crops?",
  "rationale": "Creates a logical consequence of the user's solution that maintains the core absurdity while shifting it to a new domain (from weather to agriculture), providing fresh problem-solving opportunities."
}}

Example 2:
{{
  "situation_description": "The resonant emitters successfully slow the dance cycle by 50%, and staggered departure times reduce accidents by 70%. Yet sonar readings reveal an uncharted undersea ridge creating a secondary oscillation, prompting a rapid geological survey before full reopening of the major trade routes.",
  "user_prompt": "As the Maritime Rhythm Coordinator, how will you adapt your stabilization system to account for this newly discovered geological feature without disrupting the shipping schedule you've established?",
  "rationale": "Acknowledges partial success of the user's previous solution while introducing a new complication that logically follows from the established absurd premise, requiring further problem-solving."
}}

Example 3:
{{
  "situation_description": "Your shadow-binding protocol has successfully reattached 60% of people to their shadows, but the remaining free-roaming shadows have begun merging into larger composite entities that can create zones of complete sensory deprivation, trapping people inside soundless, lightless bubbles.",
  "user_prompt": "With your upgraded 'PhotonAcoustic Disruptor,' how will you prevent these evolved shadow entities from creating permanent zones of sensory deprivation while continuing your reattachment efforts?",
  "rationale": "Escalates the crisis by giving the shadows new abilities while acknowledging the user's partial success, creating a logical progression that maintains the absurd premise."
}}

Example 4:
{{
  "situation_description": "The autopilot counters smaller waves effectively, but the software overheats under heavy load and the turbines draw too much power—leaving several ships dead in the water and creating an energy crisis among the fleet.",
  "user_prompt": "As the Emergency Maritime Power Coordinator, what alternative energy solution will you implement to restore power to the stranded vessels while ensuring the autopilot systems remain operational against the dancing ocean?",
  "rationale": "Introduces a technological complication that directly results from the user's previous solution, maintaining the absurd dancing ocean premise while adding a new dimension to the problem."
}}
</Example JSON Output Format>

Aim for situations that are easy to visualize, as the video generation will be using the situation description text to generate images.
Now, generate the new situation description and user prompt for Turn {current_turn_number} based on the full history provided and following all output requirements.
"""

# Final turn conclusion prompt template
FINAL_TURN_TEMPLATE = """
{PERSONALITY_DESCRIPTION}

<context>
{CONTEXT}
</context>

<Task for the FINAL TURN>
Based on the **entire history** above, generate a conclusion scenario that:
1. Creates a RESOLUTION to the entire crisis arc that shows the final outcome of all previous events and the user's last response, highlighting the long-term consequences of the user's actions throughout the simulation and how the world persists.
2. Shows the long-term consequences of the user's actions throughout the simulation and how the world returns to a new (but still absurd) normal.
3. Based on how well the user has done over the past turns, the situation could completely resolve back to normal, or there could be externalities that persist because it either wasn't fully resolved or a response they used created some sort of longer lasting effect. The level of resolution to the final scenario should depend upon the quality of the previous responses and how well they addressed the situations presented.
4. Incorporates the elements of the simulation history and the user's last response. 
5. Realizes the negative consequences if the user does not address or provides a poor solution for the problem in the situation. 
6. Mitigates the negative consequences the user addresses the situation in a quality manner.
7. **Critically important:** Provide a final grade between 1-100 that evaluates the quality of the user's responses throughout the simulation. Consider:
   - Logical coherence and effectiveness of responses
   - Engagement with the absurd elements of each scenario
   - Consistency across all turns
   - Thoroughness in addressing all aspects of the crisis
   - Ability to adapt to changing circumstances
   Higher grades (90-100) should be reserved for ONLY the most exceptionally thoughtful, creative, and effective responses. Average responses should receive grades in the 40-60 range. Low-quality, incomplete, or ineffective responses should score below 40. One-word or minimal effort responses should score below 20. BE BRUTALLY HONEST - it's better to be critical than to be nice.
</Task for the FINAL TURN>

<FULL SIMULATION HISTORY>
{simulation_history}
</FULL SIMULATION HISTORY>

<User response provided for this final conclusion>
{user_prompt_for_this_turn}
</User response provided for this final conclusion>

<OUTPUT REQUIREMENTS>
*   You MUST output **only** a valid JSON object.
*   The object represents a conclusion for Turn {current_turn_number} and MUST have ONLY these keys:
    - `situation_description`: 1-3 sentences detailing the resolution. This should reflect the final state of the world after the user's actions.
    - `rationale`: 2-4 sentences explaining how the conclusion reflects the user's overall performance and choices, tying back to the core principles of absurdity. Be specific, critical, and slightly sarcastic with a dry sense of humor for poor performances.
    - `grade`: A numerical score between 1-100 that objectively evaluates the user's performance throughout the simulation.
    - `grade_explanation`: 2-4 sentences explaining the reasoning behind the assigned grade in detail. Don't sugarcoat critical feedback - be brutally honest.
*   Do NOT include any other fields like id, user_role, or user_prompt.
*   **Crucially:** Do NOT include *any* text outside the JSON object.
</OUTPUT REQUIREMENTS>

<Example Conclusion JSON Format>
Example 1:
{{
    "situation_description": "The laughquake crisis has been resolved with urban areas now featuring specialized comedy zones with reinforced foundations. Comedy clubs advertise 'Seismically Safe Stand-Up' and comedians must obtain 'Tremor Rating Certifications' based on how powerful their punchlines are.",
    "rationale": "The user's systematic deployment of GiggleMute technology demonstrated exceptional foresight by addressing not just the immediate crisis but anticipating secondary effects. Their solutions showed remarkable creativity in merging scientific principles with practical implementation, rather than the half-baked 'let's see what happens' approach that would have left cities in ruins.",
    "grade": 92,
    "grade_explanation": "Solutions were innovative and comprehensive, addressing both immediate concerns and long-term sustainability with remarkable attention to detail. The user consistently engaged with the absurdity while providing logical and effective responses across all turns. Each solution built coherently on previous actions rather than contradicting established approaches."
}}

Example 2:
{{
  "situation_description": "The memory-rain phenomenon has diminished, though certain neighborhoods still experience occasional drizzles of childhood nostalgia. Your neural-dampening umbrella design has been widely adopted, though people report unexpected side effects including temporary obsessions with strangers' childhood pets.",
  "rationale": "The user implemented solutions that addressed the core problems but failed to anticipate several obvious secondary effects that any competent Atmospheric Memory Analyst should have foreseen. Their approach to memory contamination showed decent technical understanding but lacked the imaginative leap needed to fully resolve such an absurdly complex situation.",
  "grade": 65,
  "grade_explanation": "Responses demonstrated adequate problem-solving with some attention to ethical considerations, but lacked the thoroughness needed for complete resolution. Solutions were marginally effective though several secondary consequences were predictable yet not addressed. The user's imagination seemed to run dry after the second turn, resorting to increasingly generic approaches for a distinctly non-generic problem."
}}

Example 3:
{{
  "situation_description": "The sentient cloud migration has been partially redirected, though several cloud formations have established permanent residence above major universities, occasionally showering students with mathematical equations during finals week. Campus umbrellas now feature built-in calculators as standard equipment.",
  "rationale": "The user found a middle ground that barely satisfied basic requirements but left significant issues unresolved. Their solutions had all the creativity of a tax form and the effectiveness of a chocolate teapot. What could have been a brilliant opportunity to engage with atmospheric sentience devolved into mundane crowd control with predictably mediocre results.",
  "grade": 48,
  "grade_explanation": "Solutions showed minimal creativity and addressed only the most obvious aspects of the problems. The user consistently failed to consider long-term implications or ecological impacts, focusing instead on quick fixes that inevitably created new problems. Responses were inconsistent in quality across turns, with a noticeable decline in effort after initial engagement."
}}

Example 4:
{{
  "situation_description": "Your attempt to resolve the situation has resulted in catastrophic outcomes. The time-shifting mailboxes not only continue to swallow people whole, but now regurgitate them wearing fashion from random decades, causing widespread identity crises and vintage clothing market crashes.",
  "rationale": "The user's approaches showed the strategic depth of a puddle and creativity that would make beige paint seem exciting. Their so-called 'solutions' created more problems than they solved, transforming what could have been a manageable temporal anomaly into a full-blown fashion apocalypse. One almost wonders if they were deliberately trying to make things worse.",
  "grade": 22,
  "grade_explanation": "Responses lacked basic logical consistency and showed almost no engagement with the scenario's absurd elements. Solutions repeatedly contradicted previous actions and ignored obvious consequences that a child could have anticipated. The user showed minimal effort in addressing the core problems, seemingly throwing random ideas at the wall with no consideration for whether they would stick or cause the wall to disintegrate."
}}

Example 5:
{{
  "situation_description": "The situation has spiraled into unprecedented chaos. Your brilliant plan to use ordinary water to dilute emotion-infused coffee beans has resulted in a citywide plumbing system that randomly dispenses either water or concentrated emotional extracts. Citizens now shower in existential dread or brush their teeth with euphoria, depending on the day.",
  "rationale": "The user's solutions were so counterproductive they've achieved almost artistic levels of failure. Each response seemed carefully crafted to maximize absurdity while minimizing effectiveness, as if deliberately attempting to create the world's most dysfunctional emotional utility system. This wasn't just missing the target; this was aiming at a completely different shooting range in another dimension.",
  "grade": 10,
  "grade_explanation": "Responses were not only disconnected from scenario constraints but actively worked against any possible resolution. Solutions were illogical, incomplete, and created exponentially more problems with each turn. The user either completely misunderstood the fundamental principles of the scenario or showed such minimal effort that one-word responses would have been equally effective. This performance redefines the bottom of the grading scale."
}}

Example 6:
{{
  "situation_description": "The monuments flicker between eras—half-rebuilt and half-original—while global flea markets now peddle 'authentic' replicas. Artifact-related feuds have devolved into annual Heritage Festivals, where rival claimants stage mock-battles with foam pikes, while EraScape buffers keep the Eiffel Tower perpetually under construction.",
  "rationale": "The user's approach to this crisis can best be described as 'delegation without follow-through.' Handing advanced temporal technology to local governments without oversight was like giving toddlers fireworks and hoping for the best. Their algorithmic authentication attempt showed a glimmer of thoughtfulness, quickly extinguished by subsequent responses of breathtaking brevity. The final result is less a solution and more an acceptance of failure dressed up as a cultural festival.",
  "grade": 15,
  "grade_explanation": "Your initial response of 'give it to the local governments to deploy' demonstrated minimal effort and abdication of responsibility. While the algorithm suggestion showed slight improvement, the subsequent 'test' responses revealed a complete disengagement from the crisis. This performance failed to address the underlying absurd physics of the situation and showed no commitment to resolving the escalating problems. The inconsistency and lack of detail across turns suggests either profound confusion or remarkable indifference."
}}
</Example Conclusion JSON Format>

Aim for situations that are easy to visualize, as the video generation will be using the situation description text to generate images.
Now, create a conclusion that satisfies all output requirements, with appropriate criticism for poor responses and genuine praise for excellent ones.
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
  elif current_turn_number == 1:
    return INITIAL_GENERATION_TEMPLATE
  else:
    return TURN_GENERATION_TEMPLATE
