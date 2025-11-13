from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

YEARS: List[int] = [2023, 2024, 2025]

SCHEMES: Sequence[str] = [
    "Samagra Shiksha",
    "PM SHRI Schools",
    "PM POSHAN (Mid-Day Meal)",
    "PM eVIDYA",
    "SWAYAM",
    "DIKSHA (Digital Infrastructure)",
    "NISHTHA Teacher Training",
    "National Means-cum-Merit Scholarship",
    "Rashtriya Uchchatar Shiksha Abhiyan (RUSA)",
    "GIAN",
    "IMPRINT",
    "Unnat Bharat Abhiyan",
    "National Apprenticeship Training Scheme (NATS)",
]

CATEGORIES: Sequence[str] = [
    "Infrastructure",
    "Digital Learning",
    "Scholarships",
    "Teacher Training",
    "Skill Development",
]

STATE_COORDINATES: Dict[str, Dict[str, float]] = {
    # States
    "Andhra Pradesh": {"lat": 15.9129, "lng": 79.7400},
    "Arunachal Pradesh": {"lat": 28.2180, "lng": 94.7278},
    "Assam": {"lat": 26.2006, "lng": 92.9376},
    "Bihar": {"lat": 25.0961, "lng": 85.3131},
    "Chhattisgarh": {"lat": 21.2787, "lng": 81.8661},
    "Goa": {"lat": 15.2993, "lng": 74.1240},
    "Gujarat": {"lat": 22.2587, "lng": 71.1924},
    "Haryana": {"lat": 29.0588, "lng": 76.0856},
    "Himachal Pradesh": {"lat": 31.1048, "lng": 77.1734},
    "Jharkhand": {"lat": 23.6102, "lng": 85.2799},
    "Karnataka": {"lat": 15.3173, "lng": 75.7139},
    "Kerala": {"lat": 10.8505, "lng": 76.2711},
    "Madhya Pradesh": {"lat": 22.9734, "lng": 78.6569},
    "Maharashtra": {"lat": 19.7515, "lng": 75.7139},
    "Manipur": {"lat": 24.6637, "lng": 93.9063},
    "Meghalaya": {"lat": 25.4670, "lng": 91.3662},
    "Mizoram": {"lat": 23.1645, "lng": 92.9376},
    "Nagaland": {"lat": 26.1584, "lng": 94.5624},
    "Odisha": {"lat": 20.9517, "lng": 85.0985},
    "Punjab": {"lat": 31.1471, "lng": 75.3412},
    "Rajasthan": {"lat": 27.0238, "lng": 74.2179},
    "Sikkim": {"lat": 27.5330, "lng": 88.5122},
    "Tamil Nadu": {"lat": 11.1271, "lng": 78.6569},
    "Telangana": {"lat": 18.1124, "lng": 79.0193},
    "Tripura": {"lat": 23.9408, "lng": 91.9882},
    "Uttar Pradesh": {"lat": 26.8467, "lng": 80.9462},
    "Uttarakhand": {"lat": 30.0668, "lng": 79.0193},
    "West Bengal": {"lat": 22.9868, "lng": 87.8550},
    # Union Territories
    "Andaman and Nicobar Islands": {"lat": 11.7401, "lng": 92.6586},
    "Chandigarh": {"lat": 30.7333, "lng": 76.7794},
    "Dadra and Nagar Haveli and Daman and Diu": {"lat": 20.3974, "lng": 72.8328},
    "Delhi": {"lat": 28.7041, "lng": 77.1025},
    "Jammu and Kashmir": {"lat": 33.7782, "lng": 76.5762},
    "Ladakh": {"lat": 34.2268, "lng": 77.5619},
    "Lakshadweep": {"lat": 10.5667, "lng": 72.6417},
    "Puducherry": {"lat": 11.9416, "lng": 79.8083},
}


# Build a comprehensive demo dataset covering every scheme x every state x every year
from hashlib import sha256
import random

INDIAN_STATES: Sequence[str] = [
    # States
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana",
    "Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya",
    "Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
    "Uttar Pradesh","Uttarakhand","West Bengal",
    # UTs
    "Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu","Delhi",
    "Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry",
]

SCHEME_CATEGORY_HINT = {
    "Samagra Shiksha": "Infrastructure",
    "PM SHRI Schools": "Infrastructure",
    "PM POSHAN (Mid-Day Meal)": "Skill Development",
    "PM eVIDYA": "Digital Learning",
    "SWAYAM": "Digital Learning",
    "DIKSHA (Digital Infrastructure)": "Digital Learning",
    "NISHTHA Teacher Training": "Teacher Training",
    "National Means-cum-Merit Scholarship": "Scholarships",
    "Rashtriya Uchchatar Shiksha Abhiyan (RUSA)": "Infrastructure",
    "GIAN": "Skill Development",
    "IMPRINT": "Skill Development",
    "Unnat Bharat Abhiyan": "Skill Development",
    "National Apprenticeship Training Scheme (NATS)": "Skill Development",
}

STATUSES = ["On Track", "Completed", "Delayed", "At Risk"]


def _seeded_random(*parts: str) -> random.Random:
    key = "::".join(parts)
    seed = int(sha256(key.encode("utf-8")).hexdigest()[:12], 16)
    return random.Random(seed)


def _synthetic_values(state: str, scheme: str, year: int) -> Dict[str, object]:
    r = _seeded_random(state, scheme, str(year))
    # scale knobs per scheme type
    category = SCHEME_CATEGORY_HINT.get(scheme, r.choice(list(CATEGORIES)))
    base_students = r.randint(8000, 60000)
    base_schools = r.randint(80, 1200)
    progress = round(r.uniform(0.35, 0.98), 2)
    status = r.choices(STATUSES, weights=[50, 20, 20, 10], k=1)[0]
    scholarships = r.randint(200, 4000) if category in ("Scholarships",) else r.randint(0, 1200)
    budget = round(r.uniform(3.0, 20.0), 1)
    # Year growth/decline
    factor = 1.0 + 0.05 * (year - YEARS[0])
    return {
        "category": category,
        "status": status,
        "progress": progress,
        "schools_impacted": int(base_schools * factor),
        "students_impacted": int(base_students * factor),
        "scholarships_awarded": int(scholarships * factor),
        "budget_utilized": round(budget * factor, 1),
    }


INITIATIVES: List[Dict[str, object]] = []
_id = 1
for year in YEARS:
    for state in INDIAN_STATES:
        for scheme in SCHEMES:
            values = _synthetic_values(state, scheme, year)
            INITIATIVES.append({
                "id": _id,
                "name": f"{scheme} - {state}",
                "state": state,
                "scheme": scheme,
                "category": values["category"],
                "year": year,
                "status": values["status"],
                "progress": values["progress"],
                "schools_impacted": values["schools_impacted"],
                "students_impacted": values["students_impacted"],
                "scholarships_awarded": values["scholarships_awarded"],
                "budget_utilized": values["budget_utilized"],
            })
            _id += 1


ENROLLMENT_DATA: List[Dict[str, object]] = []
for year in YEARS:
    for index, month in enumerate(MONTHS, start=1):
        base_primary = 4100 + (index * 120)
        base_secondary = 2300 + (index * 95)
        growth_factor = 1 + (0.03 * (year - 2023))
        ENROLLMENT_DATA.append(
            {
                "year": year,
                "month": month,
                "primary": int(base_primary * growth_factor),
                "secondary": int(base_secondary * growth_factor * 0.83),
            }
        )


SCHOLARSHIP_DATA: List[Dict[str, object]] = []
state_weights = {
    "Karnataka": 1.0,
    "Tamil Nadu": 1.2,
    "Maharashtra": 1.5,
    "Delhi": 0.6,
    "Uttar Pradesh": 1.8,
    "West Bengal": 0.9,
}

for year in YEARS:
    for state, weight in state_weights.items():
        SCHOLARSHIP_DATA.append(
            {
                "year": year,
                "state": state,
                "beneficiaries": int(850 * weight * (0.9 + 0.06 * (year - 2023))),
            }
        )


def aggregate_initiatives_by_state(initiatives: Iterable[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
    """Summaries aggregated metrics for the provided initiatives grouped by state."""

    summary: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {
            "schools": 0,
            "students": 0,
            "scholarships": 0,
            "progress_sum": 0,
            "initiatives": 0,
        }
    )
    for init in initiatives:
        state = str(init["state"])
        summary[state]["schools"] += int(init["schools_impacted"])
        summary[state]["students"] += int(init["students_impacted"])
        summary[state]["scholarships"] += int(init["scholarships_awarded"])
        summary[state]["progress_sum"] += float(init["progress"])
        summary[state]["initiatives"] += 1
    for state, payload in summary.items():
        if payload["initiatives"]:
            payload["avg_progress"] = round(payload["progress_sum"] / payload["initiatives"], 2)
        else:
            payload["avg_progress"] = 0
    return summary

