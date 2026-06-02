"""
Main entry point for the garage complaint analysis agent.
Processes customer complaints and recommends the best garage.
"""
from src.models.complaint import Complaint
from src.agent.complaint_analyzer import ComplaintAnalyzer
from src.agent.garage_recommender import GarageRecommender
from src.utils.data_loader import load_vehicle_repair_data, load_sample_garages


def main():
    """Run the complaint analysis agent."""
    
    print("🚗 Garage Complaint Analysis Agent")
    print("=" * 70)
    
    # Load historical repair data from JSON
    # In production, load from: data/vehicle-repair-data.json
    print("\n📊 Loading historical repair data...")
    
    # Sample historical repairs for demonstration
    # Replace with: with open('data/vehicle-repair-data.json') as f: json_data = json.load(f)
    sample_historical_data = [
        {
            "repair_id": "REP-0001",
            "customer_description": "There's a grinding noise when I press the brakes, especially at low speed.",
            "fault_category": "brakes",
            "urgency": "drive-to-nearest",
            "parts_needed": ["front brake pads x2", "brake disc x2"],
            "resolution_time_hours": 2.0
        },
        {
            "repair_id": "REP-0002",
            "customer_description": "My car won't start in the morning. I hear a clicking sound when I turn the key.",
            "fault_category": "electrical",
            "urgency": "do-not-drive",
            "parts_needed": ["12V battery 70Ah"],
            "resolution_time_hours": 1.0
        },
        {
            "repair_id": "REP-0003",
            "customer_description": "The temperature gauge is going into the red and steam from under the bonnet.",
            "fault_category": "cooling",
            "urgency": "do-not-drive",
            "parts_needed": ["lower radiator hose", "coolant 5L"],
            "resolution_time_hours": 2.5
        },
    ]
    
    historical_repairs = load_vehicle_repair_data(sample_historical_data)
    garages = load_sample_garages()
    print(f"✓ Loaded {len(historical_repairs)} historical repair cases")
    print(f"✓ Loaded {len(garages)} garages in the network")
    
    # Initialize analyzer and recommender
    print("\n🔧 Initializing analysis engine...")
    analyzer = ComplaintAnalyzer(historical_repairs)
    recommender = GarageRecommender(garages)
    print("✓ Systems ready")
    
    # Example complaints to analyze
    test_complaints = [
        Complaint(
            complaint_id="CUST-001",
            text="My car won't stop properly. The brake pedal goes almost to the floor and I'm very worried about safety."
        ),
        Complaint(
            complaint_id="CUST-002",
            text="The car is making a squealing noise when I brake in the morning and feels a bit soft."
        ),
        Complaint(
            complaint_id="CUST-003",
            text="My headlights are very dim and the battery warning light turned on."
        ),
        Complaint(
            complaint_id="CUST-004",
            text="Engine is running rough and shaking when I idle. Check engine light is on."
        ),
    ]
    
    # Analyze each complaint
    for i, complaint in enumerate(test_complaints, 1):
        print("\n" + "=" * 70)
        print(f"COMPLAINT #{i}: {complaint.complaint_id}")
        print("-" * 70)
        print(f"Customer says: {complaint.text}\n")
        
        # Analyze the complaint
        analysis = analyzer.analyze(complaint)
        
        # Get garage recommendations
        garage_recs = recommender.recommend_garage(analysis)
        
        # Print formatted recommendation
        print(recommender.format_recommendation(analysis, garage_recs, top_n=3))
    
    print("\n" + "=" * 70)
    print("✓ Analysis complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
