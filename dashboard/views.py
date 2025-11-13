from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Dict, List, Optional, Tuple

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify

from .data import (
    CATEGORIES,
    ENROLLMENT_DATA,
    INITIATIVES,
    MONTHS,
    SCHEMES,
    SCHOLARSHIP_DATA,
    STATE_COORDINATES,
    YEARS,
    aggregate_initiatives_by_state,
)


try:
    from .models import Initiative as InitiativeModel, State as StateModel, Scheme as SchemeModel, Report as ReportModel  # type: ignore
except Exception:  
    InitiativeModel = None  
    StateModel = None 
    SchemeModel = None  
    ReportModel = None 


def _parse_filters(request) -> Dict[str, Optional[str]]:
    return {
        "year": request.GET.get("year") or None,
        "state": request.GET.get("state") or None,
        "scheme": request.GET.get("scheme") or None,
        "category": request.GET.get("category") or None,
    }


def _filter_initiatives(filters: Dict[str, Optional[str]]) -> List[Dict[str, object]]:
    # Prefer DB if populated; fallback to in-memory data
    if InitiativeModel is not None:
        try:
            qs = InitiativeModel.objects.select_related('state', 'scheme').all()
            if filters["year"]:
                qs = qs.filter(year=int(filters["year"]))
            if filters["state"]:
                qs = qs.filter(state__name=filters["state"])
            if filters["scheme"]:
                qs = qs.filter(scheme__name=filters["scheme"])
            if filters["category"]:
                qs = qs.filter(category=filters["category"])
            if qs.exists():
                result: List[Dict[str, object]] = []
                for obj in qs:
                    result.append({
                        "id": obj.id,
                        "name": obj.name,
                        "state": obj.state.name,
                        "scheme": obj.scheme.name,
                        "category": obj.category,
                        "year": obj.year,
                        "status": obj.status,
                        "progress": float(obj.progress),
                        "schools_impacted": int(obj.schools_impacted),
                        "students_impacted": int(obj.students_impacted),
                        "scholarships_awarded": int(obj.scholarships_awarded),
                        "budget_utilized": float(obj.budget_utilized),
                    })
                return result
        except Exception:
            pass  # fall back
    filtered: List[Dict[str, object]] = []
    for initiative in INITIATIVES:
        if filters["year"] and initiative["year"] != int(filters["year"]):
            continue
        if filters["state"] and initiative["state"] != filters["state"]:
            continue
        if filters["scheme"] and initiative["scheme"] != filters["scheme"]:
            continue
        if filters["category"] and initiative["category"] != filters["category"]:
            continue
        filtered.append(initiative)
    return filtered


def _derive_dashboard_metrics(
    filters: Dict[str, Optional[str]],
) -> Tuple[Dict[str, object], List[Dict[str, object]], Dict[str, Dict[str, float]]]:
    initiatives = _filter_initiatives(filters)
    total_schools = sum(int(item["schools_impacted"]) for item in initiatives)
    total_students = sum(int(item["students_impacted"]) for item in initiatives)
    total_scholarships = sum(int(item["scholarships_awarded"]) for item in initiatives)
    avg_progress_ratio = round(
        sum(float(item["progress"]) for item in initiatives) / len(initiatives), 2
    ) if initiatives else 0

    summary = {
        "schools": total_schools,
        "students": total_students,
        "scholarships": total_scholarships,
        "avg_progress_ratio": avg_progress_ratio,
        "avg_progress_pct": round(avg_progress_ratio * 100, 2),
        "initiatives": len(initiatives),
    }

    state_summary = aggregate_initiatives_by_state(initiatives)
    return summary, initiatives, state_summary


def _prepare_trends(filters: Dict[str, Optional[str]]) -> Dict[str, List[object]]:
    year = int(filters["year"]) if filters["year"] else YEARS[-1]
    primary = []
    secondary = []
    for entry in ENROLLMENT_DATA:
        if entry["year"] != year:
            continue
        primary.append(entry["primary"])
        secondary.append(entry["secondary"])
    return {
        "labels": MONTHS,
        "primary": primary,
        "secondary": secondary,
        "year": year,
    }


def _prepare_scholarships(filters: Dict[str, Optional[str]]) -> Dict[str, List[object]]:
    year = int(filters["year"]) if filters["year"] else YEARS[-1]
    states = []
    values = []
    for entry in SCHOLARSHIP_DATA:
        if entry["year"] != year:
            continue
        states.append(entry["state"])
        values.append(entry["beneficiaries"])
    return {
        "states": states,
        "values": values,
        "year": year,
    }


def _build_dashboard_payload(filters: Dict[str, Optional[str]]) -> Dict[str, object]:
    summary, initiatives, state_summary = _derive_dashboard_metrics(filters)
    normalized_initiatives: List[Dict[str, object]] = []
    for item in initiatives:
        normalized = dict(item)
        normalized["progress_pct"] = round(float(item["progress"]) * 100, 2)
        normalized_initiatives.append(normalized)
    trends = _prepare_trends(filters)
    scholarship = _prepare_scholarships(filters)
    map_points = []
    for state, data in state_summary.items():
        coords = STATE_COORDINATES.get(state)
        if not coords:
            continue
        map_points.append(
            {
                "state": state,
                "lat": coords["lat"],
                "lng": coords["lng"],
                "schools": data["schools"],
                "students": data["students"],
                "scholarships": data["scholarships"],
                "avg_progress": data.get("avg_progress", 0),
            }
        )
    map_points.sort(key=lambda item: item["state"])

    return {
        "summary": summary,
        "trends": trends,
        "scholarships": scholarship,
        "initiatives": normalized_initiatives,
        "map": map_points,
        "filters": filters,
    }


# -------- Frontend pages ---------
@require_GET
def overview(request) -> HttpResponse:
    filters = _parse_filters(request)
    payload = _build_dashboard_payload(filters)
    filter_options = {
        "years": YEARS,
        "states": sorted({item["state"] for item in INITIATIVES}),
        "schemes": sorted(set(SCHEMES)),
        "categories": sorted(set(CATEGORIES)),
    }
    return render(
        request,
        "dashboard/overview.html",
        {
            "payload": payload,
            "filters": filter_options,
        },
    )


@require_GET
def states_list(request) -> HttpResponse:
    states = sorted({item["state"] for item in INITIATIVES})
    return render(request, "dashboard/states.html", {"states": states})


@require_GET
def state_detail(request, state_slug: str) -> HttpResponse:
    # slug maps to state name
    states = {slugify(s): s for s in {i["state"] for i in INITIATIVES}}
    if StateModel is not None:
        try:
            for s in StateModel.objects.values_list('slug', 'name'):
                states[s[0]] = s[1]
        except Exception:
            pass
    state_name = states.get(state_slug)
    if not state_name:
        return render(request, "dashboard/state_detail.html", {"state": None, "initiatives": []}, status=404)
    filters = {**_parse_filters(request), "state": state_name}
    payload = _build_dashboard_payload(filters)
    filter_options = {
        "years": YEARS,
        "states": sorted({item["state"] for item in INITIATIVES} | set(states.values())),
        "schemes": sorted(set(SCHEMES)),
        "categories": sorted(set(CATEGORIES)),
    }
    return render(request, "dashboard/state_detail.html", {"state": state_name, "payload": payload, "filters": filter_options})


@require_GET
def state_print(request, state_slug: str) -> HttpResponse:
    states = {slugify(s): s for s in {i["state"] for i in INITIATIVES}}
    state_name = states.get(state_slug, state_slug)
    filters = {**_parse_filters(request), "state": state_name}
    payload = _build_dashboard_payload(filters)
    return render(request, "dashboard/state_print.html", {"state": state_name, "payload": payload})


@require_GET
def state_pdf(request, state_slug: str) -> HttpResponse:
    states = {slugify(s): s for s in {i["state"] for i in INITIATIVES}}
    state_name = states.get(state_slug, state_slug)
    filters = {**_parse_filters(request), "state": state_name}
    payload = _build_dashboard_payload(filters)
    try:
        from weasyprint import HTML  # type: ignore
        html = render(request, "dashboard/state_print.html", {"state": state_name, "payload": payload}).content.decode("utf-8")
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{slugify(state_name)}.pdf"'
        return response
    except Exception:
        return render(request, "dashboard/state_print.html", {"state": state_name, "payload": payload})


@require_GET
def schemes_list(request) -> HttpResponse:
    schemes_info: List[Dict[str, object]] = []
    for s in sorted(set(SCHEMES)):
        slug = slugify(s)
        items = [i for i in INITIATIVES if str(i.get("scheme")) == s]
        states = sorted({str(i.get("state")) for i in items})
        schemes_info.append({
            "name": s,
            "slug": slug,
            "initiatives_count": len(items),
            "states_count": len(states),
        })
    return render(request, "dashboard/schemes.html", {"schemes": schemes_info})


@require_GET
def scheme_detail(request, scheme_slug: str) -> HttpResponse:
    mapping = {slugify(s): s for s in set(SCHEMES)}
    if SchemeModel is not None:
        try:
            for s in SchemeModel.objects.values_list('slug', 'name'):
                mapping[s[0]] = s[1]
        except Exception:
            pass
    scheme_name = mapping.get(scheme_slug)
    if not scheme_name:
        return render(request, "dashboard/scheme_detail.html", {"scheme": None, "payload": {}}, status=404)
    filters = {**_parse_filters(request), "scheme": scheme_name}
    payload = _build_dashboard_payload(filters)
    filter_options = {
        "years": YEARS,
        "states": sorted({item["state"] for item in INITIATIVES}),
        "schemes": sorted(set(mapping.values())),
        "categories": sorted(set(CATEGORIES)),
    }
    return render(request, "dashboard/scheme_detail.html", {"scheme": scheme_name, "payload": payload, "filters": filter_options})


@require_GET
def scheme_print(request, scheme_slug: str) -> HttpResponse:
    mapping = {slugify(s): s for s in set(SCHEMES)}
    scheme_name = mapping.get(scheme_slug, scheme_slug)
    filters = {**_parse_filters(request), "scheme": scheme_name}
    payload = _build_dashboard_payload(filters)
    return render(request, "dashboard/scheme_print.html", {"scheme": scheme_name, "payload": payload})


@require_GET
def scheme_pdf(request, scheme_slug: str) -> HttpResponse:
    mapping = {slugify(s): s for s in set(SCHEMES)}
    scheme_name = mapping.get(scheme_slug, scheme_slug)
    filters = {**_parse_filters(request), "scheme": scheme_name}
    payload = _build_dashboard_payload(filters)
    # Try server-side PDF if WeasyPrint is available; else return print HTML
    try:
        from weasyprint import HTML  # type: ignore
        html = render(request, "dashboard/scheme_print.html", {"scheme": scheme_name, "payload": payload}).content.decode("utf-8")
        pdf = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{slugify(scheme_name)}.pdf"'
        return response
    except Exception:
        return render(request, "dashboard/scheme_print.html", {"scheme": scheme_name, "payload": payload})


@require_GET
def compare_view(request) -> HttpResponse:
    states = sorted({item["state"] for item in INITIATIVES})
    schemes = sorted(set(SCHEMES))
    filter_options = {"years": YEARS, "states": states, "schemes": schemes}
    return render(request, "dashboard/compare.html", {"filters": filter_options})


@require_GET
def reports_list(request) -> HttpResponse:
    reports = []
    if ReportModel is not None:
        try:
            reports = list(ReportModel.objects.all()[:200])
        except Exception:
            reports = []
    return render(request, "dashboard/reports.html", {"reports": reports})


@require_GET
def report_detail(request, report_id: str) -> HttpResponse:
    report = None
    files = []
    if ReportModel is not None:
        try:
            report = ReportModel.objects.filter(report_id=report_id).first()
        except Exception:
            report = None
    if report is None:
        # Fallback minimal info
        files = [
            {"format": "csv", "url": f"/api/v1/exports/data.csv?report={report_id}"},
        ]
        ctx = {"report_id": report_id, "status": "unknown", "files": files}
    else:
        files = [
            {"format": "pdf", "url": f"/reports/{report.report_id}?download=pdf"},
            {"format": "csv", "url": f"/api/v1/exports/data.csv?report={report.report_id}"},
        ]
        ctx = {"report_id": report.report_id, "status": report.status, "created_at": report.created_at, "files": files, "params": report.params}
    return render(request, "dashboard/report_detail.html", ctx)


# -------- Legacy/simple endpoints ---------
@require_GET
def dashboard_data(request: HttpRequest) -> JsonResponse:
    filters = _parse_filters(request)
    payload = _build_dashboard_payload(filters)
    return JsonResponse(payload)


@require_GET
def state_map_data(request: HttpRequest) -> JsonResponse:
    filters = _parse_filters(request)
    payload = _build_dashboard_payload(filters)
    return JsonResponse({"map": payload["map"]})


@require_GET
def download_report(request: HttpRequest) -> HttpResponse:
    filters = _parse_filters(request)
    _, initiatives, _ = _derive_dashboard_metrics(filters)

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Initiative",
            "State",
            "Scheme",
            "Category",
            "Year",
            "Status",
            "Progress",
            "Schools Impacted",
            "Students Impacted",
            "Scholarships Awarded",
            "Budget Utilized (Cr)",
        ]
    )
    for init in initiatives:
        writer.writerow(
            [
                init["name"],
                init["state"],
                init["scheme"],
                init["category"],
                init["year"],
                init["status"],
                f"{float(init['progress'])*100:.0f}%",
                init["schools_impacted"],
                init["students_impacted"],
                init["scholarships_awarded"],
                init["budget_utilized"],
            ]
        )
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="mhrd_dashboard_report.csv"'
    return response


# -------- API v1 ---------
@require_GET
def api_health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"ok": True})


@require_GET
def api_meta(request: HttpRequest) -> JsonResponse:
    states = sorted({item["state"] for item in INITIATIVES})
    schemes = [{"id": slugify(s), "name": s, "slug": slugify(s)} for s in sorted(set(SCHEMES))]
    return JsonResponse({
        "states": states,
        "schemes": schemes,
        "categories": sorted(set(CATEGORIES)),
        "years": YEARS,
    })


@require_GET
def api_kpis(request: HttpRequest) -> JsonResponse:
    filters = _parse_filters(request)
    summary, initiatives, _ = _derive_dashboard_metrics(filters)
    cards = {
        "schools": summary["schools"],
        "students": summary["students"],
        "scholarships": summary["scholarships"],
        "avg_progress_pct": summary["avg_progress_pct"],
        "initiatives": summary["initiatives"],
    }
    return JsonResponse({"cards": cards, "count": len(initiatives)})


@require_GET
def api_trends(request: HttpRequest) -> JsonResponse:
    filters = _parse_filters(request)
    series = _prepare_trends(filters)
    return JsonResponse(series)


@require_GET
def api_map(request: HttpRequest) -> JsonResponse:
    filters = _parse_filters(request)
    _, _, state_summary = _derive_dashboard_metrics(filters)
    choropleth = [
        {
            "state": state,
            "schools": payload["schools"],
            "students": payload["students"],
            "scholarships": payload["scholarships"],
            "avg_progress": round(payload.get("avg_progress", 0) * 100, 2),
        }
        for state, payload in state_summary.items()
    ]
    choropleth.sort(key=lambda x: x["state"]) 
    return JsonResponse({"choropleth": choropleth})


@require_GET
def api_schemes(request: HttpRequest) -> JsonResponse:
    data = [{"id": slugify(s), "name": s, "slug": slugify(s)} for s in sorted(set(SCHEMES))]
    return JsonResponse({"schemes": data})


@require_GET
def api_scheme_kpis(request: HttpRequest, scheme_id: str) -> JsonResponse:
    # Accept either slug or exact name
    mapping = {slugify(s): s for s in set(SCHEMES)}
    scheme_name = mapping.get(scheme_id, scheme_id)
    filters = {**_parse_filters(request), "scheme": scheme_name}
    summary, initiatives, _ = _derive_dashboard_metrics(filters)
    return JsonResponse({"schemeId": scheme_id, "cards": summary, "count": len(initiatives)})


@csrf_exempt
@require_http_methods(["POST"]) 
def api_create_report(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        payload = {}
    # In a real app, enqueue a job and persist. Here we persist immediately.
    report_id = f"rpt_{abs(hash(json.dumps(payload, sort_keys=True))) % 10_000_000}"
    status_val = "ready"
    if ReportModel is not None:
        try:
            obj, created = ReportModel.objects.get_or_create(report_id=report_id, defaults={"params": payload, "status": status_val})
            if not created:
                obj.params = payload
                obj.status = status_val
                obj.save(update_fields=["params", "status"])
        except Exception:
            pass
    return JsonResponse({"reportId": report_id, "status": status_val}, status=202)


@require_GET
def api_get_report(request: HttpRequest, report_id: str) -> JsonResponse:
    files = []
    status_val = "unknown"
    if ReportModel is not None:
        try:
            rpt = ReportModel.objects.filter(report_id=report_id).first()
            if rpt is not None:
                status_val = rpt.status
        except Exception:
            pass
    files = [
        {"format": "pdf", "url": f"/reports/{report_id}?download=pdf"},
        {"format": "csv", "url": f"/api/v1/exports/data.csv?report={report_id}"},
    ]
    return JsonResponse({"reportId": report_id, "status": status_val, "files": files})


@require_GET
def api_export_csv(request: HttpRequest) -> HttpResponse:
    filters = _parse_filters(request)
    _, initiatives, _ = _derive_dashboard_metrics(filters)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["name", "state", "scheme", "category", "year", "progress", "schools", "students", "scholarships", "budget"])
    for init in initiatives:
        writer.writerow([
            init["name"], init["state"], init["scheme"], init["category"], init["year"],
            f"{float(init['progress'])*100:.0f}%", init["schools_impacted"], init["students_impacted"], init["scholarships_awarded"], init["budget_utilized"]
        ])
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="mhrd_export.csv"'
    return response


@require_GET
def api_search(request: HttpRequest) -> JsonResponse:
    query = (request.GET.get("query") or "").strip().lower()
    results: List[Dict[str, object]] = []
    if query:
        for init in INITIATIVES:
            if (
                query in str(init["name"]).lower()
                or query in str(init["state"]).lower()
                or query in str(init["scheme"]).lower()
            ):
                results.append({
                    "id": init["id"],
                    "name": init["name"],
                    "state": init["state"],
                    "scheme": init["scheme"],
                    "year": init["year"],
                    "category": init["category"],
                })
    return JsonResponse({"query": query, "results": results})


@require_GET
def api_compare_trends(request: HttpRequest) -> JsonResponse:
    """Return simple yearly series for left/right entities.
    Params: left, right (state names), scheme?, metric? (students|schools|scholarships|avg_progress_pct)
    """
    left = request.GET.get("left") or ""
    right = request.GET.get("right") or ""
    scheme = request.GET.get("scheme") or None
    metric = (request.GET.get("metric") or "students").lower()
    years = YEARS  # use available years
    def value_for(filters):
        series = []
        for y in years:
            f = {**filters, "year": str(y)}
            summary, _, _ = _derive_dashboard_metrics(f)
            if metric == "schools":
                series.append(summary["schools"]) 
            elif metric == "scholarships":
                series.append(summary["scholarships"]) 
            elif metric == "avg_progress_pct":
                series.append(summary["avg_progress_pct"]) 
            else:
                series.append(summary["students"]) 
        return series
    left_filters = {"state": left, "scheme": scheme, "category": request.GET.get("category") or None}
    right_filters = {"state": right, "scheme": scheme, "category": request.GET.get("category") or None}
    return JsonResponse({
        "years": years,
        "metric": metric,
        "left": {"label": left, "values": value_for(left_filters)},
        "right": {"label": right, "values": value_for(right_filters)},
    })
