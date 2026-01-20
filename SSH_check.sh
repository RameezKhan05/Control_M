#!/bin/bash

HOST_FILE="hosts.txt"
HTML_REPORT="/tmp/ssh_report.html"
CONNECT_TIMEOUT=10

# Start HTML
cat <<EOF > "$HTML_REPORT"
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>SSH Connectivity Report</title>
<style>
body { font-family: Arial, sans-serif; background:#f5f5f5; }
h2 { text-align:center; }
table {
  border-collapse: collapse;
  width: 90%;
  margin: 20px auto;
  background: #fff;
}
th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}
th {
  background: #333;
  color: #fff;
}
.ok { color: green; font-weight: bold; }
.nok { color: red; font-weight: bold; }
.footer {
  text-align:center;
  font-size: 12px;
  color: #666;
}
</style>
</head>
<body>
<h2>SSH Connectivity Report</h2>
<table>
<tr>
  <th>User</th>
  <th>Host</th>
  <th>Status</th>
  <th>Details</th>
</tr>
EOF

# Process hosts
while read -r ENTRY; do
    [[ -z "$ENTRY" ]] && continue

    USER="${ENTRY%@*}"
    HOST="${ENTRY#*@}"

    OUTPUT=$(ssh \
        -o BatchMode=yes \
        -o ConnectTimeout=$CONNECT_TIMEOUT \
        -o StrictHostKeyChecking=accept-new \
        "$USER@$HOST" "echo SSH_OK" 2>&1)

    EXIT_CODE=$?

    if [[ $EXIT_CODE -eq 0 ]]; then
        STATUS="OK"
        CLASS="ok"
        DETAILS="SSH connection successful"
    else
        STATUS="NOK"
        CLASS="nok"
        DETAILS=$(echo "$OUTPUT" | head -n 1)
    fi

    cat <<EOF >> "$HTML_REPORT"
<tr>
  <td>$USER</td>
  <td>$HOST</td>
  <td class="$CLASS">$STATUS</td>
  <td>$DETAILS</td>
</tr>
EOF

done < "$HOST_FILE"

# Close HTML
cat <<EOF >> "$HTML_REPORT"
</table>
<div class="footer">
Generated on $(date)
</div>
</body>
</html>
EOF
