import re
import sys

END_YEAR = 2023


all_hubs = set()


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


seen_long_fams = {}
seen_short_fams = {}
seen_complex = {}


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
        "gillianedick@gmail.com": "Admin, Contact, Member, Customer, Officer",
        "sarahsandelius@gmail.com": "Admin, Officer",
        "cariaso@gmail.com": "Admin, Officer",
        "ckeeling83@gmail.com": "Officer",
        "jacquelyn_quan@yahoo.com": "Officer",
        "cherinacyborski@hotmail.com": "Officer",
        "cariaso@gmail.com": "Officer",
        "meghan.holohan@gmail.com": "Officer",
        "babytrekie@yahoo.com": "Officer",
        "victoria.levitas@gmail.com": "Officer",
        "tajpowell10@gmail.com": "Officer",
        "chris.press@gmail.com": "Officer",
        "wanujarie@gmail.com": "Officer",
        "katejulian@yahoo.com": "Officer",  # Kate Julian
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
            if not parent_info["email"]:
                errors = True
                print(f"*** no email*** for {parent_info}")

            row_info = {
                "student": [
                    student_info,
                ],
                "parent": [
                    parent_info,
                ],
            }
            if fam_id not in fam:
                fam[fam_id] = row_info
            else:
                if parent_info not in fam[fam_id]["parent"]:
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

                    # if not acontact['Email']:
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
                "Family Name",
                "Family Role",
                "Address",
                "First Name",
                "Last Name",
                "City",
                "State",
                "Zip",
                "Email",
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


if __name__ == "__main__":
    main(*sys.argv[1:])
