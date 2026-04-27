from datetime import datetime, date
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Ensure project root is on sys.path when running tests from tests/ folder.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from pawpal_system import init_pawpal_system, Owner, Constraints, Scheduler, Task, DBManager
from rag import PetCareRetriever
from ai_assistant import validate_input, PawPalAgent


def test_task_mark_complete():
    task = Task(
        task_id="t1",
        user_id="u1",
        description="Feed Mittens",
        due_time=datetime.now(),
        priority="high",
        status="pending",
        pet_id="p1"
    )

    assert task.status == "pending"
    task.mark_complete()
    assert task.status == "done"


def test_pet_task_addition_increases_count():
    system = init_pawpal_system(":memory:")
    assert system["status"] == "initialized"

    db = system["db"]
    owner = Owner(owner_id="owner-test", name="Tester", email="tester@example.com", db=db)

    pet = owner.add_pet({
        "name": "Buttercup",
        "type": "dog",
        "breed": "Beagle",
        "age": 2,
        "care_needs": {"walk": "daily"}
    })

    constraints = Constraints(start_date=date.today(), end_date=date.today())
    scheduler = Scheduler(owner, constraints, db)

    # no tasks yet
    assert len(scheduler.get_tasks_by_pet(pet.pet_id)) == 0

    scheduler.schedule_task(pet.pet_id, {
        "description": "Morning walk",
        "due_time": datetime.now(),
        "priority": "medium"
    })

    scheduler.schedule_task(pet.pet_id, {
        "description": "Feed Water",
        "due_time": datetime.now(),
        "priority": "high"
    })

    scheduler.schedule_task(pet.pet_id, {
        "description": "Evening play",
        "due_time": datetime.now(),
        "priority": "low"
    })

    tasks = scheduler.get_tasks_by_pet(pet.pet_id)
    assert len(tasks) == 3

    # check pet task count from owner aggregate
    all_tasks = owner.get_all_tasks()
    assert len(all_tasks) == 3


def test_scheduler_task_filter_by_pet_and_status():
    system = init_pawpal_system(":memory:")
    assert system["status"] == "initialized"

    db = system["db"]
    owner = Owner(owner_id="owner-test-2", name="Tester2", email="tester2@example.com", db=db)

    pet_a = owner.add_pet({"name": "Bella", "type": "dog", "breed": "Pug", "age": 3, "care_needs": {"walk": "daily"}})
    pet_b = owner.add_pet({"name": "Chirpy", "type": "bird", "breed": "Canary", "age": 1, "care_needs": {"feed": "daily"}})

    constraints = Constraints(start_date=date.today(), end_date=date.today())
    scheduler = Scheduler(owner, constraints, db)

    scheduler.schedule_task(pet_a.pet_id, {"description": "Walk Bella", "due_time": datetime.now(), "priority": "high"})
    t2 = scheduler.schedule_task(pet_a.pet_id, {"description": "Play Bella", "due_time": datetime.now(), "priority": "medium"})
    scheduler.schedule_task(pet_b.pet_id, {"description": "Feed Chirpy", "due_time": datetime.now(), "priority": "high"})

    # Mark one as done
    scheduler.mark_task_done(t2.task_id)

    pet_a_all = scheduler.get_tasks(pet_id=pet_a.pet_id)
    assert len(pet_a_all) == 2

    pet_a_pending = scheduler.get_tasks(pet_id=pet_a.pet_id, status="pending")
    assert len(pet_a_pending) == 1
    assert pet_a_pending[0].description == "Walk Bella"

    done_tasks = scheduler.get_tasks(status="done")
    assert len(done_tasks) == 1
    assert done_tasks[0].description == "Play Bella"



def test_recurring_task_recreates_next_occurrence():
    system = init_pawpal_system(":memory:")
    assert system["status"] == "initialized"

    db = system["db"]
    owner = Owner(owner_id="owner-test-3", name="Tester3", email="tester3@example.com", db=db)
    pet = owner.add_pet({"name": "Socks", "type": "cat", "breed": "Tabby", "age": 4, "care_needs": {"feed": "daily"}})

    constraints = Constraints(start_date=date.today(), end_date=date.today())
    scheduler = Scheduler(owner, constraints, db)

    daily_task = scheduler.schedule_task(pet.pet_id, {
        "description": "Feed Socks",
        "due_time": datetime.now(),
        "priority": "high",
        "frequency": "daily"
    })

    scheduler.mark_task_done(daily_task.task_id)

    pending = scheduler.get_tasks(status="pending")
    assert any(t.description == "Feed Socks" and t.task_id != daily_task.task_id for t in pending), "New daily occurrence should be created"


# ── RAG Retriever Tests ────────────────────────────────────────────────────────

def test_retriever_loads_knowledge_base():
    kb_dir = str(Path(__file__).resolve().parents[1] / "knowledge_base")
    retriever = PetCareRetriever(knowledge_dir=kb_dir)
    assert len(retriever.chunks) > 0, "Should load at least one chunk from the knowledge base"
    assert retriever.matrix is not None, "TF-IDF matrix should be built"


def test_retriever_returns_relevant_results():
    kb_dir = str(Path(__file__).resolve().parents[1] / "knowledge_base")
    retriever = PetCareRetriever(knowledge_dir=kb_dir)
    results = retriever.search("how often should I feed my dog")
    assert len(results) > 0, "Should return at least one result for a dog feeding query"
    combined = " ".join(results).lower()
    assert "dog" in combined or "feed" in combined or "meal" in combined


def test_retriever_returns_empty_for_blank_query():
    kb_dir = str(Path(__file__).resolve().parents[1] / "knowledge_base")
    retriever = PetCareRetriever(knowledge_dir=kb_dir)
    assert retriever.search("") == [], "Blank query should return empty list"
    assert retriever.search("   ") == [], "Whitespace-only query should return empty list"


def test_retriever_handles_missing_directory():
    retriever = PetCareRetriever(knowledge_dir="nonexistent_dir")
    assert retriever.chunks == [], "Should have no chunks if directory is missing"
    assert retriever.search("dog food") == [], "Search on empty retriever should return []"


# ── Guardrail Tests ────────────────────────────────────────────────────────────

def test_validate_input_accepts_valid_message():
    ok, msg = validate_input("How often should I feed my cat?")
    assert ok is True
    assert msg == ""


def test_validate_input_rejects_empty():
    ok, _ = validate_input("")
    assert ok is False
    ok, _ = validate_input("   ")
    assert ok is False


def test_validate_input_rejects_too_long():
    ok, _ = validate_input("x" * 501)
    assert ok is False


def test_validate_input_rejects_too_short():
    ok, _ = validate_input("a")
    assert ok is False


# ── Agent Tool Tests (mocked Anthropic client) ─────────────────────────────────

def _make_agent_with_owner():
    """Helper: create an in-memory system and a PawPalAgent with a real owner."""
    system = init_pawpal_system(":memory:")
    db = system["db"]
    owner = Owner(owner_id="agent-test-owner", name="Test", email="test@example.com", db=db)
    owner.add_pet({"name": "Buddy", "type": "dog", "breed": "Lab", "age": 3, "care_needs": {"feed": "daily"}})
    tasks: list = []
    agent = PawPalAgent(owner=owner, db=db, tasks=tasks, api_key="test-key")
    return agent, tasks


def test_agent_tool_list_tasks_empty():
    agent, _ = _make_agent_with_owner()
    result = agent._run_tool("list_tasks", {})
    assert result == "No tasks found."


def test_agent_tool_add_task_success():
    agent, tasks = _make_agent_with_owner()
    today = datetime.now().strftime("%Y-%m-%d")
    result = agent._run_tool("add_task", {
        "title": "Morning walk",
        "pet_name": "Buddy",
        "priority": "high",
        "due_date": today,
        "due_time": "08:00",
        "duration_minutes": 30,
    })
    assert "Morning walk" in result
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Morning walk"


def test_agent_tool_add_task_unknown_pet():
    agent, tasks = _make_agent_with_owner()
    today = datetime.now().strftime("%Y-%m-%d")
    result = agent._run_tool("add_task", {
        "title": "Feed",
        "pet_name": "NoSuchPet",
        "priority": "medium",
        "due_date": today,
        "due_time": "09:00",
    })
    assert "not found" in result.lower()
    assert len(tasks) == 0


def test_agent_tool_list_tasks_after_add():
    agent, tasks = _make_agent_with_owner()
    today = datetime.now().strftime("%Y-%m-%d")
    agent._run_tool("add_task", {
        "title": "Evening feed",
        "pet_name": "Buddy",
        "priority": "medium",
        "due_date": today,
        "due_time": "18:00",
    })
    result = agent._run_tool("list_tasks", {})
    assert "Evening feed" in result


def test_agent_tool_search_knowledge_returns_content():
    kb_dir = str(Path(__file__).resolve().parents[1] / "knowledge_base")
    system = init_pawpal_system(":memory:")
    agent = PawPalAgent(owner=None, db=system["db"], tasks=[], api_key="test-key")
    agent.retriever = PetCareRetriever(knowledge_dir=kb_dir)
    result = agent._run_tool("search_knowledge", {"query": "puppy vaccination schedule"})
    assert len(result) > 10, "Should return substantive knowledge base content"


def test_agent_chat_rejects_bad_input():
    agent, _ = _make_agent_with_owner()  # api_key="test-key" set in helper
    response, logs = agent.chat("", history=[])
    assert "error" in response.lower()
    assert logs == []


def test_agent_chat_calls_gemini_and_returns_text():
    agent, _ = _make_agent_with_owner()

    class FakePart:
        text = "Here is your care advice."
        function_call = None

    class FakeContent:
        parts = [FakePart()]

    class FakeCandidate:
        content = FakeContent()

    fake_response = MagicMock()
    fake_response.candidates = [FakeCandidate()]
    fake_response.text = "Here is your care advice."

    mock_session = MagicMock()
    mock_session.send_message.return_value = fake_response

    # Inject the mock session directly — no need to patch the SDK client
    response, logs = agent.chat("How should I care for my dog?", history=[], _session=mock_session)

    assert response == "Here is your care advice."
    assert logs == []

