import enum

class ActivityTypeEnum(str, enum.Enum):
    dashboard_update = "dashboard_update"
    profile_update = "profile_update"
    login = "login"
    logout = "logout"
    other = "other"
