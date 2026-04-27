from __future__ import annotations
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from google import genai
from google.genai import types

from pawpal_system import DBManager, Owner
from rag import PetCareRetriever

load_dotenv()

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("pawpal_ai.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("pawpal.agent")


# ── Guardrails ─────────────────────────────────────────────────────────────────
def validate_input(text: str) -> Tuple[bool, str]:
    """Return (is_valid, error_message). Rejects empty or oversized input."""
    if not text or not text.strip():
        return False, "Message cannot be empty."
    if len(text.strip()) < 2:
        return False, "Message is too short."
    if len(text) > 500:
        return False, "Message is too long (max 500 characters)."
    return True, ""


# ── Agent ──────────────────────────────────────────────────────────────────────
class PawPalAgent:
    MODEL = "gemini-2.5-flash"
    MAX_ITERATIONS = 8
    SYSTEM_PROMPT = (
        "You are PawPal+, a friendly AI pet care assistant. "
        "You help pet owners manage care schedules for their pets. "
        "Always search the knowledge base before giving specific pet care advice. "
        "When asked to set up routines, use the available tools to actually create the tasks — "
        "do not just describe what should be done. "
        "Be concise and warm."
    )

    def __init__(
        self,
        owner: Optional[Owner],
        db: DBManager,
        tasks: List[Dict],
        api_key: Optional[str] = None,
    ):
        _key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self._client = genai.Client(api_key=_key)
        self.owner = owner
        self.db = db
        self.tasks = tasks  # mutable reference — edits here update the caller's list
        self.retriever = PetCareRetriever()
        self._tool = self._build_tool()

    # ── Tool schema definition ─────────────────────────────────────────────────
    def _build_tool(self) -> types.Tool:
        S = types.Schema
        T = types.Type
        FD = types.FunctionDeclaration
        return types.Tool(
            function_declarations=[
                FD(
                    name="search_knowledge",
                    description=(
                        "Search the pet care knowledge base for information about feeding, "
                        "exercise, grooming, health, vaccinations, or puppy/kitten care."
                    ),
                    parameters=S(
                        type=T.OBJECT,
                        properties={"query": S(type=T.STRING, description="Natural language pet care query.")},
                        required=["query"],
                    ),
                ),
                FD(
                    name="list_tasks",
                    description="List all current care tasks for the owner's pets.",
                    parameters=S(type=T.OBJECT, properties={}),
                ),
                FD(
                    name="add_task",
                    description="Add a new pet care task to the schedule.",
                    parameters=S(
                        type=T.OBJECT,
                        properties={
                            "title": S(type=T.STRING, description="Short task name, e.g. 'Morning walk'."),
                            "pet_name": S(type=T.STRING, description="Name of the pet this task is for."),
                            "priority": S(type=T.STRING, description="Priority: low, medium, or high."),
                            "due_date": S(type=T.STRING, description="Date in YYYY-MM-DD format."),
                            "due_time": S(type=T.STRING, description="Time in HH:MM 24-hour format, e.g. '08:00'."),
                            "duration_minutes": S(type=T.INTEGER, description="Duration in minutes (default 30)."),
                        },
                        required=["title", "pet_name", "priority", "due_date", "due_time"],
                    ),
                ),
                FD(
                    name="add_pet",
                    description="Add a new pet to the owner's profile.",
                    parameters=S(
                        type=T.OBJECT,
                        properties={
                            "name": S(type=T.STRING, description="Pet's name."),
                            "species": S(type=T.STRING, description="Species: dog, cat, or other."),
                            "breed": S(type=T.STRING, description="Breed (optional)."),
                            "age": S(type=T.INTEGER, description="Age in years (optional)."),
                        },
                        required=["name", "species"],
                    ),
                ),
            ]
        )

    # ── Tool execution ─────────────────────────────────────────────────────────
    def _run_tool(self, name: str, inputs: Dict[str, Any]) -> str:
        logger.info("TOOL CALL | %s | %s", name, inputs)
        try:
            if name == "search_knowledge":
                results = self.retriever.search(inputs["query"])
                if not results:
                    return "No relevant information found in the pet care knowledge base."
                return "\n\n---\n\n".join(results)

            elif name == "list_tasks":
                if not self.tasks:
                    return "No tasks found."
                lines = [
                    f"- {t['title']} for {t.get('pet_name', '?')} "
                    f"at {t['due_time'].strftime('%Y-%m-%d %H:%M')} [{t['priority']}]"
                    for t in self.tasks
                ]
                return "\n".join(lines)

            elif name == "add_task":
                if self.owner is None:
                    return "No owner is set up. Please create an owner first in the Owner & Pets tab."
                pet_name = inputs["pet_name"]
                self.owner.get_pet_list()
                pet = next(
                    (p for p in self.owner.pets if p.name.lower() == pet_name.lower()), None
                )
                if pet is None:
                    available = [p.name for p in self.owner.pets]
                    return f"Pet '{pet_name}' not found. Available pets: {available}"
                due_dt = datetime.strptime(
                    f"{inputs['due_date']} {inputs['due_time']}", "%Y-%m-%d %H:%M"
                )
                task: Dict[str, Any] = {
                    "title": inputs["title"],
                    "duration_minutes": inputs.get("duration_minutes", 30),
                    "priority": inputs["priority"],
                    "pet_id": pet.pet_id,
                    "pet_name": pet.name,
                    "due_time": due_dt,
                }
                self.tasks.append(task)
                logger.info("TASK ADDED | %s for %s at %s", inputs["title"], pet.name, due_dt)
                return f"Added task '{inputs['title']}' for {pet.name} at {due_dt.strftime('%Y-%m-%d %H:%M')}."

            elif name == "add_pet":
                if self.owner is None:
                    return "No owner is set up. Please create an owner first."
                new_pet = self.owner.add_pet(
                    {
                        "name": inputs["name"],
                        "type": inputs.get("species", "other"),
                        "breed": inputs.get("breed", ""),
                        "age": inputs.get("age", 0),
                        "care_needs": {"feed": "daily"},
                    }
                )
                logger.info("PET ADDED | %s (%s)", new_pet.name, new_pet.type)
                return f"Added pet '{new_pet.name}' ({new_pet.type}) with ID {new_pet.pet_id}."

            else:
                return f"Unknown tool: {name}"

        except Exception as e:
            logger.error("TOOL ERROR | %s | %s", name, e)
            return f"Error running {name}: {e}"

    # ── Agentic loop ───────────────────────────────────────────────────────────
    def _create_chat_session(self, history: List[Dict]):
        """Create a Gemini chat session from plain-text history."""
        gemini_history = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part(text=m["content"])],
            )
            for m in history
            if isinstance(m.get("content"), str)
        ]
        return self._client.chats.create(
            model=self.MODEL,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_PROMPT,
                tools=[self._tool],
            ),
            history=gemini_history,
        )

    def chat(
        self,
        user_message: str,
        history: List[Dict],
        _session=None,  # injectable for tests
    ) -> Tuple[str, List[str]]:
        """Run the agent loop and return (response_text, log_lines)."""
        valid, err = validate_input(user_message)
        if not valid:
            logger.warning("INPUT REJECTED | %s", err)
            return f"Input error: {err}", []

        log_lines: List[str] = []
        logger.info("USER MESSAGE | %s", user_message[:200])

        chat_session = _session or self._create_chat_session(history)
        response = chat_session.send_message(user_message)

        for iteration in range(self.MAX_ITERATIONS):
            logger.info("Agent iteration %d", iteration + 1)
            fn_calls = [
                p for p in response.candidates[0].content.parts if p.function_call
            ]

            if not fn_calls:
                text = response.text
                logger.info("RESPONSE | %s", text[:200])
                return text, log_lines

            # Process all function calls and collect results
            result_parts = []
            for part in fn_calls:
                fn = part.function_call
                result = self._run_tool(fn.name, dict(fn.args))
                log_lines.append(f"`{fn.name}` → {result[:120]}")
                result_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fn.name,
                            response={"result": result},
                        )
                    )
                )

            response = chat_session.send_message(result_parts)

        return "I wasn't able to complete that request. Please try rephrasing.", log_lines
