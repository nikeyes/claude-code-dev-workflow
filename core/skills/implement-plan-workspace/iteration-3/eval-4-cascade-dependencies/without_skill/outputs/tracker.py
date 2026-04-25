import uuid
from datetime import datetime


VALID_PRIORITIES = {"low", "medium", "high"}


class Task:
    def __init__(self, title, priority="medium"):
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of {sorted(VALID_PRIORITIES)}, got '{priority}'")
        self.id = str(uuid.uuid4())
        self.title = title
        self.priority = priority
        self.status = "todo"
        self.created_at = datetime.now()
        self.completed_at = None

    def complete(self):
        self.status = "done"
        self.completed_at = datetime.now()


class TaskRepository:
    def __init__(self):
        self._tasks = {}

    def add(self, task):
        self._tasks[task.id] = task

    def get(self, task_id):
        return self._tasks.get(task_id)

    def list_by_status(self, status):
        return [t for t in self._tasks.values() if t.status == status]

    def delete(self, task_id):
        if task_id not in self._tasks:
            raise KeyError(task_id)
        del self._tasks[task_id]


class TaskService:
    def __init__(self):
        self._repo = TaskRepository()

    def create_task(self, title, priority="medium"):
        task = Task(title, priority=priority)
        self._repo.add(task)
        return task

    def get_task(self, task_id):
        return self._repo.get(task_id)

    def complete_task(self, task_id):
        task = self._repo.get(task_id)
        if task is None:
            raise KeyError(task_id)
        task.complete()

    def delete_task(self, task_id):
        self._repo.delete(task_id)

    def list_pending(self):
        return self._repo.list_by_status("todo")

    def get_summary(self):
        all_tasks = list(self._repo._tasks.values())
        todo_count = sum(1 for t in all_tasks if t.status == "todo")
        done_count = sum(1 for t in all_tasks if t.status == "done")
        return {"total": len(all_tasks), "todo": todo_count, "done": done_count}


def format_task_list(tasks):
    if not tasks:
        return "No tasks found."
    lines = [f"- [{t.status}] {t.title} [{t.priority}]" for t in tasks]
    return "\n".join(lines)
