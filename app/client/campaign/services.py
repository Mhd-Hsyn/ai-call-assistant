import io
import pandas as pd
from fastapi import UploadFile
from uuid import UUID
from app.client.models import CampaignModel, CampaignContactsModel, UserModel
from app.core.exceptions.base import AppException, NotFoundException
from math import ceil


class CampaignContactImportService:
    PHONE_KEYWORDS = ["phone", "mobile", "cell", "contact", "contact number", "telephone", "number"]
    FIRST_NAME_KEYWORDS = ["first name", "fname", "given name"]
    LAST_NAME_KEYWORDS = ["last name", "lname", "surname"]
    NAME_KEYWORDS = ["name", "full name", "contact name"]
    EMAIL_KEYWORDS = ["email", "e-mail", "mail address"]

    MAX_FILE_SIZE_MB = 200
    CHUNK_SIZE = 5000  # rows per batch

    def __init__(self, user: UserModel, campaign_uid: UUID, file: UploadFile):
        self.user = user
        self.campaign_uid = campaign_uid
        self.file = file
        self.campaign = None

    async def import_contacts(self) -> int:
        await self._validate_campaign()
        total = await self._process_file()
        return total

    async def _validate_campaign(self):
        campaign = await CampaignModel.find_one(
            CampaignModel.id == self.campaign_uid,
            CampaignModel.user.id == self.user.id
        )
        if not campaign:
            raise NotFoundException("Campaign not found")
        self.campaign = campaign

    async def _process_file(self) -> int:
        filename = self.file.filename.lower()

        # --- Validate file size ---
        self.file.file.seek(0, io.SEEK_END)
        size_mb = self.file.file.tell() / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            raise AppException(f"File too large ({size_mb:.1f} MB). Limit {self.MAX_FILE_SIZE_MB} MB.")
        self.file.file.seek(0)

        buffer = io.BytesIO(self.file.file.read())

        if filename.endswith(".csv"):
            reader = pd.read_csv(buffer, chunksize=self.CHUNK_SIZE)
        elif filename.endswith((".xls", ".xlsx")):
            reader = pd.read_excel(buffer)
        elif filename.endswith(".ods"):
            reader = pd.read_excel(buffer, engine="odf")
        else:
            raise AppException("Invalid file format.")

        total_inserted = 0
        chunks = [reader] if not isinstance(reader, pd.io.parsers.TextFileReader) else reader

        for chunk in chunks:
            df = self._normalize_columns(chunk)
            inserted = await self._insert_chunk(df)
            total_inserted += inserted

        return total_inserted

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [col.strip().lower() for col in df.columns]
        return df

    async def _insert_chunk(self, df: pd.DataFrame) -> int:
        phone_col = self._find_column(df.columns, self.PHONE_KEYWORDS)
        if not phone_col:
            raise AppException("No phone column found")

        first_name_col = self._find_column(df.columns, self.FIRST_NAME_KEYWORDS)
        last_name_col = self._find_column(df.columns, self.LAST_NAME_KEYWORDS)
        full_name_col = self._find_column(df.columns, self.NAME_KEYWORDS)
        email_col = self._find_column(df.columns, self.EMAIL_KEYWORDS)

        contacts = []
        for _, row in df.iterrows():
            phone = str(row.get(phone_col, "")).strip()
            if not phone:
                continue

            first_name, last_name = self._extract_name(row, first_name_col, last_name_col, full_name_col)
            email = str(row.get(email_col, "")).strip() if email_col else None

            data = {
                "user": self.user,
                "campaign": self.campaign,
                "phone_number": phone,
                "first_name": first_name or None,
                "last_name": last_name or None,
                "email": email or None,
                "dynamic_variables": {
                    col.replace(" ", "_"): row.get(col)
                    for col in df.columns
                    if col not in {phone_col, first_name_col, last_name_col, full_name_col, email_col}
                },
            }
            contacts.append(CampaignContactsModel(**data))

        # Batch insert in DB (safe for large sets)
        if contacts:
            for i in range(0, len(contacts), 1000):
                batch = contacts[i:i + 1000]
                await CampaignContactsModel.insert_many(batch)

        return len(contacts)

    def _find_column(self, columns, keywords):
        for col in columns:
            for key in keywords:
                if key in col:
                    return col
        return None

    def _extract_name(self, row, first_name_col, last_name_col, full_name_col):
        if first_name_col or last_name_col:
            first_name = str(row.get(first_name_col, "")).strip() if first_name_col else None
            last_name = str(row.get(last_name_col, "")).strip() if last_name_col else None
            return first_name, last_name
        if full_name_col:
            full = str(row.get(full_name_col, "")).strip()
            parts = full.split(" ", 1)
            return parts[0], parts[1] if len(parts) > 1 else None
        return None, None
