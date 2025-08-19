Add-Type -AssemblyName Microsoft.Office.Interop.Excel

function Get-Files($title, $filter, $multi=$true) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = $title
    $dialog.Filter = $filter
    $dialog.Multiselect = $multi
    if ($dialog.ShowDialog() -eq 'OK') { return $dialog.FileNames } else { return @() }
}

function Get-File($title, $filter) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = $title
    $dialog.Filter = $filter
    $dialog.Multiselect = $false
    if ($dialog.ShowDialog() -eq 'OK') { return $dialog.FileName } else { return "" }
}

function Get-Folder($description) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = $description
    if ($dialog.ShowDialog() -eq 'OK') { return $dialog.SelectedPath } else { return "" }
}

# ---- Step 1: Select CSV files ----
$csvFiles = Get-Files "Select CSV files to merge" "CSV Files (*.csv)|*.csv"
if ($csvFiles.Count -eq 0) { Write-Host "No CSV selected. Exiting."; exit }

# ---- Step 2: Select save folder ----
$saveFolder = Get-Folder "Select folder to save final XLSX"
if (-not $saveFolder) { Write-Host "No folder selected. Exiting."; exit }

# ---- Step 3: Select App.xlsx for lookup ----
$appFile = Get-File "Select App.xlsx file for VLOOKUP" "Excel Files (*.xlsx)|*.xlsx"
if (-not $appFile) { Write-Host "No lookup file selected. Exiting."; exit }

# ---- Step 4: Concatenate CSVs into temporary file ----
$tempFile = Join-Path $saveFolder "merged_temp.csv"
Remove-Item $tempFile -ErrorAction SilentlyContinue

foreach ($file in $csvFiles) {
    Get-Content $file | Add-Content $tempFile
}

# ---- Step 5: Open Excel and load merged CSV ----
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

$wb = $excel.Workbooks.Open($tempFile)
$ws = $wb.Sheets.Item(1)

# ---- Step 6: Insert new columns P, Q, R ----
$lastRow = $ws.Cells($ws.Rows.Count, 1).End(-4162).Row  # -4162 = xlUp

$ws.Cells(1, 16).Value2 = "trigram"
$ws.Range("P2:P$lastRow").Formula = '=MID(C2,3,3)'

$ws.Cells(1, 17).Value2 = "months_diff"
$ws.Range("Q2:Q$lastRow").Formula = '=DATEDIF(D2,TODAY(),"m")'

$ws.Cells(1, 18).Value2 = "lookup_val"
# Build external VLOOKUP formula
$appPath = $appFile.Replace("\", "\\")
$lookupFormula = "=VLOOKUP(P2,'[$(Split-Path $appPath -Leaf)]Sheet1'!I:I,1,FALSE)"
$ws.Range("R2:R$lastRow").Formula = $lookupFormula

# ---- Step 7: Save as XLSX ----
$finalFile = Join-Path $saveFolder "Final_Combined.xlsx"
$wb.SaveAs($finalFile, 51)   # 51 = xlOpenXMLWorkbook (.xlsx)
$wb.Close($false)

$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ws) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

# Remove temp file
Remove-Item $tempFile -ErrorAction SilentlyContinue

Write-Host "Done! Saved final XLSX as: $finalFile"
