import csv
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime

ALIAS_FILE = "alias.txt"
HOST_FILE = "host_location.csv"
EXPECTED_FILE = "alias_expected.csv"

MAIL_TO = ["team@example.com"]
MAIL_FROM = "dns-report@example.com"
SENDMAIL_PATH = "/usr/sbin/sendmail"

# -------------------------------------------------

def get_canonical_name(alias):
    try:
        result = subprocess.run(
            ["nslookup", alias],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=5
        )

        for line in result.stdout.splitlines():
            if "canonical name" in line.lower():
                return line.split("=")[1].strip().rstrip(".")

        return "NO_CNAME_FOUND"

    except Exception:
        return "ERROR"

# -------------------------------------------------

def load_expected_mapping():
    """
    alias -> expected_hostname
    """
    mapping = {}
    with open(EXPECTED_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["alias"].lower()] = row["expected_hostname"].lower()
    return mapping

# -------------------------------------------------

def load_host_mapping():
    """
    hostname -> {dc, app, team}
    """
    mapping = {}
    with open(HOST_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["hostname"].lower()] = {
                "dc": row["dc_location"],
                "app": row["application_name"],
                "team": row["team_name"]
            }
    return mapping

# -------------------------------------------------

def generate_html_report(rows):
    html = """
    <html>
    <body>
    <h3>DNS Alias Compliance Report</h3>
    <table border="1" cellpadding="6" cellspacing="0">
        <tr>
            <th>Alias</th>
            <th>Canonical Name</th>
            <th>DC Location</th>
            <th>Application</th>
            <th>Team</th>
            <th>As Per Requirement</th>
        </tr>
    """

    for r in rows:
        color = "#ccffcc" if r["status"] == "YES" else "#ffcccc"
        html += f"""
        <tr bgcolor="{color}">
            <td>{r['alias']}</td>
            <td>{r['cname']}</td>
            <td>{r['dc']}</td>
            <td>{r['app']}</td>
            <td>{r['team']}</td>
            <td><b>{r['status']}</b></td>
        </tr>
        """

    html += """
    </table>
    </body>
    </html>
    """
    return html

# -------------------------------------------------

def send_mail(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = MAIL_FROM
    msg["To"] = ", ".join(MAIL_TO)
    msg["Subject"] = f"DNS Alias Compliance Report - {datetime.date.today()}"

    msg.attach(MIMEText(html_body, "html"))

    p = subprocess.Popen(
        [SENDMAIL_PATH, "-t", "-oi"],
        stdin=subprocess.PIPE
    )
    p.communicate(msg.as_bytes())

# -------------------------------------------------

def main():
    expected_map = load_expected_mapping()
    host_map = load_host_mapping()
    report = []

    with open(ALIAS_FILE) as f:
        next(f)  # skip header
        aliases = [line.strip() for line in f if line.strip()]

    for alias in aliases:
        cname = get_canonical_name(alias)
        cname_l = cname.lower()

        # Compliance check
        expected = expected_map.get(alias.lower(), "")
        status = "YES" if expected and expected in cname_l else "CHECK"

        # Host metadata lookup
        dc = app = team = "UNKNOWN"
        for host, meta in host_map.items():
            if host in cname_l:
                dc = meta["dc"]
                app = meta["app"]
                team = meta["team"]
                break

        report.append({
            "alias": alias,
            "cname": cname,
            "dc": dc,
            "app": app,
            "team": team,
            "status": status
        })

    html = generate_html_report(report)
    send_mail(html)

    print("Compliance report generated and mail sent.")

# -------------------------------------------------

if __name__ == "__main__":
    main()
