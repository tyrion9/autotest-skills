"""Plugin pytest dùng chung cho bộ autotest-skills: sinh reports/test_summary.md
và allure environment.properties, truy vết theo MatrixID.

CÁCH DÙNG (copy file này vào thư mục chứa conftest.py của project, vd testing/):

    # testing/conftest.py
    pytest_plugins = ["autotest_reporting"]

    # (tuỳ chọn) bổ sung thông tin môi trường cho tab Environment của Allure.
    # Cách 1 — qua biến môi trường, KHÔNG cần import plugin (khuyến nghị: tránh
    # warning "Module already imported so cannot be rewritten"):
    os.environ["AUTOTEST_ENV"] = f"App.URL={BASE_URL};Browser=Chromium (Playwright)"

    # Cách 2 — qua API module (dùng khi giá trị phức tạp):
    import autotest_reporting
    autotest_reporting.ENVIRONMENT.update({"App.URL": BASE_URL})

Nơi ghi báo cáo, theo thứ tự ưu tiên:
    1. Thư mục cha của --alluredir (vd --alluredir=reports/allure-results -> reports/)
    2. Biến môi trường AUTOTEST_REPORTS_DIR
    3. <thư mục chạy lệnh>/reports

Khuyến nghị đi kèm (không bắt buộc): cài `pytest-rerunfailures` và chạy với
`--reruns 1 --reruns-delay 1` để test nghi flaky được thử lại ở TẦNG PYTEST
(cơ chế chạy được trong CI, không phụ thuộc thao tác tay của người/AI).
Cột "Lần chạy lại" bên dưới sẽ cho biết case nào đã phải rerun — case rerun
mới pass là dấu hiệu flaky cần điều tra, KHÔNG được coi là pass sạch.
"""

from __future__ import annotations

import os
import platform
import re
import time
from datetime import datetime
from pathlib import Path

# Project có thể update dict này từ conftest.py để bổ sung thông tin môi trường.
ENVIRONMENT: dict[str, str] = {}

# MatrixID nằm ở đầu tên scenario dạng "[TC-A1B2C3] ..." (do xlsx_to_feature.py sinh).
_MATRIX_ID_RE = re.compile(r"^\[([A-Za-z0-9_.\-]+)\]")

_start_time: dict[int, float] = {}
_errors: dict[int, str] = {}
_results: list[dict] = []
_reruns: dict[str, int] = {}


def _matrix_id(scenario_name: str) -> str:
    match = _MATRIX_ID_RE.match(scenario_name.strip())
    return match.group(1) if match else ""


def _reports_dir(config) -> Path:
    alluredir = getattr(config.option, "allure_report_dir", None)
    if alluredir:
        return Path(alluredir).resolve().parent
    env_dir = os.environ.get("AUTOTEST_REPORTS_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    return Path.cwd() / "reports"


# --------------------------------------------------------------------------- hooks


def pytest_bdd_before_scenario(request, feature, scenario):
    _start_time[id(scenario)] = time.perf_counter()


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    _errors[id(scenario)] = f"{type(exception).__name__}: {exception}"


def pytest_bdd_after_scenario(request, feature, scenario):
    duration = time.perf_counter() - _start_time.pop(id(scenario), time.perf_counter())
    error = _errors.pop(id(scenario), None)
    _results.append(
        {
            "matrix_id": _matrix_id(scenario.name),
            "feature": getattr(feature, "name", ""),
            "scenario": scenario.name,
            "nodeid": request.node.nodeid,
            "outcome": "FAIL" if error else "PASS",
            "error": error or "",
            "duration_s": round(duration, 3),
        }
    )


def pytest_runtest_logreport(report):
    """Đếm số lần rerun (khi dùng pytest-rerunfailures)."""
    if report.when == "call" and getattr(report, "outcome", "") == "rerun":
        _reruns[report.nodeid] = _reruns.get(report.nodeid, 0) + 1


def pytest_sessionfinish(session, exitstatus):
    if not _results:
        return
    reports_dir = _reports_dir(session.config)
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_summary(reports_dir)
    _write_allure_environment(session.config)


# --------------------------------------------------------------------------- outputs


def _write_summary(reports_dir: Path) -> None:
    total = len(_results)
    passed = sum(1 for r in _results if r["outcome"] == "PASS")
    failed = total - passed
    flaky = [r for r in _results if _reruns.get(r["nodeid"], 0) > 0 and r["outcome"] == "PASS"]

    lines = [
        "# Báo cáo kết quả testcase",
        "",
        f"- Thời điểm chạy: {datetime.now().isoformat(timespec='seconds')}",
        f"- Tổng số scenario: {total}",
        f"- Pass: {passed}  |  Fail: {failed}",
    ]
    if flaky:
        lines.append(
            f"- ⚠️ Nghi flaky (pass sau khi rerun): {len(flaky)} — "
            + ", ".join(r["matrix_id"] or r["scenario"] for r in flaky)
        )
    lines += [
        "",
        "| MatrixID | Scenario | Kết quả | Thời gian (s) | Lần chạy lại | Lỗi |",
        "|---|---|---|---|---|---|",
    ]
    for r in _results:
        err = r["error"].replace("|", "\\|").replace("\n", " ")
        rerun = _reruns.get(r["nodeid"], 0)
        lines.append(
            f"| {r['matrix_id']} | {r['scenario']} | {r['outcome']} | {r['duration_s']} | {rerun} | {err} |"
        )
    lines += [
        "",
        "> MatrixID truy vết 1-1 về dòng tương ứng trong `testcase-pairwise.xlsx` "
        "(ID ổn định theo nội dung, không đổi khi thêm/bớt dòng khác).",
    ]
    (reports_dir / "test_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _env_from_variable() -> dict[str, str]:
    """Đọc AUTOTEST_ENV dạng 'k=v;k=v' — cách cấu hình không cần import plugin."""
    raw = os.environ.get("AUTOTEST_ENV", "").strip()
    if not raw:
        return {}
    result: dict[str, str] = {}
    for part in raw.split(";"):
        if "=" in part:
            key, _, value = part.partition("=")
            key, value = key.strip(), value.strip()
            if key:
                result[key] = value
    return result


def _write_allure_environment(config) -> None:
    alluredir = getattr(config.option, "allure_report_dir", None)
    if not alluredir:
        return
    allure_path = Path(alluredir)
    if not allure_path.exists():
        return
    props = {
        "Python": platform.python_version(),
        "OS": f"{platform.system()} {platform.release()}",
        "Headless": str(os.environ.get("HEADED") != "1"),
        **_env_from_variable(),
        **ENVIRONMENT,
    }
    content = "\n".join(f"{k}={v}" for k, v in props.items())
    (allure_path / "environment.properties").write_text(content + "\n", encoding="utf-8")
