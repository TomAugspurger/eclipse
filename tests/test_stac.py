import planetary_computer
from stactools.eclipse import stac


def test_basic():
    credential = planetary_computer.sas.get_token("ai4edataeuwest", "eclipse").token
    result = stac.create_item("Chicago/2021-07-11", "abfs", {"account_name": "ai4edataeuwest", "credential": credential}, {})
    assert result.id == "Chicago-2021-07-11"
    assert result.properties["start_datetime"] == "2021-07-11T00:00:00Z"
    assert result.properties["end_datetime"] == "2021-07-18T00:00:00Z"