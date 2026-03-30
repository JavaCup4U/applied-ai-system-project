from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
import sqlite3
import uuid
import heapq
from abc import ABC, abstractmethod

# == DB helper for Pet and Task ==
class DBManager:
    def __init__(self, db_path: str = "pawpal.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._conn = sqlite3.connect(self.db_path)
        self._init_tables()


    def _connect(self):
        if self._conn:
            return self._conn
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pets (
                    pet_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    breed TEXT,
                    age INTEGER,
                    care_needs TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    pet_id TEXT,
                    description TEXT NOT NULL,
                    due_time TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',                    frequency TEXT,                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (pet_id) REFERENCES pets(pet_id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
                """
            )
            # Add indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_time ON tasks(due_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pets_user ON pets(user_id)")
            conn.commit()

    def execute(self, query: str, params: tuple = ()):
        """Execute a write query (INSERT, UPDATE, DELETE)."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
        finally:
            if self._conn is None:
                conn.close()

    def fetch_all(self, query: str, params: tuple = ()) -> List[tuple]:
        """Fetch all results from a SELECT query."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
        finally:
            if self._conn is None:
                conn.close()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """Fetch one result from a SELECT query."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
        finally:
            if self._conn is None:
                conn.close()

    def batch_insert_tasks(self, tasks: List[Task]):
        """Batch insert multiple tasks for efficiency."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            data = [t.to_db_tuple() for t in tasks]
            cursor.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)", data)
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
        finally:
            if self._conn is None:
                conn.close()


# == Validation Mixin ==
class ValidatorMixin:
    @staticmethod
    def validate_string(value: str, field_name: str, min_len: int = 1, max_len: int = 255):
        if not isinstance(value, str) or len(value) < min_len or len(value) > max_len:
            raise ValueError(f"{field_name} must be a string between {min_len}-{max_len} chars.")
        return value

    @staticmethod
    def validate_age(age: int, field_name: str = "age"):
        if not isinstance(age, int) or age < 0 or age > 150:
            raise ValueError(f"{field_name} must be an integer between 0 and 150.")
        return age

    @staticmethod
    def validate_datetime(dt: datetime, field_name: str = "datetime"):
        if not isinstance(dt, datetime):
            raise ValueError(f"{field_name} must be a datetime object.")
        return dt

    @staticmethod
    def validate_priority(priority: str, valid_priorities: List[str] = None):
        if valid_priorities is None:
            valid_priorities = ["low", "medium", "high", "urgent"]
        if priority.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}.")
        return priority.lower()


# == Data entities (lightweight wrappers, persisted through DB manager) ==
@dataclass
class Pet(ValidatorMixin):
    pet_id: str
    user_id: str
    name: str
    type: str
    breed: str
    age: int
    care_needs: Dict[str, Any]
    tasks: List[Task] = field(default_factory=list)

    def __post_init__(self):
        self.validate_string(self.name, "name")
        self.validate_string(self.type, "type")
        self.validate_age(self.age)

    def add_task(self, task: Task):
        self.tasks.append(task)

    def remove_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def to_db_tuple(self):
        return (self.pet_id, self.user_id, self.name, self.type, self.breed, self.age, str(self.care_needs))


@dataclass
class Task(ValidatorMixin):
    task_id: str
    user_id: str
    description: str
    due_time: datetime
    priority: str
    status: str = "pending"
    pet_id: Optional[str] = None
    duration: int = 30  # minutes
    frequency: Optional[str] = None

    def __post_init__(self):
        self.validate_string(self.description, "description")
        self.validate_datetime(self.due_time, "due_time")
        self.validate_priority(self.priority)
        if self.frequency is not None and self.frequency not in ["daily", "weekly", "twice", "none"]:
            raise ValueError("frequency must be one of daily, weekly, twice, none")

    def mark_complete(self):
        """Mark the task as completed."""
        self.status = "done"

    def to_db_tuple(self):
        return (self.task_id, self.user_id, self.pet_id, self.description, self.due_time.isoformat(), self.priority, self.status, self.frequency)


# == Core app classes ==
class Owner(ValidatorMixin):
    def __init__(self, owner_id: str, name: str, email: str, db: DBManager):
        self.owner_id = owner_id
        self.name = self.validate_string(name, "name")
        self.email = self.validate_string(email, "email")
        self.pets: List[Pet] = []
        self.preferences: Dict[str, Any] = {}
        self.db = db
        self._pets_loaded = False
        self._save_to_db()

    def _save_to_db(self):
        """Persist owner to database."""
        try:
            self.db.execute(
                "INSERT OR IGNORE INTO users (user_id, name, email) VALUES (?, ?, ?)",
                (self.owner_id, self.name, self.email)
            )
        except RuntimeError as e:
            print(f"Warning: Could not save owner to DB: {e}")

    def add_pet(self, pet_data: Dict[str, Any]):
        """Add a new pet and persist to DB."""
        try:
            pet_id = str(uuid.uuid4())
            pet = Pet(
                pet_id=pet_id,
                user_id=self.owner_id,
                name=pet_data["name"],
                type=pet_data["type"],
                breed=pet_data.get("breed", ""),
                age=pet_data.get("age", 0),
                care_needs=pet_data.get("care_needs", {})
            )
            self.db.execute(
                "INSERT INTO pets (pet_id, user_id, name, type, breed, age, care_needs) VALUES (?, ?, ?, ?, ?, ?, ?)",
                pet.to_db_tuple()
            )
            self.pets.append(pet)
            return pet
        except (ValueError, RuntimeError, KeyError) as e:
            raise RuntimeError(f"Failed to add pet: {e}")

    def remove_pet(self, pet_id: str):
        """Remove a pet by ID."""
        try:
            self.db.execute("DELETE FROM pets WHERE pet_id = ? AND user_id = ?", (pet_id, self.owner_id))
            self.pets = [p for p in self.pets if p.pet_id != pet_id]
        except RuntimeError as e:
            raise RuntimeError(f"Failed to remove pet: {e}")

    def update_pet(self, pet_id: str, pet_data: Dict[str, Any]):
        """Update pet details."""
        try:
            pet = next((p for p in self.pets if p.pet_id == pet_id), None)
            if not pet:
                raise ValueError(f"Pet {pet_id} not found.")
            for key, value in pet_data.items():
                if hasattr(pet, key) and key not in ["pet_id", "user_id"]:
                    setattr(pet, key, value)
            self.db.execute(
                "UPDATE pets SET name = ?, type = ?, breed = ?, age = ?, care_needs = ? WHERE pet_id = ?",
                (pet.name, pet.type, pet.breed, pet.age, str(pet.care_needs), pet_id)
            )
        except (ValueError, RuntimeError) as e:
            raise RuntimeError(f"Failed to update pet: {e}")

    def update_preferences(self, prefs: Dict[str, Any]):
        """Update owner preferences."""
        self.preferences.update(prefs)

    def get_profile(self) -> Dict[str, Any]:
        """Return owner profile summary."""
        return {
            "owner_id": self.owner_id,
            "name": self.name,
            "email": self.email,
            "pet_count": len(self.pets),
            "preferences": self.preferences
        }

    def get_pet_list(self, limit: Optional[int] = None) -> List[Pet]:
        """Fetch pets from DB, with optional limit for pagination."""
        try:
            query = "SELECT * FROM pets WHERE user_id = ?"
            params = [self.owner_id]
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            rows = self.db.fetch_all(query, tuple(params))
            self.pets = [
                Pet(
                    pet_id=row[0],
                    user_id=row[1],
                    name=row[2],
                    type=row[3],
                    breed=row[4],
                    age=row[5],
                    care_needs=eval(row[6]) if isinstance(row[6], str) else row[6]
                )
                for row in rows
            ]
            return self.pets
        except (RuntimeError, ValueError) as e:
            print(f"Warning: Could not fetch pets: {e}")
            return self.pets

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across all owned pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


# Backward compatibility alias
User = Owner


class Scheduler:
    """The brain that retrieves, organizes, and manages tasks across pets."""

    def __init__(self, owner: Owner, constraints: Constraints, db: DBManager):
        self.owner = owner
        self.constraints = constraints
        self.db = db

    def _load_owner_pets(self, limit: Optional[int] = None):
        self.owner.get_pet_list(limit=limit)

    def collect_tasks(self) -> List[Task]:
        """Fetch all tasks for an owner, from DB, and attach them to the pets."""
        self._load_owner_pets()
        # Reset pet task lists before assignment
        for pet in self.owner.pets:
            pet.tasks = []

        rows = self.db.fetch_all(
            "SELECT task_id, user_id, pet_id, description, due_time, priority, status, frequency FROM tasks WHERE user_id = ?",
            (self.owner.owner_id,)
        )

        all_tasks: List[Task] = []
        for row in rows:
            task = Task(
                task_id=row[0],
                user_id=row[1],
                pet_id=row[2],
                description=row[3],
                due_time=datetime.fromisoformat(row[4]),
                priority=row[5],
                status=row[6],
                frequency=row[7] if len(row) > 7 else None
            )
            all_tasks.append(task)
            pet = next((p for p in self.owner.pets if p.pet_id == task.pet_id), None)
            if pet:
                pet.add_task(task)

        return all_tasks

    def get_tasks(self, pet_id: Optional[str] = None, status: Optional[str] = None, limit: Optional[int] = None) -> List[Task]:
        """Retrieve owner tasks, optionally filtered by pet ID and status.

        Includes support for pagination via `limit`.
        Returns a list of Task objects (with frequency where available).
        """
        self._load_owner_pets()
        query = "SELECT task_id, user_id, pet_id, description, due_time, priority, status, frequency FROM tasks WHERE user_id = ?"
        params = [self.owner.owner_id]

        if pet_id is not None:
            query += " AND pet_id = ?"
            params.append(pet_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.db.fetch_all(query, tuple(params))
        tasks = []
        for row in rows:
            task = Task(
                task_id=row[0],
                user_id=row[1],
                pet_id=row[2],
                description=row[3],
                due_time=datetime.fromisoformat(row[4]),
                priority=row[5],
                status=row[6],
                frequency=row[7] if len(row) > 7 else None
            )
            tasks.append(task)

        if pet_id is not None:
            pet = next((p for p in self.owner.pets if p.pet_id == pet_id), None)
            if pet:
                pet.tasks = tasks

        return tasks

    def get_tasks_by_pet(self, pet_id: str) -> List[Task]:
        """Get all tasks assigned to one pet by pet ID."""
        return self.get_tasks(pet_id=pet_id)

    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Return tasks sorted by `due_time` ascending."""
        tasks = tasks if tasks is not None else self.collect_tasks()
        return sorted(tasks, key=lambda t: t.due_time)

    def get_upcoming_tasks(self, limit: int = 10) -> List[Task]:
        """Get upcoming tasks for owner by due_time."""
        tasks = self.collect_tasks()
        return sorted([t for t in tasks if t.status != "done"], key=lambda t: t.due_time)[:limit]

    def schedule_task(self, pet_id: str, task_data: Dict[str, Any]) -> Task:
        """Create and assign a task to a pet, with constraint validation.

        `task_data` may include fields:
            - description
            - due_time
            - priority
            - status
            - frequency
        """
        pet = next((p for p in self.owner.pets if p.pet_id == pet_id), None)
        if not pet:
            raise ValueError(f"Pet {pet_id} not found.")

        task = Task(
            task_id=str(uuid.uuid4()),
            user_id=self.owner.owner_id,
            pet_id=pet_id,
            description=task_data["description"],
            due_time=task_data["due_time"],
            priority=task_data.get("priority", "medium"),
            status=task_data.get("status", "pending"),
            frequency=task_data.get("frequency")
        )

        if not self.constraints.check_constraint(task):
            raise RuntimeError("Task conflicts with current constraints")

        self.db.execute(
            "INSERT INTO tasks (task_id, user_id, pet_id, description, due_time, priority, status, frequency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            task.to_db_tuple()
        )
        pet.add_task(task)
        return task

    def mark_task_done(self, task_id: str):
        """Mark a task done in DB/internal state and create next recurring instance.

        If a task is `daily` or `weekly`, it creates a new pending task for next interval,
        respecting constraints when possible.
        """
        self.db.execute("UPDATE tasks SET status = 'done' WHERE task_id = ?", (task_id,))

        found_task = None
        for p in self.owner.pets:
            for t in p.tasks:
                if t.task_id == task_id:
                    t.status = 'done'
                    found_task = t
                    break
            if found_task:
                break

        if not found_task:
            # Load from DB if not in-memory
            row = self.db.fetch_one(
                "SELECT task_id, user_id, pet_id, description, due_time, priority, status, frequency FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            if row:
                found_task = Task(
                    task_id=row[0],
                    user_id=row[1],
                    pet_id=row[2],
                    description=row[3],
                    due_time=datetime.fromisoformat(row[4]),
                    priority=row[5],
                    status=row[6],
                    frequency=row[7] if len(row) > 7 else None
                )

        if found_task and found_task.frequency in ["daily", "weekly"]:
            interval = timedelta(days=1 if found_task.frequency == "daily" else 7)
            next_due = found_task.due_time + interval
            new_task_data = {
                "description": found_task.description,
                "due_time": next_due,
                "priority": found_task.priority,
                "status": "pending",
                "frequency": found_task.frequency
            }
            # Try constraint-aware scheduling first, fallback to direct insert when out of current constraint bounds
            try:
                self.schedule_task(found_task.pet_id, new_task_data)
            except Exception:
                # direct create when recurring outside current constraint range
                next_task = Task(
                    task_id=str(uuid.uuid4()),
                    user_id=found_task.user_id,
                    description=found_task.description,
                    due_time=next_due,
                    priority=found_task.priority,
                    status="pending",
                    pet_id=found_task.pet_id,
                    frequency=found_task.frequency
                )
                self.db.execute(
                    "INSERT INTO tasks (task_id, user_id, pet_id, description, due_time, priority, status, frequency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    next_task.to_db_tuple()
                )
                pet = next((p for p in self.owner.pets if p.pet_id == found_task.pet_id), None)
                if pet:
                    pet.add_task(next_task)


    def schedule_with_greedy_priority(self, tasks: List[Task]) -> List[Task]:
        """Schedule tasks using a greedy priority-based algorithm."""
        priority_weights = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
        # Use heapq for min-heap (negate weights for max-heap effect)
        task_heap = [(-priority_weights[t.priority], t.due_time, t) for t in tasks]
        heapq.heapify(task_heap)
        
        scheduled = []
        while task_heap:
            _, _, task = heapq.heappop(task_heap)
            if self.constraints.check_constraint(task):
                scheduled.append(task)
        return scheduled

    def optimize_slot(self, task: Task) -> datetime:
        """Optimize task slot based on owner preferences."""
        if "preferred_slots" in self.owner.preferences:
            for slot in self.owner.preferences["preferred_slots"]:
                start, end = slot.split("-")
                start_hour, start_min = map(int, start.split(":"))
                end_hour, end_min = map(int, end.split(":"))
                preferred_start = task.due_time.replace(hour=start_hour, minute=start_min)
                if preferred_start >= task.due_time and preferred_start + timedelta(minutes=task.duration) <= task.due_time.replace(hour=end_hour, minute=end_min):
                    return preferred_start
        return task.due_time


class Constraints(ValidatorMixin):
    def __init__(self, start_date: date, end_date: date):
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise ValueError("start_date and end_date must be date objects.")
        if start_date > end_date:
            raise ValueError("start_date must be before end_date.")
        self.start_date = start_date
        self.end_date = end_date
        self.blocked_times: List[str] = []  # e.g., ["09:00-10:00", "14:00-15:00"]
        self.required_activities: List[str] = []  # e.g., ["walk", "feed", "play"]
        self.extra_rules: Dict[str, Any] = {}  # flexible rule storage

    def add_constraint(self, key: str, value: Any):
        """Add a constraint rule."""
        if key == "blocked_times":
            if isinstance(value, str):
                self.blocked_times.append(value)
            elif isinstance(value, list):
                self.blocked_times.extend(value)
        elif key == "required_activities":
            if isinstance(value, str):
                self.required_activities.append(value)
            elif isinstance(value, list):
                self.required_activities.extend(value)
        else:
            self.extra_rules[key] = value

    def remove_constraint(self, key: str):
        """Remove a constraint rule by key."""
        if key in self.extra_rules:
            del self.extra_rules[key]
        else:
            raise KeyError(f"Constraint key {key} not found.")

    def check_constraint(self, task: Task, schedule: Optional['Schedule'] = None) -> bool:
        """Verify if a task satisfies all constraints."""
        try:
            # Check date range
            task_date = task.due_time.date()
            if not (self.start_date <= task_date <= self.end_date):
                return False
            # Check blocked times
            task_time = task.due_time.strftime("%H:%M")
            if self._time_in_blocked_range(task_time):
                return False
            # Check required activities (simplified)
            if self.required_activities and task.description not in self.required_activities:
                return False
            # Check for overlaps if schedule provided
            if schedule and self.check_overlap(task, schedule.tasks):
                return False
            return True
        except Exception as e:
            print(f"Warning: Error checking constraints: {e}")
            return False

    def check_overlap(self, new_task: Task, existing_tasks: List[Task]) -> bool:
        """Check if new_task overlaps with any existing tasks."""
        new_end = new_task.due_time + timedelta(minutes=new_task.duration)
        for task in existing_tasks:
            task_end = task.due_time + timedelta(minutes=task.duration)
            if max(new_task.due_time, task.due_time) < min(new_end, task_end):
                return True  # Overlap detected
        return False

    def _time_in_blocked_range(self, time_str: str) -> bool:
        """Helper to check if a time falls in any blocked range."""
        try:
            for blocked in self.blocked_times:
                start, end = blocked.split("-")
                if start <= time_str <= end:
                    return True
            return False
        except (ValueError, IndexError):
            return False


class Schedule(ValidatorMixin):
    def __init__(self, constraints: Constraints, db: DBManager):
        self.schedule_id = str(uuid.uuid4())
        self.tasks: List[Task] = []
        self.constraints = constraints
        self.db = db
        self._tasks_synced = False

    def create_schedule(self, user: User, plan: 'Plan'):
        """Generate a schedule based on user, preferences, and constraints."""
        try:
            # Placeholder: apply plan logic to generate tasks
            # This will be fully implemented during the planning stage
            pass
        except Exception as e:
            raise RuntimeError(f"Failed to create schedule: {e}")

    def update_schedule(self, changes: Dict[str, Any]):
        """Update schedule metadata or task details."""
        try:
            for key, value in changes.items():
                if hasattr(self, key) and key not in ["db", "tasks", "schedule_id"]:
                    setattr(self, key, value)
        except Exception as e:
            raise RuntimeError(f"Failed to update schedule: {e}")

    def get_next_tasks(self, limit: int = 5) -> List[Task]:
        """Fetch upcoming tasks from DB with pagination."""
        try:
            query = "SELECT * FROM tasks WHERE status != 'done' ORDER BY due_time ASC LIMIT ?"
            rows = self.db.fetch_all(query, (limit,))
            tasks = [
                Task(
                    task_id=row[0],
                    user_id=row[1],
                    pet_id=row[2],
                    description=row[3],
                    due_time=datetime.fromisoformat(row[4]),
                    priority=row[5],
                    status=row[6]
                )
                for row in rows
            ]
            self.tasks = tasks
            return tasks
        except (RuntimeError, ValueError) as e:
            print(f"Warning: Could not fetch next tasks: {e}")
            return []

    def get_schedule_for_date(self, query_date: date) -> List[Task]:
        """Fetch all tasks for a specific date."""
        try:
            query = "SELECT * FROM tasks WHERE DATE(due_time) = ? ORDER BY due_time ASC"
            rows = self.db.fetch_all(query, (query_date.isoformat(),))
            tasks = [
                Task(
                    task_id=row[0],
                    user_id=row[1],
                    pet_id=row[2],
                    description=row[3],
                    due_time=datetime.fromisoformat(row[4]),
                    priority=row[5],
                    status=row[6]
                )
                for row in rows
            ]
            return tasks
        except (RuntimeError, ValueError) as e:
            print(f"Warning: Could not fetch tasks for date {query_date}: {e}")
            return []

    def add_task(self, task_data: Dict[str, Any]):
        """Create and persist a new task."""
        try:
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                user_id=task_data["user_id"],
                description=task_data["description"],
                due_time=task_data["due_time"],
                priority=task_data.get("priority", "medium"),
                status=task_data.get("status", "pending"),
                pet_id=task_data.get("pet_id"),
                frequency=task_data.get("frequency")
            )
            # Validate against constraints before inserting
            if not self.constraints.check_constraint(task):
                print(f"Warning: Task violates constraints.")
            self.db.execute(
                "INSERT INTO tasks (task_id, user_id, pet_id, description, due_time, priority, status, frequency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                task.to_db_tuple()
            )
            self.tasks.append(task)
            return task
        except (ValueError, RuntimeError, KeyError) as e:
            raise RuntimeError(f"Failed to add task: {e}")

    def remove_task(self, task_id: str):
        """Delete a task by ID."""
        try:
            self.db.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            self.tasks = [t for t in self.tasks if t.task_id != task_id]
        except RuntimeError as e:
            raise RuntimeError(f"Failed to remove task: {e}")

    def mark_task_done(self, task_id: str):
        """Mark a task as completed."""
        try:
            self.db.execute("UPDATE tasks SET status = 'done' WHERE task_id = ?", (task_id,))
            task = next((t for t in self.tasks if t.task_id == task_id), None)
            if task:
                task.status = "done"
        except RuntimeError as e:
            raise RuntimeError(f"Failed to mark task done: {e}")


class Plan(ValidatorMixin):
    def __init__(self, plan_id: Optional[str], user: User, constraints: Constraints, schedule: Schedule):
        self.plan_id = plan_id or str(uuid.uuid4())
        self.user = user
        self.constraints = constraints
        self.schedule = schedule
        self.generated_at: Optional[datetime] = None
        self.evaluation_score: float = 0.0

    def generate_plan(self):
        """Generate a comprehensive schedule plan."""
        try:
            self.generated_at = datetime.now()
            # Step 1: Apply user preferences to determine priority tasks
            prioritized_tasks = self._build_priority_tasks(self.constraints.start_date, self.constraints.end_date)
            # Step 2: Schedule tasks respecting constraints
            valid_tasks = []
            for task_data in prioritized_tasks:
                task = Task(
                    task_id=str(uuid.uuid4()),
                    user_id=self.user.user_id,
                    description=task_data["description"],
                    due_time=task_data["due_time"],
                    priority=task_data["priority"],
                    pet_id=task_data.get("pet_id")
                )
                # Optimize slot
                task.due_time = self.schedule.optimize_slot(task)
                if self.constraints.check_constraint(task, self.schedule):
                    valid_tasks.append(task)
                    self.schedule.tasks.append(task)  # Add to schedule list
            # Batch insert valid tasks
            if valid_tasks:
                self.schedule.db.batch_insert_tasks(valid_tasks)
            return {"status": "success", "plan_id": self.plan_id, "tasks_scheduled": len(self.schedule.tasks)}
        except Exception as e:
            raise RuntimeError(f"Failed to generate plan: {e}")

    def evaluate_plan(self) -> Dict[str, Any]:
        """Evaluate plan quality based on coverage and constraint satisfaction."""
        try:
            total_tasks = len(self.schedule.tasks)
            if total_tasks == 0:
                self.evaluation_score = 0.0
                return {"score": 0.0, "reason": "No tasks scheduled."}
            # Simple scoring: check how many tasks satisfy constraints
            compliant_tasks = sum(
                1 for task in self.schedule.tasks
                if self.constraints.check_constraint(task)
            )
            self.evaluation_score = (compliant_tasks / total_tasks) * 100
            return {
                "score": self.evaluation_score,
                "compliant_tasks": compliant_tasks,
                "total_tasks": total_tasks
            }
        except Exception as e:
            print(f"Warning: Evaluation failed: {e}")
            return {"score": 0.0, "error": str(e)}

    def adjust_for_constraints(self, constraints: Constraints):
        """Re-optimize schedule around new constraints."""
        try:
            self.constraints = constraints
            # Re-validate all tasks and mark violating ones as pending
            for task in self.schedule.tasks:
                if not constraints.check_constraint(task):
                    task.status = "pending"
        except Exception as e:
            raise RuntimeError(f"Failed to adjust constraints: {e}")

    def apply_user_preferences(self):
        """Tailor schedule to user preferences."""
        try:
            if "preferred_times" in self.user.preferences:
                # Adjust task scheduling around preferred times
                pass
            if "frequency" in self.user.preferences:
                # Adjust task frequency based on user preferences
                pass
        except Exception as e:
            print(f"Warning: Could not apply user preferences: {e}")

    def _build_priority_tasks(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Build a priority-ordered list of recurring tasks based on user pets and preferences."""
        tasks = []
        current_date = start_date
        while current_date <= end_date:
            for pet in self.user.pets:
                if pet.care_needs:
                    for care_type, freq in pet.care_needs.items():
                        if freq == "daily":
                            tasks.append(self._create_task(pet, care_type, current_date, "08:00"))
                        elif freq == "twice":
                            tasks.extend([
                                self._create_task(pet, care_type, current_date, "08:00"),
                                self._create_task(pet, care_type, current_date, "18:00")
                            ])
            current_date += timedelta(days=1)
        return tasks

    def _create_task(self, pet: Pet, care_type: str, task_date: date, time_str: str) -> Dict[str, Any]:
        """Helper to create a task dict."""
        hour, minute = map(int, time_str.split(":"))
        due_time = datetime.combine(task_date, datetime.min.time()).replace(hour=hour, minute=minute)
        return {
            "user_id": self.user.user_id,
            "pet_id": pet.pet_id,
            "description": f"{care_type} for {pet.name}",
            "due_time": due_time,
            "priority": "high" if care_type in ["feed", "meds"] else "medium",
            "frequency": freq
        }


# == System Initialization ==
def init_pawpal_system(db_path: str = "pawpal.db") -> Dict[str, Any]:
    """Initialize the PawPal system with database and core components."""
    try:
        dbm = DBManager(db_path)
        return {
            "db": dbm,
            "status": "initialized",
            "db_path": db_path
        }
    except Exception as e:
        print(f"Error initializing PawPal system: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Example usage
    system = init_pawpal_system()
    if system["status"] == "initialized":
        print(f"✓ PawPal system initialized at {system['db_path']}")
    else:
        print(f"✗ Failed to initialize: {system.get('error', 'Unknown error')}")
