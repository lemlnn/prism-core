# made by lemlnn + ChatGPT (used for keywords and AP classes to cover)

#region extension-metadata

EXTENSION_NAME = "pdf-classifier-APs-v1.1"
EXTENSION_PRIORITY = 70

#endregion

#region imports

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

#endregion

#region settings

MAX_PAGES_TO_READ = 3
MIN_TEXT_CHARS = 80
SENSITIVE_OVERRIDE = True
ROUTE_LOW_CONFIDENCE = True
ENABLE_PDFTOTEXT_FALLBACK = True
PDFTOTEXT_TIMEOUT_SECONDS = 6
ENABLE_OCR = False

#endregion

#region extension-options

def option_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def option_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def configure_extension(options):
    global MAX_PAGES_TO_READ
    global MIN_TEXT_CHARS
    global SENSITIVE_OVERRIDE
    global ROUTE_LOW_CONFIDENCE
    global ENABLE_PDFTOTEXT_FALLBACK
    global PDFTOTEXT_TIMEOUT_SECONDS
    global ENABLE_OCR

    options = options or {}

    MAX_PAGES_TO_READ = option_int(options.get("max_pages_to_read"), MAX_PAGES_TO_READ)
    MIN_TEXT_CHARS = option_int(options.get("min_text_chars"), MIN_TEXT_CHARS)
    SENSITIVE_OVERRIDE = option_bool(options.get("sensitive_override"), SENSITIVE_OVERRIDE)
    ROUTE_LOW_CONFIDENCE = option_bool(options.get("route_low_confidence"), ROUTE_LOW_CONFIDENCE)
    ENABLE_PDFTOTEXT_FALLBACK = option_bool(options.get("enable_pdftotext_fallback"), ENABLE_PDFTOTEXT_FALLBACK)
    PDFTOTEXT_TIMEOUT_SECONDS = option_int(options.get("pdftotext_timeout_seconds"), PDFTOTEXT_TIMEOUT_SECONDS)
    ENABLE_OCR = option_bool(options.get("enable_ocr"), ENABLE_OCR)

#endregion

#region models

@dataclass(frozen=True)
class ClassificationResult: #validated internal classification result

    category: str
    score: int
    reason: str

#endregion

#region prism-hooks

def file_target_resolve(context): #PRISM hook to suggest a PDF target category
    extension = str(getattr(context, "extension", "")).lower()

    if extension != ".pdf":
        return None

    source_path = Path(getattr(context, "source_path"))
    file_name_text = normalize_text(source_path.stem.replace("_", " ").replace("-", " "))
    extracted_text, extractor_name = extract_pdf_text(source_path, max_pages=MAX_PAGES_TO_READ)
    combined_text = normalize_text(f"{file_name_text}\n{extracted_text}")

    if SENSITIVE_OVERRIDE and looks_sensitive(combined_text):
        return {
            "category": "Review/Sensitive",
            "reason": "PDF matched sensitive-file keywords",
        }

    if len(normalize_text(extracted_text)) < MIN_TEXT_CHARS:
        return {
            "category": "Review/PDF/Needs OCR",
            "reason": f"PDF has little or no readable embedded text using {extractor_name}",
        }

    result = classify_text(combined_text)

    if result is not None:
        return {
            "category": result.category,
            "reason": f"{result.reason}; score={result.score}; extractor={extractor_name}",
        }

    if ROUTE_LOW_CONFIDENCE:
        return {
            "category": "Review/PDF/Low Confidence",
            "reason": f"PDF text extracted with {extractor_name}, but no category reached threshold",
        }

    return None

#endregion

#region pdf-extraction-api

def extract_pdf_text(path: Path, max_pages: int = MAX_PAGES_TO_READ) -> tuple[str, str]: #tries lightweight embedded PDF text extraction
    text = extract_with_pymupdf(path, max_pages)

    if has_enough_text(text):
        return text, "pymupdf"

    text = extract_with_pypdf(path, max_pages)

    if has_enough_text(text):
        return text, "pypdf"

    if ENABLE_PDFTOTEXT_FALLBACK:
        text = extract_with_pdftotext(path, max_pages)

        if has_enough_text(text):
            return text, "pdftotext"

    weak_texts = []

    for extractor in (extract_with_pymupdf, extract_with_pypdf):
        try:
            value = extractor(path, max_pages)
        except Exception:
            value = ""

        if value:
            weak_texts.append(value)

    return "\n".join(weak_texts), "embedded-text-extractors"


def extract_with_pymupdf(path: Path, max_pages: int) -> str: #extracts embedded text with PyMuPDF if installed
    try:
        import fitz
    except Exception:
        return ""

    try:
        document = fitz.open(path)
    except Exception:
        return ""

    chunks = []

    try:
        page_count = min(len(document), max_pages)

        for index in range(page_count):
            try:
                chunks.append(document[index].get_text("text") or "")
            except Exception:
                continue
    finally:
        try:
            document.close()
        except Exception:
            pass

    return "\n".join(chunks)


def extract_with_pypdf(path: Path, max_pages: int) -> str: #extracts embedded text with pypdf or PyPDF2 if installed
    try:
        from pypdf import PdfReader
    except Exception:
        try:
            from PyPDF2 import PdfReader
        except Exception:
            return ""

    try:
        reader = PdfReader(str(path))
    except Exception:
        return ""

    chunks = []

    try:
        page_count = min(len(reader.pages), max_pages)

        for index in range(page_count):
            try:
                chunks.append(reader.pages[index].extract_text() or "")
            except Exception:
                continue
    except Exception:
        return "\n".join(chunks)

    return "\n".join(chunks)


def extract_with_pdftotext(path: Path, max_pages: int) -> str: #extracts embedded text with poppler pdftotext if available
    executable = shutil.which("pdftotext")

    if executable is None:
        return ""

    command = [
        executable,
        "-f", "1",
        "-l", str(max_pages),
        "-layout",
        str(path),
        "-",
    ]

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PDFTOTEXT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return ""

    return process.stdout or ""


def has_enough_text(text: str) -> bool: #checks if extracted text is useful enough to classify
    return len(normalize_text(text)) >= MIN_TEXT_CHARS

#endregion

#region classification-api

def classify_text(text: str) -> ClassificationResult | None: #scores text against all category rules
    candidates = []

    for category, rules in CATEGORY_RULES.items():
        score, matched = score_rules(text, rules)

        if score >= rules.get("threshold", DEFAULT_THRESHOLD):
            candidates.append(
                ClassificationResult(
                    category=category,
                    score=score,
                    reason=f"matched {', '.join(matched[:6])}",
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (item.score, category_specificity(item.category)),
        reverse=True,
    )

    return candidates[0]


def score_rules(text: str, rules: dict) -> tuple[int, list[str]]: #scores a category rule packet against normalized text
    score = 0
    matched = []

    for phrase, weight in rules.get("phrases", {}).items():
        if phrase in text:
            score += weight
            matched.append(phrase)

    for pattern, weight in rules.get("patterns", {}).items():
        if re.search(pattern, text):
            score += weight
            matched.append(pattern)

    return score, matched


def category_specificity(category: str) -> int: #prefers deeper/more specific categories when scores tie
    return category.count("/")


def normalize_text(value: str) -> str: #normalizes text for keyword matching
    text = str(value).lower()
    text = text.replace("\x00", " ")
    text = re.sub(r"[^a-z0-9$%./:+#&@\- ]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

#endregion

#region sensitive-file-api

SENSITIVE_PHRASES = {
    "social security": 6,
    "ssn": 6,
    "passport": 5,
    "driver license": 5,
    "drivers license": 5,
    "license number": 5,
    "bank account": 5,
    "routing number": 5,
    "account number": 5,
    "password": 5,
    "recovery code": 5,
    "backup code": 5,
    "private key": 6,
    "secret key": 6,
    "api key": 6,
    "access token": 6,
    "birth certificate": 6,
}


def looks_sensitive(text: str) -> bool: #detects sensitive-looking PDFs and routes them to review
    score = 0

    for phrase, weight in SENSITIVE_PHRASES.items():
        if phrase in text:
            score += weight

    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
        score += 8
    if re.search(r"\b(account|routing)\s+(number|#)\b", text):
        score += 5

    return score >= 8

#endregion

#region category-rules

DEFAULT_THRESHOLD = 8

CATEGORY_RULES = {
    # Finance
    "Documents/Finance/Invoices": {
        "threshold": 8,
        "phrases": {
            "invoice": 6,
            "amount due": 5,
            "balance due": 5,
            "payment terms": 4,
            "bill to": 4,
            "invoice number": 5,
            "due date": 3,
            "subtotal": 2,
        },
        "patterns": {
            r"\binv[- ]?\d{3,}\b": 4,
        },
    },
    "Documents/Finance/Receipts": {
        "threshold": 8,
        "phrases": {
            "receipt": 6,
            "order total": 5,
            "transaction id": 5,
            "transaction number": 5,
            "purchased": 3,
            "payment method": 4,
            "sales tax": 3,
            "total paid": 5,
        },
        "patterns": {},
    },
    "Documents/Finance/Taxes": {
        "threshold": 8,
        "phrases": {
            "tax year": 5,
            "internal revenue service": 7,
            "form 1040": 7,
            "w-2": 7,
            "w2": 6,
            "1099": 7,
            "schedule c": 5,
            "tax return": 6,
            "irs": 5,
        },
        "patterns": {},
    },
    "Documents/Finance/Statements": {
        "threshold": 8,
        "phrases": {
            "statement": 4,
            "account summary": 6,
            "ending balance": 6,
            "beginning balance": 5,
            "monthly statement": 6,
            "bank statement": 7,
            "brokerage statement": 7,
        },
        "patterns": {},
    },

    # General documents
    "Documents/Legal": {
        "threshold": 9,
        "phrases": {
            "agreement": 3,
            "contract": 5,
            "lease": 5,
            "terms and conditions": 5,
            "plaintiff": 6,
            "defendant": 6,
            "court": 3,
            "legal notice": 7,
            "signature": 2,
        },
        "patterns": {},
    },
    "Documents/Medical": {
        "threshold": 9,
        "phrases": {
            "patient": 4,
            "diagnosis": 6,
            "lab result": 6,
            "prescription": 6,
            "medical record": 7,
            "insurance claim": 5,
            "provider": 2,
            "health": 2,
            "appointment": 3,
        },
        "patterns": {},
    },
    "Documents/Career": {
        "threshold": 8,
        "phrases": {
            "resume": 7,
            "curriculum vitae": 7,
            "cover letter": 7,
            "work experience": 5,
            "education": 2,
            "skills": 2,
            "references": 3,
            "professional summary": 5,
        },
        "patterns": {},
    },
    "Documents/Manuals": {
        "threshold": 8,
        "phrases": {
            "user manual": 7,
            "user guide": 7,
            "installation guide": 6,
            "warranty": 4,
            "troubleshooting": 5,
            "setup guide": 6,
            "quick start": 5,
            "safety instructions": 5,
        },
        "patterns": {},
    },
    "Documents/Forms": {
        "threshold": 8,
        "phrases": {
            "form": 2,
            "application": 3,
            "signature": 2,
            "date of birth": 4,
            "print name": 5,
            "submit this form": 6,
            "required fields": 4,
        },
        "patterns": {},
    },
    "Documents/Travel": {
        "threshold": 8,
        "phrases": {
            "itinerary": 7,
            "boarding pass": 7,
            "flight": 4,
            "hotel": 4,
            "reservation": 4,
            "confirmation number": 5,
            "departure": 3,
            "arrival": 3,
            "gate": 2,
        },
        "patterns": {},
    },
    "Documents/Household": {
        "threshold": 8,
        "phrases": {
            "utility bill": 7,
            "electric bill": 6,
            "water bill": 6,
            "mortgage": 5,
            "rent": 3,
            "repair": 3,
            "appliance": 4,
            "home warranty": 6,
            "property": 3,
        },
        "patterns": {},
    },

    # General school
    "Documents/School/Class Materials": {
        "threshold": 8,
        "phrases": {
            "syllabus": 7,
            "rubric": 6,
            "assignment": 4,
            "homework": 4,
            "unit test": 5,
            "study guide": 6,
            "worksheet": 5,
            "classwork": 4,
            "semester exam": 5,
            "final exam": 5,
        },
        "patterns": {},
    },
    "Documents/School/Math": {
        "threshold": 10,
        "phrases": {
            "function": 2,
            "equation": 2,
            "graph": 2,
            "slope": 3,
            "polynomial": 4,
            "trigonometric": 4,
            "logarithmic": 4,
            "exponential": 3,
            "matrix": 4,
            "probability": 4,
        },
        "patterns": {},
    },
    "Documents/School/Science": {
        "threshold": 10,
        "phrases": {
            "hypothesis": 3,
            "experiment": 3,
            "molecule": 3,
            "cell": 3,
            "energy": 2,
            "force": 2,
            "reaction": 3,
            "lab report": 6,
            "data table": 3,
        },
        "patterns": {},
    },
    "Documents/School/English": {
        "threshold": 9,
        "phrases": {
            "essay": 4,
            "thesis": 5,
            "rhetorical": 5,
            "annotation": 4,
            "literature": 4,
            "poem": 4,
            "claim": 2,
            "evidence": 2,
            "commentary": 3,
        },
        "patterns": {},
    },
    "Documents/School/History": {
        "threshold": 9,
        "phrases": {
            "history": 3,
            "dbq": 6,
            "leq": 6,
            "saq": 6,
            "primary source": 5,
            "empire": 3,
            "revolution": 3,
            "industrialization": 4,
            "cold war": 4,
        },
        "patterns": {},
    },
    "Documents/School/World Languages": {
        "threshold": 8,
        "phrases": {
            "vocabulary": 4,
            "conjugation": 6,
            "grammar": 3,
            "listening": 2,
            "speaking": 2,
            "spanish": 5,
            "french": 5,
            "chinese": 5,
            "japanese": 5,
            "german": 5,
            "latin": 5,
            "italian": 5,
        },
        "patterns": {},
    },

    # AP Capstone
    "Documents/School/AP Seminar": {
        "threshold": 8,
        "phrases": {
            "ap seminar": 8,
            "individual research report": 7,
            "irr": 5,
            "iwa": 5,
            "team multimedia presentation": 6,
            "eoc a": 5,
            "eoc b": 5,
            "stimulus material": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Research": {
        "threshold": 8,
        "phrases": {
            "ap research": 8,
            "academic paper": 5,
            "research question": 5,
            "methodology": 4,
            "literature review": 5,
            "oral defense": 5,
            "poster presentation": 4,
        },
        "patterns": {},
    },

    # AP Arts
    "Documents/School/AP Art History": {
        "threshold": 8,
        "phrases": {
            "ap art history": 8,
            "visual analysis": 5,
            "art historical": 5,
            "architecture": 3,
            "sculpture": 3,
            "painting": 3,
            "patronage": 4,
            "iconography": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Music Theory": {
        "threshold": 8,
        "phrases": {
            "ap music theory": 8,
            "sight singing": 6,
            "cadence": 5,
            "chord progression": 5,
            "roman numeral": 5,
            "harmonic dictation": 6,
            "melodic dictation": 6,
            "voice leading": 5,
        },
        "patterns": {},
    },

    # AP English
    "Documents/School/AP English Language": {
        "threshold": 8,
        "phrases": {
            "ap english language": 8,
            "ap lang": 7,
            "rhetorical analysis": 7,
            "synthesis essay": 7,
            "argument essay": 6,
            "rhetorical situation": 6,
            "claim evidence": 4,
            "line of reasoning": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP English Literature": {
        "threshold": 8,
        "phrases": {
            "ap english literature": 8,
            "ap lit": 7,
            "poetry analysis": 7,
            "prose analysis": 7,
            "literary argument": 7,
            "characterization": 4,
            "symbolism": 4,
            "theme": 3,
        },
        "patterns": {},
    },

    # AP Math / CS
    "Documents/School/AP Precalculus": {
        "threshold": 8,
        "phrases": {
            "ap precalculus": 8,
            "precalculus": 6,
            "polar": 4,
            "regression": 4,
            "trigonometric": 4,
            "rational function": 5,
            "exponential": 3,
            "logarithmic": 4,
            "frq": 2,
            "mcq": 2,
        },
        "patterns": {},
    },
    "Documents/School/AP Calculus AB": {
        "threshold": 8,
        "phrases": {
            "ap calculus ab": 8,
            "calculus ab": 7,
            "derivative": 4,
            "integral": 4,
            "limit": 3,
            "differentiation": 4,
            "accumulation": 4,
            "riemann": 5,
            "related rates": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Calculus BC": {
        "threshold": 8,
        "phrases": {
            "ap calculus bc": 8,
            "calculus bc": 7,
            "taylor series": 7,
            "maclaurin": 6,
            "series": 4,
            "parametric": 4,
            "polar": 3,
            "improper integral": 5,
            "convergence": 4,
        },
        "patterns": {},
    },
    "Documents/School/AP Statistics": {
        "threshold": 8,
        "phrases": {
            "ap statistics": 8,
            "confidence interval": 6,
            "hypothesis test": 6,
            "normal distribution": 5,
            "standard deviation": 4,
            "sampling distribution": 6,
            "least squares regression": 6,
            "probability": 3,
        },
        "patterns": {},
    },
    "Documents/School/AP Computer Science A": {
        "threshold": 8,
        "phrases": {
            "ap computer science a": 8,
            "ap csa": 7,
            "java": 5,
            "arraylist": 6,
            "inheritance": 5,
            "recursion": 5,
            "class object": 5,
            "method": 3,
            "boolean": 3,
        },
        "patterns": {},
    },
    "Documents/School/AP Computer Science Principles": {
        "threshold": 8,
        "phrases": {
            "ap computer science principles": 8,
            "ap csp": 7,
            "computing innovation": 6,
            "algorithm": 4,
            "pseudocode": 5,
            "binary": 3,
            "internet": 2,
            "abstraction": 4,
            "data privacy": 5,
        },
        "patterns": {},
    },

    # AP Sciences
    "Documents/School/AP Biology": {
        "threshold": 8,
        "phrases": {
            "ap biology": 8,
            "cellular respiration": 6,
            "photosynthesis": 6,
            "enzyme": 4,
            "dna": 4,
            "rna": 4,
            "protein": 3,
            "evolution": 4,
            "genetics": 4,
            "ecology": 4,
        },
        "patterns": {},
    },
    "Documents/School/AP Chemistry": {
        "threshold": 8,
        "phrases": {
            "ap chemistry": 8,
            "stoichiometry": 6,
            "molarity": 5,
            "equilibrium": 5,
            "acid base": 5,
            "thermodynamics": 5,
            "kinetics": 5,
            "electrochemistry": 6,
            "intermolecular": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Environmental Science": {
        "threshold": 8,
        "phrases": {
            "ap environmental science": 8,
            "apes": 6,
            "biodiversity": 5,
            "ecosystem services": 6,
            "pollution": 4,
            "climate change": 5,
            "watershed": 5,
            "sustainability": 5,
            "population growth": 4,
        },
        "patterns": {},
    },
    "Documents/School/AP Physics 1": {
        "threshold": 8,
        "phrases": {
            "ap physics 1": 8,
            "kinematics": 5,
            "newton's laws": 6,
            "newton laws": 5,
            "torque": 5,
            "momentum": 4,
            "simple harmonic motion": 6,
            "work energy": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Physics 2": {
        "threshold": 8,
        "phrases": {
            "ap physics 2": 8,
            "fluids": 5,
            "thermodynamics": 4,
            "electric force": 5,
            "electric potential": 5,
            "geometric optics": 6,
            "quantum": 4,
            "nuclear physics": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Physics C Mechanics": {
        "threshold": 8,
        "phrases": {
            "ap physics c mechanics": 8,
            "physics c mechanics": 7,
            "calculus based mechanics": 7,
            "center of mass": 5,
            "rotational inertia": 6,
            "angular momentum": 5,
            "differential equation": 4,
        },
        "patterns": {},
    },
    "Documents/School/AP Physics C E&M": {
        "threshold": 8,
        "phrases": {
            "ap physics c electricity": 8,
            "ap physics c e&m": 8,
            "physics c e&m": 7,
            "electric field": 5,
            "gauss law": 6,
            "electric potential": 5,
            "magnetic field": 5,
            "faraday law": 6,
            "capacitor": 4,
        },
        "patterns": {},
    },

    # AP Social Studies
    "Documents/School/AP Human Geography": {
        "threshold": 8,
        "phrases": {
            "ap human geography": 8,
            "aphug": 7,
            "migration": 4,
            "population pyramid": 6,
            "agriculture": 4,
            "urban": 3,
            "culture": 3,
            "political geography": 5,
            "development": 3,
        },
        "patterns": {},
    },
    "Documents/School/AP World History": {
        "threshold": 8,
        "phrases": {
            "ap world history": 8,
            "ap world": 6,
            "dbq": 5,
            "leq": 5,
            "saq": 5,
            "trade networks": 5,
            "empire": 3,
            "industrialization": 4,
            "continuity and change": 6,
        },
        "patterns": {},
    },
    "Documents/School/AP US History": {
        "threshold": 8,
        "phrases": {
            "ap us history": 8,
            "apush": 8,
            "dbq": 5,
            "leq": 5,
            "colonial": 3,
            "civil war": 4,
            "reconstruction": 4,
            "progressive era": 4,
            "cold war": 4,
        },
        "patterns": {},
    },
    "Documents/School/AP European History": {
        "threshold": 8,
        "phrases": {
            "ap european history": 8,
            "ap euro": 7,
            "renaissance": 4,
            "reformation": 4,
            "french revolution": 5,
            "industrial revolution": 5,
            "enlightenment": 4,
            "napoleonic": 4,
            "world war": 3,
        },
        "patterns": {},
    },
    "Documents/School/AP US Government": {
        "threshold": 8,
        "phrases": {
            "ap us government": 8,
            "ap gov": 7,
            "constitution": 4,
            "federalism": 5,
            "civil liberties": 5,
            "civil rights": 5,
            "supreme court": 5,
            "congress": 4,
            "bureaucracy": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Comparative Government": {
        "threshold": 8,
        "phrases": {
            "ap comparative government": 8,
            "comparative government": 7,
            "regime": 4,
            "sovereignty": 4,
            "political legitimacy": 6,
            "authoritarian": 4,
            "democratization": 5,
            "political culture": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Psychology": {
        "threshold": 8,
        "phrases": {
            "ap psychology": 8,
            "ap psych": 7,
            "cognition": 4,
            "neuroscience": 5,
            "learning theory": 5,
            "personality": 4,
            "developmental psychology": 6,
            "abnormal psychology": 6,
            "social psychology": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Macroeconomics": {
        "threshold": 8,
        "phrases": {
            "ap macroeconomics": 8,
            "ap macro": 7,
            "gdp": 5,
            "inflation": 5,
            "unemployment": 5,
            "aggregate demand": 6,
            "aggregate supply": 6,
            "monetary policy": 6,
            "fiscal policy": 6,
        },
        "patterns": {},
    },
    "Documents/School/AP Microeconomics": {
        "threshold": 8,
        "phrases": {
            "ap microeconomics": 8,
            "ap micro": 7,
            "supply and demand": 6,
            "market equilibrium": 6,
            "elasticity": 5,
            "marginal cost": 5,
            "monopoly": 4,
            "externality": 5,
            "consumer surplus": 5,
        },
        "patterns": {},
    },

    # AP World Languages
    "Documents/School/AP Spanish Language": {
        "threshold": 8,
        "phrases": {
            "ap spanish language": 8,
            "spanish language and culture": 8,
            "correo electronico": 5,
            "presentacion oral": 5,
            "conversacion": 4,
            "interpretive communication": 5,
            "interpersonal writing": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Spanish Literature": {
        "threshold": 8,
        "phrases": {
            "ap spanish literature": 8,
            "spanish literature and culture": 8,
            "analisis literario": 5,
            "poesia": 4,
            "prosa": 4,
            "obra": 3,
            "tema": 2,
        },
        "patterns": {},
    },
    "Documents/School/AP French": {
        "threshold": 8,
        "phrases": {
            "ap french": 8,
            "french language and culture": 8,
            "courriel": 5,
            "conversation": 3,
            "cultural comparison": 5,
            "interpretive communication": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP German": {
        "threshold": 8,
        "phrases": {
            "ap german": 8,
            "german language and culture": 8,
            "email reply": 4,
            "cultural comparison": 5,
            "interpretive communication": 5,
            "interpersonal speaking": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Italian": {
        "threshold": 8,
        "phrases": {
            "ap italian": 8,
            "italian language and culture": 8,
            "email reply": 4,
            "cultural comparison": 5,
            "interpretive communication": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Chinese": {
        "threshold": 8,
        "phrases": {
            "ap chinese": 8,
            "chinese language and culture": 8,
            "cultural presentation": 5,
            "email response": 4,
            "conversation": 3,
            "interpersonal speaking": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Japanese": {
        "threshold": 8,
        "phrases": {
            "ap japanese": 8,
            "japanese language and culture": 8,
            "cultural presentation": 5,
            "text chat": 4,
            "conversation": 3,
            "interpersonal speaking": 5,
        },
        "patterns": {},
    },
    "Documents/School/AP Latin": {
        "threshold": 8,
        "phrases": {
            "ap latin": 8,
            "vergil": 6,
            "caesar": 6,
            "aeneid": 6,
            "de bello gallico": 7,
            "latin sight reading": 6,
            "literal translation": 5,
        },
        "patterns": {},
    },
}

#endregion
