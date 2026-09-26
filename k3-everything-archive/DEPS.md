# 依赖台账（零依赖承诺的诚实边界）

- **核心层零依赖**：安装器四件（install.ps1/install.sh/verify_install.py）+ mcp/check_mcp.py + security/* 全部纯标准库，开箱即跑。
- **技能脚本两层语义**：
  - 纯标准库脚本（91/106）：开箱即跑；
  - 涉三方脚本（15/106）：其中 7 件已注入「K3 依赖预检」守卫（缺依赖显式报缺 + exit 2，不抛裸 ImportError）；8 件本就自带 try 优雅降级（缺依赖降功能不崩）。
- 三方清单：PIL×3 cv2×1 docx×1 fitz×2 numpy×3 openpyxl×1 pandas×1 psycopg2×2 pyzipper×1 qcloud_cos×1 qreader×1 rapidocr_onnxruntime×2 requests×2 scipy×1 yaml×1 zxingcpp×1（详见 testwave s3_deps.json）。
- 包内脚本间相互 import（dead_end_classifier/score_engine 等）为同目录局域引用，随包自洽。
