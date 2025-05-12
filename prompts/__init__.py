"""
Prompts Module

This module contains all the prompt templates and example JSON structures used
for generating scenarios, critiques, and media prompts throughout the simulation.
"""

# Import all prompt-related constants and functions from subdirectories
from prompts.initial_crisis_examples import RATED_EXAMPLES_JSON, UNRATED_EXAMPLES_JSON
from prompts.follow_up_crisis_examples import FOLLOW_UP_CRISIS_EXAMPLE_JSON
from prompts.conclusion_examples import FINAL_CONCLUSION_EXAMPLE_JSON
from prompts.scenario_generation_prompt import (
    INITIAL_GENERATION_TEMPLATE,
    TURN_GENERATION_TEMPLATE,
    FINAL_TURN_TEMPLATE,
    get_formatted_prompt_template
)
from prompts.video_description_generation_prompt import VIDEO_PROMPT_TEMPLATE

# Define an exported constant that combines both rated and unrated examples
INITIAL_CRISIS_EXAMPLES_JSON = RATED_EXAMPLES_JSON + UNRATED_EXAMPLES_JSON
