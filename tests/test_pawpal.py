from datetime import datetime, date
import sys
from pathlib import Path

# Ensure project root is on sys.path when running tests from tests/ folder.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from pawpal_system import init_pawpal_system, Owner, Constraints, Scheduler, Task


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

