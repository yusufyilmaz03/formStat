"""Pydantic şemaları (istek/yanıt gövdeleri)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Question ----------
class QuestionBase(BaseModel):
    type: str
    title: str
    required: bool = False
    options: list[str] | None = None
    scale_min: int | None = None
    scale_max: int | None = None
    order: int = 0


class QuestionCreate(QuestionBase):
    pass


class QuestionOut(QuestionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Form ----------
class FormBase(BaseModel):
    title: str
    description: str = ""


class FormCreate(FormBase):
    questions: list[QuestionCreate] = Field(default_factory=list)


class FormUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    questions: list[QuestionCreate] | None = None


class FormOut(FormBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    google_form_id: str | None = None
    google_responder_uri: str | None = None
    published: bool = False
    questions: list[QuestionOut] = Field(default_factory=list)


class FormSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str = ""
    created_at: datetime
    google_form_id: str | None = None
    published: bool = False
    question_count: int = 0
    response_count: int = 0


# ---------- Answers / Responses ----------
class AnswerIn(BaseModel):
    question_id: int
    value: object | None = None  # str | float | list — tipine göre normalize edilir


class ResponseCreate(BaseModel):
    source: str = "manual"
    submitted_at: datetime | None = None
    external_id: str | None = None
    answers: list[AnswerIn] = Field(default_factory=list)


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    question_id: int
    value_text: str | None = None
    value_number: float | None = None
    value_options: list | None = None


class ResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    submitted_at: datetime | None = None
    created_at: datetime
    answers: list[AnswerOut] = Field(default_factory=list)


# ---------- CSV import ----------
class ColumnMapping(BaseModel):
    """CSV sütun adı -> soru id eşlemesi."""
    column: str
    question_id: int


class CsvImportRequest(BaseModel):
    import_id: str  # /import/preview'dan dönen geçici dosya kimliği
    mappings: list[ColumnMapping]


# ---------- Analiz istekleri ----------
class TestRequest(BaseModel):
    question_a: int
    question_b: int


class RegressionRequest(BaseModel):
    target: int
    predictors: list[int]


class SegmentationRequest(BaseModel):
    questions: list[int] = Field(default_factory=list)  # boşsa tüm sayısal sorular
    n_clusters: int | None = None  # None -> otomatik (silhouette)
