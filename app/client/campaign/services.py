import io
import pandas as pd
from uuid import UUID
from fastapi import UploadFile
from app.client.models import (
    CampaignModel,
    CampaignContactsModel,
    UserModel
)
from app.core.exceptions.base import (
    AppException,
    NotFoundException
)


class CampaignContactImportService:
    """
    Service class to handle importing contacts into a campaign.
    Supports CSV, XLS, XLSX, and ODS files.
    Smartly detects column names for phone, name, and email.
    """

    # Common variations for matching columns
    PHONE_KEYWORDS = ["phone", "mobile", "cell", "contact", "contact number", "telephone", "number"]
    FIRST_NAME_KEYWORDS = ["first name", "fname", "given name", "name"]
    LAST_NAME_KEYWORDS = ["last name", "lname", "surname", "family name"]
    NAME_KEYWORDS = ["name", "full name", "contact name"]
    EMAIL_KEYWORDS = ["email", "e-mail", "mail address"]

    def __init__(self, user: UserModel, campaign_uid: UUID, file: UploadFile):
        self.user = user
        self.campaign_uid = campaign_uid
        self.file = file
        self.campaign = None
        self.df = None

    async def import_contacts(self) -> int:
        """Main entry point — orchestrates the import process."""
        await self._validate_campaign()
        self._read_file()
        return await self._process_contacts()

    # ---------------------- PRIVATE METHODS ----------------------

    async def _validate_campaign(self):
        """Ensure the campaign exists and belongs to the user."""
        campaign = await CampaignModel.find_one(
            CampaignModel.id == self.campaign_uid,
            CampaignModel.user.id == self.user.id
        )
        if not campaign:
            raise NotFoundException("Campaign not found")

        self.campaign = campaign

    def _read_file(self):
        filename = self.file.filename.lower()
        try:
            self.file.file.seek(0)  # ensure pointer reset
            content = self.file.file.read()
            buffer = io.BytesIO(content)

            if filename.endswith(".csv"):
                df = pd.read_csv(buffer)
            elif filename.endswith((".xls", ".xlsx")):
                df = pd.read_excel(buffer)
            elif filename.endswith(".ods"):
                df = pd.read_excel(buffer, engine="odf")
            else:
                raise AppException("Invalid file format. Only CSV, XLS, XLSX, or ODS are supported.")
        except Exception as e:
            raise AppException(f"Error reading file: {str(e)}")

        df.columns = [col.strip().lower() for col in df.columns]
        self.df = df

    async def _process_contacts(self) -> int:
        """Parse rows and save contacts to DB."""
        df = self.df

        # --- Detect columns ---
        phone_col = self._find_column(df.columns, self.PHONE_KEYWORDS)
        if not phone_col:
            raise AppException("No phone/contact number column found in file.")

        first_name_col = self._find_column(df.columns, self.FIRST_NAME_KEYWORDS)
        last_name_col = self._find_column(df.columns, self.LAST_NAME_KEYWORDS)
        full_name_col = self._find_column(df.columns, self.NAME_KEYWORDS)
        email_col = self._find_column(df.columns, self.EMAIL_KEYWORDS)

        contacts_to_insert = []
        for _, row in df.iterrows():
            phone_number = str(row.get(phone_col, "")).strip()
            if not phone_number:
                continue  # Skip rows without phone numbers

            # --- Name handling ---
            first_name, last_name = None, None
            if first_name_col or last_name_col:
                first_name = str(row.get(first_name_col, "")).strip() if first_name_col else None
                last_name = str(row.get(last_name_col, "")).strip() if last_name_col else None
            elif full_name_col:
                full_name = str(row.get(full_name_col, "")).strip()
                if " " in full_name:
                    first_name, last_name = full_name.split(" ", 1)
                else:
                    first_name = full_name
                    last_name = None

            email_value = str(row.get(email_col, "")).strip() if email_col else None

            contact_data = {
                "user": self.user,
                "campaign": self.campaign,
                "phone_number": phone_number,
                "first_name": first_name or None,
                "last_name": last_name or None,
                "email": email_value or None,
                "dynamic_variables": {},
            }

            # --- Add all other columns to dynamic_variables ---
            excluded = {phone_col, first_name_col, last_name_col, full_name_col, email_col}
            for col in df.columns:
                if col not in excluded and col:
                    key = col.replace(" ", "_").lower()
                    contact_data["dynamic_variables"][key] = row.get(col)

            contacts_to_insert.append(CampaignContactsModel(**contact_data))

        if contacts_to_insert:
            await CampaignContactsModel.insert_many(contacts_to_insert)

        return len(contacts_to_insert)

    # ---------------------- HELPERS ----------------------

    def _find_column(self, columns, keywords):
        """Find a matching column based on possible keywords."""
        for col in columns:
            for key in keywords:
                if key in col:
                    return col
        return None


