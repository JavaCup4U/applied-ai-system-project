from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Any, Dict, List, Optional
import sqlite3

# == DB helper for Pet and Task ==
class DBManager:
    def __init__(self, db_path: str = "pawpal.db"):
        self.db_path = db_path
        self._init_tables()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pets (
                    pet_id TEXT PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    breed TEXT,
                    age INTEGER,
                    care_needs TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    description TEXT,
                    due_time TEXT,
                    priority TEXT,
                    status TEXT
                )
                """
            )
            conn.commit()

    def execute(self, query: str, params: tuple = ()):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor


# == Data entities (lightweight wrappers, persisted through DB manager) ==
@dataclass
class Pet:
    pet_id: str
    name: str
    type: str
    breed: str
    age: int
    care_needs: Dict[str, Any]

    def to_db_tuple(self):
        return (self.pet_id, self.name, self.type, self.breed, self.age, str(self.care_needs))


@dataclass
class Task:
    task_id: str
    description: str
    due_time: datetime
    priority: str
    status: str = "pending"

    def to_db_tuple(self):
        return (self.task_id, self.description, self.due_time.isoformat(), self.priority, self.status)


# == Core app classes ==
class User:
    def __init__(self, user_id: str, name: str, email: str, db: DBManager):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.pets: List[Pet] = []
        self.preferences: Dict[str, Any] = {}
        self.db = db

    def add_pet(self, pet_data: Dict[str, Any]):
        ...

    def remove_pet(self, pet_id: str):
        ...

    def update_pet(self, pet_id: str, pet_data: Dict[str, Any]):
        ...

    def update_preferences(self, prefs: Dict[str, Any]):
        ...

    def get_profile(self) -> Dict[str, Any]:
        ...

    def get_pet_list(self) -> List[Pet]:
        ...


class Constraints:
    def __init__(self, start_date: date, end_date: date):
        self.start_date = start_date
        self.end_date = end_date
        self.blocked_times: List[str] = []
        self.required_activities: List[str] = []
        self.extra_rules: Dict[str, Any] = {}

    def add_constraint(self, key: str, value: Any):
        ...

    def remove_constraint(self, key: str):
        ...

    def check_constraint(self, task: Task) -> bool:
        ...


class Schedule:
    def __init__(self, constraints: Constraints, db: DBManager):
        self.schedule_id: str = ""
        self.tasks: List[Task] = []
        self.constraints = constraints
        self.db = db

    def create_schedule(self, user: User, plan: Plan):
        ...

    def update_schedule(self, changes: Dict[str, Any]):
        ...

    def get_next_tasks(self, limit: int = 5) -> List[Task]:
        ...

    def get_schedule_for_date(self, query_date: date) -> List[Task]:
        ...

    def add_task(self, task_data: Dict[str, Any]):
        ...

    def remove_task(self, task_id: str):
        ...

    def mark_task_done(self, task_id: str):
        ...


class Plan:
    def __init__(self, plan_id: str, user: User, constraints: Constraints, schedule: Schedule):
        self.plan_id = plan_id
        self.user = user
        self.constraints = constraints
        self.schedule = schedule

    def generate_plan(self):
        ...

    def evaluate_plan(self) -> Dict[str, Any]:
        ...

    def adjust_for_constraints(self, constraints: Constraints):
        ...

    def apply_user_preferences(self):
        ...


# Optional helper for initialization
def init_pawpal_system(db_path: str = "pawpal.db") -> Dict[str, Any]:
    dbm = DBManager(db_path)
    return {"db": dbm}
