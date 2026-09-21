"""Plugin pytest dùng chung cho bộ autotest-skills: sinh reports/test_summary.md,
allure environment.properties, và tự đính kèm BẰNG CHỨNG vào Allure (ảnh chụp
màn hình cho scenario UI, curl+response thật cho scenario API, LỊCH SỬ mọi
lời gọi HTTP (URL + mã response) trong scenario) — Allure là định dạng báo
cáo MẶC ĐỊNH của bộ skill, không phải phần tuỳ chọn.

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

Yêu cầu: cài `allure-pytest-bdd` (bắt buộc — không có thì `--alluredir` không
sinh ra gì và các attach dưới đây bị bỏ qua lặng lẽ, không lỗi).

BẰNG CHỨNG TỰ ĐỘNG CHO SCENARIO UI (Playwright):
    Nếu scenario có dùng 1 fixture đặt tên đúng là `page` (function-scope, trả
    về `playwright.sync_api.Page`, thường tạo qua `browser.new_page()`), plugin
    này TỰ:
    - chụp ảnh màn hình và đính vào Allure khi scenario kết thúc — cả khi PASS
      và FAIL — không cần step nào tự gọi gì thêm;
    - ghi LỊCH SỬ mọi request loại `document`/`xhr`/`fetch` mà trang gọi trong
      lúc chạy scenario (method, URL, mã response) và đính thành 1 attachment
      "HTTP calls (network log)" — bỏ qua ảnh/css/font để đỡ nhiễu. Đặt tên
      fixture khác `page` thì mất cả 2 phần tự động này.

BẰNG CHỨNG CHO SCENARIO API (gọi trực tiếp bằng `requests`.../không qua
`page`) — gọi `attach_api_call(...)` ngay sau khi step thực hiện request
thật, để đính kèm curl tái hiện request + response thật:

    from autotest_reporting import attach_api_call
    resp = requests.post(url, json=payload, headers=headers)
    attach_api_call(
        "POST", url, request_headers=headers, request_body=payload,
        status=resp.status_code, response_headers=dict(resp.headers),
        response_body=resp.json() if resp.content else None,
    )

CHE THÔNG TIN NHẠY CẢM (áp dụng cho cả network log tự động và
`attach_api_call`): mọi header/field/query-param có TÊN chứa (không phân biệt
hoa/thường) `key`, `password`/`passwd`, `secret`, `token`, `authorization`,
`cookie` — bao gồm đúng danh sách yêu cầu (`x-api-key`, `password`, `secret`,
`key`) và các trường tương đương thường đi kèm — bị thay bằng `***` trước khi
đính vào Allure. KHÔNG tự thêm field nhạy cảm khác vào whitelist khi chưa rõ
tên field đó ở project cụ thể — nếu project có tên field nhạy cảm khác không
khớp các từ khoá trên, phải sửa `_SENSITIVE_KEY_RE` trong bản copy của project
đó, không đợi lộ dữ liệu rồi mới sửa.

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

import json
import os
import platform
import re
import shlex
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    import allure

    _HAS_ALLURE = True
except ImportError:  # allure-pytest-bdd chưa cài -> bỏ qua mọi attach, không lỗi.
    _HAS_ALLURE = False

# Project có thể update dict này từ conftest.py để bổ sung thông tin môi trường.
ENVIRONMENT: dict[str, str] = {}

# MatrixID nằm ở đầu tên scenario dạng "[TC-A1B2C3] ..." (do autotest-gen-test đặt).
_MATRIX_ID_RE = re.compile(r"^\[([A-Za-z0-9_.\-]+)\]")

# Tên header/field/query-param bị che trước khi đính vào Allure — xem mục
# "CHE THÔNG TIN NHẠY CẢM" ở docstring đầu file.
_SENSITIVE_KEY_RE = re.compile(
    r"(api[-_ ]?key|password|passwd|secret|token|authorization|cookie)", re.IGNORECASE
)
_MASK = "***"

# Chỉ log các request có ý nghĩa nghiệp vụ (gọi API/điều hướng trang) vào
# lịch sử — bỏ ảnh/css/font/script tĩnh cho đỡ nhiễu report.
_LOGGED_RESOURCE_TYPES = {"document", "xhr", "fetch"}

_start_time: dict[int, float] = {}
_errors: dict[int, str] = {}
_results: list[dict] = []
_reruns: dict[str, int] = {}
_network_log: dict[int, list[dict]] = {}
_xfail_reason: dict[str, str] = {}


def _matrix_id(scenario_name: str) -> str:
    match = _MATRIX_ID_RE.match(scenario_name.strip())
    return match.group(1) if match else ""


def _is_sensitive_key(key) -> bool:
    return bool(_SENSITIVE_KEY_RE.search(str(key)))


def _redact_headers(headers: dict | None) -> dict:
    if not headers:
        return {}
    return {k: (_MASK if _is_sensitive_key(k) else v) for k, v in headers.items()}


def _redact_body(body):
    if isinstance(body, dict):
        return {k: (_MASK if _is_sensitive_key(k) else _redact_body(v)) for k, v in body.items()}
    if isinstance(body, list):
        return [_redact_body(v) for v in body]
    return body


def _redact_url(url: str) -> str:
    """Che giá trị các query-param nhạy cảm (vd ?api_key=... / ?token=...)."""
    parts = urlsplit(url)
    if not parts.query:
        return url
    params = parse_qsl(parts.query, keep_blank_values=True)
    safe_params = [(k, _MASK if _is_sensitive_key(k) else v) for k, v in params]
    return urlunsplit(parts._replace(query=urlencode(safe_params)))


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
    _start_network_log(request, id(scenario))


def _start_network_log(request, scenario_id: int) -> None:
    """Gắn listener lên fixture `page` (nếu scenario dùng) để ghi lại MỌI
    request document/xhr/fetch phát sinh trong lúc chạy — bằng chứng lịch sử
    gọi HTTP, không phụ thuộc step nào có tự nhớ log hay không.

    KHÔNG lọc theo `"page" in request.fixturenames` trước: tại thời điểm
    `pytest_bdd_before_scenario` chạy (trước khi step nào chạy), pytest-bdd
    chưa mở rộng closure fixture của test theo tham số các step function —
    `page` (do step tự khai báo làm tham số, không phải tham số của hàm test
    do pytest-bdd sinh ra) thường CHƯA xuất hiện trong `request.fixturenames`
    dù step sau đó có dùng, nên lọc trước sẽ luôn bỏ qua nhầm và mất toàn bộ
    network log (đã xác nhận bằng chạy thật: mất hết log tới khi bỏ điều kiện
    này). Gọi thẳng `getfixturevalue` và bắt lỗi nếu scenario thật sự không
    dùng `page`.

    Đánh đổi đã biết: nếu 1 project có CẢ scenario UI lẫn scenario API dùng
    chung 1 `conftest.py` có định nghĩa fixture `page`, gọi `getfixturevalue`
    ở đây sẽ tạo `page` (mở 1 tab trình duyệt) ngay cả cho scenario API không
    hề dùng đến nó — chấp nhận được (tab đó vẫn được teardown bình thường,
    chỉ tốn thêm chút thời gian) để đổi lại KHÔNG mất network log của mọi
    scenario UI. Muốn tránh hẳn việc này, tách scenario API sang thư mục có
    `conftest.py` riêng không định nghĩa `page`."""
    try:
        page = request.getfixturevalue("page")
    except Exception:
        return

    def on_response(response) -> None:
        try:
            req = response.request
            if req.resource_type not in _LOGGED_RESOURCE_TYPES:
                return
            _network_log.setdefault(scenario_id, []).append(
                {"method": req.method, "url": _redact_url(req.url), "status": response.status}
            )
        except Exception:
            pass  # lỗi log network không được làm hỏng test thật

    try:
        page.on("response", on_response)
    except Exception:
        pass


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    _errors[id(scenario)] = f"{type(exception).__name__}: {exception}"


def pytest_bdd_after_scenario(request, feature, scenario):
    duration = time.perf_counter() - _start_time.pop(id(scenario), time.perf_counter())
    error = _errors.pop(id(scenario), None)
    _attach_ui_screenshot(request, outcome="FAIL" if error else "PASS")
    _attach_network_history(id(scenario))
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
    """Đếm số lần rerun (khi dùng pytest-rerunfailures) và ghi nhận scenario
    nào được đánh dấu xfail (vd tag @known-bug áp `pytest.mark.xfail`) — để
    `_write_summary` phân biệt "lỗi đã biết, đang theo dõi" với lỗi mới phát
    sinh, thay vì gộp chung vào cột Fail khiến người đọc tưởng nhầm là
    regression."""
    if report.when == "call" and getattr(report, "outcome", "") == "rerun":
        _reruns[report.nodeid] = _reruns.get(report.nodeid, 0) + 1
    if report.when == "call" and getattr(report, "wasxfail", None) is not None:
        _xfail_reason[report.nodeid] = report.wasxfail or "(known bug)"


# --------------------------------------------------------------------------- bằng chứng Allure


def _attach_ui_screenshot(request, outcome: str) -> None:
    """Tự chụp + đính ảnh màn hình vào Allure cho scenario có dùng fixture
    `page` (Playwright) — cả PASS và FAIL. Im lặng bỏ qua nếu không có Allure,
    scenario không dùng `page`, hoặc chụp ảnh lỗi (vd trang đã đóng)."""
    if not _HAS_ALLURE or "page" not in request.fixturenames:
        return
    try:
        page = request.getfixturevalue("page")
        png = page.screenshot(full_page=True)
    except Exception:
        return
    allure.attach(png, name=f"Screenshot ({outcome})", attachment_type=allure.attachment_type.PNG)


def _attach_network_history(scenario_id: int) -> None:
    """Đính lịch sử các lần gọi HTTP (method, URL đã che field nhạy cảm, mã
    response) của scenario vào Allure — để trace lại đúng thứ tự đã gọi khi
    xem báo cáo, dù step không tự khai báo gì."""
    calls = _network_log.pop(scenario_id, None)
    if not _HAS_ALLURE or not calls:
        return
    width = max(len(c["method"]) for c in calls)
    lines = [
        f"{i:>3}  {c['method']:<{width}}  {c['status']:<3}  {c['url']}"
        for i, c in enumerate(calls, 1)
    ]
    allure.attach(
        "\n".join(lines), name="HTTP calls (network log)", attachment_type=allure.attachment_type.TEXT
    )


def _build_curl(method: str, url: str, headers: dict | None, body) -> str:
    parts = ["curl", "-i", "-X", method.upper(), shlex.quote(url)]
    for key, value in (headers or {}).items():
        parts += ["-H", shlex.quote(f"{key}: {value}")]
    if body is not None:
        text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
        parts += ["-d", shlex.quote(text)]
    return " ".join(parts)


def _format_http_block(status, headers: dict | None, body) -> str:
    lines = []
    if status is not None:
        lines.append(f"Status: {status}")
    lines += [f"{key}: {value}" for key, value in (headers or {}).items()]
    lines.append("")
    if body is not None:
        lines.append(body if isinstance(body, str) else json.dumps(body, ensure_ascii=False, indent=2))
    return "\n".join(lines)


def attach_api_call(
    method: str,
    url: str,
    *,
    name: str | None = None,
    request_headers: dict | None = None,
    request_body=None,
    status: int | str | None = None,
    response_headers: dict | None = None,
    response_body=None,
) -> None:
    """Đính kèm curl tái hiện request THẬT + response THẬT vào Allure. Gọi
    ngay sau khi step thực hiện lời gọi API (không phải trước), để bằng chứng
    khớp đúng request/response đã xảy ra — không tự bịa lại từ code app. Im
    lặng bỏ qua nếu chưa cài Allure (không raise, không chặn test). Tự che
    header/field nhạy cảm (xem docstring đầu file) trước khi đính — không đưa
    request_headers/request_body/response_headers/response_body gốc chưa che
    vào bất kỳ chỗ nào khác của báo cáo."""
    if not _HAS_ALLURE:
        return
    safe_url = _redact_url(url)
    label = name or f"{method.upper()} {safe_url}"
    curl = _build_curl(method, safe_url, _redact_headers(request_headers), _redact_body(request_body))
    allure.attach(curl, name=f"curl - {label}", attachment_type=allure.attachment_type.TEXT)
    safe_response_body = _redact_body(response_body)
    response_type = (
        allure.attachment_type.JSON
        if isinstance(safe_response_body, (dict, list))
        else allure.attachment_type.TEXT
    )
    allure.attach(
        _format_http_block(status, _redact_headers(response_headers), safe_response_body),
        name=f"Response - {label}",
        attachment_type=response_type,
    )


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
    # xfail (vd tag @known-bug áp pytest.mark.xfail): scenario THẬT SỰ chạy
    # và fail như dự kiến do 1 bug đã biết — tách riêng khỏi Fail để không
    # lẫn với lỗi mới phát sinh (regression). xfail bất ngờ PASS (bug đã được
    # fix nhưng quên gỡ tag) vẫn tính là FAIL — xem "Kết quả" theo `outcome`.
    xfail_nodeids = {nid for nid, why in _xfail_reason.items() if why}
    known_bug = [r for r in _results if r["outcome"] == "FAIL" and r["nodeid"] in xfail_nodeids]
    passed = sum(1 for r in _results if r["outcome"] == "PASS")
    failed = sum(1 for r in _results if r["outcome"] == "FAIL" and r["nodeid"] not in xfail_nodeids)
    flaky = [r for r in _results if _reruns.get(r["nodeid"], 0) > 0 and r["outcome"] == "PASS"]

    lines = [
        "# Báo cáo kết quả testcase",
        "",
        f"- Thời điểm chạy: {datetime.now().isoformat(timespec='seconds')}",
        f"- Tổng số scenario: {total}",
        f"- Pass: {passed}  |  Fail: {failed}  |  Known bug (xfail): {len(known_bug)}",
    ]
    if known_bug:
        lines.append(
            "- 🐞 Known bug đang theo dõi (xfail, KHÔNG phải regression mới): "
            + ", ".join(r["matrix_id"] or r["scenario"] for r in known_bug)
        )
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
        outcome = r["outcome"]
        if outcome == "FAIL" and r["nodeid"] in xfail_nodeids:
            outcome = "XFAIL (known bug)"
        lines.append(
            f"| {r['matrix_id']} | {r['scenario']} | {outcome} | {r['duration_s']} | {rerun} | {err} |"
        )
    lines += [
        "",
        "> MatrixID truy vết 1-1 về case tương ứng trong `.feature` "
        "(ID ổn định, không đổi khi thêm case khác).",
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
