"""General Health Screening questionnaire shaped from the Parkway field reference."""

from __future__ import annotations

from app.domain.models import QuestionnaireInputField, QuestionnairePrefillField

FAMILY_RELATIVES = [
    "Father",
    "Mother",
    "Siblings",
    "Paternal Relatives",
    "Maternal Relatives",
]

FAMILY_CONDITIONS = [
    "Heart Disease",
    "Stroke",
    "Diabetes",
    "High Blood Pressure",
    "High Cholesterol / Lipid Disorders",
    "Breast Cancer",
    "Cervical Cancer",
    "Colon Cancer (Age 60 and before)",
    "Colon Cancer (After Age 60)",
    "Lung Cancer",
    "Ovarian Cancer",
    "Pancreatic Cancer",
    "Prostate Cancer",
    "Other Cancers",
    "Other Diseases",
]

SHARED_CONDITIONS = [
    "Asthma",
    "Breast Lumps",
    "Chronic Kidney Disease",
    "Chronic Obstructive Pulmonary Disease (COPD)",
    "Depression / Anxiety",
    "Diabetes Type 1",
    "Diabetes Type 2",
    "Gallstones",
    "Glaucoma",
    "Gout",
    "Heart Attack",
    "Ischaemic Heart Disease",
    "Hepatitis B Carrier",
    "High Blood Pressure",
    "Hyperthyroidism",
    "Hypothyroidism",
    "Kidney Stones",
    "High Cholesterol / Lipid Disorders",
    "Non-Alcoholic Fatty Liver Disease",
    "Peripheral Vascular Disease",
    "Rheumatoid Arthritis",
    "Stroke",
    "Thalassemia Minor",
    "Prior Surgery / Endoscopy",
]

PROVIDER_LOCATIONS = {
    "Parkway Shenton Medical Clinic": [
        "Harbourfront Tower One",
        "Alexandra Retail Centre",
        "Bedok Central",
        "Bukit Batok Central",
        "Bukit Panjang Plaza",
        "Guoco Tower",
        "Jurong Gateway",
        "Metropolis",
        "Republic Plaza",
        "Serangoon North",
        "Tembeling Centre",
    ],
    "Parkway MediCentre": ["Parkway MediCentre (Woodleigh)"],
    "Executive Health Screeners": ["Paragon", "Gleneagles Hospital", "Mount Elizabeth Novena Hospital", "Mount Elizabeth Orchard"],
    "Mobile Health Screeners": ["On-site", "Home"],
    "Home Care": ["Home"],
}


def singpass_dummy_fields() -> list[dict[str, str]]:
    return [
        {"field_id": "full_name", "label": "Full name", "value": "Loh Wei Ming"},
        {"field_id": "id_type", "label": "ID type", "value": "NRIC/FIN"},
        {"field_id": "id_masked", "label": "NRIC/FIN", "value": "S••••946C"},
        {"field_id": "date_of_birth", "label": "Date of birth", "value": "26/07/1952"},
        {"field_id": "sex", "label": "Gender", "value": "Male"},
        {"field_id": "nationality", "label": "Nationality", "value": "Singaporean"},
        {"field_id": "address", "label": "Address", "value": "Blk 960 Yishun Ring Road #16-290"},
        {"field_id": "postal_code", "label": "Postal code", "value": "760960"},
        {"field_id": "contact_mobile", "label": "Mobile", "value": "+65 •••• 0206"},
        {"field_id": "email", "label": "Email", "value": "wei.loh43@hotmail.com"},
    ]


def singpass_field_templates(*, editable: bool = True) -> list[dict[str, object]]:
    """Same Singpass labels as the synthetic adapter, without autofilled values."""
    return [
        {
            "field_id": item["field_id"],
            "label": item["label"],
            "value": "",
            "source": "Patient-provided (Singpass adapter offline)",
            "editable": editable,
        }
        for item in singpass_dummy_fields()
    ]


def build_general_health_prefill(
    profile: list[dict[str, object]] | None = None,
) -> list[QuestionnairePrefillField]:
    if profile is not None:
        source_items = profile
        default_source = "Singpass / Myinfo"
    else:
        source_items = [dict(item) for item in singpass_dummy_fields()]
        default_source = "Singpass / Myinfo (synthetic)"
    prefill_ids = {
        "full_name",
        "date_of_birth",
        "contact_mobile",
        "email",
        "address",
        "postal_code",
        "id_type",
        "id_masked",
        "sex",
    }
    return [
        QuestionnairePrefillField(
            field_id=str(item.get("field_id") or ""),
            label=str(item.get("label") or ""),
            value=str(item.get("value") or ""),
            source=str(item.get("source") or default_source),
            editable=False,
        )
        for item in source_items
        if str(item.get("field_id") or "") in prefill_ids and str(item.get("value") or "").strip()
    ]


def singpass_sex_value(profile: list[dict[str, object]] | None = None) -> str | None:
    items = profile if profile is not None else [dict(item) for item in singpass_dummy_fields()]
    for item in items:
        if str(item.get("field_id") or "") == "sex":
            return normalize_gender(str(item.get("value") or ""))
    return None


def normalize_gender(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    lowered = raw.lower()
    if lowered in {"m", "male"}:
        return "Male"
    if lowered in {"f", "female"}:
        return "Female"
    if raw in {"Male", "Female"}:
        return raw
    return raw


def _field(
    field_id: str,
    label: str,
    field_type: str,
    *,
    required: bool = False,
    options: list[str] | None = None,
    value: str | None = None,
    help_text: str | None = None,
    section: str,
    show_if_field: str | None = None,
    show_if_value: str | None = None,
    show_if_mode: str = "equals",
    show_if_field_2: str | None = None,
    show_if_value_2: str | None = None,
    show_if_mode_2: str = "equals",
) -> QuestionnaireInputField:
    return QuestionnaireInputField(
        field_id=field_id,
        label=label,
        field_type=field_type,
        required=required,
        options=options or [],
        value=value,
        help_text=help_text,
        section=section,
        show_if_field=show_if_field,
        show_if_value=show_if_value,
        show_if_mode=show_if_mode,
        show_if_field_2=show_if_field_2,
        show_if_value_2=show_if_value_2,
        show_if_mode_2=show_if_mode_2,
    )


def build_general_health_fields(answers: dict[str, str | None] | None = None) -> list[QuestionnaireInputField]:
    values = dict(answers or {})
    gender = normalize_gender(values.get("gender")) or ""
    if gender and values.get("gender") != gender:
        values["gender"] = gender

    provider = values.get("screening_provider") or "Parkway Shenton Medical Clinic"
    location_options = PROVIDER_LOCATIONS.get(provider, ["Harbourfront Tower One", "Paragon", "Home", "On-site"])

    fields: list[QuestionnaireInputField] = [
        _field(
            "screening_provider",
            "Health Screening Provider",
            "select",
            required=True,
            options=list(PROVIDER_LOCATIONS.keys()),
            value=values.get("screening_provider"),
            section="Your Details",
        ),
        _field(
            "screening_location",
            "Health Screening Location",
            "select",
            required=True,
            options=location_options,
            value=values.get("screening_location"),
            help_text="Options depend on the selected provider.",
            section="Your Details",
        ),
        _field(
            "ethnicity",
            "Ethnicity (Race)",
            "select",
            required=True,
            options=["Asian", "Chinese", "Malay", "Indian", "Caucasian", "Others"],
            value=values.get("ethnicity"),
            section="Your Details",
        ),
        _field(
            "gender",
            "Gender",
            "select",
            required=True,
            options=["Male", "Female"],
            value=values.get("gender"),
            help_text="Prefills from Singpass when available; change only if incorrect.",
            section="Your Details",
        ),
        _field(
            "pregnant",
            "Are you pregnant?",
            "select",
            required=True,
            options=["No", "Yes"],
            value=values.get("pregnant"),
            section="Your Details",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "weeks_pregnant",
            "No. of weeks pregnant",
            "text",
            required=True,
            value=values.get("weeks_pregnant"),
            section="Your Details",
            show_if_field="pregnant",
            show_if_value="Yes",
        ),
        _field(
            "medical_conditions",
            "Medical history — select any that apply",
            "multiselect",
            options=[
                *SHARED_CONDITIONS,
                "Decreased Libido",
                "Ejaculatory Complaints",
                "Prostate Disease",
                "Gestational Diabetes",
                "Polycystic Ovary Syndrome (PCOS)",
                "Eczema, Hives or Skin Allergies",
            ],
            value=values.get("medical_conditions"),
            help_text="Male/female options follow gender. Skin allergy is included in this digital form for all providers.",
            section="Your Medical History",
        ),
        _field(
            "prior_surgery_details",
            "Please provide details of the surgery / endoscopy",
            "textarea",
            required=True,
            value=values.get("prior_surgery_details"),
            section="Your Medical History",
            show_if_field="medical_conditions",
            show_if_value="Prior Surgery / Endoscopy",
            show_if_mode="contains",
        ),
        _field(
            "hysterectomy",
            "Hysterectomy (womb removal surgery)",
            "select",
            required=True,
            options=["No", "Yes"],
            value=values.get("hysterectomy"),
            section="Your Medical History",
            show_if_field="gender",
            show_if_value="Female",
            show_if_field_2="medical_conditions",
            show_if_value_2="Prior Surgery / Endoscopy",
            show_if_mode_2="contains",
        ),
        _field(
            "other_diseases",
            "Other diseases (please specify)",
            "textarea",
            value=values.get("other_diseases"),
            section="Your Medical History",
        ),
        _field(
            "present_complaints",
            "Present health complaints (if any)",
            "textarea",
            value=values.get("present_complaints"),
            section="Your Medical History",
        ),
        _field(
            "last_gastroscopy_date",
            "Date of last gastroscopy",
            "text",
            value=values.get("last_gastroscopy_date"),
            help_text="Format dd/mm/yyyy",
            section="Last Scan / Screen",
        ),
        _field(
            "gastroscopy_results",
            "Gastroscopy results",
            "select",
            options=["Normal", "Abnormal"],
            value=values.get("gastroscopy_results"),
            section="Last Scan / Screen",
            show_if_field="last_gastroscopy_date",
            show_if_mode="not_empty",
            show_if_value="*",
        ),
        _field(
            "last_colonoscopy_date",
            "Date of last colonoscopy",
            "text",
            value=values.get("last_colonoscopy_date"),
            help_text="Format dd/mm/yyyy",
            section="Last Scan / Screen",
        ),
        _field(
            "colonoscopy_results",
            "Colonoscopy results",
            "select",
            options=["Normal", "Abnormal"],
            value=values.get("colonoscopy_results"),
            section="Last Scan / Screen",
            show_if_field="last_colonoscopy_date",
            show_if_mode="not_empty",
            show_if_value="*",
        ),
        _field(
            "last_ct_angiogram_date",
            "Date of last CT coronary angiogram",
            "text",
            value=values.get("last_ct_angiogram_date"),
            help_text="Format dd/mm/yyyy",
            section="Last Scan / Screen",
        ),
        _field(
            "ct_angiogram_results",
            "CT coronary angiogram results",
            "select",
            options=["Normal", "Abnormal"],
            value=values.get("ct_angiogram_results"),
            section="Last Scan / Screen",
            show_if_field="last_ct_angiogram_date",
            show_if_mode="not_empty",
            show_if_value="*",
        ),
        _field(
            "last_mammogram_date",
            "Date of last mammogram",
            "text",
            value=values.get("last_mammogram_date"),
            help_text="Format dd/mm/yyyy",
            section="Last Scan / Screen",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "mammogram_results",
            "Mammogram results",
            "select",
            options=["Normal", "Abnormal"],
            value=values.get("mammogram_results"),
            section="Last Scan / Screen",
            show_if_field="last_mammogram_date",
            show_if_mode="not_empty",
            show_if_value="*",
        ),
        _field(
            "lmp_date",
            "First day of last menstrual period",
            "text",
            value=values.get("lmp_date"),
            help_text="Format dd/mm/yyyy",
            section="Gynaecological History",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "menstrual_cycle",
            "Menstrual cycle",
            "select",
            options=["Regular", "Irregular"],
            value=values.get("menstrual_cycle"),
            section="Gynaecological History",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "heavy_periods",
            "Heavy menstrual periods",
            "select",
            options=["No", "Yes"],
            value=values.get("heavy_periods"),
            section="Gynaecological History",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "painful_periods",
            "Painful menstrual periods",
            "select",
            options=["Absent", "Mild", "Moderate", "Severe"],
            value=values.get("painful_periods"),
            section="Gynaecological History",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "contraception",
            "Do you use any contraception?",
            "select",
            options=["No", "Birth Control Pill", "Intra-uterine Device (IUD)", "Female Sterilisation", "Others"],
            value=values.get("contraception"),
            section="Gynaecological History",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "contraception_details",
            "Contraception details",
            "textarea",
            value=values.get("contraception_details"),
            section="Gynaecological History",
            show_if_field="contraception",
            show_if_value="Others",
        ),
        _field(
            "last_pap_date",
            "Date of last Pap smear / HPV DNA",
            "text",
            value=values.get("last_pap_date"),
            help_text="Format dd/mm/yyyy",
            section="Gynaecological History",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "pap_results",
            "Pap smear results",
            "select",
            options=["Normal", "Abnormal"],
            value=values.get("pap_results"),
            section="Gynaecological History",
            show_if_field="last_pap_date",
            show_if_mode="not_empty",
            show_if_value="*",
        ),
        _field(
            "vaginal_deliveries",
            "No. of vaginal deliveries",
            "text",
            value=values.get("vaginal_deliveries"),
            section="Pregnancy Related",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "caesarean_sections",
            "No. of caesarean sections",
            "text",
            value=values.get("caesarean_sections"),
            section="Pregnancy Related",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "pregnancy_illnesses",
            "Pregnancy-related illnesses and difficulties",
            "textarea",
            value=values.get("pregnancy_illnesses"),
            section="Pregnancy Related",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "current_medications_matrix",
            "Current medications — select any that apply",
            "multiselect",
            options=[
                "Diabetes Medication",
                "Hypertension Medication",
                "Statins",
                "Other Cholesterol Medication",
                "Thyroid Medication",
            ],
            value=values.get("current_medications_matrix"),
            section="Current Medications",
        ),
        _field(
            "other_medications",
            "Other medications / supplements",
            "textarea",
            value=values.get("other_medications"),
            section="Current Medications",
        ),
        _field(
            "medication_names_dosages",
            "Medication name(s) and dosage(s)",
            "textarea",
            value=values.get("medication_names_dosages"),
            section="Current Medications",
        ),
        _field(
            "drug_allergies",
            "Do you have any drug allergies?",
            "select",
            required=True,
            options=["No", "Yes"],
            value=values.get("drug_allergies"),
            section="Current Medications",
        ),
        _field(
            "drug_allergy_details",
            "Please provide name(s) of the drug(s)",
            "textarea",
            required=True,
            value=values.get("drug_allergy_details"),
            section="Current Medications",
            show_if_field="drug_allergies",
            show_if_value="Yes",
        ),
        _field(
            "recent_vaccination",
            "Any recent vaccination(s) in the past 1 month?",
            "select",
            required=True,
            options=["No", "Yes"],
            value=values.get("recent_vaccination"),
            section="Immunization History",
        ),
        _field(
            "vaccination_details",
            "Vaccination details",
            "textarea",
            required=True,
            value=values.get("vaccination_details"),
            section="Immunization History",
            show_if_field="recent_vaccination",
            show_if_value="Yes",
        ),
        _field(
            "flu_vaccination",
            "Had flu vaccination this year?",
            "select",
            required=True,
            options=["No", "Yes"],
            value=values.get("flu_vaccination"),
            section="Immunization History",
        ),
        _field(
            "covid_vaccination_male",
            "Latest COVID vaccination (>2 weeks ago)",
            "text",
            value=values.get("covid_vaccination_male"),
            help_text="Date or brief note",
            section="Immunization History",
            show_if_field="gender",
            show_if_value="Male",
        ),
        _field(
            "covid_vaccination_female",
            "Latest COVID vaccination (>6 weeks ago)",
            "text",
            value=values.get("covid_vaccination_female"),
            help_text="Date or brief note",
            section="Immunization History",
            show_if_field="gender",
            show_if_value="Female",
        ),
        _field(
            "hpv_vaccination",
            "Had HPV / cervical vaccination?",
            "select",
            options=["No", "Yes"],
            value=values.get("hpv_vaccination"),
            section="Immunization History",
            show_if_field="gender",
            show_if_value="Female",
        ),
    ]

    for condition in FAMILY_CONDITIONS:
        slug = (
            condition.lower()
            .replace(" / ", "_")
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("-", "_")
        )
        fields.append(
            _field(
                f"family_{slug}",
                f"Family history — {condition}",
                "multiselect",
                options=FAMILY_RELATIVES,
                value=values.get(f"family_{slug}"),
                help_text="Select relatives who have this history, if any.",
                section="Your Family History",
            )
        )
        if condition in {"Other Cancers", "Other Diseases"}:
            fields.append(
                _field(
                    f"family_{slug}_details",
                    f"Details — {condition}",
                    "textarea",
                    value=values.get(f"family_{slug}_details"),
                    section="Your Family History",
                    show_if_field=f"family_{slug}",
                    show_if_mode="not_empty",
                    show_if_value="*",
                )
            )

    fields.extend(
        [
            _field(
                "exercise_frequency",
                "How often do you exercise weekly?",
                "select",
                required=True,
                options=[
                    "Do not exercise regularly",
                    "Less than 100 mins/week",
                    "Between 100 to 150 mins/week",
                    "More than 150 mins/week",
                ],
                value=values.get("exercise_frequency"),
                section="Your Lifestyle",
            ),
            _field(
                "smoking_status",
                "Do you currently smoke?",
                "select",
                required=True,
                options=[
                    "No",
                    "Yes, less than 10 cigarettes/day",
                    "Yes, 10–20 cigarettes/day",
                    "Yes, more than 20 cigarettes/day",
                    "Former smoker",
                ],
                value=values.get("smoking_status"),
                section="Your Lifestyle",
            ),
            _field(
                "years_quit_smoking",
                "How many years ago did you quit?",
                "text",
                required=True,
                value=values.get("years_quit_smoking"),
                section="Your Lifestyle",
                show_if_field="smoking_status",
                show_if_value="Former smoker",
            ),
            _field(
                "years_smoking",
                "How many years have you been smoking?",
                "text",
                required=True,
                value=values.get("years_smoking"),
                section="Your Lifestyle",
                show_if_field="smoking_status",
                show_if_mode="any_of",
                show_if_value="Yes, less than 10 cigarettes/day|Yes, 10–20 cigarettes/day|Yes, more than 20 cigarettes/day",
            ),
            _field(
                "drinks_alcohol",
                "Do you drink alcohol?",
                "select",
                required=True,
                options=["No", "Yes"],
                value=values.get("drinks_alcohol"),
                section="Your Lifestyle",
            ),
            _field(
                "alcohol_intake",
                "Alcohol intake level",
                "select",
                required=True,
                options=[
                    "Occasional",
                    "Yes, less than 7 units/week",
                    "Yes, 7–14 units/week",
                    "Yes, more than 14 units/week",
                ],
                value=values.get("alcohol_intake"),
                section="Your Lifestyle",
                show_if_field="drinks_alcohol",
                show_if_value="Yes",
            ),
            _field(
                "stress_frequency",
                "Over the past few weeks, how often have you felt overwhelmed, anxious or unable to cope?",
                "select",
                required=True,
                options=["Never", "Rarely", "Sometimes", "Often", "Always"],
                value=values.get("stress_frequency"),
                section="Your Lifestyle",
            ),
            _field(
                "special_diet",
                "Special diet",
                "select",
                options=["None", "Yes — please elaborate"],
                value=values.get("special_diet"),
                section="Your Lifestyle",
            ),
            _field(
                "special_diet_details",
                "Please elaborate on the special diet",
                "textarea",
                required=True,
                value=values.get("special_diet_details"),
                section="Your Lifestyle",
                show_if_field="special_diet",
                show_if_value="Yes — please elaborate",
            ),
            _field(
                "chronic_pain",
                "Are you experiencing pain regularly in certain areas?",
                "select",
                required=True,
                options=["No", "Yes"],
                value=values.get("chronic_pain"),
                section="Pain Assessment",
            ),
            _field(
                "pain_area",
                "If so, which area(s)?",
                "textarea",
                required=True,
                value=values.get("pain_area"),
                section="Pain Assessment",
                show_if_field="chronic_pain",
                show_if_value="Yes",
            ),
            _field(
                "pain_level",
                "Pain level (1–10)",
                "select",
                required=True,
                options=[str(level) for level in range(1, 11)],
                value=values.get("pain_level"),
                section="Pain Assessment",
                show_if_field="chronic_pain",
                show_if_value="Yes",
            ),
            _field(
                "share_sexual_history",
                "Are you comfortable to share your sexual history for the past 12 months?",
                "select",
                required=True,
                options=["No", "Yes"],
                value=values.get("share_sexual_history"),
                section="Sexual History",
            ),
            _field(
                "sexually_active",
                "Have you been sexually active for the past 12 months?",
                "select",
                required=True,
                options=["No", "Yes"],
                value=values.get("sexually_active"),
                section="Sexual History",
                show_if_field="share_sexual_history",
                show_if_value="Yes",
            ),
            _field(
                "sexual_partners",
                "How many sexual partners have you had in the past 12 months?",
                "text",
                required=True,
                value=values.get("sexual_partners"),
                section="Sexual History",
                show_if_field="sexually_active",
                show_if_value="Yes",
            ),
        ]
    )

    # Gender-/provider-specific medical options from the Parkway field reference.
    # Eczema is listed for all providers so first-time patients still see the full medical-history set;
    # MediCentre remains the clinical home for that checkbox on the paper form.
    visible_conditions = list(SHARED_CONDITIONS)
    if gender == "Male":
        visible_conditions.extend(["Decreased Libido", "Ejaculatory Complaints", "Prostate Disease"])
    elif gender == "Female":
        visible_conditions.extend(["Gestational Diabetes", "Polycystic Ovary Syndrome (PCOS)"])
    else:
        # Until gender is chosen, surface both sex-specific options so nothing looks "missing".
        visible_conditions.extend(
            [
                "Decreased Libido",
                "Ejaculatory Complaints",
                "Prostate Disease",
                "Gestational Diabetes",
                "Polycystic Ovary Syndrome (PCOS)",
            ]
        )
    visible_conditions.append("Eczema, Hives or Skin Allergies")

    for index, field in enumerate(fields):
        if field.field_id == "medical_conditions":
            fields[index] = field.model_copy(update={"options": visible_conditions})

    return fields


def _condition_matches(raw: str, expected: str, mode: str) -> bool:
    if mode == "not_empty":
        return bool(raw.strip())
    if mode == "contains":
        return expected in {part.strip() for part in raw.split("|") if part.strip()}
    if mode == "any_of":
        allowed = {part.strip() for part in expected.split("|") if part.strip()}
        return raw in allowed
    return raw == expected


def field_is_visible(field: QuestionnaireInputField, answers: dict[str, str | None]) -> bool:
    if field.show_if_field:
        raw = (answers.get(field.show_if_field) or "").strip()
        if not _condition_matches(raw, field.show_if_value or "", field.show_if_mode):
            return False
    if field.show_if_field_2:
        raw = (answers.get(field.show_if_field_2) or "").strip()
        if not _condition_matches(raw, field.show_if_value_2 or "", field.show_if_mode_2):
            return False
    return True


def missing_required_fields(fields: list[QuestionnaireInputField], answers: dict[str, str | None]) -> list[str]:
    missing: list[str] = []
    for field in fields:
        if not field_is_visible(field, answers):
            continue
        if not field.required:
            continue
        value = (answers.get(field.field_id) or "").strip()
        if not value:
            missing.append(field.field_id)
    return missing
