import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const coverageCsvPath = "D:/codex_variation_analysis/outputs/additionalclaims_black_seed_oil_thymo_claimwise_coverage.csv";
const matrixCsvPath = "D:/codex_variation_analysis/outputs/additionalclaims_black_seed_oil_thymo_claimwise_matrix.csv";
const outputPath = "D:/analysis/additionalclaims_black_seed_oil_thymo_claimwise_visualization.xlsx";
const previewDir = "D:/analysis/claimwise_visualization_previews";

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let inQuotes = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (inQuotes) {
      if (char === '"' && next === '"') {
        value += '"';
        index += 1;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        value += char;
      }
    } else if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      row.push(value);
      value = "";
    } else if (char === "\n") {
      row.push(value);
      rows.push(row);
      row = [];
      value = "";
    } else if (char !== "\r") {
      value += char;
    }
  }
  if (value.length > 0 || row.length > 0) {
    row.push(value);
    rows.push(row);
  }
  return rows.filter((current) => current.some((cell) => cell !== ""));
}

function rowsToObjects(rows) {
  const [headers, ...data] = rows;
  return data.map((row) => Object.fromEntries(headers.map((header, index) => [header, row[index] ?? ""])));
}

function numberValue(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function pctFormat(value) {
  return `${Number(value).toFixed(2)}%`;
}

function safeSheetName(value) {
  return value.slice(0, 31);
}

function fillMatrix(sheet, startCell, rows) {
  sheet.getRange(startCell).write(rows);
}

function styleHeader(range, fill = "#174A5B") {
  range.format = {
    fill,
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    horizontalAlignment: "Center",
    verticalAlignment: "Center",
  };
}

function setColumnWidths(sheet, widths) {
  widths.forEach((width, index) => {
    sheet.getRangeByIndexes(0, index, 1, 1).format.columnWidthPx = width;
  });
}

function coverageColor(value) {
  if (value >= 80) return "#198754";
  if (value >= 50) return "#7CB342";
  if (value >= 33.33) return "#F3C623";
  if (value > 0) return "#F59E0B";
  return "#E5E7EB";
}

const coverageRows = rowsToObjects(parseCsv(await fs.readFile(coverageCsvPath, "utf8"))).map((row) => ({
  field: row.field,
  claim: row.claim,
  coverage_pct: numberValue(row.coverage_pct),
  asin_count: numberValue(row.asin_count),
  total_asins: numberValue(row.total_asins),
  present_asins: row.present_asins,
  absent_asins: row.absent_asins,
}));

const matrixRawRows = parseCsv(await fs.readFile(matrixCsvPath, "utf8"));
const matrixHeaders = matrixRawRows[0];
const matrixObjects = rowsToObjects(matrixRawRows);
const asinHeaders = matrixHeaders.slice(4);

const fields = ["claims", "health_claims", "certifications"];
const fieldLabels = {
  claims: "Claims",
  health_claims: "Health Claims",
  certifications: "Certifications",
};

const fieldSummary = fields.map((field) => {
  const subset = coverageRows.filter((row) => row.field === field);
  const avg = subset.reduce((sum, row) => sum + row.coverage_pct, 0) / subset.length;
  return {
    field,
    label: fieldLabels[field],
    claim_count: subset.length,
    avg_coverage_pct: avg,
    max_coverage_pct: Math.max(...subset.map((row) => row.coverage_pct)),
    shared_50_plus: subset.filter((row) => row.coverage_pct >= 50).length,
    unique_to_one_asin: subset.filter((row) => row.asin_count === 1).length,
  };
});

const sortedCoverage = [...coverageRows].sort((a, b) => {
  if (b.coverage_pct !== a.coverage_pct) return b.coverage_pct - a.coverage_pct;
  if (b.asin_count !== a.asin_count) return b.asin_count - a.asin_count;
  return a.claim.localeCompare(b.claim);
});
const topCoverage = sortedCoverage.slice(0, 20);

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Dashboard");
const coverageSheet = workbook.worksheets.add("Claim Coverage");
const matrixSheet = workbook.worksheets.add("ASIN Matrix");
const summarySheet = workbook.worksheets.add("Field Summary");
const chartDataSheet = workbook.worksheets.add("Chart Data");

for (const sheet of [dashboard, coverageSheet, matrixSheet, summarySheet, chartDataSheet]) {
  sheet.showGridLines = false;
}

// Claim Coverage sheet
const coverageTableRows = [
  ["Field", "Claim", "Coverage %", "ASIN Count", "Total ASINs", "Present ASINs", "Absent ASINs"],
  ...sortedCoverage.map((row) => [
    fieldLabels[row.field],
    row.claim,
    row.coverage_pct / 100,
    row.asin_count,
    row.total_asins,
    row.present_asins,
    row.absent_asins,
  ]),
];
fillMatrix(coverageSheet, "A1", coverageTableRows);
styleHeader(coverageSheet.getRange("A1:G1"));
coverageSheet.getRange(`A1:G${coverageTableRows.length}`).format = { wrapText: true, verticalAlignment: "Top" };
coverageSheet.getRange(`C2:C${coverageTableRows.length}`).format.numberFormat = "0.00%";
setColumnWidths(coverageSheet, [130, 310, 95, 85, 85, 360, 360]);
coverageSheet.freezePanes.freezeRows(1);
coverageSheet.tables.add(`A1:G${coverageTableRows.length}`, true, "ClaimCoverageTable");
for (let rowIndex = 1; rowIndex < coverageTableRows.length; rowIndex += 1) {
  const value = sortedCoverage[rowIndex - 1].coverage_pct;
  coverageSheet.getCell(rowIndex, 2).format = {
    fill: coverageColor(value),
    font: { bold: true, color: value >= 50 ? "#FFFFFF" : "#111827" },
  };
}

// ASIN Matrix sheet
const matrixRows = [
  matrixHeaders,
  ...matrixObjects.map((row) => [
    fieldLabels[row.field] ?? row.field,
    row.claim,
    numberValue(row.coverage_pct) / 100,
    numberValue(row.asin_count),
    ...asinHeaders.map((asin) => numberValue(row[asin]) / 100),
  ]),
];
fillMatrix(matrixSheet, "A1", matrixRows);
styleHeader(matrixSheet.getRangeByIndexes(0, 0, 1, matrixHeaders.length));
matrixSheet.getRangeByIndexes(1, 2, matrixRows.length - 1, 1).format.numberFormat = "0.00%";
matrixSheet.getRangeByIndexes(1, 4, matrixRows.length - 1, asinHeaders.length).format.numberFormat = "0%";
setColumnWidths(matrixSheet, [130, 300, 95, 85, ...asinHeaders.map(() => 92)]);
matrixSheet.freezePanes.freezeRows(1);
matrixSheet.freezePanes.freezeColumns(4);
matrixSheet.tables.add(`A1:J${matrixRows.length}`, true, "ClaimMatrixTable");
for (let rowIndex = 1; rowIndex < matrixRows.length; rowIndex += 1) {
  const coverage = numberValue(matrixObjects[rowIndex - 1].coverage_pct);
  matrixSheet.getCell(rowIndex, 2).format = {
    fill: coverageColor(coverage),
    font: { bold: true, color: coverage >= 50 ? "#FFFFFF" : "#111827" },
  };
  for (let colIndex = 4; colIndex < 4 + asinHeaders.length; colIndex += 1) {
    const present = Number(matrixRows[rowIndex][colIndex]) > 0;
    matrixSheet.getCell(rowIndex, colIndex).format = {
      fill: present ? "#B7E1CD" : "#F3F4F6",
      font: { color: present ? "#14532D" : "#6B7280" },
      horizontalAlignment: "Center",
    };
  }
}

// Field Summary sheet
const summaryRows = [
  ["Field", "Claim Count", "Average Coverage %", "Max Coverage %", "Claims >=50% Coverage", "Claims Unique To One ASIN"],
  ...fieldSummary.map((row) => [
    row.label,
    row.claim_count,
    row.avg_coverage_pct / 100,
    row.max_coverage_pct / 100,
    row.shared_50_plus,
    row.unique_to_one_asin,
  ]),
];
fillMatrix(summarySheet, "A1", summaryRows);
styleHeader(summarySheet.getRange("A1:F1"));
summarySheet.getRange("C2:D4").format.numberFormat = "0.00%";
setColumnWidths(summarySheet, [150, 110, 150, 130, 165, 180]);
summarySheet.tables.add("A1:F4", true, "FieldSummaryTable");

// Dashboard sheet
dashboard.getRange("A1:H1").merge();
dashboard.getRange("A1").values = [["Black Seed Oil Claim Coverage Dashboard"]];
dashboard.getRange("A1").format = {
  fill: "#12343B",
  font: { bold: true, color: "#FFFFFF", size: 18 },
  horizontalAlignment: "Center",
};
dashboard.getRange("A2:H2").merge();
dashboard.getRange("A2").values = [[
  "Claim-wise coverage across 6 ASINs. Coverage % = ASINs containing a formalized claim / total ASINs.",
]];
dashboard.getRange("A2").format = {
  fill: "#E8F1F2",
  font: { color: "#12343B", italic: true },
  horizontalAlignment: "Center",
};

const avgCoverage = coverageRows.reduce((sum, row) => sum + row.coverage_pct, 0) / coverageRows.length;
const kpiRows = [
  ["Metric", "Value"],
  ["Total formalized claim rows", coverageRows.length],
  ["ASINs compared", asinHeaders.length],
  ["Average coverage", avgCoverage / 100],
  ["Claims shared by >=50% ASINs", coverageRows.filter((row) => row.coverage_pct >= 50).length],
  ["Claims present in all ASINs", coverageRows.filter((row) => row.coverage_pct === 100).length],
];
fillMatrix(dashboard, "A4", kpiRows);
styleHeader(dashboard.getRange("A4:B4"), "#245A64");
dashboard.getRange("B7:B7").format.numberFormat = "0.00%";
setColumnWidths(dashboard, [190, 300, 100, 90, 110, 160, 130, 130, 130, 130, 130, 130]);

const dashSummaryRows = [
  ["Field", "Claim Count", "Average Coverage %", ">=50% Coverage"],
  ...fieldSummary.map((row) => [row.label, row.claim_count, row.avg_coverage_pct / 100, row.shared_50_plus]),
];
fillMatrix(dashboard, "D4", dashSummaryRows);
styleHeader(dashboard.getRange("D4:G4"), "#245A64");
dashboard.getRange("F5:F7").format.numberFormat = "0.00%";

const topRows = [
  ["Field", "Claim", "Coverage %", "ASIN Count"],
  ...topCoverage.map((row) => [fieldLabels[row.field], row.claim, row.coverage_pct / 100, row.asin_count]),
];
fillMatrix(dashboard, "A11", topRows);
styleHeader(dashboard.getRange("A11:D11"), "#245A64");
dashboard.getRange(`C12:C${11 + topCoverage.length}`).format.numberFormat = "0.00%";
dashboard.getRange(`A11:D${11 + topCoverage.length}`).format = { wrapText: true, verticalAlignment: "Top" };
dashboard.getRange(`C12:C${11 + topCoverage.length}`).format = {
  wrapText: false,
  horizontalAlignment: "Center",
};
dashboard.getRange(`C12:C${11 + topCoverage.length}`).format.numberFormat = "0.00%";
dashboard.getRange("A11:D31").format.rowHeightPx = 34;

// Helper ranges for charts.
const chartFieldRows = [
  ["Field", "Average Coverage %"],
  ...fieldSummary.map((row) => [row.label, row.avg_coverage_pct / 100]),
];
fillMatrix(chartDataSheet, "A1", chartFieldRows);
chartDataSheet.getRange("B2:B4").format.numberFormat = "0.00%";
const chartTopRows = [
  ["Claim", "Coverage %"],
  ...topCoverage.slice(0, 12).map((row) => [`${fieldLabels[row.field]}: ${row.claim}`, row.coverage_pct / 100]),
];
fillMatrix(chartDataSheet, "D1", chartTopRows);
chartDataSheet.getRange("E2:E13").format.numberFormat = "0.00%";
styleHeader(chartDataSheet.getRange("A1:B1"), "#245A64");
styleHeader(chartDataSheet.getRange("D1:E1"), "#245A64");
setColumnWidths(chartDataSheet, [150, 130, 30, 360, 130]);

const fieldChart = dashboard.charts.add("bar", chartDataSheet.getRange("A1:B4"));
fieldChart.title = "Average Coverage By Field";
fieldChart.hasLegend = false;
fieldChart.xAxis = { axisType: "textAxis" };
fieldChart.yAxis = { numberFormatCode: "0%" };
fieldChart.setPosition("F11", "L23");

const topChart = dashboard.charts.add("bar", chartDataSheet.getRange("D1:E13"));
topChart.title = "Top Shared Claims";
topChart.hasLegend = false;
topChart.xAxis = { axisType: "textAxis" };
topChart.yAxis = { numberFormatCode: "0%" };
topChart.setPosition("F25", "L45");

dashboard.freezePanes.freezeRows(2);

await fs.mkdir(previewDir, { recursive: true });
for (const sheetName of ["Dashboard", "Claim Coverage", "ASIN Matrix", "Field Summary"]) {
  const preview = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  await fs.writeFile(
    `${previewDir}/${safeSheetName(sheetName).replaceAll(" ", "_")}.png`,
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(`Saved ${outputPath}`);
