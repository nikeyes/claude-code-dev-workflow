import pytest
from datetime import datetime


# --- Phase 1 tests: Task model ---

def test_task_creation():
    from tracker import Task
    t = Task("Buy groceries")
    assert t.title == "Buy groceries"
    assert t.status == "todo"
    assert t.priority == "medium"
    assert isinstance(t.created_at, datetime)


def test_task_with_priority():
    from tracker import Task
    t = Task("Fix bug", priority="high")
    assert t.priority == "high"


def test_task_invalid_priority():
    from tracker import Task
    with pytest.raises(ValueError, match="Priority must be"):
        Task("Test", priority="critical")


def test_task_complete():
    from tracker import Task
    t = Task("Do thing")
    t.complete()
    assert t.status == "done"
    assert t.completed_at is not None


# --- Phase 2 tests: TaskRepository ---

def test_repo_add_and_get():
    from tracker import Task, TaskRepository
    repo = TaskRepository()
    t = Task("Test task")
    repo.add(t)
    assert repo.get(t.id) == t


def test_repo_list_by_status():
    from tracker import Task, TaskRepository
    repo = TaskRepository()
    t1 = Task("Task 1")
    t2 = Task("Task 2")
    t2.complete()
    repo.add(t1)
    repo.add(t2)
    assert repo.list_by_status("todo") == [t1]
    assert repo.list_by_status("done") == [t2]


def test_repo_delete():
    from tracker import Task, TaskRepository
    repo = TaskRepository()
    t = Task("Task")
    repo.add(t)
    repo.delete(t.id)
    assert repo.get(t.id) is None


def test_repo_delete_missing_raises():
    from tracker import Task, TaskRepository
    repo = TaskRepository()
    with pytest.raises(KeyError):
        repo.delete("nonexistent-id")


# --- Phase 3 tests: TaskService ---

def test_service_create_task():
    from tracker import TaskService
    svc = TaskService()
    t = svc.create_task("New task", priority="high")
    assert t.title == "New task"
    assert t.priority == "high"


def test_service_complete_task():
    from tracker import TaskService
    svc = TaskService()
    t = svc.create_task("Task")
    svc.complete_task(t.id)
    retrieved = svc.get_task(t.id)
    assert retrieved.status == "done"


def test_service_list_pending():
    from tracker import TaskService
    svc = TaskService()
    svc.create_task("Pending 1")
    t2 = svc.create_task("Done 1")
    svc.complete_task(t2.id)
    pending = svc.list_pending()
    assert len(pending) == 1
    assert pending[0].title == "Pending 1"


def test_service_summary():
    from tracker import TaskService
    svc = TaskService()
    svc.create_task("A")
    t2 = svc.create_task("B")
    svc.complete_task(t2.id)
    summary = svc.get_summary()
    assert summary == {"total": 2, "todo": 1, "done": 1}


# --- Phase 4 tests: integration ---

def test_full_workflow():
    from tracker import TaskService
    svc = TaskService()
    t1 = svc.create_task("Write tests", priority="high")
    t2 = svc.create_task("Fix bug", priority="low")
    t3 = svc.create_task("Deploy", priority="medium")

    svc.complete_task(t1.id)

    pending = svc.list_pending()
    assert len(pending) == 2

    summary = svc.get_summary()
    assert summary["total"] == 3
    assert summary["done"] == 1

    svc.delete_task(t2.id)
    assert svc.get_task(t2.id) is None
    assert svc.get_summary()["total"] == 2


def test_complete_missing_task_raises():
    from tracker import TaskService
    svc = TaskService()
    with pytest.raises(KeyError):
        svc.complete_task("nonexistent")


# --- Phase 5 tests: format_task_list (CLI helper) ---

def test_format_task_list():
    from tracker import TaskService, format_task_list
    svc = TaskService()
    svc.create_task("Alpha", priority="high")
    svc.create_task("Beta", priority="low")
    output = format_task_list(svc.list_pending())
    assert "Alpha" in output
    assert "[high]" in output
    assert "Beta" in output


def test_format_empty_list():
    from tracker import format_task_list
    output = format_task_list([])
    assert output == "No tasks found."
