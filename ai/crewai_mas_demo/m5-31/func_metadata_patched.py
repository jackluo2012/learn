"""
FastMCP 函数元数据处理模块（修补版）

═══════════════════════════════════════════════════════════════════════════════
用途说明
═══════════════════════════════════════════════════════════════════════════════

本模块用于将 Python 函数转换为 MCP (Model Context Protocol) 工具，主要功能：

1. **参数验证与序列化**
   - 自动将函数签名转换为 Pydantic 模型
   - 验证输入参数类型
   - 处理默认值和可选参数

2. **结构化输出支持**
   - 根据返回类型注解生成 JSON Schema
   - 支持多种返回类型：BaseModel、TypedDict、dataclass、基本类型等
   - 自动序列化复杂对象为 JSON

3. **智能参数预解析**
   - 处理 Claude Desktop 传递的 JSON 字符串参数
   - 自动将字符串形式的 JSON 解析为实际类型
   - 处理空字符串与 None 的转换

4. **特殊字段名处理**
   - 自动为与 BaseModel 属性冲突的参数名创建别名
   - 避免参数名与 Pydantic 保留字冲突

═══════════════════════════════════════════════════════════════════════════════
使用方法
═══════════════════════════════════════════════════════════════════════════════

基础用法（无结构化输出）:
```python
def my_tool(name: str, age: int = 18) -> str:
    return f"Hello {name}, you are {age} years old"

# 创建函数元数据
meta = func_metadata(my_tool)

# 验证参数
validated_args = meta.arg_model.model_validate({"name": "Alice", "age": 25})

# 调用函数
result = my_tool(**validated_args.model_dump_one_level())
```

结构化输出用法:
```python
from pydantic import BaseModel

class UserResult(BaseModel):
    user_id: int
    username: str
    is_active: bool

def get_user(user_id: int) -> UserResult:
    # 返回结构化数据
    return UserResult(user_id=user_id, username="alice", is_active=True)

# 创建函数元数据（自动检测返回类型）
meta = func_metadata(get_user)

# 验证并调用
result = get_user(123)
validated_output = meta.output_model.model_validate(result)
json_data = validated_output.model_dump(mode="json")
```

═══════════════════════════════════════════════════════════════════════════════
修补说明
═══════════════════════════════════════════════════════════════════════════════

本文件是从 FastMCP 项目中提取的修补版本，主要修改：
- 移除了对 FastMCP 内部模块的强依赖
- 保留核心的函数元数据处理逻辑
- 可独立用于 MCP 工具的元数据生成

原始项目: https://github.com/jlowin/fastmcp
"""

import inspect
import json
import types
from collections.abc import Awaitable, Callable, Sequence
from itertools import chain
from types import GenericAlias
from typing import Annotated, Any, ForwardRef, Union, cast, get_args, get_origin, get_type_hints

import pydantic_core
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    WithJsonSchema,
    create_model,
)
from pydantic._internal._typing_extra import eval_type_backport
from pydantic.fields import FieldInfo
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaWarningKind
from pydantic_core import PydanticUndefined

from mcp.server.fastmcp.exceptions import InvalidSignature
from mcp.server.fastmcp.utilities.logging import get_logger
from mcp.server.fastmcp.utilities.types import Audio, Image
from mcp.types import CallToolResult, ContentBlock, TextContent

logger = get_logger(__name__)

class StrictJsonSchema(GenerateJsonSchema):
    """严格的 JSON Schema 生成器

    与标准生成器不同，当遇到不可序列化的类型时，会抛出异常而不是发出警告。

    用途:
        在生成工具的 JSON Schema 时，提前发现类型定义问题，而不是在运行时失败。

    示例:
        >>> schema = MyModel.model_json_schema(schema_generator=StrictJsonSchema)
        # 如果类型不可序列化，会抛出 ValueError
    """

    def emit_warning(self, kind: JsonSchemaWarningKind, detail: str) -> None:
        # Raise an exception instead of emitting a warning
        raise ValueError(f"JSON schema warning: {kind} - {detail}")

class ArgModelBase(BaseModel):
    """函数参数模型的基类

    所有由 func_metadata() 生成的参数模型都继承自此类。

    特殊方法:
        model_dump_one_level(): 将模型转换为字典，但不深入转换子模型

    配置:
        arbitrary_types_allowed=True: 允许任意 Python 类型作为字段

    示例:
        >>> meta = func_metadata(my_function)
        >>> args = meta.arg_model.model_validate({"name": "Alice", "age": 25})
        >>> kwargs = args.model_dump_one_level()
        >>> result = my_function(**kwargs)
    """

    def model_dump_one_level(self) -> dict[str, Any]:
        """Return a dict of the model's fields, one level deep.

        That is, sub-models etc are not dumped - they are kept as pydantic models.
        """
        kwargs: dict[str, Any] = {}
        for field_name, field_info in self.__class__.model_fields.items():
            value = getattr(self, field_name)
            # Use the alias if it exists, otherwise use the field name
            output_name = field_info.alias if field_info.alias else field_name
            kwargs[output_name] = value
        return kwargs

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class FuncMetadata(BaseModel):
    """函数元数据的容器类

    存储函数的所有元数据信息，包括参数模型、输出模型和转换配置。

    属性:
        arg_model: Pydantic 模型类，用于验证函数的输入参数
        output_schema: 输出的 JSON Schema（如果支持结构化输出）
        output_model: Pydantic 模型类，用于验证函数的返回值（结构化输出）
        wrap_output: 是否需要将返回值包装在 {"result": ...} 中

    主要方法:
        call_fn_with_arg_validation(): 验证参数并调用函数
        convert_result(): 将函数返回值转换为适当的格式
        pre_parse_json(): 预处理 JSON 字符串参数

    使用示例:
        >>> # 创建元数据
        >>> meta = func_metadata(my_tool)
        >>>
        >>> # 验证并调用
        >>> validated_args = meta.arg_model.model_validate({"name": "Alice"})
        >>> result = await meta.call_fn_with_arg_validation(
        ...     fn=my_tool,
        ...     fn_is_async=True,
        ...     arguments_to_validate={"name": "Alice"},
        ...     arguments_to_pass_directly=None
        ... )
        >>>
        >>> # 转换结果
        >>> output = meta.convert_result(result)
    """

    arg_model: Annotated[type[ArgModelBase], WithJsonSchema(None)]
    output_schema: dict[str, Any] | None = None
    output_model: Annotated[type[BaseModel], WithJsonSchema(None)] | None = None
    wrap_output: bool = False

    async def call_fn_with_arg_validation(
        self,
        fn: Callable[..., Any | Awaitable[Any]],
        fn_is_async: bool,
        arguments_to_validate: dict[str, Any],
        arguments_to_pass_directly: dict[str, Any] | None,
    ) -> Any:
        """Call the given function with arguments validated and injected.

        Arguments are first attempted to be parsed from JSON, then validated against
        the argument model, before being passed to the function.
        """
        arguments_pre_parsed = self.pre_parse_json(arguments_to_validate)
        arguments_parsed_model = self.arg_model.model_validate(arguments_pre_parsed)
        arguments_parsed_dict = arguments_parsed_model.model_dump_one_level()

        arguments_parsed_dict |= arguments_to_pass_directly or {}

        if fn_is_async:
            return await fn(**arguments_parsed_dict)
        else:
            return fn(**arguments_parsed_dict)

    def convert_result(self, result: Any) -> Any:
        """
        Convert the result of a function call to the appropriate format for
         the lowlevel server tool call handler:

        - If output_model is None, return the unstructured content directly.
        - If output_model is not None, convert the result to structured output format
            (dict[str, Any]) and return both unstructured and structured content.

        Note: we return unstructured content here **even though the lowlevel server
        tool call handler provides generic backwards compatibility serialization of
        structured content**. This is for FastMCP backwards compatibility: we need to
        retain FastMCP's ad hoc conversion logic for constructing unstructured output
        from function return values, whereas the lowlevel server simply serializes
        the structured output.
        """
        if isinstance(result, CallToolResult):
            if self.output_schema is not None:
                assert self.output_model is not None, "Output model must be set if output schema is defined"
                self.output_model.model_validate(result.structuredContent)
            return result

        unstructured_content = _convert_to_content(result)

        if self.output_schema is None:
            return unstructured_content
        else:
            if self.wrap_output:
                result = {"result": result}

            assert self.output_model is not None, "Output model must be set if output schema is defined"
            validated = self.output_model.model_validate(result)
            structured_content = validated.model_dump(mode="json", by_alias=True)

            return (unstructured_content, structured_content)

    def pre_parse_json(self, data: dict[str, Any]) -> dict[str, Any]:
        """预处理 JSON 字符串参数

        将字符串形式的 JSON 解析为实际的 Python 对象。

        背景:
            Claude Desktop 在调用 MCP 工具时，经常会将复杂参数（列表、字典等）
            序列化为 JSON 字符串传递。这个方法会自动将这些字符串解析回原始类型。

        处理逻辑:
            1. 遍历所有输入参数
            2. 对于非字符串类型的参数，如果接收到的是字符串：
               - 尝试用 json.loads() 解析
               - 如果解析成功且结果不是基本类型，则使用解析后的值
            3. 处理空字符串与 None 的转换（可选参数）

        示例:
            >>> # 假设函数签名为: def process(items: list[str], config: dict)
            >>> # Claude Desktop 传递: {"items": '["a", "b", "c"]', "config": '{"key": "value"}'}
            >>> parsed = meta.pre_parse_json({"items": '["a", "b", "c"]', "config": '{"key": "value"}'})
            >>> # 结果: {"items": ["a", "b", "c"], "config": {"key": "value"}}
        """
        new_data = data.copy()  # Shallow copy

        # Build a mapping from input keys (including aliases) to field info
        key_to_field_info: dict[str, FieldInfo] = {}
        for field_name, field_info in self.arg_model.model_fields.items():
            # Map both the field name and its alias (if any) to the field info
            key_to_field_info[field_name] = field_info
            if field_info.alias:
                key_to_field_info[field_info.alias] = field_info

        for data_key, data_value in data.items():
            if data_key not in key_to_field_info:
                continue

            field_info = key_to_field_info[data_key]
            if data_value == "" and field_info.annotation is not str:
                origin = get_origin(field_info.annotation)
                args = get_args(field_info.annotation)
                if origin is Union and type(None) in args:
                    new_data[data_key] = None
                    continue
            if isinstance(data_value, str) and field_info.annotation is not str:
                try:
                    pre_parsed = json.loads(data_value)
                except json.JSONDecodeError:
                    continue  # Not JSON - skip
                if isinstance(pre_parsed, str | int | float):
                    # This is likely that the raw value is e.g. `"hello"` which we
                    # Should really be parsed as '"hello"' in Python - but if we parse
                    # it as JSON it'll turn into just 'hello'. So we skip it.
                    continue
                new_data[data_key] = pre_parsed
        assert new_data.keys() == data.keys()
        return new_data

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


def func_metadata(
    func: Callable[..., Any],
    skip_names: Sequence[str] = (),
    structured_output: bool | None = None,
) -> FuncMetadata:
    """将 Python 函数转换为 MCP 工具元数据

    这是本模块的核心函数，用于生成函数的参数验证模型和输出序列化配置。

    ─────────────────────────────────────────────────────────────────────────────
    基础用法
    ─────────────────────────────────────────────────────────────────────────────

    ```python
    def greet(name: str, age: int = 18) -> str:
        return f"Hello {name}, age {age}"

    # 生成元数据
    meta = func_metadata(greet)

    # 验证输入参数
    validated = meta.arg_model.model_validate({"name": "Alice", "age": 25})

    # 调用函数
    result = greet(**validated.model_dump_one_level())
    ```

    ─────────────────────────────────────────────────────────────────────────────
    结构化输出
    ─────────────────────────────────────────────────────────────────────────────

    ```python
    from pydantic import BaseModel

    class UserInfo(BaseModel):
        user_id: int
        username: str
        email: str

    def get_user(user_id: int) -> UserInfo:
        return UserInfo(user_id=user_id, username="alice", email="alice@example.com")

    # 自动检测结构化输出
    meta = func_metadata(get_user)

    # 验证返回值
    result = get_user(123)
    validated_output = meta.output_model.model_validate(result)
    json_data = validated_output.model_dump(mode="json")
    ```

    ─────────────────────────────────────────────────────────────────────────────
    参数说明
    ─────────────────────────────────────────────────────────────────────────────

    Args:
        func: 要转换的 Python 函数
        skip_names: 要跳过的参数名列表（这些参数不会被包含在模型中）
        structured_output: 控制是否启用结构化输出
            - None: 自动检测（根据返回类型注解）
            - True: 强制启用结构化输出（返回类型必须可序列化）
            - False: 强制使用非结构化输出

    返回:
        FuncMetadata 对象，包含:
        - arg_model: 用于验证输入参数的 Pydantic 模型
        - output_model: 用于验证返回值的 Pydantic 模型（结构化输出时）
        - output_schema: 返回值的 JSON Schema
        - wrap_output: 是否需要包装返回值

    ─────────────────────────────────────────────────────────────────────────────
    支持的返回类型（结构化输出）
    ─────────────────────────────────────────────────────────────────────────────

    1. Pydantic BaseModel: 直接使用
    2. TypedDict: 转换为 Pydantic 模型
    3. dataclass: 转换为 Pydantic 模型
    4. 基本类型 (str, int, float, bool, None): 包装为 {"result": ...}
    5. 泛型类型 (list[T], dict[K, V], Union[T, U]): 包装为 {"result": ...}
    6. dict[str, T]: 使用 RootModel 直接映射

    ─────────────────────────────────────────────────────────────────────────────
    特殊功能
    ─────────────────────────────────────────────────────────────────────────────

    1. **参数预解析**: 自动处理 Claude Desktop 传递的 JSON 字符串参数
    2. **别名处理**: 自动为与 BaseModel 属性冲突的参数创建别名
    3. **可选参数**: 智能处理 None 类型和默认值
    4. **类型转换**: 支持字符串类型的注解（延迟求值）
    """
    sig = _get_typed_signature(func)
    params = sig.parameters
    dynamic_pydantic_model_params: dict[str, Any] = {}
    globalns = getattr(func, "__globals__", {})
    for param in params.values():
        if param.name.startswith("_"):
            raise InvalidSignature(f"Parameter {param.name} of {func.__name__} cannot start with '_'")
        if param.name in skip_names:
            continue
        annotation = param.annotation

        # `x: None` / `x: None = None`
        if annotation is None:
            annotation = Annotated[
                None,
                Field(default=param.default if param.default is not inspect.Parameter.empty else PydanticUndefined),
            ]

        # Untyped field
        if annotation is inspect.Parameter.empty:
            annotation = Annotated[
                Any,
                Field(),
                # 🤷
                WithJsonSchema({"title": param.name, "type": "string"}),
            ]

        field_info = FieldInfo.from_annotated_attribute(
            _get_typed_annotation(annotation, globalns),
            param.default if param.default is not inspect.Parameter.empty else PydanticUndefined,
        )

        # Check if the parameter name conflicts with BaseModel attributes
        # This is necessary because Pydantic warns about shadowing parent attributes
        if hasattr(BaseModel, param.name) and callable(getattr(BaseModel, param.name)):
            # Use an alias to avoid the shadowing warning
            field_info.alias = param.name
            field_info.validation_alias = param.name
            field_info.serialization_alias = param.name
            # Use a prefixed internal name
            internal_name = f"field_{param.name}"
            dynamic_pydantic_model_params[internal_name] = (field_info.annotation, field_info)
        else:
            dynamic_pydantic_model_params[param.name] = (field_info.annotation, field_info)
        continue

    arguments_model = create_model(
        f"{func.__name__}Arguments",
        **dynamic_pydantic_model_params,
        __base__=ArgModelBase,
    )

    if structured_output is False:
        return FuncMetadata(arg_model=arguments_model)

    # set up structured output support based on return type annotation

    if sig.return_annotation is inspect.Parameter.empty and structured_output is True:
        raise InvalidSignature(f"Function {func.__name__}: return annotation required for structured output")

    output_info = FieldInfo.from_annotation(_get_typed_annotation(sig.return_annotation, globalns))
    annotation = output_info.annotation

    # Reject CallToolResult in Union types (including Optional)
    # Handle both typing.Union (Union[X, Y]) and types.UnionType (X | Y)
    origin = get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        # Check if CallToolResult appears in the union (excluding None for Optional check)
        if any(isinstance(arg, type) and issubclass(arg, CallToolResult) for arg in args if arg is not type(None)):
            raise InvalidSignature(
                f"Function {func.__name__}: CallToolResult cannot be used in Union or Optional types. "
                "To return empty results, use: CallToolResult(content=[])"
            )

    # if the typehint is CallToolResult, the user either intends to return without validation
    # or they provided validation as Annotated metadata
    if isinstance(annotation, type) and issubclass(annotation, CallToolResult):
        if output_info.metadata:
            annotation = output_info.metadata[0]
        else:
            return FuncMetadata(arg_model=arguments_model)

    output_model, output_schema, wrap_output = _try_create_model_and_schema(annotation, func.__name__, output_info)

    if output_model is None and structured_output is True:
        # Model creation failed or produced warnings - no structured output
        raise InvalidSignature(
            f"Function {func.__name__}: return type {annotation} is not serializable for structured output"
        )

    return FuncMetadata(
        arg_model=arguments_model,
        output_schema=output_schema,
        output_model=output_model,
        wrap_output=wrap_output,
    )


def _try_create_model_and_schema(
    annotation: Any, func_name: str, field_info: FieldInfo
) -> tuple[type[BaseModel] | None, dict[str, Any] | None, bool]:
    """Try to create a model and schema for the given annotation without warnings.

    Returns:
        tuple of (model or None, schema or None, wrap_output)
        Model and schema are None if warnings occur or creation fails.
        wrap_output is True if the result needs to be wrapped in {"result": ...}
    """
    model = None
    wrap_output = False

    # First handle special case: None
    if annotation is None:
        model = _create_wrapped_model(func_name, annotation, field_info)
        wrap_output = True

    # Handle GenericAlias types (list[str], dict[str, int], Union[str, int], etc.)
    elif isinstance(annotation, GenericAlias):
        origin = get_origin(annotation)

        # Special case: dict with string keys can use RootModel
        if origin is dict:
            args = get_args(annotation)
            if len(args) == 2 and args[0] is str:
                model = _create_dict_model(func_name, annotation)
            else:
                # dict with non-str keys needs wrapping
                model = _create_wrapped_model(func_name, annotation, field_info)
                wrap_output = True
        else:
            # All other generic types need wrapping (list, tuple, Union, Optional, etc.)
            model = _create_wrapped_model(func_name, annotation, field_info)
            wrap_output = True

    # Handle regular type objects
    elif isinstance(annotation, type):
        type_annotation: type[Any] = cast(type[Any], annotation)

        # Case 1: BaseModel subclasses (can be used directly)
        if issubclass(annotation, BaseModel):
            model = annotation

        # Case 2: TypedDict (special dict subclass with __annotations__)
        elif hasattr(type_annotation, "__annotations__") and issubclass(annotation, dict):
            model = _create_model_from_typeddict(type_annotation)

        # Case 3: Primitive types that need wrapping
        elif annotation in (str, int, float, bool, bytes, type(None)):
            model = _create_wrapped_model(func_name, annotation, field_info)
            wrap_output = True

        # Case 4: Other class types (dataclasses, regular classes with annotations)
        else:
            type_hints = get_type_hints(type_annotation)
            if type_hints:
                # Classes with type hints can be converted to Pydantic models
                model = _create_model_from_class(type_annotation)
            # Classes without type hints are not serializable - model remains None

    # Handle any other types not covered above
    else:
        # This includes typing constructs that aren't GenericAlias in Python 3.10
        # (e.g., Union, Optional in some Python versions)
        model = _create_wrapped_model(func_name, annotation, field_info)
        wrap_output = True

    if model:
        # If we successfully created a model, try to get its schema
        # Use StrictJsonSchema to raise exceptions instead of warnings
        try:
            schema = model.model_json_schema(schema_generator=StrictJsonSchema)
        except (TypeError, ValueError, pydantic_core.SchemaError, pydantic_core.ValidationError) as e:
            # These are expected errors when a type can't be converted to a Pydantic schema
            # TypeError: When Pydantic can't handle the type
            # ValueError: When there are issues with the type definition (including our custom warnings)
            # SchemaError: When Pydantic can't build a schema
            # ValidationError: When validation fails
            logger.info(f"Cannot create schema for type {annotation} in {func_name}: {type(e).__name__}: {e}")
            return None, None, False

        return model, schema, wrap_output

    return None, None, False


def _create_model_from_class(cls: type[Any]) -> type[BaseModel]:
    """Create a Pydantic model from an ordinary class.

    The created model will:
    - Have the same name as the class
    - Have fields with the same names and types as the class's fields
    - Include all fields whose type does not include None in the set of required fields

    Precondition: cls must have type hints (i.e., get_type_hints(cls) is non-empty)
    """
    type_hints = get_type_hints(cls)

    model_fields: dict[str, Any] = {}
    for field_name, field_type in type_hints.items():
        if field_name.startswith("_"):
            continue

        default = getattr(cls, field_name, PydanticUndefined)
        field_info = FieldInfo.from_annotated_attribute(field_type, default)
        model_fields[field_name] = (field_info.annotation, field_info)

    # Create a base class with the config
    class BaseWithConfig(BaseModel):
        model_config = ConfigDict(from_attributes=True)

    return create_model(cls.__name__, **model_fields, __base__=BaseWithConfig)


def _create_model_from_typeddict(td_type: type[Any]) -> type[BaseModel]:
    """Create a Pydantic model from a TypedDict.

    The created model will have the same name and fields as the TypedDict.
    """
    type_hints = get_type_hints(td_type)
    required_keys = getattr(td_type, "__required_keys__", set(type_hints.keys()))

    model_fields: dict[str, Any] = {}
    for field_name, field_type in type_hints.items():
        field_info = FieldInfo.from_annotation(field_type)

        if field_name not in required_keys:
            # For optional TypedDict fields, set default=None
            # This makes them not required in the Pydantic model
            # The model should use exclude_unset=True when dumping to get TypedDict semantics
            field_info.default = None

        model_fields[field_name] = (field_info.annotation, field_info)

    return create_model(td_type.__name__, **model_fields, __base__=BaseModel)


def _create_wrapped_model(func_name: str, annotation: Any, field_info: FieldInfo) -> type[BaseModel]:
    """Create a model that wraps a type in a 'result' field.

    This is used for primitive types, generic types like list/dict, etc.
    """
    model_name = f"{func_name}Output"

    # Pydantic needs type(None) instead of None for the type annotation
    if annotation is None:
        annotation = type(None)

    return create_model(model_name, result=(annotation, field_info), __base__=BaseModel)


def _create_dict_model(func_name: str, dict_annotation: Any) -> type[BaseModel]:
    """Create a RootModel for dict[str, T] types."""

    class DictModel(RootModel[dict_annotation]):
        pass

    # Give it a meaningful name
    DictModel.__name__ = f"{func_name}DictOutput"
    DictModel.__qualname__ = f"{func_name}DictOutput"

    return DictModel


def _get_typed_annotation(annotation: Any, globalns: dict[str, Any]) -> Any:
    def try_eval_type(value: Any, globalns: dict[str, Any], localns: dict[str, Any]) -> tuple[Any, bool]:
        try:
            return eval_type_backport(value, globalns, localns), True
        except NameError:
            return value, False

    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation, status = try_eval_type(annotation, globalns, globalns)

        # This check and raise could perhaps be skipped, and we (FastMCP) just call
        # model_rebuild right before using it 🤷
        if status is False:
            raise InvalidSignature(f"Unable to evaluate type annotation {annotation}")

    return annotation


def _get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    """Get function signature while evaluating forward references"""
    signature = inspect.signature(call)
    globalns = getattr(call, "__globals__", {})
    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=_get_typed_annotation(param.annotation, globalns),
        )
        for param in signature.parameters.values()
    ]
    typed_return = _get_typed_annotation(signature.return_annotation, globalns)
    typed_signature = inspect.Signature(typed_params, return_annotation=typed_return)
    return typed_signature


def _convert_to_content(
    result: Any,
) -> Sequence[ContentBlock]:
    """
    Convert a result to a sequence of content objects.

    Note: This conversion logic comes from previous versions of FastMCP and is being
    retained for purposes of backwards compatibility. It produces different unstructured
    output than the lowlevel server tool call handler, which just serializes structured
    content verbatim.
    """
    if result is None:
        return []

    if isinstance(result, ContentBlock):
        return [result]

    if isinstance(result, Image):
        return [result.to_image_content()]

    if isinstance(result, Audio):
        return [result.to_audio_content()]

    if isinstance(result, list | tuple):
        return list(
            chain.from_iterable(
                _convert_to_content(item)
                for item in result  # type: ignore
            )
        )

    if not isinstance(result, str):
        result = pydantic_core.to_json(result, fallback=str, indent=2).decode()

    return [TextContent(type="text", text=result)]