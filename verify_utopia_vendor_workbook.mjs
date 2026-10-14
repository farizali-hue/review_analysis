import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const outDir = "D:/analysis/outputs/utopia_vendor_scrape";
const workbookPath = path.join(outDir, "utopia_vendor_scrape_tables.xlsx");
const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const ranges = [
  "Core_Utopia_Overlap!A1:L6",
  "Backup_Gap_Fill_Offerings!A1:L6",
  "Excluded_Unrelated!A1:I6",
  "Source_Log!A1:E6",
];

for (const range of ranges) {
  const check = await workbook.inspect({
    kind: "table",
    range,
    include: "values",
    tableMaxRows: 6,
    tableMaxCols: 12,
  });
  console.log(`RANGE ${range}`);
  console.log(check.ndjson);
}

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "final formula error scan",
});
console.log("ERROR_SCAN");
console.log(errors.ndjson);

const stats = await fs.stat(workbookPath);
console.log(JSON.stringify({ workbookPath, size: stats.size }, null, 2));
