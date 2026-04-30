import enum

from db.base.models import Base
from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, UniqueConstraint, Uuid

__all__ = ["User", "OrganizationMember", "OrganizationRole"]


class OrganizationRole(str, enum.Enum):
    owner = "owner"


class User(Base):
    __tablename__ = "users"

    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_super_admin = Column(Boolean, nullable=False, default=False)


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_organization_members_org_user"),)

    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(OrganizationRole, name="organization_role"), nullable=False, default=OrganizationRole.owner)
