from pydantic import BaseModel
from bson import ObjectId


class MongoModel(BaseModel):
    """
    A base model for MongoDB documents that includes a smart `to_mongo` method.
    """

    def to_mongo(self, **kwargs) -> dict:
        """
        Convert the model to a dictionary suitable for MongoDB.

        This method dynamically finds any fields whose values are ObjectId instances
        and ensures they remain as such, overriding the default string serialization.
        """
        data = self.model_dump(by_alias=True, **kwargs)

        for field_name, field_info in self.__class__.model_fields.items():
            field_value = getattr(self, field_name)

            if isinstance(field_value, ObjectId):
                dict_key = field_info.alias or field_name
                data[dict_key] = field_value

        return data
