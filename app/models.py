from typing import Optional, List
from datetime import datetime
import enum
from secrets import token_hex

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, MetaData, Enum, Computed, TIMESTAMP

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

db = SQLAlchemy(model_class=Base)


class EventStatus(enum.Enum):
    scheduled = "scheduled"
    ongoing = "ongoing"
    completed = "completed"
    cancelled = "cancelled"

class SlotStatus(enum.Enum):
    booked = "booked"
    cancelled = "cancelled"


class School(Base):
    __tablename__ = 'schools'

    INVITE_CODE_LENGTH = 32
    INVITE_CODE_BYTES = INVITE_CODE_LENGTH // 2

    school_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    invite_code: Mapped[str] = mapped_column(String(INVITE_CODE_LENGTH), nullable=False, unique=True)

    buildings: Mapped[List["Building"]] = relationship("Building", back_populates="school", cascade="all, delete-orphan")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="school", cascade="all, delete-orphan")
    users: Mapped[List["User"]] = relationship("User", back_populates="school", cascade="all, delete-orphan")

    def assign_invite_code(self):
        self.invite_code = token_hex(self.INVITE_CODE_BYTES)

    def __repr__(self):
        return f'<School {self.school_name}>'

class Building(Base):
    __tablename__ = 'buildings'

    building_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(70), nullable=False)
    address: Mapped[str] = mapped_column(String(90), nullable=False)

    school_id: Mapped[int] = mapped_column(ForeignKey('schools.school_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    school: Mapped["School"] = relationship("School", back_populates="buildings")
    building_bookings: Mapped[List["BuildingBooking"]] = relationship("BuildingBooking", back_populates="building")

    def __repr__(self):
        return f'<Building {self.name}>'

class Event(Base):
    __tablename__ = 'events'

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus),
        default=EventStatus.scheduled,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=sqlalchemy.sql.func.now(), nullable=False)

    school_id: Mapped[int] = mapped_column(ForeignKey('schools.school_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    school: Mapped["School"] = relationship("School", back_populates="events")
    slots: Mapped[List["Slot"]] = relationship("Slot", back_populates="event")
    building_bookings: Mapped[List["BuildingBooking"]] = relationship("BuildingBooking", back_populates="event")

    def __repr__(self):
        return f'<Event {self.event_id}, {self.start_time}-{self.end_time} -> {self.status.value}>'

class User(Base, UserMixin):
    __tablename__ = 'users'
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(90), nullable=True)
    last_name: Mapped[str] = mapped_column(String(90), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=sqlalchemy.sql.func.now(), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")

    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey('schools.school_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=True)

    school: Mapped["School"] = relationship("School", back_populates="users")

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": role,
    }

    @property
    def surname_name(self):
        return f'{self.last_name} {self.first_name}'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.middle_name or ""}'.strip()

    @property
    def initials(self):
        return f'{self.last_name} {self.first_name[0]}. {self.middle_name[0] + "." if self.middle_name else ""}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self) -> str:
        return str(self.user_id)

    def __repr__(self):
        return f'<User {self.email}>'

class Teacher(User):
    __tablename__ = 'teachers'

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey('users.user_id', ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "teacher",
    }

    slots: Mapped[List["Slot"]] = relationship("Slot", back_populates="teacher")
    building_bookings: Mapped[List["BuildingBooking"]] = relationship("BuildingBooking", back_populates="teacher")

    def __repr__(self):
        return f'<Teacher {self.email}>'

class Parent(User):
    __tablename__ = 'parents'

    parent_id: Mapped[int] = mapped_column(
        ForeignKey('users.user_id', ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "parent",
    }

    slots: Mapped[List["Slot"]] = relationship("Slot", back_populates="parent")

    def __repr__(self):
        return f'<Parent {self.email}>'

class Admin(User):
    __tablename__ = 'admins'

    admin_id: Mapped[int] = mapped_column(
        ForeignKey('users.user_id', ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }

    def __repr__(self):
        return f'<Admin {self.email}>'

class Slot(Base):
    __tablename__ = 'slots'

    slot_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus),
        default=SlotStatus.booked,
        nullable=False
    )
    teacher_id: Mapped[int] = mapped_column(ForeignKey('teachers.teacher_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    parent_id: Mapped[int] = mapped_column(ForeignKey('parents.parent_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.event_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    duration: Mapped[int] = mapped_column(
        Integer,
        Computed("TIMESTAMPDIFF(MINUTE, start_time, end_time)")
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=sqlalchemy.sql.func.now(), nullable=False)

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="slots")
    parent: Mapped["Parent"] = relationship("Parent", back_populates="slots")
    event: Mapped["Event"] = relationship("Event", back_populates="slots")

    def __repr__(self):
        return f'<Slot {self.slot_id}: {self.start_time}-{self.end_time} -> {self.teacher} > {self.parent}>'

class BuildingBooking(Base):
    __tablename__ = 'building_booking'

    building_booking_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey('teachers.teacher_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    building_id: Mapped[int] = mapped_column(ForeignKey('buildings.building_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.event_id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    classroom: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=sqlalchemy.sql.func.now(), nullable=False)

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="building_bookings")
    building: Mapped["Building"] = relationship("Building", back_populates="building_bookings")
    event: Mapped["Event"] = relationship("Event", back_populates="building_bookings")

    def __repr__(self):
        return f'<BuildingBooking {self.building_booking_id}: {self.teacher.surname_name} > {self.building.name}>'
