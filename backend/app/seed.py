"""Demo tohumlama: veritabanı boşsa örnek bir anket + gerçekçi cevaplar oluşturur.

Demo dağıtımında (Render/Railway/Fly) her taze konteyner dolu bir örnekle açılır.
`SEED_DEMO=0` ile kapatılabilir.
"""
from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from .database import SessionLocal
from .models import Form, Question, Response
from .services.answers import build_answer


def seed_if_empty() -> None:
    if os.getenv("SEED_DEMO", "1") == "0":
        return
    db = SessionLocal()
    try:
        if (db.scalar(select(func.count(Form.id))) or 0) > 0:
            return
        _create_demo(db)
    finally:
        db.close()


def _create_demo(db) -> None:
    random.seed(42)
    form = Form(
        title="Müşteri Memnuniyet Anketi (Demo)",
        description="Örnek veriyle gelen demo anket. Dilediğin gibi düzenle, sil veya yenisini oluştur.",
    )
    questions = [
        Question(order=0, type="single_choice", title="Cinsiyet", options=["Kadın", "Erkek"]),
        Question(order=1, type="single_choice", title="Şehir", options=["İstanbul", "Ankara", "İzmir"]),
        Question(order=2, type="linear_scale", title="Memnuniyet", scale_min=1, scale_max=5),
        Question(order=3, type="number", title="Yaş"),
        Question(order=4, type="multi_choice", title="İlgi alanları",
                 options=["Spor", "Müzik", "Kitap", "Seyahat"]),
        Question(order=5, type="single_choice", title="Tavsiye eder misiniz?", options=["Evet", "Hayır"]),
        Question(order=6, type="short_text", title="Yorum"),
    ]
    for q in questions:
        form.questions.append(q)
    db.add(form)
    db.flush()  # soru id'leri için

    qmap = {q.title: q for q in form.questions}
    city_base = {"İstanbul": 3.2, "Ankara": 4.2, "İzmir": 2.6}
    comments = ["Güzel", "İyi", "Fena değil", "Harika", "Ortalama", "Memnun kaldım", ""]

    for _ in range(60):
        city = random.choice(list(city_base))
        age = random.randint(18, 65)
        # Şehir ve yaş, memnuniyeti etkiler (analizde anlamlı ilişki çıksın diye)
        sat = city_base[city] + (age - 40) * 0.03 + random.gauss(0, 0.6)
        sat = int(max(1, min(5, round(sat))))
        gender = random.choice(["Kadın", "Erkek"])
        interests = random.sample(["Spor", "Müzik", "Kitap", "Seyahat"], k=random.randint(1, 3))
        recommend = "Evet" if (sat >= 4 or random.random() < 0.25) else "Hayır"
        values = {
            "Cinsiyet": gender,
            "Şehir": city,
            "Memnuniyet": sat,
            "Yaş": age,
            "İlgi alanları": interests,
            "Tavsiye eder misiniz?": recommend,
            "Yorum": random.choice(comments),
        }
        resp = Response(
            form_id=form.id,
            source="manual",
            submitted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
        )
        for title, val in values.items():
            ans = build_answer(qmap[title], val)
            if ans is not None:
                resp.answers.append(ans)
        db.add(resp)

    db.commit()
