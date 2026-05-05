from pydantic import BaseModel, ConfigDict, RootModel
from pydantic.alias_generators import to_camel

__all__ = ["ImmutableDTO", "MutableDTO", "MODEL_CONFIG", "BaseDataclassMixin"]


MODEL_CONFIG = ConfigDict(
    str_strip_whitespace=True,
    use_enum_values=True,
    from_attributes=True,
    alias_generator=to_camel,
    allow_inf_nan=False,
    ser_json_timedelta="iso8601",
    ser_json_bytes="base64",
    validate_return=True,
    coerce_numbers_to_str=True,
    regex_engine="python-re",
    use_attribute_docstrings=True,
    extra="ignore",
    populate_by_name=True,
)

IMMUTABLE_MODEL_CONFIG = ConfigDict(**MODEL_CONFIG, frozen=True)


class DTOConfigMixin:
    model_config = MODEL_CONFIG


class ImmutableDTO(BaseModel):
    model_config = IMMUTABLE_MODEL_CONFIG


class MutableDTO(DTOConfigMixin, BaseModel):
    pass


class DataclassConfigMixin:
    model_config = MODEL_CONFIG


class DataclassSerializationMixin:
    def as_schema(self) -> BaseModel:
        return RootModel[self.__class__](self)


class BaseDataclassMixin(DataclassConfigMixin, DataclassSerializationMixin):
    pass
