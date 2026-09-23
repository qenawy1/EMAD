import html
import random
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup


@dataclass
class SearchIntent:
    """نية البحث المنظمة للمستخدم."""
    keywords: List[str]
    location: str
    job_type: str = "all"        # "all", "internship", "full_time", "part_time", "contract"
    workplace_type: str = "all"  # "all", "remote", "hybrid", "onsite"
    date_posted: str = "all"     # "all", "past_24h", "past_week", "past_month"


class JobClassifier:
    """محرك تصنيف وتحليل مسميات الوظائف ومستويات الخبرة ونوع العمل."""

    # كلمات استبعاد فورية للوظائف القيادية والخبرة العالية
    SENIOR_LEAD_PATTERNS = [
        r"\bsenior\b",
        r"\bsr\.?\b",
        r"\bsnr\.?\b",
        r"\blead\b",
        r"\bteam[\s-]lead\b",
        r"\btech[\s-]lead\b",
        r"\barchitect\b",
        r"\bstaff\b",
        r"\bprincipal\b",
        r"\bhead\b",
        r"\bdirector\b",
        r"\bmanager\b",
        r"\bvp\b",
        r"\bchief\b",
        r"\bخبير\b",
        r"\bسينيور\b",
        r"\bمدير\b",
        r"\bرئيس\b",
    ]

    # كلمات التدريب المباشرة
    INTERN_PATTERNS = [
        r"\bintern\b",
        r"\binternship\b",
        r"\bco-?op\b",
        r"\btrainee\b",
        r"\btraining\b",
        r"\bstudent\b",
        r"\bapprentice\b",
        r"\bapprenticeship\b",
        r"\bتدريب\b",
        r"\bمتدرب\b",
    ]

    # كلمات برامج الخريجين
    GRAD_PROGRAM_PATTERNS = [
        r"\bgraduate[\s-]program\b",
        r"\bgraduate[\s-]in[\s-]training\b",
        r"\bgit[\s-]program\b",
        r"\bfresh[\s-]graduate[\s-]program\b",
        r"\bnextgen\b",
        r"\bmentorship[\s-]program\b",
    ]

    # كلمات المبتدئين
    ENTRY_PATTERNS = [
        r"\bjunior\b",
        r"\bjr\.?\b",
        r"\bentry[\s-]level\b",
        r"\bfresh\b",
        r"\bfresh[\s-]grad\b",
        r"\bgraduate\b",
        r"\bمبتدئ\b",
        r"\bحديث[\s-]تخرج\b",
    ]

    # مجالات عمل متعارضة (عند البحث عن أدوار تقنية، استبعد المجالات غير التقنية)
    NON_TECH_DOMAINS = [
        r"\bmarketing\b",
        r"\bmedia[\s-]buying\b",
        r"\baccountant\b",
        r"\baccounting\b",
        r"\baudit\b",
        r"\btax\b",
        r"\brecruiter\b",
        r"\btalent[\s-]acquisition\b",
        r"\bhuman[\s-]resources\b",
        r"\bhr\b",
        r"\bsales\b",
        r"\btelesales\b",
        r"\bcivil\b",
        r"\bpharmacy\b",
        r"\bmedical\b",
        r"\blegal\b",
        r"\bcustomer[\s-]service\b",
        r"\bcall[\s-]center\b",
        r"\blogistics\b",
        r"\bsupply[\s-]chain\b",
        r"\bchef\b",
        r"\bnurse\b",
    ]

    # أنماط سنوات الخبرة الصريحة التي تستبعد وظائف التدريب وتحدد الخبرة الفعلية
    EXPERIENCE_PATTERNS = [
        r"(?<![0-9][\s–\-])\b[1-9]\d*\+?(?:\s*[–\-+to]+\s*[0-9]+)?\s*(?:years?|yrs?|yr|سنوات|سنة)\b",
        r"\b(سنتين|سنة|[1-9]\d*\s*سنوات?)\s*خبرة\b|\bخبرة\s*(سنتين|سنة|[1-9]\d*)\b",
        r"\bexperienced\b",
    ]

    # وسوم ومصطلحات التدريب
    INTERN_MODIFIERS = {
        "intern", "internship", "trainee", "training", "co-op",
        "apprentice", "apprenticeship", "student", "تدريب", "متدرب", "طلبة"
    }

    @classmethod
    def is_experience_required(cls, title: str) -> bool:
        """فحص ما إذا كان العنوان يشترط صراحة سنوات خبرة سابقة (1+ سنة)."""
        title_clean = title.lower()
        return any(re.search(pat, title_clean) for pat in cls.EXPERIENCE_PATTERNS)

    @classmethod
    def normalize_search_intent(
        cls,
        keywords: List[str],
        job_type: str,
    ) -> Tuple[List[str], str]:
        """
        تحليل وتنقية نية البحث من الكلمات المدخلة ونوع الوظيفة.
        - إذا كتب المستخدم 'flutter, intern' أو 'flutter intern' أو 'تدريب flutter':
          يتم استخلاص المسمى الفعلي 'flutter' وتحديد نوع الوظيفة 'internship'.
        - منع البحث العشوائي عن 'intern' بمفردها عندما تكون مصحوبة بمسمى تخصصي.
        """
        has_intern_signal = (job_type == "internship")
        cleaned_keywords: List[str] = []

        for kw in keywords:
            kw_clean = kw.strip()
            tokens = [t.lower() for t in re.split(r"[\s,\-_/]+", kw_clean) if t]
            if not tokens:
                continue

            # هل الكلمة بالكامل مجرد وسم تدريب؟ (مثل intern أو تدريب)
            if all(t in cls.INTERN_MODIFIERS for t in tokens):
                has_intern_signal = True
                continue

            # هل الكلمة مركبة وتحتوي على وسم تدريب وتخصص؟ (مثل flutter intern)
            if any(t in cls.INTERN_MODIFIERS for t in tokens):
                has_intern_signal = True
                clean_tokens = [t for t in tokens if t not in cls.INTERN_MODIFIERS]
                if clean_tokens:
                    cleaned_keywords.append(" ".join(clean_tokens))
                continue

            cleaned_keywords.append(kw_clean)

        if not cleaned_keywords and keywords:
            cleaned_keywords = [k.strip() for k in keywords if k.strip()]

        effective_job_type = "internship" if has_intern_signal else job_type
        return cleaned_keywords, effective_job_type

    @classmethod
    def detect_seniority(cls, title: str) -> str:
        """
        تحديد مستوى الخبرة بدقة من عنوان الوظيفة الفعلي فقط.
        القاعدة: إذا لم يكن هناك دليل صريح، فهو 'غير محدد'.
        """
        title_clean = title.lower()

        # فحص القياديين والسينيور أولاً
        for pat in cls.SENIOR_LEAD_PATTERNS:
            if re.search(pat, title_clean):
                return "خبير / قيادي (Senior/Lead)"

        # فحص اشتراط سنوات الخبرة الصريحة في العنوان
        if cls.is_experience_required(title):
            if re.search(
                r"(?<![0-9][\s–\-])\b[3-9]\d*\+?(?:\s*[–\-+to]+\s*[0-9]+)?\s*(?:years?|yrs?|yr|سنوات)\b",
                title_clean,
            ):
                return "متوسط / خبير (Mid/Senior)"
            return "مبتدئ بخبرة (1-2 Years)"

        # فحص التدريب
        for pat in cls.INTERN_PATTERNS:
            if re.search(pat, title_clean):
                return "تدريب (Intern)"

        # فحص برامج الخريجين
        for pat in cls.GRAD_PROGRAM_PATTERNS:
            if re.search(pat, title_clean):
                return "برنامج خريجين (Graduate/Trainee)"

        # فحص المبتدئ / جونيور
        for pat in cls.ENTRY_PATTERNS:
            if re.search(pat, title_clean):
                return "مبتدئ (Junior/Entry)"

        # فحص المستوى المتوسط الصريح
        if re.search(r"\b(mid[\s-]level|intermediate)\b", title_clean):
            return "متوسط (Mid Level)"

        return "غير محدد"

    @classmethod
    def detect_job_type(cls, title: str) -> str:
        """
        تحديد نوع الوظيفة.
        القاعدة الذهبية: لا تفترض نوع الوظيفة أبداً (لا تفترض Full-time) بدون دليل صريح في العنوان.
        """
        title_clean = title.lower()

        # إذا كانت الوظيفة تشترط سنوات خبرة، فهي ليست تدريباً
        if cls.is_experience_required(title):
            if re.search(r"\b(part[\s-]time|دوام[\s-]جزئي)\b", title_clean):
                return "دوام جزئي (Part-time)"
            if re.search(r"\b(contract|freelance|عقد)\b", title_clean):
                return "عقد / عمل حر (Contract)"
            if re.search(r"\b(full[\s-]time|دوام[\s-]كامل)\b", title_clean):
                return "دوام كامل (Full-time)"
            return "غير محدد"

        for pat in cls.INTERN_PATTERNS:
            if re.search(pat, title_clean):
                return "تدريب (Internship)"

        for pat in cls.GRAD_PROGRAM_PATTERNS:
            if re.search(pat, title_clean):
                return "برنامج خريجين (Graduate Program)"

        if re.search(r"\b(part[\s-]time|دوام[\s-]جزئي)\b", title_clean):
            return "دوام جزئي (Part-time)"

        if re.search(r"\b(contract|freelance|عقد)\b", title_clean):
            return "عقد / عمل حر (Contract)"

        if re.search(r"\b(full[\s-]time|دوام[\s-]كامل)\b", title_clean):
            return "دوام كامل (Full-time)"

        return "غير محدد"

    @classmethod
    def detect_workplace(cls, title: str, location: str) -> str:
        """تحديد بيئة العمل من العنوان ومكان الوظيفة."""
        combined = f"{title} {location}".lower()
        if "remote" in combined or "عن بعد" in combined or "عن بُعد" in combined:
            return "عن بُعد (Remote)"
        elif "hybrid" in combined or "هجين" in combined:
            return "هجين (Hybrid)"
        elif "on-site" in combined or "onsite" in combined or "مقر" in combined:
            return "من المقر (On-site)"
        return "غير محدد"

    @classmethod
    def is_conflicting_domain(cls, requested_keyword: str, job_title: str) -> bool:
        """
        التحقق مما إذا كانت الوظيفة تنتمي لمجال مختلف كلياً عن طلب المستخدم.
        مثال: المستخدم يبحث عن Software أو Data، والوظيفة عنوانها Marketing Intern أو Accountant.
        """
        kw_clean = requested_keyword.lower()
        title_clean = job_title.lower()

        # هل يبحث المستخدم عن مجال تقني؟
        is_tech_search = any(
            t in kw_clean
            for t in [
                "software", "engineer", "developer", "backend", "frontend",
                "data", "analyst", "analytics", "flutter", "python", "java",
                "ai", "machine learning", "mobile", "qa", "devops", "cloud",
                "programming", "مبرمج", "مهندس", "بيانات"
            ]
        )

        if is_tech_search:
            for pat in cls.NON_TECH_DOMAINS:
                # إذا وجدنا وسم غير تقني، نتأكد أن المستخدم لم يطلبه بنفسه في الكلمة المفتاحية
                if re.search(pat, title_clean) and not re.search(pat, kw_clean):
                    return True

        return False

    # كلمات وأدوات ربط مهملة أثناء تحليل الكلمات المفتاحية
    STOPWORDS = {
        "in", "for", "and", "the", "of", "or", "a", "to", "with", "at",
        "من", "في", "على", "و", "عن", "مع", "إلى", "الى"
    }

    # كلمات عامة وتعديلية لا تكفي وحدها لاعتبار الاستعلام مطابقاً
    CORE_MODIFIERS = {
        "developer", "engineer", "specialist", "officer", "job", "role",
        "intern", "internship", "trainee", "training", "junior", "senior",
        "lead", "manager", "head", "مهندس", "مطور", "تدريب", "مبتدئ", "سينيور",
    }

    # خريطة مرادفات التخصصات التقنية ومسمياتها
    ROLE_SYNONYMS = {
        "software": ["software", "swe", "developer", "engineer", "programmer", "coding", "مبرمج", "تطوير", "برمجيات"],
        "developer": ["developer", "software", "engineer", "programmer", "swe", "مبرمج"],
        "engineer": ["engineer", "engineering", "developer", "مهندس"],
        "backend": ["backend", "back-end", "python", "node", "java", "golang", "c#", ".net", "django", "fastapi", "spring", "php", "laravel"],
        "frontend": ["frontend", "front-end", "react", "vue", "angular", "javascript", "typescript", "ui", "web"],
        "data": ["data", "analyst", "analytics", "bi", "business intelligence", "machine learning", "ai", "science", "بيانات"],
        "analyst": ["analyst", "analytics", "analysis", "data", "تحليل", "محلل"],
        "cyber": ["cyber", "security", "infosec", "soc", "penetration", "سيبراني", "أمن"],
        "security": ["security", "cyber", "infosec", "soc", "أمن"],
        "mobile": ["mobile", "android", "ios", "flutter", "react native", "swift", "kotlin"],
        "qa": ["qa", "quality assurance", "test", "tester", "testing", "qc"],
        "devops": ["devops", "cloud", "sre", "infrastructure", "system admin"],
        "designer": ["designer", "design", "ui", "ux", "graphic", "مصمم"],
    }

    @classmethod
    def matches_requested_role(cls, requested_keyword: str, job_title: str) -> bool:
        """
        التحقق الصارم من أن عنوان الوظيفة يرتبط فعلاً بما بحث عنه المستخدم وليس نصاً عشوائياً.
        إذا كان الاستعلام مركباً (مثل Flutter Developer أو Flutter Intern)، نتأكد من مطابقة
        الكلمة الدلالية الأساسية للمجال (مثل Flutter) وليس فقط الكلمات العامة (مثل Developer أو Intern).
        """
        kw_clean = requested_keyword.strip().lower()
        title_clean = job_title.lower()

        # 1. مطابقة مباشرة كاملة
        if kw_clean in title_clean:
            return True

        # استخراج الكلمات واستبعاد حروف الجر والأدوات
        tokens = [
            tok for tok in re.split(r"[\s,\-_/]+", kw_clean)
            if len(tok) >= 2 and tok not in cls.STOPWORDS
        ]
        if not tokens:
            return False

        # حصر الكلمات الأساسية للتخصص
        core_tokens = [tok for tok in tokens if tok not in cls.CORE_MODIFIERS]
        tokens_to_match = core_tokens if core_tokens else tokens

        for tok in tokens_to_match:
            # مطابقة صريحة لكلمة كاملة في العنوان
            if re.search(r"\b" + re.escape(tok) + r"\b", title_clean):
                return True
            # فحص المرادفات التخصصية المباشرة
            for syn_key, syn_list in cls.ROLE_SYNONYMS.items():
                if tok == syn_key or tok in syn_list:
                    for syn in syn_list:
                        if re.search(r"\b" + re.escape(syn) + r"\b", title_clean):
                            return True

        return False

    @classmethod
    def passes_hard_filter(
        cls,
        title: str,
        company: str,
        requested_keyword: str,
        requested_job_type: str,
    ) -> bool:
        """
        بوابة الفلترة الصارمة (Hard Gate).
        أي وظيفة تخالف المعايير الصريحة أو لا ترتبط بالكلمة المفتاحية يتم استبعادها فوراً.
        """
        title_clean = title.lower()

        # 1. استبعاد فوري لأي وظيفة لا ترتبط بالكلمة المفتاحية التي بحث عنها المستخدم
        if not cls.matches_requested_role(requested_keyword, title):
            return False

        # فحص ما إذا كان طلب تدريب صريحاً إما من نوع الوظيفة أو من الكلمة المفتاحية
        is_intern_request = (
            requested_job_type == "internship"
            or any(
                k in requested_keyword.lower()
                for k in ["intern", "internship", "trainee", "training", "تدريب", "متدرب"]
            )
        )

        # 2. إذا كان الطلب تدريباً (Internship):
        if is_intern_request:
            # استبعاد قاطع لأي وظيفة تشترط سنوات خبرة (1+ سنة)
            if cls.is_experience_required(title):
                return False

            # استبعاد قاطع لأي وظيفة سينيور أو قيادية أو خبير
            for pat in cls.SENIOR_LEAD_PATTERNS:
                if re.search(pat, title_clean):
                    return False

            # استبعاد الوظائف التي لا تحتوي أي إشارة صريحة للتدريب أو الطلاب أو برامج الخريجين
            is_intern_signal = any(re.search(pat, title_clean) for pat in cls.INTERN_PATTERNS)
            is_grad_signal = any(re.search(pat, title_clean) for pat in cls.GRAD_PROGRAM_PATTERNS)

            if not (is_intern_signal or is_grad_signal):
                return False

            # استبعاد المجالات غير المطابقة (مثل محاسبة أو تسويق عند البحث عن سوفتوير)
            if cls.is_conflicting_domain(requested_keyword, title):
                return False

        # 3. إذا طلب المستخدم دوام جزئي:
        elif requested_job_type == "part_time":
            # استبعاد السينيور والليد في حال كان التناقض واضحاً
            if not re.search(r"\b(part[\s-]time|دوام[\s-]جزئي|freelance|flexible)\b", title_clean):
                # إذا كان صراحة Full-time نستبعده
                if re.search(r"\b(full[\s-]time|دوام[\s-]كامل)\b", title_clean):
                    return False

        # 4. استبعاد عام للمجالات المتعارضة كلياً
        if cls.is_conflicting_domain(requested_keyword, title):
            return False

        return True

    @classmethod
    def calculate_relevance(
        cls,
        title: str,
        requested_keyword: str,
        requested_job_type: str,
        location: str,
        target_location: str,
    ) -> int:
        """
        حساب نقاط المطابقة (Relevance Score من 0 إلى 100).
        """
        score = 0
        title_clean = title.lower()
        kw_clean = requested_keyword.lower().strip()

        # 1. مطابقة المسمى الوظيفي المطلوب (حتى 40 نقطة)
        if kw_clean in title_clean:
            score += 40
        else:
            # مطابقة أجزاء الكلمة المفتاحية
            kw_tokens = [tok for tok in re.split(r"[\s,\-_/]+", kw_clean) if len(tok) > 2]
            if kw_tokens:
                matched_tokens = sum(1 for tok in kw_tokens if tok in title_clean)
                score += int(30 * (matched_tokens / len(kw_tokens)))

        # 2. مطابقة نوع الوظيفة (حتى 35 نقطة)
        if requested_job_type == "internship":
            if any(re.search(pat, title_clean) for pat in cls.INTERN_PATTERNS):
                score += 35
            elif any(re.search(pat, title_clean) for pat in cls.GRAD_PROGRAM_PATTERNS):
                score += 25
        elif requested_job_type == "full_time":
            if re.search(r"\b(full[\s-]time|دوام[\s-]كامل)\b", title_clean):
                score += 35
            else:
                score += 20
        else:
            score += 20

        # 3. مطابقة المكان (حتى 15 نقطة)
        target_loc_clean = target_location.lower()
        loc_clean = location.lower()
        if target_loc_clean in loc_clean or loc_clean in target_loc_clean:
            score += 15
        elif "egypt" in loc_clean or "cairo" in loc_clean:
            score += 10
        else:
            score += 5

        # 4. جودة العنوان وخلوه من الضوضاء (10 نقاط)
        if len(title) <= 60:
            score += 10
        else:
            score += 5

        return min(max(score, 0), 100)


class LinkedInScraper:
    """محرك بحث وجلب وظائف وتدريبات لينكدإن بدقة فائقة وبدون حساب."""

    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="128", "Google Chrome";v="128"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    JOB_TYPE_MAP = {
        "full_time": "F",
        "internship": "I",
        "part_time": "P",
        "contract": "C",
        "temporary": "T",
        "volunteer": "V",
    }

    WORKPLACE_MAP = {
        "onsite": "1",
        "remote": "2",
        "hybrid": "3",
    }

    DATE_POSTED_MAP = {
        "past_24h": "r86400",
        "past_week": "r604800",
        "past_month": "r2592000",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.classifier = JobClassifier()

    def _generate_targeted_queries(
        self,
        keyword: str,
        job_type: str,
        workplace_type: str,
    ) -> List[str]:
        """
        توليد استعلامات بحث مستهدفة ومنظمة بناءً على نية المستخدم.
        نستخدم صيغاً محددة بدلاً من البحث العشوائي الواسع لمنع جلب وظائف الـ Senior.
        """
        clean_kw = keyword.strip()
        kw_lower = clean_kw.lower()

        queries = []

        if job_type == "internship":
            if "intern" in kw_lower or "تدريب" in kw_lower:
                queries.append(clean_kw)
            else:
                # استعلامات موجهة بدقة للتدريب
                queries.append(f'"{clean_kw}" intern')
                queries.append(f'"{clean_kw}" internship')
                queries.append(f'"{clean_kw}" trainee')
        elif job_type == "part_time":
            if "part" in kw_lower:
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" part time')
        else:
            queries.append(clean_kw)

        if workplace_type == "remote" and "remote" not in kw_lower:
            queries = [f"{q} remote" for q in queries]

        return queries

    @staticmethod
    def _normalize_string(text: str) -> str:
        """تنظيف النصوص من المسافات والرموز غير المرئية."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _make_dedup_key(company: str, title: str) -> str:
        """مفتاح إزالة التكرار الموحد عبر اسم الشركة والعنوان بعد إزالة الرموز الزائدة."""
        c = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF]", "", company.lower())
        t = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF]", "", title.lower())
        return f"{c}_{t}"

    def scrape(
        self,
        keywords: List[str],
        location: str,
        job_type: str = "all",
        workplace_type: str = "all",
        date_posted: str = "all",
        pages_per_keyword: int = 2,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[Dict[str, str]]:
        """
        جلب وتصنيف وفلترة وترتيب الوظائف مع ضمان الدقة والجودة أولاً.
        """
        clean_keywords, effective_job_type = self.classifier.normalize_search_intent(
            keywords=keywords,
            job_type=job_type,
        )
        if not clean_keywords:
            return []

        # تجهيز قائمة الاستعلامات الموجهة
        query_plan: List[Tuple[str, str]] = []  # (original_keyword, search_query)
        for kw in clean_keywords:
            targeted = self._generate_targeted_queries(kw, effective_job_type, workplace_type)
            for tq in targeted:
                query_plan.append((kw, tq))

        raw_jobs: List[Dict[str, str]] = []
        seen_job_ids: Set[str] = set()
        seen_dedup_keys: Set[str] = set()

        total_queries = len(query_plan) * pages_per_keyword
        step = 0

        for original_kw, search_query in query_plan:
            for page in range(pages_per_keyword):
                step += 1
                if progress_callback:
                    pct = min(step / max(total_queries, 1), 0.90)
                    progress_callback(
                        pct,
                        f"عماد بينكش في LinkedIn على '{search_query}' (صفحة {page + 1})...",
                    )

                start = page * 25
                params = {
                    "keywords": search_query,
                    "location": location,
                    "start": str(start),
                }

                if effective_job_type in self.JOB_TYPE_MAP:
                    params["f_JT"] = self.JOB_TYPE_MAP[effective_job_type]

                if workplace_type in self.WORKPLACE_MAP:
                    params["f_WT"] = self.WORKPLACE_MAP[workplace_type]

                if date_posted in self.DATE_POSTED_MAP:
                    params["f_TPR"] = self.DATE_POSTED_MAP[date_posted]

                try:
                    resp = self.session.get(
                        self.BASE_URL,
                        params=params,
                        timeout=12,
                    )

                    if resp.status_code == 429:
                        if progress_callback:
                            progress_callback(
                                0.92,
                                "LinkedIn حس بوجودنا وبدأ يتقل.. عماد بيفرز اللي جمعه دلوقتي!",
                            )
                        break

                    if resp.status_code != 200:
                        break

                    soup = BeautifulSoup(resp.content, "html.parser")
                    job_cards = soup.find_all("li")
                    if not job_cards:
                        break

                    for card in job_cards:
                        link_elem = card.find("a", class_="base-card__full-link")
                        if not link_elem:
                            link_elem = card.find("a")

                        if not link_elem or not link_elem.has_attr("href"):
                            continue

                        raw_link = link_elem["href"]
                        job_link = raw_link.split("?")[0].strip()

                        # استخراج Job ID
                        parts = job_link.rstrip("/").split("-")
                        job_id = parts[-1] if parts else job_link.rstrip("/").split("/")[-1]

                        if not job_id or job_id in seen_job_ids:
                            continue

                        title_elem = card.find("h3", class_="base-search-card__title")
                        raw_title = self._normalize_string(title_elem.text if title_elem else "")
                        if not raw_title:
                            continue

                        company_elem = card.find("h4", class_="base-search-card__subtitle")
                        company = self._normalize_string(company_elem.text if company_elem else "غير محدد")

                        location_elem = card.find("span", class_="job-search-card__location")
                        loc = self._normalize_string(location_elem.text if location_elem else location)

                        date_elem = card.find("time")
                        post_date = "غير محدد"
                        if date_elem:
                            post_date = (
                                date_elem["datetime"]
                                if date_elem.has_attr("datetime")
                                else self._normalize_string(date_elem.text)
                            )

                        # إزالة التكرار الموحد عبر الشركة والعنوان
                        dedup_key = self._make_dedup_key(company, raw_title)
                        if dedup_key in seen_dedup_keys:
                            continue

                        # ─── مرحلة الفلترة الصارمة (Hard Gate) ───────────────────
                        # استبعاد قاطع لأي وظيفة لا تطابق المعايير المطلوبة
                        if not self.classifier.passes_hard_filter(
                            title=raw_title,
                            company=company,
                            requested_keyword=original_kw,
                            requested_job_type=effective_job_type,
                        ):
                            continue

                        # ─── مرحلة التصنيف الدقيق ──────────────────────────────
                        classified_seniority = self.classifier.detect_seniority(raw_title)
                        classified_type = self.classifier.detect_job_type(raw_title)
                        classified_workplace = self.classifier.detect_workplace(raw_title, loc)

                        # ─── حساب نقاط المطابقة (Relevance Scoring) ─────────────
                        relevance = self.classifier.calculate_relevance(
                            title=raw_title,
                            requested_keyword=original_kw,
                            requested_job_type=effective_job_type,
                            location=loc,
                            target_location=location,
                        )

                        seen_job_ids.add(job_id)
                        seen_dedup_keys.add(dedup_key)

                        raw_jobs.append(
                            {
                                "Job ID": job_id,
                                "البحث": original_kw,
                                "المسمى الوظيفي": raw_title,
                                "الشركة": company,
                                "المكان": loc,
                                "نوع الوظيفة": classified_type,
                                "مستوى الخبرة": classified_seniority,
                                "بيئة العمل": classified_workplace,
                                "تاريخ النشر": post_date,
                                "رابط التقديم": job_link,
                                "relevance_score": relevance,
                            }
                        )

                    time.sleep(random.uniform(0.7, 1.4))

                except requests.RequestException:
                    break

        if progress_callback:
            progress_callback(1.0, "عماد فرز الوظائف ورتبهالك بالأكثر دقة وملاءمة!")

        # ─── مرحلة الترتيب بالأهمية (Relevance Ranking) ──────────────────
        # ترتيب النتائج من الأعلى مطابقة إلى الأقل
        ranked_jobs = sorted(raw_jobs, key=lambda j: j["relevance_score"], reverse=True)

        return ranked_jobs
