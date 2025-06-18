import pandas as pd
from lxml import etree

df = pd.read_excel('jobs.xlsx', sheet_name='Jobs').fillna('')
root = etree.Element('DEFINITION')

def add_text_element(parent, tag, text):
    if text:
        el = etree.SubElement(parent, tag)
        el.text = text
        return el
    return None

for _, row in df.iterrows():
    job = etree.SubElement(root, 'JOB')
    def add_if(name, val): 
        if val: job.set(name, str(val))

    add_if('Folder', row['Folder'])
    add_if('Name', row['Job Name'])
    add_if('Type', row['Type'])
    add_if('Application', row['Application'])
    add_if('SubApplication', row['Sub‑Application'])
    add_if('Description', row['Description'])
    add_if('Host', row['Host'])
    add_if('RunAs', row['Run As'])
    add_if('MaxRerun', row['MaxRerun'])
    add_if('Retries', row['Retries'])

    if row['Type'] == 'Command':
        add_if('Command', row['Command'])
    elif row['Type'] == 'Script':
        add_if('FileName', row['FileName'])
        add_if('ScriptPath', row['ScriptPath'])
    elif row['Type'] == 'EmbeddedScript':
        add_if('FileName', row['FileName'])
        add_if('Script', row['ScriptContent'])

    # Schedule
    sched = etree.SubElement(job, 'SCHED_TAB')
    add_if_sched = lambda tag, val: sched.set(tag, val) if val else None
    add_if_sched('Days', row['Days'])
    if row['Cyclic']:
        sched.set('Cyclic', str(row['Cyclic']))
        if row['Interval']:
            sched.set('Interval', str(row['Interval']))
    time_elem = etree.SubElement(sched, 'Time')
    if row['From']: time_elem.set('From', str(row['From']).zfill(4))
    if row['Until']: time_elem.set('Until', str(row['Until']))

    # In Conditions
    if row['In Conditions']:
        inconds = etree.SubElement(job, 'INCOND')
        for cond in str(row['In Conditions']).split(';'):
            cond_name, _, odate = cond.partition(' ')
            etree.SubElement(inconds, 'INCONDNAME', Name=cond_name.strip(), ODATE=odate.strip() or "ODAT")

    # Out Conditions
    if row['Out Conditions']:
        outconds = etree.SubElement(job, 'OUTCOND')
        for cond in str(row['Out Conditions']).split(';'):
            cond_name, _, odate = cond.partition(' ')
            etree.SubElement(outconds, 'OUTCONDNAME', Name=cond_name.strip(), ODATE=odate.strip() or "ODAT", Sign='ADD')

    # On OK Action
    if row['On OK Action']:
        onok = etree.SubElement(job, 'ON', STAT='OK')
        for action in str(row['On OK Action']).split(';'):
            if action.startswith("DO SHOUT="):
                msg = action.split("=", 1)[1]
                shout = etree.SubElement(onok, 'SHOUT')
                shout.set('MESSAGE', msg)
                if row['Shout Destination']:
                    shout.set('DEST', row['Shout Destination'])
            elif action.strip() == 'DO RERUN':
                etree.SubElement(onok, 'RERUN')

    # On NotOK Action
    if row['On NotOK Action']:
        notok = etree.SubElement(job, 'ON', STAT='NOTOK')
        for action in str(row['On NotOK Action']).split(';'):
            if action.startswith("DO SHOUT="):
                msg = action.split("=", 1)[1]
                shout = etree.SubElement(notok, 'SHOUT')
                shout.set('MESSAGE', msg)
                if row['Shout Destination']:
                    shout.set('DEST', row['Shout Destination'])
            elif action.strip() == 'DO RERUN':
                etree.SubElement(notok, 'RERUN')

    # Variables
    if row['Variables']:
        vars_el = etree.SubElement(job, 'VARIABLES')
        for var_pair in str(row['Variables']).split(';'):
            if '=' in var_pair:
                name, val = var_pair.split('=', 1)
                etree.SubElement(vars_el, 'VARIABLE', NAME=name.strip(), VALUE=val.strip())

# Save the XML
tree = etree.ElementTree(root)
tree.write('jobs.xml', pretty_print=True, encoding='utf-8', xml_declaration=True)
print("jobs.xml created successfully.")
