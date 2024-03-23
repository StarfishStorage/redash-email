from unittest.mock import patch

import pytest
import requests
from redashapi import APIError, Redash

REDASH_URL = "http://localhost:5003/api"
REDASH_KEY = "B9i5QnKSoU20SxQquVCXlcD8eHTOjcGaFs1IrWMV"


@patch.object(requests, "head")
def test_redash_init(requests_head):
    redash = Redash(REDASH_URL, REDASH_KEY)
    redash.headers.pop("X-CSRF-Token")
    assert redash.headers == {
        "Accept": "application/json",
        "Authorization": "Key B9i5QnKSoU20SxQquVCXlcD8eHTOjcGaFs1IrWMV",
    }


@patch.object(requests, "head")
@patch("redashapi.Redash.get")
def test_dashboard_id(redash_get, requests_head):
    redash_get.return_value = {
        "results": [{"name": "Directory History", "id": 100, "slug": "directory_history"}]
    }
    redash = Redash(REDASH_URL, REDASH_KEY)
    assert redash.dashboard_id("Directory History") == (100, "directory_history")


@patch.object(requests, "head")
@patch("redashapi.Redash.get")
def test_dashboard_id_not_found(redash_get, requests_head):
    redash_get.return_value = {"results": []}
    redash = Redash(REDASH_URL, REDASH_KEY)
    with pytest.raises(APIError, match="dashboard 'Aging Analysis' not found"):
        redash.dashboard_id("Aging Analysis")


@patch.object(requests, "head")
@patch("redashapi.Redash.get")
def test_dashboard_widget(redash_get, requests_head):
    redash_get.return_value = {
        "widgets": [
            {
                "visualization": {
                    "query": {
                        "name": "Directory Aging by Zone Classic",
                        "id": 90,
                        "is_archived": False,
                        "options": {"parameters": [{"name": "volume", "value": 100}]},
                    }
                }
            }
        ]
    }
    redash = Redash(REDASH_URL, REDASH_KEY)
    assert redash.dashboard_widget(100, "Directory Aging by Zone Classic") == (
        90,
        {"volume": 100},
    )


@patch.object(requests, "head")
@patch("redashapi.Redash.get")
def test_dashboard_widget_not_found(redash_get, requests_head):
    redash_get.return_value = {"widgets": []}
    redash = Redash(REDASH_URL, REDASH_KEY)
    with pytest.raises(
        APIError,
        match="Directory Aging by Zone Classic' not found for dashboard_id 100",
    ):
        redash.dashboard_widget(100, "Directory Aging by Zone Classic")
