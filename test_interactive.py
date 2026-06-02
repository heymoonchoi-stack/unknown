"""
Interactive test script for the garage complaint analysis agent.
Run this to test the agent with real complaints.
"""
import json
from src.models.complaint import Complaint
from src.agent.complaint_analyzer import ComplaintAnalyzer
from src.agent.garage_recommender import GarageRecommender
from src.utils.data_loader import load_vehicle_repair_data, load_sample_garages


def load_repair_data_from_file():
    """Load repair data from vehicle-repair-data.json"""
    try:
        with open('data/vehicle-repair-data.json', 'r') as f:
            json_data = json.load(f)
        return load_vehicle_repair_data(json_data)
    except FileNotFoundError:
        print("❌ Error: data/vehicle-repair-data.json not found")
        print("Please ensure the file exists in the data/ folder")
        return []


def run_interactive_test():
    """Run interactive test mode for the complaint analyzer."""
    
    print("\n" + "="*80)
    print("🚗 GARAGE COMPLAINT ANALYSIS AGENT - INTERACTIVE TEST")
    print("="*80)
    
    # Load data
    print("\n📊 Loading repair history...")
    historical_repairs = load_repair_data_from_file()
    
    if not historical_repairs:
        print("⚠️  No repair data loaded. Exiting.")
        return
    
    garages = load_sample_garages()
    print(f"✓ Loaded {len(historical_repairs)} repair cases")
    print(f"✓ Loaded {len(garages)} garages")
    
    # Initialize systems
    print("\n🔧 Initializing analysis engine...")
    analyzer = ComplaintAnalyzer(historical_repairs)
    recommender = GarageRecommender(garages)
    print("✓ Systems ready\n")
    
    # Predefined test cases
    test_cases = [
        {
            "id": "1",
            "title": "Brake Failure - CRITICAL",
            "text": "My car won't stop properly. The brake pedal goes almost to the floor and I'm very worried about safety."
        },
        {
            "id": "2",
            "title": "Brake Noise - HIGH",
            "text": "There's a grinding noise when I press the brakes, especially at low speed. It started about a week ago."
        },
        {
            "id": "3",
            "title": "Won't Start - ELECTRICAL",
            "text": "My car won't start in the morning. I hear a clicking sound when I turn the key but the engine doesn't turn over."
        },
        {
            "id": "4",
            "title": "Overheating - CRITICAL",
            "text": "The temperature gauge is going into the red and I can see steam coming from under the bonnet. I pulled over immediately."
        },
        {
            "id": "5",
            "title": "Engine Warning Light - MODERATE",
            "text": "There's a yellow warning light shaped like an engine on my dashboard. The car seems fine but the light has been on for days."
        },
        {
            "id": "6",
            "title": "Steering Pull - MODERATE",
            "text": "The car is pulling to the left when I drive on a straight road. I have to hold the steering wheel to one side."
        },
        {
            "id": "7",
            "title": "Brake Burning Smell - HIGH",
            "text": "I can smell something burning when I stop after a long drive. It's like hot plastic or rubber."
        },
        {
            "id": "8",
            "title": "AC Not Working - MODERATE",
            "text": "My air conditioning stopped blowing cold air. It just blows normal temperature air now."
        },
        {
            "id": "9",
            "title": "Engine Misfiring - MODERATE",
            "text": "The car jerks and stutters when I accelerate. It feels like the engine is misfiring."
        },
        {
            "id": "10",
            "title": "Engine Knocking - MODERATE",
            "text": "There's a knocking sound from the engine when I first start it. It goes away after a minute."
        }
    ]
    
    print("Available test cases:")
    print("-" * 80)
    for case in test_cases:
        print(f"  {case['id']}. {case['title']}")
    print(f"  a. Run all test cases")
    print(f"  c. Enter custom complaint")
    print(f"  q. Quit")
    print("-" * 80)
    
    while True:
        choice = input("\nSelect test case (1-10/a/c/q): ").strip().lower()
        
        if choice == 'q':
            print("\n👋 Goodbye!")
            break
        
        elif choice == 'a':
            # Run all test cases
            run_all_tests(test_cases, analyzer, recommender)
        
        elif choice == 'c':
            # Custom complaint
            complaint_text = input("\nEnter your complaint: ").strip()
            if complaint_text:
                complaint = Complaint(
                    complaint_id="CUSTOM-001",
                    text=complaint_text
                )
                process_complaint(complaint, analyzer, recommender)
        
        elif choice in [str(i) for i in range(1, 11)]:
            # Specific test case
            test_case = test_cases[int(choice) - 1]
            complaint = Complaint(
                complaint_id=f"TEST-{test_case['id']}",
                text=test_case['text']
            )
            process_complaint(complaint, analyzer, recommender)
        
        else:
            print("❌ Invalid choice. Please try again.")


def run_all_tests(test_cases, analyzer, recommender):
    """Run all test cases."""
    print("\n" + "="*80)
    print("🧪 RUNNING ALL TEST CASES")
    print("="*80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}]", end=" ")
        complaint = Complaint(
            complaint_id=f"TEST-{test_case['id']}",
            text=test_case['text']
        )
        process_complaint(complaint, analyzer, recommender, show_similar_cases=False)
        input("\nPress Enter for next complaint...")


def process_complaint(complaint, analyzer, recommender, show_similar_cases=True):
    """Process and display results for a single complaint."""
    
    print("\n" + "="*80)
    print(f"📋 COMPLAINT: {complaint.complaint_id}")
    print("="*80)
    print(f"\n📝 Customer says:\n{complaint.text}\n")
    
    # Analyze
    print("🔍 Analyzing complaint...")
    analysis = analyzer.analyze(complaint)
    
    # Get recommendations
    print("🏪 Recommending garages...\n")
    garage_recs = recommender.recommend_garage(analysis)
    
    # Display results
    print(recommender.format_recommendation(analysis, garage_recs, top_n=3))
    
    # Show similar cases if requested
    if show_similar_cases and analysis.similar_cases:
        print("\n" + "-"*80)
        print("📊 Similar Historical Cases Used for Analysis:")
        print("-"*80)
        for i, case in enumerate(analysis.similar_cases, 1):
            print(f"\n  {i}. Case ID: {case.case_id}")
            print(f"     Problem: {case.problem_type}")
            print(f"     Urgency: {case.urgency.value.upper()}")
            print(f"     Parts: {', '.join(case.parts_needed) if case.parts_needed else 'None'}")
            print(f"     Time: {case.repair_duration_hours} hours")


if __name__ == "__main__":
    run_interactive_test()
