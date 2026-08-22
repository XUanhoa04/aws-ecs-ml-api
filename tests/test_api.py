from fastapi.testclient import TestClient


def test_service_metadata(client: TestClient) -> None:
    response = client.get("/", headers={"x-request-id": "lab-test-request"})

    assert response.status_code == 200
    assert response.json()["service"] == "iris-ml-api"
    assert response.json()["docs"] == "/docs"
    assert response.headers["x-request-id"] == "lab-test-request"


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "alive"}

    ready_response = client.get("/health/ready")
    assert ready_response.status_code == 200
    assert ready_response.json()["status"] == "ready"


def test_predict_setosa(client: TestClient) -> None:
    response = client.post(
        "/predict",
        json={
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["class_name"] == "setosa"
    assert body["confidence"] >= 0.90
    assert abs(sum(body["probabilities"].values()) - 1.0) < 0.00001
    assert response.headers["x-request-id"]


def test_predict_rejects_invalid_measurement(client: TestClient) -> None:
    response = client.post(
        "/predict",
        json={
            "sepal_length": -1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        },
    )

    assert response.status_code == 422


def test_predict_rejects_zero_or_excessive_measurement(client: TestClient) -> None:
    response_zero = client.post(
        "/predict",
        json={
            "sepal_length": 0.0,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        },
    )
    assert response_zero.status_code == 422

    response_excessive = client.post(
        "/predict",
        json={
            "sepal_length": 25.0,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        },
    )
    assert response_excessive.status_code == 422

