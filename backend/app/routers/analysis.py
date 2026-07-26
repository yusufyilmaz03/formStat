"""Analiz uç noktaları: özet, test, çapraz tablo, regresyon, segmentasyon, içgörü."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Form
from ..schemas import RegressionRequest, SegmentationRequest, TestRequest
from ..services.stats import descriptive, inferential, insights, regression, segmentation
from ..services.stats.dataframe import to_native

router = APIRouter(prefix="/api/forms/{form_id}/analysis", tags=["analysis"])


def _get_form(form_id: int, db: Session) -> Form:
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(404, "Form bulunamadı.")
    return form


@router.get("/overview")
def overview(form_id: int, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    return to_native(descriptive.describe_form(db, form))


@router.post("/test")
def test(form_id: int, payload: TestRequest, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    return to_native(inferential.run_test(db, form, payload.question_a, payload.question_b))


@router.post("/crosstab")
def crosstab(form_id: int, payload: TestRequest, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    return to_native(inferential.crosstab(db, form, payload.question_a, payload.question_b))


@router.post("/regression")
def run_regression(form_id: int, payload: RegressionRequest, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    return to_native(regression.run_regression(db, form, payload.target, payload.predictors))


@router.post("/segmentation")
def run_segmentation(form_id: int, payload: SegmentationRequest, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    return to_native(
        segmentation.run_segmentation(db, form, payload.questions or None, payload.n_clusters)
    )


@router.get("/insights")
def get_insights(form_id: int, db: Session = Depends(get_db)):
    form = _get_form(form_id, db)
    return to_native(insights.generate_insights(db, form))
