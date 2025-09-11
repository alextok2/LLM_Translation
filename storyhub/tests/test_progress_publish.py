from translations.models import Translation
from stories.models import StoryStatus

def test_claim_finalize_publish_flow(client, translator_user, admin_user, story_draft):
    # translator claims
    client.force_login(translator_user)
    r = client.post(f"/api/stories/{story_draft.id}/claim")
    assert r.status_code == 200
    story_draft.refresh_from_db()
    assert story_draft.status == StoryStatus.IN_TRANSLATION
    assert story_draft.assigned_to_id == translator_user.id

    # finalize all paragraphs
    for p in story_draft.paragraphs.all():
        r = client.patch(f"/api/paragraphs/{p.id}/translation", {"text": f"T{p.index}", "is_finalized": True}, content_type="application/json")
        assert r.status_code in (200,201)
    story_draft.refresh_from_db()
    assert story_draft.translated_count == story_draft.paragraphs_count

    # complete by translator
    r = client.post(f"/api/stories/{story_draft.id}/complete")
    assert r.status_code == 200
    story_draft.refresh_from_db()
    assert story_draft.status == StoryStatus.REVIEW

    # publish by admin
    client.force_login(admin_user)
    r = client.post(f"/api/stories/{story_draft.id}/publish")
    assert r.status_code == 200
    story_draft.refresh_from_db()
    assert story_draft.status == StoryStatus.PUBLISHED