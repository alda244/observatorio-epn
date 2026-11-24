import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.repositories import companies


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_company_listing_preserves_total_and_filters(client, monkeypatch):
    def listing(filters):
        assert filters.group == "TEC"
        assert filters.in_pilot is False
        assert filters.sort == "empleados"
        return 42, []

    monkeypatch.setattr(companies, "list_companies", listing)
    response = client.get(
        "/v1/empresas",
        params={
            "grupo": "TEC",
            "en_piloto": "false",
            "orden": "empleados",
            "offset": 42,
            "limit": 1,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"total": 42, "limit": 1, "offset": 42, "datos": []}


@pytest.mark.parametrize(
    "params", [{"limit": 101}, {"offset": -1}, {"grupo": "X"}, {"nombre": "A"}]
)
def test_invalid_company_parameters_return_problem_json(client, params):
    response = client.get("/v1/empresas", params=params)
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == 400


def test_operational_routes_are_not_published(client):
    assert client.get("/salud").status_code == 404
    assert client.get("/salud/bd").status_code == 404
    paths = client.get("/openapi.json").json()["paths"]
    assert "/salud" not in paths and "/salud/bd" not in paths


def test_missing_company_returns_problem_json(client, monkeypatch):
    monkeypatch.setattr(companies, "get_company", lambda _: None)
    response = client.get("/v1/empresas/999")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "No existe una empresa con el expediente 999"


def test_invalid_company_id_returns_problem_json(client):
    response = client.get("/v1/empresas/0")
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
