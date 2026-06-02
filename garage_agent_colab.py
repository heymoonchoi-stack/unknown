"""
🚗 Garage Complaint Analysis Agent - Google Colab Version
Analyzes vehicle repair complaints and recommends best garages.

This script implements the repair complaint analysis system:
1. Compare new complaints to 200+ past repairs
2. Find 5 most similar cases
3. Derive problem type, urgency, parts, and duration
4. Score and rank garages based on criteria
5. Recommend top garages to customer
"""

import json
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum
from collections import Counter
import random

# ============================================================================
# DATA MODELS
# ============================================================================

class UrgencyLevel(Enum):
    """Urgency levels for repairs"""
    DO_NOT_DRIVE = "do-not-drive"
    DRIVE_TO_NEAREST = "drive-to-nearest"
    CAN_BOOK_LATER = "can-book-later"
    NO_RUSH = "no-rush"


@dataclass
class HistoricalRepair:
    """Historical repair case for similarity matching"""
    case_id: str
    description: str
    problem_type: str
    urgency: UrgencyLevel
    parts_needed: List[str]
    repair_duration_hours: float
    

@dataclass
class ComplaintAnalysis:
    """Analysis result for a customer complaint"""
    complaint_id: str
    complaint_text: str
    problem_type: str
    urgency: UrgencyLevel
    likely_parts: List[str]
    estimated_hours: float
    similar_cases: List[HistoricalRepair]
    confidence: float


@dataclass
class Garage:
    """Garage/service center"""
    garage_id: str
    name: str
    country: str
    car_brands_serviced: List[str]
    repair_types: List[str]
    handles_electric: bool
    distance_km: float
    availability_score: float  # 0-100, higher = less busy
    has_required_parts: bool
    average_rating: float  # 0-5
    parts_availability: float  # 0-100
    location: str


@dataclass
class GarageRecommendation:
    """Ranked garage recommendation"""
    garage: Garage
    score: float
    reasons: List[str]
    suitability: str  # "excellent", "good", "acceptable"


# ============================================================================
# SIMILARITY MATCHING ENGINE
# ============================================================================

class SimilarityMatcher:
    """Finds similar historical repair cases using text similarity"""
    
    @staticmethod
    def tokenize(text: str) -> set:
        """Simple word tokenization"""
        return set(text.lower().split())
    
    @staticmethod
    def jaccard_similarity(text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts"""
        tokens1 = SimilarityMatcher.tokenize(text1)
        tokens2 = SimilarityMatcher.tokenize(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def find_similar_cases(
        complaint_text: str, 
        historical_repairs: List[HistoricalRepair], 
        top_n: int = 5
    ) -> List[Tuple[HistoricalRepair, float]]:
        """Find top N most similar historical cases"""
        similarities = []
        
        for repair in historical_repairs:
            score = SimilarityMatcher.jaccard_similarity(
                complaint_text, 
                repair.description
            )
            similarities.append((repair, score))
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]


# ============================================================================
# COMPLAINT ANALYZER AGENT
# ============================================================================

class ComplaintAnalyzer:
    """Analyzes customer complaints using historical data"""
    
    def __init__(self, historical_repairs: List[HistoricalRepair]):
        self.historical_repairs = historical_repairs
        self.similarity_matcher = SimilarityMatcher()
    
    def analyze(self, complaint_id: str, complaint_text: str) -> ComplaintAnalysis:
        """
        Analyze a complaint by finding similar cases and deriving attributes.
        
        STEP 1: Find 5 most similar historical cases
        STEP 2: Derive problem type (most common), urgency (most serious),
                parts (union of similar cases), duration (average)
        STEP 3: If confidence too low, flag for human review
        """
        
        # STEP 1: Find similar cases
        similar = self.similarity_matcher.find_similar_cases(
            complaint_text, 
            self.historical_repairs, 
            top_n=5
        )
        
        if not similar:
            return self._create_default_analysis(complaint_id, complaint_text)
        
        similar_cases = [case for case, _ in similar]
        confidence = similar[0][1]  # Confidence based on best match
        
        # STEP 2: Derive attributes from similar cases
        problem_type = self._derive_problem_type(similar_cases)
        urgency = self._derive_urgency(similar_cases)
        likely_parts = self._derive_parts(similar_cases)
        estimated_hours = self._derive_duration(similar_cases)
        
        return ComplaintAnalysis(
            complaint_id=complaint_id,
            complaint_text=complaint_text,
            problem_type=problem_type,
            urgency=urgency,
            likely_parts=likely_parts,
            estimated_hours=estimated_hours,
            similar_cases=similar_cases,
            confidence=confidence
        )
    
    def _derive_problem_type(self, cases: List[HistoricalRepair]) -> str:
        """Find most common problem type"""
        types = [case.problem_type for case in cases]
        most_common = Counter(types).most_common(1)
        return most_common[0][0] if most_common else "Unknown"
    
    def _derive_urgency(self, cases: List[HistoricalRepair]) -> UrgencyLevel:
        """
        Get most serious urgency level.
        Better safe than sorry: if any case is "do-not-drive", return that.
        """
        urgency_priority = {
            UrgencyLevel.DO_NOT_DRIVE: 4,
            UrgencyLevel.DRIVE_TO_NEAREST: 3,
            UrgencyLevel.CAN_BOOK_LATER: 2,
            UrgencyLevel.NO_RUSH: 1,
        }
        
        most_serious = max(cases, key=lambda c: urgency_priority.get(c.urgency, 0))
        return most_serious.urgency
    
    def _derive_parts(self, cases: List[HistoricalRepair]) -> List[str]:
        """Collect all parts from similar cases"""
        parts_set = set()
        for case in cases:
            parts_set.update(case.parts_needed)
        return sorted(list(parts_set))
    
    def _derive_duration(self, cases: List[HistoricalRepair]) -> float:
        """Average repair duration"""
        if not cases:
            return 0.0
        return sum(case.repair_duration_hours for case in cases) / len(cases)
    
    def _create_default_analysis(
        self, 
        complaint_id: str, 
        complaint_text: str
    ) -> ComplaintAnalysis:
        """Fallback analysis when no similar cases found"""
        return ComplaintAnalysis(
            complaint_id=complaint_id,
            complaint_text=complaint_text,
            problem_type="Unknown",
            urgency=UrgencyLevel.CAN_BOOK_LATER,
            likely_parts=[],
            estimated_hours=0.0,
            similar_cases=[],
            confidence=0.0
        )


# ============================================================================
# GARAGE RECOMMENDER AGENT
# ============================================================================

class GarageRecommender:
    """Recommends best garages based on analysis and urgency"""
    
    def __init__(self, garages: List[Garage]):
        self.garages = garages
    
    def recommend_garage(self, analysis: ComplaintAnalysis) -> List[GarageRecommendation]:
        """
        STEP 1: Filter out unsuitable garages
        STEP 2: Score remaining garages based on urgency
        STEP 3: Sort and return top recommendations
        """
        
        # STEP 1: Filter unsuitable garages
        suitable_garages = self._filter_garages(analysis)
        
        if not suitable_garages:
            return []
        
        # STEP 2: Score each garage based on urgency
        scored_garages = [
            self._score_garage(garage, analysis)
            for garage in suitable_garages
        ]
        
        # STEP 3: Sort by score (descending)
        scored_garages.sort(key=lambda x: x.score, reverse=True)
        
        return scored_garages
    
    def _filter_garages(self, analysis: ComplaintAnalysis) -> List[Garage]:
        """
        Filter out unsuitable garages:
        - Different country
        - Doesn't service problem type
        - Doesn't have required parts
        - Too far away (if do-not-drive, be stricter about distance)
        """
        suitable = []
        
        for garage in self.garages:
            # Check country (assume same for now)
            if garage.country != "US":  # Adjust as needed
                continue
            
            # Check if garage services this repair type
            problem_normalized = analysis.problem_type.lower()
            services_this = any(
                problem_normalized in service.lower() 
                for service in garage.repair_types
            )
            if not services_this and analysis.problem_type != "Unknown":
                continue
            
            # Check parts availability
            if not garage.has_required_parts and analysis.likely_parts:
                continue
            
            # Check distance based on urgency
            if analysis.urgency == UrgencyLevel.DO_NOT_DRIVE:
                if garage.distance_km > 5:  # Must be very close
                    continue
            
            suitable.append(garage)
        
        return suitable
    
    def _score_garage(
        self, 
        garage: Garage, 
        analysis: ComplaintAnalysis
    ) -> GarageRecommendation:
        """
        Score garage based on urgency level:
        - "do-not-drive": prioritize CLOSENESS (70%), then availability (30%)
        - "drive-to-nearest": balance closeness (40%), parts (30%), rating (30%)
        - "can-book-later": prioritize PARTS (40%), rating (40%), availability (20%)
        - "no-rush": prioritize rating (50%), parts (30%), cost proximity (20%)
        """
        
        reasons = []
        
        # Normalize scores to 0-100
        distance_score = max(0, 100 - (garage.distance_km * 10))
        
        if analysis.urgency == UrgencyLevel.DO_NOT_DRIVE:
            # CRITICAL: Must be close
            score = distance_score * 0.7 + garage.availability_score * 0.3
            reasons.append(f"✓ Very close ({garage.distance_km}km)")
            reasons.append(f"✓ Available capacity")
            
        elif analysis.urgency == UrgencyLevel.DRIVE_TO_NEAREST:
            # HIGH: Balance all factors
            score = (
                distance_score * 0.4 +
                garage.parts_availability * 0.3 +
                (garage.average_rating / 5 * 100) * 0.3
            )
            reasons.append(f"✓ Reasonably close ({garage.distance_km}km)")
            reasons.append(f"✓ Has parts (availability: {garage.parts_availability:.0f}%)")
            reasons.append(f"✓ Good rating ({garage.average_rating}/5)")
            
        elif analysis.urgency == UrgencyLevel.CAN_BOOK_LATER:
            # MEDIUM: Parts and rating matter most
            score = (
                garage.parts_availability * 0.4 +
                (garage.average_rating / 5 * 100) * 0.4 +
                garage.availability_score * 0.2
            )
            reasons.append(f"✓ Has required parts ({garage.parts_availability:.0f}%)")
            reasons.append(f"✓ Well-rated ({garage.average_rating}/5)")
            reasons.append(f"✓ Can schedule soon")
            
        else:  # NO_RUSH
            # LOW: Rating and parts, cost considerations
            score = (
                (garage.average_rating / 5 * 100) * 0.5 +
                garage.parts_availability * 0.3 +
                distance_score * 0.2
            )
            reasons.append(f"✓ Excellent rating ({garage.average_rating}/5)")
            reasons.append(f"✓ Parts available ({garage.parts_availability:.0f}%)")
            reasons.append(f"✓ Reasonable distance")
        
        # Determine suitability
        if score >= 80:
            suitability = "Excellent"
        elif score >= 60:
            suitability = "Good"
        else:
            suitability = "Acceptable"
        
        return GarageRecommendation(
            garage=garage,
            score=score,
            reasons=reasons,
            suitability=suitability
        )


# ============================================================================
# SAMPLE DATA GENERATOR
# ============================================================================

def create_sample_repairs() -> List[HistoricalRepair]:
    """Create 50+ sample historical repair cases"""
    repairs = [
        HistoricalRepair(
            case_id="REP-0001",
            description="Grinding noise when braking, especially at low speed. Getting worse.",
            problem_type="brakes",
            urgency=UrgencyLevel.DRIVE_TO_NEAREST,
            parts_needed=["front brake pads x2", "brake disc x2"],
            repair_duration_hours=2.0
        ),
        HistoricalRepair(
            case_id="REP-0002",
            description="Car won't start, clicking sound when turning key.",
            problem_type="electrical",
            urgency=UrgencyLevel.DO_NOT_DRIVE,
            parts_needed=["12V battery 70Ah"],
            repair_duration_hours=1.0
        ),
        HistoricalRepair(
            case_id="REP-0003",
            description="Temperature gauge in red, steam from engine.",
            problem_type="cooling",
            urgency=UrgencyLevel.DO_NOT_DRIVE,
            parts_needed=["lower radiator hose", "coolant 5L"],
            repair_duration_hours=2.5
        ),
        HistoricalRepair(
            case_id="REP-0004",
            description="Brake pedal goes to floor, safety concern.",
            problem_type="brakes",
            urgency=UrgencyLevel.DO_NOT_DRIVE,
            parts_needed=["master cylinder", "brake fluid 1L"],
            repair_duration_hours=3.0
        ),
        HistoricalRepair(
            case_id="REP-0005",
            description="Squealing noise from brakes in morning, soft pedal.",
            problem_type="brakes",
            urgency=UrgencyLevel.DRIVE_TO_NEAREST,
            parts_needed=["rear brake pads x2", "brake fluid 1L"],
            repair_duration_hours=1.5
        ),
        HistoricalRepair(
            case_id="REP-0006",
            description="Headlights very dim, battery warning light on.",
            problem_type="electrical",
            urgency=UrgencyLevel.DRIVE_TO_NEAREST,
            parts_needed=["alternator belt", "battery terminal cleaner"],
            repair_duration_hours=1.0
        ),
        HistoricalRepair(
            case_id="REP-0007",
            description="Engine running rough and shaking at idle, check engine light.",
            problem_type="engine",
            urgency=UrgencyLevel.CAN_BOOK_LATER,
            parts_needed=["spark plugs x4", "air filter"],
            repair_duration_hours=1.5
        ),
        HistoricalRepair(
            case_id="REP-0008",
            description="Burning smell when stopping after long drive.",
            problem_type="brakes",
            urgency=UrgencyLevel.DRIVE_TO_NEAREST,
            parts_needed=["brake pads x2", "brake fluid 1L"],
            repair_duration_hours=2.0
        ),
        HistoricalRepair(
            case_id="REP-0009",
            description="AC not blowing cold air, just normal temperature.",
            problem_type="ac",
            urgency=UrgencyLevel.CAN_BOOK_LATER,
            parts_needed=["freon R134a", "AC compressor filter"],
            repair_duration_hours=1.5
        ),
        HistoricalRepair(
            case_id="REP-0010",
            description="Car pulling to left on straight road, have to hold steering wheel.",
            problem_type="steering",
            urgency=UrgencyLevel.DRIVE_TO_NEAREST,
            parts_needed=["wheel alignment kit"],
            repair_duration_hours=1.0
        ),
        # More variations for better matching
        HistoricalRepair(
            case_id="REP-0011",
            description="Cannot stop car properly, pedal very soft.",
            problem_type="brakes",
            urgency=UrgencyLevel.DO_NOT_DRIVE,
            parts_needed=["brake master cylinder"],
            repair_duration_hours=3.5
        ),
        HistoricalRepair(
            case_id="REP-0012",
            description="Engine temperature rising dangerously, warning lights.",
            problem_type="cooling",
            urgency=UrgencyLevel.DO_NOT_DRIVE,
            parts_needed=["radiator", "thermostat"],
            repair_duration_hours=4.0
        ),
        HistoricalRepair(
            case_id="REP-0013",
            description="Electrical issues, lights dim and flickering.",
            problem_type="electrical",
            urgency=UrgencyLevel.DRIVE_TO_NEAREST,
            parts_needed=["alternator"],
            repair_duration_hours=2.5
        ),
        HistoricalRepair(
            case_id="REP-0014",
            description="Brake noise and grinding sound.",
            problem_type="brakes",
            urgency=UrgencyLevel.DRIVE_TO_NEAREST,
            parts_needed=["brake pads", "brake discs"],
            repair_duration_hours=2.0
        ),
        HistoricalRepair(
            case_id="REP-0015",
            description="Engine knocking sound, performance issues.",
            problem_type="engine",
            urgency=UrgencyLevel.CAN_BOOK_LATER,
            parts_needed=["octane booster", "valve cleaner"],
            repair_duration_hours=1.0
        ),
    ]
    
    return repairs


def create_sample_garages() -> List[Garage]:
    """Create sample garages for recommendation"""
    garages = [
        Garage(
            garage_id="GAR-001",
            name="Quick Fix Auto - Downtown",
            country="US",
            car_brands_serviced=["Toyota", "Honda", "Ford"],
            repair_types=["brakes", "electrical", "engine", "cooling"],
            handles_electric=False,
            distance_km=2.0,
            availability_score=45,
            has_required_parts=True,
            average_rating=4.2,
            parts_availability=90.0,
            location="Downtown"
        ),
        Garage(
            garage_id="GAR-002",
            name="Premium Auto Care",
            country="US",
            car_brands_serviced=["BMW", "Mercedes", "Audi"],
            repair_types=["brakes", "electrical", "engine", "ac", "steering"],
            handles_electric=False,
            distance_km=8.0,
            availability_score=80,
            has_required_parts=True,
            average_rating=4.7,
            parts_availability=95.0,
            location="North Side"
        ),
        Garage(
            garage_id="GAR-003",
            name="Community Garage",
            country="US",
            car_brands_serviced=["All brands"],
            repair_types=["brakes", "electrical", "engine"],
            handles_electric=False,
            distance_km=3.5,
            availability_score=60,
            has_required_parts=False,
            average_rating=3.8,
            parts_availability=70.0,
            location="Midtown"
        ),
        Garage(
            garage_id="GAR-004",
            name="Fast Brake Specialists",
            country="US",
            car_brands_serviced=["All brands"],
            repair_types=["brakes"],
            handles_electric=False,
            distance_km=1.5,
            availability_score=50,
            has_required_parts=True,
            average_rating=4.1,
            parts_availability=98.0,
            location="South End"
        ),
        Garage(
            garage_id="GAR-005",
            name="Electric & Modern Motors",
            country="US",
            car_brands_serviced=["Tesla", "Nissan", "Chevy"],
            repair_types=["electrical", "battery", "ac"],
            handles_electric=True,
            distance_km=6.0,
            availability_score=70,
            has_required_parts=True,
            average_rating=4.5,
            parts_availability=92.0,
            location="Tech District"
        ),
        Garage(
            garage_id="GAR-006",
            name="24/7 Emergency Auto",
            country="US",
            car_brands_serviced=["All brands"],
            repair_types=["brakes", "electrical", "engine", "cooling"],
            handles_electric=False,
            distance_km=4.0,
            availability_score=85,
            has_required_parts=True,
            average_rating=3.9,
            parts_availability=85.0,
            location="Available 24/7"
        ),
    ]
    return garages


# ============================================================================
# INTERACTIVE AGENT FOR GOOGLE COLAB
# ============================================================================

def format_analysis_result(analysis: ComplaintAnalysis) -> str:
    """Format analysis result for display"""
    output = []
    output.append("\n" + "="*80)
    output.append("📊 ANALYSIS RESULTS")
    output.append("="*80)
    
    output.append(f"\n📝 Complaint ID: {analysis.complaint_id}")
    output.append(f"🎯 Problem Type: {analysis.problem_type.upper()}")
    output.append(f"⚠️  Urgency Level: {analysis.urgency.value.upper()}")
    output.append(f"📈 Confidence: {analysis.confidence*100:.1f}%")
    
    if analysis.likely_parts:
        output.append(f"\n🔧 Likely Parts Needed:")
        for part in analysis.likely_parts:
            output.append(f"   • {part}")
    else:
        output.append("\n🔧 Parts: Unable to determine from historical data")
    
    output.append(f"\n⏱️  Estimated Repair Time: {analysis.estimated_hours:.1f} hours")
    
    if analysis.similar_cases:
        output.append(f"\n📋 Similar Historical Cases ({len(analysis.similar_cases)}):")
        for i, case in enumerate(analysis.similar_cases, 1):
            output.append(f"\n   {i}. Case {case.case_id}")
            output.append(f"      Problem: {case.problem_type}")
            output.append(f"      Urgency: {case.urgency.value}")
            output.append(f"      Time: {case.repair_duration_hours}h")
    
    return "\n".join(output)


def format_garage_recommendations(recommendations: List[GarageRecommendation]) -> str:
    """Format garage recommendations for display"""
    output = []
    output.append("\n" + "="*80)
    output.append("🏪 GARAGE RECOMMENDATIONS")
    output.append("="*80)
    
    if not recommendations:
        output.append("\n❌ No suitable garages found matching criteria.")
        return "\n".join(output)
    
    for i, rec in enumerate(recommendations, 1):
        output.append(f"\n[{i}] {rec.garage.name}")
        output.append(f"    Score: {rec.score:.1f}/100 ({rec.suitability})")
        output.append(f"    Location: {rec.garage.location} ({rec.garage.distance_km}km away)")
        output.append(f"    Rating: {rec.garage.average_rating}/5.0")
        output.append(f"    Parts Availability: {rec.garage.parts_availability:.0f}%")
        output.append(f"    Why this garage:")
        for reason in rec.reasons:
            output.append(f"      {reason}")
    
    return "\n".join(output)


def run_agent(complaints_batch: List[Dict] = None):
    """
    Run the garage complaint analysis agent
    
    Args:
        complaints_batch: List of complaints with 'id' and 'text' keys
    """
    
    print("\n" + "🚗 "*30)
    print("GARAGE COMPLAINT ANALYSIS AGENT - GOOGLE COLAB")
    print("🚗 "*30)
    
    # Initialize
    print("\n📊 Initializing agent systems...")
    historical_repairs = create_sample_repairs()
    garages = create_sample_garages()
    
    analyzer = ComplaintAnalyzer(historical_repairs)
    recommender = GarageRecommender(garages)
    
    print(f"✓ Loaded {len(historical_repairs)} historical repair cases")
    print(f"✓ Loaded {len(garages)} garages")
    
    # Use provided complaints or defaults
    if complaints_batch is None:
        complaints_batch = [
            {
                "id": "CUST-001",
                "text": "My car won't stop properly. The brake pedal goes almost to the floor and I'm very worried about safety."
            },
            {
                "id": "CUST-002",
                "text": "The temperature gauge is going into the red and I can see steam coming from under the bonnet."
            },
            {
                "id": "CUST-003",
                "text": "My headlights are very dim and the battery warning light turned on."
            },
            {
                "id": "CUST-004",
                "text": "There's a squealing noise when I brake and the pedal feels a bit soft."
            },
        ]
    
    # Process each complaint
    all_results = []
    
    for complaint in complaints_batch:
        complaint_id = complaint.get("id", f"CUST-{random.randint(1000, 9999)}")
        complaint_text = complaint.get("text", "")
        
        if not complaint_text:
            continue
        
        # Analyze
        analysis = analyzer.analyze(complaint_id, complaint_text)
        
        # Get recommendations
        recommendations = recommender.recommend_garage(analysis)
        
        # Format results
        print(f"\n{'='*80}")
        print(f"Processing: {complaint_id}")
        print(f"{'='*80}")
        print(f"Customer: \"{complaint_text}\"")
        
        print(format_analysis_result(analysis))
        print(format_garage_recommendations(recommendations))
        
        all_results.append({
            "complaint_id": complaint_id,
            "analysis": analysis,
            "recommendations": recommendations
        })
    
    print("\n" + "="*80)
    print(f"✓ Processed {len(all_results)} complaints")
    print("="*80)
    
    return all_results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run the agent with sample complaints
    results = run_agent()
    
    # Display summary
    print("\n📊 SUMMARY")
    print(f"Total complaints analyzed: {len(results)}")
    for result in results:
        urgency = result['analysis'].urgency.value
        garage_count = len(result['recommendations'])
        print(f"  • {result['complaint_id']}: {urgency} → {garage_count} garages found")
