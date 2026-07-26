# 📊 FormStat — Anket & İstatistik Analiz Uygulaması

Form oluştur, cevap topla ve **kapsamlı istatistiksel analiz** yap. Hibrit Google Forms entegrasyonu ile uygulamada tasarladığın formu Google Forms'a aktarabilir, cevapları geri çekebilirsin. Google olmadan da CSV içe aktarma ve manuel girişle uçtan uca çalışır.

- **Backend:** FastAPI (Python) + SQLite + pandas/scipy/statsmodels/scikit-learn
- **Frontend:** React + TypeScript + Vite + Recharts
- **Kapsam:** Kişisel/lokal araç (tek kullanıcı, hesap sistemi yok)

---

## Özellikler

| Alan | Yetenekler |
|------|-----------|
| **Form Builder** | 9 soru tipi: kısa/uzun metin, tek/çoklu seçim, açılır liste, ölçek, sayı, tarih, e-posta |
| **Cevap toplama** | CSV içe aktarma (sütun→soru eşleme sihirbazı), manuel giriş, Google Forms senkronizasyonu |
| **Betimleyici** | Ortalama, medyan, mod, std, çeyrekler, çarpıklık/basıklık, histogram, frekans dağılımları |
| **Çıkarımsal** | Ki-kare (+Cramér's V), t-testi (+Cohen's d), ANOVA (+Tukey), korelasyon (Pearson/Spearman) — tipe göre **otomatik test seçimi** |
| **Çapraz tablo** | İki kategorik değişken için ısı haritalı pivot + ki-kare |
| **Regresyon** | Doğrusal (sayısal hedef) ve lojistik (ikili hedef); katsayı tablosu, p-değerleri, R²/pseudo-R² |
| **Segmentasyon** | K-means (otomatik küme sayısı, silhouette), PCA görselleştirme, segment profilleri |
| **Otomatik içgörü** | Anlamlı ilişkileri tarar, dağılım ve veri kalitesi uyarıları üretir |
| **Rapor** | Cevapları geniş formatta CSV olarak indir |

---

## Hızlı başlangıç

Gereksinimler: **Python 3.10+** ve **Node.js 18+**.

```bash
cd formstat
./run.sh
```

Ardından tarayıcıda **http://localhost:5173** aç. (İlk çalıştırmada bağımlılıklar otomatik kurulur.)

### Manuel çalıştırma (isteğe bağlı)

```bash
# Backend (:8000)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (:5173) — ayrı bir terminalde
cd frontend
npm install
npm run dev
```

API dokümantasyonu: **http://localhost:8000/docs**

---

## Kullanım akışı

1. **Form oluştur** — "Yeni Form" → soruları ekle → Kaydet.
2. **Cevap topla** — "Cevaplar" sekmesinde:
   - `sample_responses.csv` dosyasını **CSV içe aktar** ile dene (sütunlar otomatik eşlenir), veya
   - **Manuel cevap** ile tek tek gir, veya
   - Google'a aktardıysan **Google'dan senkronize et**.
3. **Analiz et** — "Analiz" sekmesinde grafikler, testler, regresyon, segmentasyon ve otomatik içgörüler.

> Uygulama örnek bir "Müşteri Memnuniyet Anketi" (40 cevap) ile birlikte gelir; hemen analiz sekmesini deneyebilirsin. Temiz başlamak için `data/formstat.db` dosyasını silmen yeterli.

---

## Google Forms entegrasyonu (opsiyonel)

Uygulamadan **gerçek Google Form oluşturmak ve cevapları çekmek** için bir kereye mahsus Google Cloud kurulumu gerekir. Bu adımları **sen** yapmalısın (Claude senin adına hesap/gizli anahtar oluşturamaz):

1. [Google Cloud Console](https://console.cloud.google.com/) → yeni bir **proje** oluştur.
2. **APIs & Services → Library** → **Google Forms API**'yi bul ve **Enable**.
3. **APIs & Services → OAuth consent screen** → **External** seç, uygulama adını gir, **Test users** listesine kendi Google e-postanı ekle. Kapsam eklemene gerek yok.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID** → uygulama tipi **Desktop app** → oluştur.
5. Oluşan istemciden **JSON indir** ve dosyayı şuraya koy:
   ```
   formstat/data/client_secret.json
   ```
6. Uygulamayı yeniden başlat, sağ üstten **Google'a Bağlan** → Google hesabınla yetkilendir.
7. Bir formda **Düzenle → Google Forms'a aktar** ile formu oluştur+yayınla; **yanıt bağlantısını** paylaş. Cevaplar geldikçe **Cevaplar → Google'dan senkronize et**.

**Kapsamlar:** `forms.body` (oluştur/güncelle), `forms.responses.readonly` (cevap çek).

> **Not (2026):** Google, 30 Haziran 2026'dan sonra API ile oluşturulan formları varsayılan olarak *yayınlanmamış* durumda üretir. Uygulama, oluşturduktan hemen sonra `setPublishSettings` ile formu otomatik yayınlar (`isPublished` + `isAcceptingResponses`).

---

## Proje yapısı

```
formstat/
├── backend/app/
│   ├── main.py            # FastAPI + CORS + tablo oluşturma
│   ├── models.py          # Form, Question, Response, Answer
│   ├── routers/           # forms, responses, analysis, reports, google
│   └── services/
│       ├── google_forms.py    # OAuth + dışa aktarma + senkron
│       ├── importers.py       # CSV içe aktarma
│       └── stats/             # descriptive, inferential, regression, segmentation, insights
├── frontend/src/
│   ├── pages/             # FormsList, FormBuilder, ResponsesPage, AnalysisDashboard
│   └── components/        # charts, analysis/*, GoogleConnect, FormHeader
├── data/                  # SQLite + geçici import + Google gizli anahtar/token (gitignore)
├── sample_responses.csv   # CSV içe aktarma denemesi için
└── run.sh
```

---

## Notlar
- Tüm veri lokalde `data/formstat.db` içinde tutulur; hiçbir şey dışarı gönderilmez (Google senkronu hariç, o da yalnızca senin yetkilendirdiğin form için).
- Analiz istatistikleri backend'de hesaplanır (pandas/scipy/statsmodels/scikit-learn), frontend yalnızca görselleştirir.
