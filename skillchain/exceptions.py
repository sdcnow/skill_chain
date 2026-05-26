# skillchain/exceptions.py


class SkillError(Exception):
    pass


class SkillNotFoundError(SkillError):
    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        super().__init__(f"Skill not found: '{skill_name}'")


class SkillExecutionError(SkillError):
    def __init__(
        self,
        skill_name: str,
        original_error: Exception,
        context_snapshot: dict | None = None,
    ):
        self.skill_name = skill_name
        self.original_error = original_error
        self.context_snapshot = context_snapshot or {}
        super().__init__(
            f"Skill '{skill_name}' failed: {original_error}"
        )


class SkillValidationError(SkillError):
    def __init__(self, message: str):
        super().__init__(message)


class ModelError(SkillError):
    def __init__(self, model: str, original_error: Exception):
        self.model = model
        self.original_error = original_error
        super().__init__(f"Model '{model}' call failed: {original_error}")


class ChainError(SkillError):
    def __init__(
        self,
        skill_name: str,
        position: int,
        original_error: Exception,
    ):
        self.skill_name = skill_name
        self.position = position
        self.original_error = original_error
        super().__init__(
            f"Chain failed at skill '{skill_name}' (position {position}): {original_error}"
        )
