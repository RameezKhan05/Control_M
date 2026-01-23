#!/bin/bash

INPUT_FILE="resources.txt"
HTML_FILE="/tmp/resource_report.html"
MAIL_TO="ops-team@example.com"
MAIL_FROM="controlm@yourdomain.com"
SUBJECT="Control-M Quantitative Resource Status"

# Start HTML
cat <<EOF > "$HTML_FILE"
<html>
<head>
<style>
  body { font-family: Arial, sans-serif; }
  table { border-collapse: collapse; width: 70%; }
  th, td { border: 1px solid #999; padding: 6px; text-align: center; }
  th { background-color: #f2f2f2; }
  .zero { background-color: #ffcccc; }
  .ok { background-color: #ccffcc; }
</style>
</head>
<body>
<h2>Control-M Quantitative Resource Status</h2>
<table>
<tr>
  <th>Resource</th>
  <th>Total</th>
  <th>Available</th>
</tr>
EOF

# Process each resource
while read -r RESOURCE
do
  [ -z "$RESOURCE" ] && continue

  OUTPUT=$(ecarqtab -list "$RESOURCE" 2>/dev/null)

  # Example expected line:
  # RESOURCE_NAME TOTAL AVAILABLE
  TOTAL=$(echo "$OUTPUT" | awk '{print $2}')
  AVAIL=$(echo "$OUTPUT" | awk '{print $3}')

  if [ "$AVAIL" = "0" ]; then
    CLASS="zero"
  else
    CLASS="ok"
  fi

  cat <<EOF >> "$HTML_FILE"
<tr class="$CLASS">
  <td>$RESOURCE</td>
  <td>$TOTAL</td>
  <td>$AVAIL</td>
</tr>
EOF

done < "$INPUT_FILE"

# Close HTML
cat <<EOF >> "$HTML_FILE"
</table>
</body>
</html>
EOF

# Send mail
{
  echo "From: $MAIL_FROM"
  echo "To: $MAIL_TO"
  echo "Subject: $SUBJECT"
  echo "MIME-Version: 1.0"
  echo "Content-Type: text/html"
  echo
  cat "$HTML_FILE"
} | sendmail -t
