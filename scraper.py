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
    """Structured search intent representing user preferences."""
    keywords: List[str]
    location: str
    job_type: str = "all"        # "all", "internship", "full_time", "part_time", "contract"
    seniority: str = "all"       # "all", "internship", "entry", "mid", "senior", "director"
    workplace_type: str = "all"  # "all", "remote", "hybrid", "onsite"
    date_posted: str = "all"     # "all", "past_24h", "past_week", "past_month"


class JobClassifier:
    """Classification and analysis engine for job titles, seniority levels, and employment types."""

    # Exclusion patterns for senior/lead roles
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

    # Internship and trainee patterns
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

    # Graduate program patterns
    GRAD_PROGRAM_PATTERNS = [
        r"\bgraduate[\s-]program\b",
        r"\bgraduate[\s-]in[\s-]training\b",
        r"\bgit[\s-]program\b",
        r"\bfresh[\s-]graduate[\s-]program\b",
        r"\bnextgen\b",
        r"\bmentorship[\s-]program\b",
    ]

    # Entry-level and junior patterns
    ENTRY_PATTERNS = [
        r"\bjunior\b",
        r"\bjr\.?\b",
        r"\bentry[\s-]level\b",
        r"\bfresh\b",
        r"\bfresh[\s-]grad\b",
        r"\bgraduate\b",
        r"\bassociate\b",
        r"\bمبتدئ\b",
        r"\bحديث[\s-]تخرج\b",
        r"\bحديثي[\s-]تخرج\b",
        r"\bحديثي[\s-]التخرج\b",
    ]

    # Non-tech domains to exclude when searching for tech roles
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

    # Explicit years of experience patterns
    EXPERIENCE_PATTERNS = [
        r"(?<![0-9][\s–\-])\b[1-9]\d*\+?(?:\s*[–\-+to]+\s*[0-9]+)?\s*(?:years?|yrs?|yr|سنوات|سنة)\b",
        r"\b(سنتين|سنة|[1-9]\d*\s*سنوات?)\s*خبرة\b|\bخبرة\s*(سنتين|سنة|[1-9]\d*)\b",
        r"\bexperienced\b",
    ]

    # Contract, freelance, and temporary work patterns
    CONTRACT_PATTERNS = [
        r"\bcontract(?:or|ual)?\b",
        r"\bfreelanc(?:e|er|ing)\b",
        r"\bproject[\s-]based\b",
        r"\b(?:[1-9]\d*[\s-]*(?:months?|month|شهور?|أشهر|شهر))\b(?!\s*(?:experience|of experience|خبرة))",
        r"\b[1-9]\d*[\s-]*(?:months?|yrs?|years?)[\s\w-]*\bproject\b",
        r"\bfixed[\s-]term\b",
        r"\btemporary\b",
        r"\bconsultant\b",
        r"\boutsourc(?:ed|ing)\b",
        r"\bعقد\b",
        r"\bعمل[\s-]حر\b",
        r"\bمستقل\b",
        r"\bمؤقت\b",
        r"\bمشروع\b",
        r"\bاستشاري\b",
    ]

    # Internship modifiers and tokens
    INTERN_MODIFIERS = {
        "intern", "internship", "trainee", "training", "co-op",
        "apprentice", "apprenticeship", "student", "تدريب", "متدرب", "طلبة"
    }

    @classmethod
    def is_experience_required(cls, title: str) -> bool:
        """Check if title explicitly requires previous years of experience (1+ years)."""
        title_clean = title.lower()
        return any(re.search(pat, title_clean) for pat in cls.EXPERIENCE_PATTERNS)

    @classmethod
    def normalize_search_intent(
        cls,
        keywords: List[str],
        job_type: str = "all",
        seniority: str = "all",
    ) -> Tuple[List[str], str, str]:
        """
        Extract and normalize search intent from keywords, job type, and seniority.
        - Extracts core roles from compound inputs (e.g., 'flutter intern' -> 'flutter', internship).
        - Prevents isolated seniority modifier queries when accompanied by domain keywords.
        """
        has_intern_signal = (job_type == "internship" or seniority == "internship")
        effective_seniority = seniority
        effective_job_type = job_type
        cleaned_keywords: List[str] = []

        for kw in keywords:
            kw_clean = kw.strip()
            tokens = [t.lower() for t in re.split(r"[\s,\-_/]+", kw_clean) if t]
            if not tokens:
                continue

            # Pure internship modifier token (e.g. 'intern' or 'trainee')
            if all(t in cls.INTERN_MODIFIERS for t in tokens):
                has_intern_signal = True
                effective_seniority = "internship"
                continue

            # Compound token containing both role and internship modifier (e.g. 'flutter intern')
            if any(t in cls.INTERN_MODIFIERS for t in tokens):
                has_intern_signal = True
                effective_seniority = "internship"
                clean_tokens = [t for t in tokens if t not in cls.INTERN_MODIFIERS]
                if clean_tokens:
                    cleaned_keywords.append(" ".join(clean_tokens))
                continue

            # Check for senior / lead modifiers
            if any(t in ["senior", "sr", "lead", "architect", "سينيور", "خبير"] for t in tokens):
                if effective_seniority == "all":
                    effective_seniority = "senior"
                clean_tokens = [t for t in tokens if t not in ["senior", "sr", "lead", "architect", "سينيور", "خبير"]]
                if clean_tokens:
                    cleaned_keywords.append(" ".join(clean_tokens))
                else:
                    cleaned_keywords.append(kw_clean)
                continue

            # Check for junior / entry-level modifiers
            if any(t in ["junior", "jr", "entry", "fresh", "مبتدئ", "حديث"] for t in tokens):
                if effective_seniority == "all":
                    effective_seniority = "entry"
                clean_tokens = [t for t in tokens if t not in ["junior", "jr", "entry", "fresh", "مبتدئ", "حديث", "تخرج"]]
                if clean_tokens:
                    cleaned_keywords.append(" ".join(clean_tokens))
                else:
                    cleaned_keywords.append(kw_clean)
                continue

            # Check for contract / freelance modifiers
            contract_tokens = ["contract", "freelance", "freelancer", "عقد", "حر", "فريلانس"]
            if any(t in contract_tokens for t in tokens):
                if effective_job_type == "all":
                    effective_job_type = "contract"
                contract_and_generic = set(contract_tokens + ["عمل", "شغل", "وظيفة", "job", "role"])
                clean_tokens = [t for t in tokens if t not in contract_and_generic]
                if clean_tokens:
                    cleaned_keywords.append(" ".join(clean_tokens))
                else:
                    cleaned_keywords.append("contract")
                continue

            cleaned_keywords.append(kw_clean)

        if not cleaned_keywords and keywords:
            cleaned_keywords = [k.strip() for k in keywords if k.strip()]

        if has_intern_signal:
            effective_job_type = "internship"
            effective_seniority = "internship"

        return cleaned_keywords, effective_job_type, effective_seniority

    @classmethod
    def detect_seniority(cls, title: str) -> str:
        """
        Detect seniority level strictly from the job title.
        Defaults to 'غير محدد' if no explicit signal is found.
        """
        title_clean = title.lower()

        for pat in cls.SENIOR_LEAD_PATTERNS:
            if re.search(pat, title_clean):
                return "خبير / قيادي (Senior/Lead)"

        # Check explicit experience requirements in title
        if cls.is_experience_required(title):
            if re.search(
                r"(?<![0-9][\s–\-])\b[3-9]\d*\+?(?:\s*[–\-+to]+\s*[0-9]+)?\s*(?:years?|yrs?|yr|سنوات)\b",
                title_clean,
            ):
                return "متوسط / خبير (Mid/Senior)"
            return "مبتدئ بخبرة (1-2 Years)"

        for pat in cls.INTERN_PATTERNS:
            if re.search(pat, title_clean):
                return "تدريب (Intern)"

        for pat in cls.GRAD_PROGRAM_PATTERNS:
            if re.search(pat, title_clean):
                return "برنامج خريجين (Graduate/Trainee)"

        for pat in cls.ENTRY_PATTERNS:
            if re.search(pat, title_clean):
                return "مبتدئ (Junior/Entry)"

        if re.search(r"\b(mid[\s-]level|intermediate)\b", title_clean):
            return "متوسط (Mid Level)"

        return "غير محدد"

    @classmethod
    def detect_job_type(cls, title: str) -> str:
        """
        Detect employment type from job title without assuming full-time by default.
        """
        title_clean = title.lower()

        for pat in cls.CONTRACT_PATTERNS:
            if re.search(pat, title_clean):
                return "عقد / عمل حر (Contract)"

        # Explicit experience requirement disqualifies internship
        if cls.is_experience_required(title):
            if re.search(r"\b(part[\s-]time|دوام[\s-]جزئي)\b", title_clean):
                return "دوام جزئي (Part-time)"
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

        if re.search(r"\b(full[\s-]time|دوام[\s-]كامل)\b", title_clean):
            return "دوام كامل (Full-time)"

        return "غير محدد"

    @classmethod
    def detect_workplace(cls, title: str, location: str) -> str:
        """Detect workplace arrangement (remote, hybrid, on-site) from title and location."""
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
        Check if the job title belongs to a conflicting non-technical domain
        when the search target is technical (e.g., Software vs Marketing/Accounting).
        """
        kw_clean = requested_keyword.lower()
        title_clean = job_title.lower()

        # Detect if requested keyword targets a tech role
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
                # Exclude if non-tech signal is present unless user explicitly searched for it
                if re.search(pat, title_clean) and not re.search(pat, kw_clean):
                    return True

        return False

    # Stopwords ignored during keyword tokenization
    STOPWORDS = {
        "in", "for", "and", "the", "of", "or", "a", "to", "with", "at",
        "من", "في", "على", "و", "عن", "مع", "إلى", "الى"
    }

    # Generic role modifiers insufficient on their own for domain matching
    CORE_MODIFIERS = {
        "developer", "engineer", "specialist", "officer", "job", "role",
        "intern", "internship", "trainee", "training", "junior", "senior",
        "lead", "manager", "head", "مهندس", "مطور", "تدريب", "مبتدئ", "سينيور",
    }

    # Synonym map for technical domains and specializations
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
        Verify that job title genuinely matches the requested role keyword,
        checking core domain tokens and technical synonyms.
        """
        kw_clean = requested_keyword.strip().lower()
        title_clean = job_title.lower()

        # 1. Direct exact match
        if kw_clean in title_clean:
            return True

        # Accept generic queries without domain constraints (contract, internship, job)
        if kw_clean in ["contract", "freelance", "freelancer", "عقد", "عمل حر", "intern", "internship", "تدريب", "وظيفة", "شغل", "job"]:
            return True

        # Tokenize and filter stopwords
        tokens = [
            tok for tok in re.split(r"[\s,\-_/]+", kw_clean)
            if len(tok) >= 2 and tok not in cls.STOPWORDS
        ]
        if not tokens:
            return False

        # Isolate core domain tokens
        core_tokens = [tok for tok in tokens if tok not in cls.CORE_MODIFIERS]
        tokens_to_match = core_tokens if core_tokens else tokens

        for tok in tokens_to_match:
            if re.search(r"\b" + re.escape(tok) + r"\b", title_clean):
                return True
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
        requested_job_type: str = "all",
        requested_seniority: str = "all",
    ) -> bool:
        """
        Hard filtering gate to immediately exclude jobs violating role, seniority, or employment criteria.
        """
        title_clean = title.lower()

        # 1. Exclude titles unrelated to requested role
        if not cls.matches_requested_role(requested_keyword, title):
            return False

        # Exclude conflicting domains
        if cls.is_conflicting_domain(requested_keyword, title):
            return False

        # Check if query targets internship
        is_intern_request = (
            requested_job_type == "internship"
            or requested_seniority == "internship"
            or any(
                k in requested_keyword.lower()
                for k in ["intern", "internship", "trainee", "training", "تدريب", "متدرب"]
            )
        )

        # 2. Internship hard filter
        if is_intern_request:
            # Reject jobs explicitly requiring 1+ years of experience
            if cls.is_experience_required(title):
                return False

            # Reject senior/lead/manager roles
            for pat in cls.SENIOR_LEAD_PATTERNS:
                if re.search(pat, title_clean):
                    return False

            # Ensure explicit intern/grad signal exists in title
            is_intern_signal = any(re.search(pat, title_clean) for pat in cls.INTERN_PATTERNS)
            is_grad_signal = any(re.search(pat, title_clean) for pat in cls.GRAD_PROGRAM_PATTERNS)

            if not (is_intern_signal or is_grad_signal):
                return False

        # 3. Entry-level / Junior hard filter
        elif requested_seniority == "entry":
            # Reject senior/lead/manager roles
            for pat in cls.SENIOR_LEAD_PATTERNS:
                if re.search(pat, title_clean):
                    return False

            # Reject 3+ years required experience
            if re.search(
                r"(?<![0-9][\s–\-])\b[3-9]\d*\+?(?:\s*[–\-+to]+\s*[0-9]+)?\s*(?:years?|yrs?|yr|سنوات)\b",
                title_clean,
            ):
                return False
            if re.search(r"\b(خبرة\s*[3-9]|[3-9]\s*سنوات\s*خبرة)\b", title_clean):
                return False

            # Exclude pure student internships when searching for entry-level roles
            if any(re.search(p, title_clean) for p in cls.INTERN_PATTERNS) and not any(re.search(p, title_clean) for p in cls.ENTRY_PATTERNS) and requested_job_type != "internship":
                return False

        # 4. Senior / Lead hard filter
        elif requested_seniority == "senior":
            # Reject entry-level and internship titles
            if any(re.search(pat, title_clean) for pat in cls.INTERN_PATTERNS):
                return False
            if any(re.search(pat, title_clean) for pat in cls.ENTRY_PATTERNS):
                return False

            # Require explicit senior/lead signal or 3+ years experience
            has_senior_signal = any(re.search(pat, title_clean) for pat in cls.SENIOR_LEAD_PATTERNS)
            has_high_exp = bool(
                re.search(
                    r"(?<![0-9][\s–\-])\b[3-9]\d*\+?(?:\s*[–\-+to]+\s*[0-9]+)?\s*(?:years?|yrs?|yr|سنوات)\b",
                    title_clean,
                )
            ) or bool(re.search(r"\b(خبرة\s*[3-9]|[3-9]\s*سنوات\s*خبرة)\b", title_clean))

            if not (has_senior_signal or has_high_exp):
                return False

        # 5. Mid-level hard filter
        elif requested_seniority == "mid":
            # Reject entry-level and internship titles
            if any(re.search(pat, title_clean) for pat in cls.INTERN_PATTERNS):
                return False
            if any(re.search(pat, title_clean) for pat in cls.ENTRY_PATTERNS):
                return False
            # Reject executive / director roles
            if any(re.search(p, title_clean) for p in [r"\bdirector\b", r"\bhead\b", r"\bchief\b", r"\bvp\b", r"\bprincipal\b", r"\bرئيس\b"]):
                return False

        # 6. Management / Director hard filter
        elif requested_seniority == "director":
            if any(re.search(pat, title_clean) for pat in cls.INTERN_PATTERNS):
                return False
            if any(re.search(pat, title_clean) for pat in cls.ENTRY_PATTERNS):
                return False
            if not any(re.search(p, title_clean) for p in [r"\bmanager\b", r"\bdirector\b", r"\bhead\b", r"\bvp\b", r"\bchief\b", r"\bexecutive\b", r"\bمدير\b", r"\bرئيس\b"]):
                return False

        # 7. Employment type hard filter (contract / part-time / full-time)
        if requested_job_type == "contract":
            has_contract_signal = any(re.search(pat, title_clean) for pat in cls.CONTRACT_PATTERNS)
            has_full_time_signal = bool(re.search(r"\b(full[\s-]time|دوام[\s-]كامل|permanent|دائم)\b", title_clean))

            # Exclude full-time/permanent roles when contract is requested unless contract signal exists
            if has_full_time_signal and not has_contract_signal:
                return False

            # Exclude student internships when contract work is requested
            if any(re.search(pat, title_clean) for pat in cls.INTERN_PATTERNS) and not has_contract_signal:
                return False

        elif requested_job_type == "part_time":
            if not re.search(r"\b(part[\s-]time|دوام[\s-]جزئي|freelance|flexible)\b", title_clean):
                if re.search(r"\b(full[\s-]time|دوام[\s-]كامل)\b", title_clean):
                    return False
        elif requested_job_type == "full_time":
            if re.search(r"\b(part[\s-]time|دوام[\s-]جزئي|freelance|عقد[\s-]مؤقت)\b", title_clean):
                return False

        return True

    @classmethod
    def calculate_relevance(
        cls,
        title: str,
        requested_keyword: str,
        requested_job_type: str = "all",
        requested_seniority: str = "all",
        location: str = "",
        target_location: str = "",
    ) -> int:
        """Calculate match relevance score from 0 to 100."""
        score = 0
        title_clean = title.lower()
        kw_clean = requested_keyword.lower().strip()

        # 1. Title keyword matching (up to 40 pts)
        if kw_clean in title_clean:
            score += 40
        else:
            # Partial token matching
            kw_tokens = [tok for tok in re.split(r"[\s,\-_/]+", kw_clean) if len(tok) > 2]
            if kw_tokens:
                matched_tokens = sum(1 for tok in kw_tokens if tok in title_clean)
                score += int(30 * (matched_tokens / len(kw_tokens)))

        # 2. Employment type & seniority match (up to 35 pts)
        sen_score = 0
        if requested_seniority == "internship" or requested_job_type == "internship":
            if any(re.search(pat, title_clean) for pat in cls.INTERN_PATTERNS):
                sen_score = 35
            elif any(re.search(pat, title_clean) for pat in cls.GRAD_PROGRAM_PATTERNS):
                sen_score = 25
        elif requested_seniority == "entry":
            if any(re.search(pat, title_clean) for pat in cls.ENTRY_PATTERNS):
                sen_score = 35
            else:
                sen_score = 25
        elif requested_seniority == "senior":
            if any(re.search(pat, title_clean) for pat in cls.SENIOR_LEAD_PATTERNS):
                sen_score = 35
            else:
                sen_score = 25
        elif requested_job_type == "contract":
            if any(re.search(pat, title_clean) for pat in cls.CONTRACT_PATTERNS):
                sen_score = 35
            else:
                sen_score = 25
        elif requested_job_type == "full_time":
            if re.search(r"\b(full[\s-]time|دوام[\s-]كامل)\b", title_clean):
                sen_score = 35
            else:
                sen_score = 20
        else:
            sen_score = 20
        score += sen_score

        # 3. Location match (up to 15 pts)
        target_loc_clean = target_location.lower()
        loc_clean = location.lower()
        if target_loc_clean in loc_clean or loc_clean in target_loc_clean:
            score += 15
        elif "egypt" in loc_clean or "cairo" in loc_clean:
            score += 10
        else:
            score += 5

        # 4. Title conciseness & noise reduction (up to 10 pts)
        if len(title) <= 60:
            score += 10
        else:
            score += 5

        return min(max(score, 0), 100)


class LinkedInScraper:
    """LinkedIn guest job search and extraction engine."""

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

    SENIORITY_MAP = {
        "internship": "1",
        "entry": "2",
        "associate": "3",
        "mid": "4",
        "senior": "4",
        "director": "5",
        "executive": "6",
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
        job_type: str = "all",
        seniority: str = "all",
        workplace_type: str = "all",
    ) -> List[str]:
        """Generate targeted search queries tailored to user intent, seniority, and workplace."""
        clean_kw = keyword.strip()
        kw_lower = clean_kw.lower()

        queries = []

        if seniority == "internship" or job_type == "internship":
            if "intern" in kw_lower or "تدريب" in kw_lower:
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" intern')
                queries.append(f'"{clean_kw}" internship')
                queries.append(f'"{clean_kw}" trainee')
        elif seniority == "entry":
            if any(k in kw_lower for k in ["junior", "entry", "fresh"]):
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" junior')
                queries.append(f'"{clean_kw}" "entry level"')
                queries.append(f'"{clean_kw}" fresh')
        elif seniority == "senior":
            if any(k in kw_lower for k in ["senior", "lead", "sr"]):
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" senior')
                queries.append(f'"{clean_kw}" lead')
        elif seniority == "mid":
            if "mid" in kw_lower:
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" "mid level"')
                queries.append(clean_kw)
        elif seniority == "director":
            if any(k in kw_lower for k in ["manager", "director", "head"]):
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" manager')
                queries.append(f'"{clean_kw}" director')
                queries.append(f'"{clean_kw}" head')
        elif job_type == "contract":
            if any(k in kw_lower for k in ["contract", "freelance", "عقد", "حر", "مستقل"]):
                queries.append(clean_kw)
            else:
                queries.append(f'"{clean_kw}" contract')
                queries.append(f'"{clean_kw}" freelance')
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
        """Normalize whitespace and invisible characters."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _make_dedup_key(company: str, title: str) -> str:
        """Generate deduplication key based on normalized company and title."""
        c = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF]", "", company.lower())
        t = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF]", "", title.lower())
        return f"{c}_{t}"

    def scrape(
        self,
        keywords: List[str],
        location: str,
        job_type: str = "all",
        seniority: str = "all",
        workplace_type: str = "all",
        date_posted: str = "all",
        pages_per_keyword: int = 2,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[Dict[str, str]]:
        """Fetch, classify, filter, and rank job listings."""
        clean_keywords, effective_job_type, effective_seniority = self.classifier.normalize_search_intent(
            keywords=keywords,
            job_type=job_type,
            seniority=seniority,
        )
        if not clean_keywords:
            return []

        # Prepare targeted query plan and balance pagination depth
        query_plan_with_pages: List[Tuple[str, str, int]] = []
        for kw in clean_keywords:
            targeted = self._generate_targeted_queries(
                kw, effective_job_type, effective_seniority, workplace_type
            )
            pages_each = max(pages_per_keyword * 2, 4) if len(targeted) == 1 else max(1, pages_per_keyword)
            for tq in targeted:
                query_plan_with_pages.append((kw, tq, pages_each))

        raw_jobs: List[Dict[str, str]] = []
        seen_job_ids: Set[str] = set()
        seen_dedup_keys: Set[str] = set()

        def safe_progress(pct: float, msg: str):
            if progress_callback:
                try:
                    progress_callback(pct, msg)
                except Exception:
                    pass

        total_queries = sum(p for _, _, p in query_plan_with_pages)
        step = 0

        for original_kw, search_query, pages_to_fetch in query_plan_with_pages:
            for page in range(pages_to_fetch):
                step += 1
                pct = min(step / max(total_queries, 1), 0.90)
                safe_progress(
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

                if effective_seniority in self.SENIORITY_MAP:
                    params["f_E"] = self.SENIORITY_MAP[effective_seniority]

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
                        safe_progress(
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
                        try:
                            link_elem = card.find("a", class_="base-card__full-link")
                            if not link_elem:
                                link_elem = card.find("a")

                            if not link_elem or not link_elem.has_attr("href"):
                                continue

                            raw_link = link_elem["href"]
                            job_link = raw_link.split("?")[0].strip()

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

                            # Deduplicate by company and title
                            dedup_key = self._make_dedup_key(company, raw_title)
                            if dedup_key in seen_dedup_keys:
                                continue

                            # Hard filtering gate
                            if not self.classifier.passes_hard_filter(
                                title=raw_title,
                                company=company,
                                requested_keyword=original_kw,
                                requested_job_type=effective_job_type,
                                requested_seniority=effective_seniority,
                            ):
                                continue

                            # Classify seniority, job type, and workplace
                            classified_seniority = self.classifier.detect_seniority(raw_title)
                            classified_type = self.classifier.detect_job_type(raw_title)
                            if classified_type == "غير محدد" and effective_job_type == "contract":
                                classified_type = "عقد / عمل حر (Contract)"
                            classified_workplace = self.classifier.detect_workplace(raw_title, loc)

                            # Calculate relevance score
                            relevance = self.classifier.calculate_relevance(
                                title=raw_title,
                                requested_keyword=original_kw,
                                requested_job_type=effective_job_type,
                                requested_seniority=effective_seniority,
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
                        except Exception:
                            continue

                    time.sleep(random.uniform(0.7, 1.4))

                except requests.RequestException:
                    break
                except Exception:
                    continue

        safe_progress(1.0, "عماد فرز الوظائف ورتبهالك بالأكثر دقة وملاءمة!")

        # Rank results by relevance score descending
        ranked_jobs = sorted(raw_jobs, key=lambda j: j["relevance_score"], reverse=True)

        return ranked_jobs
