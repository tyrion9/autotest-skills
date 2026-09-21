"""Plugin pytest dùng chung cho bộ autotest-skills: quản lý biến & tham số
môi trường, tách UAT (môi trường kiểm thử nghiệm thu) / PROD (môi trường
thật), và tách biến GLOBAL (dùng chung mọi feature) / biến LOCAL (riêng 1
feature) — để tester sửa tay được mà không đụng vào code test.

CÁCH DÙNG (copy file này + 2 file mẫu `env.global.example.yaml`,
`env.local.example.yaml` vào thư mục chứa conftest.py của project):

    # testing/conftest.py
    pytest_plugins = ["autotest_reporting", "autotest_demo", "autotest_env"]

    import autotest_env
    BASE_URL = autotest_env.global_vars()["base_url"]

CẤU TRÚC FILE (tự tạo lần đầu bằng cách copy từ 2 file .example.yaml):

    testing/env/
      global.yaml           # biến DÙNG CHUNG cho mọi feature (vd base_url)
      local/
        <feature>.yaml      # biến RIÊNG cho 1 feature (path, số điện thoại
                             # cần tra cứu, data test cụ thể...) — tên file
                             # PHẢI khớp tên feature dùng khi gọi local_vars()

Mỗi file cùng 1 cấu trúc 2 cấp: khoá cấp 1 là tên môi trường (`uat`/`prod`),
bên trong là các biến của môi trường đó — VIẾT BẰNG YAML để tester sửa tay
được và có thể chú thích bằng `#` (giải thích nguồn gốc data test, vd "số
đã seed sẵn trong DB UAT").

CÁCH DÙNG trong step definitions — import trực tiếp, KHÔNG hard-code giá trị
UAT/PROD thẳng trong step (hard-code phá mất mục đích tách môi trường):

    from autotest_env import global_vars, local_vars
    base_url = global_vars()["base_url"]
    phone = local_vars("tra_cuu_so_dien_thoai")["phone_number"]

CHỌN MÔI TRƯỜNG KHI CHẠY (mặc định `uat` — KHÔNG BAO GIỜ tự mặc định `prod`):

    pytest testing --test-env=uat     # mặc định, không cần truyền cũng được
    pytest testing --test-env=prod    # chạy trên môi trường THẬT — phải được
                                       # người dùng xác nhận rõ trước khi chạy

Thiếu key trong file (`global_vars()["base_url"]` mà file không có `base_url`
ở môi trường đang chạy) → `KeyError` thẳng, không tự bịa giá trị mặc định —
đúng chủ đích: thiếu biến môi trường là lỗi cấu hình cần tester bổ sung, không
phải điều nên "đoán qua".
"""

from __future__ import annotations

import functools
import os
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - phụ thuộc môi trường chạy thật
    raise RuntimeError(
        "Thiếu PyYAML — cài `pip install pyyaml` để autotest_env đọc "
        "testing/env/*.yaml (bắt buộc, không phải phần tuỳ chọn)."
    ) from exc

_DEFAULT_ENV = "uat"
_KNOWN_ENVS = ("uat", "prod")

_current_env = os.environ.get("AUTOTEST_ENV_NAME", _DEFAULT_ENV)


def pytest_addoption(parser):
    group = parser.getgroup("autotest-env", "Chọn môi trường (UAT/PROD) cho biến test")
    group.addoption(
        "--test-env",
        default=_current_env,
        choices=_KNOWN_ENVS,
        metavar="uat|prod",
        help="Môi trường lấy biến từ testing/env/*.yaml (mặc định: uat). "
        "KHÔNG dùng --env để tránh trùng tên với plugin pytest-env nếu có.",
    )


def pytest_configure(config):
    global _current_env
    _current_env = config.getoption("--test-env")


def current_env() -> str:
    """Tên môi trường đang chạy ('uat'/'prod'), đã chốt từ --test-env."""
    return _current_env


def _env_dir() -> Path:
    override = os.environ.get("AUTOTEST_ENV_DIR")
    return Path(override).resolve() if override else Path.cwd() / "testing" / "env"


@functools.lru_cache(maxsize=None)
def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: nội dung phải là mapping (môi trường -> {{biến: giá trị}}), "
            f"không phải {type(data).__name__}"
        )
    return data


def global_vars() -> dict:
    """Biến dùng CHUNG cho mọi feature ở môi trường đang chạy (--test-env),
    đọc từ testing/env/global.yaml. Trả về {} nếu file/mục môi trường chưa
    có — không tự bịa giá trị mặc định, để KeyError báo đúng lỗi thiếu cấu
    hình khi step truy cập 1 key không tồn tại."""
    data = _load_yaml(_env_dir() / "global.yaml")
    return dict(data.get(_current_env, {}))


def local_vars(feature: str) -> dict:
    """Biến RIÊNG cho 1 feature (tên khớp tên dùng trong
    testing/env/local/<feature>.yaml, không có phần mở rộng) ở môi trường
    đang chạy. Trả về {} nếu feature đó chưa có file/mục môi trường."""
    data = _load_yaml(_env_dir() / "local" / f"{feature}.yaml")
    return dict(data.get(_current_env, {}))


def vars_for(feature: str) -> dict:
    """Gộp global_vars() + local_vars(feature) (local đè global nếu trùng
    khoá) — tiện dùng khi step cần cả 2 loại biến trong 1 lần gọi."""
    merged = global_vars()
    merged.update(local_vars(feature))
    return merged
