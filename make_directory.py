#!/usr/bin/env python

import click
import re
import sys
import hashlib
import tempfile

@click.group()
def cli():
    pass


@cli.command("make-all-pdfs")
@click.option("--src", help="MCPS export .xlsx", required=True)
@click.pass_context
def make_all_pdfs(ctx, src):
    """setup whatever is needed"""

    pool = xlsx_to_pool(src)
    pool_to_pdf1(pool)


def partition(v):
    out = None
    if type(v) == list:
        out = v
    elif type(v) == str:
        out = [v]
    else:
        out = []
    return out


def pool_to_teacher_grade(pool):
    out = {}
    for entry in pool:
        grade = entry.get("Grade")
        teacher = entry.get("Homeroom Teacher")
        if grade not in out:
            out[grade] = {}
        if teacher not in out[grade]:
            out[grade][teacher] = []
        out[grade][teacher].append(entry)

    sorted_out = {
        "SE PreK": {},
        "K": {},
    }
    for grade in sorted(out):
        sorted_out[grade] = {}
        for teacher in sorted(out[grade]):
            # sorted_out[grade][teacher] = sorted(out[grade][teacher], key=lambda x: x.get("Student"))
            sorted_out[grade][teacher] = out[grade][teacher]
    return sorted_out


def pool_to_teacher_grade_student(pool):
    out = {}
    tg = pool_to_teacher_grade(pool)
    for grade in tg:
        out[grade] = {}
        for teacher in tg[grade]:
            students = []
            for entry in tg[grade][teacher]:
                student = entry.get("Student")
                if student not in students:
                    students.append(student)
                # students[student].append(entry)
            out[grade][teacher] = sorted(students)
    return out


def student_uid(entry):
    student_name = entry.get("Student")
    dob = entry.get("Birth Date")
    # grade = entry.get("Grade")
    # teacher = entry.get("Homeroom Teacher")
    uid = hashlib.sha1((student_name + str(dob)).encode("utf-8")).hexdigest()
    return uid


def pool_to_student_relations(pool):

    out = {}
    for entry in pool:
        student_name = entry.get("Student")
        dob = entry.get("Birth Date")
        grade = entry.get("Grade")
        teacher = entry.get("Homeroom Teacher")

        phone = entry.get("Phone")
        address1 = entry.get("Address1")
        address2 = entry.get("Address2")
        relation = entry.get("Relation")
        relation_name = entry.get("Name")
        relation_cell = entry.get("Cell Phone")
        relation_email = entry.get("Email")

        uid = student_uid(entry)
        if uid not in out:
            out[uid] = {}
        out[uid]["Student"] = student_name
        out[uid]["Grade"] = grade
        out[uid]["Homeroom Teacher"] = teacher
        if "Relations" not in out[uid]:
            out[uid]["Relations"] = []
        out[uid]["Relations"].append(
            {
                "Relation": relation,
                "Name": relation_name,
                "Cell Phone": relation_cell,
                "Email": relation_email,
            }
        )
        if address1 != withheld_marker:
            out[uid]["Address1"] = address1
        if address2 != withheld_marker:
            out[uid]["Address2"] = address2
        if phone != withheld_marker:
            out[uid]["Phone"] = phone
    return out


def pool_to_pdf1(pool):

    from hashlib import sha1
    import datetime
    import html
    import collections

    import reportlab.platypus
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, Spacer, Table
    from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.platypus.frames import Frame

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=TA_JUSTIFY))

    class MyDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kw):
            self.allowSplitting = 0
            BaseDocTemplate.__init__(
                self,
                filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
                **kw,
            )
            template = PageTemplate(
                "normal",
                [Frame(0.5 * inch, 0.1 * inch, 7.5 * inch, 10.5 * inch, id="F1")],
            )
            self.addPageTemplates(template)

        def afterFlowable(self, flowable):
            "Registers TOC entries."
            if flowable.__class__.__name__ == "Paragraph":
                text = flowable.getPlainText()
                style = flowable.style.name

                if style == "Heading1":
                    level = 0
                elif style == "Heading2":
                    level = 1
                else:
                    return

                E = [level, text, self.page]
                # if we have a bookmark name append that to our notify data
                bn = getattr(flowable, "_bookmarkName", None)
                if bn is not None:
                    E.append(bn)
                self.notify("TOCEntry", tuple(E))

    h1 = ParagraphStyle(name="Heading1", fontSize=14, leading=16)

    def linkedHeading(story, text, style):
        # create bookmarkname
        bn = sha1((text + style.name).encode("utf-8")).hexdigest()
        # modify paragraph text to include an anchor point with name bn
        h = Paragraph(text + '<a name="%s"/>' % bn, style)
        # store the bookmark name on the flowable so afterFlowable can see this
        h._bookmarkName = bn
        story.append(h)

    # from reportlab.pdfgen import canvas

    #pdffn = "afile1.pdf"
    tmppdf = tempfile.NamedTemporaryFile(
        #prefix=f"variant-pdf-{now}",
        suffix=".pdf")

    doc = MyDocTemplate(tmppdf.name)
    Story = []

    ptext = "Somerset ES 2023-2024"
    linkedHeading(Story, ptext, h1)

    #formatted_time = datetime.datetime.utcnow().strftime("%Y-%m-%d at %H:%M")
    #ptext = "<font size=12>This report was generated on %s UTC</font>" % formatted_time
    #Story.append(Paragraph(html.unescape(ptext), styles["Normal"]))
    #Story.append(Spacer(1, 12))

    # number of genotypes
    story_meta_position = len(Story)

    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(thickness=4))
    Story.append(Spacer(1, 12))
    Story.append(PageBreak())


    styleSheet = getSampleStyleSheet()

    drug_h = ParagraphStyle(name="drugHeading1", fontSize=12, leading=14, leftIndent=10)
    ext_link = ParagraphStyle(name="extLink", fontSize=10, leading=12, leftIndent=25)
    student_name = ParagraphStyle(name="studentName", fontSize=16, leading=12, leftIndent=0)



    psr = pool_to_student_relations(pool)
    num_students = 0
    for uid in psr:
        student = psr[uid]
        num_students += 1
        
        address = f"{student.get('Address1','')} {student.get('Address2','')} {student.get('Phone','')}"
        Story.append(Paragraph(student['Student'], student_name))

        if phone := student.get('Phone'):
            Story.append(Paragraph(f"Phone: {phone}", styleSheet["BodyText"]))
        if student.get('Address1') or student.get('Address2'):
            address = f"{student.get('Address1','')}<br/>{student.get('Address2','')}"
            Story.append(Paragraph(address, styleSheet["BodyText"]))
        body = f"{student['Grade']} {student['Homeroom Teacher']}"
        Story.append(Paragraph(body, styleSheet["BodyText"]))

        for relation in student["Relations"]:

            any_values = [x for x in relation.values() if x != withheld_marker]

            if any_values:
                data = []
                for key, value in relation.items():
                    print(key)
                    if value:
                        data.append(
                            [
                                Paragraph(key, styleSheet["BodyText"]),
                                Paragraph(value, styleSheet["BodyText"]),
                            ]
                        )
                if data:
                    t = Table(
                        data,
                        colWidths=[2.4 * inch, 5 * inch],
                        style=[
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ],
                    )

                    Story.append(t)
        Story.append(Spacer(1, 12))


    ptext = "By Grade & Teacher"
    linkedHeading(Story, ptext, h1)
    Story.append(Spacer(1, 12))
    
    tgs = pool_to_teacher_grade_student(pool)
    for grade in tgs:
        for teacher in tgs[grade]:
            # dnbn = sha1((grade_teacher).encode("utf-8")).hexdigest()
            dnbn = ""
            Story.append(Paragraph(f"{grade} {teacher}", drug_h))
            for student in tgs[grade][teacher]:
                # print(grade, teacher, student)
                p = Paragraph(student, ext_link)
                Story.append(p)

    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(thickness=4))
    Story.append(Spacer(1, 12))
    Story.append(PageBreak())


    # grade_teacherStory = collections.defaultdict(list)

    # allGenoStory = []
    # for i, entry in enumerate(pool):
    #     var_name = entry.get("Student")
    #     # print("Working on a", entry)

    #     ht = entry.get("Homeroom Teacher")
    #     grade = entry.get("Grade")
    #     student = entry.get("Student")
    #     phone = entry.get("Phone")
    #     address1 = entry.get("Address1")
    #     address2 = entry.get("Address2")
    #     relation = entry.get("Relation")
    #     relation_name = entry.get("Name")
    #     relation_cell = entry.get("Cell Phone")
    #     relation_email = entry.get("Email")

    #     {
    #         # "Sch Num": "405",
    #         # "School": "Somerset Elementary",
    #         "Student ": "Silverman, Luke William",
    #         "Homeroom Teacher": "Davidov, Antoinette",
    #         "Grade": "K",
    #         "Birth Date": datetime.datetime(2017, 12, 23, 0, 0),
    #         "Directory Withholding-YN": "N",
    #         "Phone": "9147995319",
    #         "Address1": "4225 Sleaford Rd",
    #         "Address2": "Bethesda, MD 20814",
    #         "Relation": "Father",
    #         "Name": "Silverman, Stephen",
    #         "Cell Phone": "4105997832",
    #         "Email": "sasilverman1@gmail.com",
    #     }

    #     dn = f"{grade} {ht}"

    #     label = f"#{i+1} {var_name}"
    #     target = f"#{i+1} {var_name}"
    #     varbn = sha1((target).encode("utf-8")).hexdigest()

    #     body = f"""{student}
    #     {phone}
    #     {address1}
    #     {address2}
    #     {relation}
    #     {relation_name}
    #     {relation_cell}
    #     {relation_email}
        
    #     """
    #     # p = Paragraph(body, ext_link)
    #     # grade_teacherStory[dn].append(p)

    #     allGenoStory.append(Paragraph(f'<a name="{varbn}"/>', styles["Normal"]))
    #     allGenoStory.append(Paragraph(html.unescape(target), styles["Normal"]))

    #     data = []
    #     chunksize = 4000
    #     for key in entry.keys():
    #         if key in ["Sch Num", "School", "Student", "Directory Withholding-YN"]:
    #             continue
    #         ready = html.escape(str(entry.get(key)))
    #         data.append(
    #             [
    #                 Paragraph(key, styleSheet["BodyText"]),
    #                 Paragraph(ready, styleSheet["BodyText"]),
    #             ]
    #         )

    #     t = Table(
    #         data,
    #         colWidths=[2.4 * inch, 5 * inch],
    #         style=[
    #             ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    #         ],
    #     )

    #     allGenoStory.append(t)
    #     allGenoStory.append(Spacer(1, 12))
    #     num_students += 1

    # #    for grade_teacher in sorted(grade_teacherStory):
    # #        dnbn = sha1((grade_teacher).encode("utf-8")).hexdigest()
    # #        Story.append(Paragraph(f'<a name="{dnbn}"/>{grade_teacher}', drug_h))
    # #        Story.extend(grade_teacherStory[grade_teacher])

    # Story.append(Spacer(1, 12))
    # Story.append(HRFlowable(thickness=4))
    # Story.append(Spacer(1, 12))
    # Story.append(PageBreak())

    # for thing in allGenoStory:
    #     Story.append(thing)

    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(thickness=4))
    Story.append(Spacer(1, 12))
    Story.append(PageBreak())

    Story[story_meta_position] = Paragraph(
        f"Number of students: {num_students}", styles["Normal"]
    )

    success = False
    try:
        doc.multiBuild(Story)
        success = True
    except reportlab.platypus.doctemplate.LayoutError as e:
        print(e)
        pdb.set_trace()
        while not success:
            try:
                doc.build(Story)
            except Exception as e:
                print("Unexpected error:", sys.exc_info()[0])
                print("exception:", e)
                print("error:", sys.exc_info()[1])
                traceback.print_exc(file=sys.stdout)
                print("removing %s" % Story[0])
                Story = Story[1:]

    if success:
        from shutil import copyfile

        copyfile(tmppdf.name, "mypdf1.pdf")
    else:
        current_app.logger.info("failed to make the pdf")

    return


withheld_marker = "(withheld)"


def xlsx_to_pool(src):
    from openpyxl import load_workbook

    wb = load_workbook(filename=src)
    sheet = wb.active

    col_labels = []
    for row in sheet.iter_rows(min_row=0, min_col=0, max_row=1, max_col=4000):
        for cell in row:
            # print(cell.row, cell.column, cell.value)
            val = cell.value
            if val:
                val = val.strip()
            col_labels.append(val)
    while col_labels[-1] is None:
        col_labels.pop()
    num_cols = len(col_labels)

    Directory_Withholding_key = "Directory Withholding-YN"
    if Directory_Withholding_key not in col_labels:
        print(f"{Directory_Withholding_key} was not found. not safe to load this")
        return

    num_withheld = 0
    num_accepted = 0
    pool = []
    for row in sheet.iter_rows(
        min_row=2,
        min_col=0,
        # max_row=6,
        max_col=num_cols,
    ):
        adict = dict(zip(col_labels, [x.value for x in row]))

        Directory_Withholding = adict.get(Directory_Withholding_key)
        if Directory_Withholding == "N":
            num_accepted += 1
            pass
        else:
            num_withheld += 1
            for k in [
                "Sch Num",
                "School",
                #'Student ', 'Homeroom Teacher', 'Grade',
                "Birth Date",
                #'Directory Withholding-YN',
                "Phone",
                "Address1",
                "Address2",
                "Relation",
                "Name",
                "Cell Phone",
                "Email",
            ]:
                adict[k] = withheld_marker
            # continue
            if Directory_Withholding == "Y":
                pass
            else:
                print(
                    f"{Directory_Withholding_key} = '{Directory_Withholding}' ... not understood, so dropping this record"
                )

        # print(adict)
        pool.append(adict)
        # print(row)
    print(f"{num_withheld=} {num_accepted=}")
    return pool


# END_YEAR = 2024


# all_hubs = set()


def hub_name(s):
    if s == "teacher-":
        breakpoint()
        return None
    if "+" in s:
        breakpoint()
    s = s.replace(", ", "-")
    s = s.replace(",", "-")
    s = s.replace(" ", "-")
    all_hubs.add(s)
    return s


# seen_long_fams = {}
# seen_short_fams = {}
# seen_complex = {}


def normalize(name, fam_id):
    if name not in seen_complex:
        seen_complex[name] = {fam_id: 1}

    if fam_id not in seen_complex[name]:
        idx = max(seen_complex[name].values()) + 1
        seen_complex[name][fam_id] = idx

    idx = seen_complex[name][fam_id]
    if idx == 1:
        long_name = name
    else:
        long_name = f"{name}#{idx}"
    return long_name


def main(fn=None):
    if fn is None:
        fn = "StudentDirRaw.tsv"

    extra_org_roles = {
        "victoria.levitas@gmail.com": "Admin, Contact, Member, Customer, Officer",
        "cariaso@gmail.com": "Admin, Officer",
        "chris.press@gmail.com": "Officer",
        # "gillianedick@gmail.com": "Admin, Contact, Member, Customer, Officer",
        # "sarahsandelius@gmail.com": "Admin, Officer",
        # "ckeeling83@gmail.com": "Officer",
        # "jacquelyn_quan@yahoo.com": "Officer",
        # "cherinacyborski@hotmail.com": "Officer",
        # "meghan.holohan@gmail.com": "Officer",
        # "babytrekie@yahoo.com": "Officer",
        # "tajpowell10@gmail.com": "Officer",
        # "wanujarie@gmail.com": "Officer",
        # "katejulian@yahoo.com": "Officer",  # Kate Julian
        # "merritt.m.crowder@mcpsmd.org" :"false",
        # "gabrielle@enrichment-academies.com" :"false",
        # "cynthia_a_houston@mcpsmd.org" :"false",
    }

    errors = False
    fam = {}

    with open(fn, "rt") as infh:
        header = [x.strip() for x in infh.readline().rstrip().split("\t")]
        next_fam_id = 123
        seen_fam = {}
        seen_fam_name = {}
        seen_fam_name_rev = {}

        grade_teachers = {}

        for line in infh:
            fam_id = None
            parts = [x.strip() for x in line.rstrip().split("\t")]
            row = dict(zip(header, parts))

            student_lastname, student_firstname = [
                x.strip() for x in row["Student"].split(",", 2)
            ]
            parent_lastname, parent_firstname = [
                x.strip() for x in row["Name"].split(",", 2)
            ]

            fam_key = "Address1"
            fam_alt_key = "Phone"
            fam_val = row[fam_key]
            if not fam_val.strip():
                fam_val = row[fam_alt_key]
                if not fam_val.strip():
                    print(f"no {fam_key} for {line.rstrip()}")
                    breakpoint()

            if fam_val in seen_fam:
                fam_id = seen_fam[fam_val]
            else:
                fam_id = f"fam{next_fam_id}"
                next_fam_id += 1
                seen_fam[fam_val] = fam_id

            # fam_id2fam_name(fam_id, fam_val, name=student_lastname)

            # print(f"##{fam_id}\t{row}##")

            grade = row["Grade"]
            teacher = row["Homeroom Teacher"]
            if grade not in grade_teachers:
                grade_teachers[grade] = {}
            if teacher not in grade_teachers[grade]:
                grade_teachers[grade][teacher] = 0
            grade_teachers[grade][teacher] += 1
            student_info = {
                "grade": row["Grade"],
                "teacher": row["Homeroom Teacher"],
                "firstname": student_firstname,
                "lastname": student_lastname,
                "phone": row["Phone"],
                "address1": row["Address1"],
                "address2": row["Address2"],
            }
            parent_info = {
                "firstname": parent_firstname,
                "lastname": parent_lastname,
                "phone": row.get("Cell Phone", row["Phone"]),
                "email": row.get("Email"),
                "address1": row["Address1"],
                "address2": row["Address2"],
            }
            parent_errors = False
            if not parent_info["email"]:
                errors = True
                parent_errors = True
                print(f"*** no parent email *** {parent_info}")

            row_info = {
                "student": [
                    student_info,
                ],
                "parent": [],
            }
            if not parent_errors:
                row_info["parent"].append(parent_info)

            if fam_id not in fam:
                fam[fam_id] = row_info
            else:
                if parent_info not in fam[fam_id].get("parent", []):
                    fam[fam_id]["parent"].append(parent_info)
                if student_info not in fam[fam_id]["student"]:
                    fam[fam_id]["student"].append(student_info)

        if errors:
            print("please fix the errors above")

        for grade in sorted(grade_teachers):
            for teacher in sorted(grade_teachers[grade]):
                print(f"grade-{grade}-{hub_name(teacher)}")

        if True:
            contacts = []

            for fam_id in fam:
                afam = fam[fam_id]

                afam_name = None

                fam_grades = set()
                fam_teachers = set()

                for astudent in afam["student"]:
                    fam_grades.add(astudent["grade"])

                    if afam_name is None:
                        afam_name = astudent["lastname"]

                    if not astudent["teacher"]:
                        errors = True
                        print(
                            f"*** Warning no teacher for fam_id={fam_id} student={astudent}"
                        )
                    else:
                        fam_teachers.add(astudent["teacher"])

                any_email = False
                for aparent in afam["parent"]:
                    if aparent["email"]:
                        any_email = True
                if not any_email:
                    errors = True
                    print(
                        f"*** Warning no family email for  fam_id={fam_id} student={astudent}"
                    )

                for aparent in afam["parent"]:
                    acontact = {}
                    # RoleName = 'parent_guardian'
                    RoleName = "Contact"

                    if afam_name is None:
                        afam_name = aparent["lastname"]

                    # RoleName = 'Parent/Guardian'
                    ##'RoleName:Year' where:
                    ##* 'RoleName' is the name of the system defined Role ie 'admin', 'parent_guardian', 'contact'
                    ##* 'Year' is an option parameter to define specific year for the user to start & expire.
                    ##* To define multiple roles within the organization, you will add a '+' to separate the difference roles ie
                    ##'Admin:2022+Parent/Guardian'
                    ##!!!## this example is in capitalization (admin vs Admin ; Parent/Guardian vs parent_guardian)

                    ##### Hubs & Hub Roles
                    ##There are many roles that a User can be assigned in Memberhub, both roles for a User in an
                    ##Organization, in a Hub, and in a Family. The general format for a Role is +HubName:RoleName:Year.
                    ##* '+' is required when assigning more than one hub role to a user
                    ##* 'HubName' is the name of the Hub
                    ##* 'RoleName' is the name of the role
                    ##* 'Year' is optional and may be included to set the date that the role is to expire. If :Year is not provided,
                    ##there will be no expiration of the role. Expiry can be expressed as :yyyy (a 4 digit year which will be
                    ##interpreted as yyyy-06-30).
                    ##An example of adding to roles to a single hub, plus an additional role to a 2nd hub:
                    ##'Hub1:Admin:2022+Hub1:Parent/Guadian+Hub2:Parent/Guardian'
                    hubs = set()
                    for grade in fam_grades:
                        ahub_name = hub_name(f"grade-{grade}")
                        ahub_role = RoleName
                        ahub_year = str(END_YEAR)
                        ahub = ":".join([ahub_name, ahub_role, ahub_year])
                        hubs.add(ahub)
                    for teacher in fam_teachers:
                        if teacher:
                            ahub_name = hub_name(f"teacher-{teacher}")
                            ahub_role = RoleName
                            ahub_year = str(END_YEAR)
                            ahub = ":".join([ahub_name, ahub_role, ahub_year])
                            hubs.add(ahub)
                    hub_str = "+".join(hubs)
                    acontact["Hubs"] = hub_str
                    # acontact['Organization Role'] = hub_str

                    acontact["First Name"] = aparent["firstname"]
                    acontact["Last Name"] = aparent["lastname"]
                    acontact["Email"] = aparent["email"]
                    acontact["Phone Number"] = aparent["phone"]

                    acontact["Address"] = aparent["address1"]

                    if m := re.search(r"([\w\s+]+), (\w\w) (\d+)", aparent["address2"]):
                        city, state, zipcode = m.groups()
                        city = city.strip()
                    acontact["City"] = city
                    acontact["State"] = state
                    acontact["Zip"] = zipcode

                    acontact["Family Name"] = normalize(afam_name, fam_id)
                    acontact["Family Role"] = "Parent/Guardian"
                    # acontact["Family Role"] = "Contact"

                    if aparent.get("email") in extra_org_roles:
                        acontact["Organization Role"] = "Admin"
                    else:
                        acontact["Organization Role"] = "Contact"

                    # if not acontact['Email'])
                    #    print(f"*** WILL NOT LOAD contact with no Email {acontact}")

                    contacts.append(acontact)

                for astudent in afam["student"]:
                    hubs = set()
                    acontact = {}

                    RoleName = "Student"

                    grade = astudent["grade"]
                    ahub_name = hub_name(f"grade-{grade}")
                    ahub_role = RoleName
                    ahub_year = str(END_YEAR)
                    ahub = ":".join([ahub_name, ahub_role, ahub_year])
                    hubs.add(ahub)

                    teacher = astudent["teacher"]
                    if teacher:
                        ahub_name = hub_name(f"teacher-{teacher}")
                        ahub_role = RoleName
                        ahub_year = str(END_YEAR)
                        ahub = ":".join([ahub_name, ahub_role, ahub_year])
                        hubs.add(ahub)
                    else:
                        print(f"*** Warning no teacher for {astudent}")

                    hub_str = "+".join(hubs)
                    acontact["Hubs"] = hub_str
                    # acontact['Organization Role'] = hub_str

                    acontact["First Name"] = astudent["firstname"]
                    acontact["Last Name"] = astudent["lastname"]
                    # acontact['Email'] = astudent['email']
                    # acontact['Phone Number'] = astudent['phone']

                    acontact["Address"] = astudent["address1"]

                    if m := re.search(
                        r"([\w\s+]+), (\w\w) (\d+)", astudent["address2"]
                    ):
                        city, state, zipcode = m.groups()
                        city = city.strip()
                    acontact["City"] = city
                    acontact["State"] = state
                    acontact["Zip"] = zipcode
                    # acontact["Family Name"] = str(fam_id)
                    acontact["Family Name"] = normalize(afam_name, fam_id)

                    acontact["Organization Role"] = "Student"
                    acontact["Family Role"] = "Child"

                    contacts.append(acontact)

        if True:
            contact_keys = [
                "First Name",
                "Last Name",
                "Email",
                "Phone Number",
                "Organization Role",
                "Address",
                "City",
                "State",
                "Zip",
                "Family Name",
                "Family Role",
                "Hubs",
                "Contact Property 1",
                "Contact Property 2",
                # "Family Name",
                # "Family Role",
                # "Address",
                # "First Name",
                # "Last Name",
                # "City",
                # "State",
                # "Zip",
                # "Email",
                #
                #'Phone Number','Organization Role','Hubs',
            ]
            for contact in contacts:
                for k in contact:
                    if k not in contact_keys:
                        contact_keys.append(k)

            seen_emails = set()
            for contact in contacts:
                if contact.get("Organization Role") not in [
                    "Contact",
                    "Admin",
                    "Store Admin",
                    "Student",
                ]:
                    print(f"bad Organization Roles for {contact}")

                if contact.get("Organization Role") not in ["Student"]:
                    if contact.get("Email") in seen_emails:
                        print(f"bad duplicate email {contact.get('Email')}")
                    else:
                        seen_emails.add(contact.get("Email"))

            with open("ready_to_load.csv", "w") as outfh:
                outfh.write(",".join(contact_keys))
                outfh.write("\n")
                for contact in contacts:
                    out = []
                    for key in contact_keys:
                        val = ""
                        if key in contact:
                            val = contact[key]
                            if val:
                                if "," in val:
                                    print("*** Warning comma in planned output {val}")
                                    breakpoint()
                                if '"' in val:
                                    print(
                                        "*** Warning double-quote in planned output {val}"
                                    )
                                    breakpoint()
                            if val is None:
                                val = ""
                        out.append(val)
                    outfh.write(",".join(out))
                    outfh.write("\n")

            print("*** YOU MUST manually make these hubs ***")
            for ahub_name in sorted(list(all_hubs)):
                print(ahub_name)

            # ALL CONTACTS MUST HAVE AN EMAIL WITH THEIR PROFILE IN ORDER TO BE IMPORTED WITH
            # THE EXCEPTION OF ANY CONTACT WITH THE ROLE STUDENT OR CHILD.

            ### Organization Role

            ##Users can be assigned multiple roles for the Organization itself. The general structure for these roles are


##'RoleName:Year' where:
##* 'RoleName' is the name of the system defined Role ie 'admin', 'parent_guardian', 'contact'
##* 'Year' is an option parameter to define specific year for the user to start & expire.
##* To define multiple roles within the organization, you will add a '+' to separate the difference roles ie
##'Admin:2022+Parent/Guardian'
##!!!## this example is in capitalization (admin vs Admin ; Parent/Guardian vs parent_guardian)


##### Hubs & Hub Roles
##There are many roles that a User can be assigned in Memberhub, both roles for a User in an
##Organization, in a Hub, and in a Family. The general format for a Role is +HubName:RoleName:Year.
##* '+' is required when assigning more than one hub role to a user
##* 'HubName' is the name of the Hub
##* 'RoleName' is the name of the role
##* 'Year' is optional and may be included to set the date that the role is to expire. If :Year is not provided,
##there will be no expiration of the role. Expiry can be expressed as :yyyy (a 4 digit year which will be
##interpreted as yyyy-06-30).
##An example of adding to roles to a single hub, plus an additional role to a 2nd hub:
##'Hub1:Admin:2022+Hub1:Parent/Guadian+Hub2:Parent/Guardian'
##### Family Name
##The Family Name column is used to place users within a family. For best results, sort your spreadsheet
##by family name prior to running the import. Families must be grouped together when importing to place
##users within a single family or the ID structure must be used. To define a single family throughout a single
##upload, you can add a suffix of '#ID' where the 'ID' is a unique value referencing this one family, all rows
##with this identifier will be placed into the same family regardless of the family name.
##```
##First Name,Family Name
##Jane, Doe
##John, Doe
##Member, Hub
##Bob, Doe
##```
##The above will create 3 families. The first 'Doe' with Jane & John in the family. Next, 'Hub' with
##'Member' as the only user & finally 'Doe' will be a separate Family with Bob as the only user
##```
##First Name,Family Name
##Jane, Doe#1
##John, Doe#1
##Member, Hub
##Bob, Doe#1
##```
##The above will create 2 families since the #ID structure is used. The first 'Doe' with Jane, John & Bob in
##the family. And 'Hub' with 'Member' as the only user
##
##Hub Roles:
##Admin
##Contact
##Parent/Guardian
##Student
##Teacher
##Teacher Assistant
##Room Parent
##
##Custom Properties:
##Check box - indicate value with t or f.
##Multiselect - make sure to only include valid choices from defined property
##Multiselect - to include more than one value?
##When listing the hub use this format:
##Hub Name:Hub Role:Expiration year of Hub role+2 nd Hub Name:Hub role:Expiration Year.
##Example, adding a parent to 2 class hubs that will no longer be in hub at end of current year:
##Ms. Smith Hub:Parent/Guardian:2022+Ms. Jones Hub:Parent/Guardian:2022
##Hubs must match exactly what is on the site (same punctuation and capitalization or else they will not
##import correctly)
##
##
##
##
##
##
##
##
# for
##        1
##        breakpoint()
##        2
##


# if __name__ == "__main__":
#    main(*sys.argv[1:])

if __name__ == "__main__":
    cli()
