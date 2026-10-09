"""
Telephony Subpackage Exports.
"""

from backend.telephony.adapter import BaseTelephonyAdapter, CallDispatchResult
from backend.telephony.plivo_adapter import PlivoAdapter

__all__ = [
    "BaseTelephonyAdapter",
    "CallDispatchResult",
    "PlivoAdapter",
]
