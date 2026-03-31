# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.


## Features Summary

### Core Data Management
- **Persistent Database**: SQLite-based storage with connection management, batch operations, and indexed queries for performance optimization
- **Owner/User Management**: Create and maintain owner profiles with preferences, email, and pet associations
- **Pet Management**: Add, remove, and update multiple pets per owner with species, breed, age, and care needs tracking
- **Task Entity Model**: Tasks with unique IDs, descriptions, priorities (low/medium/high/urgent), duration, due times, status (pending/done), and frequency (daily/weekly/once/none)

### Validation & Data Integrity
- **Validator Mixin**: Input validation for strings, ages, datetime objects, and priority levels
- **Data Constraints**: Date range validation, age bounds checking, and type safety enforcement across all data entities
- **Database Integrity**: Foreign key relationships, indexes on high-query columns (due_time, user_status), and error handling for database operations

### Task Scheduling Algorithms
- **Greedy Priority-Based Scheduling**: Uses a min-heap (via heapq) to sort and schedule tasks by priority weight (urgent=4, high=3, medium=2, low=1) and due time, selecting constraint-compliant tasks in order
- **Time Slot Optimization**: Adjusts task timing to align with owner-defined preferred time slots (e.g., morning/afternoon/evening windows)
- **Overlap Detection**: Checks for scheduling conflicts by calculating task duration and comparing time ranges against existing tasks
- **Recurring Task Auto-Generation**: Automatically creates next instances of daily/weekly tasks with constraint-aware validation and fallback scheduling

### Constraint Management
- **Time-Based Constraints**: Define date range boundaries (start_date to end_date) and blocked time windows (e.g., "09:00-10:00")
- **Activity Requirements**: Specify required care activities that must appear in the schedule
- **Flexible Rule Storage**: Extensible extra_rules dictionary for custom constraint attributes
- **Constraint Checking**: Multi-level constraint validation (date range, blocked times, required activities, overlap detection) with exception safety

### Plan Generation & Optimization
- **Priority-Ordered Task Building**: Generates recurring tasks based on pet care needs, scheduling them daily or twice-daily based on frequency preferences
- **Preference-Driven Scheduling**: Incorporates owner preferences for preferred times, frequencies, and activity types into plan creation
- **Constraint-Aware Planning**: Validates each task against constraints during plan generation with fallback for out-of-range recurring tasks
- **Batch Task Insertion**: Efficiently persists multiple scheduled tasks to database in a single operation
- **Plan Evaluation Scoring**: Calculates plan quality score based on constraint compliance percentage (compliant_tasks / total_tasks × 100)

### Task Query & Filtering
- **Flexible Task Retrieval**: Query tasks by status, pet ID, with pagination support (limit parameter)
- **Pet-Based Filtering**: Get all tasks for a specific pet or across all owner pets
- **Upcoming Task Retrieval**: Sort pending tasks by due time to identify next actions
- **Date-Based Queries**: Retrieve schedules for specific dates

### Recurring Task Management
- **Frequency Support**: Track task recurrence patterns (daily, weekly, once, none)
- **Automatic Rescheduling**: When marking a recurring task as done, automatically create next instance with updated due date
- **Constraint-Respecting Recurrence**: New recurring instances respect current constraints, with fallback direct insert when outside constraint bounds

### UI Integration
- **Streamlit Application**: Web-based interface for owner/pet registration, task management, and plan visualization
- **Session State Management**: Maintain owner, pet, and task state across user interactions
- **Interactive Inputs**: Forms for creating owners, adding pets, defining tasks with real-time feedback

## Testing PawPal+

Run tests with:
```bash
python -m pytest
```

### Test Coverage:
- Task creation and retrieval
- Scheduling logic with priority and time constraint validation
- Marking tasks as done and auto-scheduling recurring tasks
- Task filtering by pet ID and status
- Multi-pet ownership scenarios

### Confidence Level: ⭐⭐⭐⭐ (4/5 stars) 

## Screenshot 
<a href="/course_images/ai110/your_screenshot_name.png" target="_blank"><img src='/screenshots/demo.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>.