import pytest


class TestCreateTodo:
    def test_create_todo(self, auth_client):
        res = auth_client.post("/tasks", json={
            "title": "Buy groceries",
            "description": "Milk, Eggs",
            "completed": False
        })
        assert res.status_code == 200

    def test_create_todo_missing_title(self, auth_client):
        res = auth_client.post("/tasks", json={})
        assert res.status_code == 422


class TestReadTodo:
    def test_get_all_todos(self, auth_client):
        res = auth_client.get("/tasks")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


class TestDeleteTodo:
    def test_delete_todo_non_admin(self, auth_client):
        res = auth_client.delete("/tasks/1")
        assert res.status_code == 403

    # ✅ Admin user se delete karo
    def test_delete_todo_admin(self, client):
        # Admin register karo
        client.post("/register", json={
            "username": "adminuser",
            "password": "Admin@1234",
            "role": "admin"
        })
        client.post("/send-otp?username=adminuser")

        import unittest.mock as mock
        with mock.patch(
            "todo_list.components.task_manager.auth.verify_otp",
            return_value=True
        ):
            res = client.post("/verify-otp?username=adminuser&otp=123456")

        token = res.json().get("access_token")
        client.headers.update({"Authorization": f"Bearer {token}"})

        # Task banao
        task_res = client.post("/tasks", json={
            "title": "Task to delete",
            "description": "Will be deleted",
            "completed": False
        })
        task_id = task_res.json()["id"]

        # Delete karo
        del_res = client.delete(f"/tasks/{task_id}")
        assert del_res.status_code == 200