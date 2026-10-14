import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outDir = "D:/analysis/outputs/utopia_vendor_scrape";
const data = JSON.parse(await fs.readFile(path.join(outDir, "scrape_output.json"), "utf8"));

const sheets = [
  {
    name: "Core_Utopia_Overlap",
    rows: data.core,
    columns: [
      "Vendor Name",
      "Website",
      "Product URL",
      "Main Head",
      "Subcategory",
      "Title",
      "Prices",
      "Units shown on listing",
      "Product material",
      "Classification",
      "Notes",
      "Date Checked",
    ],
  },
  {
    name: "Backup_Gap_Fill_Offerings",
    rows: data.backup,
    columns: [
      "Vendor Name",
      "Website",
      "Product URL",
      "Main Head",
      "Subcategory",
      "Title",
      "Prices",
      "Units shown on listing",
      "Product material",
      "Classification",
      "Notes",
      "Date Checked",
    ],
  },
  {
    name: "Excluded_Unrelated",
    rows: data.excluded,
    columns: [
      "Vendor Name",
      "Website",
      "Product URL or Source URL",
      "Main Head",
      "Subcategory",
      "Title",
      "Reason Excluded",
      "Notes",
      "Date Checked",
    ],
  },
  {
    name: "Source_Log",
    rows: data.source_log,
    columns: [
      "Vendor Name",
      "Source URL",
      "Source Type",
      "What This Source Supports",
      "Date Checked",
    ],
  },
];

function colName(n) {
  let name = "";
  while (n > 0) {
    const r = (n - 1) % 26;
    name = String.fromCharCode(65 + r) + name;
    n = Math.floor((n - 1) / 26);
  }
  return name;
}

const workbook = Workbook.create();

for (const spec of sheets) {
  const sheet = workbook.worksheets.add(spec.name);
  const values = [
    spec.columns,
    ...spec.rows.map((row) => spec.columns.map((column) => row[column] ?? "")),
  ];
  const end = `${colName(spec.columns.length)}${values.length}`;
  sheet.getRange(`A1:${end}`).values = values;

  const header = sheet.getRange(`A1:${colName(spec.columns.length)}1`);
  try {
    header.format.fill.color = "#1F4E78";
    header.format.font.color = "#FFFFFF";
    header.format.font.bold = true;
  } catch {
    // Formatting is helpful but not required for a correct data workbook.
  }

  for (let idx = 1; idx <= spec.columns.length; idx += 1) {
    const letter = colName(idx);
    let width = 130;
    const headerName = spec.columns[idx - 1];
    if (/url/i.test(headerName)) width = 260;
    if (/title|material|notes|supports|reason/i.test(headerName)) width = 320;
    if (/vendor|website|classification|subcategory|main head|source type/i.test(headerName)) width = 180;
    if (/date|prices|units/i.test(headerName)) width = 120;
    try {
      sheet.getRange(`${letter}:${letter}`).format.columnWidth = width;
    } catch {
      // Keep default width if this runtime does not expose column sizing.
    }
  }
  try {
    sheet.freezePanes.freezeAt("A2");
  } catch {
    // Freeze panes are a convenience only.
  }
}

const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(outDir, "utopia_vendor_scrape_tables.xlsx");
await output.save(outputPath);

console.log(JSON.stringify({ outputPath }, null, 2));
