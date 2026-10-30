import pytest
from src.agent.tools import extract_search_results, extract_scrape_content

def test_v2_rest_response_with_data_web():
    response = {
        "success": True,
        "data": {
            "web": [
                {
                    "url": "https://developers.cloudflare.com/page1",
                    "title": "Cloudflare Page 1",
                    "description": "Description 1",
                    "position": 1
                }
            ]
        }
    }
    results = extract_search_results(response)
    assert len(results) == 1
    assert results[0]["url"] == "https://developers.cloudflare.com/page1"
    assert results[0]["title"] == "Cloudflare Page 1"
    assert results[0]["description"] == "Description 1"

def test_sdk_response_with_web():
    response = {
        "web": [
            {
                "url": "https://developers.cloudflare.com/page1",
                "title": "Cloudflare Page 1",
                "description": "Description 1",
                "position": 1
            },
            {
                "url": "https://developers.cloudflare.com/page2",
                "title": "Cloudflare Page 2",
                "description": "Description 2",
                "position": 2
            }
        ]
    }
    results = extract_search_results(response)
    assert len(results) == 2
    assert results[0]["url"] == "https://developers.cloudflare.com/page1"
    assert results[1]["url"] == "https://developers.cloudflare.com/page2"

def test_v1_response_with_data_list():
    response = {
        "data": [
            {
                "url": "https://example.com/v1",
                "title": "V1 Title",
                "description": "V1 Desc"
            }
        ]
    }
    results = extract_search_results(response)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/v1"

def test_direct_list_response():
    response = [
        {
            "url": "https://example.com/direct",
            "title": "Direct Item"
        }
    ]
    results = extract_search_results(response)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/direct"

def test_empty_valid_response():
    assert extract_search_results({"web": []}) == []
    assert extract_search_results({"data": []}) == []
    assert extract_search_results({}) == []
    assert extract_search_results(None) == []

def test_malformed_response():
    assert extract_search_results({"web": "invalid_string"}) == []
    assert extract_search_results("not a dictionary or list") == []
    assert extract_search_results(12345) == []

def test_results_missing_optional_metadata():
    response = {
        "web": [
            {
                "url": "https://example.com/minimal"
                # missing title, description, position
            }
        ]
    }
    results = extract_search_results(response)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/minimal"
    assert results[0]["title"] == ""
    assert results[0]["description"] == ""

def test_scrape_extraction_formats():
    assert extract_scrape_content("Direct markdown string") == "Direct markdown string"
    assert extract_scrape_content({"markdown": "# Header"}) == "# Header"
    assert extract_scrape_content({"data": {"markdown": "# Data Header"}}) == "# Data Header"
    assert extract_scrape_content({}) == ""
    assert extract_scrape_content(None) == ""
