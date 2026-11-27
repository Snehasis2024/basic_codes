
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

TOP_FOLDERS = 20
TOP_FILES = 100

print("\n========================================")
print("      WINDOWS DOWNLOADS ANALYZER")
print("========================================")
print(f"\nScanning: {DOWNLOADS}")
print("\nPlease wait. Scanning all files and folders...\n")

if not DOWNLOADS.exists():
    print("ERROR: Downloads folder not found!")
    sys.exit(1)

# ==========================================
# SCAN FILES AND FOLDERS
# ==========================================

folder_stats = defaultdict(lambda: {"size": 0, "count": 0})
extension_stats = defaultdict(lambda: {"size": 0, "count": 0})

all_files = []
all_folders = []

total_size = 0
errors = 0

def scan_error(error):
    global errors
    errors += 1

for root, dirs, files in os.walk(
    DOWNLOADS,
    topdown=True,
    onerror=scan_error,
    followlinks=False
):
    dirs[:] = [
        d for d in dirs
        if not os.path.islink(os.path.join(root, d))
    ]

    root_path = Path(root)

    if root_path != DOWNLOADS:
        all_folders.append(root_path)

    for filename in files:
        file_path = root_path / filename

        try:
            if file_path.is_symlink():
                continue

            size = file_path.stat().st_size
            total_size += size

            all_files.append({
                "name": filename,
                "path": str(root_path),
                "full_path": str(file_path),
                "size": size
            })

            # Extension statistics
            ext = file_path.suffix.lower() or "No extension"
            extension_stats[ext]["size"] += size
            extension_stats[ext]["count"] += 1

            # Add size to current folder and all parent folders
            parent = root_path

            while parent != DOWNLOADS and DOWNLOADS in parent.parents:
                folder_stats[parent]["size"] += size
                folder_stats[parent]["count"] += 1
                parent = parent.parent

        except (PermissionError, OSError):
            errors += 1

# ==========================================
# PROCESS RESULTS
# ==========================================

largest_folders = sorted(
    [
        {
            "folder": path.name,
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
    all_files,
    key=lambda x: x["size"],
    reverse=True
)[:TOP_FILES]

largest_extensions = sorted(
    [
        {
            "extension": ext,
            "size": data["size"],
            "count": data["count"]
        }
        for ext, data in extension_stats.items()
    ],
    key=lambda x: x["size"],
    reverse=True
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def mb(size):
    return size / (1024 ** 2)

def gb(size):
    return size / (1024 ** 3)

def fmt_size(size):
    if size >= 1024 ** 3:
        return f"{gb(size):.3f} GB"
    return f"{mb(size):,.2f} MB"

def safe(value):
    return html.escape(str(value))

def make_table(headers, rows):
    output = "<div class='table-container'><table><thead><tr>"

    for header in headers:
        output += f"<th>{safe(header)}</th>"

    output += "</tr></thead><tbody>"

    for row in rows:
        output += "<tr>"
        for item in row:
            output += f"<td>{safe(item)}</td>"
        output += "</tr>"

    output += "</tbody></table></div>"
    return output

# ==========================================
# CREATE FOLDER TABLE
# ==========================================

folder_rows = []

for item in largest_folders:
    folder_rows.append([
        item["folder"],
        fmt_size(item["size"]),
        f"{mb(item['size']):,.2f}",
        f"{item['count']:,}",
        item["path"]
    ])

folder_html = make_table(
    ["Folder", "Size", "Size (MB)", "Files", "Full Path"],
    folder_rows
)

# ==========================================
# CREATE FILE TABLE
# ==========================================

file_rows = []

for item in largest_files:
    file_rows.append([
        item["name"],
        fmt_size(item["size"]),
        f"{mb(item['size']):,.2f}",
        item["path"]
    ])

file_html = make_table(
    ["File Name", "Size", "Size (MB)", "Location"],
    file_rows
)

# ==========================================
# CREATE EXTENSION TABLE
# ==========================================

extension_rows = []

for item in largest_extensions:
    extension_rows.append([
        item["extension"],
        item["count"],
        fmt_size(item["size"]),
        f"{mb(item['size']):,.2f}"
    ])

extension_html = make_table(
    ["Extension", "File Count", "Total Size", "Size (MB)"],
    extension_rows
)

# ==========================================
# SUMMARY
# ==========================================

largest_file_size = (
    largest_files[0]["size"] if largest_files else 0
)

# ==========================================
# HTML DESIGN
# ==========================================

style = """
<style>
* { box-sizing: border-box; }

body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #f1f5f9;
    color: #1e293b;
    padding: 30px;
    margin: 0;
}

.container {
    max-width: 1600px;
    margin: auto;
}

h1 {
    color: #172554;
    font-size: 30px;
}

h2 {
    color: #1e40af;
    margin-top: 40px;
}

.note {
    color: #64748b;
}

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
    box-shadow: 0 3px 12px #00000010;
}

.card strong {
    display: block;
    font-size: 27px;
    color: #2563eb;
    margin-top: 10px;
    overflow-wrap: anywhere;
}

.table-container {
    overflow-x: auto;
    background: white;
    border-radius: 10px;
    margin-top: 15px;
}

table {
    border-collapse: collapse;
    width: 100%;
    background: white;
    min-width: 650px;
}

th {
    background: #1e3a8a;
    color: white;
    position: sticky;
    top: 0;
    cursor: pointer;
}

td, th {
    padding: 12px;
    border: 1px solid #e2e8f0;
    text-align: left;
    font-size: 13px;
    overflow-wrap: anywhere;
}

tr:nth-child(even) {
    background: #f8fafc;
}

tr:hover {
    background: #dbeafe;
}

input {
    padding: 12px;
    width: 350px;
    max-width: 100%;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    margin: 10px 0;
}

.footer {
    margin-top: 50px;
    padding: 20px;
    color: #64748b;
    background: white;
    border-radius: 10px;
}

@media(max-width: 600px) {
    body { padding: 12px; }
}
</style>
"""

# ==========================================
# GENERATE SEARCHABLE HTML
# ==========================================

html_report = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Downloads Storage Analysis</title>
{style}
</head>

<body>
<div class="container">

<h1>Windows Downloads - Storage Analysis</h1>

<p class="note">
Generated: {datetime.now().strftime("%d %B %Y, %I:%M:%S %p")}
</p>

<p><b>Scanned Location:</b> {safe(DOWNLOADS)}</p>

<div class="summary">

<div class="card">
Total Storage Used
<strong>{gb(total_size):.3f} GB</strong>
</div>

<div class="card">
Total Files
<strong>{len(all_files):,}</strong>
</div>

<div class="card">
Total Folders
<strong>{len(all_folders):,}</strong>
</div>

<div class="card">
Largest File
<strong>{fmt_size(largest_file_size)}</strong>
</div>

<div class="card">
Scan Errors
<strong>{errors}</strong>
</div>

</div>

<h2>Top 20 Largest Folders</h2>
<input type="text" onkeyup="filterTable(this, 'folders')"
placeholder="Search folders...">
<div id="folders">
{make_table(
    ["Folder", "Size", "Size (MB)", "Files", "Full Path"],
    folder_rows[:TOP_FOLDERS]
)}
</div>

<h2>Top 100 Largest Individual Files</h2>
<input type="text" onkeyup="filterTable(this, 'files')"
placeholder="Search files...">
<div id="files">
{file_html}
</div>

<h2>Storage by File Extension</h2>
<input type="text" onkeyup="filterTable(this, 'extensions')"
placeholder="Search extensions...">
<div id="extensions">
{extension_html}
</div>

<div class="footer">
<p><b>Analysis completed successfully.</b></p>
<p>
Folder sizes include all nested files and subfolders.
This is a read-only analysis. No files were deleted or modified.
</p>
<p>Report generated by Python Downloads Analyzer.</p>
</div>

</div>

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

</body>
</html>
"""

# ==========================================
# SAVE AND OPEN REPORT
# ==========================================

try:
    REPORT.write_text(html_report, encoding="utf-8")

    print("\n========================================")
    print("       SCAN COMPLETED SUCCESSFULLY")
    print("========================================")

    print(f"\nTotal files       : {len(all_files):,}")
    print(f"Total folders     : {len(all_folders):,}")
    print(f"Total storage     : {gb(total_size):.3f} GB")
    print(f"Scan errors       : {errors}")

    print("\nTOP 10 LARGEST FOLDERS")

    for item in largest_folders[:10]:
        print(f"{fmt_size(item['size']):>12}  {item['path']}")

    print("\nHTML REPORT:")
    print(REPORT)

    print("\nOpening report in browser...")

    webbrowser.open(REPORT.resolve().as_uri())

except OSError as error:
    print(f"\nCould not generate report: {error}")
