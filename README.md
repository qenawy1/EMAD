# 💼 Emad | Smart LinkedIn Job & Internship Finder

> **"Stop drowning in LinkedIn's noise every day. Put Emad to work—get precisely tailored jobs and internships with zero clutter, and stay relaxed."**

**Emad** is an intelligent, high-precision LinkedIn job and internship discovery engine built with **Python** and **Streamlit**. It delivers accurate, filtered opportunities directly from LinkedIn without requiring account credentials, logins, or paid subscriptions.

---

## 🌟 Key Highlights & Engine Architecture

### 1. High-Precision Filtering (Zero False Positives)
- **Title-First Classification Engine (`JobClassifier`):** Classifies positions based strictly on verified job titles and explicit signals rather than ambiguous keyword mentions in descriptions.
- **No Unsubstantiated Assumptions:** Does not default unspecified titles (e.g., *"Software Engineer"*) to Full-time unless clear, verified evidence exists in the posting.
- **Hard Gate Internship Gatekeeper:** When searching for an **Internship**, the engine strictly blocks:
  - Any senior or leadership roles (`Senior`, `Sr.`, `Lead`, `Team Lead`, `Staff`, `Principal`, `Manager`, `Architect`, `Director`, `Head`, `VP`, `Chief`).
  - Any position with explicit prior experience requirements (e.g., `1–2 years of experience`, `2+ years`, `3-5 years`).
  - Conflicting professional domains (e.g., Marketing or Accounting roles when searching for Software or Data roles).
- **Smart Intent Normalization (`normalize_search_intent`):** Handles compound inputs such as `Flutter intern`, `Flutter, intern`, or selecting the `Internship` radio button. It isolates the core discipline (`Flutter`), sets the search intent to `Internship`, and prevents irrelevant cross-domain noise.

### 2. Granular Seniority & Work Mode Categorization
- **Seniority Level Filter (`مستوى الخبرة`):**
  - `الكل (أي مستوى)` - Any experience level
  - `تدريب طلبة وخريجين (Internship)` - Dedicated internships and graduate training programs
  - `مبتدئ / حديث تخرج (Junior / Entry)` - Strictly filters for entry-level roles, blocking Senior/Lead and 3+ years experience
  - `متوسط الخبرة (Mid-Level)` - Targets intermediate roles, excluding interns and executives
  - `سينيور / خبير (Senior / Lead)` - Strictly filters for Senior/Lead/Architect roles, excluding juniors and interns
  - `إدارة وقيادة (Manager / Director)` - Targets managerial and executive leadership roles
- **Job Types (`نوع الشغلانة / نظام التعاقد`):**
  - `All (الكل)`
  - `Full-time (دوام كامل)`
  - `Part-time (دوام جزئي)`
  - `Contract / Freelance (عقد / عمل حر)`
- **Workplace Environments:**
  - `Remote (عن بُعد - من البيت)`
  - `Hybrid (هجين)`
  - `On-site (من المقر)`
  - `All (الكل)`

### 3. Detailed Geographic Coverage
- **Egypt 🇪🇬:** Cairo, Giza, Alexandria, Mansoura / Dakahlia, Tanta / Gharbia, Zagazig / Sharqia, Qalyubia, Menofia, Canal Cities, Upper Egypt, Red Sea, and South Sinai.
- **Saudi Arabia 🇸🇦:** Riyadh, Jeddah, Eastern Province (Dammam / Khobar), Mecca, Medina.
- **United Arab Emirates 🇦🇪:** Dubai, Abu Dhabi, Sharjah.
- **Custom Worldwide Search 🌍:** Input any city or country globally to target postings directly.

### 4. Posting Recency Filters
- **Past 24 Hours (`طازة طازة`):** For early applications to maximize CV review visibility.
- **Past Week (`أحسن فرصة للتقديم`):** Highest response rate window.
- **Anytime (`المتاح كله`):** Comprehensive historical listings.

### 5. Modern UI & Direct Application
- **Direct Interactive Job Cards:** Clean dark theme with clear metadata badges and direct application buttons (`Apply on LinkedIn ↗`).
- **Live Summary Metrics:** Real-time counts for Total Jobs, Unique Companies, Internships, and Remote positions.
- **Arabic-Compliant Excel / CSV Export:** One-click download formatted with `UTF-8 with BOM` encoding for seamless Arabic text rendering in Microsoft Excel.
- **Real-Time Cache Invalidation:** Automatically clears stale results the moment any search filter or keyword changes.

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/0xQenawy/job-scrabbing.git
cd job-scaraping
pip install -r requirements.txt
```

### 2. Run the Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`, set your desired role and location, and click **شوفلي الشغل يا عماد**.

---

## 📁 Project Structure

```text
job-scaraping/
├── app.py             # Streamlit web application, state management, and modern job cards UI
├── scraper.py         # Precision LinkedIn scraping engine (LinkedInScraper) & classification (JobClassifier)
├── requirements.txt   # Dependencies (streamlit, requests, beautifulsoup4, pandas)
└── README.md          # Project documentation and guide
```

---

## 💡 Best Practices for Optimal Search Results
- **Looking for an Internship?** Enter only the core discipline (e.g., `Flutter` or `Python`) and select `Internship (تدريب طلبة وخريجين)`. Emad will automatically discard any postings requiring prior experience.
- **Multi-Role Searches:** Separate multiple roles with a comma (e.g., `Data Analyst, Business Intelligence`).
- **Target Fresh Postings:** Applying to roles posted within the **past 24 hours** or **past week** significantly boosts profile visibility with recruiters.
