import csv
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime

INPUT_FILE = "input.csv"
MAIL_TO = ["team@example.com"]
MAIL_FROM = "dns-report@example.com"
SENDMAIL_PATH = "/usr/sbin/sendmail"

def get_canonical_name(alias):
    """
    Extract canonical name (CNAME) using nslookup
    """
    try:
        result = subprocess.run(
            ["nslookup", alias],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in result.stdout.splitlines():
            if "canonical name" in line.lower():
                return line.split("=")[1].strip().rstrip(".")

        return "NO_CNAME_FOUND"

    except Exception as e:
        return f"ERROR: {e}"

def identify_datacenter(cname, dc1, dc2):
    """
    Match canonical name to datacenter hostname
    """
    if dc1.lower() in cname.lower():
        return "DC1"
    elif dc2.lower() in cname.lower():
        return "DC2"
    else:
        return "UNKNOWN"

def generate_html_report(rows):
    html = """
    <html>
    <body>
    <h3>DNS Alias to Datacenter Report</h3>
    <table border="1" cellpadding="6" cellspacing="0">
        <tr>
            <th>Alias</th>
            <th>Canonical Name</th>
            <th>Datacenter</th>
        </tr>
    """

    for r in rows:
        color = "#ffcccc" if r["datacenter"] == "UNKNOWN" else "#ccffcc"
        html += f"""
        <tr bgcolor="{color}">
            <td>{r['alias']}</td>
            <td>{r['cname']}</td>
            <td>{r['datacenter']}</td>
        </tr>
        """

    html += """
    </table>
    </body>
    </html>
    """
    return html

def send_mail(html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = MAIL_FROM
    msg["To"] = ", ".join(MAIL_TO)
    msg["Subject"] = f"DNS Alias Datacenter Report - {datetime.date.today()}"

    msg.attach(MIMEText(html_body, "html"))

    p = subprocess.Popen(
        [SENDMAIL_PATH, "-t", "-oi"],
        stdin=subprocess.PIPE
    )
    p.communicate(msg.as_bytes())

def main():
    report = []

    with open(INPUT_FILE, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            alias = row["alias"]
            dc1 = row["dc1_hostname"]
            dc2 = row["dc2_hostname"]

            cname = get_canonical_name(alias)
            dc = identify_datacenter(cname, dc1, dc2)

            report.append({
                "alias": alias,
                "cname": cname,
                "datacenter": dc
            })

    html = generate_html_report(report)
    send_mail(html)

    print("DNS report generated and mail sent.")

if __name__ == "__main__":
    main()
