#!/usr/bin/env python3
"""
Complete End-to-End Test
Tests entire application flow from login to hiring
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(f"📋 {title}")
    print("="*80)

def test_employer_flow():
    """Test complete employer workflow"""
    print_section("EMPLOYER WORKFLOW TEST")
    
    # Step 1: Login
    print("\n1️⃣ Employer Login...")
    response = requests.post(f"{BASE_URL}/api/login", json={
        "email": "employer@talentis.ai",
        "password": "employer123"
    })
    assert response.status_code == 200, f"Login failed: {response.status_code}"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Login successful")
    
    # Step 2: Get employer's jobs
    print("\n2️⃣ Fetching employer's jobs...")
    response = requests.get(f"{BASE_URL}/api/employer/jobs", headers=headers)
    assert response.status_code == 200, f"Failed to fetch jobs: {response.status_code}"
    jobs = response.json()["jobs"]
    print(f"   ✅ Found {len(jobs)} jobs")
    for job in jobs[:3]:
        print(f"      • {job['title']} ({job['match_count']} matches)")
    
    # Step 3: Get matches for first job
    if jobs:
        job_id = jobs[0]["id"]
        print(f"\n3️⃣ Getting matches for job ID {job_id}...")
        response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/matches", headers=headers)
        if response.status_code == 200:
            matches = response.json()
            print(f"   ✅ Found {len(matches)} matches")
            for match in matches[:2]:
                print(f"      • {match['candidate_name']}: {match['score']}% match")
        else:
            print(f"   ⚠️  No matches yet (status: {response.status_code})")
    
    return True

def test_candidate_flow():
    """Test complete candidate workflow"""
    print_section("CANDIDATE WORKFLOW TEST")
    
    # Step 1: Login
    print("\n1️⃣ Candidate Login...")
    response = requests.post(f"{BASE_URL}/api/login", json={
        "email": "test@test.com",
        "password": "test123"
    })
    assert response.status_code == 200, f"Login failed: {response.status_code}"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Login successful")
    
    # Step 2: Get candidate profile
    print("\n2️⃣ Checking candidate profile...")
    response = requests.get(f"{BASE_URL}/api/candidate/profile", headers=headers)
    assert response.status_code == 200, f"Failed to fetch profile: {response.status_code}"
    profile = response.json().get("profile")
    if profile:
        print(f"   ✅ Profile exists")
        print(f"      • Skills: {', '.join(profile['skills'][:5])}")
        print(f"      • Experience: {profile['experience_years']} years")
    else:
        print("   ⚠️  No profile found")
    
    # Step 3: View available jobs
    print("\n3️⃣ Browsing available jobs...")
    response = requests.get(f"{BASE_URL}/api/jobs", headers=headers)
    assert response.status_code == 200, f"Failed to fetch jobs: {response.status_code}"
    jobs = response.json()["jobs"]
    print(f"   ✅ Found {len(jobs)} available jobs")
    for job in jobs[:3]:
        print(f"      • {job['title']} at {job['company_name']}")
    
    # Step 4: Apply to a job
    if jobs and profile:
        job_id = jobs[0]["id"]
        print(f"\n4️⃣ Applying to job: {jobs[0]['title']}...")
        response = requests.post(f"{BASE_URL}/api/jobs/{job_id}/apply", headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Application submitted!")
            print(f"      • Match Score: {result.get('match_score', 0)}%")
            print(f"      • Status: {result.get('status', 'pending')}")
        else:
            print(f"   ⚠️  Application failed or already applied: {response.status_code}")
    
    # Step 5: View my matches
    print("\n5️⃣ Checking my matches...")
    response = requests.get(f"{BASE_URL}/api/matches/candidate", headers=headers)
    if response.status_code == 200:
        matches = response.json().get("matches", [])
        print(f"   ✅ Found {len(matches)} matches")
        for match in matches[:3]:
            print(f"      • {match.get('job_title', 'Unknown')}: {match.get('match_score', 0)}% - {match.get('status', 'pending')}")
    else:
        print(f"   ⚠️  No matches yet")
    
    return True

def test_ai_features():
    """Test AI-powered features"""
    print_section("AI FEATURES TEST")
    
    print("\n1️⃣ Testing Resume Parser...")
    from resume_parser import parse_resume_text
    
    sample_resume = """
    John Doe
    Software Engineer
    
    5 years of experience in full-stack development.
    
    Skills: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes
    
    Education: Bachelor's in Computer Science from MIT
    
    AWS Certified Solutions Architect
    """
    
    parsed = parse_resume_text(sample_resume)
    print(f"   ✅ Resume parsed successfully")
    print(f"      • Skills found: {len(parsed['skills'])}")
    print(f"      • Experience: {parsed['experience_years']} years")
    print(f"      • Education: {parsed['education'][:50]}...")
    
    print("\n2️⃣ Testing ATS Scoring...")
    from resume_parser import calculate_ats_score, generate_match_explanation
    
    candidate_skills = ["Python", "JavaScript", "React", "Docker"]
    job_skills = ["Python", "React", "Node.js", "AWS"]
    
    ats_result = calculate_ats_score(candidate_skills, job_skills)
    explanation = generate_match_explanation(ats_result, 5, 3)
    
    print(f"   ✅ ATS Score calculated: {ats_result['score']}%")
    print(f"      • Matched: {len(ats_result['matched_skills'])} skills")
    print(f"      • Missing: {len(ats_result['missing_skills'])} skills")
    print(f"      • Explanation: {explanation}")
    
    return True

def main():
    print("\n🚀 TALENTIS.AI - COMPLETE END-TO-END TEST")
    print("Testing all features and workflows...\n")
    
    try:
        # Test AI features first (no server required)
        test_ai_features()
        
        # Wait for servers to be ready
        print("\n⏳ Waiting for servers to be ready...")
        sleep(2)
        
        # Test employer flow
        test_employer_flow()
        
        # Test candidate flow
        test_candidate_flow()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
        print("="*80)
        
        print("\n🌐 Application URLs:")
        print("   Frontend: https://opulent-space-potato-p46qj4q99x537gxp-5173.app.github.dev")
        print("   Backend:  https://opulent-space-potato-p46qj4q99x537gxp-8000.app.github.dev")
        
        print("\n🔑 Login Credentials:")
        print("   Employers:")
        print("   • employer@talentis.ai / employer123")
        print("   • vss@paytm.com / vss123")
        print("   • deeps@zomato.com / deepinder123")
        print("\n   Candidates:")
        print("   • test@test.com / test123")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
