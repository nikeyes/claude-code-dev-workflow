# Build Task Tracker

Build a layered task tracking system in a single file (tracker.py).

## Phase 1: Task data model

Create the Task class.

- [ ] `Task(title, priority="medium")` creates a task with auto-generated UUID id
- [ ] Valid priorities: "low", "medium", "high" — raises `ValueError` otherwise
- [ ] `created_at` set to `datetime.now()` on creation
- [ ] `status` starts as "todo", `completed_at` starts as None
- [ ] `complete()` sets status to "done" and records `completed_at`

## Phase 2: TaskRepository (in-memory storage)

Create a repository that stores tasks by ID.

- [ ] `add(task)` stores the task
- [ ] `get(task_id)` returns the task or None
- [ ] `list_by_status(status)` returns filtered list
- [ ] `delete(task_id)` removes the task, raises `KeyError` if not found

## Phase 3: TaskService (business logic)

Create a service layer that uses TaskRepository internally.

- [ ] `create_task(title, priority)` creates and stores a Task, returns it
- [ ] `complete_task(task_id)` marks a task as done
- [ ] `list_pending()` returns all tasks with status "todo"
- [ ] `get_summary()` returns `{"total": N, "todo": N, "done": N}`
- [ ] Note: `get_summary()` should count tasks in the repository — make sure `total` reflects the current count including any deletions

## Phase 4: Integration verification

- [ ] Full workflow test passes (create, complete, delete, summary)
- [ ] Error handling works across layers (KeyError propagation)

## Phase 5: CLI output helper

Add a `format_task_list(tasks)` function for terminal display.

- [ ] Formats each task as `"- [status] Title [priority]"`
- [ ] Returns `"No tasks found."` for empty list
- [ ] All tests pass with `make test`
