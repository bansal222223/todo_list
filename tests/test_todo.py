import pytest
import unittest.mock as mock


class TestCreateTodo:
    def test_create_todo(self, auth_client):
        res = auth_client.post("/tasks", json={
            "title": "Buy groceries",
            "description": "Milk, Eggs"
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
        res = auth_client.delete("/tasks/9999")
        assert res.status_code in [403, 404]

    def test_delete_todo_admin(self, client):
        client.post("/register", json={
            "username": "adminuser",
            "password": "Admin@1234",
            "role": "admin"
        })
        client.post("/send-otp", json={"username": "adminuser"})

        # ✅ verify_otp mock
        with mock.patch(
            "todo_list.components.task_manager.auth.verify_otp",
            return_value=True
        ):
            res = client.post("/verify-otp", json={
                "username": "adminuser", "otp": "123456"
            })

        token = res.json().get("access_token")
        assert token is not None, f"Token None! Response: {res.json()}"
        client.headers.update({"Authorization": f"Bearer {token}"})

        task_res = client.post("/tasks", json={
            "title": "Task to delete",
            "description": "Will be deleted"
        })
        print("TASK RES:", task_res.json())
        task_id = task_res.json()["id"]

        del_res = client.delete(f"/tasks/{task_id}")
        assert del_res.status_code == 200