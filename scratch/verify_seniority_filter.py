import sys
sys.path.insert(0, r"c:\Users\ABDELRAHMAN GAMAL\Desktop\job-scaraping")
from scraper import JobClassifier, LinkedInScraper

def test_seniority_filter():
    print("=" * 60)
    print("TESTING SENIORITY LEVEL ACCURACY & FILTERING")
    print("=" * 60)

    # 1. Entry / Junior Tests
    print("\n--- 1. Testing Entry / Junior Level Filter ---")
    assert JobClassifier.passes_hard_filter("Junior Python Developer", "Company A", "python", requested_seniority="entry") == True
    assert JobClassifier.passes_hard_filter("Associate Software Engineer", "Company B", "software", requested_seniority="entry") == True
    assert JobClassifier.passes_hard_filter("Fresh Graduate Data Analyst", "Company C", "data", requested_seniority="entry") == True
    assert JobClassifier.passes_hard_filter("Junior Flutter Developer (1-2 years)", "Company D", "flutter", requested_seniority="entry") == True
    # MUST REJECT seniors, leads, architects, and high experience
    assert JobClassifier.passes_hard_filter("Senior Software Engineer", "Company E", "software", requested_seniority="entry") == False
    assert JobClassifier.passes_hard_filter("Lead Backend Engineer", "Company F", "backend", requested_seniority="entry") == False
    assert JobClassifier.passes_hard_filter("Cloud Solutions Architect", "Company G", "cloud", requested_seniority="entry") == False
    assert JobClassifier.passes_hard_filter("Python Developer (3+ years experience)", "Company H", "python", requested_seniority="entry") == False
    assert JobClassifier.passes_hard_filter("Flutter Developer (5 years experience)", "Company I", "flutter", requested_seniority="entry") == False
    assert JobClassifier.passes_hard_filter("Engineering Manager", "Company J", "engineer", requested_seniority="entry") == False
    assert JobClassifier.passes_hard_filter("Summer Intern", "Company K", "summer", requested_seniority="entry") == False
    print("PASS: Entry / Junior level strictly accepts entry roles and rejects Senior/Lead/Architect/3+ years!")

    # 2. Senior / Lead Tests
    print("\n--- 2. Testing Senior / Lead Level Filter ---")
    assert JobClassifier.passes_hard_filter("Senior Python Developer", "Company A", "python", requested_seniority="senior") == True
    assert JobClassifier.passes_hard_filter("Lead Backend Engineer", "Company B", "backend", requested_seniority="senior") == True
    assert JobClassifier.passes_hard_filter("Cloud Solutions Architect", "Company C", "cloud", requested_seniority="senior") == True
    assert JobClassifier.passes_hard_filter("Python Developer (5 years experience)", "Company D", "python", requested_seniority="senior") == True
    assert JobClassifier.passes_hard_filter("Principal Engineer", "Company E", "engineer", requested_seniority="senior") == True
    # MUST REJECT junior, intern, and generic non-senior roles
    assert JobClassifier.passes_hard_filter("Junior Python Developer", "Company F", "python", requested_seniority="senior") == False
    assert JobClassifier.passes_hard_filter("Python Intern", "Company G", "python", requested_seniority="senior") == False
    assert JobClassifier.passes_hard_filter("Fresh Graduate Software Engineer", "Company H", "software", requested_seniority="senior") == False
    assert JobClassifier.passes_hard_filter("Software Engineer", "Company I", "software", requested_seniority="senior") == False
    print("PASS: Senior level strictly accepts Senior/Lead/Architect/5+ years and rejects Juniors/Interns/Generic!")

    # 3. Mid-Level Tests
    print("\n--- 3. Testing Mid Level Filter ---")
    assert JobClassifier.passes_hard_filter("Mid-Level Python Developer", "Company A", "python", requested_seniority="mid") == True
    assert JobClassifier.passes_hard_filter("Python Developer", "Company B", "python", requested_seniority="mid") == True
    assert JobClassifier.passes_hard_filter("Junior Python Developer", "Company C", "python", requested_seniority="mid") == False
    assert JobClassifier.passes_hard_filter("Python Intern", "Company D", "python", requested_seniority="mid") == False
    assert JobClassifier.passes_hard_filter("VP of Engineering", "Company E", "engineer", requested_seniority="mid") == False
    print("PASS: Mid level strictly rejects Juniors, Interns, and Executives!")

    # 4. Director / Manager Tests
    print("\n--- 4. Testing Director / Manager Filter ---")
    assert JobClassifier.passes_hard_filter("Engineering Manager", "Company A", "engineer", requested_seniority="director") == True
    assert JobClassifier.passes_hard_filter("Director of Product", "Company B", "product", requested_seniority="director") == True
    assert JobClassifier.passes_hard_filter("Head of Data", "Company C", "data", requested_seniority="director") == True
    assert JobClassifier.passes_hard_filter("Junior Developer", "Company D", "developer", requested_seniority="director") == False
    assert JobClassifier.passes_hard_filter("Senior Developer", "Company E", "developer", requested_seniority="director") == False
    print("PASS: Director/Manager level strictly matches leadership roles!")

    # 5. Normalization Tests
    print("\n--- 5. Testing normalize_search_intent with Seniority ---")
    kws, jt, sen = JobClassifier.normalize_search_intent(["Senior Python Developer"])
    assert sen == "senior" and kws[0].lower() == "python developer", f"Got {sen}, {kws}"

    kws, jt, sen = JobClassifier.normalize_search_intent(["Junior Flutter Developer"])
    assert sen == "entry" and kws[0].lower() == "flutter developer", f"Got {sen}, {kws}"

    kws, jt, sen = JobClassifier.normalize_search_intent(["Data Analyst"], seniority="entry")
    assert sen == "entry" and kws[0].lower() == "data analyst", f"Got {sen}, {kws}"
    print("PASS: normalize_search_intent properly resolves seniority intent!")

    print("\n" + "=" * 60)
    print("ALL 5 SENIORITY TEST SUITES PASSED WITH 100% ACCURACY!")
    print("=" * 60)

if __name__ == "__main__":
    test_seniority_filter()
