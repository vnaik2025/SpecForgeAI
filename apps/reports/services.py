import io
import json
import logging
import re
import time
import zipfile
from pathlib import Path

from django.conf import settings
from openai import OpenAI

from .enums import ReportStatus, ScaffoldStatus
from .models import AiAnalysis, ProjectScaffold, Report, TechStackBlueprint

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(settings.BASE_DIR) / "agent-prompts" / "summary-prompt.txt"
SCAFFOLD_PROMPT_FILE = Path(settings.BASE_DIR) / "agent-prompts" / "scaffold-prompt.txt"


def change_status(report, new_status, error=""):
    report.status = new_status
    report.error = error
    report.save(update_fields=["status", "error"])


def call_gemini(text):
    """Send text to Gemini (via Google's OpenAI-compatible endpoint) and return the Markdown reply."""
    client = OpenAI(
        api_key=settings.GEMINI_API_KEY,
        base_url=settings.GEMINI_BASE_URL,
        timeout=getattr(settings, "AI_REQUEST_TIMEOUT", 60.0),
    )
    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    response = client.chat.completions.create(
        model=settings.GEMINI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_openai(text):
    """Send text to OpenAI and return the Markdown reply."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_ai(text):
    """Call Gemini if configured, otherwise fall back to OpenAI."""
    if getattr(settings, "GEMINI_API_KEY", ""):
        return call_gemini(text)
    return call_openai(text)


def parse_robust_json(raw_content):
    """Safely decode JSON even if truncated by token limits or control chars."""
    text = raw_content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 1. Standard decode with strict=False
    try:
        return json.loads(text, strict=False)
    except Exception:
        pass

    # 2. Repair unclosed string or unclosed braces
    repaired = text
    if repaired.count('"') % 2 != 0:
        repaired += '"'
    open_braces = repaired.count("{") - repaired.count("}")
    if open_braces > 0:
        repaired += "}" * open_braces

    try:
        return json.loads(repaired, strict=False)
    except Exception:
        pass

    # 3. Regex extraction fallback for nested or flat keys
    result = {"frontend": {}, "backend": {}}
    subkeys = ["agents_md", "architecture_md", "setup_md", "skill_md", "api_setup_md", "initial_prompt"]
    
    # Try finding frontend block and backend block
    fe_match = re.search(r'"frontend"\s*:\s*\{(.*?)\}(?:\s*,\s*"backend"|\s*\})', text, re.DOTALL)
    be_match = re.search(r'"backend"\s*:\s*\{(.*?)\}\s*\}', text, re.DOTALL)
    
    if fe_match:
        fe_text = fe_match.group(1)
        for k in subkeys:
            m = re.search(r'"' + k + r'"\s*:\s*"(.*?)(?:"(?:\s*,\s*"[a-zA-Z_]+"|\s*\})|\Z)', fe_text, re.DOTALL)
            if m:
                result["frontend"][k] = m.group(1).replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
    if be_match:
        be_text = be_match.group(1)
        for k in subkeys:
            m = re.search(r'"' + k + r'"\s*:\s*"(.*?)(?:"(?:\s*,\s*"[a-zA-Z_]+"|\s*\})|\Z)', be_text, re.DOTALL)
            if m:
                result["backend"][k] = m.group(1).replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")

    # Top-level keys fallback
    for k in subkeys + ["detected_tech_stack", "frontend_agents_md", "backend_agents_md"]:
        m = re.search(r'"' + k + r'"\s*:\s*"(.*?)(?:"(?:\s*,\s*"[a-zA-Z_]+"|\s*\})|\Z)', text, re.DOTALL)
        if m:
            result[k] = m.group(1).replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")

    return result


def call_ai_structured(system_prompt, user_content):
    """Call Gemini/OpenAI expecting structured JSON output with retries, fallback models, and robust parser."""
    client = OpenAI(
        api_key=settings.GEMINI_API_KEY if getattr(settings, "GEMINI_API_KEY", "") else settings.OPENAI_API_KEY,
        base_url=settings.GEMINI_BASE_URL if getattr(settings, "GEMINI_API_KEY", "") else None,
        timeout=getattr(settings, "AI_REQUEST_TIMEOUT", 60.0),
    )
    primary_model = settings.GEMINI_MODEL if getattr(settings, "GEMINI_API_KEY", "") else settings.OPENAI_MODEL

    # Fallback models in case of transient 503 high demand spikes
    models_to_try = [primary_model]
    if getattr(settings, "GEMINI_API_KEY", ""):
        for m in ["gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-3.1-flash-lite"]:
            if m not in models_to_try:
                models_to_try.append(m)

    last_error = None
    for model in models_to_try:
        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=8192,
                    temperature=0.3,
                )
                raw_content = response.choices[0].message.content or ""
                parsed = parse_robust_json(raw_content)
                if parsed and any(parsed.values()):
                    return parsed
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                # If 429 quota exceeded on this model, try next available model in list
                if "429" in err_str or "quota" in err_str.lower() or "resource_exhausted" in err_str.lower():
                    logger.warning("Model %s hit rate/quota limit, falling back to next candidate model.", model)
                    break
                if "503" in err_str or "demand" in err_str:
                    time.sleep(1.0)
                    break
                time.sleep(0.5)

    raise last_error or RuntimeError("Failed to generate structured specification.")



def match_blueprint(scope_text):
    """Find the best matching TechStackBlueprint based on keywords or default to first."""
    blueprints = TechStackBlueprint.objects.all()
    if not blueprints.exists():
        return None

    scope_lower = scope_text.lower()
    best_match = None
    max_hits = 0

    for bp in blueprints:
        hits = 0
        for kw in bp.keywords:
            if kw.lower() in scope_lower:
                hits += 1
        if hits > max_hits:
            max_hits = hits
            best_match = bp

    return best_match or blueprints.first()


def analyse_report(report):
    """Run the full workflow for one report and return the saved AiAnalysis."""
    change_status(report, ReportStatus.PROCESSING.value)
    try:
        markdown = call_ai(f"Title: {report.title}\n\n{report.content}")
        analysis = AiAnalysis.objects.create(report=report, summary_markdown=markdown)
        change_status(report, ReportStatus.COMPLETED.value)
        return analysis
    except Exception as exc:
        logger.exception("Analysis failed for report %s", report.id)
        change_status(report, ReportStatus.FAILED.value, error=str(exc))
        raise


def extract_clean_text_from_docx_stream(raw_text: str) -> tuple[str, str]:
    """Extract clean title and human-readable text from raw Word .docx streams or binary strings."""
    if not raw_text:
        return "", ""
    if not ("PK" in raw_text and ("word/" in raw_text or "document.xml" in raw_text or "[Content_Types]" in raw_text)):
        return "", raw_text

    doc_title = ""
    paragraphs = []

    # Method 1: Try reading as a zip archive via BytesIO with multiple encodings
    for enc in ["latin-1", "utf-8", "cp1252"]:
        try:
            raw_bytes = raw_text.encode(enc, errors="ignore")
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                doc_entry = None
                for name in zf.namelist():
                    if name.endswith("word/document.xml"):
                        doc_entry = name
                        break
                if doc_entry:
                    xml_bytes = zf.read(doc_entry)
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(xml_bytes)
                    for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                        texts = [t.text for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
                        p_text = "".join(texts).strip()
                        if p_text:
                            paragraphs.append(p_text)
                    if paragraphs:
                        break
        except Exception:
            continue

    # Method 2: Fallback regex extraction of XML <w:t> tags from raw string
    if not paragraphs:
        t_matches = re.findall(r'<w:t[^>]*>(.*?)</w:t>', raw_text, re.DOTALL)
        if t_matches:
            buf = []
            for tm in t_matches:
                clean_t = re.sub(r'<[^>]+>', '', tm).strip()
                if clean_t:
                    buf.append(clean_t)
                    if len(buf) >= 3 or clean_t.endswith(('.', ':', '?', '!')):
                        paragraphs.append(" ".join(buf))
                        buf = []
            if buf:
                paragraphs.append(" ".join(buf))

    # Method 3: Clean up control characters and extract readable sequences if still empty
    if not paragraphs:
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', ' ', raw_text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        words = [w for w in cleaned.split(' ') if len(w) > 2 and any(c.isalpha() for c in w)]
        if len(words) > 10:
            paragraphs.append(" ".join(words[:500]))

    if paragraphs:
        for p in paragraphs[:5]:
            if 3 <= len(p) <= 60 and not p.lower().startswith(('table of contents', 'overview', 'page')):
                doc_title = p
                break
        clean_content = "\n\n".join(paragraphs).strip()
        return doc_title, clean_content

    return "", raw_text


def extract_clean_text_from_scope_stream(raw_text: str) -> tuple[str, str]:
    """Universal scope cleaner: automatically handles PDF streams, DOCX/PK streams, or returns clean text."""
    if not raw_text:
        return "", ""
    if "%PDF" in raw_text or "1 0 obj" in raw_text or "endobj" in raw_text or "/Filter /FlateDecode" in raw_text:
        return extract_clean_text_from_pdf_stream(raw_text)
    if "PK" in raw_text and ("word/" in raw_text or "document.xml" in raw_text or "[Content_Types]" in raw_text):
        return extract_clean_text_from_docx_stream(raw_text)
    return "", raw_text


def extract_clean_text_from_pdf_stream(raw_text: str) -> tuple[str, str]:
    """Extract clean title and human-readable text from raw PDF streams or text."""
    if not raw_text:
        return "", ""
    if "PK" in raw_text and ("word/" in raw_text or "document.xml" in raw_text):
        return extract_clean_text_from_docx_stream(raw_text)
    if not ("%PDF" in raw_text or "1 0 obj" in raw_text or "endobj" in raw_text or "/Filter /FlateDecode" in raw_text):
        return "", raw_text

    # Extract Title metadata
    titles = re.findall(r'/Title\s*\((.*?)\)', raw_text)
    doc_title = ""
    clean_titles = []
    for t in titles:
        t_clean = t.replace(r'\(', '(').replace(r'\)', ')').strip()
        if t_clean and t_clean not in clean_titles:
            clean_titles.append(t_clean)
    if clean_titles:
        doc_title = clean_titles[0]

    # Extract Alt text from figure objects
    alt_matches = re.findall(r'/Alt\s*<FEFF([0-9A-Fa-f]+)>', raw_text)
    alt_texts = []
    for hex_str in alt_matches:
        try:
            decoded = bytes.fromhex(hex_str).decode('utf-16-be').strip()
            if decoded:
                alt_texts.append(decoded)
        except Exception:
            pass

    # Extract readable strings from text parentheses
    paren_texts = re.findall(r'\(([^)]{4,})\)', raw_text)
    readable_strings = []
    for pt in paren_texts:
        pt_clean = pt.replace(r'\(', '(').replace(r'\)', ')').strip()
        if not pt_clean.startswith(('D:', 'node', 'en', 'Identity', 'Adobe')):
            if any(c.isalpha() for c in pt_clean) and len(pt_clean) > 3:
                if pt_clean not in readable_strings:
                    readable_strings.append(pt_clean)

    sections = []
    main_title = doc_title or "Uploaded Project Scope"
    sections.append(f"# Project Scope: {main_title}\n")
    if clean_titles and len(clean_titles) > 1:
        sections.append("## Key Architectural Sections & Workflows:")
        for st in clean_titles[1:]:
            sections.append(f"- {st}")
        sections.append("")

    if alt_texts:
        sections.append("## Architecture Pipelines & Pilot Phases:")
        for at in alt_texts:
            sections.append(f"- {at}")
        sections.append("")

    if readable_strings:
        sections.append("## Scope Specifications & Domain Requirements:")
        for rs in readable_strings[:50]:
            sections.append(f"- {rs}")

    clean_content = "\n".join(sections).strip()
    return doc_title, clean_content if len(clean_content) > 40 else raw_text


def extract_scope_fields_fallback(scope_content: str, filename: str = "") -> dict:
    """
    Robust rule-based metadata and technology stack extractor.
    Guarantees instant, reliable classification even without AI connectivity.
    """
    lines = [line.strip() for line in (scope_content or "").splitlines() if line.strip()]
    scope_lower = (scope_content or "").lower()

    # 1. Title Extraction
    title = ""
    stale_names = ["project scope", "scope", "prd", "document", "sample", "untitled", "requirements", "specification"]
    if filename:
        clean_fn = re.sub(r'\.(pdf|docx?|txt|md|markdown)$', '', filename, flags=re.IGNORECASE)
        clean_fn = re.sub(r'[-_]', ' ', clean_fn).strip()
        if clean_fn and not any(clean_fn.lower().startswith(x) for x in stale_names):
            title = clean_fn.title()

    if not title:
        title_match = re.search(r'^(?:#\s*Project\s*Scope:\s*|#\s*Title:\s*|#\s*)([^\r\n]+)', scope_content or "", re.MULTILINE | re.IGNORECASE)
        if title_match:
            cand = title_match.group(1).strip()
            if cand and len(cand) > 2 and cand.lower() not in stale_names:
                title = cand

    if not title:
        pdf_title = re.search(r'/Title\s*\(([^)]+)\)', scope_content or "")
        if pdf_title:
            cand = pdf_title.group(1).strip()
            if cand and len(cand) > 2:
                title = cand

    if not title and lines:
        first_line = lines[0].lstrip('#*-0123456789. ').strip()
        if len(first_line) > 3 and not first_line.startswith('/'):
            title = first_line[:60]

    if not title:
        title = "Enterprise Software System"

    # 2. Categorized Tech Stack Detection
    frontend = []
    backend = []
    database = []
    libraries_and_services = []

    # Frontend checks
    if "next.js" in scope_lower or "nextjs" in scope_lower:
        frontend.extend(["Next.js", "React", "TypeScript"])
    elif "react" in scope_lower:
        frontend.append("React")
        if "vite" in scope_lower:
            frontend.append("Vite")
    elif "vue" in scope_lower or "nuxt" in scope_lower:
        frontend.append("Vue.js")
        if "nuxt" in scope_lower:
            frontend.append("Nuxt.js")
    elif "svelte" in scope_lower:
        frontend.append("Svelte")
    elif "angular" in scope_lower:
        frontend.append("Angular")
    elif "vanilla" in scope_lower:
        frontend.append("Vanilla JS")

    if "tailwind" in scope_lower:
        frontend.append("Tailwind CSS")
    elif "bootstrap" in scope_lower:
        frontend.append("Bootstrap")
    elif "shadcn" in scope_lower:
        frontend.append("Shadcn/UI")

    if "redux" in scope_lower:
        frontend.append("Redux")
    elif "zustand" in scope_lower:
        frontend.append("Zustand")

    if "tanstack" in scope_lower or "react query" in scope_lower:
        frontend.append("TanStack Query")
    if "axios" in scope_lower:
        frontend.append("Axios")

    # Backend checks
    if "django" in scope_lower:
        backend.append("Django")
        if any(k in scope_lower for k in ["drf", "rest framework", "rest_framework"]):
            backend.append("DRF")
    elif "fastapi" in scope_lower:
        backend.extend(["FastAPI", "Python", "Pydantic"])
    elif "flask" in scope_lower:
        backend.extend(["Flask", "Python"])
    elif "express" in scope_lower or "node" in scope_lower:
        backend.extend(["Node.js", "Express"])
    elif "nestjs" in scope_lower:
        backend.extend(["NestJS", "TypeScript"])
    elif "spring" in scope_lower or "java" in scope_lower:
        backend.extend(["Java", "Spring Boot"])
    elif "golang" in scope_lower or "go " in scope_lower:
        backend.extend(["Go", "Gin"])
    elif "asp.net" in scope_lower or ".net" in scope_lower:
        backend.extend(["C#", "ASP.NET Core"])

    # Database checks
    if "postgres" in scope_lower:
        database.append("PostgreSQL")
    if "redis" in scope_lower:
        database.append("Redis")
    if "mongo" in scope_lower:
        database.append("MongoDB")
    if "mysql" in scope_lower:
        database.append("MySQL")
    if "sqlite" in scope_lower:
        database.append("SQLite")
    if "supabase" in scope_lower:
        database.append("Supabase")

    # Libraries, Auth & External Services
    if any(k in scope_lower for k in ["jwt", "token", "simplejwt"]):
        libraries_and_services.append("simplejwt" if "django" in scope_lower else "JWT")
    if "celery" in scope_lower:
        libraries_and_services.append("Celery")
    if any(k in scope_lower for k in ["stripe", "payment"]):
        libraries_and_services.append("Stripe API")
    if any(k in scope_lower for k in ["openai", "gpt", "llm"]):
        libraries_and_services.append("OpenAI API")
    if any(k in scope_lower for k in ["gemini", "google ai"]):
        libraries_and_services.append("Gemini API")
    if any(k in scope_lower for k in ["aws", "s3", "bucket"]):
        libraries_and_services.append("AWS S3")
    if "docker" in scope_lower:
        libraries_and_services.append("Docker")
    if any(k in scope_lower for k in ["websocket", "realtime", "socket.io"]):
        libraries_and_services.append("WebSockets")

    # Provide smart defaults if scope was brief
    if not frontend:
        frontend = ["React", "Tailwind CSS", "Vite"]
    if not backend:
        backend = ["Django", "DRF"]
    if not database:
        database = ["PostgreSQL"]
    if not libraries_and_services:
        libraries_and_services = ["JWT", "REST API"]

    # Combine all tags cleanly
    all_tags = []
    for grp in [backend, frontend, database, libraries_and_services]:
        for tag in grp:
            if tag not in all_tags:
                all_tags.append(tag)

    # 3. Extract or ideate modules
    detected_modules = []
    keywords_map = {
        "Authentication & RBAC": ["auth", "login", "signup", "jwt", "rbac", "role", "user", "permission"],
        "Product Catalog Management": ["product", "catalog", "item", "inventory", "stock", "category"],
        "Orders & Checkout Processing": ["order", "cart", "checkout", "payment", "invoice", "billing"],
        "Operational Pipeline & Workflows": ["pipeline", "ticket", "task", "issue", "sprint", "workflow"],
        "Customer & Account Directory": ["customer", "client", "member", "directory", "profile"],
        "Analytics & Performance KPIs": ["analytics", "report", "metrics", "kpi", "dashboard", "summary", "stats"],
        "Notifications & Communications": ["notification", "alert", "email", "sms", "message", "event"],
        "System Settings & Integrations": ["settings", "admin", "config", "audit", "integration"],
    }
    for mod_name, kws in keywords_map.items():
        if any(k in scope_lower for k in kws):
            detected_modules.append(mod_name)

    if len(detected_modules) < 3:
        detected_modules = ["Overview Dashboard", "Core Operations Workspace", "Data & Records Directory", "Analytics & Insights", "System Settings"]

    # 4. Suggested notes: ONLY populate if explicit VIP points or constraints exist in scope
    vip_lines = []
    for line in lines:
        l_low = line.lower()
        if any(k in l_low for k in ["vip", "critical requirement", "strict requirement", "strict constraint", "must adhere", "must follow", "custom constraint"]):
            cleaned_l = line.lstrip('#*-0123456789. ').strip()
            if cleaned_l and cleaned_l not in vip_lines:
                vip_lines.append(cleaned_l)
    suggested_notes = " • ".join(vip_lines) if vip_lines else ""

    summary = f"Comprehensive {title} architecture covering {len(detected_modules)} functional modules, powered by {', '.join(backend[:2])} and {', '.join(frontend[:2])}."

    return {
        "title": title,
        "summary": summary,
        "frontend": frontend,
        "backend": backend,
        "database": database,
        "libraries_and_services": libraries_and_services,
        "all_tech_tags": all_tags,
        "suggested_notes": suggested_notes,
        "modules": detected_modules,
    }


def extract_scope_fields_with_ai(scope_text: str, filename: str = "") -> dict:
    """
    1st-place AI analysis phase to extract structured metadata, categorized tech stack,
    and ideated modules from uploaded documents or PDF scopes.
    Uses Gemini LLM with robust JSON decoding, gracefully falling back to the rich heuristic extractor.
    """
    # 1. Clean PDF stream bytes if present
    doc_title, clean_scope = extract_clean_text_from_pdf_stream(scope_text)
    effective_scope = clean_scope if clean_scope and len(clean_scope) > 30 else scope_text

    # Check for AI API key
    client = None
    if getattr(settings, "GEMINI_API_KEY", ""):
        client = OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
        )
    elif getattr(settings, "OPENAI_API_KEY", ""):
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

    if not client:
        logger.info("No AI API key configured for scope extraction; running heuristic extractor.")
        res = extract_scope_fields_fallback(effective_scope, filename=filename)
        if doc_title and not res.get("title"):
            res["title"] = doc_title
        return res

    system_prompt = """You are an elite Principal Software Architect and AI Technical Analyst.
Analyze the provided project scope document, PRD, or technical specification.
Your goal is to extract key project metadata and accurately classify the entire technology stack into cleanly separated layers: Frontend, Backend, Database, and Libraries / Service Providers.

CRITICAL INSTRUCTIONS:
1. Extract or infer a concise, domain-specific project title (e.g. "School Accessories Mart", "PulseDesk Incident Hub", "CarePulse Telehealth").
2. Accurately identify or suggest all technology components:
   - Frontend: frameworks, UI libraries, CSS frameworks, state management (e.g. React, Tailwind CSS, Vite, Zustand, Next.js, Vue).
   - Backend: frameworks, runtimes, languages, ORM (e.g. Django, DRF, FastAPI, Node.js, Express, Go, Python).
   - Database: primary databases, caches (e.g. PostgreSQL, Redis, MongoDB, MySQL, SQLite).
   - Libraries & Services: authentication packages, external service providers, APIs, cloud tools (e.g. SimpleJWT, Stripe API, Celery, AWS S3, OpenAI API).
3. Deduplicate all identified technologies into a clean "all_tech_tags" array suitable for UI tags.
4. Ideate/identify 4-8 core functional modules or pages based on scope requirements.
5. Suggested Notes: Extract ONLY if the document explicitly specifies VIP points, strict architectural constraints, or custom directives. If none are explicitly provided in the scope document, return an empty string "". Never make up placeholder notes.

You must respond ONLY with a valid JSON object matching this exact schema:
{
  "title": "string",
  "summary": "string",
  "frontend": ["string"],
  "backend": ["string"],
  "database": ["string"],
  "libraries_and_services": ["string"],
  "all_tech_tags": ["string"],
  "suggested_notes": "string",
  "modules": ["string"]
}
"""

    user_prompt = f"""PROJECT DOCUMENT FILENAME: {filename or 'scope_document.txt'}
DOCUMENT PREVIEW / TITLE METADATA: {doc_title or 'N/A'}

DOCUMENT CONTENT:
{effective_scope[:14000]}

Analyze this document and extract the project title, executive summary, categorized tech stack (frontend, backend, database, libraries/services), explicit notes (if any), and ideated core modules as JSON now."""

    model_to_use = settings.GEMINI_MODEL if getattr(settings, "GEMINI_API_KEY", "") else settings.OPENAI_MODEL
    try:
        response = client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        raw_reply = response.choices[0].message.content or ""
        parsed = parse_robust_json(raw_reply)
        if isinstance(parsed, dict) and parsed.get("title"):
            # Ensure lists
            frontend = [str(x) for x in parsed.get("frontend", []) if x]
            backend = [str(x) for x in parsed.get("backend", []) if x]
            database = [str(x) for x in parsed.get("database", []) if x]
            libs = [str(x) for x in parsed.get("libraries_and_services", []) if x]
            all_tags = [str(x) for x in parsed.get("all_tech_tags", []) if x]

            if not all_tags:
                all_tags = list(dict.fromkeys(backend + frontend + database + libs))

            return {
                "title": parsed.get("title") or (doc_title or "Autonomous Software System"),
                "summary": parsed.get("summary") or "",
                "frontend": frontend,
                "backend": backend,
                "database": database,
                "libraries_and_services": libs,
                "all_tech_tags": all_tags,
                "suggested_notes": parsed.get("suggested_notes") or "",
                "modules": [str(m) for m in parsed.get("modules", []) if m],
            }
    except Exception as exc:
        logger.warning("AI scope analysis call failed: %s. Using heuristic extractor.", exc)

    fallback = extract_scope_fields_fallback(effective_scope, filename=filename)
    if doc_title and (not fallback.get("title") or fallback.get("title") == "Enterprise Software System"):
        fallback["title"] = doc_title
    return fallback


def analyze_scope_and_tech_stack(scope_text: str, custom_title: str = "", custom_tech_stack: str = "", custom_notes: str = "") -> dict:
    """
    Intelligently analyze the project scope:
    - Extracts title (honoring document headers or non-placeholder titles).
    - Detects tech stack (honoring user custom stack, else scanning scope text for framework keywords).
    - Extracts domain requirements, bullet points, entities, data models, and workflow verbs.
    - Generates REST endpoints and KPI metrics tailored to the extracted domain.
    """
    lines = [line.strip() for line in (scope_text or "").splitlines() if line.strip()]
    scope_lower = (scope_text or "").lower()

    # 1. Title Extraction
    title = ""
    stale_titles = ["School Accessories Mart", "PulseDesk Issue Tracker", "Project Workspace", "PulseDesk", "School Mart"]
    if custom_title and custom_title.strip() not in stale_titles:
        title = custom_title.strip()
    else:
        title_match = re.search(r'^(?:#\s*Project\s*Scope:\s*|#\s*Title:\s*|#\s*)([^\r\n]+)', scope_text or "", re.MULTILINE | re.IGNORECASE)
        if title_match:
            candidate = title_match.group(1).strip()
            if candidate and candidate not in stale_titles and len(candidate) > 2:
                title = candidate
        if not title:
            pdf_title = re.search(r'/Title\s*\(([^)]+)\)', scope_text or "")
            if pdf_title:
                title = pdf_title.group(1).strip()
        if not title and lines:
            first_line = lines[0].lstrip('#*-0123456789. ').strip()
            if len(first_line) > 3 and not first_line.startswith('/'):
                title = first_line[:60]
    if not title:
        title = "Autonomous Software System"

    # 2. Tech Stack Detection
    stack = ""
    if custom_tech_stack and custom_tech_stack.strip():
        stack = custom_tech_stack.strip()
    else:
        detected_parts = []
        if "next.js" in scope_lower or "nextjs" in scope_lower:
            detected_parts.append("Next.js")
        elif "react" in scope_lower:
            detected_parts.append("React 18" + (" (Vite)" if "vite" in scope_lower else ""))
        elif "vue" in scope_lower:
            detected_parts.append("Vue.js")
        elif "svelte" in scope_lower:
            detected_parts.append("Svelte")

        if "tailwind" in scope_lower:
            detected_parts.append("Tailwind CSS")

        if "django" in scope_lower:
            detected_parts.append("Django" + (" REST Framework" if any(k in scope_lower for k in ["drf", "rest framework", "rest_framework"]) else ""))
        elif "fastapi" in scope_lower:
            detected_parts.append("FastAPI")
        elif "express" in scope_lower or "node" in scope_lower:
            detected_parts.append("Node.js, Express.js")
        elif "flask" in scope_lower:
            detected_parts.append("Flask")

        if "postgres" in scope_lower:
            detected_parts.append("PostgreSQL")
        elif "mongo" in scope_lower:
            detected_parts.append("MongoDB")
        elif "mysql" in scope_lower:
            detected_parts.append("MySQL")
        elif "sqlite" in scope_lower:
            detected_parts.append("SQLite")
        elif "redis" in scope_lower:
            detected_parts.append("Redis")

        if any(k in scope_lower for k in ["voice", "audio", "whisper", "stt", "speech"]):
            detected_parts.append("Web Speech / MediaRecorder Audio Pipeline")
        if any(k in scope_lower for k in ["jwt", "token", "auth"]):
            detected_parts.append("JWT Authentication")
        if any(k in scope_lower for k in ["websocket", "realtime", "real-time"]):
            detected_parts.append("WebSockets Realtime")
        if any(k in scope_lower for k in ["rest", "api"]):
            detected_parts.append("RESTful API")

        if detected_parts:
            seen = set()
            clean_parts = []
            for p in detected_parts:
                if p not in seen:
                    seen.add(p)
                    clean_parts.append(p)
            stack = ", ".join(clean_parts)
        else:
            stack = "React 18 (Vite), Tailwind CSS, Node.js, Express, PostgreSQL, REST API"

    # 3. Requirements & Feature Extraction
    features = []
    for line in lines:
        cleaned = line.lstrip('#*-0123456789. ').strip()
        if len(cleaned) > 8 and not cleaned.startswith('http') and not cleaned.startswith('/') and len(cleaned) < 110:
            if not any(cleaned.lower().startswith(skip) for skip in ["title", "scope", "table of contents", "overview", "introduction", "document"]):
                if cleaned not in features:
                    features.append(cleaned)
        if len(features) >= 50:
            break

    if not features:
        features = [
            f"{title} Core Domain & Workflow Engine",
            "User Authentication, Authorization & Session Management",
            "Data Ingestion, Schema Validation & Persistence Layer",
            "Business Logic Processing & Domain Rules Execution",
            "Interactive Responsive Client Application & Real-time State",
            "Audit Logging, Performance Monitoring & Metric Telemetry"
        ]

    # 4. Domain Entities Detection
    common_entities = [
        "Customer", "User", "Order", "Product", "Transaction", "Item", "Ticket",
        "Invoice", "Payment", "Account", "Merchant", "Patient", "Appointment",
        "Vehicle", "Driver", "Trip", "Document", "Project", "Task", "Sprint",
        "Sensor", "Device", "Reading", "Message", "Event", "AuditLog", "Ledger",
        "School", "Uniform", "Student", "Parent", "Khata", "Category"
    ]
    detected_entities = []
    for ent in common_entities:
        if ent.lower() in scope_lower:
            detected_entities.append(ent)

    if not detected_entities:
        words = [re.sub(r'[^a-zA-Z]', '', w).capitalize() for w in title.split() if len(w) > 3]
        detected_entities = words[:2] if words else ["Record", "Item"]

    primary_entity = detected_entities[0]
    secondary_entity = detected_entities[1] if len(detected_entities) > 1 else (detected_entities[0] + "Item")
    primary_plural = primary_entity.lower() + ("es" if primary_entity.endswith(('s', 'x', 'ch', 'sh')) else "s")
    secondary_plural = secondary_entity.lower() + ("es" if secondary_entity.endswith(('s', 'x', 'ch', 'sh')) else "s")

    # 5. REST Endpoints Derivation
    endpoints = [
        {"method": "GET", "path": f"/api/v1/{primary_plural}/", "desc": f"List and query {primary_plural} with filtering & pagination"},
        {"method": "POST", "path": f"/api/v1/{primary_plural}/", "desc": f"Create and persist a new {primary_entity} record"},
        {"method": "GET", "path": f"/api/v1/{primary_plural}/:id/", "desc": f"Retrieve single {primary_entity} details and state"},
        {"method": "PATCH", "path": f"/api/v1/{primary_plural}/:id/", "desc": f"Update {primary_entity} attributes and lifecycle status"},
        {"method": "DELETE", "path": f"/api/v1/{primary_plural}/:id/", "desc": f"Soft-delete / archive {primary_entity} record"},
        {"method": "GET", "path": f"/api/v1/{secondary_plural}/", "desc": f"List associated {secondary_plural} collection"},
        {"method": "POST", "path": f"/api/v1/{primary_plural}/:id/action/", "desc": f"Trigger domain operational action for {primary_entity}"},
        {"method": "GET", "path": "/api/v1/analytics/summary/", "desc": "Retrieve real-time KPI metrics and operational summary"},
    ]

    words = [w for w in title.replace('-', ' ').replace('_', ' ').split() if w]
    prefix = "".join(w[0].upper() for w in words[:3]) or "APP"

    return {
        "title": title,
        "tech_stack": stack,
        "features": features,
        "entities": detected_entities,
        "primary_entity": primary_entity,
        "secondary_entity": secondary_entity,
        "primary_plural": primary_plural,
        "secondary_plural": secondary_plural,
        "endpoints": endpoints,
        "prefix": prefix,
    }


def generate_dynamic_specifications(scaffold, blueprint=None, analysis: dict = None) -> dict:
    """Dynamically generate high-fidelity, complete project specifications (.md files) tailored directly to the project scope and tech stack."""
    if not analysis:
        analysis = analyze_scope_and_tech_stack(
            scaffold.scope_document or "",
            custom_title=scaffold.title or "",
            custom_tech_stack=scaffold.custom_tech_stack or "",
            custom_notes=scaffold.custom_notes or ""
        )

    title = analysis["title"]
    stack = scaffold.custom_tech_stack or analysis["tech_stack"] or (blueprint.name if blueprint else "React, Vite, Tailwind CSS, Node.js, Express, PostgreSQL")
    features = analysis["features"]
    primary_entity = analysis["primary_entity"]
    secondary_entity = analysis["secondary_entity"]
    primary_plural = analysis["primary_plural"]
    secondary_plural = analysis["secondary_plural"]
    prefix = analysis["prefix"]

    # --- FRONTEND SPECIFICATIONS ---
    fe_agents_md = f"""# FRONTEND AI AGENT BOUNDARIES & ARCHITECTURAL DIRECTIVES

## Project: {title} (Frontend Client)
**Domain:** Client-Side User Interface & Application State Engine
**Target Tech Stack:** {stack}

### 1. Architectural Boundaries & UI Directives
* **Strict Client Bounded Context:** All code under `frontend/` must focus exclusively on responsive rendering, user experience, local state, and API integration for **{title}**. Scope creep into backend persistence is forbidden.
* **Three-Tier Component Taxonomy:**
  - **Tier 1 (Base UI Primitives):** Pure presentational components without business logic (`Button`, `Badge`, `Modal`, `Input`, `Select`, `Card`, `StatusPill`).
  - **Tier 2 (Form & Control Widgets):** Interactive components with client validation (`{primary_entity}Form`, `{secondary_entity}Picker`, `SearchFilterBar`, `DateRangeFilter`).
  - **Tier 3 (Domain Composite Views):** Rich domain views consuming client hooks (`{primary_entity}Table`, `{primary_entity}Card`, `{primary_entity}DetailDrawer`, `AnalyticsOverview`).
* **Service Layer Decoupling:** UI components must never issue raw `fetch` or direct network calls. All operations must pass through dedicated client services (`services/{primary_entity.lower()}Api.js`, `services/apiClient.js`).
* **State Immutability & Reactivity:** Manage server state and caching through custom hooks (`use{primary_entity}s`, `use{secondary_entity}s`) with optimistic UI updates and error rollback.
* **Responsive Design:** Mobile-first layout adhering to standard responsive breakpoints with dark/light theme tokens and WCAG 2.1 AA accessibility.

### 2. Frontend Engineering Conventions
| Rule | Convention | Example |
| :--- | :--- | :--- |
| Component Files | PascalCase or kebab-case matching standard | `{primary_entity}Card.jsx`, `{primary_entity}Table.jsx` |
| Custom Hooks | `use` prefix with domain resource | `use{primary_entity}s.js`, `use{secondary_entity}s.js` |
| API Service Modules | Resource noun + `Api` | `{primary_entity.lower()}Api.js`, `authApi.js` |
| State Updates | Functional updates with immutability | `set{primary_plural}(prev => [...prev, newRecord])` |
"""

    fe_architecture_md = f"""# FRONTEND ARCHITECTURE SPECIFICATION: {title}

## 1. Directory Structure & Layout
The frontend client implements a modular, component-driven structure built with **{stack}**.

```
frontend/
├── public/                      # Static assets, icons, manifest
├── src/
│   ├── assets/                  # CSS stylesheets, branding SVG assets
│   ├── components/
│   │   ├── common/              # Navbar.jsx, Sidebar.jsx, Modal.jsx, Toast.jsx, StatCard.jsx
│   │   ├── {primary_plural}/    # {primary_entity}Table.jsx, {primary_entity}Card.jsx, {primary_entity}Modal.jsx
│   │   └── {secondary_plural}/  # {secondary_entity}List.jsx, {secondary_entity}Picker.jsx
│   ├── hooks/                   # use{primary_entity}s.js, use{secondary_entity}s.js, useAuth.js
│   ├── services/                # apiClient.js, {primary_entity.lower()}Api.js
│   ├── context/                 # AuthContext.jsx, ThemeContext.jsx
│   ├── pages/                   # Dashboard.jsx, {primary_entity}Explorer.jsx, Settings.jsx
│   ├── App.jsx                  # Root router & global providers
│   └── main.jsx                 # Entrypoint
├── package.json
└── vite.config.js / tailwind.config.js
```

## 2. Client State & Data Flow
* **Data Fetching:** Encapsulated in custom hooks with loading, error, and cached data states.
* **Error Boundaries:** Top-level and widget-level error boundaries to gracefully catch runtime rendering failures.
* **Toast & Notification Dispatcher:** Global event-driven toast notifications for async mutations (e.g., `{primary_entity} created successfully`).

## 3. UI Requirements from Scope
{chr(10).join(f'* {feat}' for feat in features[:15])}
"""

    fe_setup_md = f"""# FRONTEND SETUP & RUN PLAYBOOK: {title}

## Prerequisites
- Node.js 18.x or 20.x LTS
- Package manager: `npm` or `pnpm` or `yarn`

## Quickstart Sequence

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Configure Environment Variables
Create `.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE={title}
```

### 3. Install Dependencies
```bash
npm install
```

### 4. Run Development Server
```bash
npm run dev
```
Open `http://localhost:5173` to interact with the frontend application.

### 5. Production Build & Linting
```bash
npm run build
npm run preview
npm run lint
```
"""

    fe_skill_md = f"""# FRONTEND AGENT CAPABILITY SPECIFICATION (SKILLS.md)

## Skill 1: UI Component Catalog & Accessibility Auditor
```bash
npm run skill:audit-ui -- --scope={primary_plural}
```
Verifies WCAG 2.1 compliance, contrast ratios, and keyboard navigation across all `{primary_plural}` views.

## Skill 2: Design Token & Styling Sanity Check
```bash
npm run skill:lint-tokens
```
Validates consistent color palettes, typography classes, spacing units, and responsive breakpoints.

## Skill 3: Frontend Mock State Generator
```bash
npm run skill:generate-mock-state -- --count=20
```
Generates realistic seed fixtures for local offline UI testing and Storybook verification.
"""

    endpoints_rows = "\n".join([f"| {ep['method']} | `{ep['path']}` | {ep['desc']} |" for ep in analysis["endpoints"]])
    fe_api_setup_md = f"""# FRONTEND API CLIENT INTEGRATION SPECIFICATION: {title}

### Base URL Configuration
```javascript
// src/services/apiClient.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({{
  baseURL: API_BASE_URL,
  headers: {{ 'Content-Type': 'application/json' }},
  timeout: 10000,
}});

// Attach JWT token automatically
apiClient.interceptors.request.use(config => {{
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${{token}}`;
  return config;
}});
```

### Service Methods for {primary_entity}
```javascript
// src/services/{primary_entity.lower()}Api.js
import {{ apiClient }} from './apiClient';

export const {primary_entity.lower()}Api = {{
  getAll: (params) => apiClient.get('/{primary_plural}/', {{ params }}),
  getById: (id) => apiClient.get(`/{primary_plural}/${{id}}/`),
  create: (data) => apiClient.post('/{primary_plural}/', data),
  update: (id, data) => apiClient.patch(`/{primary_plural}/${{id}}/`, data),
  delete: (id) => apiClient.delete(`/{primary_plural}/${{id}}/`),
}};
```

### Expected Endpoints
| Method | Route | Description |
| :--- | :--- | :--- |
{endpoints_rows}
"""

    fe_initial_prompt = f"""# FRONTEND CODING AGENT KICKOFF INSTRUCTIONS

You are the Lead Frontend / UI Engineer tasked with implementing the client interface for **{title}**.
You must build a high-performance, polished client application using **{stack}**.

### Execution Directives:
1. Review `frontend/AGENT.md` for three-tier component taxonomy, state immutability, and styling rules.
2. Review `frontend/ARCHITECTURE.md` for directory layout, pages, and component hierarchy.
3. Review `frontend/SETUP.md` for development environment configuration.
4. Review `frontend/API_SETUP.md` for HTTP client interceptors and service methods.
5. Review `frontend/UI_PROTOTYPE.html` for layout benchmarks and UX patterns.

Start by setting up the project structure, theme tokens, common layout elements, and domain components for `{primary_plural}` and `{secondary_plural}`.
"""

    # --- BACKEND SPECIFICATIONS ---
    be_agents_md = f"""# BACKEND AI AGENT BOUNDARIES & ARCHITECTURAL DIRECTIVES

## Project: {title} (Backend Services)
**Domain:** Server Architecture, Persistence Layer & Business Rule Processing
**Target Tech Stack:** {stack}

### 1. Architectural Boundaries & Server Directives
* **Strict Server Bounded Context:** All code under `backend/` must implement domain business rules, relational data modeling, security, validation, and REST API endpoints for **{title}**.
* **Layered Architecture:**
  - **Transport Layer (Controllers / Views / Routers):** Thin entrypoints responsible solely for HTTP parameter parsing, auth check, and response serialization.
  - **Service Layer (Domain Logic):** Encapsulated business rules, workflow transitions, calculation engines, and transactional workflows (`services/{primary_entity.lower()}Service`).
  - **Data Access Layer (ORM Models & Repositories):** Schema definitions, migrations, relational integrity, queries, and indexing.
* **Security & Auth:** Enforce JWT token verification, Role-Based Access Control (RBAC), SQL injection prevention via ORM parameterization, and CORS whitelisting.
* **Database Transactions:** All multi-step write operations must execute within atomic database transactions (`transaction.atomic()` or DB transaction blocks).

### 2. Backend Engineering Conventions
| Rule | Convention | Example |
| :--- | :--- | :--- |
| Model Entities | Singular PascalCase | `{primary_entity}`, `{secondary_entity}`, `User` |
| Table Names | Plural snake_case | `{primary_plural}`, `{secondary_plural}`, `users` |
| Controllers / Views | Resource noun + Controller/ViewSet | `{primary_entity}ViewSet`, `{primary_entity}Controller` |
| REST API Routes | Lowercase plural resource URLs | `/api/v1/{primary_plural}/` |
"""

    be_architecture_md = f"""# BACKEND ARCHITECTURE SPECIFICATION: {title}

## 1. Directory Structure & System Topology
The backend is structured as a resilient, decoupled service layer built with **{stack}**.

```
backend/
├── app/ or src/
│   ├── config/                  # Settings, database connection, JWT configuration
│   ├── controllers/ or views/   # {primary_entity.lower()}Controller.js / views.py
│   ├── services/                # {primary_entity.lower()}Service.js, analyticsService.js
│   ├── models/                  # {primary_entity}.js / models.py, {secondary_entity}.js
│   ├── serializers/ or dtos/    # Request/Response validation schemas
│   ├── middleware/              # AuthMiddleware, ErrorHandler, RateLimiter
│   └── routes/ or urls.py       # API route definitions
├── migrations/                  # Database migration scripts
├── seeds/                       # Development database seed scripts
├── .env.example
└── server.js / manage.py
```

## 2. Core Relational Data Schema
* **{primary_entity}:**
  - `id`: Unique identifier (Primary Key, e.g. `{prefix}-101`)
  - `title`: Primary entity name or identifier
  - `category`: Functional categorization or workflow stage
  - `status`: Lifecycle state (`Pending`, `In Progress`, `Completed`, `Archived`)
  - `priority`: Urgency level (`Low`, `Medium`, `High`, `Critical`)
  - `metadata`: JSON payload for domain attributes
  - `created_at`: Creation timestamp with index
  - `updated_at`: Modification timestamp

* **{secondary_entity}:**
  - `id`: Unique identifier (Primary Key)
  - `{primary_entity.lower()}_id`: Foreign Key referencing `{primary_entity}.id` (ON DELETE CASCADE)
  - `name`: Sub-item name or attribute description
  - `value`: Numerical or text attribute
  - `status`: Child item status

## 3. Extracted Domain Rules
{chr(10).join(f'* {feat}' for feat in features[:15])}
"""

    be_setup_md = f"""# BACKEND SETUP & RUN PLAYBOOK: {title}

## Prerequisites
- Node.js 18+ or Python 3.11+
- Database: PostgreSQL or SQLite
- Package manager: `npm` or `pip`

## Quickstart Sequence

### 1. Navigate to Backend Directory
```bash
cd backend
```

### 2. Configure Environment Variables
Create `.env`:
```env
PORT=8000
DATABASE_URL=postgres://user:password@localhost:5432/{title.lower().replace(' ', '_')}
JWT_SECRET=super_secret_jwt_key_change_in_production
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 3. Install Dependencies
```bash
# For Node.js:
npm install

# For Python/Django/FastAPI:
python -m venv .venv
source .venv/bin/activate  # or .\\.venv\\Scripts\\activate on Windows
pip install -r requirements.txt
```

### 4. Execute Migrations & Seed Database
```bash
npm run db:migrate && npm run db:seed
# Or for Django:
python manage.py migrate
python manage.py loaddata initial_seeds.json
```

### 5. Launch Backend Server
```bash
npm run dev
# Or for Django:
python manage.py runserver 0.0.0.0:8000
```
API endpoint is now live at `http://localhost:8000/api/v1/`.
"""

    be_skill_md = f"""# BACKEND AGENT CAPABILITY SPECIFICATION (SKILLS.md)

## Skill 1: {primary_entity} Lifecycle & Integrity Auditor
```bash
npm run skill:audit-{primary_plural} -- --verify-integrity
```
Audits database consistency, orphaned records, and lifecycle transitions across `{primary_plural}`.

## Skill 2: Schema Migration & Sanity Verifier
```bash
npm run skill:verify-schema
```
Checks for pending database migrations, missing table indexes, and foreign key constraints.

## Skill 3: Synthetic Seed & Stress Test Generator
```bash
npm run skill:seed-stress -- --volume=1000
```
Populates high-volume mock database records to benchmark query latency and index efficiency.
"""

    be_api_setup_md = f"""# BACKEND REST API SPECIFICATIONS: {title}

### Base URL: `/api/v1`

### Authentication Header
```http
Authorization: Bearer <jwt_access_token>
```

### Endpoint Registry & Contracts
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
{endpoints_rows}

### Standard Error Response Format (RFC 7807)
```json
{{
  "error": {{
    "code": "VALIDATION_FAILED",
    "message": "Invalid field value provided.",
    "details": [
      {{ "field": "title", "issue": "Title cannot be empty." }}
    ]
  }}
}}
```
"""

    be_initial_prompt = f"""# BACKEND CODING AGENT KICKOFF INSTRUCTIONS

You are the Lead Backend & Systems Architect for **{title}**.
Your task is to build out the server, relational database schemas, business logic service layer, and REST API endpoints using **{stack}**.

### Execution Directives:
1. Review `backend/AGENT.md` for architectural boundaries, service layer decoupling, and validation rules.
2. Review `backend/ARCHITECTURE.md` for relational entities (`{primary_entity}`, `{secondary_entity}`) and directory structure.
3. Review `backend/SETUP.md` for database migration scripts and environment setup.
4. Review `backend/API_SETUP.md` for REST API endpoint signatures and status codes.

Start by defining the database schemas and migrations, configuring database connections, implementing the domain service layer, and registering the API route controllers.
"""

    return {
        "detected_tech_stack": stack,
        "frontend": {
            "agents_md": fe_agents_md,
            "architecture_md": fe_architecture_md,
            "setup_md": fe_setup_md,
            "skill_md": fe_skill_md,
            "api_setup_md": fe_api_setup_md,
            "initial_prompt": fe_initial_prompt,
        },
        "backend": {
            "agents_md": be_agents_md,
            "architecture_md": be_architecture_md,
            "setup_md": be_setup_md,
            "skill_md": be_skill_md,
            "api_setup_md": be_api_setup_md,
            "initial_prompt": be_initial_prompt,
        },
        "frontend_agents_md": fe_agents_md,
        "frontend_architecture_md": fe_architecture_md,
        "frontend_setup_md": fe_setup_md,
        "frontend_skill_md": fe_skill_md,
        "frontend_api_setup_md": fe_api_setup_md,
        "frontend_initial_prompt": fe_initial_prompt,
        "backend_agents_md": be_agents_md,
        "backend_architecture_md": be_architecture_md,
        "backend_setup_md": be_setup_md,
        "backend_skill_md": be_skill_md,
        "backend_api_setup_md": be_api_setup_md,
        "backend_initial_prompt": be_initial_prompt,
        "agents_md": fe_agents_md,
        "architecture_md": fe_architecture_md,
        "setup_md": fe_setup_md,
        "skill_md": fe_skill_md,
        "api_setup_md": fe_api_setup_md,
        "initial_prompt": fe_initial_prompt,
    }


def generate_fallback_specifications(scaffold, blueprint=None) -> dict:
    """Wrapper delegating directly to dynamic scope-driven specification generator."""
    return generate_dynamic_specifications(scaffold, blueprint)


def generate_project_scaffold(scaffold):
    """Analyze scope, extract tech stack, generate unique .md specs and dynamic UI prototype."""
    scaffold.status = ScaffoldStatus.PROCESSING.value
    scaffold.error = ""
    scaffold.save(update_fields=["status", "error"])

    try:
        raw_scope = scaffold.scope_document or ""
        doc_title, clean_scope = extract_clean_text_from_pdf_stream(raw_scope)
        if clean_scope and clean_scope != raw_scope:
            scaffold.scope_document = clean_scope

        # Step 1: Deep Scope & Tech Stack Analysis
        analysis = analyze_scope_and_tech_stack(
            scaffold.scope_document or "",
            custom_title=scaffold.title or "",
            custom_tech_stack=scaffold.custom_tech_stack or "",
            custom_notes=scaffold.custom_notes or ""
        )

        update_fields = []
        if analysis["title"] and (not scaffold.title or scaffold.title in ["School Accessories Mart", "PulseDesk Issue Tracker", "Project Workspace"]):
            scaffold.title = analysis["title"]
            update_fields.append("title")
        if clean_scope and clean_scope != raw_scope:
            update_fields.append("scope_document")
        if update_fields:
            scaffold.save(update_fields=update_fields)
        raw_scope = scaffold.scope_document or ""
        doc_title, clean_scope = extract_clean_text_from_pdf_stream(raw_scope)
        update_fields = []
        if doc_title and (not scaffold.title or scaffold.title in ["School Accessories Mart", "PulseDesk Issue Tracker", "Project Workspace"]):
            scaffold.title = doc_title
            update_fields.append("title")
        if clean_scope and clean_scope != raw_scope:
            scaffold.scope_document = clean_scope
            update_fields.append("scope_document")
        if update_fields:
            scaffold.save(update_fields=update_fields)

        system_prompt = SCAFFOLD_PROMPT_FILE.read_text(encoding="utf-8")
        target_stack = scaffold.custom_tech_stack or analysis.get("tech_stack") or "Modern Full-Stack"

        user_content = f"""
PROJECT TITLE: {scaffold.title}
{f'PROJECT DESCRIPTION: {scaffold.description}' if scaffold.description else ''}

PROJECT SCOPE DOCUMENT:
{scaffold.scope_document}

TARGET TECHNOLOGY STACK (MUST be strictly adopted and implemented across all specifications):
{target_stack}

{f'''ADDITIONAL VIP CONSTRAINTS & SPECIFIC DIRECTIVES:
{scaffold.custom_notes}''' if scaffold.custom_notes and scaffold.custom_notes.strip() else ''}

Based purely on this project scope, target tech stack, and any user directives above, dynamically ideate the full architecture, directory structure, module boundaries, coding guidelines, API contracts, and setup scripts following the exact 6-key standard format in the system prompt. Generate the complete JSON specification now.
"""

        try:
            data = call_ai_structured(system_prompt, user_content)
        except Exception as ai_exc:
            logger.warning("AI model call failed or quota exhausted: %s. Using high-fidelity domain fallback spec generator.", ai_exc)
            data = generate_dynamic_specifications(scaffold, blueprint=None, analysis=analysis)

        fe = data.get("frontend") if isinstance(data.get("frontend"), dict) else {}
        be = data.get("backend") if isinstance(data.get("backend"), dict) else {}

        # Default fallback specifications for frontend and backend if any section missing
        fallback_specs = None

        def get_fallback():
            nonlocal fallback_specs
            if fallback_specs is None:
                fallback_specs = generate_dynamic_specifications(scaffold, blueprint=None, analysis=analysis)
            return fallback_specs

        # Frontend specifications
        fe_agents = fe.get("agents_md") or data.get("frontend_agents_md") or data.get("agents_md") or ""
        fe_arch = fe.get("architecture_md") or data.get("frontend_architecture_md") or data.get("architecture_md") or ""
        fe_setup = fe.get("setup_md") or data.get("frontend_setup_md") or data.get("setup_md") or ""
        fe_skill = fe.get("skill_md") or data.get("frontend_skill_md") or data.get("skill_md") or ""
        fe_api = fe.get("api_setup_md") or data.get("frontend_api_setup_md") or data.get("api_setup_md") or ""
        fe_prompt = fe.get("initial_prompt") or data.get("frontend_initial_prompt") or data.get("initial_prompt") or ""

        # Backend specifications
        be_agents = be.get("agents_md") or data.get("backend_agents_md") or ""
        be_arch = be.get("architecture_md") or data.get("backend_architecture_md") or ""
        be_setup = be.get("setup_md") or data.get("backend_setup_md") or ""
        be_skill = be.get("skill_md") or data.get("backend_skill_md") or ""
        be_api = be.get("api_setup_md") or data.get("backend_api_setup_md") or ""
        be_prompt = be.get("initial_prompt") or data.get("backend_initial_prompt") or ""

        # If backend missing, fill from fallback
        if not be_agents or not be_arch:
            fb = get_fallback()
            be_agents = be_agents or fb["backend"]["agents_md"]
            be_arch = be_arch or fb["backend"]["architecture_md"]
            be_setup = be_setup or fb["backend"]["setup_md"]
            be_skill = be_skill or fb["backend"]["skill_md"]
            be_api = be_api or fb["backend"]["api_setup_md"]
            be_prompt = be_prompt or fb["backend"]["initial_prompt"]

        if not fe_agents or not fe_arch:
            fb = get_fallback()
            fe_agents = fe_agents or fb["frontend"]["agents_md"]
            fe_arch = fe_arch or fb["frontend"]["architecture_md"]
            fe_setup = fe_setup or fb["frontend"]["setup_md"]
            fe_skill = fe_skill or fb["frontend"]["skill_md"]
            fe_api = fe_api or fb["frontend"]["api_setup_md"]
            fe_prompt = fe_prompt or fb["frontend"]["initial_prompt"]

        scaffold.detected_tech_stack = data.get("detected_tech_stack", target_stack)

        scaffold.frontend_agents_md = fe_agents
        scaffold.frontend_architecture_md = fe_arch
        scaffold.frontend_setup_md = fe_setup
        scaffold.frontend_skill_md = fe_skill
        scaffold.frontend_api_setup_md = fe_api
        scaffold.frontend_initial_prompt = fe_prompt

        scaffold.backend_agents_md = be_agents
        scaffold.backend_architecture_md = be_arch
        scaffold.backend_setup_md = be_setup
        scaffold.backend_skill_md = be_skill
        scaffold.backend_api_setup_md = be_api
        scaffold.backend_initial_prompt = be_prompt

        # Backwards compatible root fields
        scaffold.agents_md = fe_agents
        scaffold.architecture_md = fe_arch
        scaffold.setup_md = fe_setup
        scaffold.skill_md = fe_skill
        scaffold.api_setup_md = fe_api
        scaffold.initial_prompt = fe_prompt

        scaffold.status = ScaffoldStatus.COMPLETED.value
        scaffold.save(update_fields=[
            "detected_tech_stack",
            "frontend_agents_md", "frontend_architecture_md", "frontend_setup_md",
            "frontend_skill_md", "frontend_api_setup_md", "frontend_initial_prompt",
            "backend_agents_md", "backend_architecture_md", "backend_setup_md",
            "backend_skill_md", "backend_api_setup_md", "backend_initial_prompt",
            "agents_md", "architecture_md", "setup_md", "skill_md", "api_setup_md", "initial_prompt",
            "status"
        ])

        # Automatically synthesize custom UI prototype for this specific project
        try:
            generate_ui_prototype(scaffold)
        except Exception as ui_exc:
            logger.warning("Auto UI prototype generation fallback triggered: %s", ui_exc)
            scaffold.ui_prototype_html = synthesize_dynamic_ui_prototype(scaffold, analysis)
            scaffold.save(update_fields=["ui_prototype_html"])

        return scaffold
    except Exception as exc:
        logger.exception("Scaffold generation failed for project %s", scaffold.id)
        scaffold.status = ScaffoldStatus.FAILED.value
        scaffold.error = str(exc)
        scaffold.save(update_fields=["status", "error"])
        raise




def synthesize_dynamic_ui_prototype(scaffold: ProjectScaffold, analysis: dict = None) -> str:
    """
    Synthesize an interactive single-file HTML/Tailwind/JS prototype derived directly from
    the project scope and generated specifications. Zero canned templates.
    """
    if not analysis:
        analysis = analyze_scope_and_tech_stack(
            scaffold.scope_document or "",
            custom_title=scaffold.title or "",
            custom_tech_stack=scaffold.custom_tech_stack or "",
            custom_notes=scaffold.custom_notes or ""
        )

    title = analysis["title"]
    stack = scaffold.detected_tech_stack or scaffold.custom_tech_stack or analysis["tech_stack"]
    primary_entity = analysis["primary_entity"]
    primary_plural = analysis["primary_plural"]
    features = analysis["features"]
    prefix = analysis["prefix"]

    # Tech stack chips
    raw_stack_tags = [t.strip() for t in stack.replace('+', ',').split(',') if t.strip()]
    chips_html = "".join([f'<span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-code font-medium whitespace-nowrap">{tag}</span>' for tag in raw_stack_tags[:4]])
    if len(raw_stack_tags) > 4:
        chips_html += f'<span class="text-[10px] text-slate-400 font-code whitespace-nowrap">+{len(raw_stack_tags) - 4} more</span>'

    # Build initial mock records matching scope features
    records_js = []
    categories = ["Core Module", "Data Pipeline", "User Interface", "Security & Auth", "Operations"]
    for idx, feat in enumerate(features[:6], start=101):
        cat = categories[idx % len(categories)]
        prio = "High" if idx % 2 == 0 else "Normal"
        status = "Active" if idx == 101 else ("In Progress" if idx % 2 == 1 else "Completed")
        clean_feat = feat.replace("'", "").replace('"', '')
        records_js.append(f"""{{ id: '{prefix}-{idx}', title: '{clean_feat}', category: '{cat}', priority: '{prio}', status: '{status}', timestamp: 'Today, {idx-90}:00' }}""")
    records_str = ",\n      ".join(records_js)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Production Application Prototype</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    .font-code {{ font-family: 'JetBrains Mono', monospace; }}
    html, body {{ max-width: 100vw; overflow-x: hidden; }}
  </style>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen flex flex-col antialiased selection:bg-slate-900 selection:text-white">

  <!-- Production Navigation Header -->
  <header class="bg-white border-b border-slate-200/90 px-4 sm:px-8 py-3 sticky top-0 z-40 shadow-2xs">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
      <div class="flex items-center space-x-3.5 min-w-0">
        <div class="w-9 h-9 rounded-lg bg-slate-950 text-white font-bold flex items-center justify-center text-sm font-code shrink-0 shadow-sm">
          {prefix[:2]}
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h1 class="text-sm sm:text-base font-bold text-slate-950 leading-tight tracking-tight">
              {title}
            </h1>
            <span class="text-[10px] font-code bg-blue-50 text-blue-700 border border-blue-200/80 px-2 py-0.5 rounded-full font-semibold">Production Prototype</span>
          </div>
          <p class="text-[11px] text-slate-500 truncate">Autonomous Multi-Module System</p>
        </div>
      </div>

      <!-- Navigation Tabs for Ideated Pages -->
      <nav class="flex items-center space-x-1 sm:space-x-1.5 overflow-x-auto py-0.5 font-code text-xs">
        <button id="nav-overview" onclick="switchPage('overview')" class="nav-tab px-3 py-1.5 rounded-md font-semibold bg-slate-900 text-white transition">Overview</button>
        <button id="nav-workspace" onclick="switchPage('workspace')" class="nav-tab px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition">Workspace</button>
        <button id="nav-pipeline" onclick="switchPage('pipeline')" class="nav-tab px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition">Pipeline</button>
        <button id="nav-analytics" onclick="switchPage('analytics')" class="nav-tab px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition">Analytics</button>
        <button id="nav-settings" onclick="switchPage('settings')" class="nav-tab px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition">Settings</button>
      </nav>

      <!-- Quick Action CTA & User Profile -->
      <div class="flex items-center space-x-3 shrink-0 self-end md:self-auto">
        <button onclick="openModal()" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-md shadow-xs transition flex items-center gap-1.5 font-code cursor-pointer">
          <span>+</span> <span>New {primary_entity}</span>
        </button>
        <div class="w-8 h-8 rounded-full bg-slate-200 border border-slate-300 flex items-center justify-center text-xs font-code font-bold text-slate-700">
          U
        </div>
      </div>
    </div>
  </header>

  <!-- Main Viewports Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">

    <!-- PAGE 1: OVERVIEW DASHBOARD -->
    <section id="page-overview" class="page-view space-y-6">
      <!-- 4 Core Metric KPI Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs hover:border-slate-300 transition">
          <div class="flex items-center justify-between text-[11px] font-code text-slate-500 font-semibold uppercase">
            <span>Total {primary_plural}</span>
            <span class="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px]">+14%</span>
          </div>
          <div class="text-2xl sm:text-3xl font-bold text-slate-950 mt-2 font-code" id="statTotal">6</div>
          <p class="text-xs text-slate-500 mt-1">Across all domain workflows</p>
        </div>

        <div class="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs hover:border-slate-300 transition">
          <div class="flex items-center justify-between text-[11px] font-code text-slate-500 font-semibold uppercase">
            <span>Active Pipeline</span>
            <span class="text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded text-[10px]">Live</span>
          </div>
          <div class="text-2xl sm:text-3xl font-bold text-blue-600 mt-2 font-code" id="statInProgress">3</div>
          <p class="text-xs text-slate-500 mt-1">Current processing queue</p>
        </div>

        <div class="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs hover:border-slate-300 transition">
          <div class="flex items-center justify-between text-[11px] font-code text-slate-500 font-semibold uppercase">
            <span>Completed &amp; Verified</span>
            <span class="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px]">Validated</span>
          </div>
          <div class="text-2xl sm:text-3xl font-bold text-emerald-600 mt-2 font-code" id="statCompleted">2</div>
          <p class="text-xs text-slate-500 mt-1">100% specification pass rate</p>
        </div>

        <div class="bg-white border border-slate-200/90 rounded-xl p-5 shadow-xs hover:border-slate-300 transition">
          <div class="flex items-center justify-between text-[11px] font-code text-slate-500 font-semibold uppercase">
            <span>Service Uptime</span>
            <span class="text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded text-[10px]">Stable</span>
          </div>
          <div class="text-2xl sm:text-3xl font-bold text-slate-950 mt-2 font-code">99.9%</div>
          <p class="text-xs text-slate-500 mt-1">API contracts synchronized</p>
        </div>
      </div>

      <!-- Quick Operations & Recent Activity Banner -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-white border border-slate-200/90 rounded-xl p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-sm font-bold text-slate-950 uppercase font-code tracking-wider">Quick Domain Actions</h2>
              <span class="text-xs text-slate-400 font-code">Ready to Execute</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button onclick="switchPage('workspace')" class="p-4 rounded-lg border border-slate-200 hover:border-blue-500 hover:bg-blue-50/40 text-left transition group cursor-pointer">
                <span class="text-xs font-bold text-slate-900 group-hover:text-blue-600 block">Browse {primary_plural}</span>
                <span class="text-[11px] text-slate-500 mt-1 block">Inspect full directory &amp; filter tags</span>
              </button>
              <button onclick="openModal()" class="p-4 rounded-lg border border-slate-200 hover:border-blue-500 hover:bg-blue-50/40 text-left transition group cursor-pointer">
                <span class="text-xs font-bold text-slate-900 group-hover:text-blue-600 block">Create {primary_entity}</span>
                <span class="text-[11px] text-slate-500 mt-1 block">Spawn new item with full metadata</span>
              </button>
              <button onclick="switchPage('analytics')" class="p-4 rounded-lg border border-slate-200 hover:border-blue-500 hover:bg-blue-50/40 text-left transition group cursor-pointer">
                <span class="text-xs font-bold text-slate-900 group-hover:text-blue-600 block">Performance Audit</span>
                <span class="text-[11px] text-slate-500 mt-1 block">View system KPIs &amp; throughput</span>
              </button>
            </div>
          </div>
          <div class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-code">
            <span>Domain Scope: <strong class="text-slate-800">{primary_entity} Management</strong></span>
            <span class="text-emerald-600 font-semibold">● Active State Engine</span>
          </div>
        </div>

        <div class="bg-white border border-slate-200/90 rounded-xl p-6 shadow-xs flex flex-col">
          <h2 class="text-sm font-bold text-slate-950 uppercase font-code tracking-wider mb-4">Recent Audit Stream</h2>
          <div class="space-y-3.5 flex-1">
            <div class="flex items-start gap-3 text-xs">
              <span class="w-2 h-2 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
              <div>
                <span class="font-medium text-slate-800 block">Domain workspace initialized</span>
                <span class="text-[10px] text-slate-400 font-code">Just now • Automated</span>
              </div>
            </div>
            <div class="flex items-start gap-3 text-xs">
              <span class="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 shrink-0"></span>
              <div>
                <span class="font-medium text-slate-800 block">Core modules validated against specs</span>
                <span class="text-[10px] text-slate-400 font-code">4 mins ago • System</span>
              </div>
            </div>
            <div class="flex items-start gap-3 text-xs">
              <span class="w-2 h-2 rounded-full bg-slate-400 mt-1.5 shrink-0"></span>
              <div>
                <span class="font-medium text-slate-800 block">State machine listeners active</span>
                <span class="text-[10px] text-slate-400 font-code">10 mins ago • Background</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- PAGE 2: WORKSPACE & DIRECTORY -->
    <section id="page-workspace" class="page-view hidden space-y-6">
      <div class="bg-white border border-slate-200/90 rounded-xl shadow-xs overflow-hidden">
        <!-- Toolbar -->
        <div class="p-4 sm:p-5 border-b border-slate-200 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 whitespace-nowrap scrollbar-none font-code">
            <button onclick="filterRecords('All')" class="tab-btn px-3 py-1.5 text-xs font-semibold rounded-md bg-slate-900 text-white shrink-0">All {primary_plural}</button>
            <button onclick="filterRecords('Active')" class="tab-btn px-3 py-1.5 text-xs font-semibold rounded-md text-slate-600 hover:bg-slate-100 shrink-0">Active</button>
            <button onclick="filterRecords('In Progress')" class="tab-btn px-3 py-1.5 text-xs font-semibold rounded-md text-slate-600 hover:bg-slate-100 shrink-0">In Progress</button>
            <button onclick="filterRecords('Completed')" class="tab-btn px-3 py-1.5 text-xs font-semibold rounded-md text-slate-600 hover:bg-slate-100 shrink-0">Completed</button>
          </div>
          <div class="w-full md:w-72 shrink-0">
            <input type="text" id="searchInput" oninput="handleSearch(this.value)" placeholder="Search {primary_plural}..." class="w-full text-xs font-code border border-slate-300 rounded-lg px-3.5 py-2 focus:ring-1 focus:ring-slate-900 outline-none">
          </div>
        </div>

        <!-- Responsive Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse text-xs min-w-[820px]">
            <thead class="bg-slate-50 font-code text-slate-600 border-b border-slate-200 uppercase text-[11px]">
              <tr>
                <th class="p-3.5 whitespace-nowrap w-24">ID</th>
                <th class="p-3.5">{primary_entity} Description</th>
                <th class="p-3.5 whitespace-nowrap">Category</th>
                <th class="p-3.5 whitespace-nowrap">Priority</th>
                <th class="p-3.5 whitespace-nowrap">Lifecycle Status</th>
                <th class="p-3.5 whitespace-nowrap">Timestamp</th>
                <th class="p-3.5 text-right whitespace-nowrap w-44">Actions</th>
              </tr>
            </thead>
            <tbody id="recordList" class="divide-y divide-slate-100 font-sans">
              <!-- Populated via script -->
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- PAGE 3: PIPELINE WORKFLOW (KANBAN) -->
    <section id="page-pipeline" class="page-view hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm sm:text-base font-bold text-slate-950 font-code uppercase">Operational Workflow Pipeline</h2>
          <p class="text-xs text-slate-500">Live lifecycle status across all ideated stages</p>
        </div>
        <button onclick="openModal()" class="px-3 py-1.5 bg-slate-900 text-white rounded-md text-xs font-code font-semibold">+ Add Task</button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <!-- Stage 1 -->
        <div class="bg-slate-100/70 border border-slate-200/90 rounded-xl p-4 flex flex-col gap-3">
          <div class="flex items-center justify-between pb-2 border-b border-slate-200">
            <span class="text-xs font-bold text-slate-900 font-code uppercase">Active Queue</span>
            <span id="kanbanActiveCount" class="text-xs font-code font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">1</span>
          </div>
          <div id="kanbanActiveCol" class="space-y-3 flex-1"></div>
        </div>

        <!-- Stage 2 -->
        <div class="bg-slate-100/70 border border-slate-200/90 rounded-xl p-4 flex flex-col gap-3">
          <div class="flex items-center justify-between pb-2 border-b border-slate-200">
            <span class="text-xs font-bold text-slate-900 font-code uppercase">In Progress</span>
            <span id="kanbanProgressCount" class="text-xs font-code font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">3</span>
          </div>
          <div id="kanbanProgressCol" class="space-y-3 flex-1"></div>
        </div>

        <!-- Stage 3 -->
        <div class="bg-slate-100/70 border border-slate-200/90 rounded-xl p-4 flex flex-col gap-3">
          <div class="flex items-center justify-between pb-2 border-b border-slate-200">
            <span class="text-xs font-bold text-slate-900 font-code uppercase">Completed &amp; Validated</span>
            <span id="kanbanCompletedCount" class="text-xs font-code font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">2</span>
          </div>
          <div id="kanbanCompletedCol" class="space-y-3 flex-1"></div>
        </div>
      </div>
    </section>

    <!-- PAGE 4: ANALYTICS & PERFORMANCE -->
    <section id="page-analytics" class="page-view hidden space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white border border-slate-200/90 rounded-xl p-6 shadow-xs space-y-4">
          <h3 class="text-sm font-bold text-slate-950 uppercase font-code">System Health &amp; SLA Compliance</h3>
          <div class="space-y-3 font-code text-xs">
            <div>
              <div class="flex justify-between mb-1">
                <span>API Latency (p95)</span>
                <span class="font-bold text-emerald-600">42ms • Optimal</span>
              </div>
              <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div class="bg-emerald-500 h-full w-[25%]"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span>Data Model Integrity</span>
                <span class="font-bold text-blue-600">100% Pass</span>
              </div>
              <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div class="bg-blue-600 h-full w-[100%]"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span>Stateless JWT Session Validity</span>
                <span class="font-bold text-slate-800">12h Lifetime</span>
              </div>
              <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div class="bg-slate-900 h-full w-[80%]"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white border border-slate-200/90 rounded-xl p-6 shadow-xs space-y-4">
          <h3 class="text-sm font-bold text-slate-950 uppercase font-code">Module Distribution</h3>
          <div class="grid grid-cols-2 gap-3 text-xs font-code">
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <span class="text-slate-400 block text-[10px]">Primary Entity</span>
              <span class="font-bold text-slate-900">{primary_entity}</span>
            </div>
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <span class="text-slate-400 block text-[10px]">Architecture Pattern</span>
              <span class="font-bold text-slate-900">Thin View / Fat Service</span>
            </div>
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <span class="text-slate-400 block text-[10px]">Security</span>
              <span class="font-bold text-slate-900">Role-Based Access (RBAC)</span>
            </div>
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <span class="text-slate-400 block text-[10px]">Interface Standard</span>
              <span class="font-bold text-slate-900">Responsive Modern UI</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- PAGE 5: SETTINGS -->
    <section id="page-settings" class="page-view hidden space-y-6">
      <div class="bg-white border border-slate-200/90 rounded-xl p-6 shadow-xs max-w-2xl space-y-5">
        <h2 class="text-sm font-bold text-slate-950 uppercase font-code">Application Preferences &amp; Config</h2>
        <div class="space-y-4 text-xs">
          <div class="flex items-center justify-between p-3.5 bg-slate-50 rounded-lg border border-slate-200">
            <div>
              <span class="font-bold text-slate-900 block">Strict Specification Compliance</span>
              <span class="text-slate-500 text-[11px]">Enforces deterministic API schemas defined in API_SETUP.md</span>
            </div>
            <input type="checkbox" checked class="rounded border-slate-300 text-blue-600 focus:ring-0">
          </div>
          <div class="flex items-center justify-between p-3.5 bg-slate-50 rounded-lg border border-slate-200">
            <div>
              <span class="font-bold text-slate-900 block">Real-time State Synchronization</span>
              <span class="text-slate-500 text-[11px]">Instantly updates record statuses across all client views</span>
            </div>
            <input type="checkbox" checked class="rounded border-slate-300 text-blue-600 focus:ring-0">
          </div>
          <div class="flex items-center justify-between p-3.5 bg-slate-50 rounded-lg border border-slate-200">
            <div>
              <span class="font-bold text-slate-900 block">Audit Log Persistence</span>
              <span class="text-slate-500 text-[11px]">Log user actions and state transitions with timestamps</span>
            </div>
            <input type="checkbox" checked class="rounded border-slate-300 text-blue-600 focus:ring-0">
          </div>
        </div>
        <button onclick="showToast('Preferences updated successfully')" class="px-4 py-2 bg-slate-900 text-white rounded-md text-xs font-code font-semibold">Save Configuration</button>
      </div>
    </section>

  </main>

  <!-- Interactive Modal: Create / Add Record -->
  <div id="recordModal" class="hidden fixed inset-0 z-50 bg-slate-950/40 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white border border-slate-200 rounded-xl shadow-xl w-full max-w-md p-6 flex flex-col gap-4">
      <div class="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 class="text-sm font-bold text-slate-950 font-code">Create New {primary_entity}</h3>
        <button onclick="closeModal()" class="text-slate-400 hover:text-slate-600 text-xl leading-none">&times;</button>
      </div>
      <form id="recordForm" onsubmit="handleCreateRecord(event)" class="space-y-4 text-xs">
        <div>
          <label class="block font-semibold text-slate-700 mb-1.5">{primary_entity} Title / Name</label>
          <input type="text" id="formTitle" required placeholder="Enter description..." class="w-full border border-slate-300 rounded-lg px-3.5 py-2 focus:ring-1 focus:ring-slate-900 outline-none">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-semibold text-slate-700 mb-1.5">Category</label>
            <select id="formCategory" class="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-1 focus:ring-slate-900 outline-none font-code">
              <option value="Core Module">Core Module</option>
              <option value="Data Pipeline">Data Pipeline</option>
              <option value="User Interface">User Interface</option>
              <option value="Security & Auth">Security &amp; Auth</option>
              <option value="Operations">Operations</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1.5">Priority</label>
            <select id="formPriority" class="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-1 focus:ring-slate-900 outline-none font-code">
              <option value="Normal">Normal</option>
              <option value="High">High</option>
              <option value="Urgent">Urgent</option>
            </select>
          </div>
        </div>
        <div class="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
          <button type="button" onclick="closeModal()" class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg font-code">Cancel</button>
          <button type="submit" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg font-code shadow-xs">
            Save {primary_entity}
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Slide-out Detail Inspector Drawer -->
  <div id="inspectorDrawer" class="hidden fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-white border-l border-slate-200 shadow-2xl p-6 flex flex-col justify-between transition-transform">
    <div>
      <div class="flex items-center justify-between pb-3 border-b border-slate-100">
        <h3 class="text-sm font-bold text-slate-900 font-code" id="drawerId">Item Inspector</h3>
        <button onclick="closeDrawer()" class="text-slate-400 hover:text-slate-600 text-xl leading-none">&times;</button>
      </div>
      <div class="mt-4 space-y-4 text-xs">
        <div>
          <label class="text-[10.5px] font-code text-slate-400 uppercase font-semibold">Title</label>
          <p class="font-bold text-slate-950 mt-0.5 text-sm" id="drawerTitle">-</p>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-[10.5px] font-code text-slate-400 uppercase font-semibold">Category</label>
            <p class="font-medium text-slate-800 mt-0.5 font-code" id="drawerCategory">-</p>
          </div>
          <div>
            <label class="text-[10.5px] font-code text-slate-400 uppercase font-semibold">Priority</label>
            <p class="font-medium text-slate-800 mt-0.5 font-code" id="drawerPriority">-</p>
          </div>
        </div>
        <div>
          <label class="text-[10.5px] font-code text-slate-400 uppercase font-semibold">Current Lifecycle State</label>
          <p class="font-bold text-blue-600 mt-0.5 font-code" id="drawerStatus">-</p>
        </div>
      </div>
    </div>
    <div class="pt-4 border-t border-slate-100 flex gap-2 font-code text-xs">
      <button onclick="toggleActiveItemStatus()" class="flex-1 py-2 bg-slate-900 text-white rounded-lg font-semibold hover:bg-black transition">Cycle Status</button>
      <button onclick="closeDrawer()" class="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition">Close</button>
    </div>
  </div>

  <!-- Toast Notice -->
  <div id="toastNotice" class="fixed bottom-5 right-5 z-50 bg-slate-950 text-white text-xs font-code px-4 py-2.5 rounded-lg shadow-xl transition-all duration-300 translate-y-16 opacity-0 pointer-events-none">
    Notification
  </div>

  <script>
    let records = [
      {records_str}
    ];

    let currentFilter = 'All';
    let activeDrawerItemId = null;

    function switchPage(pageId) {{
      document.querySelectorAll('.page-view').forEach(p => p.classList.add('hidden'));
      document.querySelectorAll('.nav-tab').forEach(b => {{
        b.className = "nav-tab px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition";
      }});

      const activePage = document.getElementById(`page-${{pageId}}`);
      const activeNav = document.getElementById(`nav-${{pageId}}`);
      if (activePage) activePage.classList.remove('hidden');
      if (activeNav) {{
        activeNav.className = "nav-tab px-3 py-1.5 rounded-md font-semibold bg-slate-900 text-white transition";
      }}

      if (pageId === 'pipeline') renderKanban();
      if (pageId === 'workspace') renderRecords();
    }}

    function renderRecords() {{
      const q = (document.getElementById('searchInput')?.value || '').toLowerCase();
      const filtered = records.filter(r => {{
        const matchesFilter = (currentFilter === 'All' || r.status === currentFilter);
        const matchesSearch = r.title.toLowerCase().includes(q) || r.id.toLowerCase().includes(q) || r.category.toLowerCase().includes(q);
        return matchesFilter && matchesSearch;
      }});

      const tbody = document.getElementById('recordList');
      if (!tbody) return;
      if (filtered.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="7" class="p-8 text-center text-slate-400 font-code">No matching records found.</td></tr>';
      }} else {{
        tbody.innerHTML = filtered.map(r => `
          <tr class="hover:bg-slate-50/80 transition cursor-pointer" onclick="openDrawer('${{r.id}}')">
            <td class="p-3.5 font-code font-bold text-slate-700 whitespace-nowrap">${{r.id}}</td>
            <td class="p-3.5 font-medium text-slate-950">${{r.title}}</td>
            <td class="p-3.5 whitespace-nowrap">
              <span class="px-2 py-0.5 rounded text-[10px] font-code bg-slate-100 text-slate-700">${{r.category}}</span>
            </td>
            <td class="p-3.5 whitespace-nowrap">
              <span class="px-2 py-0.5 rounded text-[10px] font-code ${{
                r.priority === 'Urgent' ? 'bg-red-50 text-red-700 border border-red-200 font-semibold' :
                r.priority === 'High' ? 'bg-amber-50 text-amber-700 border border-amber-200 font-semibold' :
                'bg-slate-100 text-slate-600'
              }}">${{r.priority}}</span>
            </td>
            <td class="p-3.5 whitespace-nowrap">
              <span class="px-2.5 py-0.5 rounded text-[10px] font-code font-semibold ${{
                r.status === 'Completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                r.status === 'In Progress' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                'bg-slate-100 text-slate-700'
              }}">${{r.status}}</span>
            </td>
            <td class="p-3.5 text-[10px] text-slate-400 font-code whitespace-nowrap">${{r.timestamp}}</td>
            <td class="p-3.5 text-right whitespace-nowrap" onclick="event.stopPropagation()">
              <div class="flex items-center justify-end gap-1.5">
                <button onclick="toggleRecordStatus('${{r.id}}')" class="px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-[10px] font-code font-semibold text-slate-700 cursor-pointer transition">Cycle</button>
                <button onclick="openDrawer('${{r.id}}')" class="px-2 py-1 bg-blue-50 hover:bg-blue-100 rounded text-[10px] font-code text-blue-700 font-semibold cursor-pointer transition">Inspect</button>
              </div>
            </td>
          </tr>
        `).join('');
      }}

      // Update counters
      const statTotal = document.getElementById('statTotal');
      const statProg = document.getElementById('statInProgress');
      const statComp = document.getElementById('statCompleted');
      if (statTotal) statTotal.textContent = records.length;
      if (statProg) statProg.textContent = records.filter(r => r.status === 'In Progress').length;
      if (statComp) statComp.textContent = records.filter(r => r.status === 'Completed').length;
    }}

    function renderKanban() {{
      const actCol = document.getElementById('kanbanActiveCol');
      const progCol = document.getElementById('kanbanProgressCol');
      const compCol = document.getElementById('kanbanCompletedCol');
      if (!actCol || !progCol || !compCol) return;

      const active = records.filter(r => r.status === 'Active');
      const progress = records.filter(r => r.status === 'In Progress');
      const completed = records.filter(r => r.status === 'Completed');

      document.getElementById('kanbanActiveCount').textContent = active.length;
      document.getElementById('kanbanProgressCount').textContent = progress.length;
      document.getElementById('kanbanCompletedCount').textContent = completed.length;

      const card = (r) => `
        <div onclick="openDrawer('${{r.id}}')" class="bg-white border border-slate-200/90 rounded-lg p-3.5 shadow-2xs hover:shadow-xs transition cursor-pointer space-y-2">
          <div class="flex justify-between items-center text-[10px] font-code text-slate-400">
            <span class="font-bold text-slate-700">${{r.id}}</span>
            <span>${{r.priority}}</span>
          </div>
          <p class="text-xs font-semibold text-slate-900">${{r.title}}</p>
          <div class="flex justify-between items-center pt-1 text-[10px] font-code">
            <span class="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">${{r.category}}</span>
            <button onclick="event.stopPropagation(); toggleRecordStatus('${{r.id}}')" class="text-blue-600 hover:underline">Advance →</button>
          </div>
        </div>
      `;

      actCol.innerHTML = active.map(card).join('') || '<div class="text-center py-6 text-slate-400 text-xs font-code">No active tasks</div>';
      progCol.innerHTML = progress.map(card).join('') || '<div class="text-center py-6 text-slate-400 text-xs font-code">No items in progress</div>';
      compCol.innerHTML = completed.map(card).join('') || '<div class="text-center py-6 text-slate-400 text-xs font-code">No completed items</div>';
    }}

    function toggleRecordStatus(id) {{
      const r = records.find(x => x.id === id);
      if (!r) return;
      if (r.status === 'Active') r.status = 'In Progress';
      else if (r.status === 'In Progress') r.status = 'Completed';
      else r.status = 'Active';
      renderRecords();
      renderKanban();
      showToast(`Updated ${{id}} -> ${{r.status}}`);
      if (activeDrawerItemId === id) openDrawer(id);
    }}

    function filterRecords(status) {{
      currentFilter = status;
      document.querySelectorAll('.tab-btn').forEach(btn => {{
        if (btn.textContent.trim().includes(status)) {{
          btn.className = "tab-btn px-3 py-1.5 text-xs font-semibold rounded-md bg-slate-900 text-white shrink-0";
        }} else {{
          btn.className = "tab-btn px-3 py-1.5 text-xs font-semibold rounded-md text-slate-600 hover:bg-slate-100 shrink-0";
        }}
      }});
      renderRecords();
    }}

    function handleSearch(val) {{ renderRecords(); }}

    function openModal() {{ document.getElementById('recordModal').classList.remove('hidden'); }}
    function closeModal() {{ document.getElementById('recordModal').classList.add('hidden'); }}

    function openDrawer(id) {{
      const r = records.find(x => x.id === id);
      if (!r) return;
      activeDrawerItemId = id;
      document.getElementById('drawerId').textContent = r.id;
      document.getElementById('drawerTitle').textContent = r.title;
      document.getElementById('drawerCategory').textContent = r.category;
      document.getElementById('drawerPriority').textContent = r.priority;
      document.getElementById('drawerStatus').textContent = r.status;
      document.getElementById('inspectorDrawer').classList.remove('hidden');
    }}

    function closeDrawer() {{
      activeDrawerItemId = null;
      document.getElementById('inspectorDrawer').classList.add('hidden');
    }}

    function toggleActiveItemStatus() {{
      if (activeDrawerItemId) toggleRecordStatus(activeDrawerItemId);
    }}

    function handleCreateRecord(e) {{
      e.preventDefault();
      const title = document.getElementById('formTitle').value.trim();
      const cat = document.getElementById('formCategory').value;
      const prio = document.getElementById('formPriority').value;
      const newId = `{prefix}-${{100 + records.length + 1}}`;

      records.unshift({{
        id: newId,
        title: title,
        category: cat,
        priority: prio,
        status: 'Active',
        timestamp: 'Just now'
      }});

      closeModal();
      document.getElementById('recordForm').reset();
      renderRecords();
      renderKanban();
      showToast(`Created new {primary_entity} ${{newId}}`);
    }}

    function showToast(msg) {{
      const toast = document.getElementById('toastNotice');
      if (!toast) return;
      toast.textContent = msg;
      toast.classList.remove('translate-y-16', 'opacity-0');
      setTimeout(() => toast.classList.add('translate-y-16', 'opacity-0'), 2500);
    }}

    renderRecords();
  </script>
</body>
</html>"""


def generate_fallback_ui_prototype(scaffold: ProjectScaffold) -> str:
    """Wrapper delegating directly to dynamic scope-driven UI prototype synthesizer."""
    return synthesize_dynamic_ui_prototype(scaffold)


def generate_ui_prototype(scaffold: ProjectScaffold) -> str:
    """
    Synthesize an interactive single-file HTML/Tailwind/JS prototype using free Gemini Flash.
    Instructs the AI model to ideate the pages and modules directly from the scope document and ARCHITECTURE.md,
    building an authentic multi-page web application with zero internal tech-stack badges.
    """
    system_prompt = """You are an elite Principal Frontend Architect and Staff Product Designer.
Your objective is to design and build a complete, production-ready, interactive single-file HTML prototype for the provided software project scope and specifications.

CRITICAL ARCHITECTURAL DIRECTIVES:
1. DELIVER ONLY CLEAN HTML: Start directly with <!DOCTYPE html> and end with </html>. Do NOT wrap in markdown code fences (no ```html, no ```).
2. DYNAMICALLY IDEATE COMPLETE MULTI-MODULE & MULTI-PAGE APPLICATION ARCHITECTURE:
   - Carefully analyze the project's SCOPE.md, ARCHITECTURE.md, API_SETUP.md, AGENT.md, and SETUP.md to identify all user personas, functional modules, and required pages.
   - MANDATORY: The UI must contain ALL modules and all required pages. If specific pages or views are NOT fully enumerated in the scope document, you MUST proactively ideate the project modules, views, dashboards, workflows, forms, and functionalities based on the available user scope and MD files requirements!
   - Build a traditional, authentic multi-page web application with distinct page views (e.g. Dashboard/Overview, Main Interactive Domain Experience/Catalog/Studio, Operations/Records/Pipeline Directory, Analytics/KPIs, and Settings/Config).
   - Implement seamless client-side page navigation (e.g. `switchPage(pageId)` in vanilla JS) so the user can click through all the ideated pages in the top navigation bar. Every page view container must have its own dedicated section (e.g. `<section id="page-overview">`, `<section id="page-catalog">`, etc.).
3. PRODUCTION-LEVEL PERFECTION IN PADDING, MARGINS, ALIGNMENT & RESPONSIVENESS:
   - Visual Harmony & Spacing Scale: Strictly use disciplined, consistent spacing (e.g. `p-4 sm:p-6 lg:p-8`, `gap-4 sm:gap-6`, card padding `p-5 sm:p-6`, `rounded-xl`, subtle borders `border border-slate-200/80 shadow-xs`).
   - Impeccable Alignment: Clean layout structure with perfect vertical & horizontal alignment, balanced card heights, modern CSS grid layouts (`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5`).
   - Responsive Design: 100% mobile-friendly, tablet-optimized, and desktop-scalable. No awkward line breaks, no clipped elements, and NO horizontal window scrolling (`max-w-full overflow-x-hidden`).
4. AUTHENTIC USER-FACING BRANDING & NAVIGATION:
   - Include a polished application header with the brand name, custom SVG logo, domain tagline badge, navigation links/tabs for switching between the ideated pages, quick action CTA, and user profile chip.
   - NEVER display internal developer tech stack info or badges (such as "Tech Stack: React, Vite, Node.js") in the user-facing header or UI. Real consumer and enterprise applications never leak their internal developer tooling into the client navigation header!
5. DOMAIN-SPECIFIC INTERACTIVE EXPERIENCES (NEVER A GENERIC FLAT TABLE):
   - Design rich UI components tailored directly to the ideated requirements:
     * If commerce/catalog: visual product cards, category filter pills, price tags, and interactive slide-out cart drawer or order modal.
     * If tickets/support/pipeline: interactive Kanban board with draggable/clickable stage progression, priority badges, and detail modal.
     * If records/directory: searchable, filterable list with a slide-out detail inspector drawer on row click.
     * If analytics/metrics: KPI stat cards with trend arrows (+12%), visual progress bars, and activity audit timeline.
6. TAILWIND CSS & AESTHETICS:
   - Use Tailwind CSS CDN (<script src="https://cdn.tailwindcss.com"></script>) with Google Fonts (Plus Jakarta Sans and JetBrains Mono).
   - Use curated color palettes (slate neutrals, vibrant domain accent colors like emerald, indigo, or blue), smooth transitions, and inline SVGs for all icons.
7. PRE-POPULATE REALISTIC DOMAIN MOCK DATA:
   - Populate with at least 6-10 realistic domain items per module directly extracted from the scope document and personas.
"""

    user_content = f"""PROJECT TITLE: {scaffold.title}

PROJECT SCOPE (SCOPE.md):
{scaffold.scope_document}

ARCHITECTURAL SPECIFICATIONS & MODULES (ARCHITECTURE.md):
{scaffold.architecture_md[:4000] if scaffold.architecture_md else ''}

API SPECIFICATIONS (API_SETUP.md):
{scaffold.api_setup_md[:2000] if scaffold.api_setup_md else ''}

AGENT DIRECTIVES & STANDARDS (AGENT.md):
{scaffold.agents_md[:2000] if scaffold.agents_md else ''}

SETUP & ENVIRONMENT (SETUP.md):
{scaffold.setup_md[:1500] if scaffold.setup_md else ''}

Based on this scope and all architectural specifications, ideate all required modules and pages, and synthesize the complete, stunning, fully interactive multi-page HTML web application now with proper padding, margins, alignment, and responsive design. Start directly with <!DOCTYPE html>."""

    raw_html = ""
    client = None
    if getattr(settings, "GEMINI_API_KEY", ""):
        client = OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
        )
    elif getattr(settings, "OPENAI_API_KEY", ""):
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

    if client:
        primary_model = settings.GEMINI_MODEL if getattr(settings, "GEMINI_API_KEY", "") else settings.OPENAI_MODEL
        models_to_try = [primary_model]
        if getattr(settings, "GEMINI_API_KEY", ""):
            for m in ["gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash"]:
                if m not in models_to_try:
                    models_to_try.append(m)

        for model in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.3,
                )
                raw_html = response.choices[0].message.content or ""
                if raw_html and ("<!DOCTYPE" in raw_html or "<html" in raw_html):
                    break
            except Exception as exc:
                logger.warning("UI prototype generation with model %s failed: %s", model, exc)
                continue

    # Clean markdown fences if any
    cleaned_html = raw_html.strip()
    if cleaned_html.startswith("```"):
        lines = cleaned_html.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned_html = "\n".join(lines).strip()

    if not cleaned_html.startswith("<!DOCTYPE") and "<html" not in cleaned_html:
        cleaned_html = generate_fallback_ui_prototype(scaffold)

    scaffold.ui_prototype_html = cleaned_html
    scaffold.save(update_fields=["ui_prototype_html"])
    return cleaned_html


def create_scaffold_zip(scaffold, target: str = "all"):
    """
    Package generated specifications into structured zip file:
    target="all": contains frontend/ and backend/ folders, plus SCOPE.md at root
    target="frontend": contains only frontend specifications + UI_PROTOTYPE.html
    target="backend": contains only backend specifications
    """
    import re as _re

    clean = _re.sub(r"[^a-zA-Z0-9_\-]", "", scaffold.title.lower().replace(" ", "-"))[:30] or "project"
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        if target in ("all", "frontend"):
            fe_prefix = "frontend/" if target == "all" else ""
            zip_file.writestr(f"{fe_prefix}AGENT.md", scaffold.frontend_agents_md or scaffold.agents_md or "# AGENT.md\n")
            zip_file.writestr(f"{fe_prefix}ARCHITECTURE.md", scaffold.frontend_architecture_md or scaffold.architecture_md or "# ARCHITECTURE.md\n")
            zip_file.writestr(f"{fe_prefix}SETUP.md", scaffold.frontend_setup_md or scaffold.setup_md or "# SETUP.md\n")
            zip_file.writestr(f"{fe_prefix}SKILLS.md", scaffold.frontend_skill_md or scaffold.skill_md or "# SKILLS.md\n")
            if scaffold.frontend_api_setup_md or scaffold.api_setup_md:
                zip_file.writestr(f"{fe_prefix}API_SETUP.md", scaffold.frontend_api_setup_md or scaffold.api_setup_md)
            zip_file.writestr(f"{fe_prefix}INITIAL_PROMPT.md", scaffold.frontend_initial_prompt or scaffold.initial_prompt or "# INITIAL_PROMPT.md\n")
            if scaffold.ui_prototype_html:
                zip_file.writestr(f"{fe_prefix}UI_PROTOTYPE.html", scaffold.ui_prototype_html)

        if target in ("all", "backend"):
            be_prefix = "backend/" if target == "all" else ""
            zip_file.writestr(f"{be_prefix}AGENT.md", scaffold.backend_agents_md or "# AGENT.md\n")
            zip_file.writestr(f"{be_prefix}ARCHITECTURE.md", scaffold.backend_architecture_md or "# ARCHITECTURE.md\n")
            zip_file.writestr(f"{be_prefix}SETUP.md", scaffold.backend_setup_md or "# SETUP.md\n")
            zip_file.writestr(f"{be_prefix}SKILLS.md", scaffold.backend_skill_md or "# SKILLS.md\n")
            if scaffold.backend_api_setup_md:
                zip_file.writestr(f"{be_prefix}API_SETUP.md", scaffold.backend_api_setup_md)
            zip_file.writestr(f"{be_prefix}INITIAL_PROMPT.md", scaffold.backend_initial_prompt or "# INITIAL_PROMPT.md\n")

        if target == "all":
            zip_file.writestr("SCOPE.md", scaffold.scope_document or "# SCOPE.md\n")

    buffer.seek(0)
    return buffer

