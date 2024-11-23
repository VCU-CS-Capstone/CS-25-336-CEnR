import os

# Define paths
file_b_path = "Readme.md"  # Path to File B
output_dir = "Status Reports"  # Directory to save generated File A files

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Read File B content
with open(file_b_path, "r") as file_b:
    lines = file_b.readlines()

# Locate the Week Status Report table
table_start = None
for i, line in enumerate(lines):
    if line.strip().startswith("| Document"):
        table_start = i
        break

if table_start is None:
    print("Table not found in File B.")
    exit()

# Extract table rows
table_rows = lines[table_start + 1 :]

# Define File A template
file_a_template = """# *CS 25-336 CEnR*

**Students' Names: Abdul Koroma, Levi Thompson, Jasper Early, Tristan Weigand**

**Sponsor: Amy Olex**

**Faculty Advisor: Bridget McInnes**

## 1) Accomplishments this week ##
- {accomplishments}

## 2) Milestones to be completed next week ##
- {tasks}

## 3) Issues, problems or concerns ##
- {issues}
"""

# Process each row and generate new markdown files
for row in table_rows:
    # Split columns in the row
    columns = [col.strip() for col in row.split("|") if col.strip()]
    if len(columns) < 4:
        continue  # Skip incomplete rows

    week, tasks, accomplishments, issues = columns

    # Format content
    file_a_content = file_a_template.format(
        accomplishments=accomplishments,
        tasks=tasks,
        issues=issues,
    )

    # Save to a new file
    week_file = os.path.join(output_dir, f"{week.replace(' ', '_')}.md")
    with open(week_file, "w") as week_file_obj:
        week_file_obj.write(file_a_content)

print(f"Generated files are saved in the '{output_dir}' directory.")
