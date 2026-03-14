// Coaster Club - Google Apps Script Web App
// Paste this into your Apps Script project at script.google.com
// Spreadsheet name: "Reverie Coaster Club"
// Tabs are created automatically per year (e.g. "2026", "2027")

const SPREADSHEET_ID = "1t6gxhzRyrQSZpKicNMS3ayVzJcqrohfuOnyrHOaQZnQ";

function getOrCreateYearSheet(ss) {
  const year = new Date().getFullYear().toString();
  let sheet = ss.getSheetByName(year);

  if (!sheet) {
    sheet = ss.insertSheet(year);
    sheet.appendRow([
      "Timestamp",
      "Full Name",
      "Email",
      "Phone",
      "Name on Coaster",
    ]);
    sheet.getRange(1, 1, 1, 5).setFontWeight("bold");
  }

  return sheet;
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = getOrCreateYearSheet(ss);

    sheet.appendRow([
      new Date().toLocaleString(),
      data.fullName || "",
      data.email || "",
      data.phone || "",
      data.coasterName || "",
    ]);

    return ContentService.createTextOutput(
      JSON.stringify({ success: true }),
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ success: false, error: err.message }),
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

// GET handler so the URL doesn't 404 if someone opens it in a browser
function doGet() {
  return ContentService.createTextOutput(
    "Coaster Club endpoint is live.",
  ).setMimeType(ContentService.MimeType.TEXT);
}
