from enum import Enum


class UploadType(str, Enum):
    FINANCIAL_AE = "financial-ae"
    FINANCIAL_CP = "financial-cp"
