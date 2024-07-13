from .users import UserCrud
from .otp import OtpCrud
from .groups import GroupCrud, UserGroups


def get(cls_name:str):
    obj = dict(
        user_crud=UserCrud(), 
        otp_crud=OtpCrud(),
        group_crud=GroupCrud(),
        user_groups=UserGroups(),
        )
    return obj[cls_name]