"""ORM modelleri: Form, Question, Response, Answer, AppSetting."""
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# Desteklenen soru tipleri
QUESTION_TYPES = {
    "short_text",
    "long_text",
    "single_choice",   # tek seçim (radio)
    "multi_choice",    # çoklu seçim (checkbox)
    "dropdown",
    "linear_scale",    # sayısal ölçek (ör. 1-5)
    "number",
    "date",
    "email",
}

# Analizde sayısal kabul edilen tipler
NUMERIC_TYPES = {"linear_scale", "number"}
# Analizde kategorik kabul edilen tipler
CATEGORICAL_TYPES = {"single_choice", "dropdown", "multi_choice"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Form(Base):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    # Google Forms bağlantısı (Faz 6)
    google_form_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    google_responder_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False)

    questions: Mapped[list["Question"]] = relationship(
        back_populates="form",
        cascade="all, delete-orphan",
        order_by="Question.order",
    )
    responses: Mapped[list["Response"]] = relationship(
        back_populates="form", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"))
    order: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    # single_choice/multi_choice/dropdown için seçenekler
    options: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    scale_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scale_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Google Forms eşlemesi (Faz 6) — cevap senkronizasyonunda kullanılır
    google_item_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    google_question_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    form: Mapped["Form"] = relationship(back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(20), default="manual")  # google|csv|manual|inapp
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)  # tekilleştirme
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    form: Mapped["Form"] = relationship(back_populates="responses")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="response", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("responses.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_number: Mapped[float | None] = mapped_column(nullable=True)
    value_options: Mapped[list | None] = mapped_column(JSON, nullable=True)  # multi_choice

    response: Mapped["Response"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship(back_populates="answers")


class AppSetting(Base):
    """Basit anahtar-değer deposu (ör. Google token JSON'u)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
