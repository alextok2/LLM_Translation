def test_edit_denied_for_not_assigned(client, translator_user, story_draft):
    # another translator
    from django.contrib.auth.models import User, Group
    u2 = User.objects.create_user("tr2","", "pass")
    u2.groups.add(Group.objects.get(name="translator"))
    client.force_login(u2)
    p = story_draft.paragraphs.first()
    resp = client.patch(f"/api/paragraphs/{p.id}/translation", {"text":"X"}, content_type="application/json")
    assert resp.status_code == 403