import streamlit as st
from datetime import datetime, date
from pawpal_system import DBManager, Owner, Constraints, Scheduler
from ai_assistant import PawPalAgent, validate_input

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

if "last_removed_task" not in st.session_state:
    st.session_state.last_removed_task = None

# Create tabs for better organization
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Owner & Pets", "✓ Tasks", "📅 Schedule", "🤖 AI Assistant", "🐾 Debug"])

# ====== TAB 1: OWNER & PETS ======
with tab1:
    st.subheader("Owner Setup")
    col1, col2 = st.columns([2, 1])
    with col1:
        owner_name = st.text_input("Owner name", value="Jordan", key="owner_name")
    with col2:
        if st.button("Create owner", use_container_width=True):
            if pawpal["owner"] is None:
                pawpal["owner"] = Owner(owner_id="owner-1", name=owner_name, email="owner@example.com", db=pawpal["db"])
                st.success(f"Owner '{owner_name}' created!")
            else:
                st.info("Owner already exists in session.")

    if pawpal["owner"] is not None:
        st.info(f"✓ Active owner: **{pawpal['owner'].name}**")
    
    st.divider()
    
    st.subheader("Add Pet")
    pet_col1, pet_col2 = st.columns(2)
    with pet_col1:
        pet_name_input = st.text_input("Pet name", value="Mochi", key="add_pet_name")
        pet_breed = st.text_input("Breed", value="", key="add_pet_breed")
    with pet_col2:
        pet_species = st.selectbox("Species", ["dog", "cat", "other"], index=0, key="add_pet_species")
        pet_age = st.number_input("Age", min_value=0, max_value=30, value=2, key="add_pet_age")

    if st.button("Add pet", use_container_width=True):
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

    st.divider()
    
    st.subheader("Your Pets")
    if pawpal["owner"] is not None:
        pawpal["owner"].get_pet_list()
        if pawpal["owner"].pets:
            for pet in pawpal["owner"].pets:
                st.write(f"🐕 **{pet.name}** • {pet.type.title()} • Age {pet.age}" + (f" • {pet.breed}" if pet.breed else ""))
        else:
            st.info("No pets added yet.")
    else:
        st.info("Create an owner first to see their pets.")


# ====== TAB 2: TASKS ======
with tab2:
    if "tasks" not in pawpal:
        pawpal["tasks"] = []

    st.subheader("Add New Task")
    add_col1, add_col2, add_col3 = st.columns(3)
    with add_col1:
        task_title = st.text_input("Task title", value="Morning walk", key="task_title")
    with add_col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="task_duration")
    with add_col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="task_priority")

    add_col4, add_col5 = st.columns(2)
    with add_col4:
        due_date = st.date_input("Date", value=date.today(), key="task_due_date")
    with add_col5:
        time_options = []
        for hour in range(1, 13):
            for minute in (0, 15, 30, 45):
                ampm = "AM" if hour < 12 else "PM"
                display_hour = hour if hour != 12 else 12
                time_options.append(f"{display_hour:02d}:{minute:02d} {ampm}")

        now_str = datetime.now().strftime('%I:%M %p')
        if now_str in time_options:
            default_index = time_options.index(now_str)
        else:
            now = datetime.now()
            minute = (now.minute + 7) // 15 * 15
            if minute == 60:
                minute = 0
                hour = (now.hour + 1) % 24
            else:
                hour = now.hour
            ampm = "AM" if hour < 12 else "PM"
            display_hour = hour % 12 if hour % 12 != 0 else 12
            rounded_str = f"{display_hour:02d}:{minute:02d} {ampm}"
            default_index = time_options.index(rounded_str) if rounded_str in time_options else 0

        due_time_str = st.selectbox("Time", options=time_options, index=default_index, key="task_due_time")
        due_time = datetime.strptime(due_time_str, "%I:%M %p").time()

    pet_for_task = None
    if pawpal["owner"] is not None and pawpal["owner"].pets:
        pet_for_task = st.selectbox(
            "Assign to pet",
            pawpal["owner"].pets,
            format_func=lambda p: f"{p.name} ({p.type}, age {p.age})",
            key="task_pet_select"
        )
    else:
        st.warning("Add a pet first to assign tasks.")

    if st.button("Add task", use_container_width=True):
        if pawpal["owner"] is None:
            st.warning("Create an owner first.")
        elif pet_for_task is None:
            st.warning("Please choose a pet for this task.")
        else:
            scheduled_datetime = datetime.combine(due_date, due_time)
            task = {
                "title": task_title,
                "duration_minutes": int(duration),
                "priority": priority,
                "pet_id": pet_for_task.pet_id,
                "pet_name": pet_for_task.name,
                "due_time": scheduled_datetime
            }
            pawpal["tasks"].append(task)
            st.success(f"Task added: {task_title} for {pet_for_task.name}")

    st.divider()
    
    st.subheader("Manage Tasks")
    if pawpal["tasks"]:
        st.dataframe(pawpal["tasks"], use_container_width=True)

        mgmt_col1, mgmt_col2 = st.columns(2)
        
        with mgmt_col1:
            st.write("**Edit Task**")
            if pawpal["tasks"]:
                edit_option = st.selectbox(
                    "Select task",
                    options=list(range(len(pawpal["tasks"]))),
                    format_func=lambda i: f"{pawpal['tasks'][i]['title']} ({pawpal['tasks'][i]['pet_name']})",
                    key="edit_task_select"
                )

                task_to_edit = pawpal["tasks"][edit_option]
                edit_title = st.text_input("Title", value=task_to_edit["title"], key="edit_task_title")
                edit_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=int(task_to_edit.get("duration_minutes", 30)), key="edit_task_duration")
                edit_priority = st.selectbox("Priority", ["low", "medium", "high"], index=["low", "medium", "high"].index(task_to_edit.get("priority", "medium")), key="edit_task_priority")
                edit_due_date = st.date_input("Date", value=task_to_edit["due_time"].date(), key="edit_task_due_date")
                edit_due_time = st.time_input("Time", value=task_to_edit["due_time"].time(), key="edit_task_due_time")

                if st.button("Save edits", use_container_width=True):
                    updated_datetime = datetime.combine(edit_due_date, edit_due_time)
                    pawpal["tasks"][edit_option] = {
                        "title": edit_title,
                        "duration_minutes": int(edit_duration),
                        "priority": edit_priority,
                        "pet_id": task_to_edit.get("pet_id"),
                        "pet_name": task_to_edit.get("pet_name"),
                        "due_time": updated_datetime
                    }
                    st.success(f"Task '{edit_title}' updated")
        
        with mgmt_col2:
            st.write("**Remove Task**")
            if pawpal["tasks"]:
                remove_option = st.selectbox(
                    "Select task",
                    options=list(range(len(pawpal["tasks"]))),
                    format_func=lambda i: f"{pawpal['tasks'][i]['title']} ({pawpal['tasks'][i]['pet_name']})",
                    key="remove_task_select"
                )
                if st.button("Remove", use_container_width=True):
                    removed = pawpal["tasks"].pop(remove_option)
                    st.session_state.last_removed_task = removed
                    try:
                        pawpal["db"].execute(
                            "DELETE FROM tasks WHERE user_id = ? AND pet_id = ? AND description = ? AND due_time = ?",
                            (
                                pawpal["owner"].owner_id,
                                removed.get("pet_id"),
                                removed.get("title"),
                                removed.get("due_time").isoformat() if removed.get("due_time") else None,
                            ),
                        )
                    except Exception:
                        pass
                    st.success(f"Removed: {removed['title']}")

                if st.button("Undo last removal", use_container_width=True):
                    if st.session_state.last_removed_task is not None:
                        pawpal["tasks"].append(st.session_state.last_removed_task)
                        st.success(f"Restored: {st.session_state.last_removed_task['title']}")
                        st.session_state.last_removed_task = None
                    else:
                        st.info("No removed task to undo.")

                if st.button("Clear all tasks", use_container_width=True):
                    pawpal["tasks"] = []
                    st.session_state.last_removed_task = None
                    try:
                        pawpal["db"].execute(
                            "DELETE FROM tasks WHERE user_id = ?",
                            (pawpal["owner"].owner_id,),
                        )
                    except Exception:
                        pass
                    st.info("All tasks cleared.")
    else:
        st.info("No tasks yet. Add one above.")


# ====== TAB 3: SCHEDULE ======
with tab3:
    st.subheader("Build Schedule")
    
    sched_col1, sched_col2 = st.columns(2)
    with sched_col1:
        schedule_start = st.date_input("Start date", value=date.today(), key="schedule_start_date")
    with sched_col2:
        schedule_end = st.date_input("End date", value=date.today(), key="schedule_end_date")

    blocked_times_input = st.text_input("Blocked times (e.g. 09:00-10:00, 14:00-15:00)", key="blocked_times")
    required_activities_input = st.text_input("Required activities (e.g. walk, feed, play)", key="required_activities")

    if st.button("Generate schedule", use_container_width=True):
        if pawpal["owner"] is None:
            st.warning("Create an owner and pets first.")
        elif not pawpal["owner"].pets:
            st.warning("Add at least one pet first.")
        elif not pawpal["tasks"]:
            st.info("Add tasks before generating schedule.")
        else:
            if schedule_start > schedule_end:
                st.warning("Start date must be before or equal to end date.")
                st.stop()

            constraints = Constraints(start_date=schedule_start, end_date=schedule_end)
            if blocked_times_input:
                for blocked in [x.strip() for x in blocked_times_input.split(",") if x.strip()]:
                    constraints.add_constraint("blocked_times", blocked)
            if required_activities_input:
                for activity in [x.strip() for x in required_activities_input.split(",") if x.strip()]:
                    constraints.add_constraint("required_activities", activity)

            scheduler = Scheduler(pawpal["owner"], constraints, pawpal["db"])

            conflict_messages = []
            scheduled_count = 0
            for t in pawpal["tasks"]:
                pet_id = t.get("pet_id")
                if not pet_id:
                    pet_id = pawpal["owner"].pets[0].pet_id if pawpal["owner"].pets else None

                if not pet_id:
                    conflict_messages.append((t["title"], "No pet selected"))
                    continue

                task_due = t.get("due_time") if t.get("due_time") else datetime.now()

                try:
                    scheduler.schedule_task(pet_id, {
                        "description": t["title"],
                        "due_time": task_due,
                        "priority": t.get("priority", "medium"),
                        "status": "pending"
                    })
                    scheduled_count += 1
                except Exception as e:
                    conflict_messages.append((t["title"], str(e)))

            if conflict_messages:
                for title, err in conflict_messages:
                    st.warning(f"'{title}': {err}")
            if scheduled_count > 0:
                st.success(f"✓ {scheduled_count} task(s) scheduled!")

            upcoming = scheduler.get_upcoming_tasks(limit=20)
            if upcoming:
                sort_choice = st.selectbox(
                    "Sort by",
                    ["due_time", "priority", "pet_id", "status"],
                    index=0,
                    key="schedule_sort_option"
                )

                if sort_choice == "due_time":
                    sorted_tasks = scheduler.sort_by_time(upcoming)
                elif sort_choice == "priority":
                    priority_values = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
                    sorted_tasks = sorted(upcoming, key=lambda t: (-priority_values.get(t.priority, 0), t.due_time))
                elif sort_choice == "pet_id":
                    sorted_tasks = sorted(upcoming, key=lambda t: (t.pet_id or "", t.due_time))
                else:
                    sorted_tasks = sorted(upcoming, key=lambda t: (t.status or "", t.due_time))

                st.write(f"### Scheduled tasks (sorted by {sort_choice})")
                st.table([
                    {
                        "#": i + 1,
                        "description": t.description,
                        "pet_id": t.pet_id,
                        "due_time": t.due_time.strftime("%Y-%m-%d %H:%M"),
                        "priority": t.priority,
                        "status": t.status,
                        "frequency": t.frequency or "none"
                    }
                    for i, t in enumerate(sorted_tasks)
                ])

                overlaps = []
                for i, task in enumerate(sorted_tasks):
                    for j, other in enumerate(sorted_tasks):
                        if i < j and constraints.check_overlap(task, [other]):
                            overlaps.append((task.description, other.description))
                if overlaps:
                    st.warning("⚠️ Overlapping tasks detected:")
                    for a, b in overlaps:
                        st.write(f"- {a} overlaps with {b}")
            else:
                st.info("No scheduled tasks found.")


# ====== TAB 4: AI ASSISTANT ======
with tab4:
    st.subheader("AI Pet Care Assistant")
    st.caption("Ask for care advice, or say things like 'Set up a daily routine for my dog Max today'.")

    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []
    if "ai_logs" not in st.session_state:
        st.session_state.ai_logs = []

    # Display chat history
    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Show condensed action log
    if st.session_state.ai_logs:
        with st.expander("AI action log", expanded=False):
            for line in st.session_state.ai_logs[-30:]:
                st.text(line)

    # Chat input
    if prompt := st.chat_input("Ask about pet care or request tasks..."):
        is_valid, err_msg = validate_input(prompt)
        if not is_valid:
            st.warning(err_msg)
        elif pawpal["owner"] is None:
            st.warning("Create an owner first in the Owner & Pets tab.")
        else:
            with st.chat_message("user"):
                st.write(prompt)
            st.session_state.ai_messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Build plain-text history (exclude current message)
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.ai_messages[:-1]
                        if isinstance(m["content"], str)
                    ]
                    agent = PawPalAgent(
                        owner=pawpal["owner"],
                        db=pawpal["db"],
                        tasks=pawpal["tasks"],
                    )
                    response, logs = agent.chat(prompt, history[-10:])
                st.write(response)
                if logs:
                    with st.expander("Actions taken", expanded=True):
                        for line in logs:
                            st.text(line)

            st.session_state.ai_messages.append({"role": "assistant", "content": response})
            st.session_state.ai_logs.extend(logs)


# ====== TAB 5: DEBUG ======
with tab5:
    st.subheader("Session State")
    st.write("Debug st.session_state.pawpal:")
    st.json(pawpal)


