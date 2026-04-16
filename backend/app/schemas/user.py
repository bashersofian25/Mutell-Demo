from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr

RoleStr = Literal["super_admin", "tenant_admin", "manager", "viewer"]

VALID_ROLES = ("super_admin", "tenant_admin", "manager", "viewer")

ROLE_HIERARCHY: dict[str, int] = {
    "super_admin": 4,
    "tenant_admin": 3,
    "manager": 2,
    "viewer": 1,
}


class UserInvite(BaseModel):
    email: EmailStr
    full_name: str
    role: RoleStr


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: RoleStr | None = None
    status: Literal["active", "suspended", "invited"] | None = None
    max_concurrent_evaluations: int | None = None


class UserResponse(BaseModel):
    id: str
    tenant_id: str | None
    email: str
    full_name: str
    avatar_url: str | None
    role: str
    status: str
    last_login_at: datetime | None
    created_at: datetime
    max_concurrent_evaluations: int = 1

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


class PermissionItem(BaseModel):
    permission: str
    granted: bool


class PermissionListResponse(BaseModel):
    user_id: str
    permissions: list[PermissionItem]


PERMISSIONS_SCHEMA = [
    {"key": "export_reports", "label": "Export Reports", "description": "Download and export report files"},
    {"key": "view_analytics", "label": "View Analytics", "description": "Access analytics dashboards"},
    {"key": "manage_terminals", "label": "Manage Terminals", "description": "Create, edit, and revoke terminals"},
    {"key": "manage_users", "label": "Manage Users", "description": "Invite, edit, and suspend users"},
    {"key": "create_notes", "label": "Create Notes", "description": "Add notes to slots"},
    {"key": "generate_reports", "label": "Generate Reports", "description": "Create new report exports"},
]


class PermissionUpdate(BaseModel):
    permission: str
    granted: bool
