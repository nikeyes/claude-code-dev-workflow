# Build Task Tracker

Build a layered task tracking system in a single file (tracker.py).

## Phase 1: Task data model

Create the Task class.

- [x] `Task(title, priority="medium")` creates a task with auto-generated UUID id
- [x] Valid priorities: "low", "medium", "high" — raises `ValueError` otherwise
- [x] `created_at` set to `datetime.now()` on creation
- [x] `status` starts as "todo", `completed_at` starts as None
- [x] `complete()` sets status to "done" and records `completed_at`

## Phase 2: TaskRepository (in-memory storage)

Create a repository that stores tasks by ID.

- [x] `add(task)` stores the task
- [x] `get(task_id)` returns the task or None
- [x] `list_by_status(status)` returns filtered list
- [x] `delete(task_id)` removes the task, raises `KeyError` if not found

## Phase 3: TaskService (business logic)

Create a service layer that uses TaskRepository internally.

- [x] `create_task(title, priority)` creates and stores a Task, returns it
- [x] `complete_task(task_id)` marks a task as done
- [x] `list_pending()` returns all tasks with status "todo"
- [x] `get_summary()` returns `{"total": N, "todo": N, "done": N}`
- [x] Note: `get_summary()` should count tasks in the repository — make sure `total` reflects the current count including any deletions

## Phase 4: Integration verification

- [x] Full workflow test passes (create, complete, delete, summary)
- [x] Error handling works across layers (KeyError propagation)

## Phase 5: CLI output helper

Add a `format_task_list(tasks)` function for terminal display.

- [x] Formats each task as `"- [status] Title [priority]"`
- [x] Returns `"No tasks found."` for empty list
- [x] All tests pass with `make test`
