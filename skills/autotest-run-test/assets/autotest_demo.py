"""Plugin pytest: chế độ TRÌNH DIỄN — chạy test có màn hình, chậm, dừng từng testcase.

Mục đích: để tester ngồi xem và kiểm chứng BẰNG MẮT từng testcase, thay vì chỉ
nhìn dòng `29 passed` cuối cùng. Không thay thế lần chạy CI (headless, song
song, không dừng) — đây là chế độ phụ, bật bằng cờ.

CÁCH DÙNG (copy file này cạnh conftest.py của project, như autotest_reporting.py):

    # conftest.py
    pytest_plugins = ["autotest_reporting", "autotest_demo"]

    # Browser phải đọc tham số demo thì "có màn hình + chậm" mới có tác dụng:
    @pytest.fixture(scope="session")
    def browser(demo_mode):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=not demo_mode.headed,     # demo -> hiện cửa sổ trình duyệt
                slow_mo=demo_mode.slow_mo,         # demo -> chậm lại từng thao tác (ms)
            )
            yield browser
            browser.close()

Chạy:
    pytest testing --demo                    # dừng chờ Enter sau mỗi testcase
    pytest testing --demo --demo-pause=3     # tự chạy tiếp sau 3 giây
    pytest testing --demo --demo-pause=none  # không dừng, chỉ chậm + in chi tiết
    pytest testing --demo --demo-slowmo=800 --demo-step-delay=1
    pytest testing --demo -k "TC-4F2A91"     # trình diễn đúng 1 testcase

Khi đang dừng chờ: Enter = case tiếp theo · `s` = thôi dừng, chạy hết · `q` = dừng phiên.

Lưu ý: chế độ demo ép chạy TUẦN TỰ (tắt -n của pytest-xdist) vì chạy song song
thì không thể xem bằng mắt và không thể dừng theo từng case.
"""

from __future__ import annotations

import re
import sys
import time
from contextlib import nullcontext
from dataclasses import dataclass, field

import pytest

# MatrixID ở đầu tên scenario: "[TC-A1B2C3] ..." (do xlsx_to_feature.py sinh).
# Pattern siết chặt (2-4 chữ cái + "-" + mã) để KHÔNG nhận nhầm id parametrize
# của pytest, vốn cũng nằm trong ngoặc vuông: "test_x[CaPheDen-M-2]".
_MATRIX_ID_RE = re.compile(r"\[([A-Za-z]{2,4}-[0-9A-Za-z]{4,})\]")
_PLACEHOLDER_RE = re.compile(r"<([A-Za-z0-9_]+)>")
# Tiền tố "[...]" ở đầu tên scenario (chỗ chứa MatrixID) để cắt khi in tiêu đề.
_LEADING_TAG_RE = re.compile(r"^\[[^\]]*\]\s*")

_LINE = "─" * 78


@dataclass
class DemoMode:
    """Tham số chế độ trình diễn — conftest.py đọc để cấu hình browser."""

    enabled: bool = False
    headed: bool = True
    slow_mo: int = 0
    step_delay: float = 0.0
    pause: str = "none"  # "enter" | "none" | số giây dạng chuỗi
    _stop_pausing: bool = field(default=False, repr=False)

    @property
    def pause_seconds(self) -> float | None:
        try:
            return float(self.pause)
        except ValueError:
            return None


_demo = DemoMode()
_reports: dict[str, str] = {}


# --------------------------------------------------------------------------- options


def pytest_addoption(parser):
    group = parser.getgroup("autotest-demo", "Chế độ trình diễn cho tester")
    group.addoption("--demo", action="store_true", default=False,
                    help="Chạy có màn hình, chậm, in chi tiết và dừng sau mỗi testcase.")
    group.addoption("--demo-headless", action="store_true", default=False,
                    help="Vẫn bật chi tiết/dừng nhưng chạy ẩn trình duyệt.")
    group.addoption("--demo-slowmo", type=int, default=500, metavar="MS",
                    help="Độ trễ Playwright giữa các thao tác, ms (mặc định 500).")
    group.addoption("--demo-step-delay", type=float, default=0.5, metavar="GIÂY",
                    help="Nghỉ thêm sau mỗi step Gherkin, giây (mặc định 0.5).")
    group.addoption("--demo-pause", default="enter", metavar="enter|none|GIÂY",
                    help="Sau mỗi testcase: chờ Enter (mặc định), không dừng, hoặc chờ N giây.")


def pytest_configure(config):
    _demo.enabled = config.getoption("--demo")
    if not _demo.enabled:
        return

    _demo.headed = not config.getoption("--demo-headless")
    _demo.slow_mo = config.getoption("--demo-slowmo")
    _demo.step_delay = config.getoption("--demo-step-delay")
    _demo.pause = str(config.getoption("--demo-pause")).strip().lower()

    # Chạy song song thì không xem bằng mắt được -> ép tuần tự.
    if getattr(config.option, "numprocesses", None):
        config.option.numprocesses = 0

    try:
        import pytest_bdd  # noqa: F401
    except ImportError:
        pass
    else:
        config.pluginmanager.register(_BddStepEcho(), "autotest-demo-bdd")


@pytest.fixture(scope="session")
def demo_mode() -> DemoMode:
    """Fixture cho conftest.py: headless=not demo_mode.headed, slow_mo=demo_mode.slow_mo."""
    return _demo


# --------------------------------------------------------------------------- tiện ích


def _writer(config):
    return config.get_terminal_writer()


def _matrix_id(text: str) -> str:
    match = _MATRIX_ID_RE.search(text or "")
    return match.group(1) if match else ""


def _scenario_of(item):
    """Trả về đối tượng scenario của pytest-bdd (nếu test này là scenario)."""
    return getattr(getattr(item, "function", None), "__scenario__", None)


def _example_params(item) -> dict[str, str]:
    """Giá trị 1 dòng Examples (Scenario Outline) hoặc tham số parametrize."""
    params = dict(getattr(getattr(item, "callspec", None), "params", {}) or {})
    example = params.pop("_pytest_bdd_example", None)
    if isinstance(example, dict):
        params.update(example)
    return {k: v for k, v in params.items() if not str(k).startswith("_")}


def _fill(text: str, params: dict) -> str:
    return _PLACEHOLDER_RE.sub(lambda m: str(params.get(m.group(1), m.group(0))), text)


def _resolve_matrix_id(item, scenario, params: dict) -> str:
    """Ưu tiên cột MatrixID của Examples — feature do pipeline sinh đặt tiêu đề
    scenario là "[<MatrixID>]", nên tên scenario chưa thay giá trị thật."""
    for key in ("MatrixID", "matrix_id", "Matrix_ID"):
        if params.get(key):
            return str(params[key])
    return _matrix_id(getattr(scenario, "name", "")) or _matrix_id(item.name)


def _title(item, scenario, params: dict) -> str:
    name = _fill(getattr(scenario, "name", "") or item.name, params)
    return _LEADING_TAG_RE.sub("", name).strip() or item.name


def _describe(item, scenario, params: dict) -> str:
    doc = (getattr(getattr(item, "function", None), "__doc__", "") or "").strip()
    # pytest-bdd tự đặt __doc__ = "<đường dẫn>.feature: <tên scenario>" -> bỏ qua.
    if doc and ".feature:" not in doc:
        return doc.splitlines()[0]
    return _title(item, scenario, params)


# --------------------------------------------------------------------------- hooks


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    if not _demo.enabled:
        yield
        return

    _banner(item)
    yield
    _result_and_pause(item, nextitem)


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        _reports[report.nodeid] = report.outcome


def _banner(item) -> None:
    config = item.config
    writer = _writer(config)
    scenario = _scenario_of(item)
    params = _example_params(item)
    index = getattr(item.session, "_demo_index", 0) + 1
    item.session._demo_index = index
    total = getattr(item.session, "testscollected", 0)

    matrix_id = _resolve_matrix_id(item, scenario, params) or "(không có MatrixID)"
    feature = getattr(scenario, "feature", None)

    writer.line("")
    writer.line(_LINE, cyan=True)
    writer.write(f"▶  [{index}/{total}]  ", bold=True)
    writer.write(f"{matrix_id}  ", bold=True, cyan=True)
    writer.line(_title(item, scenario, params), bold=True)
    writer.line(_LINE, cyan=True)

    writer.line(f"   Mô tả    : {_describe(item, scenario, params)}")
    if feature is not None:
        writer.line(f"   Feature  : {getattr(feature, 'name', '')}")
        writer.line(f"   File     : {getattr(feature, 'filename', '')}")
    writer.line(f"   Node     : {item.nodeid}")

    data = {k: v for k, v in params.items() if k not in ("MatrixID", "matrix_id", "Matrix_ID")}
    if data:
        writer.line("   Dữ liệu  :")
        width = max(len(str(k)) for k in data)
        for key, value in data.items():
            writer.line(f"       {str(key):<{width}} = {value}")

    steps = getattr(scenario, "steps", None) or []
    if steps:
        writer.line("   Các bước :")
        for step in steps:
            keyword = (getattr(step, "keyword", "") or "").strip()
            writer.line(f"       {keyword} {_fill(getattr(step, 'name', ''), params)}")

    if _demo.enabled and _demo.headed:
        writer.line(f"   (trình duyệt hiện hình, slow_mo={_demo.slow_mo}ms, "
                    f"nghỉ {_demo.step_delay}s mỗi step)", cyan=True)
    writer.line("")


def _result_and_pause(item, nextitem) -> None:
    writer = _writer(item.config)
    outcome = _reports.pop(item.nodeid, "")
    label = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}.get(outcome, outcome.upper() or "?")
    writer.line("")
    writer.write("   Kết quả  : ", bold=True)
    writer.line(label, bold=True, green=(label == "PASS"), red=(label == "FAIL"),
                yellow=(label == "SKIP"))

    if nextitem is None or _demo._stop_pausing or _demo.pause == "none":
        writer.line("")
        return

    seconds = _demo.pause_seconds
    if seconds is not None:
        writer.line(f"   ... chạy tiếp sau {seconds}s", cyan=True)
        time.sleep(seconds)
        return

    _wait_for_enter(item, writer)


def _read_from_terminal() -> str | None:
    """Đọc 1 dòng do tester gõ. Trả về None nếu không có terminal thật.

    KHÔNG dùng input()/sys.stdin: khi pytest đang capture, sys.stdin bị thay
    bằng DontReadFromInput (isatty() luôn False, đọc là lỗi). Mở thẳng
    /dev/tty là cách chắc chắn nhất, không phụ thuộc trạng thái capture.
    """
    try:
        with open("/dev/tty", "r") as tty:          # POSIX (macOS/Linux)
            return tty.readline()
    except OSError:
        pass
    try:                                            # Windows hoặc môi trường lạ
        if sys.stdin is not None and sys.stdin.isatty():
            return sys.stdin.readline()
    except (OSError, ValueError):
        pass
    return None


def _wait_for_enter(item, writer) -> None:
    # Tắt capture của pytest trong lúc dừng để dòng nhắc hiện ra ngay.
    # Dùng global_and_fixture_disabled() (context manager chính thức) thay vì tự
    # suspend/resume — tự resume làm hỏng trạng thái capture và nuốt mất output
    # của testcase kế tiếp.
    capman = item.config.pluginmanager.getplugin("capturemanager")
    disabled = capman.global_and_fixture_disabled() if capman else nullcontext()
    with disabled:
        writer.write("   ⏎ Enter = testcase tiếp theo · s = chạy hết · q = dừng phiên: ", bold=True)
        writer.flush()
        answer = _read_from_terminal()
        writer.line("")

    if answer is None:
        writer.line("   (không có terminal để nhận phím -> bỏ qua bước dừng từ đây)", yellow=True)
        _demo._stop_pausing = True
        return

    answer = answer.strip().lower()
    if answer == "s":
        _demo._stop_pausing = True
        writer.line("   -> chạy nốt các testcase còn lại, không dừng nữa.", cyan=True)
    elif answer == "q":
        pytest.exit("Tester dừng phiên trình diễn.", returncode=0)


class _BddStepEcho:
    """In từng step Gherkin ngay khi nó chạy + nghỉ để mắt kịp theo dõi."""

    def pytest_bdd_before_step(self, request, feature, scenario, step, step_func):
        writer = _writer(request.config)
        writer.line(f"       → {step.keyword.strip()} {step.name}", cyan=True)

    def pytest_bdd_after_step(self, request, feature, scenario, step, step_func, step_func_args):
        if _demo.step_delay > 0:
            time.sleep(_demo.step_delay)

    def pytest_bdd_step_error(self, request, feature, scenario, step, step_func,
                              step_func_args, exception):
        writer = _writer(request.config)
        writer.line(f"       ✗ {step.keyword.strip()} {step.name} -> "
                    f"{type(exception).__name__}: {exception}", red=True)
