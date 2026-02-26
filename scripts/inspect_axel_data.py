import pandas as pd, warnings, pathlib
warnings.filterwarnings('ignore')

REPO = pathlib.Path(r"temp_repos/work_apps/templates")

ib = pd.read_excel(REPO / "ib_list.xlsx")
print(f"=== IB LIST: {len(ib)} rows x {len(ib.columns)} cols ===")
print("Columns:", list(ib.columns))
print()
print(ib.head(3).to_string())
print()

proj = pd.read_excel(REPO / "gh_current_projects.xlsx")
print(f"=== PROJECTS: {len(proj)} rows x {len(proj.columns)} cols ===")
print("Columns:", list(proj.columns))
print()
print(proj.head(3).to_string())
