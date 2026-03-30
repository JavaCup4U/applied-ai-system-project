from datetime import datetime, timedelta, date
from pawpal_system import init_pawpal_system, Owner, Constraints, Scheduler


def main():
    system = init_pawpal_system("pawpal.db")
    if system.get("status") != "initialized":
        print("Failed to initialize PawPal system:", system.get("error"))
        return

    db = system["db"]

    # 1) Create owner
    owner = Owner(owner_id="owner-1", name="Alice", email="alice@example.com", db=db)

    # 2) Add two pets
    pet1 = owner.add_pet({
        "name": "Mittens",
        "type": "cat",
        "breed": "Siamese",
        "age": 3,
        "care_needs": {"feed": "daily", "play": "twice"}
    })

    pet2 = owner.add_pet({
        "name": "Rex",
        "type": "dog",
        "breed": "Labrador",
        "age": 5,
        "care_needs": {"walk": "daily", "train": "weekly"}
    })

    # 3) Create constraints
    constraints = Constraints(start_date=date.today(), end_date=date.today())

    # 4) Create scheduler
    scheduler = Scheduler(owner, constraints, db)

    # 5) Add at least three tasks with different times
    now = datetime.now()
    tasks = [
        scheduler.schedule_task(pet1.pet_id, {
            "description": "Feed Mittens",
            "due_time": now.replace(hour=8, minute=0, second=0, microsecond=0),
            "priority": "high"
        }),
        scheduler.schedule_task(pet2.pet_id, {
            "description": "Walk Rex",
            "due_time": now.replace(hour=10, minute=30, second=0, microsecond=0),
            "priority": "medium"
        }),
        scheduler.schedule_task(pet1.pet_id, {
            "description": "Play with Mittens",
            "due_time": now.replace(hour=18, minute=0, second=0, microsecond=0),
            "priority": "low"
        })
    ]

    # 6) Print today's schedule
    print("\nToday's Schedule:")
    upcoming = scheduler.get_upcoming_tasks(limit=10)
    for i, t in enumerate(upcoming, start=1):
        print(f"{i}. [{t.priority}] {t.description} (Pet {t.pet_id}) at {t.due_time.strftime('%H:%M')} - {t.status}")


if __name__ == "__main__":
    main()
