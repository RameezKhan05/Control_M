import pandas as pd
from lxml import etree

# Load Excel
df = pd.read_excel('controlm_jobs_full_tags.xlsx', engine='openpyxl').fillna('')

# Create root
root = etree.Element("DEFTABLE")

# Group by folder
for folder_name, group in df.groupby("Folder Name"):
    folder_elem = etree.SubElement(root, "SMART_FOLDER", FOLDER_NAME=folder_name)

    for _, row in group.iterrows():
        job_attribs = {k: str(v) for k, v in row.items() if k not in [
            "Folder Name", "Variables", "SHOUT_WHEN", "SHOUT_TIME", "SHOUT_URGENCY", "SHOUT_DEST", 
            "SHOUT_MESSAGE", "ON_NOTOK_DOSHOUT_MESSAGE", "ON_NOTOK_DOSHOUT_DEST", 
            "INCOND_NAMES", "OUTCOND_NAMES", "QUANTITATIVE_NAMES", "RULE_BASED_CALENDARS"
        ] and v != ''}
        job_elem = etree.SubElement(folder_elem, "JOB", **job_attribs)

        # Variables
        for var in row["Variables"].split(";"):
            if "=" in var:
                name, value = var.split("=", 1)
                etree.SubElement(job_elem, "VARIABLE", NAME=name.strip(), VALUE=value.strip())

        # SHOUTS
        for when, time, urg, dst, msg in zip(
            row["SHOUT_WHEN"].split(";"), row["SHOUT_TIME"].split(";"),
            row["SHOUT_URGENCY"].split(";"), row["SHOUT_DEST"].split(";"),
            row["SHOUT_MESSAGE"].split(";")
        ):
            if msg.strip():
                etree.SubElement(job_elem, "SHOUT", WHEN=when.strip(), TIME=time.strip(),
                                 URGENCY=urg.strip(), DEST=dst.strip(), MESSAGE=msg.strip())

        # ON NOTOK → DOSHOUT
        if row["ON_NOTOK_DOSHOUT_MESSAGE"] or row["ON_NOTOK_DOSHOUT_DEST"]:
            on_elem = etree.SubElement(job_elem, "ON", STMT="*", CODE="NOTOK")
            for msg, dst in zip(
                row["ON_NOTOK_DOSHOUT_MESSAGE"].split(";"),
                row["ON_NOTOK_DOSHOUT_DEST"].split(";")
            ):
                if msg.strip():
                    etree.SubElement(on_elem, "DOSHOUT", URGENCY="V", MESSAGE=msg.strip(), DEST=dst.strip())

        # INCOND
        for cond in row["INCOND_NAMES"].split(";"):
            if cond.strip():
                etree.SubElement(job_elem, "INCOND", NAME=cond.strip(), ODATE="ODAT")

        # OUTCOND
        for cond in row["OUTCOND_NAMES"].split(";"):
            if cond.strip():
                etree.SubElement(job_elem, "OUTCOND", NAME=cond.strip(), ODATE="ODAT", SIGN="+")

        # QUANTITATIVE
        for quant in row["QUANTITATIVE_NAMES"].split(";"):
            if quant.strip():
                etree.SubElement(job_elem, "QUANTITATIVE", NAME=quant.strip(), QUANT="1", ONFAIL="R", ONOK="R")

        # RULE_BASED_CALENDARS
        for cal in row["RULE_BASED_CALENDARS"].split(";"):
            if cal.strip():
                etree.SubElement(job_elem, "RULE_BASED_CALENDARS", NAME=cal.strip())

# Write XML
tree = etree.ElementTree(root)
tree.write("converted_jobs.xml", encoding='utf-8', pretty_print=True, xml_declaration=True)
print("converted_jobs.xml created successfully.")
