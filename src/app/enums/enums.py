from enum import Enum


class JobType(Enum):
    PUBLISH_PRODUCT = "publish_product"
    DELETE_PRODUCT = "delete_product"
    UPDATE_PRODUCT = "update_product"

