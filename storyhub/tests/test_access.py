from stories.models import StoryStatus

def test_reader_sees_only_published(client, story_draft):
    resp = client.get("/api/stories/")
    assert resp.status_code == 200
    assert len(resp.json()) == 0
    story_draft.status = StoryStatus.PUBLISHED
    story_draft.save()
    resp = client.get("/api/stories/")
    assert len(resp.json()) == 1