import streamlit as st
from datetime import datetime, date
from pawpal_system import DBManager, Owner, Constraints, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Session-state-backed owner + task memory
if "pawpal" not in st.session_state:
    st.session_state.pawpal = {
        "db": DBManager(":memory:"),
        "owner": None,
        "tasks": []
    }

pawpal = st.session_state.pawpal

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan", key="owner_name")
pet_name = st.text_input("Pet name", value="Mochi", key="sample_pet_name")
species = st.selectbox("Species", ["dog", "cat", "other"], key="sample_species")

if st.button("Create owner"):
    if pawpal["owner"] is None:
        pawpal["owner"] = Owner(owner_id="owner-1", name=owner_name, email="owner@example.com", db=pawpal["db"])
        st.success(f"Owner '{owner_name}' created and stored in session.")
    else:
        st.info("Owner already exists in session.")

if pawpal["owner"] is not None:
    st.write("Owner in session:", pawpal["owner"].name)

# Add pet UI
st.subheader("Add Pet")
pet_name_input = st.text_input("Pet name", value="Mochi", key="add_pet_name")
pet_species = st.selectbox("Pet species", ["dog", "cat", "other"], index=0, key="add_pet_species")
pet_breed = st.text_input("Breed", value="", key="add_pet_breed")
pet_age = st.number_input("Age", min_value=0, max_value=30, value=2, key="add_pet_age")

if st.button("Add pet"):
    if pawpal["owner"] is None:
        st.warning("Create an owner first before adding a pet.")
    else:
        new_pet = pawpal["owner"].add_pet({
            "name": pet_name_input,
            "type": pet_species,
            "breed": pet_breed,
            "age": pet_age,
            "care_needs": {"feed": "daily"}
        })
        st.success(f"Added pet: {new_pet.name} (id: {new_pet.pet_id})")

if pawpal["owner"] is not None:
    pawpal["owner"].get_pet_list()
    st.write("Owned pets:")
    for pet in pawpal["owner"].pets:
        st.write(f"- {pet.name} ({pet.type}, age {pet.age})")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in pawpal:
    pawpal["tasks"] = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk", key="task_title")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20, key="task_duration")
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="task_priority")

if st.button("Add task"):
    task = {"title": task_title, "duration_minutes": int(duration), "priority": priority, "pet": pet_name}
    pawpal["tasks"].append(task)
    st.success("Task added to session state")

if pawpal["tasks"]:
    st.write("Current tasks:")
    st.table(pawpal["tasks"])
else:
    st.info("No tasks yet. Add one above.")

st.write("Debug st.session_state.pawpal:", pawpal)

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if pawpal["owner"] is None:
        st.warning("Create an owner and pets before generating schedule.")
    else:
        constraints = Constraints(start_date=date.today(), end_date=date.today())
        scheduler = Scheduler(pawpal["owner"], constraints, pawpal["db"])

        # Use either session-task list or DB-toy tasks built by the owner
        for t in pawpal["tasks"]:
            # Map to Scheduler's schedule_task API
            available_pets = pawpal["owner"].pets
            if not available_pets:
                continue
            target_pet = available_pets[0]
            scheduler.schedule_task(target_pet.pet_id, {
                "description": t["title"],
                "due_time": datetime.now(),
                "priority": t.get("priority", "medium"),
                "status": "pending"
            })

        output = scheduler.get_upcoming_tasks(limit=10)
        if output:
            st.success("Today's schedule:")
            for i, task in enumerate(output, start=1):
                st.write(f"{i}. [{task.priority}] {task.description} (Pet: {task.pet_id}) @ {task.due_time.strftime('%H:%M')} - {task.status}")
        else:
            st.info("No tasks available yet. Add some tasks first.")

