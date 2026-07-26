"""Form ve soru CRUD uç noktaları."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import QUESTION_TYPES, Form, Question, Response
from ..schemas import (
    FormCreate,
    FormOut,
    FormSummary,
    FormUpdate,
    QuestionCreate,
)

router = APIRouter(prefix="/api/forms", tags=["forms"])


def _validate_question(q: QuestionCreate) -> None:
    if q.type not in QUESTION_TYPES:
        raise HTTPException(400, f"Geçersiz soru tipi: {q.type}")
    if q.type in {"single_choice", "multi_choice", "dropdown"} and not q.options:
        raise HTTPException(400, f"'{q.title}' için en az bir seçenek gerekli.")
    if q.type == "linear_scale":
        lo = q.scale_min if q.scale_min is not None else 1
        hi = q.scale_max if q.scale_max is not None else 5
        if lo >= hi:
            raise HTTPException(400, f"'{q.title}' için ölçek min < max olmalı.")


def _apply_questions(form: Form, questions: list[QuestionCreate]) -> None:
    form.questions.clear()
    for idx, q in enumerate(questions):
        _validate_question(q)
        form.questions.append(
            Question(
                order=q.order if q.order else idx,
                type=q.type,
                title=q.title,
                required=q.required,
                options=q.options,
                scale_min=q.scale_min,
                scale_max=q.scale_max,
            )
        )


@router.get("", response_model=list[FormSummary])
def list_forms(db: Session = Depends(get_db)):
    forms = db.scalars(select(Form).order_by(Form.created_at.desc())).all()
    out: list[FormSummary] = []
    for f in forms:
        q_count = db.scalar(
            select(func.count(Question.id)).where(Question.form_id == f.id)
        )
        r_count = db.scalar(
            select(func.count(Response.id)).where(Response.form_id == f.id)
        )
        out.append(
            FormSummary(
                id=f.id,
                title=f.title,
                description=f.description,
                created_at=f.created_at,
                google_form_id=f.google_form_id,
                published=f.published,
                question_count=q_count or 0,
                response_count=r_count or 0,
            )
        )
    return out


@router.post("", response_model=FormOut, status_code=201)
def create_form(payload: FormCreate, db: Session = Depends(get_db)):
    form = Form(title=payload.title, description=payload.description)
    _apply_questions(form, payload.questions)
    db.add(form)
    db.commit()
    db.refresh(form)
    return form


def get_form_or_404(form_id: int, db: Session) -> Form:
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(404, "Form bulunamadı.")
    return form


@router.get("/{form_id}", response_model=FormOut)
def get_form(form_id: int, db: Session = Depends(get_db)):
    return get_form_or_404(form_id, db)


@router.put("/{form_id}", response_model=FormOut)
def update_form(form_id: int, payload: FormUpdate, db: Session = Depends(get_db)):
    form = get_form_or_404(form_id, db)
    if payload.title is not None:
        form.title = payload.title
    if payload.description is not None:
        form.description = payload.description
    if payload.questions is not None:
        _apply_questions(form, payload.questions)
    db.commit()
    db.refresh(form)
    return form


@router.delete("/{form_id}", status_code=204)
def delete_form(form_id: int, db: Session = Depends(get_db)):
    form = get_form_or_404(form_id, db)
    db.delete(form)
    db.commit()
