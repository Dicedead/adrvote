function GetSciper(input){
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const myFormula = SpreadsheetApp.getActiveRange().getFormula();
  const matches = (myFormula.indexOf("(") !== -1 && myFormula.indexOf(")") !== -1) ? myFormula.slice(myFormula.indexOf("(") + 1, myFormula.indexOf(")")) : undefined;
  const range = sheet.getRange(matches);

  // Extract the link URLs for each cell in the range
  const linkUrls = range.getRichTextValues().map(ia => ia.map(row => row.getLinkUrl().slice(row.getLinkUrl().indexOf("=") + 1)));

  // Return the link URLs
  return linkUrls;
}