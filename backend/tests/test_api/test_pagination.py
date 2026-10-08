"""Q6.4: the list is newest first, bounded, and carries the total of all pages."""

import uuid

from sqlalchemy import text


def create(client, title):
    todo_id = uuid.uuid4()
    assert (
        client.post("/todo", json={"id": str(todo_id), "title": title}).status_code
        == 200
    )
    return todo_id


def titles(response):
    return [todo["title"] for todo in response.json()["todo_entries"]]


def test_the_list_is_newest_first(real_client):
    for title in ["first", "second", "third"]:
        create(real_client, title)

    assert titles(real_client.get("/todo")) == ["third", "second", "first"]


def test_equal_creation_times_are_ordered_by_id(real_client, real_db_engine):
    low, high = uuid.UUID(int=1), uuid.UUID(int=2)
    for todo_id in (low, high):
        real_client.post("/todo", json={"id": str(todo_id), "title": todo_id.hex})
    with real_db_engine.begin() as conn:
        conn.execute(
            text("UPDATE \"toDo\" SET created_at = '2026-01-01 00:00:00.000000'")
        )

    assert titles(real_client.get("/todo")) == [high.hex, low.hex]


def test_total_counts_all_active_todos_and_results_this_page(real_client):
    ids = [create(real_client, f"todo {n}") for n in range(5)]
    real_client.delete(f"/todo/{ids[0]}")

    body = real_client.get("/todo?limit=2&page=2").json()

    assert (body["results"], body["total"]) == (2, 4)
    assert [todo["title"] for todo in body["todo_entries"]] == ["todo 2", "todo 1"]


def test_an_empty_page_still_reports_the_total(real_client):
    create(real_client, "only")

    body = real_client.get("/todo?limit=10&page=2").json()

    assert (body["results"], body["total"], body["todo_entries"]) == (0, 1, [])
