def test_tag_filter(client, admin_user, story_draft):
    story_draft.status = "PUBLISHED"
    story_draft.save()
    resp = client.get("/api/stories/?tags=sci-fi")
    assert resp.status_code == 200
    assert len(resp.json()) == 1