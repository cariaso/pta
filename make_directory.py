#!/usr/bin/env python

import click
import sys
import hashlib
import tempfile
import traceback


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


def pool_to_teacher_grade_student_uids(pool):
    out = {}
    tg = pool_to_teacher_grade(pool)
    for grade in tg:
        out[grade] = {}
        for teacher in tg[grade]:
            student_uids = []
            for entry in tg[grade][teacher]:
                astudent_uid = student_uid(entry)
                if astudent_uid not in student_uids:
                    student_uids.append(astudent_uid)
            out[grade][teacher] = student_uids
    return out


def student_uid(entry):
    student_name = entry.get("Student")
    dob = entry.get("Birth Date")
    # grade = entry.get("Grade")
    # teacher = entry.get("Homeroom Teacher")
    uid = hashlib.sha1((student_name + str(dob)).encode("utf-8")).hexdigest()
    return uid


def class_uid(grade=None, teacher=None, entry=None):
    if grade is None:
        grade = entry.get("Grade")
    if teacher is None:
        teacher = entry.get("Homeroom Teacher")
    uid = hashlib.sha1((f"{grade}_{teacher}").encode("utf-8")).hexdigest()
    return uid


def pool_to_student_relations(pool):

    out = {}
    for entry in pool:
        student_name = entry.get("Student")
        # dob = entry.get("Birth Date")
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

        relation_info = {
            "Relation": relation,
            "Name": relation_name,
            "Cell Phone": relation_cell,
            "Email": relation_email,
        }

        if address1 != withheld_marker:
            relation_info["Address1"] = address1
        if address2 != withheld_marker:
            relation_info["Address2"] = address2
        if phone != withheld_marker:
            relation_info["Phone"] = phone
        out[uid]["Relations"].append(relation_info)

    for uid in out:
        all_relations = out[uid]["Relations"]
        for k in ["Address1", "Address2", "Phone", "Email", "Cell Phone"]:
            all_vals = set([rel.get(k) for rel in all_relations])
            if all_vals == {None}:
                continue
            if len(all_vals) == 1:
                out[uid][k] = all_vals.pop()
                for rel in all_relations:
                    del rel[k]
        out[uid]["Relations"] = all_relations
        if out[uid].get("Cell Phone") and out[uid].get("Phone") == out[uid].get(
            "Cell Phone"
        ):
            del out[uid]["Cell Phone"]
    return out


def pool_to_pdf1(pool):

    # import datetime
    # import html
    # import collections

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

    from reportlab.platypus.tableofcontents import TableOfContents

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
    h2 = ParagraphStyle(name="Heading2", fontSize=12, leading=18)

    def linkedHeading(story, text, style):
        # create bookmarkname
        bn = hashlib.sha1((text + style.name).encode("utf-8")).hexdigest()
        # modify paragraph text to include an anchor point with name bn
        h = Paragraph(text + '<a name="%s"/>' % bn, style)
        # store the bookmark name on the flowable so afterFlowable can see this
        h._bookmarkName = bn
        story.append(h)

    tmppdf = tempfile.NamedTemporaryFile(suffix=".pdf")
    doc = MyDocTemplate(tmppdf.name)
    Story = []
    toc = TableOfContents()
    toc.levelStyles = [h1, h2]
    Story.append(toc)
    Story.append(PageBreak())

    ptext = "Somerset ES 2023-2024"
    linkedHeading(Story, ptext, h1)

    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(thickness=4))
    Story.append(Spacer(1, 12))
    Story.append(PageBreak())

    linkedHeading(Story, "FAQ", h1)

    # formatted_time = datetime.datetime.utcnow().strftime("%Y-%m-%d at %H:%M")
    # ptext = "<font size=12>This report was generated on %s UTC</font>" % formatted_time
    # Story.append(Paragraph(html.unescape(ptext), styles["Normal"]))
    # Story.append(Spacer(1, 12))

    # number of genotypes
    # story_meta_position = len(Story)

    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(thickness=4))
    Story.append(Spacer(1, 12))
    Story.append(PageBreak())

    styleSheet = getSampleStyleSheet()

    teacher_style = ParagraphStyle(
        name="teacher", fontSize=12, leading=14, leftIndent=10
    )
    # ext_link = ParagraphStyle(name="extLink", fontSize=10, leading=12, leftIndent=25)
    student_name_style = ParagraphStyle(
        name="studentName", fontSize=16, leading=12, leftIndent=0
    )

    phone_style = ParagraphStyle(name="phone", fontSize=12, leading=12, leftIndent=10)
    address_style = ParagraphStyle(
        name="address", fontSize=12, leading=12, leftIndent=20
    )
    teacher_style = ParagraphStyle(
        name="teacher", fontSize=12, leading=12, leftIndent=15
    )

    phone_style = styleSheet["BodyText"]
    address_style = styleSheet["BodyText"]
    teacher_style = styleSheet["BodyText"]

    psr = pool_to_student_relations(pool)
    num_students = 0

    linkedHeading(Story, "By Last Name", h1)
    by_firstname = {}
    for student_uid in psr:
        student = psr[student_uid]
        num_students += 1
        student_name = student["Student"]

        lastname, firstname = student_name.split(", ")
        by_firstname.setdefault(firstname, []).append(student_uid)

        student_anchor = f"<a name='{student_uid}'/>{student_name}"
        Story.append(Paragraph(student_anchor, student_name_style))

        if phone := student.get("Phone"):
            Story.append(Paragraph(f"Phone: {phone}", phone_style))
        if student.get("Address1") or student.get("Address2"):
            address = f"{student.get('Address1','')}<br/>{student.get('Address2','')}"
            Story.append(Paragraph(address, address_style))

        grade = student.get("Grade")
        teacher = student.get("Homeroom Teacher")
        aclass_uid = class_uid(grade=grade, teacher=teacher)
        class_anchor = f"<link href='#{aclass_uid}'>{grade} {teacher}</link>"
        Story.append(Paragraph(class_anchor, teacher_style))

        data = []

        data_keys = []
        for relation in student["Relations"]:
            for key, value in relation.items():
                if value != withheld_marker:
                    if key not in data_keys:
                        data_keys.append(key)

        for relation in student["Relations"]:
            data_row = []
            any_values = [x for x in relation.values() if x != withheld_marker]
            if any_values:
                for key in data_keys:
                    value = relation.get(key)
                    if value and value != withheld_marker:
                        data_row.append(
                            Paragraph(value, styleSheet["BodyText"]),
                        )
                    else:
                        data_row.append(None)
            if data_row:
                data.append(data_row)
        if data:
            t = Table(
                data,
                # colWidths=[2.4 * inch, 2.5 * inch, 2.5 * inch],
                style=[
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ],
            )

            Story.append(t)
        # Story.append(Spacer(1, 12))

    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(thickness=4))
    Story.append(Spacer(1, 12))
    Story.append(PageBreak())

    ptext = "By Grade & Teacher"
    linkedHeading(Story, ptext, h1)
    Story.append(Spacer(1, 12))

    tgs = pool_to_teacher_grade_student_uids(pool)
    for grade in tgs:
        for teacher in tgs[grade]:
            aclass_uid = class_uid(grade=grade, teacher=teacher)
            class_text = f"<a name='{aclass_uid}'/>{grade} {teacher}"
            Story.append(Paragraph(class_text, teacher_style))
            for student_uid in tgs[grade][teacher]:
                student = psr[student_uid]
                student_link = (
                    f"<link href='#{student_uid}'>{student.get('Student')}</link>"
                )
                p = Paragraph(student_link, styleSheet["BodyText"])
                Story.append(p)

    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(thickness=4))
    Story.append(Spacer(1, 12))
    Story.append(PageBreak())

    ptext = "By First Name"
    linkedHeading(Story, ptext, h1)
    Story.append(Spacer(1, 12))

    for firstname in sorted(by_firstname):
        for student_uid in by_firstname[firstname]:
            student = psr[student_uid]
            student_name = student.get("Student")
            alastname, afirstname = student_name.split(", ")

            student_link = (
                f"<link href='#{student_uid}'>{afirstname} {alastname}</link>"
            )
            p = Paragraph(student_link, styleSheet["BodyText"])
            Story.append(p)

    Story.append(Spacer(1, 12))
    Story.append(HRFlowable(thickness=4))
    Story.append(Spacer(1, 12))
    Story.append(PageBreak())

    # Story[story_meta_position] = Paragraph(
    #    f"Number of students: {num_students}", styles["Normal"]
    # )

    success = False
    try:
        doc.multiBuild(Story)
        success = True
    except reportlab.platypus.doctemplate.LayoutError as e:
        print(e)
        breakpoint()
        # pdb.set_trace()
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
        print("failed to make the pdf")

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


if __name__ == "__main__":
    cli()
