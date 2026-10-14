import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "D:/analysis/outputs/utopia_vendor_scrape_2026-04-28";
const payloadPath = path.join(outputDir, "scrape_payload.json");
const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));

const tableColumns = {
  Core_Utopia_Overlap: [
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
  Backup_Gap_Fill_Offerings: [
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
  Excluded_Unrelated: [
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
  Source_Log: [
    "Vendor Name",
    "Source URL",
    "Source Type",
    "What This Source Supports",
    "Date Checked",
  ],
};

function colName(index) {
  let n = index + 1;
  let out = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    out = String.fromCharCode(65 + rem) + out;
    n = Math.floor((n - 1) / 26);
  }
  return out;
}

const workbook = Workbook.create();

for (const [sheetName, columns] of Object.entries(tableColumns)) {
  const sheet = workbook.worksheets.add(sheetName);
  const rows = payload[sheetName] ?? [];
  const matrix = [
    columns,
    ...rows.map((row) => columns.map((column) => row[column] ?? "")),
  ];
  const bottomRight = `${colName(columns.length - 1)}${matrix.length}`;
  sheet.getRange(`A1:${bottomRight}`).values = matrix;
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outputDir, "utopia_vendor_product_scrape_2026-04-28.xlsx"));
console.log(JSON.stringify({
  output: path.join(outputDir, "utopia_vendor_product_scrape_2026-04-28.xlsx"),
  sheets: Object.fromEntries(Object.keys(tableColumns).map((name) => [name, payload[name]?.length ?? 0])),
}, null, 2));
