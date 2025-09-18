from unittest.mock import Mock

import pytest

from src.application.container import DIContainer


class TestDIContainer:
    def test_register_and_resolve_simple_service(self):
        container = DIContainer()

        def service_factory():
            return {"type": "simple_service", "id": 1}

        container.register("simple_service", service_factory)

        result = container.resolve("simple_service")

        assert result == {"type": "simple_service", "id": 1}

    def test_resolve_unregistered_service_raises_error(self):
        container = DIContainer()

        with pytest.raises(ValueError) as exc_info:
            container.resolve("nonexistent_service")

        assert "Service nonexistent_service not registered" in str(exc_info.value)

    def test_singleton_returns_same_instance(self):
        container = DIContainer()
        counter = {"calls": 0}

        def expensive_factory():
            counter["calls"] += 1
            return {"instance_id": counter["calls"]}

        container.register("singleton_service", expensive_factory, singleton=True)

        first_instance = container.resolve("singleton_service")
        second_instance = container.resolve("singleton_service")
        third_instance = container.resolve("singleton_service")

        assert first_instance is second_instance
        assert second_instance is third_instance
        assert counter["calls"] == 1
        assert first_instance["instance_id"] == 1

    def test_non_singleton_creates_new_instances(self):
        container = DIContainer()
        counter = {"calls": 0}

        def factory():
            counter["calls"] += 1
            return {"instance_id": counter["calls"]}

        container.register("regular_service", factory, singleton=False)

        first_instance = container.resolve("regular_service")
        second_instance = container.resolve("regular_service")
        third_instance = container.resolve("regular_service")

        assert first_instance is not second_instance
        assert second_instance is not third_instance
        assert counter["calls"] == 3
        assert first_instance["instance_id"] == 1
        assert second_instance["instance_id"] == 2
        assert third_instance["instance_id"] == 3

    def test_factory_with_dependencies(self):
        container = DIContainer()

        def database_factory():
            return {"type": "database", "connected": True}

        def repository_factory():
            db = container.resolve("database")
            return {"type": "repository", "database": db}

        def service_factory():
            repo = container.resolve("repository")
            return {"type": "service", "repository": repo}

        container.register("database", database_factory, singleton=True)
        container.register("repository", repository_factory, singleton=True)
        container.register("service", service_factory)

        service = container.resolve("service")

        assert service["type"] == "service"
        assert service["repository"]["type"] == "repository"
        assert service["repository"]["database"]["type"] == "database"
        assert service["repository"]["database"]["connected"] is True

    def test_overwrite_existing_registration(self):
        container = DIContainer()

        def first_factory():
            return {"version": 1}

        def second_factory():
            return {"version": 2}

        container.register("service", first_factory)
        first_result = container.resolve("service")
        assert first_result["version"] == 1

        container.register("service", second_factory)
        second_result = container.resolve("service")
        assert second_result["version"] == 2

    def test_singleton_overwrite_clears_cached_instance(self):
        container = DIContainer()
        counter = {"v1_calls": 0, "v2_calls": 0}

        def factory_v1():
            counter["v1_calls"] += 1
            return {"version": 1, "calls": counter["v1_calls"]}

        def factory_v2():
            counter["v2_calls"] += 1
            return {"version": 2, "calls": counter["v2_calls"]}

        container.register("singleton", factory_v1, singleton=True)
        first_instance = container.resolve("singleton")
        assert first_instance["version"] == 1
        assert counter["v1_calls"] == 1

        container.register("singleton", factory_v2, singleton=True)
        second_instance = container.resolve("singleton")
        third_instance = container.resolve("singleton")

        assert second_instance["version"] == 2
        assert second_instance is third_instance
        assert counter["v2_calls"] == 1

    def test_lambda_factories(self):
        container = DIContainer()

        container.register("config", lambda: {"debug": True})
        container.register("logger", lambda: Mock(spec=["log", "error"]))

        config = container.resolve("config")
        logger = container.resolve("logger")

        assert config == {"debug": True}
        assert hasattr(logger, "log")
        assert hasattr(logger, "error")

    def test_factory_with_exceptions(self):
        container = DIContainer()

        def failing_factory():
            raise RuntimeError("Factory initialization failed")

        container.register("failing_service", failing_factory)

        with pytest.raises(RuntimeError) as exc_info:
            container.resolve("failing_service")

        assert "Factory initialization failed" in str(exc_info.value)

    def test_multiple_containers_are_independent(self):
        container1 = DIContainer()
        container2 = DIContainer()

        container1.register("service", lambda: {"container": 1})
        container2.register("service", lambda: {"container": 2})

        result1 = container1.resolve("service")
        result2 = container2.resolve("service")

        assert result1["container"] == 1
        assert result2["container"] == 2

    def test_complex_object_factories(self):
        container = DIContainer()

        class DatabaseConnection:
            def __init__(self, host, port):
                self.host = host
                self.port = port
                self.connected = True

        class UserRepository:
            def __init__(self, db_connection):
                self.db = db_connection

            def get_user(self, user_id):
                return {"id": user_id, "name": f"User {user_id}"}

        container.register(
            "db_connection",
            lambda: DatabaseConnection("localhost", 5432),
            singleton=True,
        )

        container.register(
            "user_repository",
            lambda: UserRepository(container.resolve("db_connection")),
            singleton=True,
        )

        repo = container.resolve("user_repository")
        user = repo.get_user(123)

        assert repo.db.host == "localhost"
        assert repo.db.port == 5432
        assert repo.db.connected is True
        assert user == {"id": 123, "name": "User 123"}

    def test_empty_container_has_no_services(self):
        container = DIContainer()

        assert container._services == {}
        assert container._singletons == {}

    def test_factory_called_with_no_arguments(self):
        container = DIContainer()
        mock_factory = Mock(return_value={"created": True})

        container.register("mock_service", mock_factory)
        result = container.resolve("mock_service")

        mock_factory.assert_called_once_with()
        assert result == {"created": True}

    def test_singleton_lazy_initialization(self):
        container = DIContainer()
        mock_factory = Mock(return_value={"lazy": True})

        container.register("lazy_singleton", mock_factory, singleton=True)

        mock_factory.assert_not_called()

        result = container.resolve("lazy_singleton")

        mock_factory.assert_called_once()
        assert result == {"lazy": True}
