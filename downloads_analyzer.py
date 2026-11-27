
import os
import sys
import html
import webbrowser
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ==========================================
# CONFIGURATION
# ==========================================

DOWNLOADS = Path.home() / "Downloads"
REPORT = DOWNLOADS / "Downloads_Storage_Report.html"

print("=" * 60)
print("       WINDOWS DOWNLOADS STORAGE ANALYZER")
print("=" * 60)

if not DOWNLOADS.exists():
    print("Downloads folder not found!")
    sys.exit(1)

print(f"\nScanning: {DOWNLOADS}")
print("Please wait...\n")

# ==========================================
# SCANNING
# ==========================================

folder_stats = defaultdict(lambda: {"size": 0, "count": 0})
extension_stats = defaultdict(lambda: {"size": 0, "count": 0})

files_data = []
folders_data = []

total_size = 0
errors = 0

def scan_error(error):
    global errors
    errors += 1

for root, dirs, files in os.walk(
    DOWNLOADS,
    onerror=scan_error,
    followlinks=False
):
    dirs[:] = [
        d for d in dirs
        if not os.path.islink(os.path.join(root, d))
    ]

    current = Path(root)

    if current != DOWNLOADS:
        folders_data.append(current)

    for filename in files:
        path = current / filename

        try:
            if path.is_symlink():
                continue

            size = path.stat().st_size
            total_size += size

            files_data.append({
                "name": filename,
                "path": str(current),
                "size": size
            })

            ext = path.suffix.lower() or "No extension"

            extension_stats[ext]["size"] += size
            extension_stats[ext]["count"] += 1

            parent = current

            while parent != DOWNLOADS and DOWNLOADS in parent.parents:
                folder_stats[parent]["size"] += size
                folder_stats[parent]["count"] += 1
                parent = parent.parent

        except (PermissionError, OSError):
            errors += 1

# ==========================================
# SORT RESULTS
# ==========================================

largest_folders = sorted(
    [
        {
            "name": path.name,
            "path": str(path),
            "size": data["size"],
            "count": data["count"]
        }
        for path, data in folder_stats.items()
    ],
    key=lambda x: x["size"],
    reverse=True
)

largest_files = sorted(
    files_data,
    key=lambda x: x["size"],
    reverse=True
)[:100]

largest_extensions = sorted(
    [
        {
            "name": ext,
            "size": data["size"],
            "count": data["count"]
        }
        for ext, data in extension_stats.items()
    ],
    key=lambda x: x["size"],
    reverse=True
)

# ==========================================
# HELPERS
# ==========================================

def fmt_size(size):
    if size >= 1024**3:
        return f"{size / 1024**3:.3f} GB"
    if size >= 1024**2:
        return f"{size / 1024**2:.2f} MB"
    if size >= 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size} Bytes"

def make_table(headers, rows):
    result = "<div class='table-container'><table><thead><tr>"

    for header in headers:
        result += f"<th>{html.escape(str(header))}</th>"

    result += "</tr></thead><tbody>"

    for row in rows:
        result += "<tr>"
        for value in row:
            result += f"<td>{html.escape(str(value))}</td>"
        result += "</tr>"

    result += "</tbody></table></div>"
    return result

# ==========================================
# BUILD TABLES
# ==========================================

folder_rows = [
    [
        x["name"],
        fmt_size(x["size"]),
        x["count"],
        x["path"]
    ]
    for x in largest_folders[:20]
]

file_rows = [
    [
        x["name"],
        fmt_size(x["size"]),
        x["path"]
    ]
    for x in largest_files
]

extension_rows = [
    [
        x["name"],
        x["count"],
        fmt_size(x["size"])
    ]
    for x in largest_extensions
]

folder_html = make_table(
    ["Folder", "Size", "Files", "Full Path"],
    folder_rows
)

file_html = make_table(
    ["File Name", "Size", "Location"],
    file_rows
)

extension_html = make_table(
    ["Extension", "File Count", "Total Size"],
    extension_rows
)

# ==========================================
# CSS
# ==========================================

css = """
<style>
* { box-sizing: border-box; }

body {
    font-family: Segoe UI, Arial, sans-serif;
    background: #f1f5f9;
    color: #1e293b;
    padding: 30px;
}

.container {
    max-width: 1600px;
    margin: auto;
}

h1 { color: #172554; }
h2 { color: #1e40af; margin-top: 40px; }

.summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 18px;
    margin: 25px 0;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 12px;
    box-shadow: 0 3px 12px #0001;
}

.card strong {
    display: block;
    font-size: 26px;
    color: #2563eb;
    margin-top: 10px;
}

.table-container {
    overflow-x: auto;
    background: white;
    margin-top: 15px;
    border-radius: 10px;
}

table {
    width: 100%;
    border-collapse: collapse;
    min-width: 650px;
}

th {
    background: #1e3a8a;
    color: white;
    position: sticky;
    top: 0;
}

td, th {
    padding: 12px;
    border: 1px solid #e2e8f0;
    text-align: left;
    font-size: 13px;
    overflow-wrap: anywhere;
}

tr:nth-child(even) { background: #f8fafc; }
tr:hover { background: #dbeafe; }

input {
    padding: 12px;
    width: 350px;
    max-width: 100%;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    margin: 10px 0;
}

.note { color: #64748b; }

.footer {
    background: white;
    padding: 20px;
    margin-top: 40px;
    border-radius: 10px;
}

@media(max-width: 600px) {
    body { padding: 12px; }
}
</style>
"""

# ==========================================
# JAVASCRIPT - SEPARATE STRING
# ==========================================

javascript = r"""
<script>
function filterTable(input, containerId) {
    const query = input.value.toLowerCase();

    const rows = document.querySelectorAll(
        '#' + containerId + ' table tbody tr'
    );

    rows.forEach(row => {
        row.style.display =
            row.innerText.toLowerCase().includes(query) ? '' : 'none';
    });
}
</script>
"""

# ==========================================
# HTML REPORT
# ==========================================

largest_file_size = largest_files[0]["size"] if largest_files else 0

report_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Downloads Storage Analysis</title>
""" + css + """
</head>
<body>
<div class="container">

<h1>Windows Downloads - Storage Analysis</h1>

<p class="note">Generated: """ + html.escape(datetime.now().strftime("%d %B %Y, %I:%M:%S %p")) + """</p>

<p><b>Scanned location:</b> """ + html.escape(str(DOWNLOADS)) + """</p>

<div class="summary">

<div class="card">
Total Storage Used
<strong>""" + fmt_size(total_size) + """</strong>
</div>

<div class="card">
Total Files
<strong>""" + f"{len(files_data):,}" + """</strong>
</div>

<div class="card">
Total Folders
<strong>""" + f"{len(folders_data):,}" + """</strong>
</div>

<div class="card">
Largest File
<strong>""" + fmt_size(largest_file_size) + """</strong>
</div>

<div class="card">
Scan Errors
<strong>""" + str(errors) + """</strong>
</div>

</div>

<h2>Top 20 Largest Folders</h2>
<input type="text" onkeyup="filterTable(this, 'folders')" placeholder="Search folders...">
<div id="folders">
""" + folder_html + """
</div>

<h2>Top 100 Largest Individual Files</h2>
<input type="text" onkeyup="filterTable(this, 'files')" placeholder="Search files...">
<div id="files">
""" + file_html + """
</div>

<h2>Storage by File Extension</h2>
<input type="text" onkeyup="filterTable(this, 'extensions')" placeholder="Search extensions...">
<div id="extensions">
""" + extension_html + """
</div>

<div class="footer">
<b>Analysis completed successfully.</b>
<p>This is a read-only scan. No files were deleted or modified.</p>
<p>Folder sizes include nested subfolders.</p>
</div>

</div>
""" + javascript + """
</body>
</html>
"""

# ==========================================
# SAVE REPORT AND OPEN
# ==========================================

try:
    REPORT.write_text(report_html, encoding="utf-8")

    print("\n" + "=" * 60)
    print("         SCAN COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print(f"\nTotal files: {len(files_data):,}")
    print(f"Total folders: {len(folders_data):,}")
    print(f"Total storage: {fmt_size(total_size)}")
    print(f"Scan errors: {errors}")

    print("\nTOP 10 LARGEST FOLDERS")
    print("-" * 60)

    for item in largest_folders[:10]:
        print(f"{fmt_size(item['size']):>12}  {item['path']}")

    print("\nHTML REPORT:")
    print(REPORT)

    print("\nOpening browser...")

    webbrowser.open(REPORT.resolve().as_uri())

except OSError as error:
    print(f"ERROR generating report: {error}")
