import os

# Define the base directory for Status Reports relative to the script's location
src_dir = os.path.dirname(__file__)  # Directory where the script is located
base_dir = os.path.join(src_dir, "../Status Reports")  # Path to the Status Reports directory
file_b_path = os.path.join(base_dir, "Readme.md")  # Path to Readme.md
output_dir = base_dir  # Output files in the Status Reports directory

# Ensure the Status Reports directory exists
os.makedirs(output_dir, exist_ok=True)

# Template for Status Report
status_report_template = """# *CS 25-336 CEnR*

**Students' Names: Abdul Koroma, Levi Thompson, Jasper Early, Tristan Weigand**

**Sponsor: Amy Olex**

**Faculty Advisor: Bridget McInnes**

## 1) Accomplishments this week ##
- {accomplishments}

## 2) Milestones to be completed next week ##
- {next_tasks}

## 3) Issues, problems or concerns ##
- {issues}
"""

# Read the Readme.md file
try:
    with open(file_b_path, "r") as readme_file:
        lines = readme_file.readlines()
except FileNotFoundError:
    print(f"File not found: {file_b_path}")
    exit()

# Locate the table section
table_start = None
for i, line in enumerate(lines):
    if line.strip().startswith("| Document"):
        table_start = i
        break

if table_start is None:
    print("Table not found in Readme.md.")
    exit()

# Extract table rows
table_rows = lines[table_start + 1:]

# Generate files based on the table
for row in table_rows:
    # Split row into columns
    columns = [col.strip() for col in row.split("|") if col.strip()]
    if len(columns) < 4:
        continue  # Skip incomplete rows

    document, accomplishments, next_tasks, issues = columns

    # Extract week number (e.g., "Week 1" from "Week 1 08/22 Status Report")
    document_parts = document.split(" ")
    if len(document_parts) < 2 or not document_parts[1].isdigit():
        print(f"Skipping invalid document entry: {document}")
        continue  # Skip rows that don't follow the expected format

    week_number = document_parts[1]  # Extract the week number

    # Format content for the status report
    report_content = status_report_template.format(
        accomplishments=accomplishments,
        next_tasks=next_tasks,
        issues=issues,
    )

    # Create file name (e.g., "Status Report Spring Week 1.md")
    report_filename = f"Status Report Spring Week {week_number}.md"
    report_path = os.path.join(output_dir, report_filename)

    # Write to file
    with open(report_path, "w") as report_file:
        report_file.write(report_content)

print(f"Status reports have been generated in the directory: {output_dir}")
