def test_parse_counts(client, admin_user, story_draft):
    client.force_login(admin_user)
    resp = client.post(f"/api/stories/{story_draft.id}/parse", {"original_text": "X1\n\nX2", "machine_text": "Y1\n\nY2"}, content_type="application/json")
    assert resp.status_code == 200
    story_draft.refresh_from_db()
    assert story_draft.paragraphs_count == 2
    assert story_draft.translated_count == 0