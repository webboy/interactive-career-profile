import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CareerRecordType, EmbeddingStatus, ProfileItemType, Visibility
from app.db.models.career_record import CareerRecord
from app.db.models.profile_item import ProfileItem
from app.services.career_records import list_public_career_records
from app.services.profile_items import list_public_profile_items


PROFILE_ITEM_PAYLOAD = {
    "key": "headline",
    "type": ProfileItemType.TEXT,
    "label": "Headline",
    "value": "Senior Engineer",
}

CAREER_RECORD_PAYLOAD = {
    "record_type": CareerRecordType.EXPERIENCE,
    "title": "Platform Engineer",
    "summary": "Built internal platforms",
    "content": "Led platform engineering initiatives.",
}


@pytest.mark.asyncio
async def test_profile_items_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/admin/profile-items")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_career_records_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/admin/career-records")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_profile_item_crud(auth_client: AsyncClient) -> None:
    create_response = await auth_client.post("/api/admin/profile-items", json=PROFILE_ITEM_PAYLOAD)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["key"] == "headline"
    assert created["visibility"] == Visibility.PRIVATE
    item_id = created["id"]

    list_response = await auth_client.get("/api/admin/profile-items")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = await auth_client.get(f"/api/admin/profile-items/{item_id}")
    assert get_response.status_code == 200
    assert get_response.json()["label"] == "Headline"

    update_payload = {
        **PROFILE_ITEM_PAYLOAD,
        "label": "Updated Headline",
        "visibility": Visibility.PUBLIC,
        "sort_order": 1,
    }
    update_response = await auth_client.put(
        f"/api/admin/profile-items/{item_id}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["label"] == "Updated Headline"
    assert update_response.json()["visibility"] == Visibility.PUBLIC

    delete_response = await auth_client.delete(f"/api/admin/profile-items/{item_id}")
    assert delete_response.status_code == 204

    missing_response = await auth_client.get(f"/api/admin/profile-items/{item_id}")
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_career_record_crud(auth_client: AsyncClient) -> None:
    create_response = await auth_client.post("/api/admin/career-records", json=CAREER_RECORD_PAYLOAD)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["record_type"] == CareerRecordType.EXPERIENCE
    assert created["visibility"] == Visibility.PUBLIC
    assert created["embedding_status"] == EmbeddingStatus.PENDING
    assert created["embedding_error"] is None
    record_id = created["id"]

    list_response = await auth_client.get("/api/admin/career-records")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = await auth_client.get(f"/api/admin/career-records/{record_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Platform Engineer"

    update_payload = {
        **CAREER_RECORD_PAYLOAD,
        "title": "Updated Platform Engineer",
        "visibility": Visibility.DRAFT,
        "embedding_status": EmbeddingStatus.FAILED,
        "embedding_error": "Embedding service unavailable",
    }
    update_response = await auth_client.put(
        f"/api/admin/career-records/{record_id}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Updated Platform Engineer"
    assert updated["visibility"] == Visibility.DRAFT
    assert updated["embedding_status"] == EmbeddingStatus.FAILED
    assert updated["embedding_error"] == "Embedding service unavailable"

    delete_response = await auth_client.delete(f"/api/admin/career-records/{record_id}")
    assert delete_response.status_code == 204

    missing_response = await auth_client.get(f"/api/admin/career-records/{record_id}")
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_profile_item_enum_validation(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/admin/profile-items",
        json={
            **PROFILE_ITEM_PAYLOAD,
            "type": "invalid-type",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_career_record_enum_validation(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/admin/career-records",
        json={
            **CAREER_RECORD_PAYLOAD,
            "record_type": "invalid-type",
        },
    )
    assert response.status_code == 422

    response = await auth_client.post(
        "/api/admin/career-records",
        json={
            **CAREER_RECORD_PAYLOAD,
            "visibility": "invalid-visibility",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_list_includes_all_visibility_states(
    auth_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    db_session.add_all(
        [
            ProfileItem(
                key="public-item",
                type=ProfileItemType.TEXT,
                label="Public",
                value="Public value",
                visibility=Visibility.PUBLIC,
            ),
            ProfileItem(
                key="private-item",
                type=ProfileItemType.TEXT,
                label="Private",
                value="Private value",
                visibility=Visibility.PRIVATE,
            ),
            ProfileItem(
                key="draft-item",
                type=ProfileItemType.TEXT,
                label="Draft",
                value="Draft value",
                visibility=Visibility.DRAFT,
            ),
            CareerRecord(
                record_type=CareerRecordType.PROJECT,
                title="Public Project",
                content="Public project content",
                visibility=Visibility.PUBLIC,
            ),
            CareerRecord(
                record_type=CareerRecordType.PROJECT,
                title="Private Project",
                content="Private project content",
                visibility=Visibility.PRIVATE,
            ),
            CareerRecord(
                record_type=CareerRecordType.PROJECT,
                title="Archived Project",
                content="Archived project content",
                visibility=Visibility.ARCHIVED,
            ),
        ]
    )
    await db_session.commit()

    profile_response = await auth_client.get("/api/admin/profile-items")
    assert profile_response.status_code == 200
    assert len(profile_response.json()) == 3

    filtered_profile_response = await auth_client.get(
        "/api/admin/profile-items",
        params={"visibility": Visibility.PRIVATE},
    )
    assert filtered_profile_response.status_code == 200
    assert len(filtered_profile_response.json()) == 1
    assert filtered_profile_response.json()[0]["key"] == "private-item"

    career_response = await auth_client.get("/api/admin/career-records")
    assert career_response.status_code == 200
    assert len(career_response.json()) == 3

    filtered_career_response = await auth_client.get(
        "/api/admin/career-records",
        params={
            "visibility": Visibility.ARCHIVED,
            "record_type": CareerRecordType.PROJECT,
        },
    )
    assert filtered_career_response.status_code == 200
    assert len(filtered_career_response.json()) == 1
    assert filtered_career_response.json()[0]["title"] == "Archived Project"


@pytest.mark.asyncio
async def test_public_service_filters_return_only_public_records(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            ProfileItem(
                key="public-item",
                type=ProfileItemType.TEXT,
                label="Public",
                value="Public value",
                visibility=Visibility.PUBLIC,
            ),
            ProfileItem(
                key="private-item",
                type=ProfileItemType.TEXT,
                label="Private",
                value="Private value",
                visibility=Visibility.PRIVATE,
            ),
            CareerRecord(
                record_type=CareerRecordType.SKILL,
                title="Public Skill",
                content="Python",
                visibility=Visibility.PUBLIC,
            ),
            CareerRecord(
                record_type=CareerRecordType.SKILL,
                title="Draft Skill",
                content="Go",
                visibility=Visibility.DRAFT,
            ),
        ]
    )
    await db_session.commit()

    public_items = await list_public_profile_items(db_session)
    assert len(public_items) == 1
    assert public_items[0].key == "public-item"

    public_records = await list_public_career_records(db_session)
    assert len(public_records) == 1
    assert public_records[0].title == "Public Skill"
